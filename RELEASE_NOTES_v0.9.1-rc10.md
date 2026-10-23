# Agent Team Starter v0.9.1-rc10

Date: 2026-10-23  
Status: local release candidate; not production-approved.

## Changes
- Added `evaluations/archive_audit.py`, a standard-library-only ZIP hygiene validator for path traversal/absolute paths, duplicate entries, symlinks, selected runtime artifacts, `.env` files, bytecode, and ZIP CRC errors.
- Added six tests covering clean archives, traversal and absolute paths, Windows-style path normalization, runtime/`.env` artifacts, duplicate names, symlink entries, and invalid archives.
- Integrated the new tests into the offline test runner. The packaged archive is separately checked with the archive validator after creation.
- Updated the notebook archive reference to rc10.

## Verification scope
- Regression tests: 41/41 passed.
- Evaluation tests: 28/28 passed, including 6 archive-audit tests.
- Deterministic reference cases: 12/12 passed.
- Prompt-injection fixtures: 10 structurally valid; not a live-model resistance test.
- Offline source hygiene audit: 54 files scanned, no flagged secret candidates or read errors.
- Release ZIP archive audit: 59 entries checked, 0 findings; ZIP CRC and extracted-archive full test suite passed.
- See `rc10_test_results.txt` for exact output.
- Source hygiene audit remains heuristic; archive audit checks only its documented rules. Neither proves that all secrets or vulnerabilities are absent.
- Prompt-injection fixtures are structural fixtures only; no live LLM resistance score is claimed.
- No third-party dependencies installed; no API/network calls or spending.

## Still open
- Dedicated Gitleaks/Semgrep/OSV-Scanner/pip-audit runs.
- Live-model evaluation and human scoring for benchmark cases currently marked `not_run`.
- Actual egress-proxy destination-IP enforcement and DNS-rebinding tests.
- Existing unrelated global `pip check` conflict: moviepy requires `pillow<12`, installed Pillow is 12.3.0. Neither package is a project requirement; no environment packages were changed.
