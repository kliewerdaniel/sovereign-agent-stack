"""Phase 22 tests: Authority Transformation Algebra.

Tests verify that the transformation algebra correctly classifies
authority transformations and detects amplification across all
transformation types.
"""

import pytest
from examples.sovereign_agent.authority_transformation_algebra import (
    AuthorityTransformation,
    TransformationAlgebraEngine,
    TransformationClass,
    TransformationEnvelope,
    classify_transformation,
    run_all_phase22_experiments,
    run_identity_transformation,
    run_narrowing_transformation,
    run_broadening_transformation,
    run_scope_change_transformation,
    run_temporal_shift_transformation,
    run_capability_change_transformation,
    run_condition_change_transformation,
    run_delegation_transformation,
    run_composition_transformation,
    run_interpretation_transformation,
    run_uncertainty_policy_transformation,
    run_emergency_transformation,
    run_recovery_transformation,
)


class TestIdentityTransformation:
    """A → A: Identity is conservative."""

    def test_conservative(self):
        engine = TransformationAlgebraEngine()
        result = run_identity_transformation(engine)
        assert result.classification == TransformationClass.UNCHANGED


class TestNarrowingTransformation:
    """A → narrower(A): Narrowing is conservative."""

    def test_conservative(self):
        engine = TransformationAlgebraEngine()
        result = run_narrowing_transformation(engine)
        assert result.classification == TransformationClass.CONSERVATIVE


class TestBroadeningTransformation:
    """A → broader(A): Broadening is AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_broadening_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestScopeChangeTransformation:
    """A → different_scope(A): Scope change is INCOMPARABLE."""

    def test_incomparable(self):
        engine = TransformationAlgebraEngine()
        result = run_scope_change_transformation(engine)
        assert result.classification == TransformationClass.INCOMPARABLE


class TestTemporalShiftTransformation:
    """A → different_time(A): Temporal shift is AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_temporal_shift_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestCapabilityChangeTransformation:
    """A → different_capability(A): Capability escalation is AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_capability_change_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestConditionChangeTransformation:
    """A → different_conditions(A): Condition removal is AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_condition_change_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestDelegationTransformation:
    """A → delegated(A): Delegation should be conservative."""

    def test_conservative(self):
        engine = TransformationAlgebraEngine()
        result = run_delegation_transformation(engine)
        assert result.classification in (
            TransformationClass.CONSERVATIVE,
            TransformationClass.UNCHANGED,
        )


class TestCompositionTransformation:
    """A → composed(A+B): Composition can be AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_composition_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestInterpretationTransformation:
    """A → interpreted(A): Interpretation can be AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_interpretation_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestUncertaintyPolicyTransformation:
    """A → uncertainty_policy(A): Uncertainty policy can be AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_uncertainty_policy_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestEmergencyTransformation:
    """A → emergency(A): Emergency authority may be AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_emergency_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestRecoveryTransformation:
    """A → recovery(A): Recovery authority may be AMPLIFYING."""

    def test_amplifying(self):
        engine = TransformationAlgebraEngine()
        result = run_recovery_transformation(engine)
        assert result.classification == TransformationClass.AMPLIFYING


class TestAllPhase22Experiments:
    """Test all Phase 22 experiments."""

    def test_all_experiments_run(self):
        results = run_all_phase22_experiments()
        assert results["total_experiments"] == 13

    def test_amplifying_detected(self):
        results = run_all_phase22_experiments()
        assert results["amplifying_count"] >= 8

    def test_conservative_detected(self):
        results = run_all_phase22_experiments()
        assert results["conservative_count"] >= 1

    def test_incomparable_detected(self):
        results = run_all_phase22_experiments()
        assert results["incomparable_count"] >= 1


class TestTransformationEnvelope:
    """Test transformation envelope."""

    def test_contains(self):
        envelope = TransformationEnvelope(
            envelope_id="test",
            principal="admin",
            granted_authority={"scope": "production"},
            permitted_effects=[],
            max_scope="production",
            max_temporal_bounds=("2026-01-01", "2026-12-31"),
            max_capability_class="execute_action",
        )
        assert envelope.contains({
            "scope": "production",
            "capability_class": "execute_action",
            "temporal_bounds": ("2026-01-01", "2026-12-31"),
        })

    def test_exceeds_scope(self):
        envelope = TransformationEnvelope(
            envelope_id="test",
            principal="admin",
            granted_authority={"scope": "production"},
            permitted_effects=[],
            max_scope="production",
            max_temporal_bounds=("2026-01-01", "2026-12-31"),
            max_capability_class="execute_action",
        )
        assert not envelope.contains({"scope": "*", "capability_class": "execute_action"})

    def test_exceeds_capability(self):
        envelope = TransformationEnvelope(
            envelope_id="test",
            principal="admin",
            granted_authority={"scope": "production", "capability_class": "analyze"},
            permitted_effects=[],
            max_scope="production",
            max_temporal_bounds=("2026-01-01", "2026-12-31"),
            max_capability_class="analyze",
        )
        assert not envelope.contains({"scope": "production", "capability_class": "execute_action"})


class TestTransformationClassifier:
    """Test transformation classifier."""

    def test_identity(self):
        t = AuthorityTransformation(
            transformation_id="test",
            input_authority={"scope": "production", "capability_class": "execute"},
            effect_authority={"scope": "production", "capability_class": "execute"},
            transformation_type="identity",
            actor="admin",
            authority_basis="trust_anchor",
        )
        assert classify_transformation(t) == TransformationClass.UNCHANGED

    def test_amplifying(self):
        t = AuthorityTransformation(
            transformation_id="test",
            input_authority={"scope": "production", "capability_class": "analyze"},
            effect_authority={"scope": "production", "capability_class": "execute"},
            transformation_type="amplifying",
            actor="admin",
            authority_basis="trust_anchor",
        )
        assert classify_transformation(t) == TransformationClass.AMPLIFYING

    def test_conservative(self):
        t = AuthorityTransformation(
            transformation_id="test",
            input_authority={"scope": "*", "capability_class": "execute"},
            effect_authority={"scope": "production", "capability_class": "execute"},
            transformation_type="narrowing",
            actor="admin",
            authority_basis="trust_anchor",
        )
        assert classify_transformation(t) == TransformationClass.CONSERVATIVE

    def test_incomparable(self):
        t = AuthorityTransformation(
            transformation_id="test",
            input_authority={"scope": "production", "capability_class": "execute"},
            effect_authority={"scope": "staging", "capability_class": "execute"},
            transformation_type="scope_change",
            actor="admin",
            authority_basis="trust_anchor",
        )
        assert classify_transformation(t) == TransformationClass.INCOMPARABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
