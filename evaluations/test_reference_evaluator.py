import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from reference_evaluator import expected_cac, evaluate_numeric_answer, run_reference_suite

class ReferenceEvaluatorTests(unittest.TestCase):
    def test_correct_cac(self):
        self.assertTrue(evaluate_numeric_answer(50, 12, 4.17)["passed"])
    def test_reversed_formula_rejected(self):
        self.assertFalse(evaluate_numeric_answer(50, 12, 0.24)["passed"])
    def test_zero_orders_rejected(self):
        with self.assertRaises(ValueError): expected_cac(50, 0)
    def test_negative_cost_rejected(self):
        with self.assertRaises(ValueError): expected_cac(-50, 12)
    def test_non_finite_inputs_rejected(self):
        import math
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError): expected_cac(value, 2)
            with self.assertRaises(ValueError): expected_cac(2, value)
    def test_non_finite_answers_rejected(self):
        import math
        self.assertFalse(evaluate_numeric_answer(2, 1, math.nan)["passed"])
        self.assertFalse(evaluate_numeric_answer(2, 1, math.inf)["passed"])
    def test_invalid_tolerance_rejected(self):
        with self.assertRaises(ValueError): evaluate_numeric_answer(2, 1, 2, tolerance=-1)
    def test_all_reference_cases(self):
        results = run_reference_suite()
        self.assertEqual(len(results), 12)
        self.assertTrue(all(all(v for k, v in r.items() if k != "id") for r in results))

if __name__ == "__main__": unittest.main()
