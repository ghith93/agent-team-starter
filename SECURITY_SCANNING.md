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
2. Scanner packages are installed from the package index at run time, so the resolved versions can change. The run records installed versions; for a high-assurance pipeline, pin scanner versions and action references to reviewed commit SHAs after validating the chosen versions.
3. A scanner finding or scanner execution error fails the `python-security` job. Review reports before suppressing any finding; do not add broad ignore rules just to make CI green.
4. `pip-audit` covers only dependencies represented by `requirements.txt` (and their resolved dependency graph), not arbitrary packages already present in a developer's global environment.
5. Gitleaks uses `gitleaks/gitleaks-action@v3` and the repository-scoped `GITHUB_TOKEN`; PR comments are disabled and workflow permissions are read-only. For repositories owned by a GitHub organization, configure the encrypted `GITLEAKS_LICENSE` secret if required by the action. Personal-account repositories generally do not require that license. Do not add write permissions or expose secrets to untrusted pull-request code. The workflow uses current major action tags rather than immutable commit-SHA pins; high-assurance deployments should review and pin each action to a verified full commit SHA.
6. Passing automated scans does not certify the application as secure. Human review, threat modeling, live-provider tests, network egress controls, SSRF/DNS-rebinding tests, and prompt-injection evaluations against real models remain separate tasks.

## How to run

1. Extract the release ZIP or copy its contents into a Git repository.
2. Push the repository to GitHub.
3. Open **Actions → Tests and security scans** and inspect the first run.
4. Download the two report artifacts. Keep the run URL and artifact reports with the release evidence.

## Verified restoration candidate run

For the restored candidate currently proposed in PR #4, GitHub Actions has completed successfully:

- [Tests and security scans run](https://github.com/ghith93/agent-team-starter/actions/runs/39980384727): offline regression/evaluator job, Gitleaks secret scan, and Python SAST/secrets/dependency-audit job all passed.
- [Offline regression checks run](https://github.com/ghith93/agent-team-starter/actions/runs/39980384739): passed.
- The earlier successful security run's reports are available from [run 39980376092](https://github.com/ghith93/agent-team-starter/actions/runs/39980376092). Reported results included zero Bandit findings, zero Semgrep findings, zero detect-secrets files with findings, and no known vulnerabilities reported for the five installed runtime dependencies checked by pip-audit.

These are results for the tested candidate commit, not a permanent guarantee for later commits. The project is still under review in a draft PR; this document does not authorize a merge or production deployment.
