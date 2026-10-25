# Claudex Loop Trial — Agent Team Starter

Updated: 2026-10-25
Status: isolated evaluation branch; no CLI has been installed or executed from this GitHub session.

## Decision

Prioritize a controlled trial of [Claudex Loop](https://github.com/chaseai-yt/claudex-loop) before adopting other new agent-orchestration tools. The trial must demonstrate a measurable quality improvement over the existing workflow. Do not add it as a runtime dependency of Agent Team Starter.

Upstream describes four phases: recon/research, requirements and plan hardening, cross-provider plan review, then a build followed by independent inspection. It also provides Claudex Route for lightweight model/task routing. The full loop requires Python 3.10+, both Claude Code and Codex CLIs installed and authenticated, and compatible CLI versions. The upstream runner has no pip runtime dependencies and does not call a hosted model API directly, but CLI account usage may still consume subscription quota or incur costs depending on account configuration.

## Safety and cost boundaries

- Work only on this branch and disposable fixtures for the initial trial.
- Do not modify `main`, merge, publish, message customers, alter external accounts, or deploy.
- Do not introduce a new paid API, subscription, or unapproved quota usage.
- Do not expose or commit credentials, CLI diagnostics, private source, or model prompts containing secrets.
- Keep reviewer phases read-only. Do not weaken upstream permission controls to work around incompatible CLI versions.
- Never treat a successful process exit, empty output, or model assertion as proof of correctness.
- Run deterministic proof commands independently in the host environment; a model's inability to run a proof command must not be bypassed by widening permissions.
- Stop if either CLI is missing, unauthenticated, incompatible, or if cost cannot be bounded without user approval.

## Trial sequence

### Gate 0 — Inspect upstream

- [ ] Verify current upstream license and third-party notices.
- [ ] Read the skill manifests, runner implementation, runtime reference, validation record, and relevant tests.
- [ ] Check for shell injection risks, unsafe path handling, prompt injection boundaries, logging of secrets, timeout handling, and subprocess permissions.
- [ ] Confirm exact CLI versions and supported flags without changing global configuration.
- [ ] Record the current baseline commit and branch status.

### Gate 1 — Offline compatibility and safety

In a disposable checkout of the upstream repository, run only the documented local checks:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
git diff --check
```

These tests use fake CLI processes and should not consume model quota. Record actual command output, versions, exit codes, and any failures. Do not claim cross-platform success from a single local run.

### Gate 2 — No-cost capability check

- [ ] Check `python --version`, `codex --version`, `codex login status`, `claude --version`, and `claude auth status`.
- [ ] Verify that both CLI accounts are already available and that a disposable test can run within existing included quota.
- [ ] Do not call either model until the quota/cost status is clear.
- [ ] If a free, authorized test cannot be established, stop at offline validation and report the blocker.

### Gate 3 — Controlled live fixture (only if Gate 2 passes)

Use a tiny, synthetic Python fixture with no credentials or production data. Seed one obvious defect (for example, destructive operation before backup/read), plus at least one correct control case to measure false positives.

Compare:
1. Existing single-model workflow.
2. Claudex Loop plan review + implementation + independent inspection.

Use the same tasks, requirements, and acceptance tests for both approaches. Keep the number of rounds bounded (plan review <= 3, build fixes <= 1, inspection <= 1 reinspection). Never use production files or real account integrations for this comparison.

### Gate 4 — Score results

Record a table for each task containing:
- Defects planted and defects correctly identified (recall).
- False-positive findings on correct controls.
- Acceptance checks passed/failed, independently executed.
- Material findings missed by the final reviewer.
- Wall-clock time and token/quota usage when observable.
- CLI/provider/model identity and version, with unknown values explicitly marked unknown.
- Permission failures, interruptions, and unresolved limitations.

Do not use the number of findings as a quality score. Do not claim the loop is better unless results on matched tasks support the claim.

## Adoption criteria

Adopt the workflow only if all are true:
- Offline tests and static validation pass.
- No unresolved high-severity security or data-loss issue exists.
- Independent proof checks pass.
- It detects at least one material defect the baseline misses, without a disproportionate false-positive increase, across more than one matched fixture.
- Cost and time are acceptable and no new paid service is required.
- Integration remains optional and does not add a required dependency to the core runtime.

Otherwise, keep only the evaluation notes and do not integrate the runner.

## Trial results (2026-10-25)

### Gate 0 — Source review: partial pass

- Pinned upstream commit: `53cddc42e39346fb8c6d5d612281a3b1add14e66`.
- License: MIT. Development test dependency: PyYAML only.
- **Attribution-path caveat:** the root LICENSE says adapted `CONTEXT-FORMAT.md` / `ADR-FORMAT.md` material is covered by each skill's `THIRD-PARTY-NOTICES.md`. At the pinned commit, notices are present under `legacy/grill-me-codex/` and `legacy/grill-with-docs-codex/`, but not beside the active `skills/claudex-loop/` files. Root LICENSE attribution exists, yet the notice-path wording/mapping should be clarified upstream before copying or adopting those files. This remains an open Gate 0 item.
- Focused source review observed read-only reviewer modes, explicit MCP disabling for review, hook disabling in the Claude build invocation, process timeouts, plan snapshot/approval binding, and fresh-session inspection requirements.
- This is a focused review, not a complete independent security audit. Do not run against production repositories or sensitive data until a broader review is completed.

### Gate 1 — Offline validation: PASS

Run: https://github.com/ghith93/agent-team-starter/actions/runs/40225358182

- `python scripts/validate.py`: passed (`Skill metadata, references and manifests passed.`).
- `python -m unittest discover -s tests -v`: **37 tests passed** in 6.106 seconds, using fake CLI executables and disposable repositories; no live model calls were made.
- `git diff --check`: passed.
- Only the declared `PyYAML>=6.0,<7` development dependency was installed in the ephemeral runner.

### Gate 2 — Existing CLI authorization and bounded cost: BLOCKED

- No live Claude Code or Codex CLI call was made.
- The ephemeral CI runner does not have the user's pre-existing authenticated CLI sessions. Installing CLIs would not create authorization, and adding credentials or a paid API key is outside this no-new-cost trial.
- No credentials were requested or stored. Live evaluation remains blocked until both CLIs are already authorized in a controlled environment and quota/cost is known.

### Current decision

**Keep Claudex Loop as the priority candidate for evaluation, not as an adopted dependency.** Offline implementation contracts and metadata validation pass, but the tests use fake CLIs and therefore do not establish real cross-model quality, comparative defect recall, or acceptable live cost. Do not claim a quality improvement until the matched-fixture live evaluation in Gate 3 is completed.

- The `main` baseline when this trial branch was created was `e0927ed62e9b739f16467ba156fd0941a513625a`; a separate tooling-only PR has since been merged. All Claudex Loop trial changes remain isolated to `experiment/claudex-loop-trial` and draft PR #22. Re-review the diff against the latest `main` before any future promotion.
- Next step: perform Gate 2 in an already authenticated environment without exposing secrets; if this cannot be done without new spend, stop at the offline result and do not integrate the tool.
