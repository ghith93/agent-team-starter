# Solo-Maintainer Security Hardening Runbook

**Scope:** repository settings that require an owner-operated GitHub UI session. This document does not claim that settings have been changed.

## Current verified state (2026-10-26)

The active ruleset named `main` targets `refs/heads/main`. Its current configuration was read from the GitHub rulesets API:

- Pull request required; required approving reviews: **0**.
- Required status checks are configured, but strict/up-to-date checks are **disabled**.
- The bypass list contains repository role ID `5` (repository administrator) with mode **always**.
- Non-fast-forward updates are blocked.
- Force-pushes and deletion should be verified in the live UI rather than inferred from this API response.

The workflow that passes `HOSTLESS_TOKEN` to the inspection script is now manual-only, and a regression test protects that property.

## Recommended configuration for a solo maintainer

Open [the existing main ruleset](https://github.com/ghith93/agent-team-starter/rules/25836352) while signed in as a repository administrator.

1. **Target and enforcement**
   - Target branch: `main` / `refs/heads/main`.
   - Enforcement: `Active`.
   - Keep the pull-request requirement enabled.
2. **Approvals**
   - Keep required approving reviews at `0` while there is no independent reviewer. Do not enable CODEOWNERS approval requirements until a qualified reviewer exists.
   - This is a solo-maintainer compromise, not equivalent to independent review.
3. **Required checks**
   - Keep all required checks enabled and ensure each required context corresponds to a real check produced by GitHub Actions.
   - Enable the strict option, usually worded **Require branches to be up to date before merging**, after verifying the current checks complete reliably.
   - Preserve the no-force-push and no-delete protections.
4. **Emergency bypass**
   - In **Bypass list**, change the repository-administrator entry from **Always** to **For pull requests only**.
   - This retains an explicit emergency exception but requires a PR and leaves a reviewable/auditable trail. It is not time-limited and is still powerful; use it only when normal checks cannot reasonably be satisfied.
   - Do not add broad write/maintain roles to the bypass list. If the UI cannot offer the pull-requests-only mode for this actor, remove the bypass entry rather than leaving an unrestricted bypass; admin recovery may still require changing the rule later.
5. **Save and verify**
   - Save the ruleset.
   - Re-open it and verify the values above.
   - Open a harmless test PR and confirm a failed required check blocks merge, a successful up-to-date PR can merge normally, and a direct push to `main` is rejected. Do not deliberately push unsafe changes to production.

GitHub's official documentation:
- [Creating rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)
- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

## Repository security settings to verify separately

From **Settings → Code security and analysis**, review the available toggles and enable appropriate protections when supported by the plan and repository configuration:

- Dependabot alerts and security updates.
- Secret scanning and push protection, if available.
- Code scanning / CodeQL or the project's existing static-analysis workflow.
- Dependency review for pull requests, if supported and compatible with the workflow.
- Actions permissions: restrict the default token to read-only; require approval for external fork workflows where applicable.

Do not disable existing checks to make a PR green. If a feature is unavailable on the current plan, record that limitation rather than assuming it is active.

## Operational limitations that require external access

- Hostless aggregate runtime logs endpoint previously returned HTTP 500; deployment-scoped log retrieval worked. Provider-side remediation or credentials may be needed to diagnose the aggregate endpoint.
- A working systemd template does not prove a production service is installed or running. Confirm the real host/service and perform a restore drill before declaring 24/7 operation or backup recovery verified.
- A public repository's license choice is a legal/owner decision. `LICENSE_PENDING.md` remains unresolved; do not add a license or copy upstream code before the owner chooses.
