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

        completed = self.store.complete(queued["job_id"], {"summary": "ok"}, now=102)
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
        retried = self.store.fail(job["job_id"], "ProviderUnavailable", now=101, base_delay_seconds=7)
        self.assertEqual(retried["status"], "queued")
        self.assertEqual(retried["available_at"], 108)
        self.assertIsNone(self.store.claim_next(now=107))
        self.store.claim_next(now=108)
        final = self.store.fail(job["job_id"], "ProviderUnavailable", now=109)
        self.assertEqual(final["status"], "failed")
        self.assertEqual(final["attempts"], 2)

    def test_non_retryable_failure_is_terminal(self):
        job = self.store.enqueue("do not retry", now=100)
        self.store.claim_next(now=100)
        failed = self.store.fail(job["job_id"], "InvalidConfiguration", retryable=False, now=101)
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

    def test_invalid_transitions_are_rejected(self):
        job = self.store.enqueue("transition", now=100)
        with self.assertRaises(WorkflowStateError):
            self.store.complete(job["job_id"], {"ok": True}, now=101)
        with self.assertRaises(WorkflowStateError):
            self.store.fail(job["job_id"], "RuntimeError", now=101)
        with self.assertRaises(WorkflowStateError):
            self.store.complete("missing-job", {}, now=101)

    def test_rejects_bad_inputs_and_error_messages(self):
        with self.assertRaises(ValueError):
            self.store.enqueue(" ")
        with self.assertRaises(ValueError):
            self.store.enqueue("task", max_attempts=11)
        with self.assertRaises(ValueError):
            self.store.claim_next(lease_seconds=0)
        job = self.store.enqueue("task", now=100)
        self.store.claim_next(now=100)
        with self.assertRaises(ValueError):
            self.store.fail(job["job_id"], "secret-bearing error message", now=101)

    def test_no_claim_returns_none_when_queue_empty(self):
        self.assertIsNone(self.store.claim_next(now=100))


if __name__ == "__main__":
    unittest.main()
