# Open-Source Capability Adoption Plan

Updated: 2026-10-25

This document records which external open-source projects are worth using in
`agent-team-starter`, and how to evaluate them without adding unnecessary
runtime dependencies or triggering paid API calls.

## Decisions

| Project | Decision | Intended use | Integration approach |
|---|---|---|---|
| [REA](https://github.com/morluto/rea) | Adopt as an optional, separate research tool | Analyze applications, JavaScript/Electron bundles, websites, and binaries where inspection is authorized; document observed behavior and evidence | Keep outside the core runtime. Use its official install/setup flow in a controlled analysis environment. Do not add it as a mandatory Python dependency. |
| [Cloudflare Security Audit Skill](https://github.com/cloudflare/security-audit-skill) | Reuse methodology, not the runtime package | Coverage-led security reviews, independent validation of candidate findings, evidence-based reports | Adapt checklists and report structure to existing Python tests/security audit. Verify every finding against source and reproduce it safely. |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Pilot only | Build a local graph of repository architecture and dependencies to aid code review | Run against a disposable checkout; prefer code-only/local mode when possible. Adopt only if it finds useful relationships missed by current docs/tests. |
| [ai-memory](https://github.com/akitaonrails/ai-memory) | Defer installation | Cross-session task handoffs and durable project memory | Compare against existing GitHub status/decision logs first. Add only if a measured gap remains; secure its local service and bearer token. |
| [Cindy](https://github.com/makecindy/cindy) | Do not integrate now | Desktop/browser automation research | Revisit only if computer-use automation becomes an explicit requirement; it is a separate large application and has telemetry/service considerations. |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Separate future marketing tool | Reproducible HTML-to-video generation, potentially for product marketing | Not part of the agent-team runtime. Evaluate separately when video production is in scope. |

## REA workflow

Official repository: https://github.com/morluto/rea
Official project site: https://rea.tools/
License shown by the repository: MIT. Re-check the current license and package
release before every new adoption.

1. Use a dedicated, disposable analysis environment. Do not run unknown target
   applications with sensitive credentials or a privileged account.
2. Install REA only from the official repository/site/package links, review the
   setup changes, and approve only the MCP/agent configuration changes needed.
3. Define the target and scope before analysis. Prefer applications we own,
   open-source applications, public interfaces, or targets for which we have
   explicit authorization.
4. Ask REA to investigate a narrowly defined feature, produce evidence and
   limitations, and distinguish observed facts from hypotheses.
5. Reproduce the externally observable behavior with an independent
   implementation using our own code and assets. Add deterministic regression
   tests for expected behavior, error cases, and security boundaries.
6. Keep a record of target version, environment, commands, evidence, uncertainty,
   and test results. Do not claim parity until tests support it.
7. Do not import analyzed binaries, copied code, secrets, proprietary assets, or
   untrusted output into the production agent runtime.

### Legal and safety boundary

Reverse engineering must not be used to bypass payment, subscriptions,
authentication, DRM, license enforcement, rate limits, or access controls, or
to obtain private data or unauthorized access. Do not copy proprietary source,
assets, or trade secrets. Where a paid product is involved, limit work to
authorized interoperability, security research, or independent implementation
of observable ideas and functionality consistent with applicable law and terms.
If authorization or the legal basis is unclear, stop and use an open-source
alternative instead.

## Acceptance criteria before integrating any capability

- No new required paid service or API.
- No live provider call during offline tests.
- No new mandatory dependency unless its value is demonstrated.
- License, provenance, maintenance activity, and security implications reviewed.
- New functionality has deterministic tests and failure-path coverage.
- No secrets or private user data in logs, fixtures, reports, or commits.
- Any external side effects require a separate explicit approval gate.

## Immediate next actions

1. Keep REA as a separate optional tool; do not bundle it into the Python app.
2. Use REA first on a legally authorized sample target and evaluate whether its
   evidence supports an independent, tested implementation.
3. Adapt Cloudflare's coverage ledger and independent-finding validation to the
   existing offline security audit.
4. Run Graphify as a non-blocking pilot only if a controlled environment is
   available; record results before deciding whether to keep it.
5. Continue to use `python run_tests.py` and
   `python evaluations/offline_benchmark.py` for local/offline validation.
   Do not infer production readiness from those checks alone.
