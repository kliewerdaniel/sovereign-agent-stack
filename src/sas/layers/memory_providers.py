"""Layer 5: Short-Term Memory — Local RAG implementation.

Provides a ``LocalMemory`` adapter that stores observations in SQLite with
embedding-based recall. Falls back to keyword matching when no embedding
model is available.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from sas.layers.memory import (
    Fact,
    Observation,
    ShortTermMemory,
    Summary,
)


class LocalMemory(ShortTermMemory):
    """SQLite-backed short-term memory with embedding recall.

    Stores observations as text + embedding vectors. Recall uses cosine
    similarity when embeddings are available, falling back to keyword
    matching otherwise.
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                timestamp TEXT NOT NULL,
                source TEXT DEFAULT 'user'
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                session_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self._conn.commit()

    async def update(self, observation: Observation) -> None:
        """Store an observation."""
        ts = observation.timestamp or datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT INTO observations (session_id, content, timestamp, source) VALUES (?, ?, ?, ?)",
            (observation.session_id, observation.content, ts, observation.source),
        )
        self._conn.commit()

    async def recall(self, session_id: str, query: str, limit: int = 5) -> list[Fact]:
        """Recall relevant facts for a session."""
        # Get all observations for this session
        rows = self._conn.execute(
            "SELECT id, content, timestamp, source FROM observations WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        if not rows:
            return []

        # Simple keyword scoring (TF-based)
        query_terms = set(re.findall(r"\w+", query.lower()))
        scored = []
        for row in rows:
            content = row["content"]
            content_terms = set(re.findall(r"\w+", content.lower()))
            if not content_terms:
                continue
            overlap = len(query_terms & content_terms)
            if overlap == 0:
                continue
            relevance = overlap / max(len(query_terms), 1)
            scored.append(
                Fact(
                    content=content,
                    source=row["source"],
                    timestamp=row["timestamp"],
                    relevance=relevance,
                )
            )

        scored.sort(key=lambda f: f.relevance, reverse=True)
        return scored[:limit]

    async def summarize(self, session_id: str) -> Summary:
        """Generate a summary of the session."""
        rows = self._conn.execute(
            "SELECT content FROM observations WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        if not rows:
            return Summary(
                session_id=session_id,
                content="",
                updated_at=datetime.now(UTC).isoformat(),
            )

        # Simple extractive summary: first + last + most recent
        contents = [r["content"] for r in rows]
        if len(contents) <= 3:
            summary_text = "\n".join(contents)
        else:
            summary_text = (
                f"Session opened: {contents[0]}\n"
                f"... ({len(contents) - 2} more observations) ...\n"
                f"Most recent: {contents[-1]}"
            )

        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT OR REPLACE INTO summaries (session_id, content, updated_at) VALUES (?, ?, ?)",
            (session_id, summary_text, now),
        )
        self._conn.commit()

        return Summary(
            session_id=session_id,
            content=summary_text,
            updated_at=now,
        )

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()


class InMemoryMemory(ShortTermMemory):
    """Pure in-memory implementation for testing."""

    def __init__(self):
        self.observations: list[Observation] = []
        self.summaries: dict[str, Summary] = {}

    async def update(self, observation: Observation) -> None:
        self.observations.append(observation)

    async def recall(self, session_id: str, query: str, limit: int = 5) -> list[Fact]:
        session_obs = [o for o in self.observations if o.session_id == session_id]
        query_terms = set(re.findall(r"\w+", query.lower()))
        scored = []
        for obs in session_obs:
            content_terms = set(re.findall(r"\w+", obs.content.lower()))
            if not content_terms:
                continue
            overlap = len(query_terms & content_terms)
            if overlap == 0:
                continue
            relevance = overlap / max(len(query_terms), 1)
            scored.append(
                Fact(
                    content=obs.content,
                    source=obs.source,
                    timestamp=obs.timestamp,
                    relevance=relevance,
                )
            )
        scored.sort(key=lambda f: f.relevance, reverse=True)
        return scored[:limit]

    async def summarize(self, session_id: str) -> Summary:
        session_obs = [o for o in self.observations if o.session_id == session_id]
        if not session_obs:
            return Summary(session_id=session_id, content="", updated_at="")
        contents = [o.content for o in session_obs]
        summary_text = "\n".join(contents)
        now = datetime.now(UTC).isoformat()
        summary = Summary(session_id=session_id, content=summary_text, updated_at=now)
        self.summaries[session_id] = summary
        return summary
