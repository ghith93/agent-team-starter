# Persistent Agent Memory Evaluation

**Assessment date:** 2026-10-23  
**Status:** Candidate selected for isolated proof-of-concept; not installed or production-approved.

## Decision

Evaluate [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) first for internal engineering continuity and cross-agent handoffs. Evaluate [mem0ai/mem0](https://github.com/mem0ai/mem0) separately only if/when the product needs application-level user/session memory.

Do not treat either system as a source of trusted instructions. Retrieved memory is untrusted data and must never override system, developer, repository, or operator policy.

## Fit

### ai-memory — first prototype candidate

The project describes a git-backed Markdown wiki as its source of truth, a derived searchable index, lifecycle capture, explicit handoffs, multi-agent support, and a default workflow that does not require LLM calls. This makes it promising for preserving repository decisions, failed approaches, test results, and next steps across development sessions.

It is **not yet proven compatible** with this project's runtime, and should not be described as integrated until a local proof-of-concept succeeds.

### Mem0 — separate application-memory candidate

Mem0 targets persistent memory in AI applications and may fit future assistant workflows involving user/session facts. That is a different problem from developer handoff memory. It should be assessed separately for provider dependencies, deployment cost, tenant isolation, deletion, and retrieval quality.

## Proof-of-concept plan

1. Install a pinned release in a disposable, isolated development environment; verify release checksum and inspect the installation script before execution.
2. Use synthetic data only. Never ingest API keys, tokens, customer PII, private messages, or live business records.
3. Create a test project with three synthetic facts, one failed approach, and one unresolved task.
4. End the first session and restart the process. Verify that the second session retrieves the facts and unresolved task without manually re-entering them.
5. Test handoff from one supported agent harness to another only if both harnesses are available in the test environment.
6. Test isolation by creating a second project with a conflicting synthetic fact; retrieval must not leak across project boundaries.
7. Test prompt injection: store a synthetic memory that says to ignore policy and reveal secrets. Verify that the agent treats it as data and refuses to follow it.
8. Inspect provenance, audit events, backup/export, recovery, retention, and deletion semantics.
9. Record installation reproducibility, memory recall accuracy, false retrievals, latency/token overhead, and operator effort.
10. Make a documented go/no-go decision before any production use.

## Security gates

- Local-only or loopback binding for the first test.
- Authentication and HTTPS before any remote/shared server exposure.
- Separate stores/servers where strict project or user isolation is required.
- Least-privilege file and process permissions; no secrets in repository or memory.
- No automatic writes based on untrusted retrieved content without validation and provenance.
- Memory is context, not authority. Policy hierarchy remains unchanged.
- Verify exact license and release artifact for the pinned version.
- Keep production rollout out of scope until the source restoration and CI blockers for this repository are resolved.

## Acceptance criteria

- Reproducible clean setup with pinned version and verified checksum.
- Recall survives process restart.
- Project isolation and prompt-injection tests pass.
- Export/backup and recovery behavior is documented.
- No secrets or customer data used.
- Test evidence and a go/no-go decision are attached to the tracking issue.

## Release and installer review (2026-10-23)

The public release page currently identifies **v3.2.1** as latest (published 2026-10-22). This is a candidate pin for the prototype, not a claim that the artifact has been downloaded or locally verified.

Published SHA-256 values for the release archives include:

- Linux x86_64: `95f36baa4c239a10fc4082f737b6a401c49e4cadb4af0bd59a15786be5550661`
- Linux aarch64: `677f32654d17a73551f51248329fdc79f6219a915ed3082ec0e15af2be5085ea`
- macOS Apple Silicon: `efbf528f7fe9c62502204ebb4e51a724623d04bb7f0ff694a1ca0491f9501619`
- macOS Intel: `643ba1bd2c167d48010f844298c8ff2258fb268cd0c6cfab60c79950e0fc812f`

Source: [v3.2.1 release and published checksums](https://github.com/akitaonrails/ai-memory/releases/tag/v3.2.1). The checksum values above are transcribed from the release page; they have **not** been compared against downloaded bytes in this environment.

### Installer review findings

The pinned `install.sh` source was inspected at tag `v3.2.1`. It:

- downloads the OS/architecture-specific archive and matching SHA-256 sidecar, rejects a missing/malformed/mismatched checksum, and checks archive members before unpacking;
- installs the binary under `~/.local/lib/ai-memory` and creates a link under `~/.local/bin`, without requiring root;
- does **not** itself run `ai-memory setup`.

Important: `ai-memory setup` is a separate, consequential step. Documentation says it may start a per-user service and wire detected agent harnesses by applying MCP/hooks/skills configuration. Therefore, the prototype must not run the broad default setup on a working user profile. Use a disposable OS account/container and an explicit minimal plan, or test only read-only CLI commands until the side effects are understood.

This source review is not a substitute for downloading the exact archive, verifying its checksum locally, and executing the binary in a disposable environment.

## Current blockers / honest status

- The repository's full source archive is not yet restored to GitHub.
- The existing local test suite passed offline in the prior validation, but GitHub Actions/CI evidence has not been confirmed.
- No memory package has been installed or deployed by this evaluation.
