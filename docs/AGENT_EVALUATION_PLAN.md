# Agent Evaluation Plan

Updated: 2026-10-25

## Objective

Measure whether a workflow change improves completed task quality without increasing risk, runtime, or cost beyond agreed limits. Passing unit tests alone does not establish general task competence.

## Benchmark task contract

Every benchmark case should include:

- A stable case ID and version.
- A task prompt and a clean, disposable starting checkout.
- Explicit acceptance criteria.
- Deterministic tests or assertions wherever possible.
- A timeout and bounded retry policy.
- A record of model/provider configuration without secrets.
- Expected tool permissions and forbidden side effects.
- A result record containing pass/fail, test output references, duration, retry count, and known limitations.

Do not store provider credentials, private user data, or full sensitive task content in public benchmark artifacts.

## Starter task categories

1. Diagnose a failing test from a supplied fixture.
2. Make a minimal bug fix with a regression test.
3. Improve documentation without changing behavior.
4. Add validation for malformed input.
5. Review a patch and identify a seeded defect.
6. Diagnose a CI workflow failure from sanitized logs.
7. Reject a prompt-injection fixture that attempts to override system policy.
8. Reject an unsafe URL / SSRF fixture.

## Comparison protocol

- Run baseline and candidate against the same cases and acceptance checks.
- Use the same permission boundaries and comparable environment.
- Randomize run order when provider variance may bias results.
- Report per-case results, not only aggregate averages.
- Separate deterministic offline results from live-provider results.
- Record timeouts and failures; never silently drop failed cases.
- Do not run live comparisons unless credentials and provider quota are already configured and an authorized, non-billable or explicitly budgeted path is confirmed.

## Metrics

- Task success rate = accepted tasks / attempted tasks.
- Regression rate = previously passing cases that fail under the candidate.
- Retry rate and timeout rate.
- Median and p95 elapsed time when sample size supports them.
- Human intervention count.
- Security violations (release-blocking).
- Actual provider cost or quota usage where available; unknown cost must be reported as unknown, not zero.

## Promotion rule

Promote a candidate only when:
1. All mandatory deterministic checks pass.
2. No security boundary violation is observed.
3. It improves task success or another predeclared objective on the same cases.
4. Any latency/cost tradeoff is explicit and acceptable.
5. Results are reproducible and limitations are recorded.

Do not invent target percentages before collecting a baseline. Start with a small curated set, then expand cases based on real failures.
