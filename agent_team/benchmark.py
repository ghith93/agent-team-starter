"""Opt-in benchmark for free models on deterministic, isolated coding fixtures.

No provider requests are made unless --run is supplied and
AUTHORIZE_BENCHMARK_PROVIDER_CALLS=true. The benchmark runs only fixed free-model IDs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .patch_task import run_patch_task
from .router import FreeFirstRouter, ProviderError

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "benchmarks" / "coding_tasks.json"
ALLOWED_MODELS = {"openrouter/free"}
MAX_TASKS = 3
MAX_DIAGNOSTIC_CHARS = 240
DEFAULT_MODELS = (
    "cohere/north-mini-code:free",
    "qwen/qwen3.8-27b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)


def _load_tasks() -> list[dict]:
    payload = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= MAX_TASKS:
        raise ValueError("Benchmark task set is invalid.")
    for task in tasks:
        if not isinstance(task, dict) or not all(isinstance(task.get(k), str) and task[k] for k in ("id", "fixture", "task")):
            raise ValueError("Benchmark task definition is invalid.")
        fixture = (ROOT / task["fixture"]).resolve()
        if ROOT not in fixture.parents or not fixture.is_dir():
            raise ValueError("Benchmark fixture path escapes the repository.")
    return tasks


def _model_is_free(model: str) -> bool:
    return model in ALLOWED_MODELS or bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:free", model))


def _safe_diagnostic(value: object) -> str:
    """Bound diagnostics so reports explain failures without dumping arbitrary output."""
    text = " ".join(str(value).split())
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", text)
    text = re.sub(r"(?i)(api[_ -]?key|token|authorization)(\s*[:=]\s*)[^,; ]+", r"\1\2[REDACTED]", text)
    return text[:MAX_DIAGNOSTIC_CHARS]


def run_benchmark(models: list[str], validation: str = "unittest") -> dict:
    if not models or len(models) > 3 or len(set(models)) != len(models):
        raise ValueError("Select between one and three distinct model IDs.")
    if any(not _model_is_free(model) for model in models):
        raise ValueError("Only openrouter/free or explicit :free model IDs are allowed.")
    if validation not in {"unittest", "compile"}:
        raise ValueError("Benchmark validation must be unittest or compile.")
    if validation == "unittest" and os.environ.get("AUTHORIZE_BENCHMARK_TEST_EXECUTION", "").lower() != "true":
        raise PermissionError("Set AUTHORIZE_BENCHMARK_TEST_EXECUTION=true to run fixture tests in Docker.")
    if os.environ.get("AUTHORIZE_BENCHMARK_PROVIDER_CALLS", "").lower() != "true":
        raise PermissionError("No provider call was made. Set AUTHORIZE_BENCHMARK_PROVIDER_CALLS=true to authorize benchmark calls.")
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        raise PermissionError("OPENROUTER_API_KEY is missing; no provider call was made.")

    tasks = _load_tasks()
    results = []
    for model in models:
        router = FreeFirstRouter(
            gemini_key="",
            enable_gemini=False,
            free_models=[model],
            stage_models={"draft": [model]},
        )
        for task in tasks:
            started = time.monotonic()
            try:
                result = run_patch_task(
                    task["task"],
                    router=router,
                    workspace=ROOT / task["fixture"],
                    validations=(validation,),
                )
                changed = result.get("changed_paths", [])
                touched_tests = any(
                    Path(path).name.startswith("test_") or "/test_" in path
                    for path in changed
                )
                passed = result.get("ok") is True and not touched_tests
                row = {
                    "task_id": task["id"], "requested_model": model,
                    "reported_model": result.get("model", "unknown"),
                    "provider": result.get("provider", "unknown"),
                    "status": "passed" if passed else result.get("status", "failed"),
                    "validation": validation,
                    "validation_results": result.get("validations", []),
                    "changed_paths": changed,
                    "tests_modified": touched_tests,
                    "patch_bytes": len(result.get("patch", "").encode("utf-8")),
                    "message": _safe_diagnostic(result.get("message") or (
                        "Benchmark fixtures may be solved by model output; tests are not allowed to be changed."
                    )),
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
            except Exception as exc:
                row = {
                    "task_id": task["id"], "requested_model": model,
                    "status": "error", "error_type": type(exc).__name__,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
                # ProviderError is deliberately sanitized by router.py before it reaches here.
                # Avoid serializing arbitrary unexpected exception text into CI artifacts.
                if isinstance(exc, ProviderError):
                    row["error_message"] = _safe_diagnostic(exc)
            results.append(row)
    summary = {}
    for model in models:
        subset = [row for row in results if row.get("requested_model") == model]
        summary[model] = {
            "tasks": len(subset),
            "passed": sum(row.get("status") == "passed" for row in subset),
            "failed_or_error": sum(row.get("status") != "passed" for row in subset),
            "mean_duration_ms": round(sum(row.get("duration_ms", 0) for row in subset) / max(1, len(subset)), 2),
        }
    return {
        "benchmark_version": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation": validation,
        "logical_model_task_pairs": len(models) * len(tasks),
        "maximum_http_requests_including_one_transient_retry": 2 * len(models) * len(tasks),
        "models": models,
        "summary": summary,
        "results": results,
        "limitations": [
            "A passing score means the fixed fixture tests passed without modifying tests; it does not measure general coding ability.",
            "Provider/model availability and free quotas can change. No paid model fallback is permitted.",
            "Docker dependency image builds may use network access; candidate tests themselves run with network disabled.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Run provider calls; requires explicit environment authorization.")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--validation", choices=("unittest", "compile"), default="unittest")
    parser.add_argument("--output", default="free-model-benchmark-result.json")
    args = parser.parse_args()
    models = [item.strip() for item in args.models.split(",") if item.strip()]
    if not args.run:
        tasks = _load_tasks()
        print(json.dumps({
            "mode": "dry-run",
            "provider_calls": 0,
            "tasks": [{"id": task["id"], "fixture": task["fixture"]} for task in tasks],
            "models": models,
            "logical_model_task_pairs_if_authorized": len(tasks) * len(models),
            "maximum_http_requests_including_one_retry": 2 * len(tasks) * len(models),
            "message": "No provider calls were made. Pass --run and explicitly set AUTHORIZE_BENCHMARK_PROVIDER_CALLS=true to execute.",
        }, indent=2))
        return 0
    report = run_benchmark(models, args.validation)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "output": args.output}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
