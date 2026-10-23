import tempfile
import unittest
from pathlib import Path
from security_audit import audit


class SecurityAuditTests(unittest.TestCase):
    def test_clean_fixture_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("requests>=2.31,<3\n", encoding="utf-8")
            (root / "sample.py").write_text("print('safe')\n", encoding="utf-8")
            report = audit(root)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["summary"]["high_confidence_secret_candidates"], 0)

    def test_secret_shape_is_flagged_without_echoing_value(self):
        fake = "ghp_" + "A" * 36
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text("TOKEN = '" + fake + "'\n", encoding="utf-8")
            report = audit(root)
            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(item["rule"] == "SECRET_GITHUB_TOKEN" for item in report["findings"]))
            self.assertNotIn(fake, str(report))

    def test_review_pattern_is_not_misreported_as_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text("ev" + "al(user_input)\n", encoding="utf-8")
            report = audit(root)
            self.assertEqual(report["status"], "pass")
            self.assertTrue(any(item["rule"] == "DANGEROUS_EVAL" for item in report["findings"]))
            self.assertEqual(report["summary"]["manual_review_items"], 1)

    def test_unbounded_dependency_range_is_noted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("example-package>=1.0\n", encoding="utf-8")
            report = audit(root)
            self.assertEqual(len(report["dependency_notes"]), 1)


if __name__ == "__main__":
    unittest.main()
