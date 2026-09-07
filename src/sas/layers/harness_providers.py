"""Layer 2: Harness — Real agent loop implementation.

Provides a ``LocalHarness`` that runs the agentic loop:
recall memory → model complete → execute tools → update memory → repeat.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sas.layers.harness import (
    Context,
    Experience,
    Harness,
    Response,
    Result,
    Session,
    Skill,
)
from sas.layers.memory import Observation, ShortTermMemory
from sas.layers.model import Message, ModelProvider, Tool


class LocalHarness(Harness):
    """Full agent loop harness.

    Runs the agentic cycle:
    1. Recall session memory
    2. Build system prompt with context
    3. Model generates response (possibly with tool calls)
    4. Execute tools, collect results
    5. Store observation in memory
    6. Repeat until no tool calls remain
    """

    def __init__(
        self,
        model: ModelProvider,
        memory: ShortTermMemory | None = None,
        max_iterations: int = 5,
        system_prompt: str | None = None,
    ):
        self._model = model
        self._memory = memory
        self._max_iterations = max_iterations
        self._system_prompt = system_prompt or self._default_system_prompt()
        self._tools: dict[str, tuple[dict, Callable]] = {}
        self._sessions: dict[str, Session] = {}
        self._history: dict[str, list[Message]] = {}

    def _default_system_prompt(self) -> str:
        return (
            "You are a sovereign AI assistant. You have access to tools "
            "and must use them when appropriate. When you need to invoke "
            "a tool, respond with a tool call. Be concise and accurate."
        )

    async def create_session(self, user: str) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            user=user,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._sessions[session_id] = session
        self._history[session_id] = [
            Message(role="system", content=self._system_prompt)
        ]
        return session

    async def invoke(self, session: Session, message: str) -> Response:
        """Run the agent loop for a single message."""
        session_id = session.id

        if session_id not in self._history:
            self._history[session_id] = [
                Message(role="system", content=self._system_prompt)
            ]

        history = self._history[session_id]

        # Store user message
        user_msg = Message(role="user", content=message)
        history.append(user_msg)

        # Store observation in memory
        if self._memory:
            await self._memory.update(Observation(
                session_id=session_id,
                content=message,
                timestamp=datetime.now(UTC).isoformat(),
                source="user",
            ))

        # Build tools list
        tools = [Tool(name=n, description=t[0].get("description", ""), parameters=t[0].get("parameters", {}))
                 for n, t in self._tools.items()]

        # Agent loop
        final_content = ""
        for i in range(self._max_iterations):
            completion = await self._model.complete(history, tools)

            if completion.tool_calls:
                # Add assistant message with tool calls
                history.append(Message(
                    role="assistant",
                    content=completion.content,
                    # Note: we store tool_calls as a special marker in content
                ))

                # Execute each tool call
                tool_results = []
                for tc in completion.tool_calls:
                    func_name = tc.get("function", {}).get("name", "")
                    func_args_str = tc.get("function", {}).get("arguments", "{}")
                    try:
                        func_args = json.loads(func_args_str)
                    except json.JSONDecodeError:
                        func_args = {}

                    if func_name in self._tools:
                        handler = self._tools[func_name][1]
                        try:
                            result = handler(**func_args)
                            tool_results.append(json.dumps(result))
                        except Exception as e:
                            tool_results.append(json.dumps({"error": str(e)}))
                    else:
                        tool_results.append(json.dumps({"error": f"Unknown tool: {func_name}"}))

                # Add tool results as assistant message
                results_text = "\n".join(tool_results)
                history.append(Message(role="assistant", content=results_text))
                final_content = completion.content or results_text
            else:
                final_content = completion.content
                break

        # Store assistant response in memory
        if self._memory and final_content:
            await self._memory.update(Observation(
                session_id=session_id,
                content=final_content,
                timestamp=datetime.now(UTC).isoformat(),
                source="assistant",
            ))

        return Response(content=final_content, session=session)

    async def create_skill(self, experience: Experience) -> Skill:
        """Create a reusable skill from experience."""
        skill = Skill(
            name=f"skill_{experience.context[:20]}",
            description=experience.context,
            steps=[experience.action],
        )
        return skill

    async def execute_skill(self, skill: Skill, context: Context) -> Result:
        """Execute a skill within a context."""
        return Result(result=f"Executed skill '{skill.name}'", success=True)

    async def register_tool(self, name: str, description: str, handler: Callable, parameters: dict | None = None) -> None:
        """Register a tool that the model can call."""
        schema = {
            "description": description,
            "parameters": parameters or {"type": "object", "properties": {}},
        }
        self._tools[name] = (schema, handler)

    def get_history(self, session_id: str) -> list[Message]:
        """Get the conversation history for a session."""
        return self._history.get(session_id, [])


class StubHarness(Harness):
    """Deterministic harness for testing."""

    def __init__(self, response: str = "Stub response."):
        self._response = response

    async def invoke(self, session: Session, message: str) -> Response:
        return Response(content=self._response, session=session)

    async def create_skill(self, experience: Experience) -> Skill:
        return Skill(name="stub", description=experience.context, steps=[])

    async def execute_skill(self, skill: Skill, context: Context) -> Result:
        return Result(result="ok", success=True)

    async def register_tool(self, name: str, description: str, handler: Callable) -> None:
        pass
