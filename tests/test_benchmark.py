import os
import unittest
from unittest.mock import patch

from agent_team.benchmark import DEFAULT_MODELS, _load_tasks, _model_is_free, _safe_diagnostic, run_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_fixed_task_set_is_available_without_provider_calls(self):
        tasks = _load_tasks()
        self.assertEqual([task["id"] for task in tasks], [
            "normalize-spaces", "clamp-value", "word-count",
        ])

    def test_only_explicit_free_model_ids_are_accepted(self):
        self.assertTrue(_model_is_free("openrouter/free"))
        self.assertTrue(_model_is_free("cohere/north-mini-code:free"))
        self.assertTrue(_model_is_free("poolside/laguna-s-2.1:free"))
        self.assertTrue(_model_is_free("qwen/qwen3.8-27b:free"))
        self.assertFalse(_model_is_free("openai/gpt-4o"))
        self.assertFalse(_model_is_free("cohere/north-mini-code"))

    def test_default_benchmark_roster_uses_pinned_free_models(self):
        self.assertEqual(len(DEFAULT_MODELS), 3)
        self.assertEqual(len(set(DEFAULT_MODELS)), 3)
        self.assertIn("cohere/north-mini-code:free", DEFAULT_MODELS)
        self.assertIn("qwen/qwen3.8-27b:free", DEFAULT_MODELS)
        self.assertTrue(all(_model_is_free(model) for model in DEFAULT_MODELS))

    def test_diagnostics_are_bounded_and_redact_credentials(self):
        message = "HTTP error Bearer abcdefghijklmnop api_key=supersecretvalue " + ("x" * 400)
        diagnostic = _safe_diagnostic(message)
        self.assertNotIn("abcdefghijklmnop", diagnostic)
        self.assertNotIn("supersecretvalue", diagnostic)
        self.assertLessEqual(len(diagnostic), 240)

    def test_provider_execution_is_gated_before_router_or_provider_calls(self):
        with patch.dict(os.environ, {
            "AUTHORIZE_BENCHMARK_PROVIDER_CALLS": "false",
            "AUTHORIZE_BENCHMARK_TEST_EXECUTION": "true",
        }):
            with self.assertRaisesRegex(PermissionError, "No provider call was made"):
                run_benchmark(["openrouter/free"], validation="unittest")

    def test_paid_model_is_rejected_before_authorization_or_provider_calls(self):
        with self.assertRaisesRegex(ValueError, "Only openrouter/free"):
            run_benchmark(["vendor/paid-model"], validation="compile")


if __name__ == "__main__":
    unittest.main()
