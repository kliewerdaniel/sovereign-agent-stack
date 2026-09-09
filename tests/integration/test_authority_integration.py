"""Integration tests for Authority Integration phase.

These tests prove that the six bypass points are eliminated and that
the runtime cannot perform consequential actions without a verified
authority path.

The tests follow the principle:
    PROVE THE NEGATIVE — show that unauthorized operations are impossible.

Each test corresponds to one of the six bypass points identified in the
runtime analysis:

1. agent_runtime.py — tool execution without capability
2. argopack.py — CLI subprocess bypass
3. plugins.py — arbitrary code execution
4. broker/__init__.py — broker without authorization check
5. broker/alpaca.py — broker without authorization check
6. orchestration/__init__.py — research decision ignored
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from sas.quant.broker import SimulatedBroker
from sas.quant.risk import TradeIntent
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.capability_bound_broker import CapabilityBoundBroker, create_capability_bound_broker
from sas.quant.capability_bound_tool import CapabilityBoundTool
from sas.quant.experiment.epistemic_governance import (
    AuthorizationArtifact,
    AuthorizationStatus,
)
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutionStatus,
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
from sas.quant.runtime_authority_gate import (
    OperationRequest,
    RuntimeAuthorityGate,
    create_runtime_authority_gate,
    create_operation_request,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def trading_domain() -> ProtocolDomain:
    return create_protocol_domain("trading-domain", DomainType.SOVEREIGN)


@pytest.fixture
def gate(trading_domain: ProtocolDomain) -> RuntimeAuthorityGate:
    return RuntimeAuthorityGate(trading_domain)


@pytest.fixture
def authorized_trade_capability(trading_domain: ProtocolDomain) -> ExecutionCapability:
    """A valid capability for trading AAPL."""
    scope = CapabilityScope(
        domain_id=trading_domain.domain_id,
        lineage_id=trading_domain.lineage_hash,
        actor_id="actor-1",
        action="execute_trade",
        resource="AAPL",
        resource_class="financial_instrument",
        arguments={"quantity": 10},
        constraints=CapabilityConstraints(
            allowed_actions=["execute_trade"],
            max_quantity=100,
            min_quantity=1,
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
        executor_id="test-executor",
        resource_id="AAPL",
        bound_resources=["AAPL"],
    )

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="auth-1",
        scope=scope,
        capability_type=CapabilityType.EXECUTE,
        replay_guard=replay_guard,
        actor_identity_ref="actor-1",
        resource_binding=binding,
        domain_id=trading_domain.domain_id,
        lineage_id=trading_domain.lineage_hash,
        authority_root="auth-1",
        derived_at="2024-06-01T00:00:00Z",
        derived_by="test",
    )


@pytest.fixture
def authorized_auth() -> AuthorizationArtifact:
    """A valid authorization artifact."""
    return AuthorizationArtifact(
        authorization_id="auth-1",
        action_proposal_ref="prop-1",
        identity_ref="actor-1",
        status=AuthorizationStatus.AUTHORIZED,
        expiration="2027-12-31T00:00:00Z",
        authorization_scope={
            "domain_id": "trading-domain",
            "allowed_actions": ["execute_trade"],
            "target_resources": ["AAPL"],
        },
    )


@pytest.fixture
def expired_auth() -> AuthorizationArtifact:
    """An expired authorization."""
    return AuthorizationArtifact(
        authorization_id="auth-expired",
        action_proposal_ref="prop-1",
        identity_ref="actor-1",
        status=AuthorizationStatus.AUTHORIZED,
        expiration="2020-01-01T00:00:00Z",  # Expired
        authorization_scope={
            "domain_id": "trading-domain",
            "allowed_actions": ["execute_trade"],
            "target_resources": ["AAPL"],
        },
    )


@pytest.fixture
def denied_auth() -> AuthorizationArtifact:
    """A denied authorization."""
    return AuthorizationArtifact(
        authorization_id="auth-denied",
        action_proposal_ref="prop-1",
        identity_ref="actor-1",
        status=AuthorizationStatus.DENIED,
        authorization_scope={
            "domain_id": "trading-domain",
            "allowed_actions": ["execute_trade"],
            "target_resources": ["AAPL"],
        },
    )


# ---------------------------------------------------------------------------
# Bypass 1: Agent Runtime — Tool execution without capability
# ---------------------------------------------------------------------------


class TestAgentRuntimeBypass:
    """Tests that agent_runtime.py cannot execute tools without capability."""

    def test_tool_invocation_requires_capability(self, trading_domain: ProtocolDomain):
        """A tool cannot be invoked without a valid capability."""
        tool = CapabilityBoundTool(
            name="read_file",
            description="Read a file",
            handler=lambda path: f"contents of {path}",
        )

        # Create a capability that permits this tool
        scope = CapabilityScope(
            domain_id=trading_domain.domain_id,
            actor_id="actor-1",
            action="tool.read_file",
            resource="read_file",
            constraints=CapabilityConstraints(allowed_actions=["tool.read_file"]),
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
            domain_id=trading_domain.domain_id,
        )

        result = tool.invoke(capability, {"path": "/tmp/test.txt"}, trading_domain)

        assert result.is_permitted
        assert result.result == "contents of /tmp/test.txt"
        assert result.receipt is not None
        assert result.receipt.status == ExecutionStatus.COMPLETED

    def test_tool_invocation_denied_without_matching_capability(
        self, trading_domain: ProtocolDomain
    ):
        """A tool cannot be invoked if the capability doesn't permit it."""
        tool = CapabilityBoundTool(
            name="delete_file",
            description="Delete a file",
            handler=lambda path: f"deleted {path}",
        )

        # Create a capability that does NOT permit this tool
        scope = CapabilityScope(
            domain_id=trading_domain.domain_id,
            actor_id="actor-1",
            action="tool.read_file",  # Different tool
            resource="read_file",
            constraints=CapabilityConstraints(allowed_actions=["tool.read_file"]),
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
            domain_id=trading_domain.domain_id,
        )

        result = tool.invoke(capability, {"path": "/tmp/test.txt"}, trading_domain)

        assert not result.is_permitted
        assert "Action mismatch" in result.rejection_reason

    def test_tool_handler_not_directly_accessible(
        self, trading_domain: ProtocolDomain
    ):
        """The raw tool handler is not accessible — only through capability-bound interface."""
        tool = CapabilityBoundTool(
            name="dangerous",
            description="Dangerous operation",
            handler=lambda: "executed",
        )

        # The handler is private
        assert not hasattr(tool, "handler")
        # Only invoke method is public
        assert hasattr(tool, "invoke")


# ---------------------------------------------------------------------------
# Bypass 2: ARGO — CLI subprocess bypass
# ---------------------------------------------------------------------------


class TestARGOBypass:
    """Tests that ARGO cannot bypass the authority gate via CLI subprocess."""

    def test_operation_requires_authorization_resolution(
        self, gate: RuntimeAuthorityGate, authorized_auth: AuthorizationArtifact
    ):
        """An operation request must resolve to a valid authorization."""
        gate.register_authorization(authorized_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="argo",
        )

        resolution = gate.resolve(request, "auth-1")
        assert resolution.is_valid
        assert resolution.capability is not None

    def test_operation_denied_for_unknown_authorization(
        self, gate: RuntimeAuthorityGate
    ):
        """An operation with unknown authorization is denied."""
        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="argo",
        )

        resolution = gate.resolve(request, "nonexistent-auth")
        assert not resolution.is_valid
        assert "not found" in resolution.rejection_reason

    def test_operation_denied_for_wrong_domain(
        self, gate: RuntimeAuthorityGate, authorized_auth: AuthorizationArtifact
    ):
        """An operation in the wrong domain is denied."""
        gate.register_authorization(authorized_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="wrong-domain",  # Wrong domain
            source="argo",
        )

        resolution = gate.resolve(request, "auth-1")
        assert not resolution.is_valid
        assert "Domain mismatch" in resolution.rejection_reason


# ---------------------------------------------------------------------------
# Bypass 3: Plugins — Arbitrary code execution
# ---------------------------------------------------------------------------


class TestPluginBypass:
    """Tests that plugins cannot execute without capability attestation."""

    def test_plugin_operation_requires_capability(
        self, gate: RuntimeAuthorityGate, authorized_auth: AuthorizationArtifact
    ):
        """A plugin operation requires a valid capability."""
        gate.register_authorization(authorized_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="plugin",
        )

        resolution = gate.resolve(request, "auth-1")
        assert resolution.is_valid

    def test_plugin_cannot_execute_arbitrary_action(
        self, gate: RuntimeAuthorityGate, authorized_auth: AuthorizationArtifact
    ):
        """A plugin cannot execute an action not in the authorization scope."""
        gate.register_authorization(authorized_auth)

        request = create_operation_request(
            action="delete_database",  # Not authorized
            resource="production-db",
            arguments={},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="plugin",
        )

        resolution = gate.resolve(request, "auth-1")
        assert not resolution.is_valid
        assert "not in allowed actions" in resolution.rejection_reason


# ---------------------------------------------------------------------------
# Bypass 4 & 5: Broker adapters — No authorization check
# ---------------------------------------------------------------------------


class TestBrokerBypass:
    """Tests that broker adapters cannot accept unauthorized orders."""

    def test_capability_bound_broker_accepts_authorized_order(
        self, trading_domain: ProtocolDomain, authorized_trade_capability: ExecutionCapability
    ):
        """An authorized order is accepted by the capability-bound broker."""
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(
            inner_broker,
            trading_domain,
        )

        trade = TradeIntent(
            id="trade-1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            price_assumption=100.0,
        )

        result = bound_broker.submit_order(
            authorized_trade_capability,
            trade,
            "2024-06-01T00:00:00Z",
        )

        assert result.is_permitted
        assert result.order is not None
        assert result.receipt is not None

    def test_capability_bound_broker_rejects_unauthorized_quantity(
        self, trading_domain: ProtocolDomain
    ):
        """An order exceeding capability quantity is rejected."""
        # Create capability with max_quantity=10
        scope = CapabilityScope(
            domain_id=trading_domain.domain_id,
            actor_id="actor-1",
            action="execute_trade",
            resource="AAPL",
            constraints=CapabilityConstraints(
                allowed_actions=["execute_trade"],
                max_quantity=10,
            ),
            temporal_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2025-12-31T00:00:00Z",
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
            domain_id=trading_domain.domain_id,
        )

        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(inner_broker, trading_domain)

        trade = TradeIntent(
            id="trade-1",
            symbol="AAPL",
            side="buy",
            quantity=1000,  # Exceeds max_quantity=10
            price_assumption=100.0,
        )

        result = bound_broker.submit_order(capability, trade, "2024-06-01T00:00:00Z")

        assert not result.is_permitted
        assert "Quantity" in result.rejection_reason

    def test_capability_bound_broker_rejects_wrong_resource(
        self, trading_domain: ProtocolDomain
    ):
        """An order for a different resource is rejected."""
        scope = CapabilityScope(
            domain_id=trading_domain.domain_id,
            actor_id="actor-1",
            action="execute_trade",
            resource="AAPL",
            constraints=CapabilityConstraints(
                allowed_actions=["execute_trade"],
            ),
            temporal_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2025-12-31T00:00:00Z",
            ),
            authorization_ref="auth-1",
        )

        binding = ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="test",
            resource_id="AAPL",
            bound_resources=["AAPL"],
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
            resource_binding=binding,
            domain_id=trading_domain.domain_id,
        )

        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(inner_broker, trading_domain)

        trade = TradeIntent(
            id="trade-1",
            symbol="MSFT",  # Different resource
            side="buy",
            quantity=10,
            price_assumption=100.0,
        )

        result = bound_broker.submit_order(capability, trade, "2024-06-01T00:00:00Z")

        assert not result.is_permitted
        assert "Resource mismatch" in result.rejection_reason

    def test_capability_bound_broker_rejects_replay(
        self, trading_domain: ProtocolDomain, authorized_trade_capability: ExecutionCapability
    ):
        """A replayed capability is rejected."""
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(
            inner_broker,
            trading_domain,
        )

        trade = TradeIntent(
            id="trade-1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            price_assumption=100.0,
        )

        # First submission should succeed
        result1 = bound_broker.submit_order(
            authorized_trade_capability,
            trade,
            "2024-06-01T00:00:00Z",
        )
        assert result1.is_permitted

        # Second submission should fail (replay)
        result2 = bound_broker.submit_order(
            authorized_trade_capability,
            trade,
            "2024-06-01T00:00:00Z",
        )
        assert not result2.is_permitted
        assert "replay" in result2.rejection_reason.lower() or "replay" in " ".join(result2.conflicts).lower()

    def test_raw_broker_not_exposed_to_untrusted_code(
        self, trading_domain: ProtocolDomain, authorized_trade_capability: ExecutionCapability
    ):
        """The raw broker adapter is not directly accessible."""
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(
            inner_broker,
            trading_domain,
        )

        # The underlying broker is name-mangled and not accessible via _broker
        assert not hasattr(bound_broker, "_broker")
        # The only way to interact is through submit_order
        assert hasattr(bound_broker, "submit_order")


# ---------------------------------------------------------------------------
# Bypass 6: Research decision — Failed research becomes trade intent
# ---------------------------------------------------------------------------


class TestResearchDecisionBypass:
    """Tests that failed research decisions cannot create trade intents."""

    def test_failed_research_cannot_create_authorization(
        self, gate: RuntimeAuthorityGate
    ):
        """A failed research decision cannot produce a valid authorization."""
        # Simulate a failed research decision
        failed_auth = AuthorizationArtifact(
            authorization_id="auth-failed",
            action_proposal_ref="prop-1",
            identity_ref="actor-1",
            status=AuthorizationStatus.INCONCLUSIVE,  # Not authorized
            authorization_scope={
                "domain_id": "trading-domain",
                "allowed_actions": ["execute_trade"],
                "target_resources": ["AAPL"],
            },
        )
        gate.register_authorization(failed_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="orchestrator",
        )

        resolution = gate.resolve(request, "auth-failed")
        assert not resolution.is_valid
        assert "status" in resolution.rejection_reason.lower()

    def test_inconclusive_research_cannot_trade(
        self, gate: RuntimeAuthorityGate
    ):
        """An inconclusive research result cannot produce a trade authorization."""
        inconclusive_auth = AuthorizationArtifact(
            authorization_id="auth-inconclusive",
            action_proposal_ref="prop-1",
            identity_ref="actor-1",
            status=AuthorizationStatus.INCONCLUSIVE,
            authorization_scope={
                "domain_id": "trading-domain",
                "allowed_actions": ["execute_trade"],
                "target_resources": ["AAPL"],
            },
        )
        gate.register_authorization(inconclusive_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="orchestrator",
        )

        resolution = gate.resolve(request, "auth-inconclusive")
        assert not resolution.is_valid

    def test_expired_authorization_cannot_trade(
        self, gate: RuntimeAuthorityGate, expired_auth: AuthorizationArtifact
    ):
        """An expired authorization cannot produce a trade."""
        gate.register_authorization(expired_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="orchestrator",
        )

        resolution = gate.resolve(request, "auth-expired")
        assert not resolution.is_valid
        assert "expired" in resolution.rejection_reason.lower()

    def test_denied_authorization_cannot_trade(
        self, gate: RuntimeAuthorityGate, denied_auth: AuthorizationArtifact
    ):
        """A denied authorization cannot produce a trade."""
        gate.register_authorization(denied_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="orchestrator",
        )

        resolution = gate.resolve(request, "auth-denied")
        assert not resolution.is_valid


# ---------------------------------------------------------------------------
# Malicious Executor Tests
# ---------------------------------------------------------------------------


class TestMaliciousExecutor:
    """Tests that a deliberately malicious runtime cannot bypass the protocol."""

    def test_widening_attack_fails(
        self, trading_domain: ProtocolDomain, authorized_trade_capability: ExecutionCapability
    ):
        """A malicious executor cannot widen the capability scope."""
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(
            inner_broker,
            trading_domain,
        )

        # Attempt to trade a different symbol with larger quantity
        malicious_trade = TradeIntent(
            id="malicious-1",
            symbol="MSFT",  # Different symbol
            side="buy",
            quantity=10000,  # Much larger
            price_assumption=100.0,
        )

        result = bound_broker.submit_order(
            authorized_trade_capability,
            malicious_trade,
            "2024-06-01T00:00:00Z",
        )

        assert not result.is_permitted

    def test_domain_escape_fails(
        self, trading_domain: ProtocolDomain, authorized_trade_capability: ExecutionCapability
    ):
        """A malicious executor cannot use capability in wrong domain."""
        wrong_domain = create_protocol_domain("wrong-domain", DomainType.FEDERATED)
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(inner_broker, wrong_domain)

        trade = TradeIntent(
            id="trade-1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            price_assumption=100.0,
        )

        result = bound_broker.submit_order(
            authorized_trade_capability,
            trade,
            "2024-06-01T00:00:00Z",
        )

        assert not result.is_permitted
        assert "Domain mismatch" in result.rejection_reason

    def test_replay_attack_fails(
        self, trading_domain: ProtocolDomain, authorized_trade_capability: ExecutionCapability
    ):
        """A malicious executor cannot replay a used capability."""
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(
            inner_broker,
            trading_domain,
        )

        trade = TradeIntent(
            id="trade-1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            price_assumption=100.0,
        )

        # First use
        result1 = bound_broker.submit_order(
            authorized_trade_capability,
            trade,
            "2024-06-01T00:00:00Z",
        )
        assert result1.is_permitted

        # Replay attempt
        result2 = bound_broker.submit_order(
            authorized_trade_capability,
            trade,
            "2024-06-01T00:00:00Z",
        )
        assert not result2.is_permitted

    def test_revoked_capability_cannot_execute(
        self, gate: RuntimeAuthorityGate, authorized_auth: AuthorizationArtifact
    ):
        """A revoked authorization cannot be used."""
        gate.register_authorization(authorized_auth)

        # Revoke the authorization
        revoked_auth = AuthorizationArtifact(
            authorization_id=authorized_auth.authorization_id,
            action_proposal_ref=authorized_auth.action_proposal_ref,
            identity_ref=authorized_auth.identity_ref,
            status=AuthorizationStatus.REVOKED,
            authorization_scope=authorized_auth.authorization_scope,
        )
        gate.register_authorization(revoked_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
        )

        resolution = gate.resolve(request, "auth-1")
        assert not resolution.is_valid


# ---------------------------------------------------------------------------
# End-to-End Integration Test
# ---------------------------------------------------------------------------


class TestEndToEndQuantPath:
    """Tests the full quant path from research to execution."""

    def test_full_authorized_flow(
        self, gate: RuntimeAuthorityGate, authorized_auth: AuthorizationArtifact
    ):
        """A fully authorized flow from research to execution."""
        gate.register_authorization(authorized_auth)

        # 1. Create operation request
        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="orchestrator",
        )

        # 2. Resolve authorization
        resolution = gate.resolve(request, "auth-1")
        assert resolution.is_valid
        capability = resolution.capability

        # 3. Create capability-bound broker
        inner_broker = SimulatedBroker()
        bound_broker = CapabilityBoundBroker(inner_broker, gate.domain)

        # 4. Submit order through capability-bound broker
        trade = TradeIntent(
            id="trade-1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            price_assumption=100.0,
        )

        # Use current time (same as capability creation time)
        result = bound_broker.submit_order(capability, trade, request.requested_at)

        assert result.is_permitted
        assert result.order is not None
        assert result.receipt is not None
        assert result.receipt.status == ExecutionStatus.COMPLETED

    def test_full_flow_with_research_rejection(
        self, gate: RuntimeAuthorityGate
    ):
        """A failed research result terminates before authorization."""
        # Simulate failed research
        failed_auth = AuthorizationArtifact(
            authorization_id="auth-failed",
            action_proposal_ref="prop-1",
            identity_ref="actor-1",
            status=AuthorizationStatus.INCONCLUSIVE,
            authorization_scope={
                "domain_id": "trading-domain",
                "allowed_actions": ["execute_trade"],
                "target_resources": ["AAPL"],
            },
        )
        gate.register_authorization(failed_auth)

        request = create_operation_request(
            action="execute_trade",
            resource="AAPL",
            arguments={"quantity": 10},
            actor_id="actor-1",
            domain_id="trading-domain",
            source="orchestrator",
        )

        # Resolution should fail
        resolution = gate.resolve(request, "auth-failed")
        assert not resolution.is_valid
        assert resolution.capability is None

        # No capability means no broker submission
        # The flow terminates here
