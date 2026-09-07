"""Tests for the Agent Runtime."""

import asyncio
import pytest
from sas.layers.model import Message
from sas.layers.model_providers import StubModelProvider
from sas.layers.memory_providers import InMemoryMemory
from sas.runtime.agent_runtime import AgentRuntime, AgentSession


class TestAgentRuntime:
    """Tests for the full agentic loop."""

    def test_create_session(self):
        model = StubModelProvider()
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)
        sid = asyncio.run(runtime.create_session("test-user"))
        assert sid is not None
        assert sid in runtime._sessions

    def test_run_returns_response(self):
        model = StubModelProvider(response="Hello, user!")
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)
        sid = asyncio.run(runtime.create_session("u"))
        result = asyncio.run(runtime.run(sid, "Hi there"))
        assert result == "Hello, user!"

    def test_run_stores_user_message_in_memory(self):
        model = StubModelProvider(response="Got it")
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)
        sid = asyncio.run(runtime.create_session("u"))
        asyncio.run(runtime.run(sid, "Remember this"))

        facts = asyncio.run(memory.recall(sid, "Remember"))
        assert len(facts) >= 1

    def test_run_stores_assistant_response_in_memory(self):
        model = StubModelProvider(response="I am the assistant")
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)
        sid = asyncio.run(runtime.create_session("u"))
        asyncio.run(runtime.run(sid, "Hello"))

        facts = asyncio.run(memory.recall(sid, "assistant"))
        assert len(facts) >= 1

    def test_register_tool(self):
        model = StubModelProvider()
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)

        def my_tool(x: str) -> dict:
            return {"result": x}

        runtime.register_tool("my_tool", "A test tool", my_tool)
        assert "my_tool" in runtime._tools

    def test_run_with_unknown_session_creates_default(self):
        model = StubModelProvider(response="ok")
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)
        result = asyncio.run(runtime.run("nonexistent", "Hi"))
        assert result == "ok"

    def test_run_stream(self):
        model = StubModelProvider(response="Streamed!")
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)
        sid = asyncio.run(runtime.create_session("u"))

        tokens = []
        async def collect():
            async for token in runtime.run_stream(sid, "Hello"):
                tokens.append(token)

        asyncio.run(collect())
        assert len(tokens) >= 1
        assert "Streamed!" in tokens[0]


class TestAgentSession:
    """Tests for the session dataclass."""

    def test_defaults(self):
        session = AgentSession(id="s1", user="u")
        assert session.history == []

    def test_with_history(self):
        msg = Message(role="system", content="test")
        session = AgentSession(id="s1", user="u", history=[msg])
        assert len(session.history) == 1
