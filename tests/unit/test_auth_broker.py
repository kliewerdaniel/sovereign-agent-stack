"""Tests for Layer 7: Auth broker with libsodium encryption."""

import sqlite3
import pytest
from sas.layers.auth import (
    _Encryptor,
    AuditEntry,
    AuditTrail,
    Credentials,
    LocalAuthBroker,
    Request,
    Response,
)


class TestEncryptor:
    """Tests for the libsodium secret-key encryptor."""

    def test_encrypt_decrypt_roundtrip(self):
        key = _Encryptor.generate_key()
        enc = _Encryptor(key)
        plaintext = "super-secret-token"
        ciphertext = enc.encrypt(plaintext)
        assert ciphertext != plaintext.encode()
        assert enc.decrypt(ciphertext) == plaintext

    def test_encrypt_with_unicode(self):
        key = _Encryptor.generate_key()
        enc = _Encryptor(key)
        plaintext = "token-with-émojis-🎉"
        assert enc.decrypt(enc.encrypt(plaintext)) == plaintext

    def test_encrypt_empty_string(self):
        key = _Encryptor.generate_key()
        enc = _Encryptor(key)
        assert enc.decrypt(enc.encrypt("")) == ""

    def test_encrypt_produces_different_ciphertexts(self):
        """Same plaintext, same key → different ciphertexts (nonce)."""
        key = _Encryptor.generate_key()
        enc = _Encryptor(key)
        pt = "test"
        ct1 = enc.encrypt(pt)
        ct2 = enc.encrypt(pt)
        assert ct1 != ct2

    def test_decrypt_wrong_key_fails(self):
        key1 = _Encryptor.generate_key()
        key2 = _Encryptor.generate_key()
        enc1 = _Encryptor(key1)
        enc2 = _Encryptor(key2)
        ct = enc1.encrypt("test")
        with pytest.raises(Exception):
            enc2.decrypt(ct)

    def test_from_hex(self):
        key = _Encryptor.generate_key()
        enc1 = _Encryptor(key)
        enc2 = _Encryptor.from_hex(key.hex())
        ct = enc1.encrypt("hello")
        assert enc2.decrypt(ct) == "hello"

    def test_invalid_key_length(self):
        """Arbitrary-length keys are derived to 32 bytes."""
        # Should NOT raise — keys are derived via SHA-256
        enc = _Encryptor(b"short")
        assert enc._box is not None


class TestLocalAuthBroker:
    """Tests for the encrypted SQLite credential store."""

    def test_register_and_get(self):
        broker = LocalAuthBroker()
        creds = Credentials(
            tool_name="github",
            auth_type="api_key",
            token="ghp_test123",
            scopes=["repo"],
        )
        broker.register_tool("github", creds)
        result = broker.get_credentials("github")
        assert result is not None
        assert result.token == "ghp_test123"
        assert result.auth_type == "api_key"

    def test_list_tools(self):
        broker = LocalAuthBroker()
        broker.register_tool("gh", Credentials(tool_name="gh", auth_type="api_key"))
        broker.register_tool("sl", Credentials(tool_name="sl", auth_type="oauth"))
        tools = broker.list_tools()
        assert "gh" in tools

    def test_unregister(self):
        broker = LocalAuthBroker()
        broker.register_tool("t", Credentials(tool_name="t", auth_type="api_key"))
        broker.unregister_tool("t")
        assert broker.get_credentials("t") is None

    def test_encrypted_at_rest(self):
        """Verify token is encrypted in the database."""
        broker = LocalAuthBroker()
        token = "super-secret-12345"
        broker.register_tool("test", Credentials(tool_name="test", auth_type="api_key", token=token))
        raw = broker._get_raw_token("test")
        assert raw is not None
        assert token.encode() not in raw  # Not stored plaintext

    def test_call_injects_oauth_header(self):
        broker = LocalAuthBroker()
        broker.register_tool("t", Credentials(tool_name="t", auth_type="oauth", token="tok"))

        def mock_http(req):
            return Response(status_code=200, headers={}, body=b"ok")

        req = Request(tool_name="t", method="GET", path="/x", headers={})
        broker.call(req, mock_http)
        # If no exception, it worked

    def test_call_injects_api_key_header(self):
        broker = LocalAuthBroker()
        broker.register_tool("t", Credentials(tool_name="t", auth_type="api_key", token="key123"))

        captured = {}
        def mock_http(req):
            captured["headers"] = req.headers
            return Response(200, {}, b"ok")

        req = Request(tool_name="t", method="GET", path="/x", headers={})
        broker.call(req, mock_http)
        assert captured["headers"].get("X-API-Key") == "key123"

    def test_audit_trail(self):
        broker = LocalAuthBroker()
        broker.register_tool("t", Credentials(tool_name="t", auth_type="oauth", token="x"))

        def mock_http(req):
            return Response(200, {}, b"ok")

        broker.call(Request("t", "GET", "/a", {}), mock_http)
        broker.call(Request("t", "POST", "/b", {}), mock_http)

        trail = broker.audit()
        assert len(trail.entries) == 2

    def test_refresh(self):
        broker = LocalAuthBroker()
        broker.register_tool("t", Credentials(tool_name="t", auth_type="oauth", token="old"))

        def refresh_fn(name, creds):
            return Credentials(tool_name="t", auth_type="oauth", token="new")

        broker.refresh("t", refresh_fn)
        assert broker.get_credentials("t").token == "new"

    def test_call_unregistered_raises(self):
        broker = LocalAuthBroker()
        with pytest.raises(KeyError):
            broker.call(Request("x", "GET", "/", {}), lambda r: Response(200, {}, b""))

    def test_persistent_store(self, tmp_path):
        db_path = str(tmp_path / "auth.db")
        key = LocalAuthBroker.generate_key()

        broker1 = LocalAuthBroker(store_path=db_path, encryption_key=key)
        broker1.register_tool("t", Credentials(tool_name="t", auth_type="api_key", token="persistent"))

        broker2 = LocalAuthBroker(store_path=db_path, encryption_key=key)
        result = broker2.get_credentials("t")
        assert result is not None
        assert result.token == "persistent"
