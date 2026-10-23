"""Regression checks for essential GitHub Actions security workflow properties.

These are intentionally dependency-free text-contract checks, not a full YAML
schema validator and not a simulation of GitHub Actions execution.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security.yml"


class SecurityWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_expected_triggers_exist(self):
        for trigger in ("push:", "pull_request:", "workflow_dispatch:", "schedule:"):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, self.text)

    def test_top_level_permissions_are_read_only(self):
        self.assertRegex(self.text, r"(?m)^permissions:\n  contents: read\s*$")

    def test_required_jobs_exist(self):
        for job in ("tests:", "python-security:", "gitleaks:"):
            with self.subTest(job=job):
                self.assertRegex(self.text, rf"(?m)^  {re.escape(job)}")

    def test_scanner_steps_and_explicit_fail_closed_gate_exist(self):
        for marker in (
            "bandit -r agent_team",
            "pip-audit -r requirements.txt",
            "semgrep scan --error",
            "detect-secrets scan --all-files",
            "Fail if detect-secrets found candidates",
            "Enforce scan outcomes",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)
        self.assertIn("test \"$BANDIT_OUTCOME\" = success", self.text)
        self.assertIn("test \"$DETECT_SECRETS_GATE_OUTCOME\" = success", self.text)

    def test_reports_are_uploaded_even_after_failure(self):
        self.assertGreaterEqual(self.text.count("if: always()"), 3)
        self.assertIn("name: offline-test-reports", self.text)
        self.assertIn("name: python-security-reports", self.text)

    def test_gitleaks_scans_full_history_without_pr_comments(self):
        self.assertIn("fetch-depth: 0", self.text)
        self.assertIn("gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e", self.text)
        self.assertIn('GITLEAKS_ENABLE_COMMENTS: "false"', self.text)

    def test_checkout_major_is_currently_configured_as_v7(self):
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", self.text)
        self.assertIn("actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0", self.text)
        self.assertIn("actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9", self.text)
        self.assertNotRegex(self.text, r"uses:\\s+actions/(?:checkout|setup-python|upload-artifact)@v\\d+")
        self.assertNotRegex(self.text, r"uses:\\s+gitleaks/gitleaks-action@v\\d+")


if __name__ == "__main__":
    unittest.main()
