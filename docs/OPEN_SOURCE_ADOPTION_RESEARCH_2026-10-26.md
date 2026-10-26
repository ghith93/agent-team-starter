# Open-Source Project Adoption Plan

Status: research and design plan only. No third-party code or runtime dependencies are added by this document.

## Objective

Improve `agent-team-starter` by learning from proven open-source projects while preserving its small, free-first Python design, offline testability, explicit provider routing, privacy boundaries, and release gates.

**Policy: reuse ideas first; add dependencies only when a demonstrated gap justifies their maintenance, security, licensing, and runtime cost.** Popularity is a discovery signal, not proof of quality or compatibility.

## Baseline observed on 2026-10-26

- Repository: `ghith93/agent-team-starter`, public, default branch `main`.
- README identifies `v0.9.1-rc16`, Python 3.10+, an offline release gate, security scanning, provider routing, optional metadata-only telemetry, and an opt-in SQLite queue.
- Existing workflows include offline tests, YAML syntax checks, security workflows, promotion gate, isolated security audit, OpenRouter smoke tests, and experimental Graphify/Ruflo workflows.
- Repository metadata reports `NOASSERTION` and includes `LICENSE_PENDING.md`. **Resolve the project's own licensing decision before redistributing or incorporating third-party code.**
- README notes systemd files are templates, not an installed always-on service, and that the project is not an autonomous computer-use agent.

## Candidate projects and potential learning value

This is a curated review set, not a claim that every project is globally top-ranked. Verify each upstream repository's current license, security advisories, releases, dependencies, and maintenance before adoption.

| Candidate | Potential value | Initial decision |
|---|---|---|
| [OpenClaw](https://github.com/openclaw/openclaw) | Tool boundaries, provider/channel adapters, permission model, operations | Study architecture; do not add the whole runtime |
| [REA](https://github.com/morluto/rea) | Evidence-backed software/repository reverse engineering | Evaluate only as an optional read-only research tool |
| [Superpowers](https://github.com/obra/superpowers) | Spec → plan → implementation → verification | Adapt process patterns; keep acceptance tests explicit |
| [OpenCode](https://github.com/anomalyco/opencode) | Coding-agent loop, provider abstraction, tool permissions | Reference only; avoid duplicate agent runtime without a proven gap |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Reusable skills, memory lifecycle, task feedback | Study skill lifecycle; no autonomous write access |
| [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) | Plugin architecture and modular tool routing | Compare extension contracts and isolation |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | Web extraction for research | Preserve egress protections; review AGPL-3.0 implications before deployment |
| [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | Long-running task orchestration and checkpoints | Extract design lessons; avoid duplicating current queue without evidence |
| [Langflow](https://github.com/langflow-ai/langflow) | Visual workflow prototyping | Optional only if an operator UI is a real requirement |
| [Dify](https://github.com/langgenius/dify) | LLM workflow configuration and observability | Compare concepts; evaluate footprint and license |
| [n8n](https://github.com/n8n-io/n8n) | Event-driven workflow patterns and integrations | Not OSI open source; Sustainable Use/fair-code terms need separate review |
| [Ollama](https://github.com/ollama/ollama) | Local model execution | Optional provider; benchmark RAM/CPU and quality before enabling |
| [Transformers](https://github.com/huggingface/transformers) | Local inference/model interoperability | Add only for a concrete workload; likely too heavy for the core |
| [Linux](https://github.com/torvalds/linux) | Process isolation and resource-management concepts | Operational reference, not an app dependency |
| [React](https://github.com/facebook/react) | Potential future dashboard | Defer frontend until a defined need exists |
| [Awesome Selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | Discover monitoring, backup, and service alternatives | Discovery catalogue; verify each project individually |
| [System Design Primer](https://github.com/donnemartin/system-design-primer) | Reliability, queueing, scaling, failure modes | Apply selectively to retries and recovery |
| [Awesome](https://github.com/sindresorhus/awesome) | Discover domain-specific tools | Research index only |
| [freeCodeCamp](https://github.com/freeCodeCamp/freeCodeCamp) | Learning/reference material | Educational reference only |
| [Build Your Own X](https://github.com/codecrafters-io/build-your-own-x) | Understand internals before selecting components | Educational reference only |

Additional comparison candidates: [GitHub Spec Kit](https://github.com/github/spec-kit) for spec-driven delivery, [Codex](https://github.com/openai/codex) and [Gemini CLI](https://github.com/google-gemini/gemini-cli) as coding-agent implementations, and [OpenHands](https://github.com/All-Hands-AI/OpenHands) for isolated software-engineering agent environments.

## Implementation sequence

### Phase 0 — Baseline and guardrails
1. Preserve `main` and the existing offline release gate.
2. Resolve the repository license and retire `LICENSE_PENDING.md` only after an explicit decision.
3. Record test, security, and workflow status before code changes.
4. Inventory direct/transitive dependencies, workflow permissions, secrets exposure, and untrusted-input boundaries.
5. Keep deployment, publishing, purchases, and account changes behind explicit authorization.

### Phase 1 — Specification and repeatability
1. Use spec-first delivery: problem, non-goals, acceptance criteria, threat analysis, and rollback for every change.
2. Add deterministic tests before runtime changes.
3. Keep offline checks required; separate provider/network smoke tests and ensure billable credentials are never used accidentally.

### Phase 2 — Reliability and operations
1. Evaluate SQLite queue idempotency, stale leases, retry/backoff, poison tasks, cancellation, crash recovery.
2. Extend health, backup, and restore tests before describing any deployment as 24/7.
3. Label systemd/scheduling files as templates until installation and live health checks are verified.
4. Keep structured diagnostics minimal and redacted; do not persist task text/model outputs by default.

### Phase 3 — Agent and provider boundaries
1. Compare provider interfaces with OpenCode/Hermes/DeepSeek Harness; retain the current interface unless a concrete capability is missing.
2. Define tool contracts with strict input schemas, timeouts, bounded output, and explicit read/write capabilities.
3. Treat model outputs, web pages, repository files, and skill packages as untrusted. Never auto-execute generated code or downloaded skills.
4. Test Ollama only as an optional provider behind the same interface and benchmark resource use and quality.

### Phase 4 — Research and optional interfaces
1. Evaluate REA or similar read-only analysis tools in a disposable, no-secret environment.
2. Keep public web fetching behind an administrator-controlled egress proxy blocking private, loopback, link-local, reserved, and metadata destinations after DNS resolution and on redirects/connections.
3. Add Firecrawl only after license review and evidence of a real need.
4. Consider Langflow/Dify/React only when a visual interface is justified.

### Phase 5 — Adoption gates
For each dependency, require:
- Confirmed license compatibility with the repository's chosen license and distribution model.
- Maintenance, release provenance, security policy, and unresolved critical/high vulnerabilities review.
- A minimal isolated prototype with pinned versions and a dependency diff.
- Tests demonstrating measurable improvement over the current implementation.
- Offline regression gate and relevant security tests passing.
- Documented rollback/uninstall path and explicit approval before production enablement.

## Decision rules

- Prefer a small adapter or documented pattern over importing a full framework.
- Do not adopt tools solely because of stars or social momentum.
- Do not combine agent frameworks unless a benchmark proves benefit.
- Never run untrusted skills/plugins with repository write access, secrets, or broad network access.
- Keep paid provider calls opt-in and clearly marked.
- A green CI workflow proves only the checks actually run; it does not prove continuous uptime or complete security.

## Initial priority

1. **Immediate:** license decision, baseline workflow status, dependency and permission audit.
2. **High:** spec-first change contracts, regression coverage, queue recovery and backup/restore verification.
3. **High:** tool permissions, untrusted-input handling, egress enforcement and secret redaction.
4. **Medium:** compare OpenCode/Hermes/DeepSeek Harness; prototype Ollama only if resources permit.
5. **Deferred:** wholesale OpenClaw/n8n/Dify/Langflow/React adoption until there is a concrete need.

## Evidence and limitations

This is a research plan based on repository metadata/README and upstream discovery as of 2026-10-26. It is not a completed security audit, dependency compatibility test, or claim that any candidate has been installed. Verify live upstream licenses and advisories before adoption.
