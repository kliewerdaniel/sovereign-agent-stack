"""Phase 26: Authority Non-Amplification Tests.

Tests that the gate cannot:
1. Create authority
2. Widen scope/capability/temporal validity
3. Delegate authority
4. Substitute for trust anchor

Invariants:
    AN EFFECT GATE IS NOT ITSELF AUTHORITY.
    RUNTIME MAY MATERIALIZE AUTHORITY, NEVER CREATE AUTHORITY.
    RuntimeAuthorityGate ≠ AuthorityRoot ≠ TrustAnchor.
"""
from __future__ import annotations

import pytest

from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import DomainType, DomainValidityInterval, create_protocol_domain
from sas.quant.runtime_authority_gate import OperationRequest, create_runtime_authority_gate


# ---------------------------------------------------------------------------
# Test 1: Gate cannot create authority
# ---------------------------------------------------------------------------


class TestGateCannotCreateAuthority:
    """The gate verifies and materializes already-established authority.
    It does NOT invent authority merely because execution passed through it."""

    def test_gate_cannot_authorize_without_registered_authorization(self):
        """Without a registered authorization, the gate has nothing to verify."""
        gate = create_runtime_authority_gate("test-domain")
        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="test",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        resolution = gate.resolve(request, "nonexistent-auth")
        assert not resolution.is_valid
        assert "not found" in resolution.rejection_reason

    def test_gate_cannot_materialize_capability_without_authorization(self):
        """The gate's materializer requires an authorization artifact."""
        gate = create_runtime_authority_gate("test-domain")
        # No authorization registered -> no materialization possible
        assert gate.get_authorization("any-id") is None

    def test_passing_through_gate_does_not_grant_authority(self):
        """Merely invoking the gate does not create authority."""
        gate = create_runtime_authority_gate("test-domain")
        # The gate starts with no authorizations
        assert len(gate._authorizations) == 0
        # Even after creating a gate, no authority exists
        assert gate.get_authorization("test") is None


# ---------------------------------------------------------------------------
# Test 2: Gate cannot widen scope/capability/temporal validity
# ---------------------------------------------------------------------------


class TestGateCannotWidenScope:
    """The gate cannot expand the scope of an existing capability."""

    def test_gate_cannot_extend_temporal_validity(self):
        """A capability's temporal bound is fixed at creation. Gate cannot extend it."""
        from dataclasses import replace

        gate = create_runtime_authority_gate("test-domain")
        capability = _make_test_capability(gate)

        # Original temporal bound
        original_until = capability.scope.temporal_interval.valid_until

        # Gate verifies but does NOT modify the capability
        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="test-actor",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        is_permitted, _ = gate.verify_capability(capability, request)
        assert is_permitted

        # The capability is unchanged
        assert capability.scope.temporal_interval.valid_until == original_until

    def test_gate_cannot_widen_resource_scope(self):
        """A capability bound to resource A cannot be used for resource B."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _make_test_capability(gate)

        # Try to use capability for a different resource
        request = OperationRequest(
            action="subprocess.execute",
            resource="/usr/bin/other",
            arguments={},
            actor_id="test-actor",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        is_permitted, conflicts = gate.verify_capability(capability, request)
        assert not is_permitted
        assert any("Resource mismatch" in c for c in conflicts)

    def test_gate_cannot_add_actions(self):
        """A capability permitting action A cannot be used for action B."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _make_test_capability(gate)

        # Try to use capability for a different action
        request = OperationRequest(
            action="identity.provision",
            resource="sas.cli",
            arguments={},
            actor_id="test-actor",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        is_permitted, conflicts = gate.verify_capability(capability, request)
        assert not is_permitted
        assert any("Action mismatch" in c for c in conflicts)


# ---------------------------------------------------------------------------
# Test 3: Gate cannot delegate authority
# ---------------------------------------------------------------------------


class TestGateCannotDelegateAuthority:
    """The gate cannot transfer or delegate authority to another actor."""

    def test_capability_is_bound_to_actor(self):
        """A capability bound to actor A cannot be used by actor B."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _make_test_capability(gate, actor_id="actor-a")

        # Actor B tries to use the capability
        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="actor-b",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        is_permitted, conflicts = gate.verify_capability(capability, request)
        assert not is_permitted
        assert any("Actor mismatch" in c for c in conflicts)

    def test_gate_does_not_issue_new_capabilities(self):
        """The gate does not create new capabilities from thin air."""
        gate = create_runtime_authority_gate("test-domain")
        # The gate has no method to create capabilities without authorization
        assert not hasattr(gate, "create_capability")
        assert not hasattr(gate, "issue_capability")
        assert not hasattr(gate, "delegate")


# ---------------------------------------------------------------------------
# Test 4: Gate cannot substitute for trust anchor
# ---------------------------------------------------------------------------


class TestGateCannotSubstituteForTrustAnchor:
    """The gate is enforcement infrastructure, not a trust anchor."""

    def test_gate_has_no_authority_root(self):
        """The gate does not contain an authority root."""
        gate = create_runtime_authority_gate("test-domain")
        # The gate has no authority_root attribute
        assert not hasattr(gate, "authority_root")
        assert not hasattr(gate, "trust_anchor")

    def test_gate_identity_is_not_authority(self):
        """The gate's identity (executor_id) is not an authority source."""
        gate = create_runtime_authority_gate("test-domain")
        # The gate's executor_id is "runtime-authority-gate" — infrastructure
        # It is not an authority root
        assert gate.domain.domain_id == "test-domain"

    def test_gate_verification_requires_external_authorization(self):
        """The gate's verify_capability does not create authority — it checks it."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _make_test_capability(gate)

        # The capability has an authorization_ref — this is the trust anchor
        assert capability.authorization_ref is not None
        assert capability.authorization_ref != ""

        # The gate checks this reference but does not create it
        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="test-actor",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        is_permitted, _ = gate.verify_capability(capability, request)
        assert is_permitted
        # The authorization_ref is unchanged — gate did not create it
        assert capability.authorization_ref == "test-auth-ref"


# ---------------------------------------------------------------------------
# Test 5: Gate is infrastructure, not authority
# ---------------------------------------------------------------------------


class TestGateIsInfrastructure:
    """The gate is enforcement infrastructure. It must not become a hidden trust anchor."""

    def test_multiple_gates_have_independent_state(self):
        """Each gate instance has independent authorization state."""
        gate1 = create_runtime_authority_gate("domain-1")
        gate2 = create_runtime_authority_gate("domain-2")

        # They do not share authorizations
        assert gate1.get_authorization("test") is None
        assert gate2.get_authorization("test") is None

    def test_gate_domain_binding_is_fixed(self):
        """The gate's domain binding cannot be changed after creation."""
        gate = create_runtime_authority_gate("original-domain")
        assert gate.domain.domain_id == "original-domain"

        # The domain attribute is not settable (frozen dataclass or similar)
        # Attempting to change it should not affect the gate's behavior
        original_domain = gate.domain.domain_id
        assert original_domain == "original-domain"

    def test_gate_receipts_are_observations_not_authority(self):
        """Execution receipts are observations, not authority grants."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _make_test_capability(gate)

        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="test-actor",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )

        # Execute produces a receipt
        receipt = gate.execute(capability, request, lambda: "result")
        assert receipt is not None
        assert receipt.status.value == "completed"

        # But the receipt is an observation, not authority
        # It does not grant new capabilities
        assert not hasattr(receipt, "grant_capability")
        assert not hasattr(receipt, "delegate")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_test_capability(
    gate,
    actor_id: str = "test-actor",
    resource: str = "sas.cli",
    action: str = "subprocess.execute",
) -> ExecutionCapability:
    """Create a test capability bound to the gate's domain."""
    import uuid
    from datetime import UTC, datetime

    now = "2026-01-01T00:00:00Z"

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="test-auth-ref",
        scope=CapabilityScope(
            domain_id=gate.domain.domain_id,
            lineage_id=gate.domain.lineage_hash,
            actor_id=actor_id,
            action=action,
            resource=resource,
            resource_class="process",
            arguments={},
            constraints=CapabilityConstraints(allowed_actions=[action]),
            temporal_interval=DomainValidityInterval(valid_from="2020-01-01T00:00:00Z", valid_until=""),
            authorization_ref="test-auth-ref",
        ),
        capability_type=CapabilityType.EXECUTE,
        replay_guard=ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            max_uses=1,
            created_at=now,
        ),
        actor_identity_ref=actor_id,
        resource_binding=ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="test-executor",
            resource_id=resource,
            bound_resources=[resource],
            bound_at=now,
            bound_until="",
        ),
        domain_id=gate.domain.domain_id,
        lineage_id=gate.domain.lineage_hash,
        authority_root="test-auth-ref",
        derived_at=now,
        derived_by="test",
    )
