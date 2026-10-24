"""Local queue health, backup, and restore helpers; no network access."""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import quote


def _open_readonly(path: Path) -> sqlite3.Connection:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("Database path must be a regular file.")
    uri = "file:" + quote(str(resolved), safe="/:") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _quick_check(connection: sqlite3.Connection) -> bool:
    row = connection.execute("PRAGMA quick_check").fetchone()
    return bool(row and row[0] == "ok")


def queue_status(database: str | Path, *, now: float | None = None) -> dict:
    path = Path(database).expanduser()
    if not path.is_file():
        raise ValueError("Queue database does not exist.")
    current = time.time() if now is None else float(now)
    with closing(_open_readonly(path)) as connection:
        healthy = _quick_check(connection)
        rows = connection.execute("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status").fetchall()
        counts = {row["status"]: row["count"] for row in rows}
        expired = connection.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'running' AND lease_until <= ?",
            (current,),
        ).fetchone()[0]
        oldest_queued = connection.execute(
            "SELECT MIN(created_at) FROM jobs WHERE status = 'queued'"
        ).fetchone()[0]
        oldest_running = connection.execute(
            "SELECT MIN(updated_at) FROM jobs WHERE status = 'running'"
        ).fetchone()[0]
    return {
        "database": str(path.resolve()),
        "healthy": healthy,
        "jobs_by_status": {key: counts.get(key, 0) for key in ("queued", "running", "succeeded", "failed")},
        "expired_leases": expired,
        "oldest_queued_age_seconds": max(0.0, round(current - oldest_queued, 3)) if oldest_queued is not None else None,
        "oldest_running_age_seconds": max(0.0, round(current - oldest_running, 3)) if oldest_running is not None else None,
    }


def _copy_database(source: Path, destination: Path) -> dict:
    source = source.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve(strict=False)
    if not source.is_file():
        raise ValueError("Source must be a regular file.")
    if source == destination:
        raise ValueError("Source and destination must differ.")
    if destination.exists():
        raise ValueError("Destination already exists; refusing to overwrite it.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the destination atomically so concurrent invocations cannot
    # overwrite a file created after the existence check (TOCTOU).
    reservation_fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(reservation_fd)
    try:
        with closing(_open_readonly(source)) as src:
            with closing(sqlite3.connect(str(destination), timeout=5.0)) as dst:
                src.backup(dst)
        with closing(sqlite3.connect(str(destination), timeout=5.0)) as check:
            healthy = _quick_check(check)
        if not healthy:
            raise sqlite3.DatabaseError("Copied database failed integrity check.")
        if os.name == "posix":
            os.chmod(destination, 0o600)
        return {"ok": True, "source": str(source), "destination": str(destination), "integrity_check": "ok"}
    except Exception:
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect, back up, or restore a local agent-team queue database.")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="Read health and aggregate job counts only")
    status.add_argument("--database", type=Path, required=True)
    status.add_argument("--fail-on-expired-leases", action="store_true",
                        help="Return exit code 1 when any worker lease has expired")
    status.add_argument("--fail-on-failed-jobs", action="store_true",
                        help="Return exit code 1 when any job is terminally failed")
    status.add_argument("--max-queued-age-seconds", type=float,
                        help="Return exit code 1 when the oldest queued job exceeds this age")
    backup = commands.add_parser("backup", help="Create a consistent SQLite backup without overwriting files")
    backup.add_argument("--database", type=Path, required=True)
    backup.add_argument("--destination", type=Path, required=True)
    restore = commands.add_parser("restore", help="Restore a backup into a new database path")
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--destination", type=Path, required=True)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "status":
            if args.max_queued_age_seconds is not None and args.max_queued_age_seconds < 0:
                raise ValueError("max-queued-age-seconds must be non-negative.")
            result = queue_status(args.database)
            alerts = []
            if not result["healthy"]:
                alerts.append("database_unhealthy")
            if args.fail_on_expired_leases and result["expired_leases"]:
                alerts.append("expired_leases_present")
            if args.fail_on_failed_jobs and result["jobs_by_status"]["failed"]:
                alerts.append("failed_jobs_present")
            oldest_age = result["oldest_queued_age_seconds"]
            if (args.max_queued_age_seconds is not None and oldest_age is not None
                    and oldest_age > args.max_queued_age_seconds):
                alerts.append("queued_job_too_old")
            result["alerts"] = alerts
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if alerts else 0
        if args.command == "backup":
            result = _copy_database(args.database, args.destination)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        result = _copy_database(args.backup, args.destination)
        result["restored_from"] = result.pop("source")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
