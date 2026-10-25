# TinyFish fallback and cost-control policy

## Current decision

Do not top up TinyFish just to inspect repositories or run repeatable GitHub workflows. Prefer deterministic, auditable, free or already-connected paths first.

- GitHub repository reads and writes: use the connected GitHub integration.
- Repeatable CI, static package audits, tests, and security checks: use GitHub Actions.
- Public web search and page extraction: use TinyFish Search/Fetch when available at the published free rate, or the connected Firecrawl search/scrape tools when suitable.
- Goal-driven browser automation and hosted browser sessions: treat TinyFish Agent/Browser as metered. Do not invoke them when the wallet is negative; use only when the task genuinely requires browser interaction and the expected benefit justifies a top-up.
- Do not assume an alternate provider is free merely because its code is open source. Local/self-hosted browser automation still needs compute, a reachable runtime, and possibly model/API credentials.

## Ruflo audit path

The workflow at `.github/workflows/ruflo-package-audit.yml` performs a static audit in GitHub Actions. It:
- resolves a concrete npm version;
- reads registry metadata;
- downloads the archive with lifecycle scripts disabled;
- extracts the package manifest and file list without installing or executing Ruflo;
- uploads a short-lived evidence artifact.

It runs manually or when that workflow file changes on `main`. It has repository read-only permissions. Review the artifact before any isolated runtime experiment.

## Escalation gates

1. Use free retrieval or existing GitHub APIs for read-only tasks.
2. Use GitHub Actions for repeatable checks.
3. Use a browser agent only if a required UI interaction cannot be performed via an API or workflow.
4. Before any paid run, check the current wallet and meter rates. Never enable automatic reload without explicit user approval.
5. Never claim that a persistent runtime, MCP endpoint, or 24/7 service exists until it has been provisioned and tested.

## Evidence

The package audit is recorded in GitHub Actions run 40247003834. It inspected `ruflo@3.63.0`, reported Node.js `>=20.0.0`, MIT license, and a direct dependency on `@claude-flow/cli`. This is metadata review only, not a security certification and not evidence that Ruflo was installed or executed.
