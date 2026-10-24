"""Static regression checks for the optional systemd deployment templates."""
from pathlib import Path
import unittest


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

    def test_health_monitor_is_scheduled_and_uses_thresholds(self):
        service = (DEPLOY / "agent-team-queue-health.service").read_text(encoding="utf-8")
        timer = (DEPLOY / "agent-team-queue-health.timer").read_text(encoding="utf-8")
        script = (DEPLOY / "check-queue-health.sh").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", service)
        self.assertIn("OnCalendar=*-*-* *:0/5:00", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("--fail-on-expired-leases", script)
        self.assertIn("--max-queued-age-seconds", script)
        self.assertIn("--max-running-age-seconds", script)
        self.assertIn("flock -n 9", script)

    def test_worker_does_not_enable_unsafe_unbounded_privileges(self):
        unit = (DEPLOY / "agent-team-worker.service").read_text(encoding="utf-8")
        self.assertIn("CapabilityBoundingSet=", unit)
        self.assertIn("AmbientCapabilities=", unit)
        self.assertIn("RestrictSUIDSGID=true", unit)
        self.assertNotIn("Privileged=true", unit)
        self.assertNotIn("User=root", unit)


if __name__ == "__main__":
    unittest.main()
