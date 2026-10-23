"""Deterministic checks for known calculations; not a general language-quality judge."""
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CASES_FILE = Path(__file__).with_name("reference_cases.json")


def expected_cac(marketing_cost, delivered_orders):
    if not isinstance(marketing_cost, (int, float)) or isinstance(marketing_cost, bool):
        raise ValueError("marketing_cost must be numeric")
    if not isinstance(delivered_orders, (int, float)) or isinstance(delivered_orders, bool):
        raise ValueError("delivered_orders must be numeric")
    if not math.isfinite(marketing_cost) or not math.isfinite(delivered_orders):
        raise ValueError("inputs must be finite numbers")
    if marketing_cost < 0 or delivered_orders <= 0:
        raise ValueError("cost must be non-negative and delivered_orders must be positive")
    result = marketing_cost / delivered_orders
    if not math.isfinite(result):
        raise ValueError("result must be finite")
    # Financial-style rounding avoids Python's binary-float/banker's-rounding edge cases.
    return float((Decimal(str(marketing_cost)) / Decimal(str(delivered_orders))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def evaluate_numeric_answer(marketing_cost, delivered_orders, answer, tolerance=0.01):
    expected = expected_cac(marketing_cost, delivered_orders)
    try:
        actual = float(answer)
        if not math.isfinite(actual):
            actual = None
    except (TypeError, ValueError, OverflowError):
        actual = None
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a finite non-negative number")
    passed = actual is not None and abs(actual - expected) <= tolerance
    return {"expected": expected, "actual": actual, "tolerance": tolerance, "passed": passed}


def run_reference_suite():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        inputs = case["inputs"]
        if case["type"] == "numeric":
            good = evaluate_numeric_answer(**inputs, answer=case["expected"], tolerance=case.get("tolerance", 0.01))
            bad = evaluate_numeric_answer(**inputs, answer=case["wrong_answer"], tolerance=case.get("tolerance", 0.01))
            results.append({"id": case["id"], "correct_answer_passes": good["passed"], "wrong_answer_rejected": not bad["passed"]})
        elif case["type"] == "input_validation":
            try:
                expected_cac(**inputs)
                raised = False
            except ValueError:
                raised = True
            results.append({"id": case["id"], "invalid_input_rejected": raised})
        else:
            raise ValueError(f"Unknown case type: {case['type']}")
    return results


def main():
    results = run_reference_suite()
    passed = all(all(v for k, v in row.items() if k != "id") for row in results)
    print(json.dumps({"suite": "reference_calculations", "passed": passed, "cases": results,
                      "limitation": "Checks deterministic arithmetic and input validation only; does not score general AI answer quality."}, indent=2, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
