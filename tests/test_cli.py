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

    def test_memory_database_requires_explicit_query(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            code = main(["task", "--memory-db", "memory.sqlite3"])
        self.assertEqual(code, 2)
        self.assertIn("explicit --memory-query", out.getvalue())

    def test_memory_retrieval_is_explicit_and_passed_to_team(self):
        out = io.StringIO()
        notes = [{"title": "Retry policy", "content": "Retry transient errors."}]
        with tempfile.NamedTemporaryFile() as db:
            with patch("agent_team.cli.MemoryStore") as memory_cls:
                with patch("agent_team.cli.run_team", return_value={"ok": True}) as run:
                    with contextlib.redirect_stdout(out):
                        memory_cls.return_value.search.return_value = notes
                        code = main(["task", "--memory-db", db.name, "--memory-query", "retry policy"])
        self.assertEqual(code, 0)
        memory_cls.return_value.search.assert_called_once_with("retry policy", limit=3)
        self.assertEqual(run.call_args.kwargs["memory_context"], notes)

    def test_memory_database_must_already_exist(self):
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            code = main(["task", "--memory-db", "missing-memory.sqlite3", "--memory-query", "query"])
        self.assertEqual(code, 2)
        self.assertIn("existing local SQLite file", out.getvalue())

if __name__ == "__main__":
    unittest.main()
