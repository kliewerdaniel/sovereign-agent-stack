# — Unit tests for the Local Auth Broker (Phase 3) —

import pytest
from pathlib import Path
import tempfile

from sas.layers.auth import (
    AuditEntry,
    AuditTrail,
    AuthBroker,
    Credentials,
    LocalAuthBroker,
    Request,
    Response,
)


# ── _Encryptor ────────────────────────────────────────────────────────────────

class TestEncryptor:
    def test_encrypt_decrypt_roundtrip(self):
        from sas.layers.auth import _Encryptor
        enc = _Encryptor("test-key-123")
        plaintext = "super-secret-token"
        ciphertext = enc.encrypt(plaintext)
        assert ciphertext != plaintext.encode()
        assert enc.decrypt(ciphertext) == plaintext

    def test_different_keys_produce_different_ciphertext(self):
        from sas.layers.auth import _Encryptor
        enc1 = _Encryptor("key-A")
        enc2 = _Encryptor("key-B")
        ct1 = enc1.encrypt("token")
        ct2 = enc2.encrypt("token")
        assert ct1 != ct2

    def test_empty_string(self):
        from sas.layers.auth import _Encryptor
        enc = _Encryptor("key")
        assert enc.decrypt(enc.encrypt("")) == ""


# ── LocalAuthBroker ────────────────────────────────────────────────────────────

class TestLocalAuthBroker:
    def test_register_and_get_credentials(self):
        broker = LocalAuthBroker(store_path=":memory:")
        creds = Credentials(
            tool_name="github",
            auth_type="oauth",
            token="ghp_123456",
            refresh_token="r_789",
            scopes=["repo", "user"],
        )
        broker.register_tool("github", creds)
        retrieved = broker.get_credentials("github")
        assert retrieved is not None
        assert retrieved.token == "ghp_123456"
        assert retrieved.refresh_token == "r_789"
        assert retrieved.scopes == ["repo", "user"]

    def test_get_credentials_unknown_tool_returns_none(self):
        broker = LocalAuthBroker(store_path=":memory:")
        assert broker.get_credentials("nonexistent") is None

    def test_list_tools(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="t1"))
        broker.register_tool("slack", Credentials(tool_name="slack", auth_type="api_key", token="t2"))
        tools = broker.list_tools()
        assert set(tools) == {"github", "slack"}

    def test_unregister_tool(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="t"))
        broker.unregister_tool("github")
        assert broker.get_credentials("github") is None
        assert broker.list_tools() == []

    def test_register_overwrites_existing(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="old"))
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="new"))
        assert broker.get_credentials("github").token == "new"

    def test_encryption_at_rest(self):
        """Verify tokens are encrypted in the store."""
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="secret"))
        raw = broker._get_raw_token("github")
        assert raw is not None
        assert b"secret" not in raw  # Not stored as plaintext

    def test_call_injects_oauth_header(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="my-token"))

        captured = {}

        def mock_http_call(request: Request) -> Response:
            captured["headers"] = request.headers
            return Response(status_code=200, headers={}, body=b"ok")

        req = Request(tool_name="github", method="GET", path="/repos", headers={})
        resp = broker.call(req, mock_http_call)
        assert resp.status_code == 200
        assert captured["headers"]["Authorization"] == "Bearer my-token"

    def test_call_injects_api_key_header(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("stripe", Credentials(tool_name="stripe", auth_type="api_key", token="sk_123"))

        captured = {}

        def mock_http_call(request: Request) -> Response:
            captured["headers"] = request.headers
            return Response(status_code=200, headers={}, body=b"ok")

        req = Request(tool_name="stripe", method="POST", path="/charges", headers={})
        broker.call(req, mock_http_call)
        assert captured["headers"]["X-API-Key"] == "sk_123"

    def test_call_unknown_tool_raises(self):
        broker = LocalAuthBroker(store_path=":memory:")
        req = Request(tool_name="unknown", method="GET", path="/", headers={})
        with pytest.raises(KeyError, match="Tool not registered"):
            broker.call(req, lambda r: Response(200, {}, b""))

    def test_audit_trail(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="t"))

        def mock_http_call(request: Request) -> Response:
            return Response(200, {}, b"")

        broker.call(Request("github", "GET", "/repos", {}), mock_http_call)
        broker.call(Request("github", "POST", "/repos", {}), mock_http_call)

        trail = broker.audit()
        assert len(trail.entries) == 2
        assert trail.entries[0].tool_name == "github"
        assert trail.entries[0].method == "GET"
        assert trail.entries[1].method == "POST"

    def test_refresh(self):
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="old"))

        def refresh_fn(tool_name, creds):
            return Credentials(tool_name=tool_name, auth_type="oauth", token="refreshed")

        broker.refresh("github", refresh_fn)
        assert broker.get_credentials("github").token == "refreshed"

    def test_refresh_unknown_tool_raises(self):
        broker = LocalAuthBroker(store_path=":memory:")
        with pytest.raises(KeyError):
            broker.refresh("unknown", lambda t, c: c)


# ── Persistence ────────────────────────────────────────────────────────────────

class TestPersistence:
    def test_credentials_persist_to_disk(self, tmp_path):
        store = tmp_path / "auth.db"
        broker = LocalAuthBroker(store_path=str(store))
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="disk-token"))
        # Reopen from disk
        broker2 = LocalAuthBroker(store_path=str(store), encryption_key=broker._encryptor._key.decode())
        retrieved = broker2.get_credentials("github")
        assert retrieved is not None
        assert retrieved.token == "disk-token"

    def test_separate_broker_instances_share_store(self, tmp_path):
        store = tmp_path / "shared.db"
        broker1 = LocalAuthBroker(store_path=str(store))
        broker1.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="shared"))
        broker2 = LocalAuthBroker(store_path=str(store), encryption_key=broker1._encryptor._key.decode())
        assert broker2.get_credentials("github").token == "shared"
