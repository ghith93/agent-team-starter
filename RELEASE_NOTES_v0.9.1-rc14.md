# Agent Team Starter v0.9.1-rc14

Date: 2026-10-23  
Status: local release candidate; not production-certified.

## Changes
- Added a GitHub Actions workflow for offline regression tests and compilation, using Node 24-compatible major action releases.
- Added external security jobs for Bandit, pip-audit, Semgrep (finding-gated), detect-secrets (explicit finding gate), and Gitleaks.
- Added scheduled weekly scanning and artifact retention for machine-readable reports.
- Documented the exact workflow trigger, expected artifacts, and limitations in `SECURITY_SCANNING.md`.

## Verification performed locally
- Carried forward the rc13 source and release contents without removing prior release notes.
- Workflow syntax and contents were reviewed locally; GitHub Actions itself was not run.
- The local environment previously failed DNS resolution when attempting to install external scanners. Therefore no claim is made that Gitleaks, Semgrep, Bandit, pip-audit, or detect-secrets ran locally.
- Full offline tests and final ZIP hygiene audit are recorded in the accompanying release evidence.

## Important limitation
This release adds CI configuration only. The external scanners will run after the archive is pushed into a GitHub repository with Actions enabled. A successful local build does not imply that external scans have passed or that the project is production-certified.
