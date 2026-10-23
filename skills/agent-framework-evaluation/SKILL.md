---
name: agent-framework-evaluation
description: Compare agent frameworks or coding agents against an existing baseline using identical tasks, permissions, environments, timeouts, and scoring rules.
---

# Agent Framework Evaluation

1. State the hypothesis before choosing a candidate: which measurable limitation should the framework solve?
2. Freeze a baseline snapshot and a versioned task set. Record licenses, supported Python versions, dependencies, telemetry, permissions, network behavior, and maintenance activity.
3. Use identical task inputs, model/provider, tool allowlists, context, timeouts, environment, and retry policy for baseline and candidate.
4. Score task correctness and evidence quality separately from security violations, latency, token/API cost, tool calls, and human intervention.
5. Mark skipped tasks `not_run`; never convert a local unit test into a claim of end-to-end agent quality.
6. Repeat non-deterministic tasks and report spread, not just the best run. Keep raw outputs and redacted logs reproducible.
7. Reject candidates with a critical security regression regardless of aggregate score. Include integration and rollback costs in the decision.
8. Adopt only when measured improvement exceeds added complexity and maintenance burden; otherwise keep the smaller baseline.
