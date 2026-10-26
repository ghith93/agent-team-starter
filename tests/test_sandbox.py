import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_team.sandbox import run_sandboxed_command


class SandboxTests(unittest.TestCase):
    def test_no_docker_fails_closed_without_host_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "candidate").mkdir()
            (root / "trusted").mkdir()
            with patch("agent_team.sandbox.shutil.which", return_value=None):
                with patch("agent_team.sandbox.subprocess.run") as run:
                    result = run_sandboxed_command(
                        root / "candidate", root / "trusted",
                        ("python", "-m", "unittest", "discover", "-v"),
                        "unittest", 10,
                    )
        self.assertFalse(result.passed)
        self.assertIn("Docker is required", result.output)
        run.assert_not_called()

    def test_rejects_unsafe_requirements_before_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, trusted = root / "candidate", root / "trusted"
            candidate.mkdir(); trusted.mkdir()
            (trusted / "requirements.txt").write_text("--extra-index-url https://example.invalid/simple\n", encoding="utf-8")
            with patch("agent_team.sandbox.shutil.which", return_value="/usr/bin/docker"):
                with patch("agent_team.sandbox.subprocess.run") as run:
                    result = run_sandboxed_command(candidate, trusted, ("python", "run_tests.py"), "project-tests", 10)
        self.assertFalse(result.passed)
        self.assertIn("unsupported dependency syntax", result.output)
        run.assert_not_called()

    def test_container_is_network_disabled_and_resource_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, trusted = root / "candidate", root / "trusted"
            candidate.mkdir(); trusted.mkdir()
            (trusted / "requirements.txt").write_text("requests>=2.31.0\n", encoding="utf-8")
            results = [
                subprocess.CompletedProcess(["docker", "build"], 0, ""),
                subprocess.CompletedProcess(["docker", "run"], 0, "all tests passed"),
                subprocess.CompletedProcess(["docker", "rm"], 0, ""),
                subprocess.CompletedProcess(["docker", "image", "rm"], 0, ""),
            ]
            with patch("agent_team.sandbox.shutil.which", return_value="/usr/bin/docker"):
                with patch("agent_team.sandbox.subprocess.run", side_effect=results) as run:
                    result = run_sandboxed_command(
                        candidate, trusted, ("python", "run_tests.py"), "project-tests", 30,
                    )
        self.assertTrue(result.passed)
        self.assertIn("all tests passed", result.output)
        run_args = run.call_args_list[1].args[0]
        self.assertIn("--network", run_args)
        self.assertIn("none", run_args)
        self.assertIn("--read-only", run_args)
        self.assertIn("--cap-drop=ALL", run_args)
        self.assertIn("--security-opt=no-new-privileges", run_args)
        self.assertIn("--pids-limit=128", run_args)
        self.assertNotIn("OPENROUTER_API_KEY", run.call_args_list[1].kwargs["env"])

    def test_test_output_redacts_credential_like_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, trusted = root / "candidate", root / "trusted"
            candidate.mkdir(); trusted.mkdir()
            (trusted / "requirements.txt").write_text("", encoding="utf-8")
            results = [
                subprocess.CompletedProcess(["docker", "build"], 0, ""),
                subprocess.CompletedProcess(["docker", "run"], 1, "api_key=secret-value-123456"),
                subprocess.CompletedProcess(["docker", "rm"], 0, ""),
                subprocess.CompletedProcess(["docker", "image", "rm"], 0, ""),
            ]
            with patch("agent_team.sandbox.shutil.which", return_value="/usr/bin/docker"):
                with patch("agent_team.sandbox.subprocess.run", side_effect=results):
                    result = run_sandboxed_command(
                        candidate, trusted, ("python", "run_tests.py"), "project-tests", 30,
                    )
        self.assertFalse(result.passed)
        self.assertNotIn("secret-value-123456", result.output)
        self.assertIn("[REDACTED]", result.output)


if __name__ == "__main__":
    unittest.main()
