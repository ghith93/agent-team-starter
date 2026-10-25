# Roadmap

This roadmap prioritizes evidence, reversible changes, and free/open-source options. A roadmap item is complete only when its evidence is recorded.

## Phase A — Baseline and documentation
- [x] Establish a pre-audit recovery reference branch (not an independent backup).
- [x] Record verified state and known unknowns.
- [x] Add an iPhone-first runbook and license-decision record.
- [x] Reapply operational documentation on current `main` and preserve the narrowed secret-scanner fix.
- [x] Review `.gitignore` and keep `.env.example` trackable.

## Phase B — Repository safeguards
- [x] Enable and verify the active `main` ruleset: PR required, six correctly named checks required, zero required approvals, force pushes blocked; verified 2026-10-25.
- [ ] Verify Secret Scanning and Push Protection availability and state.
- [x] Keep Gitleaks scanning on PRs and run history-aware scans in CI.
- [ ] Add a synthetic canary test proving the secret scanner fails closed without committing a real credential.
- [x] Enforce read-only workflow/job permissions and full-SHA pins for external GitHub Actions with regression checks; latest main checks observed 2026-10-26.
- [ ] Decide on a root license after confirming intended reuse/distribution policy.

## Phase C — Test quality
- [x] Keep offline regression/evaluator tests deterministic and provider-free.
- [x] Run Python compilation and YAML parsing in CI.
- [x] Generate deterministic reports as workflow artifacts.
- [x] Add queue, memory, deployment-preflight, shell-syntax, backup/restore, and CLI regression tests.
- [x] Run Gitleaks, Bandit, pip-audit, Semgrep, and detect-secrets in CI for the reviewed PR #28 head.
- [ ] Continue review of scanner findings and dependency updates; CI success is not a blanket security guarantee.
- [ ] Add any further redirect-handling and malformed-provider-response tests only where current coverage is insufficient.

## Phase D — Monitoring and recovery
- [x] Add opt-in durable SQLite queue state with worker leases, stale-worker fencing, bounded retries, and terminal failure state.
- [x] Add local queue health checks and backup/restore scripts with temporary-database tests.
- [x] Provide systemd unit/timer templates and an iPhone-first deployment preflight/runbook.
- [ ] Identify/provision a suitable runtime host before enabling a continuous worker.
- [ ] Select a backup destination separate from the primary repository/account and encrypt it.
- [ ] Perform and document an operational restore drill from the independent backup destination.
- [ ] Configure external monitoring and verify that a test alert reaches the intended destination.
- [ ] Add retry jitter/circuit breaker only if real runtime behavior and failure modes justify it.

## Phase E — Free/open-source capability review
- [ ] Compare maintained tools against actual needs, license, permissions, free-tier quotas, and iPhone usability.
- [x] Evaluate Graphify as an optional offline code-graph pilot; keep it nonessential and review output manually.
- [ ] Run a genuine cross-model quality trial only with authorized existing CLI sessions and a bounded budget; do not use paid APIs by default.
- [ ] Keep optional tools isolated, tested, and removable.

## Phase F — Operational acceptance
- [x] On main commit `0f46b28ae6b6c624fb54549b2ebbf48474529aa3`, `tests`, YAML validation, Gitleaks, and offline regression/evaluator checks were observed passing; aggregate Python SAST/secrets/dependency audit was still in progress at last check. Recheck the exact commit before claiming complete CI success.
- [ ] Verify GitHub Secret Scanning and Push Protection settings; review ruleset bypass/freshness policy separately.
- [ ] Deploy to an explicitly chosen host and verify restart/recovery behavior.
- [ ] Test external alert delivery.
- [ ] Test off-host backup restoration.
- [ ] Document known limitations and free-tier failure modes before claiming production readiness.
