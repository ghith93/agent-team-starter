# Hosting decision gate

Last reviewed: 2026-10-26

## Decision

**Do not deploy the current SQLite queue to Render Free or another runtime with ephemeral local storage.** The queue depends on durable local SQLite state. A service that sleeps, restarts unpredictably, or loses its filesystem can interrupt work or lose queued tasks.

Official references:
- Render free services: https://render.com/docs/free
- Render persistent disks: https://render.com/docs/disks
- Cloudflare Workers storage options: https://developers.cloudflare.com/workers/platform/storage-options/

Render's published free-tier constraints include automatic spin-down after inactivity, ephemeral filesystem state, and no persistent disk attachment on free services. Those constraints conflict with this project's durability requirements.

## Viable paths

### Path A — existing operator-controlled Linux host (preferred minimal-change path)

Use only if a host is already available and controlled by the operator.

Acceptance requirements:
- Supported Linux host with systemd and persistent local disk.
- Dedicated unprivileged service account; repository and virtual environment are not writable by that account.
- Provider credentials injected through a root-managed environment file or equivalent secret manager; never committed.
- Network egress restricted to required provider endpoints and an administrator-controlled safe-fetch proxy where applicable.
- Worker, health timer, backup timer, and restore-test timer installed and verified.
- External alert destination configured and a test notification received.
- Encrypted backup copied to a separate account/provider/storage boundary; restore drill completed from that copy.
- Reboot and process-restart behavior observed; logs and disk usage reviewed.
- Explicit operator approval before any live provider smoke test that may consume quota or incur charges.

No host is currently known to be provisioned, so this path is not yet deployable.

### Path B — migrate to a managed/serverless architecture

A design such as Cloudflare Workers + Queues + D1 may reduce server administration, but it is **not** a drop-in replacement for SQLite. Before choosing it:
- Define durable task schema, lease/visibility semantics, retry policy, dead-letter handling, and idempotency guarantees.
- Replace the SQLite-specific store behind a tested storage interface.
- Add migration/import/export tooling and recovery tests.
- Define secret management, provider egress controls, monitoring, alerting, and data retention.
- Verify actual free-tier quotas, region availability, service limits, and cost behavior in the target account.
- Run offline contract tests plus a bounded authenticated acceptance test only after explicit cost/credential authorization.

No account, resource, deployment, or migration has been created.

## Mandatory no-go conditions

Do not claim production readiness while any of these remain true:
- no persistent runtime host;
- no verified secret injection;
- no external alert delivery test;
- no independent encrypted backup and restore drill;
- no tested recovery after reboot/process failure;
- unresolved GitHub ruleset bypass and approval policy;
- unresolved root license decision.

## Evidence and status

This document records a decision based on published platform constraints; it does not claim a deployment or account configuration. Current project status and remaining blockers are tracked in [STATE.md](../STATE.md) and [ROADMAP.md](../ROADMAP.md).
