"""Tests for Layer 2: Harness providers."""

import asyncio
import pytest
from sas.layers.harness import Session, Experience, Context, Skill
from sas.layers.model import Message
from sas.layers.memory import Observation
from sas.layers.model_providers import StubModelProvider
from sas.layers.memory_providers import InMemoryMemory
from sas.layers.harness_providers import LocalHarness, StubHarness


class TestLocalHarness:
    """Tests for the real agent loop harness."""

    def test_create_session(self):
        model = StubModelProvider()
        harness = LocalHarness(model=model)
        session = asyncio.run(harness.create_session("test-user"))
        assert session.user == "test-user"
        assert session.id is not None

    def test_invoke_returns_response(self):
        model = StubModelProvider(response="Hello, user!")
        harness = LocalHarness(model=model)
        session = asyncio.run(harness.create_session("test-user"))
        response = asyncio.run(harness.invoke(session, "Hi there"))
        assert response.content == "Hello, user!"
        assert response.session == session

    def test_invoke_stores_observation(self):
        model = StubModelProvider(response="Got it")
        memory = InMemoryMemory()
        harness = LocalHarness(model=model, memory=memory)
        session = asyncio.run(harness.create_session("test-user"))
        asyncio.run(harness.invoke(session, "Remember this"))

        # Check memory has the user message
        facts = asyncio.run(memory.recall(session.id, "Remember"))
        assert len(facts) >= 1

    def test_register_tool(self):
        model = StubModelProvider()
        harness = LocalHarness(model=model)

        def my_tool(x: str) -> dict:
            return {"result": x}

        asyncio.run(harness.register_tool("my_tool", "A test tool", my_tool))
        # Tool registered successfully

    def test_create_skill(self):
        model = StubModelProvider()
        harness = LocalHarness(model=model)
        exp = Experience(context="test context", action="do something", outcome="success")
        skill = asyncio.run(harness.create_skill(exp))
        assert skill.name.startswith("skill_")
        assert "do something" in skill.steps

    def test_execute_skill(self):
        model = StubModelProvider()
        harness = LocalHarness(model=model)
        session = asyncio.run(harness.create_session("u"))
        skill = Skill(name="s", description="d", steps=["step1"])
        ctx = Context(session=session, variables={})
        result = asyncio.run(harness.execute_skill(skill, ctx))
        assert result.success

    def test_get_history(self):
        model = StubModelProvider(response="Hi")
        harness = LocalHarness(model=model)
        session = asyncio.run(harness.create_session("u"))
        asyncio.run(harness.invoke(session, "Hello"))
        history = harness.get_history(session.id)
        assert len(history) >= 2  # system + user + assistant


class TestStubHarness:
    """Tests for the deterministic stub harness."""

    def test_invoke_returns_stub(self):
        harness = StubHarness(response="Stub!")
        session = Session(id="s1", user="u", created_at="now")
        response = asyncio.run(harness.invoke(session, "Hi"))
        assert response.content == "Stub!"

    def test_create_skill(self):
        harness = StubHarness()
        exp = Experience(context="c", action="a", outcome="o")
        skill = asyncio.run(harness.create_skill(exp))
        assert skill.name == "stub"

    def test_register_tool_noop(self):
        harness = StubHarness()
        asyncio.run(harness.register_tool("t", "d", lambda: None))
