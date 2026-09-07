"""Tests for Layer 5: Memory providers."""

import pytest
from sas.layers.memory import Observation, Summary
from sas.layers.memory_providers import LocalMemory, InMemoryMemory


class TestLocalMemory:
    """Tests for the SQLite-backed memory."""

    def test_store_and_recall(self, tmp_path):
        mem = LocalMemory(db_path=tmp_path / "test.db")
        obs = Observation(
            session_id="sess-1",
            content="The user likes Python programming",
            timestamp="2024-01-01T00:00:00Z",
        )
        import asyncio
        asyncio.run(mem.update(obs))

        facts = asyncio.run(mem.recall("sess-1", "Python"))
        assert len(facts) >= 1
        assert "Python" in facts[0].content

    def test_recall_filters_by_session(self, tmp_path):
        mem = LocalMemory(db_path=tmp_path / "test.db")
        import asyncio

        asyncio.run(mem.update(Observation(
            session_id="sess-1", content="alpha", timestamp="2024-01-01T00:00:00Z",
        )))
        asyncio.run(mem.update(Observation(
            session_id="sess-2", content="beta", timestamp="2024-01-01T00:00:00Z",
        )))

        facts = asyncio.run(mem.recall("sess-1", "alpha"))
        assert all("alpha" in f.content for f in facts)

    def test_recall_no_match_returns_empty(self, tmp_path):
        mem = LocalMemory(db_path=tmp_path / "test.db")
        import asyncio
        asyncio.run(mem.update(Observation(
            session_id="sess-1", content="hello", timestamp="2024-01-01T00:00:00Z",
        )))
        facts = asyncio.run(mem.recall("sess-1", "zzzznonexistent"))
        assert facts == []

    def test_summarize(self, tmp_path):
        mem = LocalMemory(db_path=tmp_path / "test.db")
        import asyncio
        asyncio.run(mem.update(Observation(
            session_id="sess-1", content="first observation", timestamp="2024-01-01T00:00:00Z",
        )))
        asyncio.run(mem.update(Observation(
            session_id="sess-1", content="second observation", timestamp="2024-01-02T00:00:00Z",
        )))

        summary = asyncio.run(mem.summarize("sess-1"))
        assert "first" in summary.content
        assert summary.session_id == "sess-1"

    def test_close(self, tmp_path):
        mem = LocalMemory(db_path=tmp_path / "test.db")
        mem.close()


class TestInMemoryMemory:
    """Tests for the pure in-memory adapter."""

    def test_store_and_recall(self):
        import asyncio
        mem = InMemoryMemory()
        asyncio.run(mem.update(Observation(
            session_id="sess-1", content="hello world", timestamp="2024-01-01T00:00:00Z",
        )))
        facts = asyncio.run(mem.recall("sess-1", "hello"))
        assert len(facts) >= 1

    def test_summarize(self):
        import asyncio
        mem = InMemoryMemory()
        asyncio.run(mem.update(Observation(
            session_id="s1", content="line1", timestamp="t1",
        )))
        asyncio.run(mem.update(Observation(
            session_id="s1", content="line2", timestamp="t2",
        )))
        summary = asyncio.run(mem.summarize("s1"))
        assert "line1" in summary.content
        assert "line2" in summary.content
