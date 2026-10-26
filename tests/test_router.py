import unittest
from unittest.mock import patch
from agent_team.router import FreeFirstRouter, ProviderError, classify_http_error, openrouter_chat, gemini_chat
from agent_team.team import run_team
from agent_team.router import ModelResult


class RouterTests(unittest.TestCase):
    def test_classifies_common_statuses(self):
        self.assertEqual(classify_http_error(401), "authentication_or_permission")
        self.assertEqual(classify_http_error(402), "payment_required")
        self.assertEqual(classify_http_error(404), "model_or_endpoint_not_found")
        self.assertEqual(classify_http_error(400), "invalid_request")
        self.assertEqual(classify_http_error(429), "rate_limited")
        self.assertEqual(classify_http_error(503), "provider_unavailable")

    def test_rejects_nonfree_fallback(self):
        with self.assertRaises(ValueError):
            FreeFirstRouter(free_models=["provider/model"])

    def test_accepts_openrouter_free_router(self):
        router = FreeFirstRouter(free_models=["openrouter/free"], gemini_key="", openrouter_key="")
        self.assertEqual(router.free_models, ["openrouter/free"])

    def test_gemini_key_does_not_enable_provider_by_default(self):
        calls = []
        router = FreeFirstRouter(
            gemini_key="gemini-key", openrouter_key="", free_models=[],
            gemini_call=lambda *args, **kwargs: calls.append(args) or "should not run",
        )
        with self.assertRaises(ProviderError):
            router.ask("test")
        self.assertFalse(router.enable_gemini)
        self.assertEqual(calls, [])

    def test_stage_specific_free_models_are_used_with_global_fallback(self):
        calls = []
        def openrouter(key, model, prompt, *, system_prompt=""):
            calls.append(model)
            return "ok"
        router = FreeFirstRouter(
            gemini_key="", openrouter_key="o", free_models=["openrouter/free"],
            stage_models={
                "draft": ["cohere/north-mini-code:free", "openrouter/free"],
                "review": ["nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter/free"],
            },
            openrouter_call=openrouter,
        )
        router.ask("draft", stage="draft")
        router.ask("review", stage="review")
        router.ask("default")
        self.assertEqual(calls, [
            "cohere/north-mini-code:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "openrouter/free",
        ])

    def test_stage_specific_paid_models_are_rejected(self):
        with self.assertRaises(ValueError):
            FreeFirstRouter(
                free_models=["openrouter/free"],
                stage_models={"draft": ["provider/paid-model"]},
            )

    def test_stage_specific_models_can_be_configured_by_environment(self):
        with patch.dict("os.environ", {
            "OPENROUTER_FREE_MODELS": "openrouter/free",
            "OPENROUTER_DRAFT_MODELS": "cohere/north-mini-code:free,openrouter/free",
        }, clear=False):
            router = FreeFirstRouter(gemini_key="", openrouter_key="")
        self.assertEqual(router.stage_models["draft"], ["cohere/north-mini-code:free", "openrouter/free"])
        self.assertEqual(router.stage_models["review"], ["openrouter/free"])



    def test_falls_back_after_gemini_transient_error(self):
        def bad_gemini(*args):
            raise ProviderError("provider_unavailable", 503)
        def good_openrouter(key, model, prompt, *, system_prompt=""):
            self.assertEqual(system_prompt, "trusted role")
            return "fallback works"
        router = FreeFirstRouter(
            gemini_key="g", openrouter_key="o",
            free_models=["provider/model:free"],
            gemini_call=bad_gemini, openrouter_call=good_openrouter, enable_gemini=True
        )
        result = router.ask("test", system_prompt="trusted role")
        self.assertEqual(result.provider, "OpenRouter")
        self.assertEqual(result.text, "fallback works")

    def test_falls_back_after_gemini_404(self):
        def bad_gemini(*args):
            raise ProviderError("model_or_endpoint_not_found", 404)
        router = FreeFirstRouter(
            gemini_key="g", openrouter_key="o",
            free_models=["provider/model:free"],
            gemini_call=bad_gemini,
            openrouter_call=lambda *args: "fallback works",
            enable_gemini=True,
        )
        self.assertEqual(router.ask("test").text, "fallback works")

    def test_retries_transient_provider_failure_once(self):
        calls = []
        def flaky_openrouter(key, model, prompt, *, system_prompt=""):
            calls.append(model)
            if len(calls) == 1:
                raise ProviderError("provider_unavailable", 503)
            return "recovered"
        router = FreeFirstRouter(
            gemini_key="", openrouter_key="o",
            free_models=["openrouter/free"], openrouter_call=flaky_openrouter,
        )
        result = router.ask("test")
        self.assertEqual(result.text, "recovered")
        self.assertEqual(calls, ["openrouter/free", "openrouter/free"])

    def test_retries_empty_success_response_once(self):
        calls = []
        class Response:
            status_code = 200
            def __init__(self, content):
                self.content = content
            def json(self):
                return {"choices": [{"message": {"content": self.content}}]}
        def response_sequence(*args, **kwargs):
            calls.append(1)
            return Response("" if len(calls) == 1 else "recovered")
        router = FreeFirstRouter(
            gemini_key="", openrouter_key="test-key",
            free_models=["openrouter/free"],
        )
        with patch("agent_team.router.requests.post", side_effect=response_sequence):
            result = router.ask("test")
        self.assertEqual(result.text, "recovered")
        self.assertEqual(len(calls), 2)

    def test_does_not_retry_authentication_failure(self):
        calls = []
        def unauthorized(key, model, prompt, *, system_prompt=""):
            calls.append(model)
            raise ProviderError("authentication_or_permission", 401)
        router = FreeFirstRouter(
            gemini_key="", openrouter_key="o",
            free_models=["openrouter/free", "other/model:free"],
            openrouter_call=unauthorized,
        )
        with self.assertRaises(ProviderError):
            router.ask("test")
        self.assertEqual(calls, ["openrouter/free"])

    def test_final_provider_error_preserves_safe_actionable_hint(self):
        def unavailable(key, model, prompt, *, system_prompt=""):
            raise ProviderError("provider_unavailable (HTTP 503): model temporarily overloaded", 503)
        router = FreeFirstRouter(
            gemini_key="", openrouter_key="test-key", free_models=["sample/model:free"],
            openrouter_call=unavailable,
        )
        with self.assertRaises(ProviderError) as caught:
            router.ask("test")
        self.assertIn("provider_unavailable", str(caught.exception))
        self.assertIn("temporarily overloaded", str(caught.exception))

    def test_final_provider_error_redacts_credentials_from_custom_provider(self):
        def unsafe_provider(key, model, prompt, *, system_prompt=""):
            raise ProviderError("invalid token=supersecret123 Bearer abc.def.ghi", 401)
        router = FreeFirstRouter(
            gemini_key="", openrouter_key="account-key-123", free_models=["sample/model:free"],
            openrouter_call=unsafe_provider,
        )
        with self.assertRaises(ProviderError) as caught:
            router.ask("test")
        message = str(caught.exception)
        self.assertNotIn("supersecret123", message)
        self.assertNotIn("abc.def.ghi", message)
        self.assertNotIn("account-key-123", message)
        self.assertIn("[REDACTED]", message)

    def test_no_keys_fails_closed(self):
        router = FreeFirstRouter(gemini_key="", openrouter_key="", free_models=[])
        with self.assertRaises(ProviderError):
            router.ask("test")

    def test_rejects_empty_prompt(self):
        router = FreeFirstRouter(gemini_key="", openrouter_key="", free_models=[])
        with self.assertRaises(ValueError):
            router.ask("  ")

    def test_rejects_empty_task(self):
        class NeverCalledRouter:
            def ask(self, prompt):
                raise AssertionError("Router should not be called")
        with self.assertRaises(ValueError):
            run_team(" ", NeverCalledRouter())

    def test_malformed_non_object_error_body_does_not_mask_provider_error(self):
        class Response:
            status_code = 503
            text = "untrusted error body"
            def json(self):
                return ["unexpected", "shape"]
        with patch("agent_team.router.requests.post", return_value=Response()):
            with self.assertRaises(ProviderError) as caught:
                openrouter_chat("k", "openrouter/free", "test")
        self.assertIn("provider_unavailable (HTTP 503)", str(caught.exception))

    def test_provider_error_detail_redacts_bearer_token(self):
        class Response:
            status_code = 401
            text = "untrusted error body"
            def json(self):
                return {"error": {"message": "Bearer abc.def.ghi authorization=secret-value"}}
        with patch("agent_team.router.requests.post", return_value=Response()):
            with self.assertRaises(ProviderError) as caught:
                openrouter_chat("k", "openrouter/free", "test")
        message = str(caught.exception)
        self.assertNotIn("abc.def.ghi", message)
        self.assertNotIn("secret-value", message)

    def test_provider_error_detail_redacts_exact_api_key_if_echoed(self):
        credential_fixture = "test_key_echo_marker_73921"
        class Response:
            status_code = 401
            text = "untrusted error body"
            def json(self):
                return {"error": {"message": f"invalid credential {credential_fixture}"}}
        with patch("agent_team.router.requests.post", return_value=Response()):
            with self.assertRaises(ProviderError) as caught:
                openrouter_chat(credential_fixture, "openrouter/free", "test")
        self.assertNotIn(credential_fixture, str(caught.exception))
        self.assertIn("[REDACTED]", str(caught.exception))

    def test_gemini_error_detail_redacts_exact_api_key_if_echoed(self):
        credential_fixture = "test_key_echo_marker_28463"
        class Response:
            status_code = 401
            text = "untrusted error body"
            def json(self):
                return {"error": {"message": f"invalid credential {credential_fixture}"}}
        with patch("agent_team.router.requests.post", return_value=Response()):
            with self.assertRaises(ProviderError) as caught:
                gemini_chat(credential_fixture, "gemini-test", "test")
        self.assertNotIn(credential_fixture, str(caught.exception))
        self.assertIn("[REDACTED]", str(caught.exception))

    def test_openrouter_uses_separate_system_message(self):
        class Response:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}
        with patch("agent_team.router.requests.post", return_value=Response()) as post:
            self.assertEqual(openrouter_chat("k", "openrouter/free", "untrusted", system_prompt="trusted"), "ok")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "trusted"})
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "untrusted"})

    def test_gemini_uses_separate_system_instruction(self):
        class Response:
            status_code = 200
            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        with patch("agent_team.router.requests.post", return_value=Response()) as post:
            self.assertEqual(gemini_chat("k", "gemini-test", "untrusted", system_prompt="trusted"), "ok")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "trusted")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "untrusted")


    def test_provider_requests_do_not_follow_redirects(self):
        class OpenRouterResponse:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        class GeminiResponse:
            status_code = 200
            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

        with patch("agent_team.router.requests.post", return_value=OpenRouterResponse()) as post:
            openrouter_chat("key", "openrouter/free", "task")
            self.assertIs(post.call_args.kwargs["allow_redirects"], False)

        with patch("agent_team.router.requests.post", return_value=GeminiResponse()) as post:
            gemini_chat("key", "gemini-test", "task")
            self.assertIs(post.call_args.kwargs["allow_redirects"], False)


if __name__ == "__main__":
    unittest.main()
