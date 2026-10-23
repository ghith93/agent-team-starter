import unittest
from prompt_injection_suite import ALLOWED_ACTIONS, run_suite, validate_cases


class PromptInjectionFixtureTests(unittest.TestCase):
    def test_project_fixtures_are_well_formed(self):
        report = run_suite()
        self.assertTrue(report["passed"], report["errors"])
        self.assertGreaterEqual(report["cases_checked"], 10)

    def test_duplicate_ids_are_rejected(self):
        case = {"id": "same", "category": "x", "scenario": "x", "untrusted_content": "x", "task": "x", "expected_action": "continue_safe_task", "must_not": ["x"]}
        errors = validate_cases([case, dict(case)])
        self.assertTrue(any("duplicate id" in error for error in errors))

    def test_unknown_action_is_rejected(self):
        case = {"id": "x", "category": "x", "scenario": "x", "untrusted_content": "x", "task": "x", "expected_action": "trust_everything", "must_not": ["x"]}
        self.assertTrue(any("unsupported expected_action" in error for error in validate_cases([case])))

    def test_missing_required_field_is_rejected(self):
        self.assertTrue(any("missing fields" in error for error in validate_cases([{"id": "x"}])))

    def test_all_actions_used_by_fixtures_are_declared(self):
        from pathlib import Path
        import json
        cases = json.loads((Path(__file__).with_name("prompt_injection_cases.json")).read_text(encoding="utf-8"))
        self.assertTrue({case["expected_action"] for case in cases} <= ALLOWED_ACTIONS)


if __name__ == "__main__":
    unittest.main()
