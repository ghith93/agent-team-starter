# Project State
Last updated: 2026-10-25
Current phase: Phase 2 — safe operational baseline
Repository: ghith93/agent-team-starter
Working branch: fix/phase2-baseline-main-clean
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
- The main branch was reported unprotected during the initial audit; current protection settings have not been verified.
- FreeLLMAPI integration was previously removed; do not reintroduce it without a new explicit requirement.
- PR #26 narrowed secret-scanner exclusions and merged into `main` at commit `d388caa522c3166aaa574c7f414229971f4b6ca0`.

## Completed in this change
- Reapplied the operational documentation on a clean branch based on current `main`, preserving the merged secret-scanner fix.
- Kept the license decision explicit rather than adding a license without owner intent.

## Not yet verified
- Whether GitHub Secret Scanning and Push Protection are enabled for this repository.
- Whether branch protection/rulesets can be enabled with the current account permissions.
- Whether a live application is deployed and what its health endpoint is.
- Whether an independent, restorable backup destination exists.
- Whether the historical Git commit graph contains exposed credentials. A workflow scan is not proof that history is clean.
- Whether current provider credentials are valid or have remaining free quota. No live model calls were made.

## Open risks
1. Main branch protection is not verified.
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

## Next actions
1. Run CI on this clean branch and verify all mandatory checks pass.
2. Run a safe synthetic secret-detection regression that confirms a non-exempt canary is still detected.
3. Review repository security settings in GitHub UI because the connected integration cannot verify branch protection; do not infer settings are enabled.
4. Identify the actual runtime/deployment target before designing external monitoring or backups.
5. Plan an independent backup destination and restore drill.
6. Keep the PR in draft until CI and review are complete.

## Limits
- No live inference, deployment, merge, or account-level security setting changes were performed.
- CI success is limited to the exact commit and checks recorded by GitHub; it is not proof of 24/7 availability or a clean entire history.
