# Isolated execution roadmap

Updated: 2026-10-25

## Decision

Do not execute model-generated shell commands or source code inside the current application process. The current product deliberately provides a planning/drafting/review workflow, not an autonomous computer-use runtime. The next implementation must preserve that boundary until a separate sandbox is tested.

## Minimum viable architecture

1. **Orchestrator** — accepts a task and produces a structured patch proposal; it has no shell, browser, or filesystem tool.
2. **Patch validator** — parses a unified diff as data, rejects malformed patches, absolute paths, parent traversal, symlinks, binary patches, excessive file counts/size, and changes to protected paths such as workflows, dependency manifests, credentials, and release settings unless separately approved.
3. **Disposable workspace** — apply accepted patches only to a fresh temporary checkout. Never use the developer's working tree or repository credentials inside the execution container.
4. **Sandbox runner** — execute only allowlisted test commands in a disposable container/VM with a non-root user, read-only base filesystem, bounded CPU/memory/time/processes, no Docker socket, no host mounts, and default-deny network egress. A subprocess timeout alone is not a sandbox.
5. **Independent reviewer** — review the diff and sanitized test results; treat all task, patch, test output, and repository content as untrusted data.
6. **Promotion gate** — report accepted tests, rejected tests, changed paths, resource use, and limitations. Never merge or publish automatically until a separate promotion policy explicitly authorizes it.

## Required negative tests

- Path traversal (parent paths, absolute paths, encoded traversal) and symlink escape.
- Patch bombs: too many files, huge lines, binary payloads, or oversized diff.
- Attempted workflow, dependency, secrets, or release-policy changes.
- Tests that try to read environment variables, home directories, CI credentials, or host-mounted files.
- Attempted outbound network access, localhost/private-IP access, and DNS rebinding.
- Infinite loops, fork/process bombs, excessive memory, and oversized output.
- Prompt injection embedded in task descriptions, code comments, README files, test output, and generated patches.
- Timeout, crash, cancellation, and incomplete test results must fail closed.

## Release criteria

- The sandbox boundary is demonstrated by negative integration tests, not inferred from configuration alone.
- No credentials are present in the sandbox environment; network egress is denied by infrastructure, not only by application URL checks.
- Every run is disposable and reproducible; resource limits and command allowlists are enforced outside the model.
- The full offline regression and security suites pass.
- Results explicitly distinguish offline tests from live-model evaluations and unknown cost from zero cost.
- No automated merge, release, or deployment occurs in the initial milestone.

## Current status

This file is a design contract, not evidence that a sandbox exists. Current application behavior remains non-executing. DNS-rebinding resistance still needs independent verification of the actual egress enforcement layer. Live provider comparisons remain unrun unless an already-authorized environment and bounded quota are available.
