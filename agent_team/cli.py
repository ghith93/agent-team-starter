"""Command-line entry point with explicit offline/configuration modes."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path
from .memory_store import MemoryStore
from .router import FreeFirstRouter, ProviderError
from .team import MAX_TASK_CHARS, TeamExecutionError, run_team
from .tool_runtime import create_default_registry
from .workflow_store import WorkflowStateError, WorkflowStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Free-first Planner → Executor → Reviewer → Reviser agent team")
    parser.add_argument("task", nargs="*", help="Task text (omit when using --task-file)")
    parser.add_argument("--task-file", type=Path, help="Read task text from a UTF-8 file")
    parser.add_argument("--check-config", action="store_true", help="Report configured provider names only; makes no API calls")
    parser.add_argument("--telemetry", type=Path, help="Opt in to metadata-only JSONL telemetry")
    parser.add_argument("--tools", action="store_true", help="Enable bounded read-only repository tools and proxy-gated public-web research")
    parser.add_argument("--memory-db", type=Path, help="Opt in to local memory retrieval from this SQLite database")
    parser.add_argument("--memory-query", help="Explicit keyword query for notes sent to the model provider")
    parser.add_argument("--memory-limit", type=int, default=3, help="Maximum notes to retrieve (1-5)")
    parser.add_argument("--queue-db", type=Path, help="Opt in to a local SQLite workflow queue")
    queue_mode = parser.add_mutually_exclusive_group()
    queue_mode.add_argument("--enqueue", action="store_true", help="Persist this task in --queue-db without calling a model")
    queue_mode.add_argument("--run-next", action="store_true", help="Claim and execute one queued task from --queue-db")
    queue_mode.add_argument("--worker", action="store_true", help="Continuously poll the local queue until interrupted or --max-jobs is reached")
    parser.add_argument("--max-attempts", type=int, default=3, help="Queue retry limit for --enqueue (1-10)")
    parser.add_argument("--lease-seconds", type=int, default=300, help="Worker lease duration for --run-next/--worker (1-86400)")
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0, help="Base retry delay for transient provider failures")
    parser.add_argument("--poll-interval-seconds", type=float, default=5.0, help="Idle wait between worker polls (0.5-300)")
    parser.add_argument("--max-jobs", type=int, default=0, help="Worker exit limit; 0 means keep running until interrupted")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output (default)")
    return parser


def _run_with_lease_heartbeat(store: WorkflowStore, job: dict, lease_seconds: int, router, tool_registry=None):
    stop = threading.Event()
    lease_lost = threading.Event()
    interval = max(0.5, min(30.0, lease_seconds / 3))

    def heartbeat():
        while not stop.wait(interval):
            try:
                if not store.renew_lease(job["job_id"], job["claim_token"], lease_seconds=lease_seconds):
                    lease_lost.set()
                    return
            except (OSError, sqlite3.Error, WorkflowStateError):
                lease_lost.set()
                return

    thread = threading.Thread(target=heartbeat, name="queue-lease-heartbeat", daemon=True)
    thread.start()
    try:
        result = run_team(job["task"], router, tool_registry=tool_registry)
    finally:
        stop.set()
        thread.join(timeout=interval + 1)
    if lease_lost.is_set():
        raise WorkflowStateError("Job lease was lost during execution; result was not committed.")
    return result


def main(argv=None):
    args = build_parser().parse_args(argv)
    router = FreeFirstRouter()
    if args.check_config:
        print(json.dumps({
            "configured_providers": (["Gemini"] if router.gemini_key else []) + (["OpenRouter"] if router.openrouter_key else []),
            "gemini_model_configured": bool(router.gemini_model),
            "openrouter_free_models": router.free_models,
            "live_check_performed": False,
            "note": "Configuration presence only; no network request or billing check was performed."
        }, ensure_ascii=False, indent=2))
        return 0
    if args.queue_db and not (args.enqueue or args.run_next or args.worker):
        print("--queue-db requires --enqueue, --run-next, or --worker.", file=sys.stderr)
        return 2
    if (args.enqueue or args.run_next or args.worker) and not args.queue_db:
        print("--enqueue, --run-next, and --worker require --queue-db.", file=sys.stderr)
        return 2
    if args.task_file and args.task:
        print("Use either task arguments or --task-file, not both.", file=sys.stderr)
        return 2
    if args.task_file:
        try:
            # Bound bytes before decoding: UTF-8 characters occupy at most four bytes.
            with args.task_file.open("rb") as handle:
                raw_task = handle.read(MAX_TASK_CHARS * 4 + 1)
            if len(raw_task) > MAX_TASK_CHARS * 4:
                print(f"Task file is too long (maximum {MAX_TASK_CHARS} characters).", file=sys.stderr)
                return 2
            task = raw_task.decode("utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"Could not read task file: {type(exc).__name__}", file=sys.stderr)
            return 2
    else:
        task = " ".join(args.task)
    if len(task) > MAX_TASK_CHARS:
        print(f"Task is too long (maximum {MAX_TASK_CHARS} characters).", file=sys.stderr)
        return 2
    if (args.run_next or args.worker) and task.strip():
        print("Queue workers take tasks from the queue; do not pass task text or --task-file.", file=sys.stderr)
        return 2
    if not (args.run_next or args.worker) and not task.strip():
        print('Provide task text or --task-file. Use --check-config for a no-network check.', file=sys.stderr)
        return 2
    if args.enqueue and args.tools:
        print("--tools is not needed when enqueueing; enable it when running queued tasks.", file=sys.stderr)
        return 2
    if (args.enqueue or args.run_next or args.worker) and (args.memory_db or args.memory_query):
        print("Queue mode cannot be combined with --memory-db/--memory-query; enqueue only non-sensitive task text.", file=sys.stderr)
        return 2
    if args.enqueue and not 1 <= args.max_attempts <= 10:
        print("--max-attempts must be from 1 to 10.", file=sys.stderr)
        return 2
    if (args.run_next or args.worker) and not 1 <= args.lease_seconds <= 86400:
        print("--lease-seconds must be from 1 to 86400.", file=sys.stderr)
        return 2
    if args.worker and (args.poll_interval_seconds < 0.5 or args.poll_interval_seconds > 300):
        print("--poll-interval-seconds must be from 0.5 to 300.", file=sys.stderr)
        return 2
    if args.worker and (args.max_jobs < 0 or args.max_jobs > 1000000):
        print("--max-jobs must be from 0 to 1000000.", file=sys.stderr)
        return 2
    if (args.run_next or args.worker) and (args.retry_delay_seconds < 0 or args.retry_delay_seconds > 3600):
        print("--retry-delay-seconds must be from 0 to 3600.", file=sys.stderr)
        return 2
    tool_registry = create_default_registry(Path.cwd()) if args.tools else None
    if args.enqueue:
        try:
            store = WorkflowStore(args.queue_db)
            job = store.enqueue(task, max_attempts=args.max_attempts)
        except (OSError, ValueError, sqlite3.Error) as exc:
            print(json.dumps({"ok": False, "error_type": type(exc).__name__}), file=sys.stderr)
            return 2
        print(json.dumps({
            "ok": True, "queued": True, "job_id": job["job_id"],
            "status": job["status"], "max_attempts": job["max_attempts"],
            "database": str(args.queue_db),
            "note": "Queue stores task text in plaintext SQLite. Keep this database private and outside version control."
        }, ensure_ascii=False, indent=2))
        return 0
    if args.worker:
        if not args.queue_db.is_file():
            print("--worker requires an existing queue database; enqueue a task first.", file=sys.stderr)
            return 2
        processed = 0
        print(json.dumps({"worker": "started", "poll_interval_seconds": args.poll_interval_seconds,
                          "max_jobs": args.max_jobs, "database": str(args.queue_db)}, ensure_ascii=False), flush=True)
        try:
            while args.max_jobs == 0 or processed < args.max_jobs:
                captured_out, captured_err = io.StringIO(), io.StringIO()
                nested_args = ["--queue-db", str(args.queue_db), "--run-next",
                               "--lease-seconds", str(args.lease_seconds),
                               "--retry-delay-seconds", str(args.retry_delay_seconds)]
                if args.tools:
                    nested_args.append("--tools")
                with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
                    code = main(nested_args)
                output = captured_out.getvalue().strip()
                error_output = captured_err.getvalue().strip()
                try:
                    payload = json.loads(output) if output else {}
                except json.JSONDecodeError:
                    payload = {}
                if not payload.get("job_id") and error_output:
                    try:
                        error_payload = json.loads(error_output)
                    except json.JSONDecodeError:
                        error_payload = {}
                    if isinstance(error_payload, dict) and error_payload.get("job_id"):
                        payload = error_payload
                claimed = payload.get("claimed") is True or bool(payload.get("job_id"))
                if claimed:
                    processed += 1
                    event = {"worker": "job_attempt", "attempts_processed": processed,
                             "exit_code": code, "job_id": payload.get("job_id"),
                             "status": payload.get("status"), "retryable": payload.get("retryable")}
                    print(json.dumps(event, ensure_ascii=False), flush=True)
                    if error_output:
                        print(error_output, file=sys.stderr, flush=True)
                elif code != 0:
                    print(error_output or output or "Queue worker encountered an unclassified error.",
                          file=sys.stderr, flush=True)
                    time.sleep(args.poll_interval_seconds)
                else:
                    time.sleep(args.poll_interval_seconds)
        except KeyboardInterrupt:
            print(json.dumps({"worker": "stopped", "reason": "interrupt",
                              "attempts_processed": processed}, ensure_ascii=False), flush=True)
            return 130
        print(json.dumps({"worker": "stopped", "reason": "max_jobs_reached",
                          "attempts_processed": processed}, ensure_ascii=False), flush=True)
        return 0
    if args.run_next:
        if not args.queue_db.is_file():
            print("--run-next requires an existing queue database.", file=sys.stderr)
            return 2
        try:
            store = WorkflowStore(args.queue_db)
            job = store.claim_next(lease_seconds=args.lease_seconds)
        except (OSError, ValueError, sqlite3.Error) as exc:
            print(json.dumps({"ok": False, "error_type": type(exc).__name__}), file=sys.stderr)
            return 2
        if job is None:
            print(json.dumps({"ok": True, "claimed": False, "note": "No queued job is ready."}, ensure_ascii=False))
            return 0
        try:
            result = _run_with_lease_heartbeat(store, job, args.lease_seconds, router, tool_registry=tool_registry)
            metadata = {
                "run_id": result.get("run_id"),
                "stage_count": len(result.get("trace", [])),
                "providers": sorted({str(event.get("provider", "unknown")) for event in result.get("trace", [])}),
                "total_duration_ms": result.get("total_duration_ms"),
                "final_chars": len(result.get("final", "")) if isinstance(result.get("final"), str) else None,
            }
            store.complete(job["job_id"], metadata, claim_token=job["claim_token"])
            print(json.dumps({"ok": True, "claimed": True, "job_id": job["job_id"],
                              "status": "succeeded", "result_metadata": metadata}, ensure_ascii=False, indent=2))
            return 0
        except Exception as exc:
            cause = exc.cause if isinstance(exc, TeamExecutionError) else exc
            retryable = isinstance(cause, ProviderError) and (
                cause.status_code is None or cause.status_code == 429 or
                (cause.status_code is not None and 500 <= cause.status_code <= 599)
            )
            error_type = type(cause).__name__
            try:
                failed = store.fail(job["job_id"], error_type, claim_token=job["claim_token"], retryable=retryable,
                                    base_delay_seconds=args.retry_delay_seconds)
                status = failed["status"]
            except (WorkflowStateError, ValueError, sqlite3.Error) as store_exc:
                print(json.dumps({"ok": False, "job_id": job["job_id"],
                                  "error_type": type(store_exc).__name__}, ensure_ascii=False), file=sys.stderr)
                return 1
            print(json.dumps({"ok": False, "job_id": job["job_id"], "status": status,
                              "retryable": retryable, "error_type": error_type}, ensure_ascii=False), file=sys.stderr)
            return 1
    if args.memory_db and not args.memory_query:
        print("--memory-db requires an explicit --memory-query; retrieved notes are sent to the model provider.", file=sys.stderr)
        return 2
    if args.memory_query and not args.memory_db:
        print("--memory-query requires --memory-db.", file=sys.stderr)
        return 2
    if not 1 <= args.memory_limit <= 5:
        print("--memory-limit must be from 1 to 5.", file=sys.stderr)
        return 2
    memory_context = None
    if args.memory_db:
        if not args.memory_db.is_file():
            print("--memory-db must point to an existing local SQLite file.", file=sys.stderr)
            return 2
        try:
            memory_context = MemoryStore(args.memory_db).search(args.memory_query, limit=args.memory_limit)
        except (OSError, ValueError, sqlite3.Error) as exc:
            print(f"Could not read local memory: {type(exc).__name__}", file=sys.stderr)
            return 2
    try:
        result = run_team(task, router, telemetry_path=args.telemetry, memory_context=memory_context, tool_registry=tool_registry)
    except (ProviderError, ValueError, TeamExecutionError) as exc:
        payload = {"ok": False, "error": str(exc)}
        if isinstance(exc, TeamExecutionError):
            payload.update({"failed_stage": exc.stage, "completed_stages": list(exc.completed), "trace": exc.trace})
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
