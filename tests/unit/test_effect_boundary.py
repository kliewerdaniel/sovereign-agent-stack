"""Phase 15 tests: Effect Boundary.

Tests investigate what authority must be established for a policy
transformation to legitimately create or alter downstream authority.

Key finding: 24 of 26 experiments detect authority amplification or
exceed the authority envelope. The architecture requires a distinct
concept of POLICY EFFECT AUTHORITY.
"""

import pytest
from examples.sovereign_agent.effect_boundary import (
    AuthorityEnvelope,
    AuthoritySurface,
    AuthorityTransformationType,
    CapabilityClass,
    EffectBoundaryEngine,
    EffectBoundaryResult,
    PolicyEffectAuthorityType,
    run_all_phase15_experiments,
    run_authority_creation_as_governed_operation,
    run_authority_amplification_with_explicit_meta_authority,
    run_broad_policy_change,
    run_capability_class_expansion,
    run_condition_removal,
    run_delegated_meta_authority,
    run_explicit_effect_authority_boundary,
    run_narrow_policy_change,
    run_new_authorization_path,
    run_policy_composition,
    run_policy_effect_provenance,
    run_revocation_and_effect_authority,
    run_scope_expansion,
    run_temporal_expansion,
)


class TestAuthoritySurface:
    """Test authority surface comparisons."""

    def test_same_surface_permits(self):
        """Test that identical surfaces permit each other."""
        surf = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            capability_class=CapabilityClass.MODIFY_POLICY,
        )
        assert surf.permits(surf) is True

    def test_different_principal_rejects(self):
        """Test that different principals are rejected."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        surf2 = AuthoritySurface(
            principal="other",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        assert surf1.permits(surf2) is False

    def test_different_scope_rejects(self):
        """Test that different scopes are rejected."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        surf2 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="staging",
        )
        assert surf1.permits(surf2) is False

    def test_wildcard_scope_permits(self):
        """Test that wildcard scope permits any scope."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="*",
        )
        surf2 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        assert surf1.permits(surf2) is True

    def test_temporal_containment(self):
        """Test that temporal intervals must contain."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            temporal_interval=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        )
        surf2 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            temporal_interval=("2026-06-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        )
        assert surf1.permits(surf2) is True

    def test_temporal_expansion_rejects(self):
        """Test that temporal expansion is rejected."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        )
        surf2 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            temporal_interval=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        )
        assert surf1.permits(surf2) is False

    def test_conditions_superset_permits(self):
        """Test that superset conditions permit subset."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            conditions=frozenset({"provenance_required", "dual_approval_required"}),
        )
        surf2 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            conditions=frozenset({"provenance_required"}),
        )
        assert surf1.permits(surf2) is True

    def test_conditions_subset_rejects(self):
        """Test that subset conditions reject superset."""
        surf1 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            conditions=frozenset({"provenance_required"}),
        )
        surf2 = AuthoritySurface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            conditions=frozenset({"provenance_required", "dual_approval_required"}),
        )
        assert surf1.permits(surf2) is False


class TestAuthorityEnvelope:
    """Test authority envelope containment."""

    def test_within_envelope(self):
        """Test that effects within envelope are contained."""
        engine = EffectBoundaryEngine()
        input_auth = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            capability_class=CapabilityClass.MODIFY_POLICY,
        )
        envelope = engine.create_envelope(
            principal="admin",
            granted_authority=input_auth,
            max_scope="production",
            max_capability_class=CapabilityClass.MODIFY_POLICY,
        )
        effect = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            capability_class=CapabilityClass.MODIFY_POLICY,
        )
        assert envelope.contains_effect(effect) is True

    def test_exceeds_envelope_scope(self):
        """Test that scope expansion exceeds envelope."""
        engine = EffectBoundaryEngine()
        input_auth = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="staging",
            capability_class=CapabilityClass.MODIFY_POLICY,
        )
        envelope = engine.create_envelope(
            principal="admin",
            granted_authority=input_auth,
            max_scope="staging",
            max_capability_class=CapabilityClass.MODIFY_POLICY,
        )
        effect = engine.create_authority_surface(
            principal="admin",
            operation="execute_payment",
            resource="payment_policy",
            scope="production",
            capability_class=CapabilityClass.EXECUTE_PAYMENT,
        )
        assert envelope.contains_effect(effect) is False

    def test_exceeds_envelope_temporal(self):
        """Test that temporal expansion exceeds envelope."""
        engine = EffectBoundaryEngine()
        input_auth = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
            capability_class=CapabilityClass.MODIFY_POLICY,
        )
        envelope = engine.create_envelope(
            principal="admin",
            granted_authority=input_auth,
            max_scope="production",
            max_temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
            max_capability_class=CapabilityClass.MODIFY_POLICY,
        )
        effect = engine.create_authority_surface(
            principal="admin",
            operation="execute_payment",
            resource="payment_policy",
            scope="production",
            temporal_interval=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
            capability_class=CapabilityClass.EXECUTE_PAYMENT,
        )
        assert envelope.contains_effect(effect) is False


class TestNarrowPolicyChange:
    """Test narrow policy changes."""

    def test_narrow_change_within_envelope(self):
        """Test that narrow policy changes remain within envelope."""
        engine = EffectBoundaryEngine()
        result = run_narrow_policy_change(engine)
        assert result.result == EffectBoundaryResult.WITHIN_ENVELOPE
        assert result.authority_amplified is False


class TestBroadPolicyChange:
    """Test broad policy changes."""

    def test_broad_change_exceeds_envelope(self):
        """Test that broad policy changes exceed envelope."""
        engine = EffectBoundaryEngine()
        result = run_broad_policy_change(engine)
        assert result.result == EffectBoundaryResult.EXCEEDS_ENVELOPE
        assert result.authority_amplified is True


class TestScopeExpansion:
    """Test scope expansion."""

    def test_scope_expansion_detected(self):
        """Test that scope expansion is detected."""
        engine = EffectBoundaryEngine()
        result = run_scope_expansion(engine)
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestTemporalExpansion:
    """Test temporal expansion."""

    def test_temporal_expansion_detected(self):
        """Test that temporal expansion is detected."""
        engine = EffectBoundaryEngine()
        result = run_temporal_expansion(engine)
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestConditionRemoval:
    """Test condition removal."""

    def test_condition_removal_detected(self):
        """Test that condition removal is detected."""
        engine = EffectBoundaryEngine()
        result = run_condition_removal(engine)
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestNewAuthorizationPath:
    """Test new authorization path creation."""

    def test_new_path_exceeds_envelope(self):
        """Test that creating new paths exceeds envelope."""
        engine = EffectBoundaryEngine()
        result = run_new_authorization_path(engine)
        assert result.result == EffectBoundaryResult.EXCEEDS_ENVELOPE
        assert result.authority_amplified is True


class TestCapabilityClassExpansion:
    """Test capability class expansion."""

    def test_capability_expansion_exceeds_envelope(self):
        """Test that capability class expansion exceeds envelope."""
        engine = EffectBoundaryEngine()
        result = run_capability_class_expansion(engine)
        assert result.result == EffectBoundaryResult.EXCEEDS_ENVELOPE
        assert result.authority_amplified is True


class TestPolicyComposition:
    """Test policy composition."""

    def test_composition_exceeds_envelope(self):
        """Test that policy composition exceeds envelope."""
        engine = EffectBoundaryEngine()
        result = run_policy_composition(engine)
        assert result.result == EffectBoundaryResult.EXCEEDS_ENVELOPE
        assert result.authority_amplified is True


class TestDelegatedMetaAuthority:
    """Test delegated meta-authority."""

    def test_delegated_meta_authority_detected(self):
        """Test that delegated meta-authority is still detected as amplification."""
        engine = EffectBoundaryEngine()
        result = run_delegated_meta_authority(engine)
        # Even with explicit effect authority, the output effect is broader
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestExplicitEffectAuthorityBoundary:
    """Test explicit effect authority boundary."""

    def test_explicit_effect_boundary_detected(self):
        """Test that explicit effect authority boundary is detected."""
        engine = EffectBoundaryEngine()
        result = run_explicit_effect_authority_boundary(engine)
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestAuthorityCreationAsGovernedOperation:
    """Test authority creation as a governed operation."""

    def test_authority_creation_exceeds_envelope(self):
        """Test that authority creation exceeds envelope."""
        engine = EffectBoundaryEngine()
        result = run_authority_creation_as_governed_operation(engine)
        assert result.result == EffectBoundaryResult.EXCEEDS_ENVELOPE
        assert result.authority_amplified is True


class TestPolicyEffectProvenance:
    """Test policy effect provenance."""

    def test_provenance_exceeds_envelope(self):
        """Test that policy effect provenance exceeds envelope."""
        engine = EffectBoundaryEngine()
        result = run_policy_effect_provenance(engine)
        assert result.result == EffectBoundaryResult.EXCEEDS_ENVELOPE
        assert result.authority_amplified is True


class TestRevocationAndEffectAuthority:
    """Test revocation and effect authority."""

    def test_revocation_detected(self):
        """Test that revocation is detected."""
        engine = EffectBoundaryEngine()
        result = run_revocation_and_effect_authority(engine)
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestAuthorityAmplificationWithExplicitMetaAuthority:
    """Test authority amplification with explicit meta-authority."""

    def test_amplification_with_meta_authority(self):
        """Test that amplification is still detected with meta-authority."""
        engine = EffectBoundaryEngine()
        result = run_authority_amplification_with_explicit_meta_authority(engine)
        assert result.result == EffectBoundaryResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestAllPhase15Experiments:
    """Test all Phase 15 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 15 experiments run."""
        results = run_all_phase15_experiments()
        assert results["total_experiments"] == 26

    def test_narrow_change_within_envelope(self):
        """Test that narrow policy change is within envelope."""
        results = run_all_phase15_experiments()
        assert results["experiments"]["narrow_policy_change"].result == EffectBoundaryResult.WITHIN_ENVELOPE

    def test_all_other_experiments_detect_amplification(self):
        """Test that all other experiments detect amplification."""
        results = run_all_phase15_experiments()
        # Identity transformation (A → A) is NOT amplifying
        non_amplifying = {"narrow_policy_change", "transformation_0"}
        for name, exp in results["experiments"].items():
            if name not in non_amplifying:
                assert exp.authority_amplified is True, f"{name} did not detect amplification"


class TestEffectBoundaryEngine:
    """Test effect boundary engine."""

    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = EffectBoundaryEngine()
        assert len(engine.experiments) == 0
        assert len(engine.transformations) == 0

    def test_authority_surface_creation(self):
        """Test that authority surfaces are created correctly."""
        engine = EffectBoundaryEngine()
        surf = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        assert surf.principal == "admin"
        assert surf.operation == "modify_policy"
        assert surf.resource == "payment_policy"
        assert surf.scope == "production"

    def test_envelope_creation(self):
        """Test that envelopes are created correctly."""
        engine = EffectBoundaryEngine()
        input_auth = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        envelope = engine.create_envelope(
            principal="admin",
            granted_authority=input_auth,
            max_scope="production",
        )
        assert envelope.principal == "admin"
        assert envelope.max_scope == "production"

    def test_transformation_recording(self):
        """Test that transformations are recorded correctly."""
        engine = EffectBoundaryEngine()
        input_surf = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
        )
        output_surf = engine.create_authority_surface(
            principal="admin",
            operation="execute_payment",
            resource="payment_policy",
            scope="production",
        )
        transformation = engine.record_transformation(
            transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
            input_surface=input_surf,
            output_surface=output_surf,
            actor="admin",
            authority_basis="test",
            timestamp="2026-01-15T00:00:00Z",
        )
        assert transformation.transformation_type == AuthorityTransformationType.CAPABILITY_TRANSITION
        assert transformation.is_amplifying is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
