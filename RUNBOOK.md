# Operations Runbook (iPhone-first)

## Safety rules
- Never paste a provider key, GitHub token, cookie, recovery code, or customer data into chat, an issue, a commit, or a public log.
- Do not merge a change while required checks are failing or unexplained.
- Do not use a GitHub Actions workflow as proof that a continuously running service is healthy.
- Do not assume a backup is usable until a restore has been tested.

## Check CI
1. Open https://github.com/ghith93/agent-team-starter/actions in Safari or the GitHub app.
2. Open the latest run for the branch being reviewed.
3. Inspect each failed step and its log. Share only redacted error messages.
4. Do not rerun a live-provider workflow unless its purpose, quota impact, and secrets are understood.

## Recover from a bad change
1. Open the repository and select the relevant branch.
2. Inspect the commit or pull request that introduced the change.
3. Prefer reverting the specific commit through GitHub's UI or creating a revert pull request.
4. Do not delete branches or rewrite history as the first response.
5. Re-run offline CI and security checks after the revert.

## If a credential may have leaked
1. Treat it as compromised even if the file was deleted.
2. Revoke/rotate the credential at the provider immediately.
3. Update the corresponding GitHub Actions Secret or deployment secret.
4. Review workflow logs, artifacts, issues, pull requests, and commit history for exposure.
5. Run a history-aware secret scan. Rewrite history only with a deliberate recovery plan because it affects collaborators and references.
6. Never post the old or replacement credential in an issue or chat.

## If the model provider fails
1. Open the latest workflow or application log and identify the HTTP status/category, not the secret-bearing request.
2. For 401/403: check secret name, scope, and provider permissions; do not retry in a loop.
3. For 402 or quota/billing errors: stop live calls and verify the provider's current plan/limits.
4. For 429: respect Retry-After if supplied and use bounded backoff.
5. For 5xx/network errors: retry only a limited number of times with exponential backoff and jitter.
6. Run offline tests separately to distinguish local regressions from provider outages.

## If a scheduled workflow does not run
1. Open Actions and inspect the workflow's latest run and workflow file.
2. Confirm the default branch contains the workflow and that Actions are enabled.
3. Check repository activity and GitHub's current scheduled-workflow restrictions.
4. Use workflow_dispatch for a manual diagnostic run when available.
5. Do not add fake commits merely to keep the repository active; design an explicit, auditable maintenance check instead.

## Backup recovery
1. Identify the latest backup artifact and its creation time.
2. Confirm the backup is in a separate destination/account from the primary repository.
3. Restore into a new branch or temporary location first.
4. Validate file counts, checksums, and tests.
5. Replace production state only after the restore has been verified and the rollback path is documented.

## Monitoring and alerting
- Alert delivery is not considered configured until a test notification is received on the intended phone/email/chat.
- Never put a Telegram bot token, webhook secret, or email credential in workflow YAML.
- Keep health endpoints minimal: return status only; do not return environment variables, stack traces, prompts, or provider responses.
