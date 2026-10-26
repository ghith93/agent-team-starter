# Ruflo protobufjs remediation experiment

**Reviewed:** 2026-10-26  
**Workflow run:** https://github.com/ghith93/agent-team-starter/actions/runs/40247878606  
**Scope:** Lockfile-only npm dependency resolution and `npm audit`. The workflow did not install dependencies into a runtime environment or execute Ruflo package code.

## Results

| Candidate | Critical | High | Moderate | Total |
|---|---:|---:|---:|---:|
| Baseline `@claude-flow/cli@3.63.0` | 1 | 14 | 22 | 37 |
| Override `protobufjs@7.6.6` | 0 | 12 | 22 | 34 |
| Override plus `npm audit fix --package-lock-only --ignore-scripts` | 0 | 12 | 22 | 34 |

The override candidate removes the nested `onnx-proto/node_modules/protobufjs@6.11.6` entry from the resolved lockfile. The audit finding count drops by three, and the critical count drops from one to zero in this specific comparison.

## What did not auto-fix

The lockfile-only `npm audit fix` pass exited with code 1 and did not reduce the finding count further.

- The audit log identifies `@claude-flow/security@3.0.5` as a bundled dependency of `@claude-flow/cli@3.63.0`; npm says it cannot be fixed independently and recommends checking for a CLI update.
- For several other findings, npm proposes changing `@claude-flow/cli` to `3.32.29`, marked as a breaking change. This experiment deliberately did not apply that downgrade.
- High-severity findings remain in the Ruflo package family and transitive dependencies, including OpenTelemetry, agentdb, agentic-flow, transformers, and sharp. See the workflow artifact for the full machine-readable audit output.

## Decision

**Do not treat Ruflo 3.63.0 as remediated or approved for production.** The protobufjs override is evidence for further investigation, not a runtime fix: `onnx-proto` may expect protobufjs 6.x behavior, and this lockfile-only test cannot verify compatibility.

Keep the existing Python agent pipeline as the baseline. If Ruflo is evaluated later, do so in an ephemeral unprivileged sandbox with synthetic inputs, no production secrets, no write access to the main repository, and explicit compatibility tests. Do not blindly apply the suggested CLI downgrade.

## Artifact

The full three-way comparison, lockfiles, npm audit JSON reports, and the audit-fix log are attached to the [successful workflow run](https://github.com/ghith93/agent-team-starter/actions/runs/40247878606).

## Additional version comparison (2026-10-26)

A five-way run compared `@claude-flow/cli@3.63.0` with `@claude-flow/cli@3.62.0`, each with and without the protobufjs override where applicable. The audit result for CLI 3.62.0 was identical to 3.63.0:

| Candidate | Critical | High | Moderate | Total |
|---|---:|---:|---:|---:|
| CLI 3.62.0, baseline dependencies | 1 | 14 | 22 | 37 |
| CLI 3.62.0 + `protobufjs@7.6.6` override | 0 | 12 | 22 | 34 |

Therefore, switching from 3.63.0 to 3.62.0 did not reduce the advisory counts on its own. The same protobufjs override was responsible for the improvement in both dependency trees.

- Successful five-way workflow: https://github.com/ghith93/agent-team-starter/actions/runs/40248135986
- Artifact ID: `12620000976` (retained by GitHub Actions for 14 days from creation).

This remains a metadata/lockfile audit only; it does not demonstrate that either CLI version or the override is safe at runtime.
