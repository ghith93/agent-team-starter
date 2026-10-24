# Durable local workflow queue

The queue is opt-in. It does not start a background service or make GitHub Actions run continuously.

## Requirements

- Python environment and project dependencies installed.
- At least one configured model provider for actual execution.
- A local writable path for a SQLite database. Keep it outside the repository and back it up only to a trusted destination.
- Do not queue secrets, credentials, personal information, confidential prompts, or customer records. SQLite stores task text in plaintext.

## Add a task without calling a model

```bash
python -m agent_team.cli --queue-db "$HOME/.agent-team/queue.sqlite3" --enqueue "Prepare a non-sensitive task"
```

This creates the database if needed and writes the task in a `queued` state. It does not call a provider.

Set a bounded retry allowance:

```bash
python -m agent_team.cli --queue-db "$HOME/.agent-team/queue.sqlite3" --enqueue --max-attempts 3 "Summarize public release notes"
```

## Execute one ready task

```bash
python -m agent_team.cli --queue-db "$HOME/.agent-team/queue.sqlite3" --run-next
```

Each invocation claims at most one ready task using a lease, runs the existing Planner → Executor → Reviewer flow, and persists a metadata-only result. It does not save generated output in the queue database. The task itself remains stored as plaintext.

Transient provider errors (network/unknown status, HTTP 429, or HTTP 5xx) are requeued with bounded exponential backoff while attempts remain. Authentication, payment, invalid-request, and other non-transient failures are terminal. A later invocation can recover expired worker leases.

Run the command again to process another ready task. An empty queue returns successfully without calling a provider.

## Memory mode

Queue mode intentionally cannot be combined with `--memory-db` or `--memory-query` in this initial integration. This avoids silently mixing separate plaintext data stores or implying that memory is snapshotted with a queued task.

## Operational limitations

- This is a local, single-machine SQLite queue, not a distributed queue.
- `--run-next` processes one job and exits. No scheduler, daemon, automatic process restart, health alert, backup job, or deployment is included.
- A lease reduces abandoned-job risk but cannot guarantee exactly-once external model calls. A crash after the provider returns but before the success state is committed may cause a later retry and duplicate provider usage.
- Model-provider calls can use external services and may be subject to provider limits or policies. No provider call occurs for `--enqueue`.
- Before any unattended 24/7 deployment, configure a supervised runtime, log rotation, monitoring/alerts, secure secret injection, backup/restore tests, and a policy for handling private data.
