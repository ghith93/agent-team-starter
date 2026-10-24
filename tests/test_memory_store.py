import tempfile
import unittest
from pathlib import Path

from agent_team.memory_store import MemoryStore


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "knowledge" / "memory.sqlite3"
        self.store = MemoryStore(self.database)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_add_and_retrieve_persisted_note(self):
        item = self.store.add(
            "Retry policy", "Retry transient failures only.",
            tags=["workflow", "retries", "workflow"], source="operations guide", now=10,
        )
        self.assertEqual(item["tags"], ["workflow", "retries"])
        reopened = MemoryStore(self.database)
        saved = reopened.get(item["memory_id"])
        self.assertEqual(saved["title"], "Retry policy")
        self.assertEqual(saved["content"], "Retry transient failures only.")
        self.assertTrue(reopened.health_check())

    def test_keyword_search_requires_all_terms(self):
        self.store.add("Retry policy", "Retry transient failures only.", tags=["workflow"], now=10)
        self.store.add("Secrets", "Never retry authentication failures.", tags=["security"], now=20)
        results = self.store.search("retry workflow")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Retry policy")
        self.assertEqual(self.store.search("retry authentication")[0]["title"], "Secrets")

    def test_search_is_case_insensitive_and_tag_aware(self):
        self.store.add("Provider notes", "Use bounded retries.", tags=["OpenRouter"], now=10)
        self.assertEqual(len(self.store.search("openrouter BOUNDED")), 1)

    def test_search_limit_is_bounded(self):
        for index in range(3):
            self.store.add(f"Note {index}", "same content", now=index)
        self.assertEqual(len(self.store.search("same", limit=2)), 2)

    def test_rejects_empty_inputs_and_bad_limits(self):
        with self.assertRaises(ValueError):
            self.store.add(" ", "content")
        with self.assertRaises(ValueError):
            self.store.add("title", " ")
        with self.assertRaises(ValueError):
            self.store.search(" ")
        with self.assertRaises(ValueError):
            self.store.search("content", limit=0)
        with self.assertRaises(ValueError):
            self.store.add("title", "content", tags=["ok", " "])
        with self.assertRaises(ValueError):
            MemoryStore(":memory:")


if __name__ == "__main__":
    unittest.main()
