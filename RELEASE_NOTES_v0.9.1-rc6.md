# Agent Team Starter v0.9.1-rc6 — explicit egress routing

## Changes
- Uses an explicit `requests.Session` with `trust_env=False` for public-page fetching. This prevents ambient `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`/`no_proxy` settings from silently bypassing or changing the explicitly configured trusted egress proxy.
- Retains rc5 proxy URL syntax checks: no embedded credentials, invalid ports, control characters, paths, queries, or fragments.
- Adds a regression test that deliberately sets conflicting ambient proxy and no-proxy variables and verifies the explicit egress proxy is used in the request configuration.

## Verification
- Regression tests: 37 passed.
- Evaluator tests: 13 passed.
- Deterministic reference cases: 12 passed.
- Local compile and archive tests run without installing dependencies, making API calls, requesting external network resources, or spending money.

## Security limits
- This is a release candidate, not production approval.
- The test proves only the Python request configuration, not that the configured proxy actually blocks private, loopback, link-local, reserved, or metadata-service destinations after DNS resolution.
- DNS rebinding resistance remains dependent on independently verified network-level egress controls.
- `trust_env=False` also disables implicit environment-based netrc authentication and environment-based CA-bundle selection; configure any required trust roots explicitly through the runtime/deployment environment.
- No live-model quality, latency, cost, or human-intervention evaluation was run.
