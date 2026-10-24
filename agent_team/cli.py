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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Free-first Planner → Executor → Reviewer agent team")
    parser.add_argument("task", nargs="*", help="Task text (omit when using --task-file)")
    parser.add_argument("--task-file", type=Path, help="Read task text from a UTF-8 file")
    parser.add_argument("--check-config", action="store_true", help="Report configured provider names only; makes no API calls")
    parser.add_argument("--telemetry", type=Path, help="Opt in to metadata-only JSONL telemetry")
    parser.add_argument("--memory-db", type=Path, help="Opt in to local memory retrieval from this SQLite database")
    parser.add_argument("--memory-query", help="Explicit keyword query for notes sent to the model provider")
    parser.add_argument("--memory-limit", type=int, default=3, help="Maximum notes to retrieve (1-5)")
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
    if not task.strip():
        print('Provide task text or --task-file. Use --check-config for a no-network check.', file=sys.stderr)
        return 2
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
