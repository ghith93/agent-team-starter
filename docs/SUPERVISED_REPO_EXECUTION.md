# Supervised repository patch evaluation

\`agent_team.repo_executor.evaluate_patch\` adds a bounded local verification step for a proposed unified diff.

## Safety model

- The original checkout is never modified. Files are copied to a disposable temporary directory, the patch is applied there, and the directory is deleted afterward.
- Model-supplied shell commands are never executed. Callers can select only \`project-tests\`, \`pytest\`, \`unittest\`, or \`compile\`, each mapped to a fixed argument array.
- Patches are size-limited; binary patches, traversal, secret-like paths, and \`.github/workflows/**\` changes are rejected.
- The copy excludes Git metadata, virtual environments, common caches, and common secret/configuration paths.
- Validation commands have timeouts and output caps. This helper does not provide OS-level sandboxing or network isolation. Run validation only in an appropriately restricted environment and treat project test code as trusted code.

## Example

\`\`\`python
from agent_team.repo_executor import evaluate_patch

result = evaluate_patch(
    ".",
    proposed_unified_diff,
    validations=("project-tests", "compile"),
    timeout_seconds=120,
)
print(result.to_dict())
\`\`\`

A passing result means only that selected commands passed in the temporary copy. It is not proof of correctness or security and does not apply, commit, push, or merge the patch. Human review is required before promoting changes.
