"""Phase 5.5 tests: Scoped Impact Propagation.

Tests validate the ScopedImpactPropagationEngine against semantic requirements.
"""

import pytest
from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    DependencyStrength,
    DependencyType,
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from research.examples.sovereign_agent.scoped_impact_propagation import (
    ScopedFrontier,
    ScopedFrontierMember,
    ScopedImpactPropagationEngine,
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from research.examples.sovereign_agent.scoped_propagation_experiment import (
    PropagationExperimentResult,
    run_all_propagation_experiments,
    run_scope_mismatch_experiment,
    run_typed_propagation_experiment,
    run_unknown_scope_experiment,
)


class TestTypedPropagation:
    """Tests for typed semantic propagation."""

    def test_typed_propagation_includes_all_layers(self):
        """Test that typed propagation includes dependency, proposition, and authorization."""
        results = run_typed_propagation_experiment()
        result = results[0]

        # All layers should be in the frontier
        assert "E1" in result.actual_members
        assert "P1" in result.actual_members
        assert "A1" in result.actual_members

    def test_typed_propagation_by_type(self):
        """Test that each artifact type is correctly classified."""
        results = run_typed_propagation_experiment()
        result = results[0]

        assert "E1" in result.actual_by_type["dependency"]
        assert "P1" in result.actual_by_type["proposition"]
        assert "A1" in result.actual_by_type["authorization"]

    def test_typed_propagation_scope_matches(self):
        """Test that scope matches for typed propagation."""
        results = run_typed_propagation_experiment()
        result = results[0]

        assert result.scope_matches is True


class TestScopeMismatch:
    """Tests for scope mismatch handling."""

    def test_scope_mismatch_documents_limitation(self):
        """Test that scope mismatch documents the metadata limitation."""
        results = run_scope_mismatch_experiment()
        result = results[0]

        # The dependency itself should be in the frontier
        assert "E1" in result.actual_members
        # Scope doesn't match
        assert result.scope_matches is False


class TestUnknownScope:
    """Tests for unknown scope handling."""

    def test_unknown_scope_includes_dependency(self):
        """Test that unknown scope still includes the dependency."""
        results = run_unknown_scope_experiment()
        result = results[0]

        # E1 should be in the frontier
        assert "E1" in result.actual_members

    def test_unknown_scope_excludes_downstream(self):
        """Test that unknown scope excludes downstream artifacts."""
        results = run_unknown_scope_experiment()
        result = results[0]

        # P1 and A1 should NOT be in the frontier (unknown scope)
        assert "P1" not in result.actual_members
        assert "A1" not in result.actual_members

    def test_unknown_scope_status(self):
        """Test that unknown scope results in appropriate completeness status."""
        results = run_unknown_scope_experiment()
        result = results[0]

        # Completeness should reflect the unknown scope
        assert result.completeness_status in (
            CompletenessStatus.UNKNOWN,
            CompletenessStatus.KNOWN_INCOMPLETE,
        )


class TestScopedFrontier:
    """Tests for the ScopedFrontier data structure."""

    def test_scoped_frontier_is_not_authoritative(self):
        """Test that a scoped frontier is never authoritative."""
        frontier = ScopedFrontier(
            frontier_id="test",
            world_change_id="test",
            authorization_id="test",
            timestamp="2026-01-01T00:00:00Z",
        )

        assert frontier.is_authoritative() is False

    def test_scoped_frontier_empty(self):
        """Test empty frontier detection."""
        frontier = ScopedFrontier(
            frontier_id="test",
            world_change_id="test",
            authorization_id="test",
            timestamp="2026-01-01T00:00:00Z",
        )

        assert frontier.is_empty() is True

    def test_scoped_frontier_members_by_type(self):
        """Test member type filtering."""
        frontier = ScopedFrontier(
            frontier_id="test",
            world_change_id="test",
            authorization_id="test",
            timestamp="2026-01-01T00:00:00Z",
            members=[
                ScopedFrontierMember(
                    artifact_id="E1",
                    artifact_type="dependency",
                    scope=create_completeness_scope("p1", "payment"),
                ),
                ScopedFrontierMember(
                    artifact_id="P1",
                    artifact_type="proposition",
                    scope=create_completeness_scope("p1", "payment"),
                ),
            ],
        )

        deps = frontier.get_members_by_type("dependency")
        props = frontier.get_members_by_type("proposition")

        assert len(deps) == 1
        assert len(props) == 1
        assert deps[0].artifact_id == "E1"
        assert props[0].artifact_id == "P1"


class TestPropagationExperimentResults:
    """Tests for the experiment results."""

    def test_all_experiments_produce_results(self):
        """Test that all experiments produce results."""
        results = run_all_propagation_experiments()

        assert len(results) >= 3

    def test_results_have_expected_fields(self):
        """Test that results have all expected fields."""
        results = run_all_propagation_experiments()

        for r in results:
            assert r.test_name
            assert r.changed_dependency
            assert r.expected_members is not None
            assert r.actual_members is not None
            assert r.completeness_status is not None
            assert r.intersection_status is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
