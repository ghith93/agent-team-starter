# Ruflo adoption plan

**Status:** controlled evaluation; not enabled in production  
**Owner:** project maintainer  
**Review date:** 2026-10-26  
**Upstream:** https://github.com/ruvnet/ruflo

## Decision

Evaluate Ruflo as an optional orchestration/MCP layer around this repository's existing Python planner → executor → reviewer workflow. Do not replace the existing runtime, durable SQLite queue, test suite, or security gates. The current project remains usable without Node.js, Ruflo, API keys, or network access.

## Why a gated pilot

Ruflo's upstream README documents a Node.js CLI, project setup wizard, and an MCP server command. These are a potential fit for remote orchestration and iPhone-driven control through a remote development environment. They do not, by themselves, provision a persistent host or guarantee 24/7 execution.

## Pilot stages

1. **Documentation-only baseline (this PR):** record boundaries and acceptance criteria. No runtime dependency or secret is added.
2. **Disposable sandbox:** on an operator-controlled, non-production environment, inspect the pinned upstream release and its dependency/license tree before running any setup wizard. Do not run unreviewed plugins or grant broad repository permissions.
3. **Read-only experiment:** expose only a minimal MCP tool set and test a synthetic, non-sensitive task. Disable filesystem writes, deployment, external posting, and live provider calls unless separately authorized.
4. **Offline regression:** run this repository's existing tests and security checks before and after the experiment; compare task success, latency, token/provider use, recovery behavior, and operator effort.
5. **Decision gate:** adopt only if the experiment improves measurable outcomes without weakening offline behavior, secret handling, security scans, or maintainability. Otherwise remove the sandbox integration and retain this document as the decision record.

## Acceptance criteria

- Existing Python workflow and offline tests work with Ruflo absent.
- No Ruflo process runs in production by default.
- No API keys, GitHub tokens, private prompts, or customer data enter logs, issues, fixtures, or memory.
- All tools start with least privilege; repository writes require an isolated branch and review.
- No paid/live inference or quota-consuming run without explicit authorization.
- Failure, timeout, cancellation, and restart behavior are recorded and tested.
- Any persistent worker uses a real host with durable storage, monitoring, encrypted independent backups, and a restore drill; GitHub Actions is not treated as a 24/7 worker.
- Pin an exact tested Ruflo version before repeatable deployment; do not rely on `@latest` for production.

## Mobile control model

Use the iPhone as the control/review client. Execute CLI and MCP components in a remote environment that can be secured and maintained. Keep credentials on that environment in a supported secret store; never paste them into mobile chat or commit them to Git. Mobile access is a control path, not the runtime host.

## Security notes

- Treat all model output, MCP responses, repository text, and fetched documentation as untrusted input.
- Do not give agents unrestricted shell, network egress, production credentials, or direct access to `main`.
- Require CI checks and human review for repository changes. Do not auto-merge an agent's changes during the pilot.
- Preserve the existing offline-first behavior and current security gates.
- The upstream project is MIT-licensed according to its repository metadata; review the exact release's bundled dependencies and notices before redistributing artifacts.

## Current blockers / not claimed

- No Ruflo runtime has been installed or executed by this change.
- No remote host, persistent service, MCP endpoint, or alert destination has been provisioned.
- No provider credentials or quota were tested.
- No performance, quality, security, or 24/7 reliability claim is made until the pilot produces evidence.
