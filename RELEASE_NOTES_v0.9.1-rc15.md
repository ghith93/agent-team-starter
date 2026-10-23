# Agent Team Starter v0.9.1-rc15

Date: 2026-10-23  
Status: local release candidate; not production-certified.

## Changes
- Updated `actions/checkout` to major v7 after reviewing the upstream release page.
- Added offline regression tests that guard the security workflow contract: required triggers, read-only permissions, expected jobs/scanners, explicit fail-closed enforcement, report uploads, and full-history Gitleaks checkout.
- Updated the Colab notebook archive reference to rc15.

## Verification performed locally
- `python run_tests.py` passed, including the new workflow contract tests.
- `python -m compileall -q agent_team evaluations tests` passed.
- Workflow YAML parsed successfully with the locally available `ruamel.yaml` parser; contract checks passed.
- ZIP integrity, contents, SHA-256, and archive hygiene are recorded in the companion evidence files.

## Limitations
- GitHub Actions was not run and the repository was not pushed.
- Bandit, pip-audit, Semgrep, detect-secrets, and Gitleaks have not been run against this candidate; no external scanner pass is claimed.
- Action references still use major tags rather than immutable full commit SHAs, and scanner package versions are resolved at run time.
- No live-model, prompt-injection, SSRF/DNS-rebinding, or real network-egress security validation was performed.
