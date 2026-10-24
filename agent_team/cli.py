"""Command-line entry point with explicit offline/configuration modes."""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from .memory_store import MemoryStore
from .router import FreeFirstRouter, ProviderError
from .team import TeamExecutionError, run_team
from .workflow_store import WorkflowStateError, WorkflowStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Free-first Planner → Executor → Reviewer agent team")
    parser.add_argument("task", nargs="*", help="Task text (omit when using --task-file)")
    parser.add_argument("--task-file", type=Path, help="Read task text from a UTF-8 file")
    parser.add_argument("--check-config", action="store_true", help="Report configured provider names only; makes no API calls")
    parser.add_argument("--telemetry", type=Path, help="Opt in to metadata-only JSONL telemetry")
    parser.add_argument("--memory-db", type=Path, help="Opt in to local memory retrieval from this SQLite database")
    parser.add_argument("--memory-query", help="Explicit keyword query for notes sent to the model provider")
    parser.add_argument("--memory-limit", type=int, default=3, help="Maximum notes to retrieve (1-5)")
    parser.add_argument("--queue-db", type=Path, help="Opt in to a local SQLite workflow queue")
    queue_mode = parser.add_mutually_exclusive_group()
    queue_mode.add_argument("--enqueue", action="store_true", help="Persist this task in --queue-db without calling a model")
    queue_mode.add_argument("--run-next", action="store_true", help="Claim and execute one queued task from --queue-db")
    parser.add_argument("--max-attempts", type=int, default=3, help="Queue retry limit for --enqueue (1-10)")
    parser.add_argument("--lease-seconds", type=int, default=300, help="Worker lease duration for --run-next (1-86400)")
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0, help="Base retry delay for transient provider failures")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output (default)")
    return parser


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
    if args.queue_db and not (args.enqueue or args.run_next):
        print("--queue-db requires either --enqueue or --run-next.", file=sys.stderr)
        return 2
    if (args.enqueue or args.run_next) and not args.queue_db:
        print("--enqueue and --run-next require --queue-db.", file=sys.stderr)
        return 2
    if args.task_file and args.task:
        print("Use either task arguments or --task-file, not both.", file=sys.stderr)
        return 2
    if args.task_file:
        try:
            task = args.task_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Could not read task file: {type(exc).__name__}", file=sys.stderr)
            return 2
    else:
        task = " ".join(args.task)
    if args.run_next and task.strip():
        print("--run-next takes its task from the queue; do not pass task text or --task-file.", file=sys.stderr)
        return 2
    if not args.run_next and not task.strip():
        print('Provide task text or --task-file. Use --check-config for a no-network check.', file=sys.stderr)
        return 2
    if (args.enqueue or args.run_next) and (args.memory_db or args.memory_query):
        print("Queue mode cannot be combined with --memory-db/--memory-query; enqueue only non-sensitive task text.", file=sys.stderr)
        return 2
    if args.enqueue and not 1 <= args.max_attempts <= 10:
        print("--max-attempts must be from 1 to 10.", file=sys.stderr)
        return 2
    if args.run_next and not 1 <= args.lease_seconds <= 86400:
        print("--lease-seconds must be from 1 to 86400.", file=sys.stderr)
        return 2
    if args.run_next and (args.retry_delay_seconds < 0 or args.retry_delay_seconds > 3600):
        print("--retry-delay-seconds must be from 0 to 3600.", file=sys.stderr)
        return 2
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
            result = run_team(job["task"], router)
            metadata = {
                "run_id": result.get("run_id"),
                "stage_count": len(result.get("trace", [])),
                "providers": sorted({str(event.get("provider", "unknown")) for event in result.get("trace", [])}),
                "total_duration_ms": result.get("total_duration_ms"),
                "final_chars": len(result.get("final", "")) if isinstance(result.get("final"), str) else None,
            }
            store.complete(job["job_id"], metadata)
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
                failed = store.fail(job["job_id"], error_type, retryable=retryable,
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
        result = run_team(task, router, telemetry_path=args.telemetry, memory_context=memory_context)
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
