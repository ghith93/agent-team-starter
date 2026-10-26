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


## Expanded eight-way comparison (2026-10-26)

Successful workflow: https://github.com/ghith93/agent-team-starter/actions/runs/40248469953  
Artifact ID: `12619536778` (`ruflo-protobufjs-remediation-comparison`).

| Candidate | Critical | High | Moderate | Total |
|---|---:|---:|---:|---:|
| CLI 3.63.0 baseline | 1 | 14 | 22 | 37 |
| CLI 3.63.0 + `protobufjs@7.6.6` | 0 | 12 | 22 | 34 |
| CLI 3.63.0 + protobufjs override + lockfile-only audit fix | 0 | 12 | 22 | 34 |
| CLI 3.62.0 | 1 | 14 | 22 | 37 |
| CLI 3.62.0 + `protobufjs@7.6.6` | 0 | 12 | 22 | 34 |
| CLI 3.32.29 | 1 | 12 | 23 | 36 |
| CLI 3.32.29 + `protobufjs@7.6.6` | 0 | 10 | 23 | 33 |
| CLI 3.63.0 + `protobufjs@7.6.6`, `zod@4.6.6`, `sharp@0.35.5` | 0 | 2 | 26 | 28 |

### Interpretation

- The CLI downgrade to 3.32.29 alone reduces the total by only one finding and leaves one critical finding. With the protobufjs override it reports 33 findings (0 critical, 10 high), but it is still a breaking-version downgrade and not an acceptable production recommendation without compatibility testing.
- The targeted three-package override produces the lowest observed count: 28 (0 critical, 2 high, 26 moderate). In this report, the two remaining high findings are associated with the OpenTelemetry Jaeger propagator and OpenTelemetry SDK Node dependency tree. Ruflo/agentdb and numerous OpenTelemetry moderate findings remain.
- These are npm audit advisory counts for a synthetic, lockfile-only dependency graph. Counts are not a direct measure of exploitability, and one package can aggregate multiple advisories. All candidate audit commands exit 1 because vulnerabilities remain.
- The `sharp@0.35.5` and `zod@4.6.6` overrides are experimental. The lockfile resolves, but no package code was installed or run and no API/ABI compatibility was tested. In particular, forcing transitive versions may violate consumers' declared version expectations.

### Decision after expanded comparison

Keep Ruflo out of the production/runtime dependency set. The targeted override is the best **audit-only candidate for a later isolated compatibility experiment**, not a security approval or a mergeable runtime fix. The next safe step is to map the remaining OpenTelemetry advisories to their dependency constraints and test compatible patched version families in metadata-only experiments. Only after that should a separate disposable sandbox perform minimal smoke/compatibility tests with synthetic data, no secrets, and no repository write credentials.

The Python agent pipeline remains the production baseline. No runtime dependency was changed by this experiment.


## Final expanded dependency-graph audit (2026-10-26)

Successful 12-candidate run: https://github.com/ghith93/agent-team-starter/actions/runs/40249131130  
Artifact ID: `12619967852` (`ruflo-protobufjs-remediation-comparison`).

| Candidate | Critical | High | Moderate | Total |
|---|---:|---:|---:|---:|
| CLI 3.63.0 baseline | 1 | 14 | 22 | 37 |
| CLI 3.62.0 baseline | 1 | 14 | 22 | 37 |
| CLI 3.32.29 baseline | 1 | 12 | 23 | 36 |
| CLI 3.63.0 + protobufjs 7.6.6 | 0 | 12 | 22 | 34 |
| CLI 3.63.0 + protobufjs 7.6.6 + lockfile-only audit fix | 0 | 12 | 22 | 34 |
| CLI 3.62.0 + protobufjs 7.6.6 | 0 | 12 | 22 | 34 |
| CLI 3.32.29 + protobufjs 7.6.6 | 0 | 10 | 23 | 33 |
| protobufjs + zod + sharp overrides | 0 | 2 | 26 | 28 |
| Previous overrides + Jaeger propagator 2.9.0 + SDK Node 0.220.0 | 0 | 0 | 6 | 6 |
| Previous candidate + lockfile-only `npm audit fix` | 0 | 0 | 6 | 6 |
| Previous overrides + OpenTelemetry core/resources 2.8.0 | 0 | 0 | 0 | 0 |
| Previous overrides + OpenTelemetry core/resources 2.9.0 | 0 | 0 | 0 | 0 |

The two zero-finding candidates use these lockfile-only overrides: `protobufjs@7.6.6`, `zod@4.6.6`, `sharp@0.35.5`, `@opentelemetry/propagator-jaeger@2.9.0`, `@opentelemetry/sdk-node@0.220.0`, and either `@opentelemetry/core@2.8.0` + `@opentelemetry/resources@2.8.0`, or the matching 2.9.0 pair.

### What this result proves—and what it does not

- Both candidate lockfiles resolve, and `npm audit --json` reports zero known advisories for those resolved graphs at the time of the run.
- This is not proof that the packages are secure in every configuration, that no undisclosed or newly published vulnerabilities exist, or that the overrides are runtime compatible.
- The changes force versions across dependency ranges and major-version families. In particular, `protobufjs`, `sharp`, `zod`, and OpenTelemetry overrides may violate consumer assumptions or introduce behavioral/API incompatibilities. No package code was installed or executed, and no functional/ABI test was run.
- The lockfile-only `npm audit fix` pass for the OpenTelemetry-patched candidate remained at six moderate findings and recommended a breaking CLI downgrade. The explicit core/resources overrides removed those six findings from the audit graph, but are experimental.
- The existing Python agent pipeline was not changed. No Ruflo runtime dependency was added.

### Final audit disposition

**Metadata-only dependency audit: complete for the 12 tested candidates. Ruflo production approval: not granted.** The best observed audit result is zero reported advisories in the synthetic lockfile graph with the aligned core/resources 2.8.0 or 2.9.0 override. Before any runtime adoption, create a disposable, unprivileged compatibility test with synthetic inputs, no secrets, no repository write credentials, and explicit API/behavior tests; independently review the remaining moderate advisory surface in the Ruflo dependency tree and rerun the audit immediately before any promotion.


## Compatibility audit correction — global OpenTelemetry overrides are negative controls

The 12-candidate audit returned zero npm advisory findings for the global OpenTelemetry core/resources 2.8.0 and 2.9.0 overrides. A follow-up review of the resolved lockfiles found dependency-range conflicts, so these zero-count results must **not** be described as viable remediation candidates:

- The 2.8.0 candidate forces OpenTelemetry core/resources 2.8.0 while multiple OpenTelemetry packages in the same resolved graph declare an exact dependency on 2.9.0. This violates the dependency manifest's declared version contract.
- The 2.9.0 candidate aligns with the OpenTelemetry packages that require 2.9.0, but the lockfile shows `agentdb@3.0.0-alpha.20` declares optional dependency `@opentelemetry/resources@^1.25.0`; forcing the globally resolved resources package to 2.9.0 violates that declared major-version range. The old core/resources graph also has consumers expecting the 1.x family.
- `npm install --package-lock-only` allows these overrides to produce a lockfile; that is not equivalent to checking API/behavior compatibility. A zero audit count only means the specific lockfile graph did not match the advisories returned by npm at that time.

The workflow was corrected to remove the 2.8.0 global override from future runs and rename the 2.9.0 global override as a `negative-control` experiment. It remains useful for demonstrating how an over-broad override can make advisory counts look clean while breaking declared dependency contracts.

### Revised conclusion

The best **plausible audit-only candidate** remains the targeted protobufjs/zod/sharp overrides plus the Jaeger propagator and SDK Node version adjustments (six moderate findings), but it is still not runtime-approved. The remaining findings include Ruflo/agentdb advisories and old OpenTelemetry core/resources pulled in for compatibility. Resolve these by updating or replacing the consumers that require 1.x, or by using parent-scoped overrides that preserve declared ranges; do not force a global major-version replacement merely to reach zero findings.

Ruflo is not approved for production. No runtime dependency changes were made. Any compatibility work must be isolated, unprivileged, use synthetic inputs, and run explicit tests before promotion.
