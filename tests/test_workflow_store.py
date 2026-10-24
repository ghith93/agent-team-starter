import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_team.workflow_store import WorkflowStateError, WorkflowStore


class WorkflowStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "state" / "workflow.sqlite3"
        self.store = WorkflowStore(self.database)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_migrates_existing_database_without_claim_token_column(self):
        legacy_path = Path(self.tempdir.name) / "legacy.sqlite3"
        with sqlite3.connect(legacy_path) as connection:
            connection.execute("""
                CREATE TABLE jobs (
                    job_id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued','running','succeeded','failed')),
                    attempts INTEGER NOT NULL CHECK(attempts >= 0),
                    max_attempts INTEGER NOT NULL CHECK(max_attempts BETWEEN 1 AND 10),
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    available_at REAL NOT NULL,
                    lease_until REAL,
                    result_json TEXT,
                    error_type TEXT
                )
            """)
        migrated = WorkflowStore(legacy_path)
        queued = migrated.enqueue("legacy database task", now=100)
        claimed = migrated.claim_next(now=101)
        self.assertEqual(claimed["job_id"], queued["job_id"])
        self.assertTrue(claimed["claim_token"])
        completed = migrated.complete(
            queued["job_id"], {"ok": True}, claim_token=claimed["claim_token"], now=102
        )
        self.assertEqual(completed["status"], "succeeded")

    def test_requires_explicit_file_path(self):
        with self.assertRaises(ValueError):
            WorkflowStore("")
        with self.assertRaises(ValueError):
            WorkflowStore(":memory:")

    def test_enqueue_claim_complete_survives_reopen(self):
        queued = self.store.enqueue("prepare report", now=100)
        self.assertEqual(queued["status"], "queued")
        claimed = self.store.claim_next(now=101, lease_seconds=30)
        self.assertEqual(claimed["job_id"], queued["job_id"])
        self.assertEqual(claimed["status"], "running")
        self.assertEqual(claimed["attempts"], 1)

        completed = self.store.complete(queued["job_id"], {"summary": "ok"}, claim_token=claimed["claim_token"], now=102)
        self.assertEqual(completed["status"], "succeeded")
        reopened = WorkflowStore(self.database)
        self.assertEqual(reopened.get(queued["job_id"])["result"], {"summary": "ok"})
        self.assertTrue(reopened.health_check())

    def test_does_not_claim_future_job(self):
        self.store.enqueue("later", now=100, available_at=200)
        self.assertIsNone(self.store.claim_next(now=199))

    def test_retry_uses_bounded_backoff_and_attempt_limit(self):
        job = self.store.enqueue("retry me", max_attempts=2, now=100)
        first = self.store.claim_next(now=100)
        retried = self.store.fail(job["job_id"], "ProviderUnavailable", claim_token=first["claim_token"], now=101, base_delay_seconds=7)
        self.assertEqual(retried["status"], "queued")
        self.assertEqual(retried["available_at"], 108)
        self.assertIsNone(self.store.claim_next(now=107))
        second = self.store.claim_next(now=108)
        final = self.store.fail(job["job_id"], "ProviderUnavailable", claim_token=second["claim_token"], now=109)
        self.assertEqual(final["status"], "failed")
        self.assertEqual(final["attempts"], 2)

    def test_non_retryable_failure_is_terminal(self):
        job = self.store.enqueue("do not retry", now=100)
        claimed = self.store.claim_next(now=100)
        failed = self.store.fail(job["job_id"], "InvalidConfiguration", claim_token=claimed["claim_token"], retryable=False, now=101)
        self.assertEqual(failed["status"], "failed")
        self.assertIsNone(self.store.claim_next(now=1000))

    def test_expired_lease_is_recovered_once(self):
        job = self.store.enqueue("recover", max_attempts=2, now=100)
        self.store.claim_next(now=100, lease_seconds=10)
        reclaimed = self.store.claim_next(now=111, lease_seconds=10)
        self.assertEqual(reclaimed["job_id"], job["job_id"])
        self.assertEqual(reclaimed["status"], "running")
        self.assertEqual(reclaimed["attempts"], 2)
        self.store.claim_next(now=122)
        self.assertEqual(self.store.get(job["job_id"])["status"], "failed")

    def test_stale_claim_cannot_complete_or_fail_after_reclaim(self):
        job = self.store.enqueue("stale worker", max_attempts=3, now=100)
        first = self.store.claim_next(now=100, lease_seconds=5)
        second = self.store.claim_next(now=106, lease_seconds=5)
        self.assertNotEqual(first["claim_token"], second["claim_token"])
        with self.assertRaises(WorkflowStateError):
            self.store.complete(job["job_id"], {"wrong": True}, claim_token=first["claim_token"], now=107)
        with self.assertRaises(WorkflowStateError):
            self.store.fail(job["job_id"], "StaleWorker", claim_token=first["claim_token"], now=107)
        completed = self.store.complete(job["job_id"], {"ok": True}, claim_token=second["claim_token"], now=108)
        self.assertEqual(completed["status"], "succeeded")

    def test_lease_renewal_extends_only_the_live_current_claim(self):
        job = self.store.enqueue("heartbeat", now=100)
        claimed = self.store.claim_next(now=100, lease_seconds=10)
        self.assertTrue(self.store.renew_lease(job["job_id"], claimed["claim_token"], lease_seconds=10, now=109))
        self.assertEqual(self.store.get(job["job_id"])["lease_until"], 119)
        self.assertFalse(self.store.renew_lease(job["job_id"], "wrong-token", lease_seconds=10, now=110))
        self.assertIsNone(self.store.claim_next(now=111))

    def test_invalid_transitions_are_rejected(self):
        job = self.store.enqueue("transition", now=100)
        with self.assertRaises(WorkflowStateError):
            self.store.complete(job["job_id"], {"ok": True}, claim_token="stale", now=101)
        with self.assertRaises(WorkflowStateError):
            self.store.fail(job["job_id"], "RuntimeError", claim_token="stale", now=101)
        with self.assertRaises(WorkflowStateError):
            self.store.complete("missing-job", {}, claim_token="missing", now=101)

    def test_rejects_bad_inputs_and_error_messages(self):
        with self.assertRaises(ValueError):
            self.store.enqueue(" ")
        with self.assertRaises(ValueError):
            self.store.enqueue("task", max_attempts=11)
        with self.assertRaises(ValueError):
            self.store.claim_next(lease_seconds=0)
        job = self.store.enqueue("task", now=100)
        claimed = self.store.claim_next(now=100)
        with self.assertRaises(ValueError):
            self.store.fail(job["job_id"], "secret-bearing error message", claim_token=claimed["claim_token"], now=101)

    def test_no_claim_returns_none_when_queue_empty(self):
        self.assertIsNone(self.store.claim_next(now=100))


if __name__ == "__main__":
    unittest.main()
