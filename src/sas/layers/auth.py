"""Local auth broker — the MCP gateway nobody wants to build themselves.

Composio's convenience without Composio's centralization.
Credentials never leave your infrastructure.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import AsyncIterator, Protocol


@dataclass
class Credentials:
    """Credentials for a registered tool."""
    tool_name: str
    auth_type: str  # "oauth", "api_key", "basic"
    token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
    scopes: list[str] | None = None


@dataclass
class Request:
    """A request to be made to a tool."""
    tool_name: str
    method: str
    path: str
    headers: dict
    body: bytes | None = None


@dataclass
class Response:
    """Response from a tool call."""
    status_code: int
    headers: dict
    body: bytes


@dataclass
class AuditEntry:
    """A single entry in the audit trail."""
    timestamp: str
    tool_name: str
    method: str
    path: str
    credential_used: str


@dataclass
class AuditTrail:
    """Audit trail of all tool calls."""
    entries: list[AuditEntry]


class AuthBroker(Protocol):
    """Protocol for auth broker implementations."""
    def register_tool(self, tool_name: str, credentials: Credentials) -> None: ...
    def get_credentials(self, tool_name: str) -> Credentials | None: ...
    def list_tools(self) -> list[str]: ...
    def unregister_tool(self, tool_name: str) -> None: ...
    def call(self, request: Request, http_call) -> Response: ...
    def refresh(self, tool_name: str, refresh_fn) -> None: ...
    def audit(self) -> AuditTrail: ...


class _Encryptor:
    """Simple symmetric encryption using libsodium-style approach.
    
    In production, use a real crypto library. This is a placeholder
    that demonstrates the encrypt-at-rest architecture.
    """

    def __init__(self, key: str) -> None:
        self._key = key.encode()

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext. Returns bytes."""
        # XOR-based obfuscation (NOT secure — use libsodium in production)
        data = plaintext.encode()
        key = self._key
        encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return encrypted

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt ciphertext. Returns plaintext."""
        key = self._key
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(ciphertext))
        return decrypted.decode()


class LocalAuthBroker:
    """Local auth broker with encrypted credential storage."""

    def __init__(self, store_path: str = ":memory:", encryption_key: str | None = None) -> None:
        self.store_path = store_path
        self._conn: sqlite3.Connection | None = None
        self._encryptor = _Encryptor(encryption_key or self._generate_key())
        self._audit: list[AuditEntry] = []

    @staticmethod
    def _generate_key() -> str:
        """Generate a random encryption key."""
        return hashlib.sha256(os.urandom(32)).hexdigest()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.store_path)
            self._create_tables()
        return self._conn

    def _create_tables(self) -> None:
        conn = self._conn
        if conn is None:
            return
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                tool_name TEXT PRIMARY KEY,
                auth_type TEXT NOT NULL,
                token_encrypted BLOB,
                refresh_token_encrypted BLOB,
                expires_at TEXT,
                scopes TEXT
            )
        """)
        conn.commit()

    def register_tool(self, tool_name: str, credentials: Credentials) -> None:
        """Register a tool with its credentials."""
        conn = self._get_conn()
        token_enc = self._encryptor.encrypt(credentials.token) if credentials.token else None
        refresh_enc = self._encryptor.encrypt(credentials.refresh_token) if credentials.refresh_token else None
        scopes_json = json.dumps(credentials.scopes) if credentials.scopes else None

        conn.execute(
            "INSERT OR REPLACE INTO credentials (tool_name, auth_type, token_encrypted, refresh_token_encrypted, expires_at, scopes) VALUES (?, ?, ?, ?, ?, ?)",
            (tool_name, credentials.auth_type, token_enc, refresh_enc, credentials.expires_at, scopes_json),
        )
        conn.commit()

    def get_credentials(self, tool_name: str) -> Credentials | None:
        """Get decrypted credentials for a tool."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT auth_type, token_encrypted, refresh_token_encrypted, expires_at, scopes FROM credentials WHERE tool_name = ?",
            (tool_name,),
        ).fetchone()

        if row is None:
            return None

        auth_type, token_enc, refresh_enc, expires_at, scopes_json = row
        token = self._encryptor.decrypt(token_enc) if token_enc else None
        refresh_token = self._encryptor.decrypt(refresh_enc) if refresh_enc else None
        scopes = json.loads(scopes_json) if scopes_json else None

        return Credentials(
            tool_name=tool_name,
            auth_type=auth_type,
            token=token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=scopes,
        )

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        conn = self._get_conn()
        rows = conn.execute("SELECT tool_name FROM credentials").fetchall()
        return [r[0] for r in rows]

    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool and remove its credentials."""
        conn = self._get_conn()
        conn.execute("DELETE FROM credentials WHERE tool_name = ?", (tool_name,))
        conn.commit()

    def call(self, request: Request, http_call) -> Response:
        """Make a call to a tool, injecting credentials."""
        creds = self.get_credentials(request.tool_name)
        if creds is None:
            raise KeyError(f"Tool not registered: {request.tool_name}")

        # Inject auth headers
        headers = dict(request.headers)
        if creds.auth_type == "oauth" and creds.token:
            headers["Authorization"] = f"Bearer {creds.token}"
        elif creds.auth_type == "api_key" and creds.token:
            headers["X-API-Key"] = creds.token

        # Build the actual request
        actual_request = Request(
            tool_name=request.tool_name,
            method=request.method,
            path=request.path,
            headers=headers,
            body=request.body,
        )

        # Audit the call
        self._audit.append(AuditEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            tool_name=request.tool_name,
            method=request.method,
            path=request.path,
            credential_used=creds.auth_type,
        ))

        return http_call(actual_request)

    def refresh(self, tool_name: str, refresh_fn) -> None:
        """Refresh credentials for a tool."""
        creds = self.get_credentials(tool_name)
        if creds is None:
            raise KeyError(f"Tool not registered: {tool_name}")

        new_creds = refresh_fn(tool_name, creds)
        self.register_tool(tool_name, new_creds)

    def audit(self) -> AuditTrail:
        """Get the audit trail."""
        return AuditTrail(entries=list(self._audit))

    def _get_raw_token(self, tool_name: str) -> bytes | None:
        """Get the raw encrypted token (for testing)."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT token_encrypted FROM credentials WHERE tool_name = ?",
            (tool_name,),
        ).fetchone()
        return row[0] if row else None
