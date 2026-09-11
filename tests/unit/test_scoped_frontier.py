"""Phase 5 tests: Conditional and Scoped Frontier Semantics.

Tests determine how conditionality changes semantic impact.
Documents the gap between expected scoped behavior and current implementation.
"""

import pytest
from research.examples.sovereign_agent.scoped_frontier_experiment import (
    ScopeDimension,
    ScopedFrontierResult,
    analyze_scoped_results,
    run_all_scoped_frontier_experiments,
    test_actor_scope,
    test_domain_scope,
    test_environment_scope,
    test_feature_flag_scope,
    test_operation_scope,
    test_temporal_scope,
    test_unknown_scope,
)
from research.examples.sovereign_agent.frontier_impact_propagation import (
    PropagationRule,
)


class TestEnvironmentScope:
    """Tests for environment-scoped frontier propagation."""

    def test_production_mutation_affects_production(self):
        """Test that production mutation affects production artifacts."""
        results = test_environment_scope()
        prod_result = next(r for r in results if r.test_name == "environment_production")

        assert prod_result.scope_matches is True
        assert "E1" in prod_result.expected_frontier
        assert "P1" in prod_result.expected_frontier
        assert "A1" in prod_result.expected_frontier

    def test_production_mutation_excludes_staging(self):
        """Test that production mutation excludes staging artifacts."""
        results = test_environment_scope()
        staging_result = next(r for r in results if r.test_name == "environment_staging")

        assert staging_result.scope_matches is False
        # Staging should NOT be affected by production mutation
        assert staging_result.expected_frontier == set()


class TestFeatureFlagScope:
    """Tests for feature-flag-scoped frontier propagation."""

    def test_flag_enabled_affects_enabled_artifacts(self):
        """Test that mutation with flag enabled affects enabled artifacts."""
        results = test_feature_flag_scope()
        enabled_result = next(r for r in results if r.test_name == "feature_flag_enabled")

        assert enabled_result.scope_matches is True
        assert "P1" in enabled_result.expected_frontier
        assert "A1" in enabled_result.expected_frontier

    def test_flag_disabled_affects_disabled_artifacts(self):
        """Test that mutation with flag disabled affects disabled artifacts."""
        results = test_feature_flag_scope()
        disabled_result = next(r for r in results if r.test_name == "feature_flag_disabled")

        assert disabled_result.scope_matches is True
        assert "P2" in disabled_result.expected_frontier
        assert "A2" in disabled_result.expected_frontier


class TestTemporalScope:
    """Tests for temporal-scoped frontier propagation."""

    def test_t2_mutation_affects_t0_t5_scope(self):
        """Test that T2 mutation affects [T0,T5] scope."""
        results = test_temporal_scope()
        t2_result = next(r for r in results if r.test_name == "temporal_t2")

        assert t2_result.scope_matches is True
        assert "P1" in t2_result.expected_frontier
        assert "A1" in t2_result.expected_frontier

    def test_t7_mutation_affects_t5_t10_scope(self):
        """Test that T7 mutation affects [T5,T10] scope."""
        results = test_temporal_scope()
        t7_result = next(r for r in results if r.test_name == "temporal_t7")

        assert t7_result.scope_matches is True
        assert "P2" in t7_result.expected_frontier
        assert "A2" in t7_result.expected_frontier


class TestActorScope:
    """Tests for actor-scoped frontier propagation."""

    def test_shared_dependency_affects_both_actors(self):
        """Test that shared dependency affects both actors."""
        results = test_actor_scope()
        
        # Both operators should be affected by E1 mutation (shared P1)
        actor_1_result = next(r for r in results if r.test_name == "actor_operator_1")
        actor_2_result = next(r for r in results if r.test_name == "actor_operator_2")

        assert actor_1_result.scope_matches is True
        assert actor_2_result.scope_matches is True
        assert "A1" in actor_1_result.expected_frontier
        assert "A2" in actor_2_result.expected_frontier


class TestOperationScope:
    """Tests for operation-scoped frontier propagation."""

    def test_shared_dependency_affects_both_operations(self):
        """Test that shared dependency affects both operations."""
        results = test_operation_scope()
        
        payment_result = next(r for r in results if r.test_name == "operation_payment")
        refund_result = next(r for r in results if r.test_name == "operation_refund")

        assert payment_result.scope_matches is True
        assert refund_result.scope_matches is True
        assert "A1" in payment_result.expected_frontier
        assert "A2" in refund_result.expected_frontier


class TestDomainScope:
    """Tests for sovereign-domain-scoped frontier propagation."""

    def test_domain_a_mutation_affects_domain_a(self):
        """Test that Domain A mutation affects Domain A artifacts."""
        results = test_domain_scope()
        domain_a_result = next(r for r in results if r.test_name == "domain_a")

        assert domain_a_result.scope_matches is True
        assert "P1" in domain_a_result.expected_frontier
        assert "A1" in domain_a_result.expected_frontier

    def test_domain_a_mutation_excludes_domain_b(self):
        """Test that Domain A mutation excludes Domain B artifacts."""
        results = test_domain_scope()
        domain_b_result = next(r for r in results if r.test_name == "domain_b")

        assert domain_b_result.scope_matches is False
        # Domain B should NOT be affected by Domain A mutation
        assert domain_b_result.expected_frontier == set()


class TestUnknownScope:
    """Tests for unknown scope handling."""

    def test_unknown_scope_not_out_of_scope(self):
        """Test that unknown scope is NOT treated as out-of-scope."""
        results = test_unknown_scope()
        unknown_result = next(r for r in results if r.test_name == "unknown_scope")

        # Unknown scope should require evaluation, not exclusion
        assert unknown_result.propagation_rule == PropagationRule.REQUIRES_EVALUATION
        # At minimum, E1 should be in the frontier
        assert "E1" in unknown_result.expected_frontier


class TestScopedFrontierAnalysis:
    """Tests for the scoped frontier analysis."""

    def test_analysis_finds_scope_dimensions(self):
        """Test that analysis finds all scope dimensions."""
        results = run_all_scoped_frontier_experiments()
        analysis = analyze_scoped_results(results)

        assert len(analysis["dimensions_tested"]) >= 6

    def test_analysis_finds_scope_mismatches(self):
        """Test that analysis finds scope mismatches."""
        results = run_all_scoped_frontier_experiments()
        analysis = analyze_scoped_results(results)

        # Should find at least 2 scope mismatches (staging, domain_b)
        assert analysis["scope_mismatches"] >= 2

    def test_analysis_finds_under_approximations(self):
        """Test that analysis finds under-approximations."""
        results = run_all_scoped_frontier_experiments()
        analysis = analyze_scoped_results(results)

        # Most cases should be under-approximated (current implementation only returns {E1})
        assert analysis["under_approximated"] >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
