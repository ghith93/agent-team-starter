"""Opt-in, local keyword-searchable knowledge store; no embeddings or network access."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any


class MemoryStore:
    """Persist small knowledge notes in a caller-selected SQLite database.

    Storage is plaintext. Only save information appropriate for local persistence;
    do not store credentials, private customer data, or secrets.
    """

    def __init__(self, database_path: str | Path):
        if database_path is None or not str(database_path).strip():
            raise ValueError("An explicit database path is required.")
        if str(database_path) == ":memory:":
            raise ValueError("Use a file-backed database so knowledge survives reconnects.")
        self.path = Path(database_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS memories_updated_idx ON memories(updated_at DESC)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @staticmethod
    def _record(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        return item

    def add(self, title: str, content: str, *, tags: list[str] | None = None,
            source: str = "", now: float | None = None) -> dict[str, Any]:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Memory title must be non-empty.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Memory content must be non-empty.")
        normalized_tags = []
        for tag in tags or []:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("Memory tags must be non-empty strings.")
            value = tag.strip()
            if value not in normalized_tags:
                normalized_tags.append(value)
        if not isinstance(source, str):
            raise ValueError("Memory source must be text.")
        current = time.time() if now is None else float(now)
        memory_id = str(uuid.uuid4())
        with closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO memories
                   (memory_id, title, content, tags_json, source, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (memory_id, title.strip(), content.strip(),
                 json.dumps(normalized_tags, ensure_ascii=False), source.strip(), current, current),
            )
            return self._record(connection.execute(
                "SELECT * FROM memories WHERE memory_id = ?", (memory_id,)
            ).fetchone())

    def get(self, memory_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            return self._record(connection.execute(
                "SELECT * FROM memories WHERE memory_id = ?", (memory_id,)
            ).fetchone())

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query must be non-empty.")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100.")
        terms = [term.casefold() for term in query.split() if term.strip()]
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC, created_at DESC"
            ).fetchall()
        matches = []
        for row in rows:
            item = self._record(row)
            searchable = " ".join([item["title"], item["content"], item["source"], *item["tags"]]).casefold()
            if all(term in searchable for term in terms):
                matches.append(item)
                if len(matches) >= limit:
                    break
        return matches

    def health_check(self) -> bool:
        with closing(self._connect()) as connection:
            row = connection.execute("PRAGMA quick_check").fetchone()
            return bool(row and row[0] == "ok")
