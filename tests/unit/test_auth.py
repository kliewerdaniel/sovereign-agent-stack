"""Tests for the local auth broker / MCP gateway."""

import pytest

from sas.layers.auth import (
    AuditEntry,
    AuditTrail,
    Credentials,
    LocalAuthBroker,
    Request,
    Response,
)


class TestCredentials:
    """Tests for the Credentials dataclass."""

    def test_create_oauth_credentials(self) -> None:
        """OAuth credentials have token and refresh token."""
        creds = Credentials(
            tool_name="slack",
            auth_type="oauth",
            token="xoxb-123",
            refresh_token="xoxr-456",
            expires_at="2026-09-05T00:00:00",
            scopes=["channels:read", "chat:write"],
        )
        assert creds.tool_name == "slack"
        assert creds.auth_type == "oauth"
        assert creds.token == "xoxb-123"
        assert creds.refresh_token == "xoxr-456"

    def test_create_api_key_credentials(self) -> None:
        """API key credentials have only a token."""
        creds = Credentials(
            tool_name="github",
            auth_type="api_key",
            token="ghp_123456",
        )
        assert creds.tool_name == "github"
        assert creds.auth_type == "api_key"
        assert creds.token == "ghp_123456"
        assert creds.refresh_token is None


class TestLocalAuthBroker:
    """Tests for the local auth broker."""

    def test_register_tool(self) -> None:
        """Registering a tool stores its credentials."""
        broker = LocalAuthBroker(store_path=":memory:")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="xoxb-123")
        broker.register_tool("slack", creds)
        # Should not raise
        assert True

    def test_register_duplicate_tool_overwrites(self) -> None:
        """Registering the same tool twice overwrites credentials."""
        broker = LocalAuthBroker(store_path=":memory:")
        creds1 = Credentials(tool_name="slack", auth_type="oauth", token="old-token")
        creds2 = Credentials(tool_name="slack", auth_type="oauth", token="new-token")
        broker.register_tool("slack", creds1)
        broker.register_tool("slack", creds2)
        stored = broker.get_credentials("slack")
        assert stored is not None
        assert stored.token == "new-token"

    def test_get_credentials_returns_none_for_unknown(self) -> None:
        """Getting credentials for an unregistered tool returns None."""
        broker = LocalAuthBroker(store_path=":memory:")
        assert broker.get_credentials("unknown") is None

    def test_call_injects_credentials(self) -> None:
        """Calling a tool injects credentials into the request."""
        broker = LocalAuthBroker(store_path=":memory:")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="xoxb-123")
        broker.register_tool("slack", creds)

        request = Request(
            tool_name="slack",
            method="POST",
            path="/api/chat.postMessage",
            headers={"Content-Type": "application/json"},
            body=b'{"channel": "#general", "text": "hello"}',
        )

        # Mock the actual HTTP call
        called = []
        def mock_http_call(req: Request) -> Response:
            called.append(req)
            return Response(status_code=200, headers={}, body=b'{"ok": true}')

        response = broker.call(request, http_call=mock_http_call)

        assert response.status_code == 200
        assert len(called) == 1
        # Verify auth header was injected
        assert "Authorization" in called[0].headers
        assert called[0].headers["Authorization"] == "Bearer xoxb-123"

    def test_call_without_credentials_raises(self) -> None:
        """Calling an unregistered tool raises an error."""
        broker = LocalAuthBroker(store_path=":memory:")
        request = Request(
            tool_name="unknown",
            method="GET",
            path="/api/test",
            headers={},
        )
        with pytest.raises(KeyError):
            broker.call(request, http_call=lambda r: Response(200, {}, b""))

    def test_refresh_triggers_refresh(self) -> None:
        """Refresh triggers token refresh for a tool."""
        broker = LocalAuthBroker(store_path=":memory:")
        creds = Credentials(
            tool_name="slack",
            auth_type="oauth",
            token="old-token",
            refresh_token="refresh-123",
        )
        broker.register_tool("slack", creds)

        refreshed = []
        def mock_refresh(tool_name: str, creds: Credentials) -> Credentials:
            refreshed.append(tool_name)
            return Credentials(
                tool_name=tool_name,
                auth_type="oauth",
                token="new-token",
                refresh_token="new-refresh",
            )

        broker.refresh("slack", refresh_fn=mock_refresh)

        assert len(refreshed) == 1
        stored = broker.get_credentials("slack")
        assert stored is not None
        assert stored.token == "new-token"

    def test_audit_trail(self) -> None:
        """Audit trail records all tool calls."""
        broker = LocalAuthBroker(store_path=":memory:")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="xoxb-123")
        broker.register_tool("slack", creds)

        request = Request(
            tool_name="slack",
            method="POST",
            path="/api/chat.postMessage",
            headers={},
            body=b'{"text": "hello"}',
        )

        def mock_http_call(req: Request) -> Response:
            return Response(status_code=200, headers={}, body=b'{"ok": true}')

        broker.call(request, http_call=mock_http_call)

        trail = broker.audit()
        assert len(trail.entries) == 1
        entry = trail.entries[0]
        assert entry.tool_name == "slack"
        assert entry.method == "POST"
        assert entry.path == "/api/chat.postMessage"

    def test_audit_trail_multiple_calls(self) -> None:
        """Audit trail records multiple calls in order."""
        broker = LocalAuthBroker(store_path=":memory:")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="xoxb-123")
        broker.register_tool("slack", creds)

        def mock_http_call(req: Request) -> Response:
            return Response(status_code=200, headers={}, body=b'{"ok": true}')

        for i in range(3):
            request = Request(
                tool_name="slack",
                method="POST",
                path=f"/api/call{i}",
                headers={},
                body=b"{}",
            )
            broker.call(request, http_call=mock_http_call)

        trail = broker.audit()
        assert len(trail.entries) == 3
        assert trail.entries[0].path == "/api/call0"
        assert trail.entries[2].path == "/api/call2"

    def test_list_tools(self) -> None:
        """List tools returns all registered tool names."""
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("slack", Credentials("slack", "oauth", token="t1"))
        broker.register_tool("github", Credentials("github", "api_key", token="t2"))
        tools = broker.list_tools()
        assert set(tools) == {"slack", "github"}

    def test_unregister_tool(self) -> None:
        """Unregistering a tool removes its credentials."""
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("slack", Credentials("slack", "oauth", token="t1"))
        broker.unregister_tool("slack")
        assert broker.get_credentials("slack") is None
        assert broker.list_tools() == []


class TestEncryption:
    """Tests for credential encryption."""

    def test_credentials_encrypted_at_rest(self) -> None:
        """Credentials are encrypted when stored."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="test-key")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="secret-token")
        broker.register_tool("slack", creds)

        # The raw stored value should not contain the plaintext token
        raw = broker._get_raw_token("slack")
        assert raw is not None
        assert b"secret-token" not in raw

    def test_credentials_decrypted_on_retrieval(self) -> None:
        """Credentials are decrypted when retrieved."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="test-key")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="secret-token")
        broker.register_tool("slack", creds)

        stored = broker.get_credentials("slack")
        assert stored is not None
        assert stored.token == "secret-token"

    def test_different_keys_produce_different_ciphertexts(self) -> None:
        """Different encryption keys produce different ciphertexts."""
        broker1 = LocalAuthBroker(store_path=":memory:", encryption_key="key1")
        broker2 = LocalAuthBroker(store_path=":memory:", encryption_key="key2")
        creds = Credentials(tool_name="slack", auth_type="oauth", token="secret")
        broker1.register_tool("slack", creds)
        broker2.register_tool("slack", creds)

        raw1 = broker1._get_raw_token("slack")
        raw2 = broker2._get_raw_token("slack")
        assert raw1 != raw2
