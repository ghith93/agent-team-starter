# Graphify Code-Only Pilot Results — 2026-10-25

## Status

**First pilot succeeded** on an ephemeral GitHub-hosted runner using Graphify `0.9.95`. The run was code-only, `GRAPHIFY_BACKEND=none`, and did not use a model API. The target was a disposable copy of tracked repository files; no generated graph was committed to the source tree.

- Workflow run: https://github.com/ghith93/agent-team-starter/actions/runs/40225343536
- Artifact (temporary; 3-day retention): https://github.com/ghith93/agent-team-starter/actions/runs/40225343536/artifacts/12611001977
- Graphify release: `0.9.95`
- Source files: 41 classified code files; 6 additional files skipped as unsupported/unclassified
- Graph: 492 nodes, 806 edges, 24 communities
- Edge provenance: 97% extracted, 3% inferred, 0% ambiguous; 23 inferred edges (reported average confidence 0.89)
- Import cycles: none detected by this run
- Model token usage reported by Graphify: 0 input / 0 output

## Useful initial observations

- High-connectivity nodes included `run_team()`, `FreeFirstRouter`, `ProviderError`, `audit_archive()`, `_validate_public_url()`, and `fetch_public_page()`.
- Graphify connected test nodes with implementation nodes, which may help identify cross-module review paths.
- It reported no import cycles, which is useful as a screening signal but is not proof that no architectural cycles exist.

## Limitations and follow-up

- `cluster-only --no-label` deliberately avoids model-generated community names, so the report labels communities generically (`Community 0`, etc.). This preserves the zero-API constraint but reduces readability.
- The initial report included GitHub workflow YAML as code-like nodes; this created several low-cohesion communities dominated by workflow fields. The next pilot should exclude `.github/**` in the disposable copy and compare whether the application/test graph becomes more useful.
- Treat inferred edges as hypotheses. In particular, relationships between `RouterTests`, `FreeFirstRouter`, `ProviderError`, and `FakeRouter` need source-level confirmation before being used for design decisions.
- Graphify is not integrated into runtime, no assistant configuration was changed, and regular adoption is not yet justified. Keep it optional unless a second, cleaner graph reveals actionable relationships that existing docs/tests miss.

## Decision

**Keep Graphify as an optional architecture-review aid, not a required dependency.** The first run proves that the pinned tool installs and produces a local graph without model calls. A second filtered run is required before judging its practical value.

## Filtered rerun after merging the pilot workflow

- Workflow run: https://github.com/ghith93/agent-team-starter/actions/runs/40225936210
- The workflow excluded `.github/**` from the disposable copy and kept `GRAPHIFY_BACKEND=none`.
- Result: 34 code files; 284 nodes, 588 edges, 12 communities.
- Compared with the initial run (41 classified code files; 492 nodes, 806 edges, 24 communities), the filtered graph is substantially smaller. The first-run counts included workflow YAML and related configuration noise.
- This is evidence the filter reduces graph size, not yet proof of better findings. No import cycles or model/API use should be inferred beyond what the run itself reported. Keep Graphify optional until a human review confirms that the communities reveal actionable code relationships.
