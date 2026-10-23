# Open-Source Integration Radar
Reviewed: 2026-10-23
Purpose: shortlist candidates for the marketing and sales agent stack. This is an initial shortlist, not a completed security audit.

## Priority 1 — Meta Ads API / MCP
**Candidate:** [getmcpads-com/meta-ads-mcp-server](https://github.com/getmcpads-com/meta-ads-mcp-server)
- Why: purpose-built MCP adapter for Meta Ads Marketing API; repository documentation describes read tools for campaigns/insights and write tools that are disabled by default.
- License: Apache-2.0 (as stated in the repository README).
- Runtime: Node.js 22.12+ according to its current README.
- Important guardrails: begin with read-only scopes such as `ads_read`; do not set `META_ENABLE_WRITES=1` during initial setup. Review the exact release, tool schemas, permissions, security policy and CI before deployment.
- Main limitation: this adapter does not grant Meta access; a valid Meta app/token and approved account permissions are still required. Its hosted UI/features are not all included in the standalone repository.
- Initial decision: **evaluate first for read-only reporting**, then separately assess guarded writes.

## Priority 2 — Social publishing and content calendar
**Candidate:** [gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app)
- Why: open-source social media management platform with scheduling, publishing, analytics and an API; repository README lists Facebook and multiple other social networks.
- License: AGPL-3.0 according to repository README.
- Initial decision: **evaluate for draft-first scheduling**. Review AGPL obligations and supported Facebook/Page permissions before integrating or modifying.
- Risks/unknowns to verify: exact feature availability in self-hosted edition, current provider API restrictions, setup complexity, asset permissions and whether all desired actions are available through the public API.

## Priority 3 — Customer conversations
**Candidate:** [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot)
- Why: customer engagement/inbox platform potentially useful for consolidating conversations and support workflows.
- License: repository states MIT for content outside its `enterprise/` directory, with enterprise code under a separate license.
- Initial decision: **evaluate inbox and channel coverage**, especially whether the exact Facebook/Instagram messaging workflow required is supported in the intended deployment.
- Do not assume access to private messages or Page inbox data without verifying Meta's current permissions and product/API constraints.

## Priority 4 — CRM
**Candidate:** [twentyhq/twenty](https://github.com/twentyhq/twenty)
- Why: self-hostable CRM candidate for contacts, opportunities and a sales pipeline.
- License: primarily AGPL-3.0 with specific enterprise-file and MIT-package exceptions described in its LICENSE.
- Initial decision: **evaluate as a structured sales record system**, not as the first messaging connector.
- Risks: larger deployment footprint than a simple spreadsheet; review license, hosting requirements, API/webhooks and current edition boundaries.

## Priority 5 — Workflow orchestration
**Candidate:** [n8n-io/n8n](https://github.com/n8n-io/n8n)
- Why: broad workflow orchestration and integration ecosystem.
- License: the repository's LICENSE describes a Sustainable Use License for applicable files, with enterprise-file exceptions; do not label it OSI-approved open source.
- Initial decision: **evaluate only after licensing review** for the intended internal/commercial usage and after a minimal architecture is agreed.
- Alternative: use a small custom Python orchestrator if licensing, resource use or deployment complexity is unsuitable.

## Candidate architecture
1. **Research & planning:** Agent Team Starter + source/evidence registry.
2. **Ad performance:** Meta Ads MCP read-only adapter.
3. **Content workflow:** content drafts → human approval → Postiz schedule/publish.
4. **Conversation workflow:** Chatwoot only if channel support and permissions are confirmed.
5. **Sales record:** CRM (Twenty or a simpler initial order ledger).
6. **Automation:** n8n or a small custom workflow layer.
7. **Measurement:** delivered-order economics and a source-linked reporting ledger.

## Required due diligence before installing any candidate
- Pin a tagged release or commit SHA; avoid blindly tracking `latest`.
- Verify license and all enterprise/hosted feature boundaries.
- Inspect dependency health, security advisories, CI status, permissions and secret handling.
- Confirm self-hosted CPU/RAM/storage needs and whether external services are mandatory.
- Test with synthetic data and read-only credentials first.
- Record known gaps, rollback steps, and the evidence used for acceptance.
