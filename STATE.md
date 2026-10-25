# Project State
Last updated: 2026-10-23
Current phase: Phase 2 — safe operational baseline
Repository: ghith93/agent-team-starter
Working branch: fix/phase2-operational-baseline
Baseline reference: backup/pre-audit-2026-10-23

## Project purpose
A free-first Python multi-agent workflow (planner → executor → reviewer) with model routing, offline regression tests, evaluation reports, and security checks.

## Verified from repository inspection
- Python project with source under `agent_team/`.
- Existing offline regression workflow: `.github/workflows/offline-tests.yml`.
- Existing YAML syntax workflow: `.github/workflows/yaml-syntax.yml`.
- Existing scheduled security workflow: `.github/workflows/security.yml`.
- Dependabot configuration exists at `.github/dependabot.yml`.
- `agent_team/web_research.py` documents that URL validation is defense-in-depth and DNS rebinding is not fully prevented by application-level validation.
- The `main` branch was reported unprotected during the initial audit.
- The repository is private according to the repository metadata read during the audit.
- FreeLLMAPI integration was previously removed; do not reintroduce it without a new explicit requirement.

## Completed in this change
- Created a recovery reference branch: `backup/pre-audit-2026-10-23`.
- Created this state register and the initial operations roadmap/runbook/changelog on an isolated repair branch.

## Not yet verified
- Whether GitHub Secret Scanning and Push Protection are enabled for this repository.
- Whether branch protection/rulesets can be enabled with the current account permissions.
- Whether a live application is deployed and what its health endpoint is.
- Whether an independent, restorable backup destination exists.
- Whether the historical Git commit graph contains exposed credentials. A workflow scan is not proof that history is clean.
- Whether current provider credentials are valid or have remaining free quota. No live model calls were made.

## Open risks
1. Main branch protection is not enabled (initial audit evidence).
2. No independent scheduled backup and restore drill has been verified.
3. No external service health monitor has been verified.
4. Web fetcher requires network-level egress controls for hostile or public-facing use.
5. No root license file was found in the inspected repository tree; licensing decision is pending owner/project intent.
6. Do not claim 24/7 availability based on scheduled GitHub Actions alone.

## Operating constraints
- Do not commit API keys, tokens, passwords, customer data, cookies, or private identifiers.
- Keep provider keys in GitHub Actions Secrets or the deployment platform's secret manager.
- Do not trigger paid/live inference, public deployment, destructive operations, or public publishing without explicit approval.
- Prefer feature branches and pull requests; do not write directly to `main`.
- Before risky changes, preserve a recovery point and document rollback.
- Treat all automated scan findings as candidates requiring review; never silence broad patterns merely to make a workflow green.

## Next actions (updated 2026-10-23 18:53 UTC)
1. Run a safe synthetic secret-detection regression that verifies only the intended test strings are excluded and that a non-exempt canary is still detected.
2. Review repository security settings in GitHub UI because the connected integration cannot access the branch-protection endpoint (HTTP 403); do not infer that Secret Scanning, Push Protection, or branch protection is enabled.
3. Identify the actual runtime/deployment target before designing external monitoring or backups.
4. Plan an independent backup destination and a restore drill; the in-repository recovery ref is not an independent backup.
5. Keep PR #16 in draft and unmerged pending owner review.

## Latest validation — 2026-10-23 18:50 UTC
- Commit `e7b9d7cc48773bbd384ef12a0edcf408a4ca0a33` passed YAML syntax validation: https://github.com/ghith93/agent-team-starter/actions/runs/40006567343
- Offline regression checks passed: https://github.com/ghith93/agent-team-starter/actions/runs/40006567235
- Promotion readiness gate passed: https://github.com/ghith93/agent-team-starter/actions/runs/40006567254
- Tests and security scans passed: https://github.com/ghith93/agent-team-starter/actions/runs/40006567240. The security workflow's detect-secrets gate passed after tightening the line exclusion; Bandit, pip-audit, Semgrep, and Gitleaks also succeeded.
- An earlier commit, `73fc40a4dd7fb35bb21e18448e7493a5f38177e9`, failed only the detect-secrets findings gate; this was superseded by the passing `e7b9d7c` run. The older failed result remains in history and is not hidden.
- CI is green for the validated commit only. This does not prove that all repository history is free of credentials or that GitHub-level push protection is enabled.
- PR #16 remains draft and unmerged. No live inference, deployment, merge, or account-level security setting changes were performed.
