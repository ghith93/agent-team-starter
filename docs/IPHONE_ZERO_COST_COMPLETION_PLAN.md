# Zero-cost completion plan (iPhone-only)

Last reviewed: 2026-10-26

## Goal and boundary

Use only an iPhone, the existing public GitHub repository, and free features. Do not buy hosting, subscribe to services, create paid resources, trigger paid model calls, or store credentials in the repository. This plan separates repository tasks that can be completed now from tasks that require an actual host, account configuration, or live delivery test.

## Work that can be completed from the iPhone now

- Review CI runs and their artifacts in GitHub Actions.
- Review repository files and make changes on a feature branch, then use a pull request.
- Keep deterministic offline tests and security scans as required checks.
- Review and document GitHub security settings, branch protection, and license decision.
- Prepare backup/restore, health-check, deployment, and rollback procedures.
- Add or improve offline tests and fail-closed gates without provider calls.
- Keep all provider/live workflows opt-in and stop when a provider may charge or consume quota.

## Required GitHub UI checks (no paid feature should be enabled without confirming availability)

Open the repository in Safari, sign in, and use these routes:

1. **Security features:** https://github.com/ghith93/agent-team-starter/settings/security_analysis
   - Find the Secret scanning section and record whether it is available and enabled.
   - Find Push protection and record whether it is available and enabled.
   - If unavailable on the current plan/account, leave it documented as unavailable; do not infer status from CI scanners.
2. **Rulesets:** https://github.com/ghith93/agent-team-starter/settings/rules
   - Open the active `main` ruleset.
   - Review required checks, required approvals, stale-branch/strict status, and bypass actors.
   - Do not remove bypass access or change required checks without confirming that the owner can still recover a broken branch.
   - Current known concern: repository-role bypass is set to `always`, required approvals are zero, and strict freshness is off. Track a deliberate decision; do not silently change policy.
3. **Actions:** https://github.com/ghith93/agent-team-starter/actions
   - Open the latest run for `main` and confirm all required checks have a completed success status.
   - Download and review report artifacts where available. A skipped, cancelled, or still-running security job is not a pass.
4. **License:** https://github.com/ghith93/agent-team-starter/blob/main/LICENSE_PENDING.md
   - Do not select a license until ownership and third-party code/content rights are reviewed. Public visibility alone does not grant permission to reuse the project.

Record only the setting names and their status in an issue or project note. Never include tokens, cookies, webhook URLs, recovery codes, or other secrets.

## Free operational acceptance tests (must run on a real target before production)

A checklist or passing CI is not execution evidence. Once a persistent Linux host and an alert/backup destination are actually available, complete these tests:

- [ ] Run `bash deploy/systemd/preflight-deploy.sh` and retain its redacted output.
- [ ] On the target host, run preflight with `--host-checks`; review systemd unit verification.
- [ ] Verify the worker runs under an unprivileged dedicated account and cannot write to source or configuration.
- [ ] Start a harmless test task and verify its durable result in SQLite.
- [ ] Restart the worker and reboot the host; verify queued work is recovered without duplicate side effects.
- [ ] Configure a trusted HTTPS alert destination and confirm a test alert arrives at its intended recipient.
- [ ] Create an encrypted backup in a separate account/provider boundary.
- [ ] Restore that off-host backup into a new location; validate integrity and run tests before any cutover.
- [ ] Test egress policy against loopback, private, link-local, reserved, and cloud-metadata targets, including redirects and DNS rebinding. Application URL validation alone is insufficient.
- [ ] Record timestamps, commit SHA, results, and failures. Do not include secret values.

## What cannot honestly be completed with an iPhone and repository access alone

- Provision or administer a persistent Linux host when no host/account is available.
- Prove 24/7 worker operation or reboot recovery without a real target runtime.
- Prove external alert delivery without a real destination.
- Prove off-host disaster recovery without a separate storage boundary and a restore drill.
- Enforce network-level egress/DNS-rebinding protections from repository code alone.
- Verify or change account/repository security settings unless GitHub exposes those settings to the signed-in owner and the UI action is performed.
- Conduct authenticated provider evaluation without an explicitly authorized provider/session and a known no-cost quota.

## No-cost operating rule

Prefer GitHub Actions for finite CI checks, not as a substitute for a persistent worker. Keep provider calls disabled by default. Do not put private task data or secrets into the public repository, SQLite task payloads, CI logs, or artifacts. Never report a checklist as complete until its evidence exists.

## Newly researched hosting path — Hostless free allowance (2026-10-26)

Official references:
- Platform overview and free allowance: https://docs.hostless.cloud/overview
- Current resource limits: https://docs.hostless.cloud/plans/limits
- Product entry point: https://web.hostless.cloud/

The official overview currently advertises an always-on app and worker with no credit card, within a shared account allowance of 0.5 vCPU, 1 GiB RAM, and 512 MiB managed-database storage. It supports Git-based deployment. This is a candidate to investigate, not proof of suitability or a guarantee of uninterrupted service.

### Critical compatibility and cost safeguards

- **Do not deploy the current SQLite-backed durable queue as production state on an assumed-persistent local filesystem.** The free allowance describes managed database storage, not a guarantee that application-local SQLite files survive redeploys or host replacement.
- Before production, either (A) migrate queue, leases, retries, idempotency, and recovery semantics to a managed database such as PostgreSQL and add integration/concurrency/restart tests, or (B) obtain and verify explicit persistent-volume guarantees for the chosen resource. Do not silently swap databases or weaken queue guarantees.
- The free CPU, memory, and database allowance is shared across account resources. The provider documents usage-based charges above the allowance. Because the operator cannot pay, **do not attach a payment card, create oversized resources, or enable paid capacity**. Confirm in the account UI that the intended resource fits the no-card free allowance before creation. A spending limit should not be treated as a guaranteed invoice cap.
- Hostless is a third-party provider and a new dependency. Review its terms, privacy, security, account recovery, and operational status before storing any task content. Begin with synthetic, non-sensitive tasks only.
- Connecting the repository and creating a hosted resource requires the account owner to sign in and authorize GitHub access. Repository access alone does not grant this account-level permission, so no account/resource has been created by this plan.

### Execution sequence with no laptop and no budget

1. Keep the currently passing offline CI as the safe baseline; use GitHub's mobile web UI and feature branches for changes.
2. In the provider's UI, inspect the free entitlement and no-card path only; do not create a resource if the screen implies paid capacity or asks for a payment method.
3. Implement and review the persistence migration on a feature branch before connecting any production queue to the host. Keep SQLite tests and add backend parity, concurrency, retry, idempotency, migration, and restore tests.
4. Deploy a disposable synthetic-task smoke test first. Confirm logs, restart behavior, and resource consumption. Do not send secrets, private prompts, or customer data.
5. Only call the service production-ready after queue recovery and an independent backup/restore test pass. If the free allowance is insufficient, remain in offline/test mode rather than incur costs.

### Honest interim capability

Until a free host and compatible durable storage are actually provisioned and tested, the repository can still run finite CI tests and scheduled, bounded maintenance checks on GitHub Actions. These are not a continuously running worker and must not be represented as 24/7 runtime.



## Decision update — replace Hostless for this project

Decision: do not continue using Hostless as the project's operational target. The Hostless diagnostic workflow is being retired because its aggregate runtime-log endpoint repeatedly returns HTTP 500. For occasional, manually initiated work, use GitHub Actions workflow `.github/workflows/on-demand-agent-task.yml` and the [on-demand runbook](ON_DEMAND_GITHUB_ACTIONS_RUNBOOK.md). It needs no permanent Linux host and is not a 24/7 worker. Live OpenRouter calls are gated by an explicit input and can consume provider quota; no live call is performed by CI.

This retires the repository integration only. Repository access cannot cancel an external Hostless subscription, delete a Hostless account/resource, or stop an external deployment. If a resource exists, the account owner must stop/delete it in the Hostless dashboard and separately verify billing and GitHub access. The local SQLite durable queue remains a separate optional mode and is not persisted across GitHub-hosted runner jobs.
