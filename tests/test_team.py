import unittest
from unittest.mock import patch
from types import SimpleNamespace

from agent_team.router import ProviderError
from agent_team.team import MAX_STAGE_OUTPUT_CHARS, TeamExecutionError, run_team


class FakeRouter:
    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at

    def ask(self, prompt, *, system_prompt=""):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        if self.fail_at == len(self.calls):
            raise ProviderError("simulated provider failure", 503)
        return SimpleNamespace(provider="fake", model="offline", text=f"stage-{len(self.calls)}")


class TeamTests(unittest.TestCase):
    def test_successful_run_has_three_stages(self):
        router = FakeRouter()
        result = run_team("test task", router)
        self.assertEqual(len(router.calls), 3)
        self.assertEqual(result["plan"]["text"], "stage-1")
        self.assertEqual(result["draft"]["text"], "stage-2")
        self.assertEqual(result["review"]["text"], "stage-3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["final"], result["draft"]["text"])
        self.assertTrue(result["run_id"])
        self.assertGreaterEqual(result["total_duration_ms"], 0)
        self.assertIn("stage-1", router.calls[1]["prompt"])
        self.assertIn("stage-2", router.calls[2]["prompt"])
        self.assertIn("untrusted data", router.calls[0]["system_prompt"])
        self.assertIn("execution agent", router.calls[1]["system_prompt"])
        self.assertIn("independent reviewer", router.calls[2]["system_prompt"])
        self.assertNotIn("You are the planning agent", router.calls[0]["prompt"])
        self.assertNotIn("You are the execution agent", router.calls[1]["prompt"])

    def test_failure_reports_stage_and_partial_results(self):
        router = FakeRouter(fail_at=2)
        with self.assertRaises(TeamExecutionError) as caught:
            run_team("test task", router)
        error = caught.exception
        self.assertEqual(error.stage, "draft")
        self.assertIn("plan", error.completed)
        self.assertNotIn("draft", error.completed)
        self.assertEqual(len(router.calls), 2)

    def test_oversized_task_is_rejected_before_router_execution(self):
        router = FakeRouter()
        with self.assertRaisesRegex(ValueError, "maximum 12000 characters"):
            run_team("x" * 12001, router)
        self.assertEqual(router.calls, [])

    def test_telemetry_write_failure_does_not_fail_successful_run(self):
        router = FakeRouter()
        with patch("agent_team.team._write_events", side_effect=OSError("private path detail")):
            result = run_team("test task", router, telemetry_path="unused.jsonl")
        self.assertTrue(result["ok"])
        self.assertEqual(result["final"], "stage-2")
        self.assertEqual(result["telemetry_warning"], "Telemetry write failed (OSError).")
        self.assertNotIn("private path detail", str(result))

    def test_telemetry_write_failure_does_not_mask_stage_failure(self):
        router = FakeRouter(fail_at=1)
        with patch("agent_team.team._write_events", side_effect=OSError("private path detail")):
            with self.assertRaises(TeamExecutionError) as caught:
                run_team("test task", router, telemetry_path="unused.jsonl")
        self.assertEqual(caught.exception.stage, "plan")
        self.assertIsInstance(caught.exception.cause, ProviderError)
        self.assertEqual(caught.exception.telemetry_warning, "Telemetry write failed (OSError).")
        self.assertNotIn("private path detail", str(caught.exception))

    def test_empty_output_stops_at_stage(self):
        class EmptyRouter:
            def ask(self, prompt, *, system_prompt=""):
                return SimpleNamespace(provider="fake", model="offline", text=" ")
        with self.assertRaises(TeamExecutionError) as caught:
            run_team("test task", EmptyRouter())
        self.assertEqual(caught.exception.stage, "plan")

    def test_oversized_stage_output_is_rejected(self):
        class OversizedRouter:
            def ask(self, prompt, *, system_prompt=""):
                return SimpleNamespace(provider="fake", model="offline", text="x" * (MAX_STAGE_OUTPUT_CHARS + 1))
        with self.assertRaises(TeamExecutionError) as caught:
            run_team("test task", OversizedRouter())
        self.assertEqual(caught.exception.stage, "plan")
        self.assertNotIn("x" * 100, str(caught.exception))

    def test_stage_error_message_does_not_echo_sensitive_exception_text(self):
        class LeakyRouter:
            def ask(self, prompt, *, system_prompt=""):
                raise RuntimeError("Bearer sensitive-token prompt-fragment")
        with self.assertRaises(TeamExecutionError) as caught:
            run_team("test task", LeakyRouter())
        self.assertEqual(caught.exception.stage, "plan")
        self.assertNotIn("sensitive-token", str(caught.exception))
        self.assertNotIn("prompt-fragment", str(caught.exception))
        self.assertIsInstance(caught.exception.cause, RuntimeError)


if __name__ == "__main__":
    unittest.main()
