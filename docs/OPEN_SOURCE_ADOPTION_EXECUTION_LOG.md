# Open-Source Adoption Execution Log

Date: 2026-10-26  
Repository: `ghith93/agent-team-starter`  
Original working branch: `research/open-source-adoption-plan`  
Related pull request: [#75 — research open-source adoption strategy](https://github.com/ghith93/agent-team-starter/pull/75) (merged)

## Verified checks for the research-plan commit

Commit: `b16f74ff2547c6cbdd302ba7bdfc8243ac87d257`

GitHub Actions reported all 14 associated check runs as completed with `success`, including:
- Offline regression and evaluator suites.
- Deterministic benchmark and dependency audit.
- Python static security analysis.
- Semgrep Python rules.
- Gitleaks secret scanning.
- Workflow and Dependabot YAML parsing.

This confirms the checks that ran for the documentation-only commit. It is not a full security certification, does not establish 24/7 runtime operation, and does not prove that upstream projects are compatible or safe to install.

## Existing work found — avoid duplicate implementation

The repository already has relevant baseline material and tests:
- `docs/OPEN_SOURCE_TOOL_RADAR_2026-10-23.md`: research on testing/evaluation, MCP security, AST tools, skills and sandboxing.
- `docs/OPEN_SOURCE_INTEGRATION_RADAR.md`: marketing/sales stack candidates, including Meta Ads MCP, Postiz, Chatwoot, Twenty and n8n.
- `docs/SECURITY_THREAT_MODEL.md`: prompt injection, secrets, SSRF, DNS rebinding, dependency integrity, CI permissions and cost controls.
- `docs/QUEUE_HEALTH_BACKUP_RUNBOOK.md` and `docs/DURABLE_QUEUE_RUNBOOK.md`: queue health, backup/restore and operational limits.
- Existing test modules cover routing, team execution, CLI, memory, queue admin, telemetry, web research, skill lint, workflow storage, deployment preflight and security contracts.

These are existing files discovered in the default-branch tree. They should be reviewed and updated where appropriate rather than replaced by a parallel framework.

## Adoption decisions

| Capability | Decision | Evidence required before activation |
|---|---|---|
| Spec-first development (Superpowers / Spec Kit patterns) | Reuse as process, no runtime dependency | Each code change has acceptance criteria, threat analysis and rollback |
| Coding-agent patterns (OpenCode / Hermes / DeepSeek Harness / OpenClaw) | Compare interfaces; do not combine full runtimes yet | Fixed benchmark demonstrates improvement without weakening permissions |
| Local inference (Ollama / Transformers) | Optional future provider; not enabled | Resource/quality benchmark and provider contract tests |
| Web extraction (Firecrawl) | Defer installation | License review, isolated prototype, egress/SSRF controls and cost analysis |
| Workflow platforms (n8n / Dify / Langflow) | Defer core adoption | Concrete use case, license review and deployment-footprint comparison |
| UI (React) | Defer | Defined operator need and API/authentication design |
| Catalogues and learning repositories | Research references only | No production dependency needed |
| Meta/social/CRM tools in existing integration radar | Keep as separate product-integration track | Read-only scopes first, provider permissions verified, synthetic-data test and explicit authorization for writes |

## Mandatory blockers before importing third-party code

1. The repository currently has `LICENSE_PENDING.md` and GitHub reports `NOASSERTION`. The owner must choose the project's intended license; do not silently choose one on the owner's behalf.
2. Verify each upstream repository's exact license, release/commit provenance, security advisories, maintenance status, transitive dependencies and network behavior.
3. Keep third-party agents, MCP servers and skill bundles isolated from repository write access, secrets, and unrestricted network access.
4. Pin versions, record a dependency diff, run offline regression and security gates, and document rollback.
5. Do not claim that a tool was installed or integrated until a commit, test evidence, and runtime verification exist.

## Next implementation order

1. Review the existing security and integration radars together; reconcile duplicates and stale licensing/activity claims.
2. Audit workflow permissions and ensure any skipped/cancelled mandatory scan blocks security-clear claims.
3. Review current web-research DNS/egress boundaries and add tests before changing network behavior.
4. Extend queue reliability only where tests expose a real gap (idempotency, lease expiry, retry limits, cancellation, crash recovery).
5. Prototype one candidate at a time in a disposable branch; use the same fixed offline benchmark and compare against baseline.
6. Keep external posting, purchases, deployment, provider spend, and write-enabled integrations disabled unless separately authorized.

## Current status (refreshed 2026-10-26)

- The research/adoption plan was merged through PR #75 into `main`; the original plan and review history remain available in the linked PR.
- PR #75's checks passed for the documentation-only change. This is not a full security certification and does not prove runtime availability.
- Subsequent security work includes merged PR #79 (broader credential redaction) and PR #80 (semicolon-delimited query-key redaction). PR #80's test, secret-scanning, static-analysis, dependency-audit, YAML, isolated-audit, and promotion-readiness checks all passed before merge.
- The Hostless aggregate runtime logs endpoint has been observed returning HTTP 500 while deployment-scoped logs remained available as a fallback; see [issue #73](https://github.com/ghith93/agent-team-starter/issues/73). This remains an open provider/runtime issue, not a resolved repository-code defect.
- Main-branch ruleset review, verified repository security settings, monitoring/alerting, and independent backup/restore proof remain open work tracked in [#38](https://github.com/ghith93/agent-team-starter/issues/38), [#17](https://github.com/ghith93/agent-team-starter/issues/17), [#19](https://github.com/ghith93/agent-team-starter/issues/19), and [#18](https://github.com/ghith93/agent-team-starter/issues/18).
- No third-party runtime dependencies were installed and no upstream source code was copied as part of the adoption research.
- A successful deployment record does not by itself establish continuous 24/7 availability; live monitoring and a proven restore process are still required.
