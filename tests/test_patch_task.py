import tempfile
import unittest
from pathlib import Path

from agent_team.patch_task import collect_repository_context, extract_patch
from agent_team.repo_executor import PatchRejected


class PatchTaskTests(unittest.TestCase):
    def test_extracts_plain_unified_diff(self):
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
        self.assertEqual(extract_patch(patch), patch)

    def test_extracts_fenced_diff(self):
        patch = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new"
        fence = chr(96) * 3
        self.assertEqual(extract_patch(fence + "diff\n" + patch + "\n" + fence).strip(), patch)

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


if __name__ == "__main__":
    unittest.main()
