# Agent Team Starter v0.9

## What changed
- Hardened deterministic CAC evaluation against NaN, positive/negative infinity, non-finite results, and invalid tolerances.
- Expanded the offline reference suite from 6 to 12 cases: 8 arithmetic checks and 4 invalid-input checks.
- Added unit tests for non-finite values and tolerance validation.
- Retained v0.8 URL-fetch protections and CSV benchmark security gate.

## Verification
- Run `python run_tests.py` for the offline release gate.
- These checks establish only deterministic local behavior; they do not prove live model quality or availability.
- No live model/API calls or spending are required.

## Known security limitation
DNS rebinding is not fully prevented by application-level validation alone. Do not expose the public-page fetcher to hostile inputs without network-level egress controls.
