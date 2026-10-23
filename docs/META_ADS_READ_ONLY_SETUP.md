# Meta Ads MCP — Read-Only Evaluation Runbook
Reviewed: 2026-10-23
Candidate: https://github.com/getmcpads-com/meta-ads-mcp-server
Reviewed source release: v2.0.0 (2026-09-20)
License: Apache-2.0
Runtime: Node.js >=22.12

## Verified from the candidate repository
- The README labels the standalone server as 41 read tools and 23 optional write tools.
- `META_ACCESS_TOKEN` is required.
- `META_ENABLE_WRITES` is unset by default; setting it to `1` registers write tools.
- The README states write tools preview before applying changes, with explicit confirmation required.
- The repository says its hosted product's creative galleries and MCP Apps UI are not part of the standalone release.
- The `server.json` description specifies a Meta token with at least `ads_read`.
- CI in the source repository tests Node 22 and 24.

## Initial configuration policy
1. Pin the reviewed release/tag or commit; do not use an unpinned latest build for the first connection.
2. Use a token with `ads_read` only for the initial evaluation, and grant access only to the intended ad account/assets.
3. Do not define `META_ENABLE_WRITES`; verify the process environment does not inherit it from another shell or deployment.
4. Store `META_ACCESS_TOKEN` in the local secret manager or deployment environment. Never place it in this repository, a notebook, chat, screenshot, issue, or logs.
5. First verify account discovery, campaign/ad-set/ad reads, date range, currency, time zone, attribution settings, and metric definitions.
6. Compare a small sample of returned data against Ads Manager for the same account and period. Record discrepancies before relying on reports.
7. Use only read operations during setup. Do not create, publish, pause, reactivate, rename, or change any budget/audience/schedule.

## Acceptance checks before any write access is considered
- [ ] Correct Meta business and ad account identified.
- [ ] Token has the least-privilege scopes and asset assignments; no unnecessary write permissions.
- [ ] Read-only data reconciles with Ads Manager for an agreed test period.
- [ ] Tool catalog and arguments are inspected at the pinned version.
- [ ] Logs redact tokens and do not store customer data unnecessarily.
- [ ] A human approval gate and rollback/audit trail exist for every mutation.
- [ ] A separate explicit approval is obtained before write permissions are enabled.

## Limits and open questions
- GitHub authorization does not grant Meta authorization.
- The MCP server does not bypass Meta app review, access-token expiry, account restrictions, rate limits, or Marketing API policy.
- The local standalone server requires a compatible MCP client/runtime; ChatGPT availability must be verified for the user's actual connection path rather than assumed.
- This document is a configuration/runbook only. No Meta token was supplied or tested, and no live account was connected.
