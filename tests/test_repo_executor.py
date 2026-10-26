import tempfile
import unittest
from unittest.mock import patch as patcher
from pathlib import Path

from agent_team.repo_executor import PatchRejected, _safe_patch_diagnostic, _validate_patch, evaluate_patch
from agent_team.sandbox import SandboxResult


class RepoExecutorTests(unittest.TestCase):
    def test_patch_diagnostic_is_bounded_and_redacts_credentials(self):
        diagnostic = _safe_patch_diagnostic(
            "error: sample.py failed Bearer abcdef123456 token=supersecret " + ("x" * 400)
        )
        self.assertIn("sample.py", diagnostic)
        self.assertNotIn("abcdef123456", diagnostic)
        self.assertNotIn("supersecret", diagnostic)
        self.assertLessEqual(len(diagnostic), 240)

    def test_patch_application_failure_includes_bounded_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample.py").write_text("actual\\n", encoding="utf-8")
            patch = (
                "--- a/sample.py\\n+++ b/sample.py\\n"
                "@@ -1 +1 @@\\n-expected\\n+updated\\n"
            )
            result = evaluate_patch(root, patch, validations=("compile",))
            self.assertFalse(result.accepted)
            self.assertEqual(result.validations, ())
            self.assertIn("sample.py", result.message)
            self.assertIn("Diagnostic:", result.message)

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

    def test_project_tests_are_delegated_to_sandbox_and_never_host_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("old\n", encoding="utf-8")
            patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
            with patcher("agent_team.repo_executor.run_sandboxed_command") as sandbox:
                sandbox.return_value = SandboxResult(False, None, False, "Docker is required; tests not run.")
                result = evaluate_patch(root, patch, validations=("unittest",))
        self.assertFalse(result.accepted)
        self.assertTrue(result.applied_in_temporary_copy)
        self.assertFalse(result.validations[0].passed)
        self.assertIn("Docker is required", result.validations[0].output)
        sandbox.assert_called_once()

    def test_rejects_non_diff(self):
        with self.assertRaises(PatchRejected):
            _validate_patch("please change the code")


    def test_rejects_symlink_patch(self):
        patch = "diff --git a/link b/link\nnew file mode 120000\n--- /dev/null\n+++ b/link\n@@ -0,0 +1 @@\n+../../outside\n"
        with self.assertRaisesRegex(PatchRejected, "Symlink"):
            _validate_patch(patch)

    def test_rejects_symlink_in_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root.parent / "outside-agent-team-test"
            outside.write_text("do not copy\n", encoding="utf-8")
            try:
                (root / "linked").symlink_to(outside)
                patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
                with self.assertRaisesRegex(ValueError, "symbolic link"):
                    evaluate_patch(root, patch, validations=("compile",))
            finally:
                outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
