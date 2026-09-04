"""Layer 7: Auth — Local MCP Gateway.

Manages OAuth, API keys, token refresh, permission scoping across all tools the agent touches.
Self-hosted = owned. Composio hosted broker = rented.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Credentials:
    tool_name: str
    auth_type: str  # "oauth", "api_key", "basic"
    token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
    scopes: list[str] | None = None


@dataclass
class Request:
    tool_name: str
    method: str
    path: str
    headers: dict
    body: bytes | None = None


@dataclass
class Response:
    status_code: int
    headers: dict
    body: bytes


@dataclass
class AuditEntry:
    timestamp: str
    tool_name: str
    method: str
    path: str
    credential_used: str


@dataclass
class AuditTrail:
    entries: list[AuditEntry]


class AuthBroker(Protocol):
    async def register_tool(self, tool_name: str, credentials: Credentials) -> None: ...
    async def call(self, request: Request) -> Response: ...
    async def refresh(self, tool_name: str) -> None: ...
    async def audit(self) -> AuditTrail: ...
