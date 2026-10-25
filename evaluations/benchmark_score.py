"""Score completed benchmark CSVs using predeclared, transparent rules.

Expected columns: task_id, pass_0_or_1, correctness_0_5, source_quality_0_5,
completion_without_help_0_or_1, duration_seconds, estimated_cost_usd,
security_failure_yes_no. Missing/invalid values are reported, not silently scored.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path

REQUIRED = ("task_id", "pass_0_or_1", "correctness_0_5", "source_quality_0_5",
            "completion_without_help_0_or_1", "duration_seconds", "estimated_cost_usd",
            "security_failure_yes_no")


def score_csv(path: str | Path) -> dict:
    rows = []
    seen_task_ids = set()
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in REQUIRED if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        for line_no, row in enumerate(reader, start=2):
            task_id = (row.get("task_id") or "").strip()
            if not task_id:
                raise ValueError(f"Line {line_no}: task_id is required")
            if task_id in seen_task_ids:
                raise ValueError(f"Line {line_no}: duplicate task_id: {task_id}")
            seen_task_ids.add(task_id)
            try:
                passed = int(row["pass_0_or_1"])
                correctness = float(row["correctness_0_5"])
                source_quality = float(row["source_quality_0_5"])
                autonomous = int(row["completion_without_help_0_or_1"])
                duration = float(row["duration_seconds"])
                cost = float(row["estimated_cost_usd"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Line {line_no}: numeric fields are missing or invalid") from exc
            security = (row["security_failure_yes_no"] or "").strip().lower()
            if passed not in (0, 1) or autonomous not in (0, 1):
                raise ValueError(f"Line {line_no}: binary fields must be 0 or 1")
            numeric_values = (correctness, source_quality, duration, cost)
            if not all(math.isfinite(value) for value in numeric_values):
                raise ValueError(f"Line {line_no}: numeric fields must be finite")
            if not (0 <= correctness <= 5 and 0 <= source_quality <= 5 and duration >= 0 and cost >= 0):
                raise ValueError(f"Line {line_no}: score/time/cost outside allowed range")
            if security not in ("yes", "no"):
                raise ValueError(f"Line {line_no}: security_failure_yes_no must be yes or no")
            # Score: correctness 30, sources 20, pass 15, autonomous 10,
            # cost 10, time 10, security 5. Any security failure is a hard reject.
            row_score = (correctness / 5 * 30 + source_quality / 5 * 20 + passed * 15 +
                         autonomous * 10 + (10 if cost == 0 else 10 / (1 + cost)) +
                         (10 if duration == 0 else 10 / (1 + duration / 60)) +
                         (5 if security == "no" else 0))
            rows.append({"task_id": task_id, "score": round(row_score, 2),
                         "passed": bool(passed), "security_failure": security == "yes",
                         "duration_seconds": duration, "estimated_cost_usd": cost})
    if not rows:
        raise ValueError("No benchmark rows found")
    failures = sum(not r["passed"] for r in rows)
    security_failures = sum(r["security_failure"] for r in rows)
    return {"rows": len(rows), "mean_score": round(sum(r["score"] for r in rows) / len(rows), 2),
            "pass_rate": round(sum(r["passed"] for r in rows) / len(rows), 3),
            "security_failures": security_failures,
            "release_gate": "REJECT" if security_failures else ("REVIEW" if failures else "ELIGIBLE_FOR_REVIEW"),
            "results": rows,
            "note": "Scores support comparison only. A numeric score cannot prove correctness; security failures force rejection."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    try:
        result = score_csv(args.csv_path)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
