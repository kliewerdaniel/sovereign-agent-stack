"""Tests for Agent Runtime Orchestrator."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from sas.runtime.orchestrator import (
    AgentRuntime,
    FleetCoordinator,
    AgentContext,
    AgentStatus,
)
from sas.core.config import SASConfig


class TestAgentRuntime:
    """Tests for AgentRuntime."""
    
    def test_from_defaults(self):
        runtime = AgentRuntime.from_defaults()
        assert runtime.context.status == AgentStatus.INITIALIZED
        assert runtime.context.config is not None
    
    def test_initialize(self):
        runtime = AgentRuntime.from_defaults()
        runtime.initialize()
        assert runtime.context.status == AgentStatus.RUNNING
    
    def test_shutdown(self):
        runtime = AgentRuntime.from_defaults()
        runtime.initialize()
        runtime.shutdown()
        assert runtime.context.status == AgentStatus.STOPPED
    
    def test_register_tool(self):
        runtime = AgentRuntime.from_defaults()
        runtime.register_tool(
            "test_tool",
            "A test tool",
            {"type": "object", "properties": {}},
            ["read_filesystem"],
        )
        assert "test_tool" in runtime._tools
    
    def test_execute_tool_success(self):
        runtime = AgentRuntime.from_defaults()
        runtime.context.capability_registry.grant("read_filesystem")
        runtime.register_tool(
            "test_tool",
            "A test tool",
            {"type": "object", "properties": {}},
            ["read_filesystem"],
        )
        result = runtime.execute_tool("test_tool", {"query": "test"})
        assert result["status"] == "ok"
        assert result["tool"] == "test_tool"
    
    def test_execute_tool_missing_capability(self):
        runtime = AgentRuntime.from_defaults()
        runtime.register_tool(
            "test_tool",
            "A test tool",
            {"type": "object", "properties": {}},
            ["write_filesystem"],  # Not granted
        )
        with pytest.raises(PermissionError):
            runtime.execute_tool("test_tool", {})
    
    def test_execute_tool_not_registered(self):
        runtime = AgentRuntime.from_defaults()
        with pytest.raises(ValueError, match="not registered"):
            runtime.execute_tool("nonexistent", {})
    
    def test_get_status(self):
        runtime = AgentRuntime.from_defaults()
        runtime.initialize()
        status = runtime.get_status()
        assert "session_id" in status
        assert "status" in status
        assert "sovereignty_score" in status
        assert "sovereignty_verdict" in status


class TestFleetCoordinator:
    """Tests for FleetCoordinator."""
    
    def test_spawn_agent(self):
        coordinator = FleetCoordinator()
        session_id = coordinator.spawn_agent()
        assert session_id in coordinator._agents
    
    def test_terminate_agent(self):
        coordinator = FleetCoordinator()
        session_id = coordinator.spawn_agent()
        coordinator.terminate_agent(session_id)
        assert session_id not in coordinator._agents
    
    def test_terminate_nonexistent_agent(self):
        coordinator = FleetCoordinator()
        with pytest.raises(ValueError, match="not found"):
            coordinator.terminate_agent("nonexistent")
    
    def test_list_agents(self):
        coordinator = FleetCoordinator()
        coordinator.spawn_agent()
        coordinator.spawn_agent()
        agents = coordinator.list_agents()
        assert len(agents) == 2
    
    def test_fleet_status_empty(self):
        coordinator = FleetCoordinator()
        status = coordinator.fleet_status()
        assert status["agents"] == 0
        assert status["status"] == "empty"
    
    def test_fleet_status_with_agents(self):
        coordinator = FleetCoordinator()
        coordinator.spawn_agent()
        status = coordinator.fleet_status()
        assert status["agents"] == 1
        assert "average_sovereignty_score" in status
    
    def test_shutdown_all(self):
        coordinator = FleetCoordinator()
        coordinator.spawn_agent()
        coordinator.spawn_agent()
        coordinator.shutdown_all()
        assert len(coordinator._agents) == 0


class TestAgentContext:
    """Tests for AgentContext."""
    
    def test_default_context(self):
        context = AgentContext()
        assert context.status == AgentStatus.INITIALIZED
        assert context.session_id is not None
        assert context.config is not None
    
    def test_context_has_required_components(self):
        context = AgentContext()
        assert context.execution_context is not None
        assert context.capability_registry is not None
        assert context.policy_enforcer is not None
        assert context.state_machine is not None
        assert context.sovereignty_asserter is not None
