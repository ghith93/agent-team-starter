"""Free-first model routing with explicit fallback behavior."""
from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Callable, Optional
import inspect
import requests


@dataclass
class ModelResult:
    provider: str
    model: str
    text: str


class ProviderError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def classify_http_error(status: int, body: str = "") -> str:
    if status in (401, 403):
        return "authentication_or_permission"
    if status == 402:
        return "payment_required"
    if status == 404:
        return "model_or_endpoint_not_found"
    if status == 400:
        return "invalid_request"
    if status == 429:
        return "rate_limited"
    if 500 <= status <= 599:
        return "provider_unavailable"
    return "request_failed"


def _safe_provider_detail(response: requests.Response, sensitive_values: tuple[str, ...] = ()) -> str:
    """Return a short provider error hint without dumping headers or secrets."""
    try:
        payload = response.json()
        if not isinstance(payload, dict):
            return ""
        error = payload.get("error", {})
        if isinstance(error, dict):
            detail = error.get("message") or error.get("code") or ""
        else:
            detail = str(error)
    except (ValueError, TypeError, AttributeError):
        detail = ""
    detail = " ".join(str(detail).split())
    # Redact the exact credentials used for this request before generic patterns.
    for secret in sorted((value for value in sensitive_values if value), key=len, reverse=True):
        detail = detail.replace(secret, "[REDACTED]")
    # Provider error bodies are untrusted and may echo credentials or request content.
    detail = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[REDACTED]", detail)
    detail = re.sub(r"(?i)(api[_ -]?key|token|authorization)(\s*[:=]\s*)[^,; ]+", r"\1\2[REDACTED]", detail)
    return detail[:120]


def openrouter_chat(api_key: str, model: str, prompt: str, timeout: int = 45, *, system_prompt: str = "") -> str:
    if model != "openrouter/free" and not model.endswith(":free"):
        raise ProviderError("Refusing non-free OpenRouter model.")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [{"role": "user", "content": prompt}], "max_tokens": 1200},
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise ProviderError(f"Network error: {type(exc).__name__}") from exc
    if response.status_code != 200:
        category = classify_http_error(response.status_code, response.text[:500])
        detail = _safe_provider_detail(response, (api_key,))
        suffix = f": {detail}" if detail else ""
        raise ProviderError(f"{category} (HTTP {response.status_code}){suffix}", response.status_code)
    try:
        text = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Malformed response from OpenRouter") from exc
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("Provider returned empty text")
    return text.strip()




def gemini_chat(api_key: str, model: str, prompt: str, timeout: int = 45, *, system_prompt: str = "") -> str:
    # REST endpoint avoids adding a second SDK dependency.
    model = model.removeprefix("models/")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        response = requests.post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=({"systemInstruction": {"parts": [{"text": system_prompt}]}} if system_prompt else {}) | {"contents": [{"parts": [{"text": prompt}]}]},
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise ProviderError(f"Network error: {type(exc).__name__}") from exc
    if response.status_code != 200:
        category = classify_http_error(response.status_code, response.text[:500])
        detail = _safe_provider_detail(response, (api_key,))
        suffix = f": {detail}" if detail else ""
        raise ProviderError(f"{category} (HTTP {response.status_code}){suffix}", response.status_code)
    try:
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Malformed response from Gemini") from exc
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("Provider returned empty text")
    return text.strip()


class FreeFirstRouter:
    def __init__(
        self,
        gemini_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        free_models: Optional[list[str]] = None,
        gemini_call: Callable = gemini_chat,
        openrouter_call: Callable = openrouter_chat,
        enable_gemini: bool = False,
    ):
        # Gemini may be billable and is therefore disabled unless the caller explicitly opts in.
        self.enable_gemini = enable_gemini is True
        self.gemini_key = (gemini_key if gemini_key is not None else os.getenv("GEMINI_API_KEY", "")).strip()
        self.openrouter_key = (openrouter_key if openrouter_key is not None else os.getenv("OPENROUTER_API_KEY", "")).strip()
        self.gemini_model = (gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()
        raw = os.getenv(
            "OPENROUTER_FREE_MODELS",
            "openrouter/free",
        )
        self.free_models = free_models if free_models is not None else [x.strip() for x in raw.split(",") if x.strip()]
        if any(not model or (model != "openrouter/free" and not model.endswith(":free")) for model in self.free_models):
            raise ValueError("OpenRouter models must be 'openrouter/free' or end with ':free'.")
        self.gemini_call = gemini_call
        self.openrouter_call = openrouter_call

    @staticmethod
    def _is_transient_provider_error(exc: ProviderError) -> bool:
        # Empty/malformed transient responses and network errors have no status code.
        # Retry rate limits and server errors once; never retry auth/payment/invalid requests.
        return exc.status_code is None or exc.status_code == 429 or (
            exc.status_code is not None and 500 <= exc.status_code <= 599
        )

    @staticmethod
    def _call_provider(call: Callable, args: tuple, system_prompt: str) -> str:
        """Pass a system instruction when the provider callable supports it.

        The compatibility branch permits simple legacy test doubles/custom callables;
        production provider functions support the separated system instruction.
        """
        try:
            signature = inspect.signature(call)
            supports = "system_prompt" in signature.parameters or any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
        except (TypeError, ValueError):
            supports = False
        if supports:
            return call(*args, system_prompt=system_prompt)
        return call(*args)

    @classmethod
    def _call_provider_with_retry(cls, call: Callable, args: tuple, system_prompt: str) -> str:
        # One bounded retry absorbs occasional free-router empty responses and transient network/provider failures.
        for attempt in range(2):
            try:
                return cls._call_provider(call, args, system_prompt)
            except ProviderError as exc:
                if attempt == 0 and cls._is_transient_provider_error(exc):
                    continue
                raise

    def ask(self, prompt: str, *, system_prompt: str = "") -> ModelResult:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")
        failures = []
        if self.enable_gemini and self.gemini_key:
            try:
                return ModelResult("Gemini", self.gemini_model,
                                   self._call_provider_with_retry(self.gemini_call, (self.gemini_key, self.gemini_model, prompt), system_prompt))
            except ProviderError as exc:
                failures.append(f"Gemini: {classify_http_error(exc.status_code) if exc.status_code else type(exc).__name__}" )
        if self.openrouter_key:
            for model in self.free_models:
                try:
                    return ModelResult("OpenRouter", model,
                                       self._call_provider_with_retry(self.openrouter_call, (self.openrouter_key, model, prompt), system_prompt))
                except ProviderError as exc:
                    failures.append(f"{model}: {classify_http_error(exc.status_code) if exc.status_code else type(exc).__name__}")
                    # Authentication/payment failures usually affect the whole key/account.
                    if exc.status_code in (401, 403, 402):
                        break
        raise ProviderError("No model succeeded. " + " | ".join(failures or ["No API keys configured."]))
