"""Agent Runtime Orchestrator.

The central runtime that manages agent lifecycle, tool execution,
policy enforcement, and sovereignty verification.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from sas.core.config import SASConfig, parse_sas_yaml
from sas.core.scoring import generate_report, SovereigntyReport
from sas.rust_bridge import (
    ExecutionContext,
    AgentStateMachine,
    CapabilityRegistry,
    PolicyEnforcer,
    SovereigntyAsserter,
)

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent runtime status."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentContext:
    """Context for an agent execution session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: SASConfig = field(default_factory=SASConfig)
    execution_context: ExecutionContext = field(default_factory=ExecutionContext)
    capability_registry: CapabilityRegistry = field(default_factory=CapabilityRegistry)
    policy_enforcer: PolicyEnforcer = field(default_factory=lambda: PolicyEnforcer("allow"))
    state_machine: AgentStateMachine = field(default_factory=AgentStateMachine)
    sovereignty_asserter: SovereigntyAsserter = field(default_factory=SovereigntyAsserter)
    status: AgentStatus = AgentStatus.INITIALIZED
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class AgentRuntime:
    """Sovereign Agent Runtime Orchestrator.
    
    Manages agent lifecycle, tool execution, policy enforcement,
    and sovereignty verification.
    
    Usage:
        runtime = AgentRuntime.from_config("sas.yaml")
        runtime.initialize()
        runtime.run()
    """
    
    def __init__(self, context: AgentContext):
        self.context = context
        self._tools: dict[str, Any] = {}
        self._middleware: list[Any] = []
    
    @classmethod
    def from_config(cls, config_path: str | Path) -> "AgentRuntime":
        """Create a runtime from a sas.yaml configuration file."""
        config = parse_sas_yaml(Path(config_path))
        context = AgentContext(config=config)
        
        # Configure capabilities based on config
        context.capability_registry.grant("read_filesystem")
        context.capability_registry.grant("read_knowledge")
        
        # Configure sovereignty asserter
        cls._configure_sovereignty(context, config)
        
        return cls(context)
    
    @classmethod
    def from_defaults(cls) -> "AgentRuntime":
        """Create a runtime with default configuration."""
        context = AgentContext()
        # Grant basic capabilities
        context.capability_registry.grant("read_filesystem")
        context.capability_registry.grant("read_knowledge")
        return cls(context)
    
    @staticmethod
    def _configure_sovereignty(context: AgentContext, config: SASConfig):
        """Configure sovereignty asserter based on config."""
        # Model layer
        if config.model_primary and config.model_primary.location == "local":
            context.sovereignty_asserter.with_layer("model", "owned")
        else:
            context.sovereignty_asserter.with_layer("model", "rented")
        
        # Harness layer (always owned - ARGO)
        context.sovereignty_asserter.with_layer("harness", "owned")
        
        # Compute layer
        from sas.core.config import SubstrateType
        if config.substrate in (SubstrateType.LOCAL_DOCKER, SubstrateType.LOCAL_VM):
            context.sovereignty_asserter.with_layer("compute", "owned")
        else:
            context.sovereignty_asserter.with_layer("compute", "rented")
        
        # Identity (unavoidably rented)
        context.sovereignty_asserter.with_layer("identity", "rented")
        
        # Memory layers
        from sas.core.config import MemoryProvider
        if config.memory_short_term == MemoryProvider.LOCAL_RAG:
            context.sovereignty_asserter.with_layer("short_term_memory", "owned")
        else:
            context.sovereignty_asserter.with_layer("short_term_memory", "rented")
        
        from sas.core.config import LongTermProvider
        if config.memory_long_term == LongTermProvider.COMPILE_TIME_GRAPH:
            context.sovereignty_asserter.with_layer("long_term_knowledge", "owned")
        else:
            context.sovereignty_asserter.with_layer("long_term_knowledge", "rented")
        
        # Auth layer
        from sas.core.config import AuthBroker
        if config.auth_broker == AuthBroker.LOCAL_MCP_GATEWAY:
            context.sovereignty_asserter.with_layer("auth", "owned")
        else:
            context.sovereignty_asserter.with_layer("auth", "rented")
        
        # Payments (unavoidably rented)
        context.sovereignty_asserter.with_layer("payments", "rented")
    
    def initialize(self):
        """Initialize the runtime."""
        logger.info(f"Initializing agent runtime {self.context.session_id}")
        self.context.state_machine.transition("Compiling")
        self.context.status = AgentStatus.RUNNING
        logger.info(f"Runtime initialized with sovereignty score: {self.context.sovereignty_asserter.score:.2f}")
    
    def shutdown(self):
        """Shutdown the runtime."""
        logger.info(f"Shutting down agent runtime {self.context.session_id}")
        # Transition through valid states to reach Completed
        current = self.context.state_machine.current
        if current not in ("Completed", "Failed", "Idle"):
            self.context.state_machine.transition("Failed")
        if self.context.state_machine.current == "Failed":
            self.context.state_machine.transition("Idle")
        self.context.status = AgentStatus.STOPPED
    
    def register_tool(self, name: str, description: str, schema: dict, 
                      required_capabilities: list[str]) -> None:
        """Register a tool with the runtime."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "schema": schema,
            "required_capabilities": required_capabilities,
        }
        logger.info(f"Registered tool: {name}")
    
    def execute_tool(self, name: str, input_data: dict) -> dict:
        """Execute a registered tool with policy enforcement."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
        
        tool = self._tools[name]
        
        # Check capabilities
        for cap in tool["required_capabilities"]:
            if not self.context.capability_registry.is_granted(cap):
                raise PermissionError(
                    f"Tool '{name}' requires capability '{cap}' which is not granted"
                )
        
        # Execute with state tracking
        self.context.state_machine.transition("Executing")
        
        try:
            # In a real implementation, this would dispatch to the actual tool
            result = {"status": "ok", "tool": name, "input": input_data}
            self.context.state_machine.transition("Verifying")
            self.context.state_machine.transition("Completed")
            return result
        except Exception as e:
            self.context.state_machine.transition("Failed")
            raise
    
    def verify_sovereignty(self) -> SovereigntyReport:
        """Verify and return sovereignty report."""
        config = self.context.config
        report = generate_report(config)
        logger.info(f"Sovereignty score: {report.score:.2f} ({report.verdict})")
        return report
    
    def get_status(self) -> dict:
        """Get runtime status."""
        return {
            "session_id": self.context.session_id,
            "status": self.context.status.value,
            "state": self.context.state_machine.current,
            "sovereignty_score": self.context.sovereignty_asserter.score,
            "sovereignty_verdict": self.context.sovereignty_asserter.verdict,
            "registered_tools": list(self._tools.keys()),
            "granted_capabilities": list(self.context.capability_registry.granted_capabilities()),
            "created_at": self.context.created_at,
            "last_activity": self.context.last_activity,
        }


class FleetCoordinator:
    """Multi-agent fleet coordinator.
    
    Manages multiple agent runtimes and coordinates their activities.
    """
    
    def __init__(self):
        self._agents: dict[str, AgentRuntime] = {}
        self._fleet_state_machine = AgentStateMachine()
    
    def spawn_agent(self, config_path: Optional[str] = None) -> str:
        """Spawn a new agent in the fleet."""
        if config_path:
            runtime = AgentRuntime.from_config(config_path)
        else:
            runtime = AgentRuntime.from_defaults()
        
        runtime.initialize()
        self._agents[runtime.context.session_id] = runtime
        
        logger.info(f"Spawned agent {runtime.context.session_id}")
        return runtime.context.session_id
    
    def terminate_agent(self, session_id: str) -> None:
        """Terminate an agent in the fleet."""
        if session_id not in self._agents:
            raise ValueError(f"Agent '{session_id}' not found")
        
        self._agents[session_id].shutdown()
        del self._agents[session_id]
        logger.info(f"Terminated agent {session_id}")
    
    def get_agent(self, session_id: str) -> AgentRuntime:
        """Get an agent runtime by session ID."""
        return self._agents[session_id]
    
    def list_agents(self) -> list[dict]:
        """List all agents in the fleet."""
        return [
            {
                "session_id": sid,
                "status": agent.context.status.value,
                "state": agent.context.state_machine.current,
                "sovereignty_score": agent.context.sovereignty_asserter.score,
            }
            for sid, agent in self._agents.items()
        ]
    
    def fleet_status(self) -> dict:
        """Get overall fleet status."""
        if not self._agents:
            return {"agents": 0, "status": "empty"}
        
        scores = [a.context.sovereignty_asserter.score for a in self._agents.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "agents": len(self._agents),
            "average_sovereignty_score": avg_score,
            "agents_list": self.list_agents(),
            "fleet_state": self._fleet_state_machine.current,
        }
    
    def shutdown_all(self):
        """Shutdown all agents in the fleet."""
        for agent in self._agents.values():
            agent.shutdown()
        self._agents.clear()
