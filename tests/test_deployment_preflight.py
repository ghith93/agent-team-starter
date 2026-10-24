import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy" / "systemd" / "preflight-deploy.sh"


class DeploymentPreflightTests(unittest.TestCase):
    def run_preflight(self, *args, env=None):
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            ["bash", str(SCRIPT), *args], cwd=ROOT, env=merged,
            text=True, capture_output=True, check=False, timeout=15,
        )

    def test_default_preflight_is_non_mutating_and_reports_host_checks_skipped(self):
        result = self.run_preflight()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("host checks not requested", result.stdout)
        self.assertIn("Dry-run only", result.stdout)

    def test_rejects_unknown_arguments(self):
        result = self.run_preflight("--not-a-real-option")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown argument", result.stderr)

    def test_rejects_insecure_webhook_without_echoing_value(self):
        with tempfile.TemporaryDirectory() as temp:
            envfile = Path(temp) / "health.env"
            secretish = "http://private.example.invalid/hook?sample=redacted"
            envfile.write_text("ALERT_WEBHOOK_URL=" + secretish + "\n", encoding="utf-8")
            envfile.chmod(0o600)
            result = self.run_preflight("--health-env-file", str(envfile))
            self.assertEqual(result.returncode, 1)
            self.assertIn("ALERT_WEBHOOK_URL is malformed", result.stderr)
            self.assertNotIn(secretish, result.stdout + result.stderr)

    def test_accepts_https_webhook_and_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            envfile = Path(temp) / "health.env"
            envfile.write_text('ALERT_WEBHOOK_URL="https://hooks.example.invalid/path"\n', encoding="utf-8")
            envfile.chmod(0o600)
            result = self.run_preflight("--health-env-file", str(envfile))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("configured webhook uses HTTPS", result.stdout)
            self.assertNotIn("hooks.example.invalid", result.stdout + result.stderr)

    @unittest.skipUnless(os.name == "posix", "POSIX permissions required")
    def test_warns_on_broad_env_file_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            envfile = Path(temp) / "worker.env"
            envfile.write_text("EXAMPLE=value\n", encoding="utf-8")
            envfile.chmod(0o644)
            result = self.run_preflight("--env-file", str(envfile))
            self.assertEqual(result.returncode, 1)
            self.assertIn("permissions are too broad", result.stderr)


if __name__ == "__main__":
    unittest.main()
