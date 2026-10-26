# Live smoke test and go-live checklist

This repository is a Python CLI, not a hosted web service. The workflow below verifies that a configured OpenRouter key can complete the real four-stage Planner → Executor → Reviewer → Reviser flow. It does not deploy a permanent service.

## Run the live smoke test

1. In GitHub, open **Settings → Secrets and variables → Actions** and add repository secret `OPENROUTER_API_KEY`. Never put the key in a workflow file, issue, task, artifact, or commit.
2. Open **Actions → Live provider smoke test (explicit opt-in) → Run workflow**.
3. Enable `authorize_provider_call` only when you intend to send the fixed, non-sensitive smoke-test prompt to OpenRouter. The workflow uses only `openrouter/free`; free availability and quota are not guaranteed.
4. Inspect the job result and the short-lived `live-provider-smoke-summary` artifact. The workflow emits stage status, provider/model identifiers, elapsed time and output length only; it deliberately does not publish model output, the prompt, raw stderr, or the API key.
5. If it fails, use the failure stage/type and provider account's own usage/status pages to distinguish missing secret, authentication/payment restriction, quota/rate limit, provider outage, or malformed output. Do not enable debug logging that prints credentials or raw prompts.

A successful run means one live task completed all four stages. It is not a benchmark of reasoning quality, proof of factual correctness, or proof that the service is production-ready.

## Local smoke test

Use a trusted machine with Python 3.10+ and a protected environment variable:

```bash
python -m pip install -r requirements.txt
python run_tests.py
python -m agent_team.cli --check-config
python -m agent_team.cli "Create a short checklist for launching a simple public website"
```

The last command makes real provider calls. Do not paste the key into shell history or share the full output if it contains private task data. A successful `--check-config` only verifies local configuration presence; it does not test authentication or provider availability.

## Before unattended deployment

- Choose a host that can stay online and keep provider credentials in its secret manager.
- Run the worker under a process supervisor with a restricted service account and a local writable state directory.
- Keep the SQLite queue outside the repository; task text is stored in plaintext. Do not enqueue credentials, customer data, or confidential prompts.
- Configure resource limits, log retention, health checks, alerts, backup and restore tests, and a shutdown/restart procedure.
- Set provider quotas/budgets where supported. A free-model ID does not guarantee zero ancillary costs, uptime, or quota.
- Test representative tasks and security cases, and review results before offering the service to customers.
- Add a web/API front end and authentication/rate limiting before exposing tasks to other users. The current CLI/queue worker is not a public multi-tenant service.
- Do not integrate payments or Sham Cash until a supported API, credentials, terms and an end-to-end test environment exist.

## Current boundary

The smoke workflow is manual and opt-in; it does not run on every push, deploy a server, create credentials, or guarantee continuous operation. Offline CI remains the default test path.
