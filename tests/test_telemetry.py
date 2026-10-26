import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent_team.team import TeamExecutionError, run_team


class FakeRouter:
    def __init__(self, fail_at=None):
        self.calls = 0
        self.fail_at = fail_at

    def ask(self, prompt, *, system_prompt=""):
        self.calls += 1
        if self.calls == self.fail_at:
            raise RuntimeError("simulated failure")
        return SimpleNamespace(provider="fake", model="offline", text=f"private output {self.calls}")


class TelemetryTests(unittest.TestCase):
    def test_trace_is_returned_without_logging_by_default(self):
        result = run_team("private task", FakeRouter())
        self.assertEqual([x["stage"] for x in result["trace"]], ["plan", "draft", "review", "revise"])
        self.assertTrue(all(x["status"] == "success" for x in result["trace"]))

    def test_opt_in_log_contains_metadata_but_not_prompts_or_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logs" / "events.jsonl"
            result = run_team("SECRET TASK", FakeRouter(), telemetry_path=path)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["stage"], "plan")
            self.assertIn("duration_ms", rows[0])
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("SECRET TASK", raw)
            self.assertNotIn("private output", raw)
            self.assertEqual(len(result["trace"]), 4)

    def test_failure_trace_is_preserved_and_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            with self.assertRaises(TeamExecutionError) as caught:
                run_team("test task", FakeRouter(fail_at=2), telemetry_path=path)
            self.assertEqual(caught.exception.stage, "draft")
            self.assertEqual(caught.exception.trace[-1]["status"], "failure")
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([r["status"] for r in rows], ["success", "failure"])


if __name__ == "__main__":
    unittest.main()
