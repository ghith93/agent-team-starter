"""Run only deterministic benchmark checks; live-model tasks remain explicitly unrun.

Usage: python evaluations/offline_benchmark.py [--output PATH]
No provider calls, API keys, external network, or third-party dependencies are used.
"""
from __future__ import annotations
import argparse
import json
import io
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# These mappings are intentionally narrow: they claim only the exact local
# regression tests executed, not complete end-to-end quality for the task.
CHECKS = {
    "TASK-04": [("tests.test_web_research", "WebResearchTests", "test_rejects_localhost"),
                ("tests.test_web_research", "WebResearchTests", "test_rejects_private_ip_literal")],
    "TASK-05": [("tests.test_web_research", "WebResearchTests", "test_rejects_dns_name_resolving_to_private_ip"),
                ("tests.test_web_research", "WebResearchTests", "test_rejects_mixed_public_and_private_dns_answers")],
    "TASK-09": [("tests.test_router", "RouterTests", "test_falls_back_after_gemini_transient_error"),
                ("tests.test_router", "RouterTests", "test_no_keys_fails_closed")],
    "TASK-10": [("tests.test_telemetry", "TelemetryTests", "test_opt_in_log_contains_metadata_but_not_prompts_or_outputs")],
}

LIVE_TASKS = ["TASK-01", "TASK-02", "TASK-03", "TASK-06", "TASK-07", "TASK-08", "TASK-11", "TASK-12"]

class QuietResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.details = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.details.append({"test": test.id(), "status": "passed"})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.details.append({"test": test.id(), "status": "failed", "error_type": err[0].__name__})
    def addError(self, test, err):
        super().addError(test, err)
        self.details.append({"test": test.id(), "status": "error", "error_type": err[0].__name__})


def load_test(module_name: str, class_name: str, method_name: str):
    module = __import__(module_name, fromlist=[class_name])
    case = getattr(module, class_name)
    return case(method_name)


def run(output: Path | None = None) -> dict:
    tasks = []
    for task_id, specs in CHECKS.items():
        suite = unittest.TestSuite(load_test(*spec) for spec in specs)
        runner = unittest.TextTestRunner(stream=io.StringIO(), resultclass=QuietResult)
        start = time.perf_counter()
        result = runner.run(suite)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        statuses = [x["status"] for x in result.details]
        task_status = "passed" if result.wasSuccessful() else "failed"
        tasks.append({"task_id": task_id, "status": task_status,
                      "checks_passed": statuses.count("passed"), "checks_total": len(specs),
                      "local_test_duration_ms": elapsed_ms, "evidence": result.details,
                      "scope_note": "Only mapped offline regression checks; not a full task-quality score."})
    for task_id in LIVE_TASKS:
        tasks.append({"task_id": task_id, "status": "not_run",
                      "reason": "Requires live-model or human evaluation; deliberately not attempted."})
    # TASK-11 is intentionally unrun: this package has no general JSON-schema
    # output contract to test; do not treat arbitrary parseability as quality.
    report = {
        "suite": "agent_team_starter_offline_benchmark",
        "suite_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "offline_deterministic_only",
        "network_calls": 0,
        "provider_api_calls": 0,
        "estimated_cost_usd": 0,
        "task_count": len(tasks),
        "passed_tasks": sum(t["status"] == "passed" for t in tasks),
        "failed_tasks": sum(t["status"] == "failed" for t in tasks),
        "not_run_tasks": sum(t["status"] == "not_run" for t in tasks),
        "release_decision": "REVIEW_REQUIRED" if any(t["status"] == "failed" for t in tasks) else "OFFLINE_CHECKS_PASS_LIVE_EVALUATION_REQUIRED",
        "limitations": [
            "This report measures only the named deterministic local tests.",
            "No general model accuracy, source quality, human intervention, live latency, or live cost is measured.",
            "DNS rebinding resistance depends on an independently verified egress proxy; this suite does not test a real proxy policy.",
            "A passed local test does not establish overall product security or readiness for public deployment."
        ],
        "tasks": tasks,
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluations" / "results" / "offline_deterministic_report.json")
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({k: report[k] for k in ("suite", "task_count", "passed_tasks", "failed_tasks", "not_run_tasks", "release_decision", "network_calls", "provider_api_calls", "estimated_cost_usd")}, ensure_ascii=False, indent=2))
    print(f"Report: {args.output}")
    return 1 if report["failed_tasks"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
