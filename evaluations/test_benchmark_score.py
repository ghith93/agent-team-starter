import csv, tempfile, unittest
from pathlib import Path
from benchmark_score import score_csv

FIELDS = ["task_id", "pass_0_or_1", "correctness_0_5", "source_quality_0_5", "completion_without_help_0_or_1", "duration_seconds", "estimated_cost_usd", "security_failure_yes_no"]

class BenchmarkScoreTests(unittest.TestCase):
    def make_csv(self, row):
        temp = tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", suffix=".csv", delete=False)
        with temp:
            writer = csv.DictWriter(temp, fieldnames=FIELDS)
            writer.writeheader(); writer.writerow(row)
        self.addCleanup(lambda: Path(temp.name).unlink(missing_ok=True))
        return temp.name

    def test_results_template_matches_scorer_schema(self):
        template = Path(__file__).with_name("benchmark_results_template.csv")
        with template.open(newline="", encoding="utf-8") as handle:
            headers = next(csv.reader(handle))
        self.assertEqual(headers, FIELDS)

    def test_good_case_is_eligible_for_review(self):
        path = self.make_csv(dict(task_id="T1", pass_0_or_1=1, correctness_0_5=5, source_quality_0_5=5, completion_without_help_0_or_1=1, duration_seconds=10, estimated_cost_usd=0, security_failure_yes_no="no"))
        result = score_csv(path)
        self.assertEqual(result["release_gate"], "ELIGIBLE_FOR_REVIEW")
        self.assertEqual(result["pass_rate"], 1.0)

    def test_security_failure_forces_reject(self):
        path = self.make_csv(dict(task_id="T1", pass_0_or_1=1, correctness_0_5=5, source_quality_0_5=5, completion_without_help_0_or_1=1, duration_seconds=1, estimated_cost_usd=0, security_failure_yes_no="yes"))
        self.assertEqual(score_csv(path)["release_gate"], "REJECT")

    def test_invalid_values_are_rejected(self):
        path = self.make_csv(dict(task_id="T1", pass_0_or_1=3, correctness_0_5=5, source_quality_0_5=5, completion_without_help_0_or_1=1, duration_seconds=1, estimated_cost_usd=0, security_failure_yes_no="no"))
        with self.assertRaises(ValueError): score_csv(path)

if __name__ == "__main__": unittest.main()
