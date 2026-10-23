# Agent Team Starter v0.9.1-rc1 — security hardening candidate

Status: release candidate for offline validation; not a production security certification.

## Changes
- Page retrieval fails closed unless `AGENT_TEAM_TRUSTED_EGRESS_PROXY` is configured.
- Added regression tests proving the fetcher makes no direct request when the proxy is missing or malformed.
- Added a 12-task realistic benchmark specification and CSV results template.
- Fixed Colab notebook metadata to identify v0.9.1.

## Verification
- 29 regression tests passed.
- 11 evaluator tests passed.
- 12 deterministic reference cases passed.
- Python compile check and ZIP integrity check are required before packaging.
- No live provider/API calls or spend were used.

## Security boundary
The configured proxy must be administrator-controlled and enforce destination-IP restrictions after DNS resolution for every connection. A generic proxy is not sufficient. This candidate does not claim complete SSRF protection absent verified network egress controls.

## Not measured
No live model accuracy, source quality, latency, cost, or human intervention rate has been measured. The benchmark file is a test specification, not benchmark results.

## Follow-up fix (rc2)
- Fixed a schema mismatch in the benchmark CSV template: its header now matches the scorer's required columns.
- Added a regression test to prevent template/scorer schema drift.
