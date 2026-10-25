#!/usr/bin/env python3
"""Fail CI when detect-secrets reports any unreviewed candidate."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} DETECT_SECRETS_REPORT.json", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    try:
        with report_path.open(encoding="utf-8") as report_file:
            report = json.load(report_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read detect-secrets report: {exc}", file=sys.stderr)
        return 2

    results = report.get("results", {})
    findings = {path: items for path, items in results.items() if items}
    print(json.dumps({"files_with_findings": len(findings), "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
