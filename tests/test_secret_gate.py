"""Regression tests for the shared detect-secrets gate."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "check_detect_secrets.py"


class SecretGateRegressionTests(unittest.TestCase):
    def run_gate(self, report_text: str | None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "report.json"
            if report_text is not None:
                report_path.write_text(report_text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(GATE), str(report_path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_clean_report_passes(self) -> None:
        report = json.dumps({"results": {}})
        result = self.run_gate(report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"files_with_findings": 0', result.stdout)

    def test_any_finding_fails_gate(self) -> None:
        report = json.dumps({"results": {"src/example.py": [{"type": "ExampleDetector", "line_number": 3}]}})
        result = self.run_gate(report)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("src/example.py", result.stdout)

    def test_invalid_json_fails_closed_with_error_code(self) -> None:
        result = self.run_gate("{not-json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR: cannot read detect-secrets report", result.stderr)

    def test_missing_report_fails_closed_with_error_code(self) -> None:
        result = self.run_gate(None)
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR: cannot read detect-secrets report", result.stderr)

    def test_missing_argument_returns_usage_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GATE)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
