## 2026-10-25 — Operational baseline re-applied to current main

- Re-applied `STATE.md`, `ROADMAP.md`, `RUNBOOK.md`, and `LICENSE_PENDING.md` on a clean branch based on the current `main` commit.
- Preserved the narrowed secret-scanner exclusions merged in PR #26.
- Confirmed the documentation does not claim a live 24/7 deployment, independent backup, or verified alerting.
- No live provider calls, deployment, or spending performed.

# Changelog

## v0.9.1-rc16 — bounded stage outputs and safer failure messages
- Follow-up hardening pins GitHub Actions to reviewed full commit SHAs and adds contract checks against mutable action tags.
- Added a 30,000-character cap for each model stage output to limit accidental context growth and oversized responses.
- Changed stage-failure summaries to avoid echoing raw custom-router/provider exception text into CLI output; the original exception remains available programmatically as `cause`.
- Added regression tests for oversized stage outputs and exception-message redaction.
- Offline-only hardening: this does not prove provider behavior, prompt-injection resistance, or live deployment security.

## v0.9.1-rc15 — CI workflow contract checks and action refresh
- Updated `actions/checkout` references from major v6 to v7 after checking the upstream release information.
- Added dependency-free regression checks for the security workflow's triggers, least-privilege permissions, required scanner steps, fail-closed outcome gate, report uploads, and full-history Gitleaks checkout.
- Kept scanner packages unpinned intentionally for this candidate; the workflow records resolved versions, and immutable action-SHA pinning remains a recommended follow-up before high-assurance use.
- Local YAML parsing and workflow-contract checks are validation of configuration structure only; they do not execute GitHub Actions or external scanners.

## v0.9.1-rc14 — external CI security gates
- Added GitHub Actions workflow for offline tests, Python security lint, dependency audit, Semgrep, detect-secrets, and Gitleaks.
- Added weekly scheduled scans and report artifacts; documented that external checks require a completed GitHub Actions run.

## v0.9
- Hardened numeric evaluation for non-finite inputs/results and invalid tolerances.
- Expanded deterministic reference cases from 6 to 12.

# Changelog

## v0.9 — benchmark scoring and public URL validation hardening
- Added `evaluations/benchmark_score.py` for validated, reproducible CSV scoring and a hard reject on security-failure rows.
- Added tests for invalid benchmark values, security gate behavior, invalid URL ports, single-label hostnames, and DNS results containing private IPs.
- Tightened public URL checks for local/internal hostnames and all resolved IP answers.
- Limitation retained: DNS rebinding is not fully prevented without connection-level IP pinning or network egress controls.
- No live provider calls or external actions were performed.


## v0.7 — operational hardening and cleaner integration
- Added top-level `ok`, `run_id`, `final`, and total-duration result fields.
- Added CLI configuration inspection with no network calls, task-file input, and optional metadata-only telemetry.
- Reduced credential leakage risk by sanitizing provider error hints and summarizing provider failures by category.
- Normalized API-key whitespace and updated the configurable Gemini default model.
- Rewrote Colab setup to match the current version and clarify that configuration inspection is not a live health check.
- Added CLI and result-contract tests while preserving existing APIs and offline evaluator.

## v0.6
- Added per-stage execution trace with status, duration, provider/model, and output length.
- Added opt-in metadata-only JSONL telemetry; prompts and model outputs are excluded.
- Preserved traces on stage failures.

## v0.5
- Added deterministic reference cases for CAC and invalid inputs.
- Added one-command offline test runner and explicit limitation notes.

## v0.4
- Added stage-aware failures, partial results, and empty-output checks.

## v0.3
- Added HTTP error classification, free-first routing, bounded public-page retrieval, and offline regression tests.


## Unreleased security hardening (post-v0.9 audit)
- Fail closed for page retrieval unless an explicitly configured trusted egress proxy is supplied.
- Added regression tests proving no direct HTTP request is made when proxy configuration is absent or malformed.
- This is a candidate fix, not a released version; the proxy must independently enforce destination-IP restrictions after DNS resolution.

## v0.9.1-rc3 (unreleased candidate)
- Added an offline deterministic benchmark runner that executes only explicitly mapped local regression checks and marks live-model/human tasks `not_run` rather than fabricating scores.
- Runner report records zero network/provider calls and zero estimated spend for this offline run, with explicit scope and release limitations.
- Added regression coverage to prevent the benchmark report from overstating live evaluation.

## Unreleased — tooling and workflow pack

- Added an offline local-tool inventory command (`python -m agent_team.tooling_audit`) that performs no installation, network call, or secret-value read.
- Added a source-linked open-source tooling radar covering coding-agent evaluation, static analysis, MCP/skill security, code archaeology, and authorized reverse engineering.
- Added reusable skills for codebase archaeology, security gating, and authorized reverse engineering.
- Added regression tests for the tooling inventory contract. No third-party dependency was added.

## v0.9.1-rc4 — 2026-10-23

- Added offline developer-tool inventory and snapshot.
- Added a source-linked open-source tool radar and three reusable skills for code archaeology, security review, and authorized reverse engineering.
- Added two tooling-audit regression tests; no dependencies added.
- Verification: 31 regression tests, 13 evaluator tests, 12 reference cases, compileall and ZIP checks passed. No API calls, installations or spending.
- Release remains a candidate: live evaluation and real egress-proxy security verification remain open.


## v0.9.1-rc5 — 2026-10-23

- Added strict syntax validation for the configured trusted egress proxy: rejects embedded credentials, malformed ports, control characters, and proxy paths/query/fragments.
- Preserves support for an explicitly configured localhost proxy; syntax validation does not imply that proxy is trusted or enforces destination policy.
- Added five regression tests for proxy configuration edge cases.
- Verification: 36 regression tests, 13 evaluator tests, 12 reference cases. No new dependency, install, API call, or spend.
- Release remains a candidate; actual proxy enforcement, DNS rebinding resistance, and live-model evaluation remain unverified.


## v0.9.1-rc6 — 2026-10-23

- Disabled ambient `requests` environment configuration for public-page fetches by using an explicit session with `trust_env=False`; this prevents `NO_PROXY`/ambient proxy settings from silently bypassing the explicitly configured trusted egress proxy.
- Added a regression test that sets `NO_PROXY=*`, `no_proxy`, `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY`, then verifies the explicitly configured egress proxy remains the only configured route.
- Verification: 37 regression tests, 13 evaluator tests, 12 reference cases. No dependency changes, installations, API calls, network requests, or spend.
- Release remains a candidate; the actual proxy's destination-IP enforcement and DNS-rebinding resistance remain unverified.

## v0.9.1-rc7 — 2026-10-23

- Added `agent_team.skill_lint`, a standard-library-only offline validator for a conservative subset of Agent Skills metadata.
- Added four tests for valid metadata, folder-name mismatch, missing frontmatter, and project-wide skill inventory.
- Added skills for prompt-injection defense, fair agent-framework evaluation, and Google agent-stack assessment.
- Expanded the open-source radar with official Anthropic and Google repositories: Agent Skills, Claude Code, Gemini CLI, Google ADK, OSS-Fuzz, and OSV-Scanner. Separated project license from hosted model access, quotas, data transmission, and deployment cost.
- No external dependencies installed; no API/network calls or spending performed. This release does not claim that live agent quality or real egress policy has been verified.


## v0.9.1-rc8 — 2026-10-23

- Added 10 structured prompt-injection fixtures covering untrusted web content, tool-output poisoning, fake-canary exfiltration, task override, unauthorized side effects, tool trust boundaries, quoted instructions, private-network access requests, evidence integrity, and safe completion.
- Added a standard-library-only fixture validator and tests for malformed records, duplicate IDs, and unsupported expected actions. Integrated fixture integrity into the offline release gate.
- Updated the notebook archive reference to rc8.
- This suite checks fixture integrity only; it does not evaluate a live model or prove security controls. No dependencies, installations, API calls, network requests, or spending.


## v0.9.1-rc9 — 2026-10-23

- Added an offline static-hygiene audit for common secret/token shapes, selected risky-code patterns, and dependency-range notes; matched credential values are never emitted in reports.
- Added tests for clean input, secret detection/redaction, review-only findings, and unbounded dependency ranges. Integrated the audit into the offline release gate.
- Updated the Colab notebook archive reference to rc9.
- This heuristic audit is not a substitute for Gitleaks, Semgrep, OSV-Scanner, pip-audit, or human review; it does not query vulnerability databases. No external packages installed and no network/API calls made by tests.

## v0.9.1-rc10 — 2026-10-23

- Added ZIP archive hygiene validator for path traversal, absolute paths, duplicate entries, symlinks, selected runtime/sensitive files, and CRC errors.
- Added five offline archive-audit tests and integrated them into the offline test runner.
- Updated notebook archive reference to rc10. No external dependencies, installations, API/network calls, or spending.
- Release remains a candidate; archive hygiene does not establish full security, live-model quality, or real egress enforcement.


## v0.9.1-rc11 — 2026-10-23

- Hardened release ZIP auditing with configurable entry-count, per-member size, total uncompressed size, and compression-ratio limits.
- CRC testing is skipped when a metadata limit is exceeded, avoiding decompression of archives already identified as oversized/suspicious.
- Added four regression tests for the new limits; no new dependencies, installations, API/network calls, or spending.
- Release remains a candidate; these checks do not replace sandboxing or independent security tooling.


## v0.9.1-rc12 — 2026-10-23

- Moved Planner, Executor, and Reviewer role instructions into provider-native system-instruction fields for OpenRouter and Gemini, instead of embedding them in the user message.
- Kept task text and inter-stage outputs in user content, explicitly labeling prior plan/draft material as untrusted.
- Added offline payload-shape tests for both provider request formats and stage separation tests.
- No live model calls, network requests, package installs, or spending. This is defense-in-depth, not proof of prompt-injection resistance.

## v0.9.1-rc13 — 2026-10-23

- Hardened provider error parsing for non-object JSON bodies so malformed upstream errors do not mask the original provider failure.
- Added regression coverage for malformed provider error payloads and bearer/API-token redaction.
- Updated the Colab notebook archive reference to rc13.
- Attempted isolated installation of Bandit and pip-audit after explicit authorization, but package-index DNS resolution failed in the execution environment. No tools were installed; external scanner status remains not run.
- Offline tests pass; no live model calls, API calls, or spending. Release remains a candidate and dependency vulnerability status is unknown.
