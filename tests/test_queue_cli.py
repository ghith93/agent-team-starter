import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_team.cli import main
from agent_team.router import ProviderError
from agent_team.team import TeamExecutionError
from agent_team.workflow_store import WorkflowStore


class QueueCliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "runtime" / "queue.sqlite3"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_enqueue_persists_task_without_calling_model(self):
        out = io.StringIO()
        with patch("agent_team.cli.run_team") as run, contextlib.redirect_stdout(out):
            code = main(["--queue-db", str(self.database), "--enqueue", "prepare a report"])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertTrue(payload["queued"])
        self.assertEqual(payload["status"], "queued")
        self.assertNotIn("prepare a report", out.getvalue())
        run.assert_not_called()
        saved = WorkflowStore(self.database).get(payload["job_id"])
        self.assertEqual(saved["task"], "prepare a report")

    def test_run_next_completes_job_and_persists_metadata_only(self):
        store = WorkflowStore(self.database)
        job = store.enqueue("private task")
        fake_result = {
            "ok": True,
            "run_id": "run-123",
            "final": "sensitive generated text",
            "trace": [
                {"stage": "plan", "provider": "Gemini"},
                {"stage": "draft", "provider": "OpenRouter"},
                {"stage": "review", "provider": "Gemini"},
            ],
            "total_duration_ms": 12.5,
        }
        out = io.StringIO()
        with patch("agent_team.cli.run_team", return_value=fake_result) as run, contextlib.redirect_stdout(out):
            code = main(["--queue-db", str(self.database), "--run-next"])
        self.assertEqual(code, 0)
        run.assert_called_once()
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["status"], "succeeded")
        self.assertNotIn("sensitive generated text", out.getvalue())
        saved = WorkflowStore(self.database).get(job["job_id"])
        self.assertEqual(saved["status"], "succeeded")
        self.assertEqual(saved["result"]["providers"], ["Gemini", "OpenRouter"])
        self.assertNotIn("final", saved["result"])

    def test_run_next_retries_only_transient_provider_errors(self):
        store = WorkflowStore(self.database)
        job = store.enqueue("temporary provider outage", max_attempts=2)
        error = TeamExecutionError("draft", ProviderError("provider unavailable", 503), {}, [])
        out = io.StringIO()
        with patch("agent_team.cli.run_team", side_effect=error), contextlib.redirect_stderr(out):
            code = main(["--queue-db", str(self.database), "--run-next", "--retry-delay-seconds", "0"])
        self.assertEqual(code, 1)
        saved = WorkflowStore(self.database).get(job["job_id"])
        self.assertEqual(saved["status"], "queued")
        self.assertEqual(saved["error_type"], "ProviderError")

    def test_run_next_does_not_retry_authentication_errors(self):
        store = WorkflowStore(self.database)
        job = store.enqueue("invalid provider credentials", max_attempts=3)
        error = TeamExecutionError("draft", ProviderError("not authorized", 401), {}, [])
        with patch("agent_team.cli.run_team", side_effect=error), contextlib.redirect_stderr(io.StringIO()):
            code = main(["--queue-db", str(self.database), "--run-next"])
        self.assertEqual(code, 1)
        self.assertEqual(WorkflowStore(self.database).get(job["job_id"])["status"], "failed")

    def test_worker_processes_a_job_and_exits_at_limit(self):
        store = WorkflowStore(self.database)
        job = store.enqueue("worker task")
        result = {
            "ok": True, "run_id": "worker-run", "final": "output",
            "trace": [{"provider": "Gemini"}] * 3, "total_duration_ms": 3.0,
        }
        out = io.StringIO()
        with patch("agent_team.cli.run_team", return_value=result) as run, contextlib.redirect_stdout(out):
            code = main(["--queue-db", str(self.database), "--worker", "--max-jobs", "1"])
        self.assertEqual(code, 0)
        self.assertEqual(WorkflowStore(self.database).get(job["job_id"])["status"], "succeeded")
        self.assertEqual(run.call_count, 1)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(lines[-1]["reason"], "max_jobs_reached")
        self.assertEqual(lines[-1]["attempts_processed"], 1)

    def test_empty_queue_is_a_successful_noop(self):
        WorkflowStore(self.database)
        out = io.StringIO()
        with patch("agent_team.cli.run_team") as run, contextlib.redirect_stdout(out):
            code = main(["--queue-db", str(self.database), "--run-next"])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out.getvalue())["claimed"])
        run.assert_not_called()

    def test_queue_modes_require_explicit_database_and_action(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            code = main(["--enqueue", "task"])
        self.assertEqual(code, 2)
        self.assertIn("--queue-db", out.getvalue())


if __name__ == "__main__":
    unittest.main()
