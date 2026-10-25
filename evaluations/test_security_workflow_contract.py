"""Regression checks for essential GitHub Actions security workflow properties.

These are intentionally dependency-free text-contract checks, not a full YAML
schema validator and not a simulation of GitHub Actions execution.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security.yml"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


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
        self.assertIn('test "$BANDIT_OUTCOME" = success', self.text)
        self.assertIn('test "$DETECT_SECRETS_GATE_OUTCOME" = success', self.text)

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
        self.assertNotRegex(self.text, r"uses:\s+actions/(?:checkout|setup-python|upload-artifact)@v\d+")
        self.assertNotRegex(self.text, r"uses:\s+gitleaks/gitleaks-action@v\d+")

    @staticmethod
    def _permission_blocks(source):
        """Return workflow/job permission maps without requiring a YAML package."""
        lines = source.splitlines()
        blocks = []
        for index, line in enumerate(lines):
            match = re.match(r"^(\s*)permissions:\s*(.*?)\s*(?:#.*)?$", line)
            if not match:
                continue
            indent = len(match.group(1))
            inline = match.group(2).strip()
            if inline:
                blocks.append([("<inline>", inline)])
                continue
            entries = []
            for child in lines[index + 1:]:
                if not child.strip() or child.lstrip().startswith("#"):
                    continue
                child_indent = len(child) - len(child.lstrip())
                if child_indent <= indent:
                    break
                if child_indent != indent + 2:
                    continue
                entry = re.match(r"^\s*([a-z-]+):\s*([^\s#]+)", child)
                if entry:
                    entries.append((entry.group(1), entry.group(2)))
            blocks.append(entries)
        return blocks

    def test_all_workflows_and_job_permissions_are_read_only(self):
        workflows = sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))
        self.assertTrue(workflows, "expected workflow files to audit")
        for path in workflows:
            with self.subTest(workflow=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("pull_request_target:", source)
                self.assertRegex(
                    source,
                    r"(?m)^permissions:\n(?:  [^\n]*\n)*  contents: read(?:\n|$)",
                    "workflow must declare top-level contents: read permissions",
                )
                for block_index, entries in enumerate(self._permission_blocks(source)):
                    with self.subTest(workflow=path.name, permission_block=block_index):
                        for permission, level in entries:
                            self.assertIn(
                                level,
                                ("read", "none"),
                                f"{permission} permission must not grant write access",
                            )

    def test_permission_contract_rejects_write_scopes(self):
        fixtures = (
            "permissions:\n  contents: read\n  actions: write\n",
            "permissions:\n  contents: read\njobs:\n  test:\n    permissions:\n      pull-requests: write\n",
            "permissions: write-all\n",
        )
        for source in fixtures:
            with self.subTest(source=source):
                self.assertTrue(
                    any(level not in ("read", "none") for block in self._permission_blocks(source) for _, level in block)
                )

    def test_all_external_actions_are_pinned_to_full_commit_shas(self):
        workflows = sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))
        action_refs = []
        for path in workflows:
            source = path.read_text(encoding="utf-8")
            action_refs.extend(
                (path.name, ref)
                for ref in re.findall(r"(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)", source)
                if not ref.startswith("./")
            )
        self.assertTrue(action_refs, "expected external action references to audit")
        for workflow, ref in action_refs:
            with self.subTest(workflow=workflow, action=ref):
                self.assertRegex(
                    ref,
                    r"^[^@]+@[0-9a-f]{40}$",
                    "external GitHub Actions must be pinned to immutable full commit SHAs",
                )

    def test_live_provider_workflow_is_manual_and_explicitly_gated(self):
        source = (WORKFLOWS_DIR / "openrouter-smoke.yml").read_text(encoding="utf-8")
        trigger_block = source.split("\npermissions:", 1)[0]
        self.assertIn("workflow_dispatch:", trigger_block)
        self.assertNotRegex(trigger_block, r"(?m)^  (?:push|pull_request|schedule):")
        self.assertIn("confirm_live_provider_calls:", trigger_block)
        self.assertIn("default: false", trigger_block)
        self.assertIn("if: inputs.confirm_live_provider_calls == true", source)


    def test_required_isolated_audit_runs_on_every_pull_request_to_main(self):
        source = (WORKFLOWS_DIR / "security-audit-isolated.yml").read_text(encoding="utf-8")
        trigger_block = source.split("\\npermissions:", 1)[0]
        match = re.search(
            r"(?ms)^  pull_request:\\n(.*?)(?=^  [A-Za-z_][\\w-]*:|\\Z)",
            trigger_block,
        )
        self.assertIsNotNone(match, "isolated security audit must run on pull requests")
        pull_request_block = match.group(1)
        self.assertRegex(
            pull_request_block,
            r"(?m)^    branches:\\s*\\[main\\]\\s*$",
            "the required audit should be scoped to pull requests targeting main",
        )
        self.assertNotRegex(
            pull_request_block,
            r"(?m)^    paths(?:-ignore)?:",
            "path filters can leave required checks pending on docs-only pull requests",
        )


if __name__ == "__main__":
    unittest.main()
