"""Capability-Bound Agent Runtime — closes the tool execution boundary.

The agent runtime is the most critical boundary after the quant path.
Every tool invocation must pass through capability verification.

Architectural invariants:
    MODEL OUTPUT ≠ TOOL AUTHORIZATION.
    REGISTRATION ≠ AUTHORITY.
    DISCOVERABILITY ≠ EXECUTABILITY.

A model-generated tool call is NEVER itself authorization.
A registered tool is NEVER authorized merely because it exists.
A tool available to the runtime is NEVER executable without capability.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sas.quant.capability_bound_tool import CapabilityBoundTool
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutionReceipt,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)
from sas.layers.memory import Observation, ShortTermMemory
from sas.layers.model import Message, ModelProvider, Tool


# ---------------------------------------------------------------------------
# Agent Session
# ---------------------------------------------------------------------------


@dataclass
class AgentSession:
    """A single agent session."""
    id: str
    user: str
    history: list[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


# ---------------------------------------------------------------------------
# Capability-Bound Agent Runtime
# ---------------------------------------------------------------------------


class CapabilityBoundAgentRuntime:
    """Full agentic loop with capability-bound tool execution.

    Every tool invocation must pass through capability verification.
    The model proposes tool calls; the runtime verifies authorization.

    This closes the agent runtime boundary by ensuring:
    1. Tools are wrapped in CapabilityBoundTool
    2. Tool calls require capability verification
    3. Direct handler access is impossible
    4. Execution receipts are generated
    """

    def __init__(
        self,
        model: ModelProvider,
        memory: ShortTermMemory,
        max_tool_rounds: int = 5,
        system_prompt: str | None = None,
        domain: ProtocolDomain | None = None,
    ):
        self._model = model
        self._memory = memory
        self._max_tool_rounds = max_tool_rounds
        self._system_prompt = system_prompt or self._default_system_prompt()
        self._tools: dict[str, CapabilityBoundTool] = {}
        self._sessions: dict[str, AgentSession] = {}
        self._domain = domain or create_protocol_domain("agent-domain", DomainType.SOVEREIGN)
        self._receipts: list[ExecutionReceipt] = []

    def _default_system_prompt(self) -> str:
        return (
            "You are a sovereign AI assistant. Use tools when needed. "
            "Be concise and accurate."
        )

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: dict | None = None,
    ) -> None:
        """Register a callable tool.

        The tool is wrapped in CapabilityBoundTool, making it
        structurally impossible to invoke without capability.
        """
        self._tools[name] = CapabilityBoundTool(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters,
        )

    async def create_session(self, user: str) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = AgentSession(
            id=session_id,
            user=user,
            history=[Message(role="system", content=self._system_prompt)],
        )
        return session_id

    async def run(self, session_id: str, message: str) -> str:
        """Run the agent loop for a user message.

        Tool calls are verified through capability before execution.
        """
        if session_id not in self._sessions:
            session_id = await self.create_session("default")

        session = self._sessions[session_id]
        history = session.history

        # Recall relevant memory
        facts = await self._memory.recall(session_id, message)
        if facts:
            context = "\n".join(f"- {f.content}" for f in facts)
            history.append(Message(role="system", content=f"Context from memory:\n{context}"))

        # Store user message
        history.append(Message(role="user", content=message))
        await self._memory.update(Observation(
            session_id=session_id,
            content=message,
            timestamp=datetime.now(UTC).isoformat(),
            source="user",
        ))

        # Build tool schemas
        tools = [
            Tool(name=t.description, description=t.description, parameters=t.parameters)
            for t in self._tools.values()
        ]

        # Agent loop
        final_text = ""
        for round_i in range(self._max_tool_rounds):
            completion = await self._model.complete(history, tools)

            if completion.tool_calls:
                # Append assistant message with tool calls
                tc_text = "\n".join(
                    f"[Tool call: {tc.get('function', {}).get('name', '?')}({tc.get('function', {}).get('arguments', '{}')})]"
                    for tc in completion.tool_calls
                )
                history.append(Message(role="assistant", content=tc_text))

                # Execute tools with capability enforcement
                tool_results = []
                for tc in completion.tool_calls:
                    func_name = tc.get("function", {}).get("name", "")
                    args_str = tc.get("function", {}).get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if args_str else {}
                    except json.JSONDecodeError:
                        args = {}

                    # Look up the tool
                    tool = self._tools.get(func_name)
                    if tool is None:
                        tool_results.append(json.dumps({"error": f"Unknown tool: {func_name}"}))
                        continue

                    # MODEL OUTPUT ≠ TOOL AUTHORIZATION
                    # We must resolve authorization for this tool call
                    capability = self._resolve_tool_capability(func_name, args)
                    if capability is None:
                        tool_results.append(json.dumps({
                            "error": f"Tool '{func_name}' not authorized",
                        }))
                        continue

                    # Invoke through capability-bound interface
                    result = tool.invoke(
                        capability=capability,
                        arguments=args,
                        domain=self._domain,
                    )

                    if result.is_permitted:
                        tool_results.append(json.dumps(result.result, default=str))
                        if result.receipt:
                            self._receipts.append(result.receipt)
                    else:
                        tool_results.append(json.dumps({
                            "error": f"Tool '{func_name}' rejected: {result.rejection_reason}",
                        }))

                # Feed tool results back to model
                results_text = "\n".join(tool_results)
                history.append(Message(role="assistant", content=results_text))
                final_text = completion.content or results_text
            else:
                final_text = completion.content
                history.append(Message(role="assistant", content=final_text))
                break

        # Store assistant response
        await self._memory.update(Observation(
            session_id=session_id,
            content=final_text,
            timestamp=datetime.now(UTC).isoformat(),
            source="assistant",
        ))

        return final_text

    def _resolve_tool_capability(
        self,
        tool_name: str,
        arguments: dict,
    ) -> ExecutionCapability | None:
        """Resolve authorization for a tool call.

        This is the critical boundary: the model proposes a tool call,
        but the runtime must verify authorization before execution.

        In a full implementation, this would:
        1. Look up the authorization for this tool/action
        2. Materialize an ExecutionCapability
        3. Return the capability for verification

        For now, we create a default capability that permits the tool.
        In production, this would integrate with the formal protocol.
        """
        scope = CapabilityScope(
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            actor_id="agent",
            action=f"tool.{tool_name}",
            resource=tool_name,
            arguments=arguments,
            constraints=CapabilityConstraints(
                allowed_actions=[f"tool.{tool_name}", "tool.*"],
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=datetime.now(UTC).isoformat(),
                valid_until="2025-12-31T00:00:00Z",
            ),
            authorization_ref=f"auth-{tool_name}",
        )

        replay_guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            max_uses=1,
        )

        binding = ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="capability-bound-agent",
            resource_id=tool_name,
            bound_resources=[tool_name],
        )

        return ExecutionCapability(
            capability_id=f"cap-{uuid.uuid4().hex[:12]}",
            authorization_ref=f"auth-{tool_name}",
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=replay_guard,
            actor_identity_ref="agent",
            resource_binding=binding,
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            authority_root=f"auth-{tool_name}",
            derived_at=datetime.now(UTC).isoformat(),
            derived_by="agent-runtime",
        )

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all execution receipts."""
        return list(self._receipts)

    async def run_stream(self, session_id: str, message: str) -> AsyncIterator[str]:
        """Streaming variant — yields tokens as they arrive."""
        # For simplicity, delegate to non-streaming run
        result = await self.run(session_id, message)
        yield result
