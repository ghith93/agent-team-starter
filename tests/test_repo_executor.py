import tempfile
import unittest
from pathlib import Path

from agent_team.repo_executor import PatchRejected, _validate_patch, evaluate_patch


class RepoExecutorTests(unittest.TestCase):
    def test_rejects_parent_traversal(self):
        patch = "--- a/../outside.py\n+++ b/../outside.py\n@@ -1 +1 @@\n-a\n+b\n"
        with self.assertRaises(PatchRejected):
            _validate_patch(patch)

    def test_rejects_workflow_changes(self):
        patch = "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n@@ -1 +1 @@\n-a\n+b\n"
        with self.assertRaisesRegex(PatchRejected, "human review"):
            _validate_patch(patch)

    def test_rejects_secret_paths(self):
        patch = "--- a/.env\n+++ b/.env\n@@ -1 +1 @@\n-A\n+B\n"
        with self.assertRaises(PatchRejected):
            _validate_patch(patch)

    def test_rejects_arbitrary_validation_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
            with self.assertRaisesRegex(ValueError, "Unknown validation"):
                evaluate_patch(temporary, patch, validations=("rm -rf /",))

    def test_evaluation_does_not_change_original_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("old\n", encoding="utf-8")
            patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
            result = evaluate_patch(root, patch, validations=("compile",))
            self.assertTrue(result.applied_in_temporary_copy)
            self.assertEqual(result.changed_paths, ("README.md",))
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "old\n")

    def test_rejects_non_diff(self):
        with self.assertRaises(PatchRejected):
            _validate_patch("please change the code")


if __name__ == "__main__":
    unittest.main()
