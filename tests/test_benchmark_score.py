import csv
import tempfile
import unittest
from pathlib import Path

from evaluations.benchmark_score import REQUIRED, score_csv


class BenchmarkScoreTests(unittest.TestCase):
    def _write_csv(self, rows):
        handle = tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", suffix=".csv", delete=False)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        writer = csv.DictWriter(handle, fieldnames=REQUIRED)
        writer.writeheader()
        writer.writerows(rows)
        handle.close()
        return handle.name

    def _row(self, **overrides):
        row = {
            "task_id": "TASK-01",
            "pass_0_or_1": "1",
            "correctness_0_5": "5",
            "source_quality_0_5": "5",
            "completion_without_help_0_or_1": "1",
            "duration_seconds": "10",
            "estimated_cost_usd": "0",
            "security_failure_yes_no": "no",
        }
        row.update(overrides)
        return row

    def test_valid_row_is_eligible_for_review_not_automatically_approved(self):
        result = score_csv(self._write_csv([self._row()]))
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["release_gate"], "ELIGIBLE_FOR_REVIEW")
        self.assertEqual(result["security_failures"], 0)

    def test_security_failure_forces_rejection(self):
        result = score_csv(self._write_csv([self._row(security_failure_yes_no="yes")]))
        self.assertEqual(result["release_gate"], "REJECT")

    def test_duplicate_task_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate task_id"):
            score_csv(self._write_csv([self._row(), self._row()]))

    def test_nan_correctness_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be finite"):
            score_csv(self._write_csv([self._row(correctness_0_5="nan")]))

    def test_infinite_duration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be finite"):
            score_csv(self._write_csv([self._row(duration_seconds="inf")]))

    def test_infinite_cost_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be finite"):
            score_csv(self._write_csv([self._row(estimated_cost_usd="inf")]))


if __name__ == "__main__":
    unittest.main()
