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
