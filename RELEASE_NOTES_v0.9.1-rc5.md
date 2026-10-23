# Agent Team Starter v0.9.1-rc5 — proxy configuration hardening

## Changes
- Added `_validate_egress_proxy()` to validate proxy URL syntax before passing it to `requests`.
- Rejects credentials embedded in proxy URLs, malformed/out-of-range ports, control characters, and paths, queries, or fragments.
- Allows localhost proxy endpoints intentionally, because a trusted local egress proxy can be a valid deployment choice. Localhost is not treated as trusted merely because it is local.
- Added five regression tests covering the new proxy validation rules.

## Verification
- Regression tests: 36 passed.
- Evaluator tests: 13 passed.
- Deterministic reference cases: 12 passed.
- All checks ran locally without API calls, network requests, package installations, or spend.

## Security limits
- This is a release candidate, not production approval.
- URL syntax validation does not prove the configured proxy blocks private, loopback, link-local, reserved, or metadata-service destinations after DNS resolution.
- DNS rebinding protection remains dependent on independently verified network-level egress controls.
- No live-model quality, latency, cost, or human-intervention evaluation was run.
