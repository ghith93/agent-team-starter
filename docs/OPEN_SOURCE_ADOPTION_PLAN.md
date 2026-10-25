# Open-Source Capability Adoption Plan

Updated: 2026-10-25

This document records which external open-source projects are worth using in
`agent-team-starter`, and how to evaluate them without adding unnecessary
runtime dependencies or triggering paid API calls.

## Decisions

| Project | Decision | Intended use | Integration approach |
|---|---|---|---|
| [REA](https://github.com/morluto/rea) | Adopt as an optional, separate research tool | Analyze applications, JavaScript/Electron bundles, websites, and binaries where inspection is authorized; document observed behavior and evidence | Keep outside the core runtime. Use its official install/setup flow in a controlled analysis environment. Do not add it as a mandatory Python dependency. |
| [Cloudflare Security Audit Skill](https://github.com/cloudflare/security-audit-skill) | Reuse methodology, not the runtime package | Coverage-led security reviews, independent validation of candidate findings, evidence-based reports | Adapt the coverage and evidence contract into `skills/security-gate/SKILL.md`; do not bulk-import the upstream workflow or claim a full audit without running its phases. |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Pilot only | Build a local graph of repository architecture and dependencies to aid code review | Run against a disposable checkout in code-only mode; keep output outside the source checkout. Adopt only if it finds useful relationships missed by current docs/tests. |
| [ai-memory](https://github.com/akitaonrails/ai-memory) | Defer installation | Cross-session task handoffs and durable project memory | Compare against existing GitHub status/decision logs first. Add only if a measured gap remains; secure its local service and bearer token. |
| [Cindy](https://github.com/makecindy/cindy) | Do not integrate now | Desktop/browser automation research | Revisit only if computer-use automation becomes an explicit requirement; it is a separate large application and has telemetry/service considerations. |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Separate future marketing tool | Reproducible HTML-to-video generation, potentially for product marketing | Not part of the agent-team runtime. Evaluate separately when video production is in scope. |

## REA workflow

Official repository: https://github.com/morluto/rea
Official project site: https://rea.tools/
License shown by the repository: MIT. Re-check the current license, official package name,
supported Node.js versions, and package release before every new adoption. The current
README documents Node.js 22.x (>=22.19), 24.x (>=24.11), or 26+, plus npm; setup may
register an MCP server and write agent configuration.

1. Use a dedicated, disposable analysis environment. Do not run unknown target
   applications with sensitive credentials or a privileged account.
2. Install REA only from the official repository/site/package links. Review the
   exact package/version and setup diff; approve only the MCP/agent configuration
   changes needed. Do not let setup install paid tools or change global configuration
   without a separate explicit decision.
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

## Graphify pilot (zero API requirement)

Official repository: https://github.com/Graphify-Labs/graphify
The official project documents the Python package `graphifyy` and CLI `graphify`.
Its code-only graph extraction uses local parsing and does not require an API key.
Do not run `graphify install` during the pilot because it writes assistant integration
configuration; only a separate disposable environment should receive such changes.

1. Create a disposable checkout of the exact commit being reviewed.
2. Install the official package into an isolated tool environment only after checking
   the current license, release, and dependency metadata.
3. Run code-only extraction against the disposable checkout and direct generated
   files to a separate scratch/output directory; do not include private documents,
   secrets, or unneeded assets.
4. Compare the graph report against existing module structure, call paths, and tests.
   Record only concrete relationships or review questions it surfaced that were
   otherwise missed. Treat inferred edges as hypotheses, not source facts.
5. Remove the disposable checkout and outputs after recording non-sensitive results.
   Keep Graphify optional unless the pilot produces measurable review value.

Example command shape after installation (replace the output path with a new,
empty scratch directory outside the checkout):

```bash
graphify extract /path/to/disposable-checkout --code-only --out /path/to/scratch-output
```

This command has not yet been run in the current environment.

## Legal and safety boundary

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
- Tool installation and execution occur only in a disposable environment with
  permissions and network behavior reviewed.

## Immediate next actions

1. Keep REA as a separate optional tool; do not bundle it into the Python app.
2. Run REA only when a disposable Node.js-compatible analysis environment is available,
   using an authorized target and reviewing every setup change.
3. Use the expanded offline tooling inventory to check prerequisites without installing
   anything: `python -m agent_team.tooling_audit --json`.
4. Run the Graphify code-only pilot in an isolated environment; record whether it
   identifies architecture relationships that existing docs and tests miss.
5. Continue to use `python run_tests.py` and
   `python evaluations/offline_benchmark.py` for local/offline validation.
   Do not infer production readiness from those checks alone.
