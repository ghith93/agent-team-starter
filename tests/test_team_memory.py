import unittest
from types import SimpleNamespace

from agent_team.team import run_team


class FakeRouter:
    def __init__(self):
        self.calls = []

    def ask(self, prompt, *, system_prompt=""):
        self.calls.append((prompt, system_prompt))
        return SimpleNamespace(provider="test", model="fake", text=f"stage output {len(self.calls)}")


class TeamMemoryTests(unittest.TestCase):
    def test_retrieved_memory_is_bounded_and_marked_untrusted_for_every_stage(self):
        router = FakeRouter()
        result = run_team(
            "Prepare an operational plan",
            router=router,
            memory_context=[{
                "title": "Retry policy",
                "content": "Retry transient errors only.",
                "tags": ["reliability"],
                "source": "runbook",
            }],
        )
        self.assertEqual(result["memory_context_count"], 1)
        self.assertEqual(len(router.calls), 3)
        for prompt, system_prompt in router.calls:
            self.assertIn("<retrieved_memory_untrusted>", prompt)
            self.assertIn("Retry transient errors only.", prompt)
            self.assertIn("untrusted", system_prompt.lower())

    def test_empty_memory_does_not_add_context(self):
        router = FakeRouter()
        result = run_team("Simple task", router=router, memory_context=[])
        self.assertEqual(result["memory_context_count"], 0)
        self.assertTrue(all("<retrieved_memory_untrusted>" not in prompt for prompt, _ in router.calls))

    def test_memory_context_has_strict_note_count_and_shape_limits(self):
        router = FakeRouter()
        with self.assertRaises(ValueError):
            run_team("task", router=router, memory_context=[{"title": "x", "content": "y"}] * 6)
        with self.assertRaises(ValueError):
            run_team("task", router=router, memory_context=[{"title": "missing content"}])
        self.assertEqual(router.calls, [])

    def test_memory_context_budget_is_enforced(self):
        router = FakeRouter()
        context = [{"title": "note", "content": "x" * 3000} for _ in range(3)]
        with self.assertRaises(ValueError):
            run_team("task", router=router, memory_context=context)
        self.assertEqual(router.calls, [])


if __name__ == "__main__":
    unittest.main()
