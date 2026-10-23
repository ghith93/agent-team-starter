# Agent Team Starter v0.9.1-rc4 — tooling and workflow pack

## Changes
- Added `agent_team/tooling_audit.py`, an offline inventory of developer/security tools and Python modules discoverable in the current environment.
- Added a dated, source-linked open-source tool radar covering agent evaluation, static analysis, MCP and skill security, structural code search, and authorized reverse engineering.
- Added reusable `SKILL.md` workflows for codebase archaeology, security gates, and authorized reverse engineering.
- Added an environment snapshot at `evaluations/results/tooling_inventory_2026-10-23.json`.
- No third-party dependency added. No tool was installed. No API or network request was made by the inventory command.

## Verification
- Regression tests: 31 passed.
- Evaluator tests: 13 passed.
- Reference cases: 12 passed.
- `compileall`: passed.
- Notebook JSON structure: passed (12 cells).
- Local inventory contract: offline mode, zero network calls, zero installs, no secret-value reads.
- Existing deterministic benchmark: 4 task groups passed local mapped checks, 0 failed, 8 marked `not_run` because they require live-model or human evaluation.
- ZIP integrity checked after packaging.

## Research and environment findings
- Current environment discovers `pytest` and `requests`; the CLI/module checks did not find Semgrep, ast-grep, Ruff, pip-audit, Bandit, Gitleaks, detect-secrets, Promptfoo, DeepEval, or LangGraph.
- These are point-in-time observations, not a statement that those projects are unavailable.
- Priority recommendations: first use existing tests and offline inventory; then opt-in Gitleaks/Semgrep/pip-audit; Promptfoo for reproducible agent/security evaluations; MCP Inspector/MCP-Scan for MCP-specific validation after reviewing their network/data-sharing behavior; ast-grep for structural code archaeology. Ghidra, radare2, Frida, and mitmproxy are specialist tools for authorized reverse engineering and controlled traffic analysis.
- Research source list: `docs/OPEN_SOURCE_TOOL_RADAR_2026-10-23.md`.

## Limits and release status
- This is a release candidate, not a production-approved release.
- No real egress proxy was tested; DNS-rebinding protection is not proven by local mocks.
- No live model/provider evaluation, live latency/cost measurement, human-intervention measurement, DeepEval execution, or fair LangGraph/OpenHands comparison was performed.
- Do not expose the public-page fetcher to hostile inputs until network-level egress policy is independently verified.
