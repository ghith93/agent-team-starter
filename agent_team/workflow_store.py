"""SQLite-backed, opt-in durable queue primitives for local workflows.

This module performs no scheduling, network calls, or task execution by itself.
Callers must explicitly create a store and decide what task/result data to persist.
"""
from __future__ import annotations

import json
import os
import stat
from contextlib import closing
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


_ERROR_TYPE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,79}$")
_MAX_ATTEMPTS = 10
_MAX_LEASE_SECONDS = 86400
_MAX_BACKOFF_SECONDS = 3600


class WorkflowStateError(RuntimeError):
    """Raised when a job transition is invalid or a job does not exist."""


def _prepare_private_database(path: Path) -> None:
    """Create or tighten a SQLite file before opening it; reject symlinks/non-files."""
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("SQLite database path must be a regular file, not a symlink or special file.")
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        else:
            os.chmod(path, 0o600)
    finally:
        os.close(descriptor)


class WorkflowStore:
    """Persist jobs in a caller-selected local SQLite database.

    The database is plaintext. Do not persist credentials, private customer data,
    or sensitive prompts/results. Keep the database outside version control and
    use an explicit, durable path; this class intentionally has no implicit default.
    """

    def __init__(self, database_path: str | Path):
        if database_path is None or not str(database_path).strip():
            raise ValueError("An explicit database path is required.")
        self.path = Path(database_path).expanduser()
        if str(database_path) == ":memory:":
            raise ValueError("Use a file-backed database so state survives reconnects.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _prepare_private_database(self.path)
        with closing(self._connect()) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
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
                    claim_token TEXT,
                    error_type TEXT
                )
            """)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(jobs)")}
            if "claim_token" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN claim_token TEXT")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS jobs_ready_idx ON jobs(status, available_at, created_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS jobs_lease_idx ON jobs(status, lease_until)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @staticmethod
    def _job(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json")) if item["result_json"] is not None else None
        return item

    def enqueue(self, task: str, *, max_attempts: int = 3, available_at: float | None = None,
                now: float | None = None) -> dict[str, Any]:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Task must be a non-empty string.")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= _MAX_ATTEMPTS:
            raise ValueError(f"max_attempts must be an integer from 1 to {_MAX_ATTEMPTS}.")
        current = time.time() if now is None else float(now)
        ready_at = current if available_at is None else float(available_at)
        job_id = str(uuid.uuid4())
        with closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO jobs
                   (job_id, task, status, attempts, max_attempts, created_at, updated_at,
                    available_at, lease_until, result_json, error_type)
                   VALUES (?, ?, 'queued', 0, ?, ?, ?, ?, NULL, NULL, NULL)""",
                (job_id, task.strip(), max_attempts, current, current, ready_at),
            )
            return self._job(connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone())

    def claim_next(self, *, lease_seconds: int = 300, now: float | None = None) -> dict[str, Any] | None:
        if not isinstance(lease_seconds, int) or isinstance(lease_seconds, bool) or not 1 <= lease_seconds <= _MAX_LEASE_SECONDS:
            raise ValueError(f"lease_seconds must be an integer from 1 to {_MAX_LEASE_SECONDS}.")
        current = time.time() if now is None else float(now)
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                # Recover abandoned workers. Exhausted jobs become terminal failures.
                connection.execute(
                    """UPDATE jobs
                       SET status = CASE WHEN attempts >= max_attempts THEN 'failed' ELSE 'queued' END,
                           available_at = ?, lease_until = NULL, updated_at = ?, claim_token = NULL,
                           error_type = CASE WHEN attempts >= max_attempts
                                             THEN COALESCE(error_type, 'LeaseExpired') ELSE error_type END
                       WHERE status = 'running' AND lease_until <= ?""",
                    (current, current, current),
                )
                row = connection.execute(
                    """SELECT * FROM jobs
                       WHERE status = 'queued' AND available_at <= ?
                       ORDER BY available_at, created_at, job_id LIMIT 1""",
                    (current,),
                ).fetchone()
                if row is None:
                    connection.execute("COMMIT")
                    return None
                claim_token = str(uuid.uuid4())
                connection.execute(
                    """UPDATE jobs SET status = 'running', attempts = attempts + 1,
                       lease_until = ?, updated_at = ?, error_type = NULL, claim_token = ?
                       WHERE job_id = ? AND status = 'queued'""",
                    (current + lease_seconds, current, claim_token, row["job_id"]),
                )
                claimed = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (row["job_id"],)).fetchone()
                connection.execute("COMMIT")
                return self._job(claimed)
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def complete(self, job_id: str, result: Any, *, claim_token: str, now: float | None = None) -> dict[str, Any]:
        current = time.time() if now is None else float(now)
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT status, claim_token, lease_until FROM jobs WHERE job_id = ?", (job_id,)
                ).fetchone()
                if row is None:
                    raise WorkflowStateError("Job not found.")
                if row["status"] != "running":
                    raise WorkflowStateError("Only a running job can be completed.")
                if row["claim_token"] != claim_token:
                    raise WorkflowStateError("Claim token mismatch; stale worker cannot complete job.")
                if row["lease_until"] is None or row["lease_until"] <= current:
                    raise WorkflowStateError("Job lease expired; stale worker cannot complete job.")
                connection.execute(
                    """UPDATE jobs SET status = 'succeeded', result_json = ?, lease_until = NULL,
                       error_type = NULL, claim_token = NULL, updated_at = ?
                       WHERE job_id = ? AND status = 'running' AND claim_token = ?""",
                    (encoded, current, job_id, claim_token),
                )
                updated = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
                connection.execute("COMMIT")
                return self._job(updated)
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def fail(self, job_id: str, error_type: str, *, claim_token: str, retryable: bool = True,
             base_delay_seconds: float = 5.0, now: float | None = None) -> dict[str, Any]:
        if not isinstance(error_type, str) or not _ERROR_TYPE.fullmatch(error_type):
            raise ValueError("error_type must be a short exception/type name, not an error message.")
        if base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must be non-negative.")
        current = time.time() if now is None else float(now)
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
                if row is None:
                    raise WorkflowStateError("Job not found.")
                if row["status"] != "running":
                    raise WorkflowStateError("Only a running job can fail.")
                if row["claim_token"] != claim_token:
                    raise WorkflowStateError("Claim token mismatch; stale worker cannot fail job.")
                if row["lease_until"] is None or row["lease_until"] <= current:
                    raise WorkflowStateError("Job lease expired; stale worker cannot fail job.")
                should_retry = bool(retryable) and row["attempts"] < row["max_attempts"]
                if should_retry:
                    delay = min(_MAX_BACKOFF_SECONDS, float(base_delay_seconds) * (2 ** (row["attempts"] - 1)))
                    connection.execute(
                        """UPDATE jobs SET status = 'queued', available_at = ?, lease_until = NULL, claim_token = NULL,
                           error_type = ?, updated_at = ? WHERE job_id = ? AND claim_token = ?""",
                        (current + delay, error_type, current, job_id, claim_token),
                    )
                else:
                    connection.execute(
                        """UPDATE jobs SET status = 'failed', lease_until = NULL, claim_token = NULL,
                           error_type = ?, updated_at = ? WHERE job_id = ? AND claim_token = ?""",
                        (error_type, current, job_id, claim_token),
                    )
                updated = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
                connection.execute("COMMIT")
                return self._job(updated)
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def renew_lease(self, job_id: str, claim_token: str, *, lease_seconds: int = 300,
                    now: float | None = None) -> bool:
        """Extend a live lease only for its current claimant; never revive an expired lease."""
        if not isinstance(lease_seconds, int) or isinstance(lease_seconds, bool) or not 1 <= lease_seconds <= _MAX_LEASE_SECONDS:
            raise ValueError(f"lease_seconds must be an integer from 1 to {_MAX_LEASE_SECONDS}.")
        current = time.time() if now is None else float(now)
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """UPDATE jobs SET lease_until = ?
                   WHERE job_id = ? AND status = 'running' AND claim_token = ? AND lease_until > ?""",
                (current + lease_seconds, job_id, claim_token, current),
            )
            return cursor.rowcount == 1

    def get(self, job_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            return self._job(connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone())

    def health_check(self) -> bool:
        """Return whether SQLite can execute a trivial read; no secrets or row data returned."""
        with closing(self._connect()) as connection:
            row = connection.execute("PRAGMA quick_check").fetchone()
            return bool(row and row[0] == "ok")
