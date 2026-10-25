#!/usr/bin/env python3
"""Read-only Hostless worker inspection for a manually dispatched GitHub workflow.

Never prints the API token or raw HTTP error bodies. The report is redacted and
stored only as a short-lived workflow artifact.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_BASE = "https://api.hostless.cloud/v1"
TOKEN = os.environ.get("HOSTLESS_TOKEN", "").strip()
WORKER = os.environ.get("HOSTLESS_WORKER", "agent-team-worker").strip()
OUT = Path("hostless-report/report.json")
MAX_RESPONSE_BYTES = 1_000_000
MAX_LOG_CHARS = 20_000

SENSITIVE_KEY = re.compile(
    r"(token|secret|password|authorization|api.?key|credential|private.?key|cookie)",
    re.IGNORECASE,
)
PATTERNS = [
    (re.compile(r"\bhlk_[A-Za-z0-9_-]{8,}\b"), "[REDACTED_HOSTLESS_TOKEN]"),
    (re.compile(r"(?i)\bBearer\s+[^\s,;]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)([?&](?:token|key|password|secret|api_key)=)[^&\s]+"), r"\1[REDACTED]"),
]

def redact_text(value: str) -> str:
    if TOKEN:
        value = value.replace(TOKEN, "[REDACTED_HOSTLESS_TOKEN]")
    for pattern, replacement in PATTERNS:
        value = pattern.sub(replacement, value)
    return value[:MAX_LOG_CHARS] + ("\n[TRUNCATED]" if len(value) > MAX_LOG_CHARS else "")

def redact(value, key: str = ""):
    if SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value[:500]]
    if isinstance(value, str):
        return redact_text(value)
    return value

def get_json(path: str):
    req = Request(
        API_BASE + path,
        headers={"Authorization": TOKEN, "Accept": "application/json", "User-Agent": "agent-team-hostless-readonly-inspector"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                return {"status": response.status, "error": "response exceeded 1 MB safety limit"}
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return {"status": response.status, "error": "response was not valid JSON"}
            return {"status": response.status, "data": redact(data)}
    except HTTPError as exc:
        # Deliberately do not emit response bodies; they may contain sensitive details.
        return {"status": exc.code, "error": "Hostless API request failed; inspect status and token scopes"}
    except (URLError, TimeoutError) as exc:
        return {"status": None, "error": f"network error: {type(exc).__name__}"}

def main() -> int:
    if not TOKEN:
        print("HOSTLESS_TOKEN secret is missing; add it in repository Actions secrets.", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", WORKER):
        print("Invalid worker name; use letters, digits, dot, underscore, or hyphen only.", file=sys.stderr)
        return 2

    worker_path = "/workers/" + quote(WORKER, safe="")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "worker_name": WORKER,
        "mode": "read-only",
        "note": "Sensitive fields and common token patterns are redacted. Review before sharing logs.",
        "checks": {
            "worker": get_json(worker_path),
            "deployments": get_json(worker_path + "/deployments"),
            "runtime_logs": get_json(worker_path + "/logs"),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    statuses = {name: value.get("status") for name, value in report["checks"].items()}
    print("Hostless read-only inspection completed. HTTP statuses: " + json.dumps(statuses))
    print("A redacted report was written to hostless-report/report.json.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
