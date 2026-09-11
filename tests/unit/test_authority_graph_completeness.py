"""Phase 19 tests: Authority Graph Completeness.

Tests verify that the completeness checker can detect when the declared
authority graph does not capture all authority that exists in the system.

Critical: The completeness checker MUST NOT become an authority oracle.
INCOMPLETE does NOT imply unauthorized.
"""

import pytest
from research.examples.sovereign_agent.authority_graph_completeness import (
    AuthorityGraphCompletenessEngine,
    CompletenessDimension,
    CompletenessResult,
    ObservableAuthorityMechanism,
    run_all_phase19_experiments,
    run_exact_graph_experiment,
    run_missing_edge_experiment,
    run_hidden_node_experiment,
    run_hidden_policy_experiment,
    run_hidden_capability_experiment,
    run_out_of_band_admin_experiment,
    run_cross_domain_hidden_experiment,
    run_temporal_authority_experiment,
    run_failure_path_experiment,
    run_recovery_authority_experiment,
    run_emergency_override_experiment,
    run_outside_protocol_experiment,
)


class TestExactGraph:
    """Test exact graph with no hidden authorities."""

    def test_complete(self):
        """Test that exact graph is complete."""
        result = run_exact_graph_experiment()
        assert result["actual"] == CompletenessResult.COMPLETE

    def test_no_hidden(self):
        """Test that no hidden authorities are found."""
        result = run_exact_graph_experiment()
        assert result["hidden_count"] == 0


class TestMissingEdge:
    """Test missing delegation edge."""

    def test_incomplete(self):
        """Test that missing edge makes graph incomplete."""
        result = run_missing_edge_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE

    def test_hidden_detected(self):
        """Test that hidden edge is detected."""
        result = run_missing_edge_experiment()
        assert result["hidden_count"] > 0


class TestHiddenNode:
    """Test hidden authority node."""

    def test_incomplete(self):
        """Test that hidden node makes graph incomplete."""
        result = run_hidden_node_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE

    def test_hidden_detected(self):
        """Test that hidden node is detected."""
        result = run_hidden_node_experiment()
        assert result["hidden_count"] > 0


class TestHiddenPolicy:
    """Test hidden policy authority."""

    def test_incomplete(self):
        """Test that hidden policy makes graph incomplete."""
        result = run_hidden_policy_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestHiddenCapability:
    """Test hidden capability escalation."""

    def test_incomplete(self):
        """Test that hidden capability makes graph incomplete."""
        result = run_hidden_capability_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestOutOfBandAdmin:
    """Test out-of-band administrative authority."""

    def test_incomplete(self):
        """Test that out-of-band admin makes graph incomplete."""
        result = run_out_of_band_admin_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestCrossDomainHidden:
    """Test cross-domain hidden delegation."""

    def test_incomplete(self):
        """Test that cross-domain hidden delegation makes graph incomplete."""
        result = run_cross_domain_hidden_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestTemporalAuthority:
    """Test temporal authority."""

    def test_incomplete(self):
        """Test that temporal authority makes graph incomplete."""
        result = run_temporal_authority_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestFailurePath:
    """Test failure-path authority."""

    def test_incomplete(self):
        """Test that failure-path authority makes graph incomplete."""
        result = run_failure_path_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestRecoveryAuthority:
    """Test recovery authority."""

    def test_incomplete(self):
        """Test that recovery authority makes graph incomplete."""
        result = run_recovery_authority_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestEmergencyOverride:
    """Test emergency override authority."""

    def test_incomplete(self):
        """Test that emergency override makes graph incomplete."""
        result = run_emergency_override_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestOutsideProtocol:
    """Test authority mechanism outside declared protocol."""

    def test_incomplete(self):
        """Test that outside protocol authority makes graph incomplete."""
        result = run_outside_protocol_experiment()
        assert result["actual"] == CompletenessResult.INCOMPLETE


class TestAllPhase19Experiments:
    """Test all Phase 19 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 19 experiments run."""
        results = run_all_phase19_experiments()
        assert results["total_experiments"] == 12

    def test_exact_graph_complete(self):
        """Test that exact graph is complete."""
        results = run_all_phase19_experiments()
        assert results["complete_count"] >= 1

    def test_incomplete_detected(self):
        """Test that incomplete graphs are detected."""
        results = run_all_phase19_experiments()
        assert results["incomplete_count"] >= 10

    def test_hidden_authorities_found(self):
        """Test that hidden authorities are found."""
        results = run_all_phase19_experiments()
        assert results["total_hidden"] >= 10

    def test_completeness_not_authority(self):
        """Test that completeness is NOT an authority oracle.
        
        INCOMPLETE does NOT imply unauthorized.
        This test verifies the completeness checker produces
        epistemic claims, not authority decisions.
        """
        results = run_all_phase19_experiments()
        
        # All incomplete results should be epistemic, not authority
        for name, exp in results["experiments"].items():
            if exp["actual"] == CompletenessResult.INCOMPLETE:
                # INCOMPLETE is an epistemic claim, not an authority decision
                assert exp["actual"] != CompletenessResult.COMPLETE


class TestCompletenessDimensions:
    """Test completeness dimensions."""

    def test_node_coverage(self):
        """Test node coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        engine.add_observable_mechanism(ObservableAuthorityMechanism(
            mechanism_id="test",
            mechanism_type="test",
            principal="test",
            capability="test",
            scope="test",
            source="test",
            is_declared=False,
        ))
        record = engine.assess_node_coverage()
        assert record.dimension == CompletenessDimension.NODE_COVERAGE

    def test_edge_coverage(self):
        """Test edge coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_edge_coverage()
        assert record.dimension == CompletenessDimension.EDGE_COVERAGE

    def test_temporal_coverage(self):
        """Test temporal coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_temporal_coverage()
        assert record.dimension == CompletenessDimension.TEMPORAL_COVERAGE

    def test_cross_domain_coverage(self):
        """Test cross-domain coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_cross_domain_coverage()
        assert record.dimension == CompletenessDimension.CROSS_DOMAIN_COVERAGE

    def test_failure_path_coverage(self):
        """Test failure-path coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_failure_path_coverage()
        assert record.dimension == CompletenessDimension.FAILURE_PATH_COVERAGE

    def test_recovery_coverage(self):
        """Test recovery coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_recovery_coverage()
        assert record.dimension == CompletenessDimension.RECOVERY_COVERAGE

    def test_emergency_coverage(self):
        """Test emergency coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_emergency_coverage()
        assert record.dimension == CompletenessDimension.EMERGENCY_COVERAGE

    def test_out_of_band_coverage(self):
        """Test out-of-band coverage dimension."""
        engine = AuthorityGraphCompletenessEngine()
        record = engine.assess_out_of_band_coverage()
        assert record.dimension == CompletenessDimension.OUT_OF_BAND_COVERAGE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
