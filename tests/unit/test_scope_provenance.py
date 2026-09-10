"""Phase 5.6 tests: Scope Provenance and Semantic Scope Authority.

Tests validate the ScopeProvenanceEngine's decisions about scope propagation.
"""

import pytest
from examples.sovereign_agent.authorization_dependencies import (
    DependencyStrength,
    DependencyType,
)
from examples.sovereign_agent.dependency_completeness import (
    create_completeness_scope,
)
from examples.sovereign_agent.scope_provenance_experiment import (
    ScopeAuthority,
    ScopeProvenanceEngine,
    ScopeProvenanceResult,
    ScopeSource,
    ScopedArtifact,
    run_scope_provenance_experiments,
)


class TestScopeProvenance:
    """Tests for scope provenance decisions."""

    def test_independent_scope_prevents_propagation(self):
        """Test that downstream with independent scope prevents upstream propagation."""
        engine = ScopeProvenanceEngine()

        upstream = ScopedArtifact(
            artifact_id="E1",
            artifact_type="dependency",
            scope=create_completeness_scope("p1", "payment", environment="production"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )
        downstream = ScopedArtifact(
            artifact_id="P1",
            artifact_type="proposition",
            scope=create_completeness_scope("p1", "payment", environment="production"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )

        result = engine.investigate_scope_propagation(
            upstream, downstream, DependencyType.EVIDENCE, DependencyStrength.DIRECT,
        )

        # Downstream has independent scope, so upstream scope should NOT propagate
        assert result.expected_propagation is False
        assert result.scope_source == ScopeSource.DECLARED
        assert result.scope_authority == ScopeAuthority.ESTABLISHED

    def test_unknown_scope_allows_propagation(self):
        """Test that downstream with unknown scope allows upstream propagation."""
        engine = ScopeProvenanceEngine()

        upstream = ScopedArtifact(
            artifact_id="E1",
            artifact_type="dependency",
            scope=create_completeness_scope("p1", "payment", environment="production"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )
        downstream = ScopedArtifact(
            artifact_id="P1",
            artifact_type="proposition",
            scope=create_completeness_scope("p1", "payment", environment="unknown"),
            scope_source=ScopeSource.UNKNOWN,
            scope_authority=ScopeAuthority.UNKNOWN,
        )

        result = engine.investigate_scope_propagation(
            upstream, downstream, DependencyType.EVIDENCE, DependencyStrength.DIRECT,
        )

        # Downstream has no independent scope, relationship permits propagation
        assert result.expected_propagation is True
        assert result.scope_source == ScopeSource.INHERITED
        assert result.scope_authority == ScopeAuthority.PROPAGATED

    def test_transitive_relationship_blocks_propagation(self):
        """Test that transitive relationships block scope propagation."""
        engine = ScopeProvenanceEngine()

        upstream = ScopedArtifact(
            artifact_id="E1",
            artifact_type="dependency",
            scope=create_completeness_scope("p1", "payment", environment="production"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )
        downstream = ScopedArtifact(
            artifact_id="AUDIT_LOG",
            artifact_type="audit",
            scope=create_completeness_scope("p1", "payment", environment="unknown"),
            scope_source=ScopeSource.UNKNOWN,
            scope_authority=ScopeAuthority.UNKNOWN,
        )

        result = engine.investigate_scope_propagation(
            upstream, downstream, DependencyType.PROVENANCE, DependencyStrength.TRANSITIVE,
        )

        # Transitive relationship does not permit scope propagation
        assert result.expected_propagation is False
        assert result.scope_source == ScopeSource.UNKNOWN
        assert result.scope_authority == ScopeAuthority.UNKNOWN

    def test_cross_domain_with_independent_scope(self):
        """Test that cross-domain scope doesn't propagate when downstream has independent scope."""
        engine = ScopeProvenanceEngine()

        upstream = ScopedArtifact(
            artifact_id="E1",
            artifact_type="dependency",
            scope=create_completeness_scope("p1", "payment", domain="DOMAIN_A"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )
        downstream = ScopedArtifact(
            artifact_id="P1",
            artifact_type="proposition",
            scope=create_completeness_scope("p1", "payment", domain="DOMAIN_B"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )

        result = engine.investigate_scope_propagation(
            upstream, downstream, DependencyType.EVIDENCE, DependencyStrength.DIRECT,
        )

        # Downstream has independent scope in different domain
        assert result.expected_propagation is False
        assert result.scope_source == ScopeSource.DECLARED
        assert result.scope_authority == ScopeAuthority.ESTABLISHED


class TestScopeProvenanceExperiments:
    """Tests for the full scope provenance experiment suite."""

    def test_all_experiments_produce_results(self):
        """Test that all experiments produce results."""
        results = run_scope_provenance_experiments()

        assert len(results) >= 4

    def test_all_results_match_expected(self):
        """Test that all results match expected propagation decisions."""
        results = run_scope_provenance_experiments()

        for r in results:
            assert r.expected_propagation == r.actual_propagation, \
                f"Mismatch in {r.test_name}: expected={r.expected_propagation}, actual={r.actual_propagation}"

    def test_scope_sources_are_valid(self):
        """Test that scope sources are valid enum values."""
        results = run_scope_provenance_experiments()

        for r in results:
            assert isinstance(r.scope_source, ScopeSource)
            assert isinstance(r.scope_authority, ScopeAuthority)


class TestScopedArtifact:
    """Tests for ScopedArtifact data structure."""

    def test_scoped_artifact_creation(self):
        """Test creating a scoped artifact."""
        artifact = ScopedArtifact(
            artifact_id="E1",
            artifact_type="dependency",
            scope=create_completeness_scope("p1", "payment", environment="production"),
            scope_source=ScopeSource.DECLARED,
            scope_authority=ScopeAuthority.ESTABLISHED,
        )

        assert artifact.artifact_id == "E1"
        assert artifact.scope_source == ScopeSource.DECLARED
        assert artifact.scope_authority == ScopeAuthority.ESTABLISHED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
