import unittest
from offline_benchmark import run

class OfflineBenchmarkTests(unittest.TestCase):
    def test_report_marks_live_tasks_not_run_and_never_claims_live_metrics(self):
        report = run()
        self.assertEqual(report["task_count"], 12)
        self.assertEqual(report["passed_tasks"], 4)
        self.assertEqual(report["failed_tasks"], 0)
        self.assertEqual(report["not_run_tasks"], 8)
        self.assertEqual(report["network_calls"], 0)
        self.assertEqual(report["provider_api_calls"], 0)
        self.assertEqual(report["estimated_cost_usd"], 0)
        self.assertTrue(all(t["status"] == "not_run" for t in report["tasks"] if t["task_id"] in {"TASK-01", "TASK-02", "TASK-03", "TASK-06", "TASK-07", "TASK-08", "TASK-11", "TASK-12"}))

if __name__ == "__main__":
    unittest.main()
