---
name: codebase-archaeology
description: Inspect an unfamiliar codebase efficiently before changing it. Use for repository audits, dependency mapping, call-path tracing, regression diagnosis, and finding the smallest safe implementation point.
---

# Codebase Archaeology

1. Establish repository root, current branch/status, package manifests, entry points, tests, CI, and release artifacts.
2. Read the target implementation and its callers/callees before editing. Search for tests, configs, duplicated implementations, and documented contracts.
3. Trace one representative path end-to-end; write down inputs, trust boundaries, side effects, errors, and outputs.
4. Prefer structural search (AST-aware) for refactors and exact text search for literal names. Never mass-rewrite without a disposable branch and a diff review.
5. Turn every confirmed defect into a failing regression test before fixing it.
6. Make the smallest change consistent with existing architecture. Do not add a framework if a small standard-library change solves the problem.
7. Run targeted tests, then the full test suite, static checks if available, and packaging checks.
8. Report evidence, files changed, commands run, test counts, unresolved risks, and anything not tested. Do not infer runtime quality from code inspection alone.
