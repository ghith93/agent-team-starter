# Project State
Last updated: 2026-10-26
Current phase: Phase 2 — durable workflow primitives merged; deployment acceptance remains open
Repository: ghith93/agent-team-starter
Last verified main checkpoint before PR #54: `c3d351e359edb0653d218e27c08ed66e76550dc6`; all five required checks passed on that exact commit.
Recovery reference: `backup/pre-audit-2026-10-23`

## Project purpose
A free-first Python multi-agent workflow (planner → executor → reviewer) with model routing, offline regression tests, evaluation reports, local durable queue/memory primitives, and security checks.

## Recently merged
- PR #26 narrowed secret-scanner exclusions; broad provider-key line suppression was removed.
- PR #27 added the operational state register, roadmap, iPhone-first runbook, `.gitignore` safeguards, and pending-license decision record.
- PR #28 added an opt-in SQLite workflow queue with leases, bounded retries, stale-worker fencing, local memory retrieval, CLI queue modes, health/backup/restore helpers, systemd templates, and regression tests.
- PR #28 CI passed on the reviewed head: offline regression/evaluator suite, YAML validation, Gitleaks, Bandit, pip-audit, Semgrep, detect-secrets, isolated security audits, and promotion-readiness gate.
- PR #39 fixed required isolated-security checks for docs-only pull requests; PR #40 added a regression test for that trigger contract; PR #41 and PR #42 refreshed operational status; PR #45 added a synthetic secret-scanner canary and shared fail-closed gate.

## Verified
- The repository is public. PR #53 merged the iPhone-only zero-cost completion plan at `c3d351e359edb0653d218e27c08ed66e76550dc6`; all five required checks passed on that exact commit. PR #54 then refreshed the status documents; its post-merge checks are tracked independently.
- The active `main` ruleset (`25836352`) requires pull requests and six checks: `tests`, `Offline regression and evaluator suites`, `Python static security analysis`, `Dependency vulnerability audit`, `Gitleaks secret scan`, and `Parse workflow and Dependabot YAML`. Required approvals are set to zero; force pushes are blocked. `strict=false` means the PR branch need not be up to date before merge.
- PR #39 merged a fix so the isolated security workflow reports required checks on docs-only pull requests.
- Python project sources live under `agent_team/`.
- On checkpoint `c3d351e359edb0653d218e27c08ed66e76550dc6`, all five required checks completed successfully: `tests`, YAML parsing, Gitleaks, offline regression/evaluator, and Python SAST/secrets/dependency audit. The synthetic canary was detected and rejected by the shared gate on PR #45 before merge.
- `agent_team/workflow_store.py` implements durable SQLite queue state; `agent_team/memory_store.py` provides opt-in local memory retrieval.
- Deployment and systemd files are templates only; no host has been provisioned, and no service has been installed or started.
- The security workflow on `main` retains the narrow exclusions merged in PR #26. `scripts/check_detect_secrets.py` is the shared fail-closed gate used by the production scan and the synthetic canary test.
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

## Hosting decision update — 2026-10-26
- Official Render documentation rules out Render Free as a durable SQLite worker host: free services can spin down after 15 minutes without inbound traffic, their local filesystem is ephemeral, and persistent disks are unavailable on the free tier. Sources: https://render.com/docs/free and https://render.com/docs/disks.
- Do not deploy the current SQLite queue to an ephemeral filesystem or treat a periodic hosted CI job as a persistent worker.
- The low-risk path is an existing operator-controlled Linux host with persistent local storage, systemd, restrictive service permissions, and a separately managed alert/backup destination. None is currently provisioned or verified.
- A serverless alternative (for example, Cloudflare Workers + Queues + D1) is an architecture migration, not a drop-in host: it requires replacing SQLite-specific queue semantics and adding migration, idempotency, failure/retry, security, and recovery tests before acceptance. No Cloudflare account, resource, or migration has been created.

## Zero-cost iPhone execution plan
- PR #53 merged `docs/IPHONE_ZERO_COST_COMPLETION_PLAN.md` at checkpoint `c3d351e359edb0653d218e27c08ed66e76550dc6`. It records the mobile UI checks, evidence standards, free-only operational tests, and hard blockers that cannot be proven from repository access alone. This is documentation, not evidence that those live checks have been performed.

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


## Verified follow-up — 2026-10-26 01:32 UTC

- At this checkpoint, `main` was `8581565462c95bc726515bf60da2296c44800858` (commit: `fix: detect restorable queue backups when live database is missing`).
- The change updates the systemd restore-test path to discover and verify the newest valid backup even when the live queue database has not been created, and adds regression coverage for that condition.
- CI for this exact main SHA completed successfully: offline regression checks, YAML syntax validation, isolated security audits, and the full tests/security workflow. The eight reported check runs all concluded `success`, including tests, offline regression/evaluator, Gitleaks, Python SAST/secrets/dependency audit, Semgrep, dependency audit, and YAML validation. Evidence: https://github.com/ghith93/agent-team-starter/actions/runs/40254651319 and https://github.com/ghith93/agent-team-starter/actions/runs/40254651292.
- This verifies repository checks only. It does not close external/runtime acceptance gaps: Hostless aggregate runtime logs still return HTTP 500 (issue #73); ruleset bypass/zero-approval/non-strict freshness remains unresolved (issue #38); Secret Scanning/Push Protection settings remain unverified; and an independent encrypted off-host backup/restore drill plus end-to-end alert delivery remain unverified.
- No live model calls, paid provider requests, deployment changes, or external notifications were performed as part of this repository review.


## Verified follow-up — 2026-10-26 01:43 UTC

- PR #87 merged the HTML text-extraction fix at main commit `4d9ecbe7d2beed917e949cd9ae4780cb62dc54c9`: ignored HTML elements are now tracked by matching tag, preventing a mismatched closing tag from exposing content within an SVG/script/style/noscript region.
- On the exact PR head `37ad4f68e2b3f12b4298c4232f975727ccd109b7`, the regression suite, deterministic benchmark/promotion gate, YAML validation, Gitleaks, Python SAST, Semgrep, and dependency audit all completed successfully before merge.
- Post-merge checks on `4d9ecbe7d2beed917e949cd9ae4780cb62dc54c9` were still running at the time of this update. Verify their final conclusions before treating the merged commit as fully green.
- This code change does not resolve the external Hostless aggregate runtime-logs HTTP 500 in issue #73, and does not prove network-level egress policy, a persistent production host, independent encrypted backup/restore, external alert delivery, or GitHub Secret Scanning/Push Protection settings.
- The Notion Custom Agent search could not run because the connected workspace requires a Business plan or higher. No metered external research or live model provider calls were launched.


## Operating-scope decision — 2026-10-26

- Owner decision: do not block progress on a continuously running 24/7 worker; a bounded, on-demand pilot is acceptable.
- No operator-managed Linux host is available. Do not install systemd templates or claim host-level restart/recovery evidence.
- The existing queue supports finite local execution with `--run-next` or `--worker --max-jobs 1`, but those commands still require an environment that can run Python and access the configured provider. The current Hostless read-only workflow only inspects deployment status/logs; it does not execute user tasks.
- Therefore the immediate target is a safe, manually initiated, bounded pilot—not a 24/7 service. Keep live model calls disabled until the execution path, provider/quota, and task data are explicitly approved. Do not represent CI or a read-only deployment inspection as proof that an agent task ran.
- Current `main` checkpoint: `6bef4442cbb381161796d8eaf63eb6a4019edc39`. All five check runs observed on this exact SHA completed successfully: tests, offline regression/evaluator suites, YAML validation, Gitleaks, and Python SAST/secrets/dependency audit.
- Still unresolved for any hosted pilot: Hostless aggregate runtime logs return HTTP 500 (issue #73); current deployment activation after the latest main commit has not been re-verified; network-level egress enforcement, independent encrypted backup/restore, external alert delivery, and authoritative GitHub Secret Scanning/Push Protection settings remain unverified.

## Verified follow-up — 2026-10-26 01:55 UTC

- Current `main` checkpoint: `e0ebd15f0c36edca613ee967cbf2961f075eb6f9` (PR #89: code-only Graphify CI pilot).
- The latest `Tests and security scans` workflow on this exact SHA completed successfully: offline regression/evaluator suites, Gitleaks, and Python SAST/secrets/dependency audit. The audit completed all steps successfully, including Bandit, pip-audit, Semgrep, detect-secrets, and its fail-closed outcome gate. Evidence: https://github.com/ghith93/agent-team-starter/actions/runs/40256296008.
- Graphify code-only pilot succeeded on both PR and main: https://github.com/ghith93/agent-team-starter/actions/runs/40256197460 and https://github.com/ghith93/agent-team-starter/actions/runs/40256296045. The workflow uses no LLM backend.
- Issue #73 remains open: Hostless aggregate runtime-log requests still return HTTP 500; deployment-scoped fallback logs contain build output only, not runtime logs. Do not treat HTTP 200 from the fallback as proof of runtime log availability. Follow up with Hostless support privately using request IDs from the short-lived private artifact; never put request IDs or raw responses in public issues.
- These checks verify repository CI and the read-only diagnostic workflow only. They do not prove that a user task executed, that live model calls are authorized/working, or that external alerts, independent off-host restore, network-level egress controls, or GitHub Secret Scanning/Push Protection settings are verified.
