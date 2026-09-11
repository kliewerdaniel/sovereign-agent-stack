"""Phase 14 tests: Closed Authority Loop.

Tests validate that the authority architecture is actually closed against
amplification, bypass, and escalation attacks.

Key finding: 13 of 15 experiments detect authority amplification.
The current architecture lacks a second authority boundary over policy effects.
"""

import pytest
from research.examples.sovereign_agent.closed_authority_loop import (
    AttackClass,
    ClosedAuthorityLoopEngine,
    ClosedLoopResult,
    run_all_phase14_experiments,
    run_authorized_policy_broadening,
    run_scope_escalation,
    run_temporal_escalation,
    run_authority_expiration,
    run_policy_composition_escalation,
    run_predicate_weakening,
    run_authorization_path_creation,
    run_emergency_override,
    run_rollback_escalation,
    run_historical_reproducibility,
    run_policy_authority_revocation,
    run_policy_effect_analysis,
    run_legitimate_authority_abuse,
    run_multi_step_escalation,
    run_compositional_escalation,
)


class TestAuthorizedPolicyBroadening:
    """Test: Authorized policy broadening."""

    def test_broadening_detected(self):
        """Test that policy broadening is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_authorized_policy_broadening(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True
        assert result.authority_escalated is True


class TestScopeEscalation:
    """Test: Scope escalation."""

    def test_scope_escalation_detected(self):
        """Test that scope escalation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_scope_escalation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestTemporalEscalation:
    """Test: Temporal escalation."""

    def test_temporal_escalation_detected(self):
        """Test that temporal escalation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_temporal_escalation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestAuthorityExpiration:
    """Test: Authority expiration."""

    def test_authority_expiration_detected(self):
        """Test that authority expiration is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_authority_expiration(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestPolicyCompositionEscalation:
    """Test: Policy composition escalation."""

    def test_composition_escalation_detected(self):
        """Test that policy composition escalation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_policy_composition_escalation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestPredicateWeakening:
    """Test: Predicate weakening."""

    def test_predicate_weakening_detected(self):
        """Test that predicate weakening is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_predicate_weakening(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestAuthorizationPathCreation:
    """Test: Authorization path creation."""

    def test_path_creation_detected(self):
        """Test that authorization path creation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_authorization_path_creation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestEmergencyOverride:
    """Test: Emergency override."""

    def test_override_detected(self):
        """Test that emergency override is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_emergency_override(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestRollbackEscalation:
    """Test: Rollback escalation."""

    def test_rollback_closed(self):
        """Test that rollback does not escalate authority."""
        engine = ClosedAuthorityLoopEngine()
        result = run_rollback_escalation(engine)
        
        assert result.result == ClosedLoopResult.CLOSED
        assert result.authority_amplified is False


class TestHistoricalReproducibility:
    """Test: Historical reproducibility."""

    def test_historical_closed(self):
        """Test that historical reproducibility is maintained."""
        engine = ClosedAuthorityLoopEngine()
        result = run_historical_reproducibility(engine)
        
        assert result.result == ClosedLoopResult.CLOSED
        assert result.authority_amplified is False


class TestPolicyAuthorityRevocation:
    """Test: Policy authority revocation."""

    def test_revocation_detected(self):
        """Test that policy authority revocation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_policy_authority_revocation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestPolicyEffectAnalysis:
    """Test: Policy effect analysis."""

    def test_effect_analysis_detected(self):
        """Test that policy effect analysis detects amplification."""
        engine = ClosedAuthorityLoopEngine()
        result = run_policy_effect_analysis(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestLegitimateAuthorityAbuse:
    """Test: Legitimate authority abuse."""

    def test_abuse_detected(self):
        """Test that legitimate authority abuse is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_legitimate_authority_abuse(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True
        assert result.authority_escalated is True


class TestMultiStepEscalation:
    """Test: Multi-step escalation."""

    def test_multi_step_detected(self):
        """Test that multi-step escalation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_multi_step_escalation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestCompositionalEscalation:
    """Test: Compositional escalation."""

    def test_compositional_detected(self):
        """Test that compositional escalation is detected."""
        engine = ClosedAuthorityLoopEngine()
        result = run_compositional_escalation(engine)
        
        assert result.result == ClosedLoopResult.AMPLIFICATION_DETECTED
        assert result.authority_amplified is True


class TestAllPhase14Experiments:
    """Test all Phase 14 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 14 experiments run."""
        results = run_all_phase14_experiments()
        
        assert results["total_experiments"] == 15
        assert results["closed_count"] == 2
        assert results["amplification_count"] == 13
        assert results["bypass_count"] == 0
        assert results["escalation_count"] == 0

    def test_rollback_and_historical_closed(self):
        """Test that rollback and historical reproducibility are closed."""
        results = run_all_phase14_experiments()
        
        assert results["experiments"]["rollback_escalation"].result == ClosedLoopResult.CLOSED
        assert results["experiments"]["historical_reproducibility"].result == ClosedLoopResult.CLOSED

    def test_all_other_experiments_detect_amplification(self):
        """Test that all other experiments detect amplification."""
        results = run_all_phase14_experiments()
        
        closed_experiments = [
            "rollback_escalation",
            "historical_reproducibility",
        ]
        
        for name, exp in results["experiments"].items():
            if name not in closed_experiments:
                assert exp.result == ClosedLoopResult.AMPLIFICATION_DETECTED, \
                    f"{name} did not detect amplification"


class TestClosedAuthorityLoopEngine:
    """Test closed authority loop engine."""

    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = ClosedAuthorityLoopEngine()
        
        assert len(engine.experiments) == 0
        assert len(engine.authority_tokens) == 0
        assert len(engine.transition_log) == 0

    def test_authority_token_creation(self):
        """Test that authority tokens are created correctly."""
        engine = ClosedAuthorityLoopEngine()
        
        token = engine.create_authority_token(
            source="test",
            scope="production",
            capability_class="modify_policy",
        )
        
        assert token.token_id.startswith("auth_")
        assert token.source == "test"
        assert token.scope == "production"
        assert token.capability_class == "modify_policy"

    def test_transition_recording(self):
        """Test that transitions are recorded correctly."""
        engine = ClosedAuthorityLoopEngine()
        
        input_token = engine.create_authority_token(
            source="test",
            scope="production",
            capability_class="modify_policy",
        )
        
        output_token = engine.create_authority_token(
            source="test",
            scope="production",
            capability_class="execute_action",
        )
        
        step = engine.record_transition(
            step_name="test_transition",
            input_token=input_token,
            output_token=output_token,
            transformation="test",
            actor="test",
            authority_basis="test",
            timestamp="2026-01-01T00:00:00Z",
            scope="production",
        )
        
        assert step.step_id.startswith("step_")
        assert step.authority_amplified is True  # Different capability class


class TestTransitionStep:
    """Test transition step."""

    def test_authority_conserved_same_capability(self):
        """Test that authority is conserved when capability class is the same."""
        from research.examples.sovereign_agent.closed_authority_loop import (
            AuthorityToken,
            TransitionStep,
        )
        
        input_token = AuthorityToken(
            token_id="auth_001",
            source="test",
            scope="production",
            temporal_bounds=("unbounded", "unbounded"),
            capability_class="modify_policy",
        )
        
        output_token = AuthorityToken(
            token_id="auth_002",
            source="test",
            scope="production",
            temporal_bounds=("unbounded", "unbounded"),
            capability_class="modify_policy",
        )
        
        step = TransitionStep(
            step_id="step_001",
            step_name="test",
            input_authority=input_token,
            output_authority=output_token,
            transformation="test",
            actor="test",
            authority_basis="test",
            timestamp="2026-01-01T00:00:00Z",
            scope="production",
        )
        
        assert step.authority_conserved is True
        assert step.authority_amplified is False

    def test_authority_amplified_different_capability(self):
        """Test that authority is amplified when capability class differs."""
        from research.examples.sovereign_agent.closed_authority_loop import (
            AuthorityToken,
            TransitionStep,
        )
        
        input_token = AuthorityToken(
            token_id="auth_001",
            source="test",
            scope="production",
            temporal_bounds=("unbounded", "unbounded"),
            capability_class="modify_policy",
        )
        
        output_token = AuthorityToken(
            token_id="auth_002",
            source="test",
            scope="production",
            temporal_bounds=("unbounded", "unbounded"),
            capability_class="execute_action",
        )
        
        step = TransitionStep(
            step_id="step_001",
            step_name="test",
            input_authority=input_token,
            output_authority=output_token,
            transformation="test",
            actor="test",
            authority_basis="test",
            timestamp="2026-01-01T00:00:00Z",
            scope="production",
        )
        
        assert step.authority_conserved is False
        assert step.authority_amplified is True

    def test_authority_amplified_scope_expansion(self):
        """Test that authority is amplified when scope expands."""
        from research.examples.sovereign_agent.closed_authority_loop import (
            AuthorityToken,
            TransitionStep,
        )
        
        input_token = AuthorityToken(
            token_id="auth_001",
            source="test",
            scope="production",
            temporal_bounds=("unbounded", "unbounded"),
            capability_class="modify_policy",
        )
        
        output_token = AuthorityToken(
            token_id="auth_002",
            source="test",
            scope="staging",  # Different scope
            temporal_bounds=("unbounded", "unbounded"),
            capability_class="modify_policy",
        )
        
        step = TransitionStep(
            step_id="step_001",
            step_name="test",
            input_authority=input_token,
            output_authority=output_token,
            transformation="test",
            actor="test",
            authority_basis="test",
            timestamp="2026-01-01T00:00:00Z",
            scope="staging",
        )
        
        assert step.authority_conserved is False
        assert step.authority_amplified is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
