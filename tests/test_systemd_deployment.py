"""Regression checks for optional systemd deployment templates and health logic."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from agent_team.queue_admin import _copy_database
from agent_team.workflow_store import WorkflowStore


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy" / "systemd"


class SystemdDeploymentTemplateTests(unittest.TestCase):
    def test_worker_is_supervised_and_hardened(self):
        unit = (DEPLOY / "agent-team-worker.service").read_text(encoding="utf-8")
        for required in (
            "Type=simple",
            "User=agent-team",
            "Restart=on-failure",
            "RestartSec=10s",
            "StartLimitBurst=5",
            "MemoryMax=1G",
            "CPUQuota=100%",
            "TasksMax=64",
            "UMask=0077",
            "NoNewPrivileges=true",
            "ProtectSystem=strict",
            "ProtectHome=true",
            "StateDirectory=agent-team",
            "EnvironmentFile=/etc/agent-team/worker.env",
            "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
        ):
            with self.subTest(directive=required):
                self.assertIn(required, unit)

    def test_backup_timer_is_persistent_and_uses_oneshot_service(self):
        service = (DEPLOY / "agent-team-queue-backup.service").read_text(encoding="utf-8")
        timer = (DEPLOY / "agent-team-queue-backup.timer").read_text(encoding="utf-8")
        script = (DEPLOY / "backup-queue.sh").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", service)
        self.assertIn("UMask=0077", service)
        self.assertIn("OnCalendar=daily", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("flock -n 9", script)
        self.assertIn("queue_admin backup", script)
        self.assertIn("Apply retention only after a new backup has passed its integrity check", script)
        self.assertIn("RETENTION_DAYS", script)

    def test_restore_test_timer_is_daily_and_uses_isolated_temporary_restore(self):
        service = (DEPLOY / "agent-team-queue-restore-test.service").read_text(encoding="utf-8")
        timer = (DEPLOY / "agent-team-queue-restore-test.timer").read_text(encoding="utf-8")
        script = (DEPLOY / "test-queue-restore.sh").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", service)
        self.assertIn("OnCalendar=daily", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("mktemp -d", script)
        self.assertIn("queue_admin restore", script)
        self.assertIn("queue_admin status", script)
        self.assertIn("trap", script)
        self.assertIn("QUEUE_DB", script)

    def test_restore_test_script_restores_latest_backup_and_cleans_temp_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "queue.sqlite3"
            WorkflowStore(database)
            backup_dir = root / "backups"
            backup_dir.mkdir()
            _copy_database(database, backup_dir / "queue-test.sqlite3")
            env = os.environ.copy()
            env.update({
                "APP_DIR": str(ROOT), "PYTHON": sys.executable, "PYTHONPATH": str(ROOT),
                "QUEUE_DB": str(database), "BACKUP_DIR": str(backup_dir),
                "RESTORE_TEST_DIR": str(root / "restore-test"),
            })
            result = subprocess.run(["bash", str(DEPLOY / "test-queue-restore.sh")],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Restore test passed", result.stdout)
            self.assertEqual(list((root / "restore-test").glob("*")), [])

    def test_restore_test_script_fails_when_no_backup_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "queue.sqlite3"
            WorkflowStore(database)
            backup_dir = root / "backups"
            backup_dir.mkdir()
            env = os.environ.copy()
            env.update({
                "APP_DIR": str(ROOT), "PYTHON": sys.executable, "PYTHONPATH": str(ROOT),
                "QUEUE_DB": str(database), "BACKUP_DIR": str(backup_dir),
                "RESTORE_TEST_DIR": str(root / "restore-test"),
            })
            result = subprocess.run(["bash", str(DEPLOY / "test-queue-restore.sh")],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=15)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("no queue backup was found", result.stderr)

    def test_alert_wrapper_sends_generic_webhook_only_on_health_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            check = root / "check.sh"
            check.write_text('#!/usr/bin/env bash\necho "private task text must not be forwarded"\nexit 1\n', encoding="utf-8")
            curl = root / "curl"
            capture = root / "curl-args.txt"
            curl.write_text(
                '#!/usr/bin/env bash\nprintf "%s\n" "$@" > "$CURL_CAPTURE"\nexit 0\n',
                encoding="utf-8",
            )
            check.chmod(0o700)
            curl.chmod(0o700)
            env = os.environ.copy()
            env.update({
                "HEALTH_CHECK_SCRIPT": str(check),
                "CURL_BIN": str(curl),
                "CURL_CAPTURE": str(capture),
                "ALERT_WEBHOOK_URL": "https://alerts.example.test/hook",
            })
            result = subprocess.run(
                ["bash", str(DEPLOY / "run-queue-health-with-alert.sh")],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=10,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            args = capture.read_text(encoding="utf-8")
            self.assertIn("https://alerts.example.test/hook", args)
            self.assertIn("Agent Team queue health check failed", args)
            self.assertNotIn("private task text", args)

    def test_alert_wrapper_does_not_send_on_success_and_rejects_non_https(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            check = root / "check.sh"
            check.write_text('#!/usr/bin/env bash\nexit 0\n', encoding="utf-8")
            curl = root / "curl"
            capture = root / "curl-called"
            curl.write_text('#!/usr/bin/env bash\ntouch "$CURL_CAPTURE"\n', encoding="utf-8")
            check.chmod(0o700)
            curl.chmod(0o700)
            env = os.environ.copy()
            env.update({
                "HEALTH_CHECK_SCRIPT": str(check), "CURL_BIN": str(curl),
                "CURL_CAPTURE": str(capture), "ALERT_WEBHOOK_URL": "http://insecure.example.test/hook",
            })
            result = subprocess.run(
                ["bash", str(DEPLOY / "run-queue-health-with-alert.sh")],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(capture.exists())
            check.write_text('#!/usr/bin/env bash\nexit 1\n', encoding="utf-8")
            result = subprocess.run(
                ["bash", str(DEPLOY / "run-queue-health-with-alert.sh")],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=10,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("requires an HTTPS URL", result.stderr)
            self.assertFalse(capture.exists())

    def test_health_monitor_is_scheduled_and_checks_queue_and_backup_integrity(self):
        service = (DEPLOY / "agent-team-queue-health.service").read_text(encoding="utf-8")
        timer = (DEPLOY / "agent-team-queue-health.timer").read_text(encoding="utf-8")
        script = (DEPLOY / "check-queue-health.sh").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", service)
        self.assertIn("OnCalendar=*-*-* *:0/5:00", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("--fail-on-expired-leases", script)
        self.assertIn("--max-queued-age-seconds", script)
        self.assertIn("--max-running-age-seconds", script)
        self.assertIn("MAX_BACKUP_AGE_SECONDS", script)
        self.assertIn("no queue backup was found", script)
        self.assertIn("latest queue backup exceeds the configured age threshold", script)
        self.assertIn("latest queue backup cannot be opened or failed its integrity check", script)
        self.assertIn("queue_admin status --database", script)
        self.assertIn("flock -n 9", script)

    def _run_health_check(self, root: Path, backup_age_seconds: int = 172800) -> subprocess.CompletedProcess:
        database = root / "queue.sqlite3"
        WorkflowStore(database)
        backup_dir = root / "backups"
        backup_dir.mkdir(exist_ok=True)
        env = os.environ.copy()
        env.update({
            "APP_DIR": str(ROOT),
            "PYTHON": sys.executable,
            "PYTHONPATH": str(ROOT),
            "QUEUE_DB": str(database),
            "BACKUP_DIR": str(backup_dir),
            "LOCK_DIR": str(root / "locks"),
            "MAX_BACKUP_AGE_SECONDS": str(backup_age_seconds),
        })
        return subprocess.run(
            ["bash", str(DEPLOY / "check-queue-health.sh")],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

    def test_health_check_accepts_recent_readable_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "queue.sqlite3"
            WorkflowStore(database)
            backup_dir = root / "backups"
            backup_dir.mkdir()
            _copy_database(database, backup_dir / "queue-current.sqlite3")
            result = self._run_health_check_existing(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("latest queue backup is recent and readable", result.stdout)

    def test_health_check_rejects_missing_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self._run_health_check(Path(temp))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("no queue backup was found", result.stderr)

    def test_health_check_rejects_corrupt_latest_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self._run_health_check(root)
            self.assertEqual(result.returncode, 1)
            backup = root / "backups" / "queue-corrupt.sqlite3"
            backup.write_text("not a SQLite database", encoding="utf-8")
            result = self._run_health_check_existing(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("cannot be opened or failed its integrity check", result.stderr)

    def test_health_check_rejects_stale_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "queue.sqlite3"
            WorkflowStore(database)
            backup_dir = root / "backups"
            backup_dir.mkdir()
            _copy_database(database, backup_dir / "queue-old.sqlite3")
            old = time.time() - 120
            os.utime(backup_dir / "queue-old.sqlite3", (old, old))
            result = self._run_health_check_existing(root, backup_age_seconds=1)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("exceeds the configured age threshold", result.stderr)

    def _run_health_check_existing(self, root: Path, backup_age_seconds: int = 172800) -> subprocess.CompletedProcess:
        database = root / "queue.sqlite3"
        backup_dir = root / "backups"
        env = os.environ.copy()
        env.update({
            "APP_DIR": str(ROOT),
            "PYTHON": sys.executable,
            "PYTHONPATH": str(ROOT),
            "QUEUE_DB": str(database),
            "BACKUP_DIR": str(backup_dir),
            "LOCK_DIR": str(root / "locks"),
            "MAX_BACKUP_AGE_SECONDS": str(backup_age_seconds),
        })
        return subprocess.run(
            ["bash", str(DEPLOY / "check-queue-health.sh")],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

    def test_worker_does_not_enable_unsafe_unbounded_privileges(self):
        unit = (DEPLOY / "agent-team-worker.service").read_text(encoding="utf-8")
        self.assertIn("CapabilityBoundingSet=", unit)
        self.assertIn("AmbientCapabilities=", unit)
        self.assertIn("RestrictSUIDSGID=true", unit)
        self.assertNotIn("Privileged=true", unit)
        self.assertNotIn("User=root", unit)


if __name__ == "__main__":
    unittest.main()
