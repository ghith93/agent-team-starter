# Release report — Agent Team Starter v0.8

Date: 2026-10-23

## Outcome
Created v0.8 as a new release without overwriting v0.5 or v0.6. The release preserves the three-stage workflow and offline reference evaluator.

## Implemented
- Carries forward the v0.7 result contract, CLI configuration check, task-file input, metadata-only opt-in telemetry, provider-error sanitization, and configurable Gemini model.
- Adds `evaluations/benchmark_score.py` to score completed benchmark CSVs using validated fields and transparent scoring rules.
- A recorded security failure forces a `REJECT` release gate regardless of numeric score.
- Hardens public URL validation against malformed ports, single-label hostnames, local/internal suffixes, and DNS answers containing any non-public IP, including mixed public/private results.
- Adds regression tests for URL validation and benchmark gate behavior.

## Verification
- `python run_tests.py`: PASS.
- 27 regression tests passed.
- 8 evaluator unit tests passed.
- 6 deterministic reference cases passed.
- ZIP integrity test passed.
- `compileall` passed.
- No live provider calls were made; no API keys were read from an external account; no spend occurred.

## Known limitations
- The default Gemini model name is configurable but not verified against the user's account. Provider model catalog, quotas and billing terms may change.
- A passing offline suite does not measure general answer quality or live-provider availability.
- Reviewer is a model-based check, not independent fact verification.
- DNS rebinding is not fully prevented because DNS validation and the HTTP connection resolve separately; network-level egress controls remain necessary for hostile inputs or public-facing deployments.
- Telemetry is metadata-only but provider/model and timing data may still be operationally sensitive.
- This remains a local/Colab starter, not an autonomous agent with tools, database, persistent memory, permissions, or production observability.

## Reproducibility
Run from the extracted `agent_team_starter_v0.8` directory:
```bash
python -m pip install -r requirements.txt
python run_tests.py
python -m agent_team.cli --check-config
```
The last command checks environment-variable presence only. It does not contact providers.


## v0.8 additional verification
- Added strict benchmark CSV scoring and security-failure release rejection.
- Expanded URL validation for malformed ports, single-label/internal hostnames, and private/mixed DNS answers.
- Regression tests now include these cases.
- DNS rebinding remains a residual risk; this is not a hardened public-facing fetch service.
