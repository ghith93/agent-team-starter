import unittest
from unittest.mock import patch
from agent_team.tooling_audit import collect_inventory


class ToolingAuditTests(unittest.TestCase):
    @patch("agent_team.tooling_audit.shutil.which", return_value=None)
    @patch("agent_team.tooling_audit.importlib.util.find_spec", return_value=None)
    def test_inventory_is_offline_and_does_not_claim_installs(self, _module, _command):
        report = collect_inventory()
        self.assertEqual(report["network_calls"], 0)
        self.assertEqual(report["installations_performed"], 0)
        self.assertFalse(report["secret_values_read"])
        self.assertEqual(set(report["commands"].values()), {False})
        self.assertEqual(set(report["python_modules"].values()), {False})

    def test_inventory_schema_contains_limitations(self):
        report = collect_inventory()
        self.assertEqual(report["execution_mode"], "local_discovery_only")
        self.assertIn("limitations", report)
        self.assertGreaterEqual(len(report["limitations"]), 3)


if __name__ == "__main__":
    unittest.main()
