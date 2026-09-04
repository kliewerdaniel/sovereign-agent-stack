"""Layer 2: Harness — Orchestration around the model.

The harness is MIT-licensed and self-hostable. ARGO provides the base.
SAS extends it with the compile-time knowledge graph, local auth broker, and payments abstraction.
"""

from dataclasses import dataclass
from typing import AsyncIterator, Protocol


@dataclass
class Session:
    id: str
    user: str
    created_at: str


@dataclass
class Response:
    content: str
    session: Session


@dataclass
class Skill:
    name: str
    description: str
    steps: list[str]


@dataclass
class Experience:
    context: str
    action: str
    outcome: str


@dataclass
class Context:
    session: Session
    variables: dict


@dataclass
class Result:
    result: str
    success: bool


class Harness(Protocol):
    async def invoke(self, session: Session, message: str) -> Response: ...
    async def create_skill(self, experience: Experience) -> Skill: ...
    async def execute_skill(self, skill: Skill, context: Context) -> Result: ...
    async def register_tool(self, name: str, description: str, handler: callable) -> None: ...
