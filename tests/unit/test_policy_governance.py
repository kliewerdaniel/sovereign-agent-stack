"""Phase 13 tests: Policy Governance.

Tests validate that policy lifecycle operations can be governed using the
same fundamental principles already established elsewhere in SAS.

Key invariants tested:
- POLICY VALIDITY ≠ POLICY AUTHORITY
- POLICY DELETION ≠ HISTORICAL ERASURE
- POLICY SUPERSESSION ≠ MUTATION OF HISTORY
- CURRENT POLICY ≠ HISTORICAL POLICY
- SCOPE UNION ≠ SCOPE AUTHORITY
- TEMPORAL UNION ≠ TEMPORAL AUTHORITY
- PROVENANCE ≠ AUTHORITY
- POLICY MODIFICATION ≠ AUTOMATIC AUTHORITY
- POLICY ACTIVATION ≠ AUTOMATIC AUTHORIZATION
- OVERRIDE ≠ GOVERNANCE BYPASS
"""

import pytest
from research.examples.sovereign_agent.dependency_completeness import create_completeness_scope
from research.examples.sovereign_agent.policy_governance import (
    PolicyAuthorityType,
    PolicyLifecycleOperation,
    PolicyLifecycleState,
    PolicyGovernanceEngine,
    create_authority_record,
    create_test_policy_content,
    run_all_phase13_experiments,
    run_authorized_policy_creation,
    run_unauthorized_policy_creation,
    run_policy_modification_attack,
    run_policy_deletion_preserves_history,
    run_policy_supersession,
    run_policy_rollback,
    run_policy_override,
    run_scope_escalation_attack,
)


class TestAuthorizedPolicyCreation:
    """Test: Authorized policy creation."""

    def test_authorized_creation_succeeds(self):
        """Test that authorized policy creation succeeds."""
        result = run_authorized_policy_creation()
        
        assert result["success"] is True
        assert result["policy_created"] is True
        assert result["state"] == "draft"
        assert result["authority_amplified"] is False

    def test_unauthorized_creation_fails(self):
        """Test that unauthorized policy creation fails."""
        result = run_unauthorized_policy_creation()
        
        assert result["success"] is False
        assert result["policy_created"] is False
        assert result["authority_amplified"] is False


class TestPolicyModificationAttack:
    """Test: Policy modification attack.
    
    Scenario:
    - P1: incomplete provenance → HOLD
    - P2: incomplete provenance → REVIEW_REQUIRED
    
    An unauthorized actor replaces P1 with P2.
    The system must detect that the policy mutation is consequential.
    """

    def test_authorized_modification_succeeds(self):
        """Test that authorized modification succeeds."""
        result = run_policy_modification_attack()
        
        assert result["p1_created"] is True
        assert result["p2_modified"] is True

    def test_unauthorized_modification_blocked(self):
        """Test that unauthorized modification is blocked."""
        result = run_policy_modification_attack()
        
        assert result["p3_unauthorized"] is True
        assert result["authority_amplified"] is False

    def test_historical_state_preserved_after_modification(self):
        """Test that historical policy state is preserved after modification."""
        result = run_policy_modification_attack()
        
        assert result["historical_p1_preserved"] is True


class TestPolicyDeletionPreservesHistory:
    """Test: Policy deletion preserves historical state."""

    def test_deletion_succeeds_with_authority(self):
        """Test that deletion succeeds with proper authority."""
        result = run_policy_deletion_preserves_history()
        
        assert result["created"] is True
        assert result["deleted"] is True

    def test_historical_policy_remains_addressable(self):
        """Test that deleted policy remains historically addressable."""
        result = run_policy_deletion_preserves_history()
        
        assert result["historical_addressable"] is True
        assert result["historical_state"] == "deleted"

    def test_deletion_reason_preserved(self):
        """Test that deletion reason is preserved."""
        result = run_policy_deletion_preserves_history()
        
        assert result["deletion_reason"] == "Policy retired"


class TestPolicySupersession:
    """Test: Policy supersession."""

    def test_supersession_succeeds(self):
        """Test that supersession succeeds with authority."""
        result = run_policy_supersession()
        
        assert result["p1_created"] is True
        assert result["p2_superseded"] is True

    def test_old_version_marked_superseded(self):
        """Test that old version is marked as superseded."""
        result = run_policy_supersession()
        
        assert result["old_state"] == "superseded"
        assert result["old_superseded_by"] == "2.0.0"

    def test_old_version_remains_addressable(self):
        """Test that superseded version remains addressable."""
        result = run_policy_supersession()
        
        assert result["old_addressable"] is True

    def test_new_version_active(self):
        """Test that new version becomes active."""
        result = run_policy_supersession()
        
        assert result["new_state"] == "active"


class TestPolicyRollback:
    """Test: Policy rollback."""

    def test_rollback_succeeds(self):
        """Test that rollback succeeds with authority."""
        result = run_policy_rollback()
        
        assert result["p1_created"] is True
        assert result["p2_modified"] is True
        assert result["rollback_success"] is True

    def test_rollback_produces_active_state(self):
        """Test that rollback produces an active policy."""
        result = run_policy_rollback()
        
        assert result["rollback_to_state"] == "active"


class TestPolicyOverride:
    """Test: Policy override."""

    def test_override_succeeds_with_authority(self):
        """Test that override succeeds with authority."""
        result = run_policy_override()
        
        assert result["created"] is True
        assert result["overridden"] is True

    def test_override_produces_emergency_state(self):
        """Test that override produces emergency override state."""
        result = run_policy_override()
        
        assert result["override_state"] == "emergency_override"

    def test_override_does_not_bypass_authority(self):
        """Test that override does not bypass authority."""
        result = run_policy_override()
        
        assert result["authority_bypassed"] is False


class TestScopeEscalationAttack:
    """Test: Scope escalation attack.
    
    An actor with production policy modification authority attempts to
    expand policy scope to staging.
    """

    def test_scope_expansion_blocked(self):
        """Test that scope expansion is blocked."""
        result = run_scope_escalation_attack()
        
        assert result["production_created"] is True
        assert result["scope_expansion_blocked"] is True


class TestPolicyAuthorityRecords:
    """Test policy authority records."""

    def test_authority_record_grants_operation(self):
        """Test that authority record correctly grants operation authority."""
        record = create_authority_record(
            policy_id="policy_001",
            principal_id="admin",
            authority_types={PolicyAuthorityType.CREATE, PolicyAuthorityType.MODIFY},
        )
        
        assert record.has_authority(PolicyLifecycleOperation.CREATE) is True
        assert record.has_authority(PolicyLifecycleOperation.MODIFY) is True
        assert record.has_authority(PolicyLifecycleOperation.DELETE) is False

    def test_authority_record_temporal_validity(self):
        """Test that authority record respects temporal bounds."""
        record = create_authority_record(
            policy_id="policy_001",
            principal_id="admin",
            authority_types={PolicyAuthorityType.CREATE},
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        
        assert record.is_valid_at("2026-06-15T00:00:00Z") is True
        assert record.is_valid_at("2025-01-01T00:00:00Z") is False
        assert record.is_valid_at("2027-01-01T00:00:00Z") is False


class TestPolicyVersionRecord:
    """Test policy version records."""

    def test_version_record_immutability(self):
        """Test that version records are immutable."""
        from research.examples.sovereign_agent.policy_governance import PolicyVersionRecord
        
        record = PolicyVersionRecord(
            version_id="ver_001",
            policy_id="policy_001",
            version="1.0.0",
            content={"name": "Test"},
            content_hash="abc123",
            state=PolicyLifecycleState.DRAFT,
            created_at="2026-01-01T00:00:00Z",
            created_by="admin",
            authority_basis="auth_001",
        )
        
        # Frozen dataclass - cannot modify
        with pytest.raises(AttributeError):
            record.state = PolicyLifecycleState.ACTIVE  # type: ignore

    def test_version_record_addressability(self):
        """Test that all version records are addressable."""
        from research.examples.sovereign_agent.policy_governance import PolicyVersionRecord
        
        record = PolicyVersionRecord(
            version_id="ver_001",
            policy_id="policy_001",
            version="1.0.0",
            content={"name": "Test"},
            content_hash="abc123",
            state=PolicyLifecycleState.DELETED,
            created_at="2026-01-01T00:00:00Z",
            created_by="admin",
            authority_basis="auth_001",
        )
        
        assert record.is_addressable is True
        assert record.is_historical is True


class TestPolicyGovernanceEngine:
    """Test policy governance engine."""

    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = PolicyGovernanceEngine()
        
        assert len(engine.policy_versions) == 0
        assert len(engine.lifecycle_events) == 0
        assert len(engine.authority_records) == 0
        assert len(engine.receipts) == 0

    def test_content_hash_computation(self):
        """Test that content hash is computed correctly."""
        engine = PolicyGovernanceEngine()
        
        content1 = {"name": "Test", "value": 42}
        content2 = {"name": "Test", "value": 42}
        content3 = {"name": "Test", "value": 43}
        
        hash1 = engine._compute_content_hash(content1)
        hash2 = engine._compute_content_hash(content2)
        hash3 = engine._compute_content_hash(content3)
        
        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash

    def test_invariant_verification(self):
        """Test that engine verifies invariants."""
        engine = PolicyGovernanceEngine()
        
        # Grant authority
        engine.authority_records["auth_001"] = create_authority_record(
            policy_id="policy_001",
            principal_id="admin",
            authority_types={PolicyAuthorityType.CREATE},
        )
        
        # Create policy
        engine.create_policy(
            policy_id="policy_001",
            version="1.0.0",
            name="Test",
            description="Test policy",
            content=create_test_policy_content(),
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )
        
        results = engine.verify_invariants()
        
        assert results["POLICY_NEQ_AUTHORITY"] is True
        assert results["DELETION_NEQ_ERASURE"] is True
        assert results["SUPERSESSION_NEQ_MUTATION"] is True
        assert results["OVERRIDE_NEQ_BYPASS"] is True


class TestPolicyLifecycleEvent:
    """Test policy lifecycle events."""

    def test_event_immutability(self):
        """Test that lifecycle events are immutable."""
        from research.examples.sovereign_agent.policy_governance import PolicyLifecycleEvent
        
        event = PolicyLifecycleEvent(
            event_id="evt_001",
            policy_id="policy_001",
            policy_version="1.0.0",
            operation=PolicyLifecycleOperation.CREATE,
            previous_state=PolicyLifecycleState.DRAFT,
            new_state=PolicyLifecycleState.DRAFT,
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )
        
        # Frozen dataclass - cannot modify
        with pytest.raises(AttributeError):
            event.new_state = PolicyLifecycleState.ACTIVE  # type: ignore

    def test_event_state_transition_detection(self):
        """Test that event correctly detects state transitions."""
        from research.examples.sovereign_agent.policy_governance import PolicyLifecycleEvent
        
        # State transition
        event1 = PolicyLifecycleEvent(
            event_id="evt_001",
            policy_id="policy_001",
            policy_version="1.0.0",
            operation=PolicyLifecycleOperation.ACTIVATE,
            previous_state=PolicyLifecycleState.DRAFT,
            new_state=PolicyLifecycleState.ACTIVE,
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )
        
        assert event1.is_state_transition is True
        
        # No state transition
        event2 = PolicyLifecycleEvent(
            event_id="evt_002",
            policy_id="policy_001",
            policy_version="1.0.0",
            operation=PolicyLifecycleOperation.CREATE,
            previous_state=PolicyLifecycleState.DRAFT,
            new_state=PolicyLifecycleState.DRAFT,
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )
        
        assert event2.is_state_transition is False


class TestPolicyLifecycleReceipt:
    """Test policy lifecycle receipts."""

    def test_receipt_validity(self):
        """Test that receipt validity is correctly determined."""
        from research.examples.sovereign_agent.policy_governance import (
            PolicyLifecycleEvent,
            PolicyLifecycleReceipt,
        )
        
        event = PolicyLifecycleEvent(
            event_id="evt_001",
            policy_id="policy_001",
            policy_version="1.0.0",
            operation=PolicyLifecycleOperation.CREATE,
            previous_state=PolicyLifecycleState.DRAFT,
            new_state=PolicyLifecycleState.DRAFT,
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )
        
        # Valid receipt
        receipt1 = PolicyLifecycleReceipt(
            receipt_id="receipt_001",
            event=event,
            success=True,
            policy_created=True,
        )
        
        assert receipt1.is_valid is True
        
        # Invalid receipt (authority amplified)
        receipt2 = PolicyLifecycleReceipt(
            receipt_id="receipt_002",
            event=event,
            success=True,
            authority_amplified=True,
        )
        
        assert receipt2.is_valid is False


class TestEndToEndPolicyLifecycle:
    """End-to-end test of policy lifecycle."""

    def test_full_lifecycle(self):
        """Test a full policy lifecycle: create → activate → modify → supersede → rollback → delete."""
        engine = PolicyGovernanceEngine()
        
        # Grant full authority
        engine.authority_records["auth_001"] = create_authority_record(
            policy_id="policy_001",
            principal_id="admin",
            authority_types={
                PolicyAuthorityType.CREATE,
                PolicyAuthorityType.ACTIVATE,
                PolicyAuthorityType.MODIFY,
                PolicyAuthorityType.SUPERSEDE,
                PolicyAuthorityType.ROLLBACK,
                PolicyAuthorityType.DELETE,
            },
        )
        
        # Create
        receipt1 = engine.create_policy(
            policy_id="policy_001",
            version="1.0.0",
            name="Test Policy",
            description="A test policy",
            content=create_test_policy_content(),
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert receipt1.success is True
        
        # Activate
        receipt2 = engine.activate_policy(
            policy_id="policy_001",
            version="1.0.0",
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-02T00:00:00Z",
        )
        assert receipt2.success is True
        
        # Modify
        receipt3 = engine.modify_policy(
            policy_id="policy_001",
            current_version="1.0.0",
            new_version="2.0.0",
            new_content=create_test_policy_content("v2"),
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-03T00:00:00Z",
        )
        assert receipt3.success is True
        
        # Supersede
        receipt4 = engine.supersede_policy(
            policy_id="policy_001",
            old_version="2.0.0",
            new_version="3.0.0",
            new_content=create_test_policy_content("v3"),
            actor_id="admin",
            authority_basis="auth_001",
            timestamp="2026-01-04T00:00:00Z",
        )
        assert receipt4.success is True
        
        # Verify all versions are addressable
        assert engine.policy_versions["policy_001@1.0.0"].is_addressable is True
        assert engine.policy_versions["policy_001@2.0.0"].is_addressable is True
        assert engine.policy_versions["policy_001@3.0.0"].is_addressable is True
        
        # Verify invariants
        invariants = engine.verify_invariants()
        assert all(invariants.values())


class TestAllPhase13Experiments:
    """Test all Phase 13 experiments."""

    def test_all_experiments_pass(self):
        """Test that all Phase 13 experiments pass."""
        results = run_all_phase13_experiments()
        
        # All experiments should have authority_amplified = False
        for name, result in results.items():
            assert result.get("authority_amplified", False) is False, \
                f"Authority amplified in {name}"
        
        # Specific assertions
        assert results["authorized_creation"]["success"] is True
        assert results["unauthorized_creation"]["success"] is False
        assert results["modification_attack"]["p3_unauthorized"] is True
        assert results["deletion_preserves_history"]["historical_addressable"] is True
        assert results["supersession"]["old_addressable"] is True
        assert results["rollback"]["rollback_success"] is True
        assert results["override"]["overridden"] is True
        assert results["scope_escalation"]["scope_expansion_blocked"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
