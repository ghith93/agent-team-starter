# On-demand agent tasks using GitHub Actions

## Decision

Use a manually triggered GitHub Actions workflow instead of Hostless for bounded, occasional tasks. This needs no persistent Linux server and does not claim to provide a continuously running worker.

Workflow: `.github/workflows/on-demand-agent-task.yml`

## How to run it

1. Open the repository's **Actions** tab.
2. Select **On-demand agent task (GitHub-hosted runner)** and choose **Run workflow**.
3. Enter one task and keep it non-sensitive. The workflow input is stored in GitHub Actions run metadata.
4. Leave **authorize_provider_calls** disabled to verify the safety guard; this makes no model request.
5. To actually execute the task, explicitly enable **authorize_provider_calls** and run it. This sends the task to OpenRouter and may consume provider quota. The repository must have an `OPENROUTER_API_KEY` Actions secret configured and the account must have access to an eligible free model.
6. Download the `agent-task-result` artifact from the run. It expires after one day.

## Safety and operating limits

- The workflow runs only on manual dispatch; it has no push, schedule, web endpoint, or always-on worker.
- A Boolean authorization input defaults to false. The task job is skipped unless the operator explicitly enables it.
- Only the `openrouter/free` model route is configured. A “free” model label does not guarantee availability, quota, quality, or zero ancillary costs.
- The workflow never prints the task or generated content to job logs. The result artifact contains generated content and is available to people with repository Actions access; use only non-sensitive tasks.
- Do not place API keys or private customer data in task input, workflow files, logs, or artifacts.
- The workflow executes one task per run. GitHub-hosted runner storage is temporary. This does not preserve the SQLite queue across runs, provide a persistent API, or replace the local durable queue.
- No live provider request is made during implementation or CI validation. The first real run must be explicitly authorized by the operator.

## Why not migrate to another always-on host now?

A serverless platform such as Cloudflare Workers + Queues + D1 is a possible future path, but it is not a drop-in replacement for the current Python + SQLite queue. It requires an architecture migration and tests for persistence, leases, retries, idempotency, security, and recovery. Since continuous uptime is not required, manual GitHub Actions is the smaller and safer interim replacement.

## Hostless retirement boundary

This repository change removes the Hostless-specific inspection workflow and script so the project no longer relies on Hostless diagnostics. It cannot delete a Hostless account, cancel an external subscription, or stop a deployment in the Hostless dashboard. If any external Hostless resource was created, the account owner must separately stop/delete it in Hostless and verify any billing or connected GitHub access there.
