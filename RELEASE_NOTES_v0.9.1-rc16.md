# Agent Team Starter v0.9.1-rc16

## Changes
- Bound each planner/executor/reviewer output to 30,000 characters. Over-limit outputs stop the run at that stage and preserve stage-aware failure metadata.
- Prevent raw exception text from being echoed in `TeamExecutionError` messages, reducing accidental disclosure of provider response fragments or custom-router details in CLI output. The original exception remains available via the Python `cause` attribute for controlled debugging.
- Added regression coverage for both safeguards.

## Verification scope
- Offline regression, evaluator, archive, prompt-injection fixture-integrity, static-hygiene, and compilation checks are required before packaging.
- No live provider calls, external network requests, or paid actions are required for these checks.
- This candidate does not claim live-model quality or full security certification.
