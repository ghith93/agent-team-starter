# Agent Team Starter v0.9.1-rc13

Date: 2026-10-23
Status: local release candidate; not production-certified.

## Changes
- Hardened provider error parsing: non-object JSON error bodies now produce a safe empty detail rather than raising an `AttributeError` that masks the provider error.
- Added regression tests for malformed provider error JSON and redaction of bearer/API-token-like values in provider error details.
- Updated the Colab notebook to point to the rc13 archive.

## Verification
- Regression suite: 45/45 passed.
- Evaluator suite: 32/32 passed.
- Reference arithmetic cases: 12/12 passed.
- Archive audit: run separately on the final release ZIP; see `rc13_archive_audit.json`.
- Offline static hygiene scan: 56 files scanned; zero high-confidence secret candidates, read errors, manual-review findings, or dependency-range notes.
- Python compileall passed; notebook JSON valid with 14 cells and the rc13 archive reference.
- Full tests were run from the extracted release archive as an additional release gate.

## External scanner attempt and limitation
The user authorized installing/running external scanners. An isolated `pip install --target ... bandit pip-audit` attempt was made, but the execution environment could not resolve the package index host (`Temporary failure in name resolution`). No package was installed and no system package was changed. Gitleaks, Semgrep, OSV-Scanner, and pip-audit therefore remain **not run**. `pip check` also reports an existing global environment conflict: `moviepy 2.2.1` requires `pillow<12`, while Pillow 12.3.0 is installed; neither is listed in this project's `requirements.txt`.

## Security limitations
- The offline scan is heuristic and is not a substitute for Gitleaks, Semgrep, OSV-Scanner, pip-audit, human review, or a threat model.
- No vulnerability database was queried; dependency vulnerability status is unknown.
- No live model call was made. Prompt-injection resistance and live-model quality remain unverified.
- DNS rebinding and actual network-level egress enforcement were not tested. Code-level URL checks alone are not a complete SSRF defense.
- No API calls or spending occurred.
