# Agent Team Starter v0.9.1-rc12

Date: 2026-10-23  
Status: local release candidate; not production-approved.

## Changes
- Planner, Executor, and Reviewer policies now use provider-native system-instruction fields for OpenRouter and Gemini, rather than being concatenated into the user message.
- User task and inter-stage outputs remain user content; plan and draft are explicitly marked untrusted in subsequent stages.
- Added offline tests verifying the outgoing request payload shape for both provider formats and confirming stage instructions are separated.
- Updated README, changelog, and Colab notebook archive reference to rc12.

## Verification scope
- Full offline regression/evaluation gate passed; see `rc12_test_results.txt` for exact counts.
- Request-payload tests use mocked HTTP responses; they do not make network calls or verify provider-side behavior.
- No external dependencies installed, no live model calls, no external network requests, and no spending.

## Limitations / remaining work
- System/user separation is defense-in-depth and does not prove prompt-injection resistance.
- No Gitleaks, Semgrep, OSV-Scanner, or pip-audit scan has been run.
- Live-model quality, adversarial prompt-injection resistance, real egress-proxy enforcement, and DNS-rebinding resistance remain unverified.
- Tasks sent to configured hosted providers are transmitted to those providers; review data-handling terms and do not submit secrets without authorization.
