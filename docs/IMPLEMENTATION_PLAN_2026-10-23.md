# Implementation Plan — Marketing & Sales Agent Stack
Date: 2026-10-23
Status: planning baseline; no live account connected and no campaigns published.

## Objective
Prepare a low-cost, auditable agent workspace that can support:
1. Meta Ads analysis and carefully gated campaign operations.
2. Organic content planning, creation, approval, scheduling and performance tracking.
3. Lead/conversation tracking and sales pipeline management.
4. Delivered-order economics, attribution and reporting.
5. Research, evaluation and workflow automation through MCP/API integrations.

## Current verified baseline
- GitHub connector has read/write access to this repository; the project repo itself was previously almost empty.
- The locally archived Agent Team Starter v0.9.1-rc16 ZIP was recovered from the user's Library.
- ZIP integrity check passed.
- Local offline checks passed: 47 core tests, 39 evaluation tests, 12 reference calculations, 10 structurally valid prompt-injection fixtures, and static hygiene scan with no flagged candidates.
- These are offline checks only. No live-model quality, live egress policy, GitHub Actions run, Meta access, or production security certification is claimed.

## Workstreams for today
### A. Source-of-truth restoration
- Preserve the recovered release archive and its SHA-256 evidence.
- Reconcile the repository contents with the archive before treating GitHub as canonical.
- Keep changes on a branch and review through a pull request; do not force-push or change `main` directly.
- Re-run tests from the exact candidate that is proposed for merge.

### B. Meta Ads connector
- Evaluate `getmcpads-com/meta-ads-mcp-server` first for read-only campaign insights and guarded write operations.
- Start with read-only permissions; writes remain disabled until separately configured and explicitly approved.
- Test permissions, account discovery, metric definitions, date ranges, currency, and read-after-write verification before considering any mutation.
- Never publish, pause, reactivate, or change budgets as part of setup tests.

### C. Organic content operations
- Evaluate `gitroomhq/postiz-app` for publishing/scheduling and platform support.
- Use draft/approval states first. Verify exact Facebook Page and Instagram assets, supported APIs, rate limits, and self-hosting requirements.
- Generated content must be reviewed for factual claims, rights, platform rules and brand consistency before publication.

### D. CRM and sales pipeline
- Evaluate Chatwoot for customer conversations and Twenty for CRM workflows; do not assume either supports every desired Meta inbox or messaging path without verification.
- Build a minimal order lifecycle: new lead → qualified conversation → confirmed order → dispatched → delivered → returned/cancelled.
- Calculate acquisition cost against delivered orders and contribution margin, not message count alone.

### E. Orchestration and reporting
- Evaluate n8n as the workflow orchestrator only after checking its license restrictions for the intended use.
- Keep secrets in the deployment's secret store/environment, never in source control, prompts, logs, notebooks or chat.
- Add audit logs, idempotency, retries, rate limiting, approval gates, and a kill switch before enabling any external side effects.

## Acceptance gates
- [ ] Project source and release archive are reconciled.
- [ ] CI and security scanners run on the candidate; results are recorded accurately.
- [ ] Each dependency has a recorded license, activity check, deployment footprint, required credentials, and integration limits.
- [ ] Meta connection works in read-only mode and only exposes authorized assets.
- [ ] Content can be drafted and previewed without publishing.
- [ ] CRM can track a test lead/order without contacting a real customer.
- [ ] Sales dashboard reconciles chats to confirmed, delivered, returned and cancelled orders.
- [ ] No paid service, campaign spend, message sending, or public posting occurs during setup tests.

## Non-goals for this setup session
- No claim of unrestricted access to all user accounts.
- No claim that an MCP connector grants Meta permissions by itself.
- No campaign publishing, budget change, customer messaging, or irreversible account action.
- No claim that open-source software is automatically safe, free to operate, or production-ready.
