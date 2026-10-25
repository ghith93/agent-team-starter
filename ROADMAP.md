# Roadmap

This roadmap prioritizes evidence, reversible changes, and free/open-source options. A roadmap item is not complete until its test evidence is recorded.

## Phase A — Baseline and documentation
- [x] Establish a pre-audit recovery branch.
- [x] Record the current verified state and known unknowns.
- [x] Add an initial iPhone-friendly runbook.
- [x] Verify all CI and security workflows on the repair branch (latest recorded run passed).
- [x] Review .gitignore and environment example; confirm `.env.example` remains trackable.
- [x] Run Gitleaks against full repository history and working tree in CI; this is not a guarantee that no credential exists outside scanned scope.

## Phase B — Repository safeguards
- [ ] Enable an appropriate main-branch ruleset/protection (require PR and successful checks where supported).
- [ ] Verify Secret Scanning and Push Protection availability and state.
- [ ] Keep Gitleaks scanning on pushes and pull requests; separately verify failure behavior with a synthetic test fixture that contains no real credential.
- [ ] Review permissions and pin third-party GitHub Actions to verified immutable commit SHAs.
- [ ] Decide on a root license after confirming the intended reuse/distribution policy.

## Phase C — Test quality
- [ ] Keep offline tests deterministic and free of provider API calls.
- [ ] Add regression tests for URL validation, redirect handling, provider error redaction, and malformed provider responses.
- [ ] Run Python compilation and YAML parsing in CI.
- [ ] Generate reports as artifacts without uploading secrets or customer data.
- [ ] Review dependency audit findings and update only after compatibility tests.

## Phase D — Monitoring and recovery
- [ ] Identify whether the application is a scheduled job, webhook service, or continuously running worker.
- [ ] Define a minimal health check that does not expose secrets or internal diagnostics.
- [ ] Add a scheduled external check only after a verified endpoint and alert destination exist.
- [ ] Add retry with exponential backoff and jitter where safe; cap retries and avoid retrying authentication/configuration errors.
- [ ] Add a circuit breaker for repeated transient failures if the runtime model requires it.
- [ ] Select a backup destination separate from the primary repository/account.
- [ ] Perform and document a restore drill before claiming backup coverage.
- [ ] Add mobile-friendly recovery instructions and alert delivery test.

## Phase E — Free/open-source capability review
- [ ] Compare maintained tools against actual project needs, license, permissions, free-tier quotas, and iPhone usability.
- [ ] Prefer one tool integration at a time, with a test and rollback plan.
- [ ] Do not add a continuously running server or paid external dependency merely to satisfy a 24/7 label.

## Phase F — Operational acceptance
- [ ] CI passes on the proposed change.
- [ ] Security checks have reviewed outcomes; no unexplained findings are suppressed.
- [ ] Secret protection and branch protection states are recorded.
- [ ] Monitoring alert delivery is tested.
- [ ] Backup restoration is tested.
- [ ] Known limitations and free-tier failure modes are documented.
