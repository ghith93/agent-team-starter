"""Regression tests for narrow detect-secrets line exclusions.

Uses inert placeholders only; no valid credentials are embedded or committed.
"""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security.yml"


class SecretScanExclusionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(r"--exclude-lines '([^']*)'", source)
        if match is None:
            raise AssertionError("security workflow must define explicit --exclude-lines")
        cls.pattern = re.compile(match.group(1))

    def test_known_non_secret_examples_are_excluded(self):
        fixtures = (
            "https://user:pass@example.com",
            "http://user:secret@proxy.example:8080",
            "Prefer Colab's notebook setup GEMINI_API_KEY OPENROUTER_API_KEY",
            "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "ref: 3d3c42e5aac5ba805825da76410c181273ba90b1",
        )
        for line in fixtures:
            with self.subTest(line=line):
                self.assertRegex(line, self.pattern)

    def test_provider_key_lines_are_not_excluded(self):
        # Intentionally inert values: these are not valid provider credentials.
        candidates = (
            "GEMINI_API_KEY=AIzaSyDUMMY_NOT_A_REAL_KEY",
            "OPENROUTER_API_KEY=sk-or-v1-DUMMY_NOT_A_REAL_KEY",
            "export GEMINI_API_KEY=placeholder OPENROUTER_API_KEY=placeholder",
        )
        for line in candidates:
            with self.subTest(line=line):
                self.assertIsNone(
                    self.pattern.search(line),
                    "provider-key line was accidentally excluded from secret scanning",
                )

    def test_action_sha_exclusion_is_limited_to_immutable_refs(self):
        self.assertRegex(
            "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            self.pattern,
        )
        self.assertIsNone(self.pattern.search("uses: actions/checkout@v4"))
        self.assertIsNone(self.pattern.search("uses: attacker/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"))

    def test_isolated_security_audit_actions_are_immutable(self):
        audit_workflow = ROOT / ".github" / "workflows" / "security-audit-isolated.yml"
        source = audit_workflow.read_text(encoding="utf-8")
        action_refs = re.findall(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", source, flags=re.MULTILINE)
        self.assertTrue(action_refs, "expected third-party actions in isolated security workflow")
        for ref in action_refs:
            with self.subTest(action=ref):
                self.assertRegex(ref, r"^[^@]+@[0-9a-f]{40}$", "action references must be pinned to immutable commit SHAs")


if __name__ == "__main__":
    unittest.main()
