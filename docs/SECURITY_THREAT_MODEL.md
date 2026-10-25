# Agent Team Starter Security Threat Model

Updated: 2026-10-25

## Scope and current limits

The application coordinates Planner, Executor, and Reviewer stages. Model outputs are untrusted text and must not be executed. The current product is not an autonomous computer-use agent and must not be described as one. Any later filesystem, shell, browser, or account integration is a new trust boundary and requires a separate design review.

## Assets to protect

- Provider credentials and environment variables.
- User task content, source code, and private repository data.
- CI tokens, repository write permissions, artifacts, and logs.
- Integrity of generated patches, tests, release archives, and benchmark reports.
- Availability and quota of free-tier providers and CI runners.

## Threats and required controls

| Threat | Minimum control | Evidence required |
|---|---|---|
| Prompt injection in task/research content | Treat retrieved content and model output as data, not authority; tool actions require independent policy checks | Regression fixtures and negative tests |
| Secret exposure | Never log credentials; scan history and working tree; redact provider errors | Gitleaks pass plus reviewed test coverage |
| Unsafe URL / SSRF | Validate destinations and redirects; enforce network-level egress policy after DNS resolution; block private, loopback, link-local, reserved, and metadata addresses | Unit tests plus deployment-level egress evidence |
| DNS rebinding | Validation and connection must share a safe resolution boundary or egress proxy must enforce destination policy at connect time | Architecture review and hostile DNS test |
| Dependency compromise | Reproducible dependency constraints and automated vulnerability audit | Completed pip-audit report |
| Generated-code execution | Do not execute model output by default; any future execution must be sandboxed with resource and network limits | Negative test and sandbox review |
| Over-privileged CI | Read-only token permissions by default; grant write scopes only to a specific workflow that needs them | Workflow permission review |
| Infinite retries / cost growth | Bounded retries, per-stage timeout, explicit provider selection and budget/quota controls | Deterministic tests and run trace |
| False success from incomplete scans | Distinguish pass, fail, skipped, cancelled, and unavailable; cancelled security jobs must not count as a pass | CI run and status gate |

## Release gate

A release candidate is not security-cleared unless:

1. Offline regression and deterministic evaluator suites pass.
2. Secret scanning completes successfully.
3. Dependency audit completes and findings are triaged.
4. Static security scans complete and findings are triaged.
5. Prompt-injection, URL/SSRF, error-redaction, and permission-boundary regression tests pass.
6. Any skipped or cancelled mandatory security check is reported as incomplete and blocks a security-clear claim.
7. The final report names exact commits, tools, results, and known gaps.

A scanner's clean output is evidence only for the rules and code it actually analyzed; it is not proof of absence of vulnerabilities.

## Claudex Loop trial gate

Keep the integration optional and isolated until it demonstrates measurable improvement on the same fixed tasks as the baseline. Record success rate, test results, retries, elapsed time, token/API use if available, and any security-boundary violations. Do not claim live model quality or zero cost without evidence. Never require a paid API key for offline CI.

## Incident handling

If a credential is exposed, revoke/rotate it at its provider, remove it from active configuration, inspect repository history and logs, and document the incident. Deleting a visible string alone is not sufficient if the credential remains valid or present in history.
