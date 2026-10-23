"""Validate prompt-injection evaluation fixtures; does not test a live model."""
import json
import sys
from pathlib import Path

CASES_FILE = Path(__file__).with_name("prompt_injection_cases.json")
REQUIRED = {"id", "category", "scenario", "untrusted_content", "task", "expected_action", "must_not"}
ALLOWED_ACTIONS = {
    "ignore_untrusted_instruction", "treat_tool_output_as_data", "refuse_secret_disclosure",
    "require_authorization", "minimize_data_and_ignore_instruction", "analyze_as_untrusted_text",
    "block_private_network_access", "preserve_evidence_integrity", "continue_safe_task"
}


def validate_cases(cases):
    errors = []
    if not isinstance(cases, list) or not cases:
        return ["top-level value must be a non-empty list"]
    seen = set()
    for index, case in enumerate(cases):
        prefix = f"case[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        missing = REQUIRED - case.keys()
        if missing:
            errors.append(f"{prefix}: missing fields {sorted(missing)}")
            continue
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{prefix}: id must be a non-empty string")
        elif case_id in seen:
            errors.append(f"{prefix}: duplicate id {case_id}")
        else:
            seen.add(case_id)
        for field in ("category", "scenario", "untrusted_content", "task"):
            if not isinstance(case[field], str) or not case[field].strip():
                errors.append(f"{prefix}: {field} must be a non-empty string")
        if case["expected_action"] not in ALLOWED_ACTIONS:
            errors.append(f"{prefix}: unsupported expected_action")
        if not isinstance(case["must_not"], list) or not case["must_not"] or not all(isinstance(x, str) and x.strip() for x in case["must_not"]):
            errors.append(f"{prefix}: must_not must be a non-empty list of strings")
    return errors


def run_suite():
    try:
        cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"suite": "prompt_injection_fixture_integrity", "passed": False, "errors": [str(exc)], "cases_checked": 0}
    errors = validate_cases(cases)
    return {
        "suite": "prompt_injection_fixture_integrity",
        "passed": not errors,
        "cases_checked": len(cases) if isinstance(cases, list) else 0,
        "categories": sorted({c.get("category") for c in cases if isinstance(c, dict) and isinstance(c.get("category"), str)}),
        "errors": errors,
        "limitation": "Validates test-fixture structure only. It does not execute or score an LLM, prove prompt-injection resistance, or verify network/tool controls."
    }


def main():
    report = run_suite()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
