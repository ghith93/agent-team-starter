# Ruflo 3.63.0 static dependency audit findings

**Reviewed:** 2026-10-26  
**Source:** GitHub Actions run https://github.com/ghith93/agent-team-starter/actions/runs/40247132976  
**Artifact:** `ruflo-package-audit-3.63.0`  
**Scope:** npm registry metadata, package manifests, archive file lists, CLI entrypoint and postinstall script inspection, and `npm audit` against a lockfile-only dependency resolution. No package code was executed or installed.

## Decision

**Do not install Ruflo 3.63.0 into the main project or a credential-bearing environment yet.** Keep it optional and continue with a disposable, unprivileged sandbox only after dependency findings have been reconciled.

## Findings

- `ruflo@3.63.0` declares MIT and Node.js `>=20.0.0`, with a direct dependency on `@claude-flow/cli@3.63.0`.
- The direct CLI package declares a `postinstall` script at `scripts/postinstall.cjs`.
- Static review of that script shows it searches for reachable `agentdb` installations and may copy directories under `dist/src` into sibling paths and edit `agentdb/package.json` exports. This appears intended as a compatibility patch, but it is a package-install-time filesystem mutation and should be tested only in a disposable environment.
- The lockfile-only dependency resolution returned **37 npm audit findings: 1 critical, 14 high, 22 moderate**. These counts describe the resolved dependency tree and advisory database, not proof that all affected code paths are loaded or reachable in every installation.
- The critical advisory is associated with nested `protobufjs@6.11.6` under `onnx-proto`, and npm audit lists an arbitrary-code-execution advisory: https://github.com/advisories/GHSA-xq3m-2v4x-88gg. Treat this as a release-blocking dependency concern until the exact tree is reconciled and a clean audit is obtained.
- Other high-severity advisories include transitive `zod`, `agentdb`, `agentic-flow`, `onnxruntime-web`, and `sharp` packages in the resolved tree. The complete machine-readable output is in the linked artifact.
- npm audit suggested `@claude-flow/cli@3.32.29` as a fix path while auditing `3.63.0`. Since that version is numerically lower than the inspected version and the suggested change is marked as a major change, do **not** blindly apply the suggestion; validate release provenance and the dependency tree first.

## Required next checks

1. Compare the package tarball and manifest against the official upstream release/tag and verify npm dist integrity.
2. Reconcile the npm audit tree, including optional dependencies, duplicate package versions, and advisory ranges; confirm the critical advisory is eliminated in a tested, supported dependency set.
3. Review the full CLI entrypoint, postinstall behavior, and relevant MCP tool handlers.
4. If proceeding, run only in an ephemeral container/VM with no production secrets, no write access to the main repository, restricted network egress, and a synthetic task.
5. Keep the existing Python planner/executor/reviewer and offline tests as the production baseline until the isolated pilot passes acceptance tests.

## Limits

A successful GitHub Actions workflow means the inspection completed and the evidence was uploaded. It does not certify Ruflo as safe, and it does not mean Ruflo was installed, started, connected to MCP, or deployed 24/7.
