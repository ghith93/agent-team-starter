# Project State
Last updated: 2026-10-25
Current phase: Phase 2 — durable workflow primitives merged; deployment acceptance remains open
Repository: ghith93/agent-team-starter
Current main commit at this state update: `0761339734a7dc8e24830c96c833ef330e28e446`
Recovery reference: `backup/pre-audit-2026-10-23`

## Project purpose
A free-first Python multi-agent workflow (planner → executor → reviewer) with model routing, offline regression tests, evaluation reports, local durable queue/memory primitives, and security checks.

## Recently merged
- PR #26 narrowed secret-scanner exclusions; broad provider-key line suppression was removed.
- PR #27 added the operational state register, roadmap, iPhone-first runbook, `.gitignore` safeguards, and pending-license decision record.
- PR #28 added an opt-in SQLite workflow queue with leases, bounded retries, stale-worker fencing, local memory retrieval, CLI queue modes, health/backup/restore helpers, systemd templates, and regression tests.
- PR #28 CI passed on the reviewed head: offline regression/evaluator suite, YAML validation, Gitleaks, Bandit, pip-audit, Semgrep, detect-secrets, isolated security audits, and promotion-readiness gate.

## Verified
- Python project sources live under `agent_team/`.
- Offline regression, YAML validation, security scan, and promotion-readiness workflows exist and passed on PR #28's head.
- `agent_team/workflow_store.py` implements durable SQLite queue state; `agent_team/memory_store.py` provides opt-in local memory retrieval.
- Deployment and systemd files are templates only; no host has been provisioned, and no service has been installed or started.
- The security workflow on `main` retains the narrow exclusions merged in PR #26.
- FreeLLMAPI integration was previously removed; do not reintroduce it without a new explicit requirement.

## Not yet verified / open risks
1. Main-branch ruleset/protection state is not verified.
2. GitHub Secret Scanning and Push Protection settings are not verified.
3. No live worker or 24/7 deployment exists as far as the available evidence shows.
4. No external health alert has been configured and test-delivered to a real destination.
5. No independent off-host backup and operational restore drill has been verified. The included backup/restore scripts and CI tests do not establish off-host recovery.
6. SQLite stores task text and local backups in plaintext. Never enqueue credentials, confidential prompts, or private customer data; restrict backup file access and encrypt any external backup destination.
7. Web fetching still needs network-level egress controls for hostile/public-facing use; application URL validation alone does not fully prevent DNS rebinding.
8. No root license has been selected; `LICENSE_PENDING.md` is a decision record, not a license.
9. CI scans do not prove the entire Git history is free of credentials or that provider keys/quotas are valid.

## Operating constraints
- Do not commit API keys, tokens, passwords, cookies, recovery codes, or customer data.
- Do not trigger paid/live inference or spend provider quota without explicit authorization.
- Prefer feature branches and pull requests; do not write directly to `main`.
- Treat scan findings as candidates for review; never weaken scanners broadly to make a workflow green.
- Do not claim 24/7 availability based on templates or scheduled GitHub Actions.

## Next actions
1. Verify repository branch protection and secret-protection settings with authorized GitHub access.
2. Decide whether/where to host the worker; assess free-tier sleep, quotas, persistent disk, and secret storage before deployment.
3. Configure an external health check and alert destination only after a real endpoint and destination exist; test notification delivery.
4. Configure an independent encrypted backup destination and complete a restore drill.
5. Decide the project license after checking ownership and third-party content.
6. Run a genuine authenticated cross-model evaluation only if existing authorized CLI sessions are available; do not spend paid quota by default.

## Limits
- No live model calls, deployment, host provisioning, external alert delivery, independent backup, or account-level security setting changes were performed.
- Passing CI verifies the tested commit and checks only; it does not prove production reliability, complete history cleanliness, or 24/7 operation.
