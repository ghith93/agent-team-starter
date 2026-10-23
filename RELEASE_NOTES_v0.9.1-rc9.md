# Agent Team Starter v0.9.1-rc9

Date: 2026-10-23  
Status: local release candidate; not production-approved.

## Changes
- Added `evaluations/security_audit.py`, a standard-library-only offline hygiene audit for common credential shapes, selected risky-code patterns, and dependency range notes. Credential values are never copied into findings.
- Added four tests for clean inputs, secret-shape detection with redaction, review-level code findings, and unbounded dependency ranges.
- Integrated the hygiene audit into `python run_tests.py` and updated the notebook archive reference to rc9.

## Validation scope
The audit is heuristic and may miss secrets or produce false positives. It does not inspect remote vulnerability databases, prove that dependencies are vulnerability-free, or replace Gitleaks/Semgrep/OSV-Scanner/pip-audit. Review-level code findings are prompts for manual review, not confirmed vulnerabilities. Live-model quality, real egress proxy enforcement, and DNS-rebinding resistance remain unverified.

## Constraints
- No third-party dependencies added or installed.
- No network requests or API calls made by project tests.
- No spending.
- Previous release candidates are preserved unchanged.

## Verification results
- 41/41 regression tests passed.
- 22/22 evaluation tests passed.
- 12/12 deterministic reference cases passed.
- 10 prompt-injection fixtures passed structural validation.
- Offline hygiene scan: 51 source-like files scanned; no high-confidence secret candidates, read errors, review findings, or dependency-range notes.
- `compileall`, notebook JSON/archive-reference checks, and ZIP integrity checks passed. The full test suite is rerun from the extracted release archive before packaging is considered verified.
- Environment note: `pip check` reports an unrelated pre-existing global environment conflict (`moviepy` requires `pillow<12`, while installed `pillow` is 12.3.0). Neither package is listed in this project's `requirements.txt`; no environment packages were changed.

## Still not verified
- The offline hygiene scan is not equivalent to Gitleaks, Semgrep, OSV-Scanner, or pip-audit.
- No live model or real tools were used to score prompt-injection resistance.
- No real egress proxy or DNS-rebinding test was performed.
- The 12-task offline benchmark still has 8 tasks marked `not_run` because they require live-model or human evaluation.
