"""Layer 2b: Agent Runtime — Full agentic loop.

Binds the model, memory, and harness into a working agent that can:
1. Receive user input
2. Recall relevant session memory
3. Invoke the model (with tool calls)
4. Execute tools and update memory
5. Repeat until the model produces a text-only response
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sas.layers.memory import Observation, ShortTermMemory
from sas.layers.model import Message, ModelProvider, Tool


class AgentRuntime:
    """Full agentic loop: model ↔ memory ↔ tool execution."""

    def __init__(
        self,
        model: ModelProvider,
        memory: ShortTermMemory,
        max_tool_rounds: int = 5,
        system_prompt: str | None = None,
    ):
        self._model = model
        self._memory = memory
        self._max_tool_rounds = max_tool_rounds
        self._system_prompt = system_prompt or self._default_system_prompt()
        self._tools: dict[str, dict] = {}
        self._sessions: dict[str, AgentSession] = {}

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
        """Register a callable tool."""
        self._tools[name] = {
            "description": description,
            "handler": handler,
            "parameters": parameters or {"type": "object", "properties": {}},
        }

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
        """Run the agent loop for a user message. Returns the final response text."""
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
            Tool(name=t["description"], description=t["description"], parameters=t["parameters"])
            for t in self._tools.values()
        ]

        # Agent loop
        final_text = ""
        for round_i in range(self._max_tool_rounds):
            completion = await self._model.complete(history, tools)

            if completion.tool_calls:
                # Append assistant message with tool calls
                tc_text = "\n".join(
                    f"[Tool call: {tc.get('function', {}).get('name', '?')}({tc.get('function', {}).get('arguments', '{}')})"
                    for tc in completion.tool_calls
                )
                history.append(Message(role="assistant", content=tc_text))

                # Execute tools
                tool_results = []
                for tc in completion.tool_calls:
                    func_name = tc.get("function", {}).get("name", "")
                    args_str = tc.get("function", {}).get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if args_str else {}
                    except json.JSONDecodeError:
                        args = {}

                    tool_entry = self._tools.get(func_name)
                    if tool_entry:
                        try:
                            result = tool_entry["handler"](**args)
                            tool_results.append(json.dumps(result, default=str))
                        except Exception as e:
                            tool_results.append(json.dumps({"error": str(e)}))
                    else:
                        tool_results.append(json.dumps({"error": f"Unknown tool: {func_name}"}))

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

    async def run_stream(self, session_id: str, message: str) -> AsyncIterator[str]:
        """Streaming variant — yields tokens as they arrive."""
        if session_id not in self._sessions:
            session_id = await self.create_session("default")

        session = self._sessions[session_id]
        history = session.history

        facts = await self._memory.recall(session_id, message)
        if facts:
            context = "\n".join(f"- {f.content}" for f in facts)
            history.append(Message(role="system", content=f"Context from memory:\n{context}"))

        history.append(Message(role="user", content=message))
        await self._memory.update(Observation(
            session_id=session_id,
            content=message,
            timestamp=datetime.now(UTC).isoformat(),
            source="user",
        ))

        tools = [
            Tool(name=t["description"], description=t["description"], parameters=t["parameters"])
            for t in self._tools.values()
        ]

        # For streaming, we use a non-streaming complete to keep the loop simple
        final_text = ""
        for round_i in range(self._max_tool_rounds):
            completion = await self._model.complete(history, tools)

            if completion.tool_calls:
                tc_text = "\n".join(
                    f"[Tool call: {tc.get('function', {}).get('name', '?')}({tc.get('function', {}).get('arguments', '{}')})"
                    for tc in completion.tool_calls
                )
                history.append(Message(role="assistant", content=tc_text))

                tool_results = []
                for tc in completion.tool_calls:
                    func_name = tc.get("function", {}).get("name", "")
                    args_str = tc.get("function", {}).get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if args_str else {}
                    except json.JSONDecodeError:
                        args = {}

                    tool_entry = self._tools.get(func_name)
                    if tool_entry:
                        try:
                            result = tool_entry["handler"](**args)
                            tool_results.append(json.dumps(result, default=str))
                        except Exception as e:
                            tool_results.append(json.dumps({"error": str(e)}))
                    else:
                        tool_results.append(json.dumps({"error": f"Unknown tool: {func_name}"}))

                results_text = "\n".join(tool_results)
                history.append(Message(role="assistant", content=results_text))
                final_text = completion.content or results_text
            else:
                final_text = completion.content
                history.append(Message(role="assistant", content=final_text))
                break

        await self._memory.update(Observation(
            session_id=session_id,
            content=final_text,
            timestamp=datetime.now(UTC).isoformat(),
            source="assistant",
        ))

        yield final_text


@dataclass
class AgentSession:
    """Session state for the agent runtime."""
    id: str
    user: str
    history: list[Message] = field(default_factory=list)
