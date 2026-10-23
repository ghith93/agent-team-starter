# Independent Audit and Promotion Readiness

Audit date: 2026-10-23
Candidate reviewed: `integration/github-mcp-access-check`
Candidate merge commit: `cea453678238e088e2e4d1fbb2d75d41deb8a81b`

## Purpose and scope

This is an evidence-based review of repository controls and promotion risks. It is not a penetration test, formal security certification, or proof of production readiness. Review of source and existing CI is independent of the project's model-based Reviewer stage, but it is not an external third-party audit.

## Verified evidence

- PR #4 is merged into `integration/github-mcp-access-check`, not `main`.
- Post-merge offline regression/evaluator checks and Gitleaks passed on the merge commit.
- Python SAST, secrets, and dependency audit completed successfully on the post-merge workflow run recorded in issue #5.
- The project has no code-execution or browser/account-control capability through model prompts; generated text is not executed by the team workflow.
- Router retries are bounded to one retry for transient errors; authentication/permission and invalid-request errors are not retried as transient errors.
- Stage input is bounded to 12,000 characters and each model stage output to 30,000 characters. Telemetry is opt-in and records stage metadata rather than task/output text.
- URL retrieval fails closed without `AGENT_TEAM_TRUSTED_EGRESS_PROXY`, blocks redirects, disables ambient proxy inheritance, and enforces response size/time bounds.

## Risks and limitations still open

1. **Main branch protection is unknown.** The available GitHub integration received HTTP 403 when querying branch protection. Do not interpret this as proof that protection is absent. An owner/admin must inspect repository Settings → Rules/Branches and verify required reviews/checks, force-push/deletion restrictions, and bypass permissions.
2. **Network egress remains an external trust boundary.** URL syntax/DNS checks do not fully prevent DNS rebinding or guarantee what IP a proxy ultimately connects to. Any deployment enabling page retrieval must verify that the configured egress proxy blocks loopback, private, link-local, reserved, and metadata-service destinations after DNS resolution and at connection time.
3. **Prompt-injection resistance is not guaranteed.** Role separation and offline fixtures are defense-in-depth. The existing fixture suite is not a live adversarial evaluation of hosted models.
4. **Provider behavior and answer quality remain unproven for this merge commit.** Offline checks do not establish current quotas, service availability, factual accuracy, or live task success. No live-provider test is required by the promotion gate, so it can be run without provider keys or quota.
5. **Scanner versions are not fully pinned.** The security workflow installs scanner packages at run time. Its recorded versions improve auditability but do not make every run reproducible.
6. **Promotion size is substantial.** Integration is 59 commits ahead of main. Review the complete diff and release intent, not only the latest fix.
7. **Live-provider smoke test trigger is not a substitute for a release gate.** The existing live test is scoped to its configured branch and may use provider quota. It must not be described as a post-merge live verification unless a run against the exact candidate SHA is found.

## Promotion checklist

- [ ] Repository owner verifies main branch rules and records evidence.
- [ ] Review the integration-to-main diff and confirm all 59 commits belong in the release.
- [ ] Open a dedicated promotion PR from integration to main; do not push directly to main.
- [ ] Require the promotion-gate workflow and existing security/offline workflows to pass on the exact PR head.
- [ ] Review benchmark reports and distinguish offline deterministic checks from live-model/human checks marked not run.
- [ ] Decide whether a live-provider test is justified; check quota and cost first and require explicit approval before any potentially billable request.
- [ ] Verify an egress proxy's actual network policy before enabling URL retrieval in a deployed service.
- [ ] Obtain human review/approval from an authorized repository maintainer.
- [ ] Merge only after all above conditions are satisfied; retain workflow links and rollback commit.

## Decision

**Not approved for automatic promotion yet.** CI is green, but branch protection is unverified, the candidate contains 59 commits beyond main, and network/live-model risks require explicit review. Keep main unchanged until the checklist is completed.

## No-cost execution policy

The automated promotion gate runs offline tests, static skill metadata checks, a deterministic benchmark, compilation, and dependency audit. It does not configure API keys, call hosted models, deploy a service, publish content, or change accounts. The dependency audit needs package-index network access but does not require a paid service.
