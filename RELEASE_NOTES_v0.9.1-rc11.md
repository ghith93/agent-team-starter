# Agent Team Starter v0.9.1-rc11

Date: 2026-10-23  
Status: local release candidate; not production-approved.

## Changes
- Extended `evaluations/archive_audit.py` with configurable limits for ZIP entry count, individual uncompressed member size, total uncompressed size, and compression ratio.
- The auditor skips CRC decompression checks when an archive exceeds a configured metadata limit.
- Added four regression tests for these limits.
- Updated README, changelog, and Colab notebook archive reference to rc11.

## Verification scope
- Full offline regression/evaluation gate: passed; see `rc11_test_results.txt` for exact counts.
- Archive-specific tests: 10 passed.
- Release archive will be audited after packaging and tested again from extracted bytes.
- No third-party dependencies installed; no live provider/API calls, external network requests, or spending.

## Limitations / remaining work
- Limits are based on ZIP metadata and do not make extraction of arbitrary archives safe; use a sandbox for untrusted inputs.
- No Gitleaks, Semgrep, OSV-Scanner, or pip-audit scan has been run.
- Live-model quality, prompt-injection resistance, real egress-proxy enforcement, and DNS-rebinding resistance remain unverified.
