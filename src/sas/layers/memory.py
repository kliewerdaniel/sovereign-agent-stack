"""Layer 5: Short-term Memory — Session context, rolling window, preference inference.

Runtime memory is re-derived every time — a fact you re-infer at token cost.
Owned if local RAG or self-hosted Honcho; rented if Honcho cloud tier.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Fact:
    content: str
    source: str
    timestamp: str
    relevance: float


@dataclass
class Observation:
    content: str
    session_id: str
    timestamp: str
    source: str = "user"


@dataclass
class Summary:
    session_id: str
    content: str
    updated_at: str


class ShortTermMemory(Protocol):
    async def recall(self, session_id: str, query: str) -> list[Fact]: ...
    async def update(self, observation: Observation) -> None: ...
    async def summarize(self, session_id: str) -> Summary: ...
