# External security scanning in GitHub Actions

This repository includes `.github/workflows/security.yml`. Once the project is pushed to a GitHub repository with Actions enabled, it runs on pushes, pull requests, manual dispatch, and weekly schedule.

## Checks

- `python run_tests.py`: offline regression, evaluator, reference arithmetic, prompt-injection case suite, heuristic source scan, and archive-audit tests.
- `compileall`: Python syntax/bytecode compilation.
- Bandit: Python security lint.
- pip-audit: checks declared Python dependencies against the vulnerability data available to the runner.
- Semgrep: Python and secrets rules; findings fail the scan step.
- detect-secrets: repository working-tree secret scan, followed by an explicit gate that fails when candidate findings exist.
- Gitleaks Action: secret scanning over repository history and working tree.

## Where results go

The workflow uploads `offline-test-reports` and `python-security-reports` artifacts from each run. Scanner package versions are recorded in `scanner-versions.txt`. Gitleaks findings are reported by the action in the workflow log/security interface.

## Important operating notes

1. **This file does not mean the scanners have already run.** They run only after the repository is pushed to GitHub and a workflow run completes. This local environment could not resolve external hosts during the previous install attempt.
2. Scanner packages are installed from the package index at run time, so the resolved scanner versions can change. The workflow records installed versions in `scanner-versions.txt`; pin scanner package versions as a separate hardening step when a reviewed, compatible set has been selected. Third-party GitHub Actions are pinned to reviewed full commit SHAs.
3. A scanner finding or scanner execution error fails the `python-security` job. Review reports before suppressing any finding; do not add broad ignore rules just to make CI green.
4. `pip-audit` covers only dependencies represented by `requirements.txt` (and their resolved dependency graph), not arbitrary packages already present in a developer's global environment.
5. Gitleaks uses `gitleaks/gitleaks-action@v3` and the repository-scoped `GITHUB_TOKEN`; PR comments are disabled and workflow permissions are read-only. For repositories owned by a GitHub organization, configure the encrypted `GITLEAKS_LICENSE` secret if required by the action. Personal-account repositories generally do not require that license. Do not add write permissions or expose secrets to untrusted pull-request code. The workflows pin third-party actions to full commit SHAs checked against upstream GitHub tag refs during review. When updating an action, verify the new tag/commit and update the workflow-contract tests in the same change.
6. Passing automated scans does not certify the application as secure. Human review, threat modeling, live-provider tests, network egress controls, SSRF/DNS-rebinding tests, and prompt-injection evaluations against real models remain separate tasks.

## How to run

1. Extract the release ZIP or copy its contents into a Git repository.
2. Push the repository to GitHub.
3. Open **Actions → Tests and security scans** and inspect the first run.
4. Download the two report artifacts. Keep the run URL and artifact reports with the release evidence.

## Verified restoration candidate run

For the candidate at commit `f661e539e125f0133356112df3a68ad1904e0068` proposed in PR #4, both current GitHub Actions workflows completed successfully:

- [Tests and security scans run](https://github.com/ghith93/agent-team-starter/actions/runs/39982891091): offline regression/evaluator job, Gitleaks secret scan, and Python SAST/secrets/dependency-audit job all passed.
- [Offline regression checks run](https://github.com/ghith93/agent-team-starter/actions/runs/39982891206): passed.
- The tests include regressions proving that error responses echoing the exact Gemini or OpenRouter API key are redacted. The Gitleaks configuration allowlists only two synthetic test-fixture strings, scoped to `tests/test_router.py`; it does not disable scanning for real credentials.
- An earlier successful security run's reports remain available from [run 39980376092](https://github.com/ghith93/agent-team-starter/actions/runs/39980376092). Its reported results included zero Bandit findings, zero Semgrep findings, zero detect-secrets files with findings, and no known vulnerabilities reported for the five installed runtime dependencies checked by pip-audit.

These are results for the specific tested candidate commit, not a permanent guarantee for later commits. The project is still under review in a draft PR; this document does not authorize a merge or production deployment.
