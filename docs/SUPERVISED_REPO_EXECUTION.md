# Supervised repository patch evaluation

\`agent_team.repo_executor.evaluate_patch\` provides a bounded local verification step for a proposed unified diff.

## Safety model

- The original checkout is never modified. Files are copied to a disposable temporary directory, the patch is applied there, and the directory is deleted afterward.
- Model-supplied shell commands are never executed. Callers can select only \`project-tests\`, \`pytest\`, \`unittest\`, or \`compile\`, each mapped to a fixed argument array.
- The default validation is \`compile\`; this avoids executing newly generated project code by default.
- Patches are size-limited; binary patches, traversal, secret-like paths, symlink/submodule/rename patches, and \`.github/workflows/**\` changes are rejected.
- Workspaces containing symlinks are rejected rather than dereferenced. The workspace copy has file-count and byte-size limits and excludes Git metadata, virtual environments, common caches, and common secret/configuration paths.
- Compile-only validation uses a fixed command in a restricted subprocess. Project-test, pytest, and unittest validations run in a Docker container with `--network none`, a read-only container root, dropped Linux capabilities, `no-new-privileges`, PID/memory/CPU limits, and only the disposable candidate workspace mounted writable. No provider API key or host environment secrets are passed into the container.
- The sandbox image is built from the original workspace's sanitized `requirements.txt` before candidate code runs. Dependency image build/install still requires network access and trusts the original dependency declarations; unsupported requirements syntax fails closed. If Docker is unavailable, test validations fail instead of falling back to host execution.
- Container isolation is defense in depth, not a formal security proof; it still relies on the host kernel and Docker daemon. Review changes to tests and dependencies, and never put confidential data into the provider task.

## Example

\`\`\`python
from agent_team.repo_executor import evaluate_patch

result = evaluate_patch(
    ".",
    proposed_unified_diff,
    validations=("compile",),
    timeout_seconds=120,
)
print(result.to_dict())
\`\`\`

A passing result means only that selected commands passed in the temporary copy. It is not proof of correctness or security and does not apply, commit, push, or merge the patch. Human review is required before promoting changes.


## Manual free-model proposal workflow

The \`.github/workflows/repository-patch-proposal.yml\` workflow can be dispatched manually from GitHub Actions. It requires \`authorize_provider_calls=true\`; leaving the input false makes no provider call. When authorized, it explicitly disables Gemini and permits only the OpenRouter \`openrouter/free\` alias. A provider quota may still be consumed.

The workflow sends a bounded selection of repository text to the model, excluding \`.github/**\`, common secret/configuration paths, binary files, and credential-like lines. It asks for a unified diff and rejects unsafe patch paths. The default is compile-only validation in a disposable copy. The manual workflow also offers `project-tests` and `unittest`, but these modes require the separate `authorize_test_execution=true` checkbox and run inside the network-disabled Docker sandbox. If that checkbox is absent, the workflow exits before any provider call. It produces a one-day artifact containing the proposed patch and validation result.

This is a proposal-and-compile-check workflow, not a merge bot. It does not change the checkout, commit, push, create a PR, or run project tests. Review the patch manually before applying it. Do not submit secrets or confidential task data. Repository text sent to the model is disclosed to the configured provider.


## Agent-team review loop

The task workflow runs four bounded stages: planner, executor, independent reviewer, and final reviser. The reviser receives the original task, plan, draft, and review findings and produces the final answer rather than returning the unreviewed draft. This improves feedback integration but adds one provider request per task and remains model-based; it is not a substitute for project tests, source verification, or human review. All provider calls remain behind the existing explicit workflow authorization and free-model-only configuration.


## Validated patch publication as a pull request

The manual patch workflow has a separate `authorize_open_pr` checkbox, disabled by default. A PR is attempted only when the provider call was authorized, patch validation completed successfully, and PR publication was separately authorized. The publication job receives a short-lived workflow token with `contents: write` and `pull-requests: write`; the model-generation and candidate-test job has read-only repository permissions and no persisted checkout credentials.

The publication job downloads the validation artifact, independently checks its status, validation results, size and changed paths, applies the patch and verifies the resulting file list. It does not execute candidate code in the publication job. The patch is committed to a dedicated branch and opened as a PR; no automatic merge is performed. A PR is a proposal, not an assertion that the change is correct. Review the diff and CI results before merging. Workflow-file changes remain blocked by the patch evaluator.

The PR publication token is not passed to the provider or into the Docker test container. Keep candidate code and tests out of any step that has write credentials. The job still relies on GitHub Actions and the runner's security boundary; this is defense in depth, not a guarantee against every platform compromise.

## Repeatable free-model coding benchmark

Run `python -m agent_team.benchmark` locally for a dry-run summary; it makes zero provider requests. The fixed benchmark set is in `benchmarks/coding_tasks.json` and contains three small, deterministic fixtures: whitespace normalization, numeric clamping, and word counting. The benchmark scores a task only when the fixed fixture tests pass and the model has not modified test files.

To run the benchmark, both `AUTHORIZE_BENCHMARK_PROVIDER_CALLS=true` and `AUTHORIZE_BENCHMARK_TEST_EXECUTION=true` are required, and `OPENROUTER_API_KEY` must be present. The manual GitHub Actions workflow requires two separate authorization checkboxes and compares three configured free routes: `cohere/north-mini-code:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, and `openrouter/free`. This is 9 logical model/task pairs; the router may retry a transient provider failure once, so the maximum is 18 HTTP requests. There is no paid-model fallback. Results are uploaded as a one-day artifact; the workflow is never scheduled automatically.

A score is only evidence for these fixtures and test conditions, not a general ranking of coding ability. The alias `openrouter/free` may resolve to different underlying models over time, and free model availability and quotas change. Test containers run without network access, but Docker image builds install dependencies before candidate code runs and may use the network.
