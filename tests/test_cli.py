import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from agent_team.cli import main


class CliTests(unittest.TestCase):
    def test_check_config_does_not_call_provider(self):
        out = io.StringIO()
        with patch.dict(os.environ, {"GEMINI_API_KEY": " test-key ", "OPENROUTER_API_KEY": ""}, clear=False), contextlib.redirect_stdout(out):
            code = main(["--check-config"])
        self.assertEqual(code, 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result["configured_providers"], ["Gemini"])
        self.assertFalse(result["live_check_performed"])
        self.assertNotIn("test-key", out.getvalue())

    def test_task_file_and_task_conflict(self):
        out = io.StringIO()
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as f, contextlib.redirect_stderr(out):
            f.write("task"); f.flush()
            code = main(["inline task", "--task-file", f.name])
        self.assertEqual(code, 2)

if __name__ == "__main__":
    unittest.main()
