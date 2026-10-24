# Durable workflow state store

Status: initial, opt-in local persistence primitive; not yet wired into the CLI or run_team.

## What it provides

- File-backed SQLite storage for queued, running, succeeded, and failed jobs.
- Atomic claiming with a bounded lease, so two workers do not claim the same queued job in the same transaction.
- Recovery of expired worker leases on the next claim attempt.
- Bounded retries with exponential backoff; authentication/configuration failures can be marked non-retryable by the caller.
- Explicit state-transition checks and metadata-only error type names.
- A lightweight SQLite integrity check.

## Minimal example

```python
from agent_team.workflow_store import WorkflowStore

store = WorkflowStore("./runtime/workflow.sqlite3")  # explicit local path
job = store.enqueue("Generate a draft", max_attempts=3)
claimed = store.claim_next(lease_seconds=300)
if claimed is not None:
    try:
        # Call the application-specific worker here; this module executes no tasks.
        result = {"status": "example-only"}
        store.complete(claimed["job_id"], result)
    except Exception as exc:
        # Persist the exception type only, never the exception message.
        store.fail(claimed["job_id"], type(exc).__name__, retryable=False)
```

## Security and operational limits

- SQLite data is stored in plaintext. Do not persist API keys, passwords, cookies, customer data, or sensitive prompts/results.
- The database path is explicit; keep it outside the repository and ensure it is covered by an appropriate local backup policy.
- This is not a distributed queue, scheduler, web service, monitoring system, or cross-machine database.
- A lease cannot prevent a slow worker from continuing after its lease expires. Workers must make side effects idempotent and re-check ownership before external writes.
- The store does not automatically call model providers, execute shell commands, use a browser, or integrate with run_team.
- No 24/7 uptime or backup coverage is implied. Recovery must be tested in the intended runtime environment.

## Validation

The offline test suite covers persistence across store instances, claim/complete, delayed jobs, retry limits, lease recovery, invalid transitions, input validation, and SQLite health checks.
