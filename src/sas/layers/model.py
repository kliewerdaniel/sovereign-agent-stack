"""Layer 1: Model — Raw next-token prediction.

This layer is a commodity. The intelligence is commoditized; the rent has moved up.
SAS uses Ollama local + API fallback, but the model layer is sovereignty-irrelevant.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ModelLocation(Enum):
    LOCAL = "local"
    API = "api"


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict


@dataclass
class Completion:
    content: str
    tool_calls: list[dict] | None = None
    usage: dict | None = None


@dataclass
class Token:
    content: str
    finish_reason: str | None = None


@dataclass
class ModelIdentity:
    name: str
    context_window: int
    location: ModelLocation
    provider: str


class ModelProvider(Protocol):
    async def complete(self, messages: list[Message], tools: list[Tool]) -> Completion: ...
    def stream(self, messages: list[Message], tools: list[Tool]) -> AsyncIterator[Token]: ...
    @property
    def identity(self) -> ModelIdentity: ...
