# Persistent local knowledge store

Status: opt-in SQLite note store with exact keyword search and bounded, explicitly requested injection into agent prompts.

## Capabilities

- Save a note with title, content, tags, source label, and timestamps.
- Retrieve by ID and search with case-insensitive substring matching. Every whitespace-separated query term must match somewhere in the title, content, source, or tags.
- Reopen the same database across process instances.
- Validate inputs and run a lightweight SQLite integrity check.

## Example

```python
from agent_team.memory_store import MemoryStore

memory = MemoryStore("./runtime/knowledge.sqlite3")
memory.add(
    "Retry policy",
    "Retry transient errors only; do not loop on authentication errors.",
    tags=["workflow", "reliability"],
    source="operations runbook",
)
for note in memory.search("retry authentication"):
    print(note["title"], note["content"])
```

## Limits and safety

- Database content is plaintext; never store API keys, passwords, cookies, sensitive prompts, or private customer data.
- Search is keyword-based, not semantic/vector retrieval; it does not infer synonyms.
- CLI retrieval is opt-in: pass both `--memory-db PATH` and `--memory-query TEXT`. The explicit query is required because retrieved notes are sent to the configured model provider. At most five notes and 6,000 title/content characters are included per run.
- Retrieved notes are wrapped in an `untrusted` context block and all three stages are instructed not to follow embedded instructions. This is defense-in-depth, not a guarantee against prompt injection; review retrieved sources before use.
- Keep the database outside version control and back it up only to an approved destination.
- Do not claim persistent agent memory integration until context selection, prompt-size limits, trust labels, and retrieval tests are implemented.
