# Agent Team Starter

**Current repository status (2026-10-23):** access verified through the connected GitHub integration. The existing `main` branch was initialized but does not yet contain the full source tree.

The latest recovered local release archive is **Agent Team Starter v0.9.1-rc16**. Its ZIP integrity check passed, and local offline checks passed: 47 core tests, 39 evaluation tests, and 12 deterministic reference calculations. Ten prompt-injection fixtures passed structural checks.

These are local/offline results only. They do not establish live-model quality, production security, or real egress-proxy enforcement. The source archive has **not yet been restored to this repository**.

## Project plans

- [Implementation plan: marketing and sales agent stack](docs/IMPLEMENTATION_PLAN_2026-10-23.md)
- [Open-source integration radar](docs/OPEN_SOURCE_INTEGRATION_RADAR.md)
- [Access boundaries and approval gates](docs/ACCESS_AND_AUTOMATION_BOUNDARIES.md)
- [Meta Ads MCP read-only setup runbook](docs/META_ADS_READ_ONLY_SETUP.md)

## Intended integration direction

1. Meta Ads reporting through a read-only MCP integration first.
2. Draft-first content planning and scheduling.
3. Customer conversation and CRM workflow evaluation.
4. Delivered-order economics and attribution.
5. Guarded automation with least privilege, audit trails, and explicit approval for public, financial, or customer-facing side effects.

No campaign has been published, no budget has been changed, and no real customer message has been sent as part of this setup.

## Next engineering gate

Restore the recovered rc16 source tree on a feature branch, verify archive-to-repository parity, run tests in CI, and review security scan results before merging to `main`.
