> **Retired on 2026-10-26:** this runbook is no longer an active deployment path. The repository's Hostless integration has been removed. Do not create or connect a Hostless resource based on this document. For occasional tasks, use [the on-demand GitHub Actions runbook](ON_DEMAND_GITHUB_ACTIONS_RUNBOOK.md). Repository changes cannot cancel an external Hostless resource or subscription; handle that separately in the Hostless account dashboard if one exists.

# Retired: Hostless deployment gate (historical reference)

Status: **NOT READY FOR PRODUCTION**. This runbook prevents connecting a live queue to a worker before storage and provider-call behavior are verified.

## What this repository is

The project is a Python CLI/worker, not an HTTP web application. The queue worker is started with:

```sh
python -m agent_team.cli --queue-db /data/queue.sqlite3 --worker
```

Do not configure it as a public web app unless an HTTP service with a health endpoint is deliberately implemented and tested. If Hostless offers a background-worker resource, that is the relevant resource type.

## Hard blockers before creating a live worker

1. **Persistent storage:** the queue implementation uses local SQLite. Do not assume an application's writable directory survives redeploys, restarts, or replacement. Confirm documented persistent-volume semantics in the account, or migrate queue state to managed PostgreSQL with migration, concurrency, retry, lease, idempotency, and restore tests.
2. **No-provider smoke mode:** a normal queue worker can call configured model providers while executing tasks. The current `--check-config` mode is safe and performs no network request, but it does not run the worker loop. Do not enqueue tasks or start a live worker as a “smoke test” until a separately tested provider-disabled synthetic execution mode exists.
3. **Cost guard:** do not add a payment method, enable paid capacity, or create a resource if the dashboard does not clearly show that it fits within the no-card free allowance. Free quotas may be shared across resources and policies can change.
4. **Secrets:** never put API keys in the repository, Docker image, build arguments, or logs. For the initial deployment, leave provider credentials absent.
5. **Least privilege:** use synthetic non-sensitive tasks only. Do not expose queue administration or the CLI as a public unauthenticated endpoint.

## Safe account inspection

1. Sign in at https://web.hostless.cloud/ and select the GitHub-connected repository.
2. Inspect resource type, runtime, start command, persistent storage options, database quota, and estimated cost before creating anything.
3. Stop if the dashboard asks for a payment method or indicates paid capacity.
4. Do not deploy the existing SQLite queue to an unverified ephemeral filesystem.
5. Record the selected runtime and storage behavior, then run the acceptance tests below before production.

## Acceptance tests required before production

- [ ] Offline regression suite passes on the exact deployed commit: `python run_tests.py`.
- [ ] The provider-disabled synthetic mode completes a task without network access or provider credentials.
- [ ] Queue state survives a worker restart and an application redeploy.
- [ ] Concurrent claims, expired leases, retries, and idempotency behavior are tested against the production storage backend.
- [ ] A backup is stored outside the app resource and restored into a separate location successfully.
- [ ] Logs contain no task text, secrets, or provider payloads by default.
- [ ] A real health/alert mechanism is configured and a test alert is received.
- [ ] CPU, memory, storage, and quota usage remain within the no-card allowance.

## Current verified limitations

Passing GitHub Actions tests does not prove Hostless deployment, persistence, external alert delivery, backup recovery, or continuous operation. Do not describe the service as 24/7 until those checks have real evidence.

Official Hostless references:
- https://docs.hostless.cloud/overview
- https://docs.hostless.cloud/plans/limits
- https://docs.hostless.cloud/plans/free-tier
- https://docs.hostless.cloud/app/overview
- https://docs.hostless.cloud/app/deployments
