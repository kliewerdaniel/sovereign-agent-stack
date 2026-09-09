"""Tests for the capability-bound auth broker.

Proves that credentials are never exposed to arbitrary callers and that
credential use requires a verified capability.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from sas.quant.capability_bound_auth import (
    CapabilityBoundAuthBroker,
    CredentialUseRequest,
    create_capability_bound_auth_broker,
)
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)
from sas.layers.auth import Credentials, LocalAuthBroker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_domain() -> ProtocolDomain:
    return create_protocol_domain("auth-domain", DomainType.SOVEREIGN)


@pytest.fixture
def wrong_domain() -> ProtocolDomain:
    return create_protocol_domain("wrong-domain", DomainType.FEDERATED)


@pytest.fixture
def local_auth_broker() -> LocalAuthBroker:
    broker = LocalAuthBroker()
    broker.register_tool("github", Credentials(
        tool_name="github",
        auth_type="oauth",
        token="test-token-12345",
    ))
    return broker


@pytest.fixture
def bound_auth_broker(
    local_auth_broker: LocalAuthBroker,
    auth_domain: ProtocolDomain,
) -> CapabilityBoundAuthBroker:
    return CapabilityBoundAuthBroker(local_auth_broker, auth_domain)


@pytest.fixture
def valid_credential_capability(
    auth_domain: ProtocolDomain,
) -> ExecutionCapability:
    scope = CapabilityScope(
        domain_id=auth_domain.domain_id,
        lineage_id=auth_domain.lineage_hash,
        actor_id="actor-1",
        action="credential.access",
        resource="github",
        constraints=CapabilityConstraints(
            allowed_actions=["credential.access"],
        ),
        temporal_interval=DomainValidityInterval(
            valid_from="2024-01-01T00:00:00Z",
            valid_until="2027-12-31T00:00:00Z",
        ),
        authorization_ref="auth-1",
    )

    replay_guard = ReplayGuard(
        guard_type=ReplayProtectionType.SINGLE_USE,
        nonce=f"nonce-{uuid.uuid4().hex[:12]}",
        max_uses=1,
    )

    binding = ExecutorBinding(
        binding_id=f"binding-{uuid.uuid4().hex[:12]}",
        executor_id="capability-bound-auth-broker",
        resource_id="github",
        bound_resources=["github"],
    )

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="auth-1",
        scope=scope,
        capability_type=CapabilityType.EXECUTE,
        replay_guard=replay_guard,
        actor_identity_ref="actor-1",
        resource_binding=binding,
        domain_id=auth_domain.domain_id,
        lineage_id=auth_domain.lineage_hash,
        authority_root="auth-1",
        derived_at="2024-06-01T00:00:00Z",
        derived_by="test",
    )


# ---------------------------------------------------------------------------
# Credential Access Tests
# ---------------------------------------------------------------------------


class TestCredentialAccess:
    """Tests that credential access is capability-bound."""

    def test_valid_capability_allows_access(
        self,
        bound_auth_broker: CapabilityBoundAuthBroker,
        valid_credential_capability: ExecutionCapability,
    ):
        """Valid capability → credential use permitted."""
        request = CredentialUseRequest(
            tool_name="github",
            method="GET",
            path="/user",
        )

        def mock_http_call(req):
            from sas.layers.auth import Response
            return Response(status_code=200, headers={}, body=b'{"login": "test"}')

        result = bound_auth_broker.use_credentials(
            valid_credential_capability,
            request,
            mock_http_call,
            "2024-06-01T00:00:00Z",
        )

        assert result.is_permitted
        assert result.response is not None
        assert result.receipt is not None

    def test_wrong_tool_rejected(
        self,
        bound_auth_broker: CapabilityBoundAuthBroker,
        valid_credential_capability: ExecutionCapability,
    ):
        """Wrong tool → rejection."""
        request = CredentialUseRequest(
            tool_name="gitlab",  # Not authorized
            method="GET",
            path="/user",
        )

        def mock_http_call(req):
            from sas.layers.auth import Response
            return Response(status_code=200, headers={}, body=b'{}')

        result = bound_auth_broker.use_credentials(
            valid_credential_capability,
            request,
            mock_http_call,
            "2024-06-01T00:00:00Z",
        )

        assert not result.is_permitted

    def test_wrong_domain_rejected(
        self,
        local_auth_broker: LocalAuthBroker,
        wrong_domain: ProtocolDomain,
        valid_credential_capability: ExecutionCapability,
    ):
        """Wrong domain → rejection."""
        broker = CapabilityBoundAuthBroker(local_auth_broker, wrong_domain)

        request = CredentialUseRequest(
            tool_name="github",
            method="GET",
            path="/user",
        )

        def mock_http_call(req):
            from sas.layers.auth import Response
            return Response(status_code=200, headers={}, body=b'{}')

        result = broker.use_credentials(
            valid_credential_capability,
            request,
            mock_http_call,
            "2024-06-01T00:00:00Z",
        )

        assert not result.is_permitted

    def test_credentials_never_exposed(
        self,
        bound_auth_broker: CapabilityBoundAuthBroker,
        valid_credential_capability: ExecutionCapability,
    ):
        """Credentials are NEVER returned to the caller."""
        request = CredentialUseRequest(
            tool_name="github",
            method="GET",
            path="/user",
        )

        def mock_http_call(req):
            from sas.layers.auth import Response
            return Response(status_code=200, headers={}, body=b'{"login": "test"}')

        result = bound_auth_broker.use_credentials(
            valid_credential_capability,
            request,
            mock_http_call,
            "2024-06-01T00:00:00Z",
        )

        # The result should NOT contain credential material
        assert result.is_permitted
        # No credential field in result
        assert not hasattr(result, "credentials")
        assert not hasattr(result, "token")
        # The receipt should NOT contain credential material
        if result.receipt:
            assert "token" not in result.receipt.observed_effect.lower()
            assert "test-token" not in result.receipt.observed_effect

    def test_receipt_does_not_contain_secrets(
        self,
        bound_auth_broker: CapabilityBoundAuthBroker,
        valid_credential_capability: ExecutionCapability,
    ):
        """Receipts must never contain credential material."""
        request = CredentialUseRequest(
            tool_name="github",
            method="GET",
            path="/user",
        )

        def mock_http_call(req):
            from sas.layers.auth import Response
            return Response(status_code=200, headers={}, body=b'{"login": "test"}')

        result = bound_auth_broker.use_credentials(
            valid_credential_capability,
            request,
            mock_http_call,
            "2024-06-01T00:00:00Z",
        )

        assert result.receipt is not None
        receipt = result.receipt
        # No secret material in any receipt field
        assert "test-token" not in str(receipt.__dict__)
        assert "12345" not in str(receipt.__dict__)


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------


class TestRegistration:
    """Tests that registration is capability-bound."""

    def test_registration_requires_authority_capability(
        self,
        local_auth_broker: LocalAuthBroker,
        auth_domain: ProtocolDomain,
    ):
        """Registration requires authority.mutation capability."""
        broker = CapabilityBoundAuthBroker(local_auth_broker, auth_domain)

        # Create a capability for authority mutation
        scope = CapabilityScope(
            domain_id=auth_domain.domain_id,
            actor_id="actor-1",
            action="authority.mutation",
            resource="new-tool",
            constraints=CapabilityConstraints(
                allowed_actions=["authority.mutation"],
            ),
            temporal_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2027-12-31T00:00:00Z",
            ),
            authorization_ref="auth-1",
        )

        capability = ExecutionCapability(
            capability_id=f"cap-{uuid.uuid4().hex[:12]}",
            authorization_ref="auth-1",
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=ReplayGuard(
                guard_type=ReplayProtectionType.SINGLE_USE,
                nonce=f"nonce-{uuid.uuid4().hex[:12]}",
            ),
            domain_id=auth_domain.domain_id,
        )

        creds = Credentials(
            tool_name="new-tool",
            auth_type="api_key",
            token="new-token",
        )

        result = broker.register_tool(
            capability,
            "new-tool",
            creds,
            "2024-06-01T00:00:00Z",
        )

        assert result.is_permitted
        assert result.receipt is not None

    def test_registration_without_authority_capability_rejected(
        self,
        local_auth_broker: LocalAuthBroker,
        auth_domain: ProtocolDomain,
        valid_credential_capability: ExecutionCapability,
    ):
        """Registration without authority.mutation → rejection."""
        broker = CapabilityBoundAuthBroker(local_auth_broker, auth_domain)

        creds = Credentials(
            tool_name="new-tool",
            auth_type="api_key",
            token="new-token",
        )

        result = broker.register_tool(
            valid_credential_capability,  # credential.access, not authority.mutation
            "new-tool",
            creds,
            "2024-06-01T00:00:00Z",
        )

        assert not result.is_permitted


# ---------------------------------------------------------------------------
# Raw Broker Inaccessible Tests
# ---------------------------------------------------------------------------


class TestRawBrokerInaccessible:
    """Tests that the raw broker is not accessible."""

    def test_raw_broker_not_exposed(
        self,
        bound_auth_broker: CapabilityBoundAuthBroker,
    ):
        """Raw broker is not accessible via public attributes."""
        assert not hasattr(bound_auth_broker, "broker")
        assert not hasattr(bound_auth_broker, "_broker")
        assert not hasattr(bound_auth_broker, "__broker")  # Name-mangled

    def test_get_credentials_not_exposed(
        self,
        bound_auth_broker: CapabilityBoundAuthBroker,
    ):
        """The raw get_credentials method is not accessible."""
        assert not hasattr(bound_auth_broker, "get_credentials")
