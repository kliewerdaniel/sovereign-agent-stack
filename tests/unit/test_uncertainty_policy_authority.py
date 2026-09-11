"""Phase 21 tests: Uncertainty Policy Authority and Epistemic Escalation.

Tests verify that uncertainty policy itself can amplify authority and
that the architecture detects and bounds such amplification.
"""

import pytest
from research.examples.sovereign_agent.uncertainty_policy_authority import (
    UncertaintyPolicyAuthorityEngine,
    UncertaintyPolicyResult,
    run_all_phase21_experiments,
    run_unknown_hold,
    run_unknown_review,
    run_unknown_escalate,
    run_unknown_deny,
    run_unknown_authorize,
    run_incomplete_authorize,
    run_was_complete_authorize,
    run_historical_policy_change,
    run_emergency_policy,
    run_cross_domain_policy,
    run_policy_modification,
    run_policy_activation,
    run_policy_rollback,
    run_narrow_authority_attempt,
    run_policy_exceeds_envelope,
    run_hidden_policy_authority,
    run_unobservable_emergency,
    run_different_semantics,
)


class TestUnknownHold:
    """UNKNOWN → HOLD: No amplification."""

    def test_no_amplification(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_unknown_hold(engine)
        assert result.result == UncertaintyPolicyResult.NO_AMPLIFICATION


class TestUnknownReview:
    """UNKNOWN → REVIEW: No amplification."""

    def test_no_amplification(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_unknown_review(engine)
        assert result.result == UncertaintyPolicyResult.NO_AMPLIFICATION


class TestUnknownEscalate:
    """UNKNOWN → ESCALATE: No amplification."""

    def test_no_amplification(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_unknown_escalate(engine)
        assert result.result == UncertaintyPolicyResult.NO_AMPLIFICATION


class TestUnknownDeny:
    """UNKNOWN → DENY: No amplification."""

    def test_no_amplification(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_unknown_deny(engine)
        assert result.result == UncertaintyPolicyResult.NO_AMPLIFICATION


class TestUnknownAuthorize:
    """UNKNOWN → AUTHORIZE: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_unknown_authorize(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestIncompleteAuthorize:
    """INCOMPLETE → AUTHORIZE: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_incomplete_authorize(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestWasCompleteAuthorize:
    """WAS_COMPLETE_AT_T → AUTHORIZE: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_was_complete_authorize(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestHistoricalPolicyChange:
    """Historical policy change: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_historical_policy_change(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestEmergencyPolicy:
    """Emergency uncertainty policy: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_emergency_policy(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestCrossDomainPolicy:
    """Cross-domain uncertainty policy: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_cross_domain_policy(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestPolicyModification:
    """Policy modification: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_policy_modification(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestPolicyActivation:
    """Policy activation: AMPLIFICATION DETECTED."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_policy_activation(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestPolicyRollback:
    """Policy rollback: NO AMPLIFICATION."""

    def test_no_amplification(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_policy_rollback(engine)
        assert result.result == UncertaintyPolicyResult.NO_AMPLIFICATION


class TestNarrowAuthorityAttempt:
    """Actor with narrow authority attempts broad policy change."""

    def test_effect_boundary_violation(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_narrow_authority_attempt(engine)
        assert result.result in (
            UncertaintyPolicyResult.EFFECT_BOUNDARY_VIOLATION,
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED,
        )


class TestPolicyExceedsEnvelope:
    """Policy creates authority exceeding its envelope."""

    def test_policy_exceeds_authority(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_policy_exceeds_envelope(engine)
        assert result.result in (
            UncertaintyPolicyResult.POLICY_EFFECT_EXCEEDS_AUTHORITY,
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED,
        )


class TestHiddenPolicyAuthority:
    """Hidden uncertainty-policy authority."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_hidden_policy_authority(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestUnobservableEmergency:
    """Unobservable emergency uncertainty policy."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_unobservable_emergency(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestDifferentSemantics:
    """Two domains with different uncertainty semantics."""

    def test_amplification_detected(self):
        engine = UncertaintyPolicyAuthorityEngine()
        result = run_different_semantics(engine)
        assert result.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED


class TestAllPhase21Experiments:
    """Test all Phase 21 experiments."""

    def test_all_experiments_run(self):
        results = run_all_phase21_experiments()
        assert results["total_experiments"] == 18

    def test_amplification_detected(self):
        results = run_all_phase21_experiments()
        assert results["amplification_detected"] >= 10

    def test_no_amplification(self):
        results = run_all_phase21_experiments()
        assert results["no_amplification"] >= 4

    def test_policy_validity_not_authority(self):
        """Test that policy validity ≠ policy authority.
        
        Both conservative and aggressive policies are valid,
        but only aggressive policies amplify authority.
        """
        results = run_all_phase21_experiments()
        assert results["amplification_detected"] > 0
        assert results["no_amplification"] > 0


class TestBoundedCompleteness:
    """Test bounded completeness semantics."""

    def test_bounded_complete(self):
        from research.examples.sovereign_agent.uncertainty_policy_authority import BoundedCompleteness
        bc = BoundedCompleteness(
            state="complete",
            scope="production",
            temporal_interval=("2026-01-01", "2026-12-31"),
            observation_method="static_analysis",
            confidence=0.9,
        )
        assert bc.is_bounded_complete()
        assert bc.is_observation_bounded()

    def test_unbounded_complete(self):
        from research.examples.sovereign_agent.uncertainty_policy_authority import BoundedCompleteness
        bc = BoundedCompleteness(
            state="complete",
            scope="*",
            temporal_interval=("unbounded", "unbounded"),
            observation_method="",
            confidence=1.0,
        )
        assert bc.is_bounded_complete()
        assert not bc.is_observation_bounded()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
