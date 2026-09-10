"""Phase 4.5 tests: Frontier Impact Propagation.

Tests that determine what "affected" means for a revalidation frontier,
which edge types permit impact propagation, and which explicitly prohibit it.
"""

import pytest
from examples.sovereign_agent.frontier_impact_propagation import (
    ImpactPropagationResult,
    PropagationRule,
    analyze_propagation_results,
    run_all_propagation_experiments,
    test_minimal_chain_propagation,
    test_non_propagation_by_edge_type,
    test_revalidation_vs_invalidation,
    test_scope_limited_propagation,
    test_selective_propagation,
    test_shared_dependency_propagation,
)
from examples.sovereign_agent.authorization_dependencies import (
    DependencyType,
    DependencyStrength,
)


class TestMinimalChainPropagation:
    """Tests for impact propagation through a minimal chain."""

    def test_all_layers_affected(self):
        """Test that all layers in a minimal chain are affected."""
        result = test_minimal_chain_propagation()
        
        # All layers should be in the expected frontier
        assert "E1" in result.expected_minimum_frontier
        assert "P1" in result.expected_minimum_frontier
        assert "S1" in result.expected_minimum_frontier
        assert "A1" in result.expected_minimum_frontier

    def test_directly_changed_is_dependency(self):
        """Test that only the dependency is directly changed."""
        result = test_minimal_chain_propagation()
        
        assert result.directly_changed == {"E1"}

    def test_epistemic_and_authority_impact(self):
        """Test that epistemic and authority layers are affected."""
        result = test_minimal_chain_propagation()
        
        assert "P1" in result.epistemically_affected
        assert "S1" in result.epistemically_affected
        assert "A1" in result.authority_affected


class TestSelectivePropagation:
    """Tests for selective propagation based on semantic dependency."""

    def test_semantic_dependency_excludes_unrelated(self):
        """Test that semantic dependency excludes unrelated artifacts."""
        result = test_selective_propagation()
        
        # P2 and A2 should NOT be in the frontier
        assert "P2" in result.unaffected
        assert "A2" in result.unaffected

    def test_semantic_dependency_includes_related(self):
        """Test that semantic dependency includes related artifacts."""
        result = test_selective_propagation()
        
        # P1 and A1 should be in the frontier
        assert "P1" in result.expected_minimum_frontier
        assert "A1" in result.expected_minimum_frontier


class TestSharedDependencyPropagation:
    """Tests for propagation through shared dependencies."""

    def test_shared_dependency_affects_all_dependents(self):
        """Test that a shared dependency affects all its dependents."""
        result = test_shared_dependency_propagation()
        
        # All propositions should be affected
        assert "P1" in result.epistemically_affected
        assert "P2" in result.epistemically_affected
        assert "P3" in result.epistemically_affected
        
        # All authorizations should be affected
        assert "A1" in result.authority_affected
        assert "A2" in result.authority_affected
        assert "A3" in result.authority_affected


class TestNonPropagationByEdgeType:
    """Tests for edge types that prohibit propagation."""

    def test_observability_does_not_propagate(self):
        """Test that observability edges don't propagate impact."""
        result = test_non_propagation_by_edge_type()
        
        assert "OBSERVABILITY_TAG" in result.unaffected

    def test_audit_reference_does_not_propagate(self):
        """Test that audit reference edges don't propagate impact."""
        result = test_non_propagation_by_edge_type()
        
        assert "AUDIT_LOG" in result.unaffected

    def test_only_dependency_is_affected(self):
        """Test that only the dependency itself is affected."""
        result = test_non_propagation_by_edge_type()
        
        assert result.expected_minimum_frontier == {"E1"}


class TestScopeLimitedPropagation:
    """Tests for scope-limited propagation."""

    def test_production_mutation_excludes_staging(self):
        """Test that production mutation excludes staging artifacts."""
        result = test_scope_limited_propagation()
        
        assert "P1_staging" in result.unaffected
        assert "A1_staging" in result.unaffected

    def test_production_mutation_includes_production(self):
        """Test that production mutation includes production artifacts."""
        result = test_scope_limited_propagation()
        
        assert "P1_prod" in result.expected_minimum_frontier
        assert "A1_prod" in result.expected_minimum_frontier


class TestRevalidationVsInvalidation:
    """Tests for revalidation vs invalidation distinction."""

    def test_frontier_membership_is_not_invalidation(self):
        """Test that frontier membership does NOT equal invalidation."""
        result = test_revalidation_vs_invalidation()
        
        # Frontier membership means revalidation candidate
        # NOT invalidation
        assert "A1" in result.expected_minimum_frontier
        # The artifact should be in the revalidation surface
        # but this does NOT mean it's invalid


class TestPropagationAnalysis:
    """Tests for the propagation analysis."""

    def test_analysis_finds_propagation_cases(self):
        """Test that analysis finds propagation cases."""
        results = run_all_propagation_experiments()
        analysis = analyze_propagation_results(results)
        
        assert analysis["propagation_cases"] > 0

    def test_analysis_finds_non_propagation_cases(self):
        """Test that analysis finds non-propagation cases."""
        results = run_all_propagation_experiments()
        analysis = analyze_propagation_results(results)
        
        assert analysis["non_propagation_cases"] > 0

    def test_analysis_derives_propagation_law(self):
        """Test that analysis derives a propagation law."""
        results = run_all_propagation_experiments()
        analysis = analyze_propagation_results(results)
        
        assert "FRONTIER" in analysis["minimum_propagation_law"]
        assert "PROPAGATION" in analysis["minimum_propagation_law"]


class TestEdgeSemantics:
    """Tests for edge semantics."""

    def test_evidence_edge_propagates(self):
        """Test that evidence edges propagate impact."""
        result = test_minimal_chain_propagation()
        
        evidence_edges = [
            e for e in result.edge_semantics
            if e.edge_type == DependencyType.EVIDENCE
        ]
        assert len(evidence_edges) > 0
        assert evidence_edges[0].propagation_rule == PropagationRule.PROPAGATES

    def test_provenance_edge_does_not_propagate(self):
        """Test that provenance edges don't propagate impact."""
        result = test_non_propagation_by_edge_type()
        
        provenance_edges = [
            e for e in result.edge_semantics
            if e.edge_type == DependencyType.PROVENANCE
        ]
        assert len(provenance_edges) > 0
        assert provenance_edges[0].propagation_rule == PropagationRule.DOES_NOT_PROPAGATE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
