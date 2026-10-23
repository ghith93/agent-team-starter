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

## Next actions
1. Run CI, YAML validation, and security checks on this branch.
2. Review and tighten `.gitignore` without excluding security-relevant files.
3. Inspect the complete secret-scanning workflow and ensure Gitleaks runs on pull requests and pushes.
4. Design monitoring and backup only after confirming the deployment target and available secrets.
5. Verify GitHub repository security settings and branch protection in repository settings.
6. Open a pull request after the changes pass; do not merge automatically.


## Update after first repair-branch validation — 2026-10-23 18:35 UTC
- Pull request opened as draft: https://github.com/ghith93/agent-team-starter/pull/16
- YAML syntax validation passed: https://github.com/ghith93/agent-team-starter/actions/runs/40004421410
- Offline regression checks passed: https://github.com/ghith93/agent-team-starter/actions/runs/40004421199
- Tests and security scans workflow passed: https://github.com/ghith93/agent-team-starter/actions/runs/40004421478
- The successful security workflow included Bandit, pip-audit, Semgrep, detect-secrets, and Gitleaks steps. This is evidence of workflow success for this commit only, not a guarantee that no secret exists anywhere or that repository-level push protection is enabled.
- Created follow-up issues:
  - https://github.com/ghith93/agent-team-starter/issues/17 — verify repository security settings and main-branch rules.
  - https://github.com/ghith93/agent-team-starter/issues/18 — independent backup and restore drill.
  - https://github.com/ghith93/agent-team-starter/issues/19 — runtime monitoring and mobile alerting.
- The web research module already fails closed unless an explicitly configured trusted egress proxy is present; its docstring and README warn that the proxy must enforce destination restrictions. This is an existing mitigation, not a newly added fix in this PR.
- No deployment target or health endpoint has been confirmed, so a truthful 24/7 monitor cannot yet be configured without guessing.
- Current pull request remains a draft and has not been merged.
