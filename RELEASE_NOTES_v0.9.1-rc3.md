# Agent Team Starter v0.9.1-rc3 — release candidate

## Changes from rc2
- Adds `evaluations/offline_benchmark.py`, an offline deterministic benchmark harness for a narrowly mapped subset of the 12-task evaluation plan.
- Emits a machine-readable JSON report with each task marked `passed`, `failed`, or `not_run`; live-model and human tasks are not assigned invented results.
- Adds a regression test that enforces the report's explicit `not_run` states and zero network/provider calls for the offline run.
- Updates README and changelog with invocation and limitations.

## Validation
Validation completed in the local environment:
- Regression suite: 29/29 passed.
- Evaluation suite: 13/13 passed.
- Reference evaluator: 12/12 reference cases passed.
- `compileall`: passed.
- Notebook JSON/metadata: passed.
- Benchmark specification: 12 unique task IDs.
- Offline runner: 4 deterministic task groups passed, 0 failed, 8 live/human tasks explicitly `not_run`.
- No provider API calls or paid services were used. The runner's local checks use mocked network/provider boundaries; no live egress proxy was verified.

A successful offline report is not a general quality or production-security certification.

## Security limitation
SSRF hardening remains fail-closed unless `AGENT_TEAM_TRUSTED_EGRESS_PROXY` is configured. The proxy must be independently configured and verified to enforce destination-IP policy after DNS resolution on each connection. Mocked tests do not prove that an actual proxy has this property.
