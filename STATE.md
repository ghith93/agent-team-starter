# Project State
Last updated: 2026-10-26
Current phase: Phase 2 — durable workflow primitives merged; deployment acceptance remains open
Repository: ghith93/agent-team-starter
Current main commit at this state update: `0f46b28ae6b6c624fb54549b2ebbf48474529aa3`
Recovery reference: `backup/pre-audit-2026-10-23`

## Project purpose
A free-first Python multi-agent workflow (planner → executor → reviewer) with model routing, offline regression tests, evaluation reports, local durable queue/memory primitives, and security checks.

## Recently merged
- PR #26 narrowed secret-scanner exclusions; broad provider-key line suppression was removed.
- PR #27 added the operational state register, roadmap, iPhone-first runbook, `.gitignore` safeguards, and pending-license decision record.
- PR #28 added an opt-in SQLite workflow queue with leases, bounded retries, stale-worker fencing, local memory retrieval, CLI queue modes, health/backup/restore helpers, systemd templates, and regression tests.
- PR #28 CI passed on the reviewed head: offline regression/evaluator suite, YAML validation, Gitleaks, Bandit, pip-audit, Semgrep, detect-secrets, isolated security audits, and promotion-readiness gate.
- PR #39 fixed required isolated-security checks for docs-only pull requests; PR #40 added a regression test for that trigger contract; PR #41 and PR #42 refreshed operational status and reconciled root state/roadmap documentation.

## Verified
- The repository is public and `main` now points to `0f46b28ae6b6c624fb54549b2ebbf48474529aa3` after PR #42 merged.
- The active `main` ruleset (`25836352`) requires pull requests and six checks: `tests`, `Offline regression and evaluator suites`, `Python static security analysis`, `Dependency vulnerability audit`, `Gitleaks secret scan`, and `Parse workflow and Dependabot YAML`. Required approvals are set to zero; force pushes are blocked. `strict=false` means the PR branch need not be up to date before merge.
- PR #39 merged a fix so the isolated security workflow reports required checks on docs-only pull requests.
- Python project sources live under `agent_team/`.
- On `0f46b28ae6b6c624fb54549b2ebbf48474529aa3`, the observed `tests`, YAML validation, Gitleaks, and offline regression/evaluator checks passed; the aggregate Python SAST/secrets/dependency audit was still in progress at the last observation. Do not mark all post-merge checks complete until that job finishes.
- `agent_team/workflow_store.py` implements durable SQLite queue state; `agent_team/memory_store.py` provides opt-in local memory retrieval.
- Deployment and systemd files are templates only; no host has been provisioned, and no service has been installed or started.
- The security workflow on `main` retains the narrow exclusions merged in PR #26.
- FreeLLMAPI integration was previously removed; do not reintroduce it without a new explicit requirement.

## Not yet verified / open risks
1. GitHub Secret Scanning and Push Protection settings remain unverified; do not claim they are enabled until checked in repository settings.
2. The ruleset's repository-role bypass uses `bypass_mode=always`, and required approvals are zero. Issue #38 tracks this governance tradeoff. Review whether bypass can be narrowed while preserving the intended solo-maintainer workflow.
3. The ruleset uses `strict=false`; branches need not be up to date with `main` before merging. Decide whether to enable strict checks.
4. No live worker or 24/7 deployment exists as far as the available evidence shows.
5. No external health alert has been configured and test-delivered to a real destination.
6. No independent off-host backup and operational restore drill has been verified. The included backup/restore scripts and CI tests do not establish off-host recovery.
7. SQLite stores task text and local backups in plaintext. Never enqueue credentials, confidential prompts, or private customer data; restrict backup file access and encrypt any external backup destination.
8. Web fetching still needs network-level egress controls for hostile/public-facing use; application URL validation alone does not fully prevent DNS rebinding.
9. No root license has been selected; `LICENSE_PENDING.md` is a decision record, not a license.
10. CI scans do not prove the entire Git history is free of credentials or that provider keys/quotas are valid.

## Operating constraints
- Do not commit API keys, tokens, passwords, cookies, recovery codes, or customer data.
- Do not trigger paid/live inference or spend provider quota without explicit authorization.
- Prefer feature branches and pull requests; do not write directly to `main`.
- Treat scan findings as candidates for review; never weaken scanners broadly to make a workflow green.
- Do not claim 24/7 availability based on templates or scheduled GitHub Actions.

## Next actions
1. Verify GitHub Secret Scanning and Push Protection settings and review ruleset bypass/freshness policy.
2. Decide whether/where to host the worker; assess free-tier sleep, quotas, persistent disk, and secret storage before deployment.
3. Configure an external health check and alert destination only after a real endpoint and destination exist; test notification delivery.
4. Configure an independent encrypted backup destination and complete a restore drill.
5. Decide the project license after checking ownership and third-party content.
6. Run a genuine authenticated cross-model evaluation only if existing authorized CLI sessions are available; do not spend paid quota by default.

## Limits
- No live model calls, deployment, host provisioning, external alert delivery, independent backup, or GitHub Secret Scanning/Push Protection setting changes were performed. The `main` ruleset was read and verified, but its bypass policy has not been changed.
- Passing CI verifies the tested commit and checks only; it does not prove production reliability, complete history cleanliness, or 24/7 operation.
