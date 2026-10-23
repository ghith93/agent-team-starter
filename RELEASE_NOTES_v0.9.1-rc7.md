# Agent Team Starter v0.9.1-rc7

Date: 2026-10-23
Status: local release candidate; not production-approved.

## Changes
- Added `python -m agent_team.skill_lint .` to validate required metadata for project-local Agent Skills.
- Added tests for valid metadata, missing frontmatter, folder/name mismatch, and project skill inventory.
- Added three skills: `prompt-injection-defense`, `agent-framework-evaluation`, and `google-agent-stack`.
- Expanded the source-linked tool radar for Anthropic Agent Skills/Claude Code and Google Gemini CLI/ADK/OSS-Fuzz/OSV-Scanner.
- Explicitly distinguishes open-source code from hosted model terms, free-tier quotas, network transmission, and deployment costs.

## Validation
- 41/41 regression tests passed.
- 13/13 evaluator tests passed.
- 12/12 deterministic reference cases passed.
- Skill lint: 6 skills checked, 0 errors, 0 warnings.
- `compileall` passed; notebook JSON parsed successfully (14 cells).
- ZIP integrity and tests from an extracted archive must be confirmed before release publication.

## Limitations
- No external tools installed; no API calls or spend.
- Skill lint is a conservative metadata check, not full specification conformance or a safety guarantee.
- Real network egress enforcement and DNS-rebinding resistance remain unverified.
- Live model quality, source quality, latency, cost, and human intervention remain unmeasured.
