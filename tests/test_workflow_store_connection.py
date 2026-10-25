"""Regression tests for SQLite connection lifecycle in WorkflowStore."""
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_team.workflow_store import WorkflowStore


class WorkflowStoreConnectionTests(unittest.TestCase):
    def test_database_permissions_are_owner_only(self):
        if os.name != "posix":
            self.skipTest("POSIX file permission semantics required")
        with tempfile.TemporaryDirectory() as tempdir:
            database = Path(tempdir) / "private.sqlite3"
            WorkflowStore(database)
            self.assertEqual(stat.S_IMODE(database.stat().st_mode), 0o600)

    def test_public_operations_close_every_connection(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = WorkflowStore(Path(tempdir) / "queue.sqlite3")
            original_connect = sqlite3.connect
            opened = []

            def tracking_connect(*args, **kwargs):
                connection = original_connect(*args, **kwargs)
                opened.append(connection)
                return connection

            with patch("agent_team.workflow_store.sqlite3.connect", side_effect=tracking_connect):
                first = store.enqueue("first task", now=100)
                claimed = store.claim_next(now=101)
                store.complete(claimed["job_id"], {"ok": True}, claim_token=claimed["claim_token"], now=102)
                second = store.enqueue("second task", now=103)
                claimed_second = store.claim_next(now=104)
                store.fail(claimed_second["job_id"], "TemporaryError", claim_token=claimed_second["claim_token"], now=105)
                store.get(first["job_id"])
                store.health_check()

            self.assertGreaterEqual(len(opened), 7)
            for connection in opened:
                with self.subTest(connection=connection):
                    with self.assertRaises(sqlite3.ProgrammingError):
                        connection.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
