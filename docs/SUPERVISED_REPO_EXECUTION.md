# Supervised repository patch evaluation

\`agent_team.repo_executor.evaluate_patch\` provides a bounded local verification step for a proposed unified diff.

## Safety model

- The original checkout is never modified. Files are copied to a disposable temporary directory, the patch is applied there, and the directory is deleted afterward.
- Model-supplied shell commands are never executed. Callers can select only \`project-tests\`, \`pytest\`, \`unittest\`, or \`compile\`, each mapped to a fixed argument array.
- The default validation is \`compile\`; this avoids executing newly generated project code by default.
- Patches are size-limited; binary patches, traversal, secret-like paths, symlink/submodule/rename patches, and \`.github/workflows/**\` changes are rejected.
- Workspaces containing symlinks are rejected rather than dereferenced. The workspace copy has file-count and byte-size limits and excludes Git metadata, virtual environments, common caches, and common secret/configuration paths.
- Validation commands have timeouts and output caps. This helper does not provide OS-level sandboxing or network isolation. Optional project test commands execute project code and should only be enabled in an appropriately restricted environment.

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
