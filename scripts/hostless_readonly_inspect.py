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
import time
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
    (re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|id[_-]?token|session(?:[_-]?id)?|jwt|signature|authorization|auth|password|secret)\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)([?&](?:token|key|password|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|id[_-]?token|session(?:[_-]?id)?|jwt|signature|authorization|auth)=)[^&;\s]+"), r"\1[REDACTED]"),
]

def redact_text(value: str) -> str:
    if TOKEN:
        value = value.replace(TOKEN, "[REDACTED_HOSTLESS_TOKEN]")
    value = re.sub(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[REDACTED_EMAIL]", value)
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

def summarize_log_processes(value):
    """Classify which log streams an API response actually contains."""
    if not isinstance(value, list):
        return None, None
    processes = sorted({
        item.get("process")
        for item in value
        if isinstance(item, dict) and isinstance(item.get("process"), str)
    })
    contains_runtime = any(process.lower() != "build" for process in processes)
    return processes[:10], contains_runtime


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
        # Keep only a small allowlist of structured diagnostics. Never emit the
        # raw body, headers, or arbitrary provider fields into workflow artifacts.
        details = {}
        try:
            raw_error = exc.read(32_000)
            parsed_error = json.loads(raw_error.decode("utf-8"))
            if isinstance(parsed_error, dict):
                for key in ("statusCode", "code", "error", "message", "requestId"):
                    value = parsed_error.get(key)
                    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                        details[key] = redact_text(str(value))[:500]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
        headers = exc.headers or {}
        request_id = next(
            (headers.get(name) for name in ("x-request-id", "request-id", "cf-ray") if headers.get(name)),
            None,
        )
        if request_id:
            details["response_request_id"] = redact_text(str(request_id))[:200]
        result = {
            "status": exc.code,
            "error": "Hostless API request failed; inspect sanitized error details",
        }
        if details:
            result["error_details"] = details
        return result
    except (URLError, TimeoutError) as exc:
        return {"status": None, "error": f"network error: {type(exc).__name__}"}

def wait_for_target_deployment(worker_path: str):
    """Wait briefly for the deployment triggered by this commit to finish.

    Hostless auto-deploys on pushes to main, but its build can lag behind the
    GitHub Actions push event. Polling here prevents the report from mistaking
    an older active deployment for the newly pushed commit.
    """
    target_commit = os.environ.get("GITHUB_SHA", "").strip()
    if not target_commit:
        return get_json(worker_path + "/deployments"), {
            "target_commit": None,
            "waited_seconds": 0,
            "target_deployment_found": False,
            "target_deployment_status": None,
            "note": "GITHUB_SHA unavailable; skipped deployment wait",
        }

    started = time.monotonic()
    deadline = started + 180
    latest_response = None
    target_status = None
    found = False
    while True:
        latest_response = get_json(worker_path + "/deployments")
        data = latest_response.get("data")
        items = (
            data.get("items", [])
            if isinstance(data, dict)
            else data if isinstance(data, list) else []
        )
        match = next(
            (
                item for item in items
                if isinstance(item, dict)
                and item.get("gitCommitHash") == target_commit
                and item.get("id")
            ),
            None,
        )
        if match:
            found = True
            target_status = match.get("status")
            if target_status not in {
                "DEPLOYMENT_QUEUED", "QUEUED", "PENDING",
                "BUILD_STARTED", "BUILDING", "DEPLOYING", "DEPLOYMENT_IN_PROGRESS"
            }:
                break
        if time.monotonic() >= deadline:
            break
        time.sleep(10)

    return latest_response, {
        "target_commit": target_commit,
        "waited_seconds": round(time.monotonic() - started, 1),
        "target_deployment_found": found,
        "target_deployment_status": target_status,
        "note": "wait limit reached" if (
            time.monotonic() >= deadline
            and (
                not found
                or target_status in {
                    "DEPLOYMENT_QUEUED", "QUEUED", "PENDING",
                    "BUILD_STARTED", "BUILDING", "DEPLOYING", "DEPLOYMENT_IN_PROGRESS"
                }
            )
        ) else None,
    }


def main() -> int:
    if not TOKEN:
        print("HOSTLESS_TOKEN secret is missing; add it in repository Actions secrets.", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", WORKER):
        print("Invalid worker name; use letters, digits, dot, underscore, or hyphen only.", file=sys.stderr)
        return 2

    worker_path = "/workers/" + quote(WORKER, safe="")
    deployments_check, deployment_wait = wait_for_target_deployment(worker_path)
    worker_check = get_json(worker_path)
    runtime_logs_check = get_json(worker_path + "/logs")
    worker_data_for_logs = worker_check.get("data")
    project_id_for_logs = (
        worker_data_for_logs.get("projectId")
        if isinstance(worker_data_for_logs, dict) else None
    )
    runtime_logs_project_filtered = None
    if runtime_logs_check.get("status") != 200 and project_id_for_logs:
        # List endpoints can be scoped to a project. Retry once with the
        # worker's own project ID in case an unfiltered log query fails.
        runtime_logs_project_filtered = get_json(
            worker_path + "/logs?projectId=" + quote(str(project_id_for_logs), safe="")
        )

    # Hostless may fail the aggregate worker log endpoint while serving
    # deployment-scoped logs. Try the newest successful deployment as a
    # read-only fallback; never print raw API error bodies.
    deployment_data = deployments_check.get("data")
    deployment_items = (
        deployment_data.get("items", [])
        if isinstance(deployment_data, dict)
        else deployment_data if isinstance(deployment_data, list) else []
    )
    latest_deployment = next(
        (
            item for item in deployment_items
            if isinstance(item, dict) and item.get("id")
        ),
        None,
    )
    latest_successful = next(
        (
            item for item in deployment_items
            if isinstance(item, dict)
            and item.get("status") == "DEPLOYMENT_SUCCESSFUL"
            and item.get("id")
        ),
        None,
    )
    deployment_logs_check = None
    deployment_details_check = None
    if latest_deployment:
        deployment_id = str(latest_deployment["id"])
        deployment_path = worker_path + "/deployments/" + quote(deployment_id, safe="")
        deployment_details_check = get_json(deployment_path)
        deployment_logs_check = get_json(deployment_path + "/logs")

    fallback_log_data = (
        deployment_logs_check.get("data")
        if isinstance(deployment_logs_check, dict) else None
    )
    fallback_log_processes, fallback_contains_runtime_logs = summarize_log_processes(
        fallback_log_data
    )

    worker_data = worker_check.get("data")
    latest_commit = latest_deployment.get("gitCommitHash") if latest_deployment else None
    worker_commit = worker_data.get("gitCommitHash") if isinstance(worker_data, dict) else None
    active_deployment = worker_data.get("activeDeployment") if isinstance(worker_data, dict) else None
    latest_deployment_id = latest_deployment.get("id") if latest_deployment else None

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "worker_name": WORKER,
        "mode": "read-only",
        "note": "Sensitive fields and common token patterns are redacted. Review before sharing logs.",
        "diagnostics": {
            "deployment_wait": deployment_wait,
            "latest_deployment_id": latest_deployment_id,
            "latest_deployment_status": latest_deployment.get("status") if latest_deployment else None,
            "latest_deployment_commit": latest_commit,
            "latest_successful_deployment_id": latest_successful.get("id") if latest_successful else None,
            "runtime_logs_api_failed": (
                runtime_logs_check.get("status") != 200
                if isinstance(runtime_logs_check, dict) else None
            ),
            "deployment_logs_fallback_succeeded": (
                deployment_logs_check.get("status") == 200
                if isinstance(deployment_logs_check, dict) else None
            ),
            "deployment_logs_fallback_processes": fallback_log_processes,
            "deployment_logs_fallback_contains_runtime_logs": fallback_contains_runtime_logs,
            "worker_active_deployment_matches_latest": (
                active_deployment == latest_deployment_id
                if active_deployment and latest_deployment_id else None
            ),
            "worker_reported_commit": worker_commit,
            "worker_commit_comparison_note": (
                "Worker metadata may describe configured source state rather than the active deployment; "
                "use the deployment record and activeDeployment for deployment identity."
            ),
        },
        "checks": {
            "worker": worker_check,
            "deployments": deployments_check,
            "runtime_logs": runtime_logs_check,
            "runtime_logs_project_filtered": runtime_logs_project_filtered,
            "latest_deployment_details": deployment_details_check,
            "latest_deployment_logs_fallback": deployment_logs_check,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    statuses = {
        name: (value.get("status") if isinstance(value, dict) else None)
        for name, value in report["checks"].items()
    }
    print("Hostless read-only inspection completed. HTTP statuses: " + json.dumps(statuses))
    print("Deployment consistency diagnostics: " + json.dumps(report["diagnostics"]))
    print("A redacted report was written to hostless-report/report.json.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
