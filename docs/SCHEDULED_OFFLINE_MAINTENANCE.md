# Scheduled offline maintenance

## What runs automatically

The `.github/workflows/scheduled-offline-maintenance.yml` workflow runs every Monday at 09:17 UTC and can also be started manually from GitHub Actions.

It runs the local release tests, Python compilation, skill metadata lint, local tooling inventory, provider-configuration check, and deterministic offline benchmark. It publishes available reports as a seven-day artifact.

## Provider and cost boundary

- This workflow does not call Gemini, OpenRouter, or any other hosted model.
- It does not receive or read provider API secrets.
- `python -m agent_team.cli --check-config` reports configured provider names without making a network request.
- Installing pinned project dependencies uses package indexes and may consume GitHub Actions minutes, but does not send a task to an AI provider.
- The scheduled workflow is a health-check and readiness loop. It does not autonomously modify code, open pull requests, or run the multi-agent planner/executor/reviewer against a hosted model.

## Running multi-agent tasks

Use the separate [on-demand agent task workflow](../.github/workflows/on-demand-agent-task.yml) when you want the planner, executor, and reviewer to process a task. A live run requires explicitly enabling `authorize_provider_calls` and configuring the `OPENROUTER_API_KEY` repository secret. Do not enable it unless you authorize the provider request and possible quota use.

## Limitations

GitHub scheduled workflows are best-effort and may be delayed. This is not a continuously running agent or a persistent queue worker. The workflow is read-only with respect to repository contents; inspect the artifact and create a pull request for any proposed code changes.
