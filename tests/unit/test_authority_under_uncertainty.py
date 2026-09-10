"""Phase 20 tests: Authority Under Incomplete Knowledge.

Tests verify that the system can safely make authority decisions when
the authority graph is known to be incomplete or its completeness is
unknown.

Critical: The system must refuse to silently promote incomplete authority
knowledge into authority, while still allowing governance to make explicit
policy decisions about uncertainty.
"""

import pytest
from examples.sovereign_agent.authority_under_uncertainty import (
    AuthorityUnderUncertaintyEngine,
    AuthorityUnderUncertaintyResult,
    CompletenessState,
    UncertaintyDisposition,
    UncertaintyPolicy,
    run_adversarial_observation_gap,
    run_all_phase20_experiments,
    run_world_a_known_complete,
    run_world_b_missing_edge,
    run_world_c_unknown,
    run_world_d_hidden_authority,
    run_world_e_discovered_after,
    run_world_f_emergency_path,
    run_world_g_cross_domain,
    run_world_h_becomes_incomplete,
    run_was_complete_at_t,
)


class TestWorldAKnownComplete:
    """World A: Known complete graph → normal governance."""

    def test_authority_granted(self):
        """Test that authority is granted with complete graph."""
        result = run_world_a_known_complete()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.AUTHORITY_GRANTED

    def test_normal_disposition(self):
        """Test that disposition is NORMAL."""
        result = run_world_a_known_complete()
        assert result["disposition"] == UncertaintyDisposition.NORMAL


class TestWorldBMissingEdge:
    """World B: Known missing edge → UNKNOWN."""

    def test_revalidation_required(self):
        """Test that revalidation is required."""
        result = run_world_b_missing_edge()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED


class TestWorldCUnknown:
    """World C: Unknown graph completeness → UNKNOWN."""

    def test_authority_deferred(self):
        """Test that authority is deferred."""
        result = run_world_c_unknown()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.AUTHORITY_DEFERRED


class TestWorldDHiddenAuthority:
    """World D: Hidden authority outside observation → UNKNOWN."""

    def test_revalidation_required(self):
        """Test that revalidation is required."""
        result = run_world_d_hidden_authority()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED


class TestWorldEDiscoveredAfter:
    """World E: Hidden authority discovered after authorization."""

    def test_historical_preserved(self):
        """Test that historical decision is preserved."""
        result = run_world_e_discovered_after()
        assert result["historical_preserved"] is True

    def test_revalidation_required(self):
        """Test that revalidation is required."""
        result = run_world_e_discovered_after()
        assert result["revalidation_required"] is True

    def test_no_automatic_revocation(self):
        """Test that automatic revocation does NOT happen."""
        result = run_world_e_discovered_after()
        assert result["automatic_revocation"] is False


class TestWorldFEmergencyPath:
    """World F: Hidden authority in emergency path."""

    def test_authority_deferred(self):
        """Test that authority is deferred."""
        result = run_world_f_emergency_path()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.AUTHORITY_DEFERRED


class TestWorldGCrossDomain:
    """World G: Hidden cross-domain delegation."""

    def test_revalidation_required(self):
        """Test that revalidation is required."""
        result = run_world_g_cross_domain()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED


class TestWorldHBecomesIncomplete:
    """World H: Graph becomes incomplete after prior authorization."""

    def test_revalidation_required(self):
        """Test that revalidation is required."""
        result = run_world_h_becomes_incomplete()
        assert result["revalidation_required"] is True

    def test_no_automatic_revocation(self):
        """Test that automatic revocation does NOT happen."""
        result = run_world_h_becomes_incomplete()
        assert result["automatic_revocation"] is False

    def test_historical_preserved(self):
        """Test that historical authorization is preserved."""
        result = run_world_h_becomes_incomplete()
        assert result["historical_preserved"] is True


class TestAdversarialObservationGap:
    """Adversarial: Observation gap attack."""

    def test_revalidation_required(self):
        """Test that revalidation is required under observation gap."""
        result = run_adversarial_observation_gap()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED


class TestWasCompleteAtT:
    """Test WAS_COMPLETE_AT_T state."""

    def test_revalidation_required(self):
        """Test that revalidation is required for historical completeness."""
        result = run_was_complete_at_t()
        assert result["actual_result"] == AuthorityUnderUncertaintyResult.REVALIDATION_REQUIRED


class TestAllPhase20Experiments:
    """Test all Phase 20 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 20 experiments run."""
        results = run_all_phase20_experiments()
        assert results["total_experiments"] == 10

    def test_authority_granted_count(self):
        """Test that authority is granted only for complete graphs."""
        results = run_all_phase20_experiments()
        assert results["authority_granted_count"] == 1

    def test_no_automatic_revocation(self):
        """Test that automatic revocation NEVER happens."""
        results = run_all_phase20_experiments()
        assert results["automatic_revocation_count"] == 0

    def test_historical_preserved(self):
        """Test that historical decisions are preserved."""
        results = run_all_phase20_experiments()
        assert results["historical_preserved_count"] >= 1

    def test_revalidation_required(self):
        """Test that revalidation is required for incomplete graphs."""
        results = run_all_phase20_experiments()
        assert results["revalidation_required_count"] >= 5


class TestUncertaintyPolicy:
    """Test uncertainty policy."""

    def test_default_policy(self):
        """Test default uncertainty policy."""
        policy = UncertaintyPolicy(
            policy_id="test",
            name="Test",
            description="Test policy",
            state_to_disposition={
                CompletenessState.COMPLETE: UncertaintyDisposition.NORMAL,
                CompletenessState.INCOMPLETE: UncertaintyDisposition.REVIEW,
                CompletenessState.UNKNOWN: UncertaintyDisposition.HOLD,
                CompletenessState.WAS_COMPLETE_AT_T: UncertaintyDisposition.REVIEW,
            },
        )
        assert policy.get_disposition(CompletenessState.COMPLETE) == UncertaintyDisposition.NORMAL
        assert policy.get_disposition(CompletenessState.INCOMPLETE) == UncertaintyDisposition.REVIEW
        assert policy.get_disposition(CompletenessState.UNKNOWN) == UncertaintyDisposition.HOLD
        assert policy.get_disposition(CompletenessState.WAS_COMPLETE_AT_T) == UncertaintyDisposition.REVIEW

    def test_custom_policy(self):
        """Test custom uncertainty policy."""
        policy = UncertaintyPolicy(
            policy_id="custom",
            name="Custom",
            description="Custom policy",
            state_to_disposition={
                CompletenessState.COMPLETE: UncertaintyDisposition.NORMAL,
                CompletenessState.INCOMPLETE: UncertaintyDisposition.DENY,
                CompletenessState.UNKNOWN: UncertaintyDisposition.HOLD,
            },
        )
        assert policy.get_disposition(CompletenessState.INCOMPLETE) == UncertaintyDisposition.DENY


class TestCompletenessState:
    """Test four completeness states."""

    def test_four_states(self):
        """Test that there are four distinct completeness states."""
        assert len(CompletenessState) == 4
        assert CompletenessState.COMPLETE is not None
        assert CompletenessState.INCOMPLETE is not None
        assert CompletenessState.UNKNOWN is not None
        assert CompletenessState.WAS_COMPLETE_AT_T is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
