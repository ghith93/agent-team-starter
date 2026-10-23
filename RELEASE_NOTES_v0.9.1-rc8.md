# Agent Team Starter v0.9.1-rc8

Date: 2026-10-23  
Status: local release candidate; not production-approved.

## Changes
- Added 10 structured prompt-injection test fixtures with explicit expected policy outcomes and prohibited behaviors.
- Covered untrusted webpage content, tool-output poisoning, fake-canary disclosure attempts, task override, unauthorized side effects, tool trust boundaries, quoted instructions, private-network access requests, evidence integrity, and safe completion.
- Added a standard-library-only fixture validator and tests for missing fields, duplicate IDs, and unsupported action labels.
- Integrated fixture-integrity validation into `python run_tests.py` and updated the Colab notebook to reference the rc8 archive.

## Validation scope
The prompt-injection suite validates only fixture structure. It does not call a model, exercise real tools, test network egress enforcement, or establish prompt-injection resistance. Live-model quality, real proxy enforcement, DNS-rebinding resistance, source quality, latency, cost, and human intervention remain unverified.

## Release constraints
- No third-party dependencies added.
- No external tools installed.
- No API calls or network requests made by project tests.
- No spending.
- Earlier release archives are preserved unchanged.
