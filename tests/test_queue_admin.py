import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_team.queue_admin import _copy_database, main, queue_status
from agent_team.workflow_store import WorkflowStore


class QueueAdminTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.database = self.root / "runtime" / "queue.sqlite3"
        self.store = WorkflowStore(self.database)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_status_reports_counts_without_task_content(self):
        queued = self.store.enqueue("do not reveal this task", now=100)
        claimed = self.store.claim_next(now=101, lease_seconds=5)
        result = queue_status(self.database, now=107)
        self.assertTrue(result["healthy"])
        self.assertEqual(result["jobs_by_status"]["running"], 1)
        self.assertEqual(result["expired_leases"], 1)
        self.assertNotIn("do not reveal this task", json.dumps(result))

    def test_backup_and_restore_preserve_queue_and_integrity(self):
        job = self.store.enqueue("backup sample task")
        backup = self.root / "backups" / "queue-backup.sqlite3"
        restored = self.root / "restored" / "queue.sqlite3"
        backup_result = _copy_database(self.database, backup)
        self.assertEqual(backup_result["integrity_check"], "ok")
        if os.name == "posix":
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        restore_result = _copy_database(backup, restored)
        self.assertEqual(restore_result["integrity_check"], "ok")
        self.assertEqual(WorkflowStore(restored).get(job["job_id"])["task"], "backup sample task")
        self.assertTrue(queue_status(restored)["healthy"])

    def test_backup_refuses_overwrite_and_source_as_destination(self):
        backup = self.root / "backup.sqlite3"
        _copy_database(self.database, backup)
        with self.assertRaises(ValueError):
            _copy_database(self.database, backup)
        with self.assertRaises(ValueError):
            _copy_database(self.database, self.database)

    def test_failed_backup_removes_reserved_partial_destination(self):
        invalid_source = self.root / "not-a-database.sqlite3"
        invalid_source.write_text("not sqlite", encoding="utf-8")
        destination = self.root / "backups" / "should-not-remain.sqlite3"
        with self.assertRaises(sqlite3.DatabaseError):
            _copy_database(invalid_source, destination)
        self.assertFalse(destination.exists())

    def test_status_reports_queue_ages_and_threshold_alerts(self):
        self.store.enqueue("old queued task", now=100)
        self.store.enqueue("running task", now=120)
        self.store.claim_next(now=125, lease_seconds=10)
        result = queue_status(self.database, now=130)
        self.assertEqual(result["oldest_queued_age_seconds"], 10.0)
        self.assertEqual(result["oldest_running_age_seconds"], 5.0)

        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([
                "status", "--database", str(self.database),
                "--max-queued-age-seconds", "0",
            ])
        self.assertEqual(code, 1)
        payload = json.loads(out.getvalue())
        self.assertIn("queued_job_too_old", payload["alerts"])

    def test_status_can_fail_for_expired_leases_and_terminal_failures(self):
        self.store.enqueue("will fail", now=100, max_attempts=1)
        claimed = self.store.claim_next(now=101, lease_seconds=10)
        self.store.fail(claimed["job_id"], "PermanentError", claim_token=claimed["claim_token"], retryable=False, now=102)
        self.store.enqueue("lease expires", now=103)
        self.store.claim_next(now=104, lease_seconds=1)
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([
                "status", "--database", str(self.database),
                "--fail-on-expired-leases", "--fail-on-failed-jobs",
            ])
        self.assertEqual(code, 1)
        payload = json.loads(out.getvalue())
        self.assertIn("failed_jobs_present", payload["alerts"])
        self.assertIn("expired_leases_present", payload["alerts"])

    def test_status_can_alert_on_running_job_age(self):
        self.store.enqueue("long-running task", now=100)
        self.store.claim_next(now=101, lease_seconds=1000)
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([
                "status", "--database", str(self.database),
                "--max-running-age-seconds", "0",
            ])
        self.assertEqual(code, 1)
        payload = json.loads(out.getvalue())
        self.assertIn("running_job_too_old", payload["alerts"])

    def test_status_rejects_negative_running_age_threshold(self):
        import io
        from contextlib import redirect_stderr
        err = io.StringIO()
        with redirect_stderr(err):
            code = main([
                "status", "--database", str(self.database),
                "--max-running-age-seconds", "-1",
            ])
        self.assertEqual(code, 2)
        self.assertIn("max-running-age-seconds must be non-negative", err.getvalue())

    def test_status_requires_existing_database(self):
        with self.assertRaises(ValueError):
            queue_status(self.root / "missing.sqlite3")

    def test_status_cli_returns_aggregate_json(self):
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["status", "--database", str(self.database)])
        self.assertEqual(code, 0)
        result = json.loads(out.getvalue())
        self.assertTrue(result["healthy"])
        self.assertEqual(result["jobs_by_status"]["queued"], 0)


if __name__ == "__main__":
    unittest.main()
