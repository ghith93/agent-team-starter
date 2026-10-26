from pathlib import Path

import pytest

from agent_team.repo_executor import PatchRejected, _validate_patch, evaluate_patch


def test_rejects_parent_traversal():
    patch = "--- a/../outside.py\n+++ b/../outside.py\n@@ -1 +1 @@\n-a\n+b\n"
    with pytest.raises(PatchRejected):
        _validate_patch(patch)


def test_rejects_workflow_changes():
    patch = "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n@@ -1 +1 @@\n-a\n+b\n"
    with pytest.raises(PatchRejected, match="human review"):
        _validate_patch(patch)


def test_rejects_secret_paths():
    patch = "--- a/.env\n+++ b/.env\n@@ -1 +1 @@\n-A\n+B\n"
    with pytest.raises(PatchRejected):
        _validate_patch(patch)


def test_rejects_arbitrary_validation_command(tmp_path):
    patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
    with pytest.raises(ValueError, match="Unknown validation"):
        evaluate_patch(tmp_path, patch, validations=("rm -rf /",))


def test_evaluation_does_not_change_original_workspace(tmp_path):
    (tmp_path / "README.md").write_text("old\n", encoding="utf-8")
    patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
    result = evaluate_patch(tmp_path, patch, validations=("compile",))
    assert result.applied_in_temporary_copy is True
    assert result.changed_paths == ("README.md",)
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "old\n"


def test_rejects_non_diff():
    with pytest.raises(PatchRejected):
        _validate_patch("please change the code")
