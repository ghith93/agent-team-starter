# Agent Team Starter v0.9.1-rc16

A small, free-first Python agent workflow: **Planner → Executor → Reviewer**. Designed for offline testing, explicit provider routing, traceable failures, and privacy-conscious optional telemetry. It is not an autonomous computer-use agent: it cannot access your filesystem, browser, or accounts through model prompts, and it does not execute generated code.

## What's improved in v0.9
- Adds a transparent CSV benchmark scorer with strict field/range validation and a hard rejection gate for any declared security failure.
- Expands public URL validation: rejects invalid ports, single-label hostnames, local/internal suffixes, and DNS names resolving to any non-public address (including mixed public/private answers).
- Adds regression tests for these URL-validation cases and benchmark gate behavior.
- DNS rebinding is still not fully prevented because validation and the HTTP connection resolve separately; network-level egress controls remain required for hostile inputs.

## What's improved in v0.7
- Adds a `final` field containing the executor draft so callers do not have to extract it from nested JSON.
- Adds a per-run UUID and total elapsed time; stage trace still records status, latency, provider/model, and output size.
- Adds CLI `--check-config` that reports provider names only and makes no network request; supports UTF-8 task files and opt-in metadata-only telemetry.
- Sanitizes provider error hints and prevents full provider error messages from being repeated in fallback summaries.
- Trims surrounding whitespace from environment keys and sets a configurable Gemini default (`gemini-2.5-flash`). Provider availability can change; configure a model enabled for your account.
- Corrects Colab instructions to match v0.7 folder and archive names.
- Retains offline reference evaluator and release gate.

## Install
Python 3.10+.
```bash
python -m pip install -r requirements.txt
python run_tests.py
# Score a completed benchmark CSV using predefined rules
python evaluations/benchmark_score.py benchmark_results.csv
```

## Configure
Use environment variables or Colab Secrets. Never hard-code real credentials.
```bash
export GEMINI_API_KEY="..."
export OPENROUTER_API_KEY="..."
# Optional local FreeLLMAPI gateway (only enabled when its unified key is set):
export FREELLMAPI_API_KEY="freellmapi-your-local-unified-key"
export FREELLMAPI_BASE_URL="http://127.0.0.1:3001/v1"
export FREELLMAPI_MODEL="auto"
# Optional: GEMINI_MODEL=...; OPENROUTER_FREE_MODELS=openrouter/free,provider/model:free
```

## Run
```bash
# No network request: reports configured provider names only
python -m agent_team.cli --check-config
# Live run (may use provider quota and may be billable depending on provider/account)
python -m agent_team.cli "Draft a checklist for validating a small online business idea"
# Task file and optional metadata-only telemetry
python -m agent_team.cli --task-file task.txt --telemetry logs/events.jsonl
```

No keys means no provider requests. OpenRouter accepts only `openrouter/free` or model IDs ending in `:free`. A free label is not a guarantee of uptime, quota, or absence of ancillary costs. `--check-config` does not test credentials or billing.

FreeLLMAPI is an optional fallback. Run it locally and keep it bound to `127.0.0.1`; do not expose its single-user API to the public internet. Plain HTTP is accepted only for loopback URLs; remote FreeLLMAPI endpoints must use HTTPS. See [the integration assessment](docs/FREELLMAPI_INTEGRATION_ASSESSMENT.md) for adoption limits, privacy, and evaluation requirements.

## Result contract
Successful `run_team()` results include `ok`, `run_id`, `task`, `final`, `plan`, `draft`, `review`, `trace`, `total_duration_ms`, and a limitation note. `final` is the draft, not a merged rewrite by the reviewer. Review is model-generated and is not proof of correctness. On a stage failure, `TeamExecutionError` exposes the failed stage, successful prior outputs, and trace.

## Privacy and security boundaries
- Telemetry is disabled unless a path is explicitly provided. It excludes task text and model outputs, but provider/model identifiers and timing can still be sensitive.
- Do not share telemetry logs publicly without review. Never log API keys or paste them into source, notebooks, screenshots, or version control.
- Model outputs are untrusted text and are never executed.
- `web_research.fetch_public_page()` fails closed unless `AGENT_TEAM_TRUSTED_EGRESS_PROXY` is set to an administrator-controlled egress proxy. That proxy must block private, loopback, link-local, reserved, and cloud metadata destinations after DNS resolution and on every redirect/connection. Redirects are also blocked by the fetcher. Do not expose it as a public service without independently verifying network egress policy. The proxy configuration itself is a trust boundary. The proxy URL parser rejects embedded credentials, invalid ports, control characters, and paths/query/fragments; this is syntax validation only, not a test of proxy policy. The fetcher also disables requests environment inheritance (`trust_env=False`) so `NO_PROXY` and ambient proxy variables cannot silently override the explicitly configured proxy.
- No external actions, posting, purchases, or account changes are implemented.

## Release gate
`python run_tests.py` runs regression tests, deterministic reference cases, and emits a machine-readable result. The offline release gate validates prompt-injection fixture integrity, runs a heuristic static-hygiene scan, and checks release ZIP paths, selected accidental files, CRC, and configured archive-size/compression-ratio limits. See the release notes for the exact counts from this run. Passing it demonstrates only tested code behavior and fixed reference arithmetic; it does not establish live-provider availability or general answer quality. Live-provider checks were not performed as part of this offline release.

## Offline benchmark runner
Run the deterministic subset without provider credentials or network access:
```bash
python evaluations/offline_benchmark.py
```
The JSON report is written to `evaluations/results/offline_deterministic_report.json`. It executes only named local regression checks and labels all live-model/human-evaluation tasks `not_run`. It deliberately does not invent accuracy, source-quality, live latency, cost, or human-intervention scores. Passing this subset is not a release approval and does not verify a real egress proxy's network policy.

## Developer tooling and reusable skills

- `python -m agent_team.tooling_audit` inventories locally discoverable tools without installing packages, reading secret values, or making network requests. Use `--json` for machine-readable output.
- `docs/OPEN_SOURCE_TOOL_RADAR_2026-10-23.md` contains a prioritized, source-linked tool review and an adoption plan. It is a research snapshot, not proof that each tool is installed or compatible.
- `skills/` contains reusable `SKILL.md` workflows for codebase archaeology, security gating, and authorized reverse engineering. These are plain-text guidance files, not auto-installed plugins; inspect and test skills before importing them into an agent runtime.

## Portable agent skills and offline lint

Project-specific skills live in `skills/*/SKILL.md`. Run the conservative metadata check with:

```bash
python -m agent_team.skill_lint .
python -m agent_team.skill_lint . --json
```

This validates required metadata and folder-name consistency only. It does not execute skills, validate every part of the Agent Skills specification, or certify skill safety. See `docs/OPEN_SOURCE_TOOL_RADAR_2026-10-23.md` for the Anthropic/Google project comparison and the zero-install adoption policy.


## Prompt-injection fixture suite (offline)

Run `python evaluations/prompt_injection_suite.py` or use `python run_tests.py`. The fixture set covers untrusted webpage instructions, tool-output poisoning, fake-canary disclosure attempts, task override, unauthorized side effects, tool trust boundaries, quoted instructions, private-network access requests, evidence fabrication, and safe completion. These are structured test cases and expected policy outcomes—not a live-model adversarial benchmark. No model is called and no network request is made by this suite.


## Offline static-hygiene audit (rc9)

Run `python evaluations/security_audit.py`. It scans source-like project files for several common credential shapes and selected risky-code patterns, redacts matched values, and writes `evaluations/results/offline_security_audit.json`. This is a local heuristic—not a full secret scanner, dependency vulnerability scan, or security certification. It does not access the network.


## Instruction boundaries (rc12+)

Planner, Executor, and Reviewer role policies are sent using provider-native system-instruction fields (OpenRouter `system` message and Gemini `systemInstruction`). The task and previous-stage content remain separate user content and are labeled as untrusted in stage prompts. This improves instruction separation but does not guarantee prompt-injection resistance; live adversarial evaluation is still required. Any task sent to a configured hosted provider is transmitted to that provider. Do not submit secrets or sensitive data unless you have reviewed the provider's terms and are authorized to share it.

## Release ZIP hygiene (rc10+)

Run `python evaluations/archive_audit.py PATH_TO_ZIP` to check ZIP paths, duplicate names, symlinks, selected sensitive/runtime files, CRC, entry count, member size, total uncompressed size, and compression ratio. The defaults are 10,000 entries, 100 MiB per member, 500 MiB total uncompressed size, and a 1,000:1 compression ratio. If metadata exceeds a configured limit, CRC testing is skipped to avoid decompressing the archive. These are conservative metadata checks, not a sandbox or full archive-security guarantee.
