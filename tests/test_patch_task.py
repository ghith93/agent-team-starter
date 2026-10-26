import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from agent_team.patch_task import collect_repository_context, extract_patch, main, run_patch_task
from agent_team.repo_executor import PatchRejected


class PatchTaskTests(unittest.TestCase):
    def test_extracts_plain_unified_diff(self):
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
        self.assertEqual(extract_patch(patch), patch)

    def test_extracts_fenced_diff(self):
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new"
        fence = chr(96) * 3
        self.assertEqual(extract_patch(fence + "diff\n" + patch + "\n" + fence).strip(), patch)

    def test_skips_non_diff_fence_and_extracts_later_diff_fence(self):
        fence = chr(96) * 3
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new"
        response = fence + "python\nprint(1)\n" + fence + "\n"
        response += fence + "diff\n" + patch + "\n" + fence
        self.assertEqual(extract_patch(response).strip(), patch)

    def test_extracts_diff_from_language_labeled_fence(self):
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new"
        fence = chr(96) * 3
        self.assertEqual(extract_patch(fence + "diff\n" + patch + "\n" + fence).strip(), patch)

    def test_extracts_diff_after_short_preamble(self):
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
        response = "Here is the requested change:\n\n" + patch
        self.assertEqual(extract_patch(response), patch)

    def test_rejects_pseudo_file_headers_after_preamble(self):
        with self.assertRaises(PatchRejected):
            extract_patch("Here is a patch:\n--- FILE: README.md ---\n+++ FILE: README.md +++\n")

    def test_rejects_non_diff_model_output(self):
        with self.assertRaises(PatchRejected):
            extract_patch("Here are some suggestions, but no patch.")

    def test_context_skips_environment_and_workflow_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "agent.py").write_text("print('safe')\n", encoding="utf-8")
            key_name = "OPENROUTER_" + "API_KEY"
            (root / ".env").write_text(key_name + "=dummy-value\n", encoding="utf-8")
            workflow = root / ".github" / "workflows"
            workflow.mkdir(parents=True)
            (workflow / "ci.yml").write_text("deploy: true\n", encoding="utf-8")
            context = collect_repository_context(root)
            self.assertIn("agent.py", context)
            self.assertNotIn(key_name, context)
            self.assertNotIn("ci.yml", context)

    def test_invalid_validation_is_rejected_before_provider_call(self):
        class NeverCalledRouter:
            def ask(self, *args, **kwargs):
                raise AssertionError("Provider must not be called for invalid validation.")
        with self.assertRaisesRegex(ValueError, "Unknown validation"):
            run_patch_task("task", router=NeverCalledRouter(), validations=("shell",))

    def test_test_execution_requires_explicit_authorization_before_provider_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            previous = os.getcwd()
            try:
                os.chdir(temporary)
                with patch.dict(os.environ, {
                    "TASK_INPUT": "safe test task",
                    "PATCH_VALIDATION_LEVEL": "unittest",
                    "AUTHORIZE_TEST_EXECUTION": "false",
                }, clear=False):
                    with patch("agent_team.patch_task.run_patch_task") as run:
                        code = main()
                self.assertEqual(code, 2)
                run.assert_not_called()
                result = json.loads((Path(temporary) / "repository-patch-result.json").read_text(encoding="utf-8"))
                self.assertEqual(result["status"], "test_execution_not_authorized")
            finally:
                os.chdir(previous)

    def test_context_redacts_credential_like_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key_name = "API_" + "KEY"
            fake_value = "dummy" + "-value"
            (root / "settings.py").write_text(
                f"{key_name} = '{fake_value}'\nnormal = True\n",
                encoding="utf-8",
            )
            context = collect_repository_context(root)
            self.assertIn("[REDACTED: credential-like line]", context)
            self.assertNotIn(fake_value, context)

    def test_context_redacts_quoted_json_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_value = "dummy-secret-value-12345"
            (root / "settings.json").write_text(
                '{"api_key": "' + fake_value + '", "safe": true}\n',
                encoding="utf-8",
            )
            context = collect_repository_context(root)
            self.assertIn("[REDACTED: credential-like line]", context)
            self.assertNotIn(fake_value, context)

    def test_context_redacts_multiline_json_and_yaml_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            json_secret = "json-secret-value-12345"
            yaml_secret = "yaml-secret-value-67890"
            (root / "settings.json").write_text(
                '{\n  "' + "api" + "_key" + '":\n    "' + json_secret + '",\n  "safe": true\n}\n',
                encoding="utf-8",
            )
            (root / "settings.yaml").write_text(
                "service:\n  " + "pass" + "word:\n    " + yaml_secret + "\n  mode: safe\n",
                encoding="utf-8",
            )
            context = collect_repository_context(root)
            self.assertIn("[REDACTED: credential-like file]", context)
            self.assertNotIn(json_secret, context)
            self.assertNotIn(yaml_secret, context)


if __name__ == "__main__":
    unittest.main()
