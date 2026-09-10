"""Phase 18 tests: Authority Genesis and Sovereign Domain Integration.

Tests verify that the entire effective authority graph can be reconstructed
from explicit trust anchors and bounded delegation without relying on an
implicit authority source.
"""

import pytest
from examples.sovereign_agent.authority_genesis import (
    AuthorityGenesisEngine,
    AuthorityGraphNode,
    AuthoritySourceType,
    GenesisExperimentResult,
    run_all_phase18_experiments,
    run_anchor_integration_test,
    run_authority_exceeding_envelope,
    run_complete_graph_reconstruction,
    run_cross_domain_sovereignty,
    run_detect_cycles,
    run_detect_envelope_violation,
    run_detect_implicit_authority,
    run_self_authorization_prevention,
    run_sovereign_domain_integration,
    run_trace_all_authorities,
)


class TestAuthorityGraph:
    """Test authority graph operations."""

    def test_add_trust_anchor(self):
        """Test adding a trust anchor."""
        engine = AuthorityGenesisEngine()
        node = engine.add_trust_anchor(
            anchor_id="anchor_001",
            principal="admin",
            scope="production",
        )
        assert node.source_type == AuthoritySourceType.TRUST_ANCHOR
        assert node.trust_anchor_id == "anchor_001"

    def test_add_delegated_authority(self):
        """Test adding a delegated authority."""
        engine = AuthorityGenesisEngine()
        engine.add_trust_anchor(
            anchor_id="anchor_001",
            principal="admin",
            scope="production",
        )
        node = engine.add_delegated_authority(
            node_id="policy_admin",
            principal="policy_admin",
            capability="modify_policy",
            scope="production",
            delegator_id="anchor_001",
            trust_anchor_id="anchor_001",
        )
        assert node.source_type == AuthoritySourceType.DELEGATION
        assert node.trust_anchor_id == "anchor_001"

    def test_add_implicit_authority(self):
        """Test adding an implicit authority."""
        engine = AuthorityGenesisEngine()
        node = engine.add_implicit_authority(
            node_id="implicit_admin",
            principal="admin",
            capability="*",
            scope="*",
        )
        assert node.source_type == AuthoritySourceType.IMPLICIT
        assert node.is_implicit is True

    def test_detect_cycles(self):
        """Test cycle detection."""
        engine = AuthorityGenesisEngine()
        engine.add_trust_anchor(
            anchor_id="anchor_001",
            principal="admin",
            scope="production",
        )
        engine.add_delegated_authority(
            node_id="policy_admin",
            principal="policy_admin",
            capability="modify_anchor",
            scope="production",
            delegator_id="anchor_001",
            trust_anchor_id="anchor_001",
        )
        # Create cycle
        engine.authority_graph.add_edge("policy_admin", "anchor_001")
        cycles = engine.authority_graph.detect_cycles()
        assert len(cycles) > 0

    def test_find_implicit_authorities(self):
        """Test implicit authority detection."""
        engine = AuthorityGenesisEngine()
        engine.add_trust_anchor(
            anchor_id="anchor_001",
            principal="admin",
            scope="production",
        )
        engine.add_implicit_authority(
            node_id="implicit_admin",
            principal="admin",
            capability="*",
            scope="*",
        )
        implicit = engine.authority_graph.find_implicit_authorities()
        assert len(implicit) > 0

    def test_traceability(self):
        """Test authority traceability."""
        engine = AuthorityGenesisEngine()
        engine.add_trust_anchor(
            anchor_id="anchor_001",
            principal="admin",
            scope="production",
        )
        engine.add_delegated_authority(
            node_id="policy_admin",
            principal="policy_admin",
            capability="modify_policy",
            scope="production",
            delegator_id="anchor_001",
            trust_anchor_id="anchor_001",
        )
        implicit = engine.authority_graph.find_implicit_authorities()
        assert len(implicit) == 0


class TestTraceAllAuthorities:
    """Test tracing all authorities to trust anchor."""

    def test_all_traceable(self):
        """Test that all authorities are traceable."""
        engine = AuthorityGenesisEngine()
        result = run_trace_all_authorities(engine)
        assert result.result == GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE


class TestDetectImplicitAuthority:
    """Test implicit authority detection."""

    def test_implicit_detected(self):
        """Test that implicit authority is detected."""
        engine = AuthorityGenesisEngine()
        result = run_detect_implicit_authority(engine)
        assert result.result == GenesisExperimentResult.IMPLICIT_AUTHORITY_DETECTED


class TestDetectCycles:
    """Test cycle detection."""

    def test_cycles_detected(self):
        """Test that cycles are detected."""
        engine = AuthorityGenesisEngine()
        result = run_detect_cycles(engine)
        assert result.result == GenesisExperimentResult.CYCLE_DETECTED


class TestDetectEnvelopeViolation:
    """Test envelope violation detection."""

    def test_envelope_violation(self):
        """Test envelope violation detection."""
        engine = AuthorityGenesisEngine()
        result = run_detect_envelope_violation(engine)
        assert result.result == GenesisExperimentResult.ENVELOPE_VIOLATION


class TestSovereignDomainIntegration:
    """Test sovereign domain integration."""

    def test_sovereign_domains(self):
        """Test sovereign domain integration."""
        engine = AuthorityGenesisEngine()
        result = run_sovereign_domain_integration(engine)
        assert result.result == GenesisExperimentResult.CROSS_DOMAIN_SOVEREIGN


class TestAnchorIntegration:
    """Test anchor integration."""

    def test_anchor_integrated(self):
        """Test that anchor is integrated into production path."""
        engine = AuthorityGenesisEngine()
        result = run_anchor_integration_test(engine)
        assert result.result == GenesisExperimentResult.ANCHOR_INTEGRATED


class TestSelfAuthorizationPrevention:
    """Test self-authorization prevention."""

    def test_self_authorization_detected(self):
        """Test that self-authorization is detected."""
        engine = AuthorityGenesisEngine()
        result = run_self_authorization_prevention(engine)
        assert result.result == GenesisExperimentResult.CYCLE_DETECTED


class TestCrossDomainSovereignty:
    """Test cross-domain sovereignty."""

    def test_cross_domain(self):
        """Test cross-domain sovereignty preservation."""
        engine = AuthorityGenesisEngine()
        result = run_cross_domain_sovereignty(engine)
        assert result.result == GenesisExperimentResult.CROSS_DOMAIN_SOVEREIGN


class TestAuthorityExceedingEnvelope:
    """Test authority exceeding envelope."""

    def test_envelope_violation(self):
        """Test authority exceeding envelope detection."""
        engine = AuthorityGenesisEngine()
        result = run_authority_exceeding_envelope(engine)
        assert result.result == GenesisExperimentResult.ENVELOPE_VIOLATION


class TestCompleteGraphReconstruction:
    """Test complete graph reconstruction."""

    def test_complete_reconstruction(self):
        """Test complete graph reconstruction."""
        engine = AuthorityGenesisEngine()
        result = run_complete_graph_reconstruction(engine)
        assert result.result == GenesisExperimentResult.ALL_AUTHORITIES_TRACEABLE


class TestAllPhase18Experiments:
    """Test all Phase 18 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 18 experiments run."""
        results = run_all_phase18_experiments()
        assert results["total_experiments"] == 10

    def test_all_traceable_count(self):
        """Test that all authorities are traceable."""
        results = run_all_phase18_experiments()
        assert results["all_traceable_count"] >= 2

    def test_implicit_detected(self):
        """Test that implicit authority is detected."""
        results = run_all_phase18_experiments()
        assert results["implicit_detected_count"] >= 1

    def test_cycles_detected(self):
        """Test that cycles are detected."""
        results = run_all_phase18_experiments()
        assert results["cycle_detected_count"] >= 1

    def test_sovereign_domains(self):
        """Test that sovereign domains are valid."""
        results = run_all_phase18_experiments()
        assert results["cross_domain_sovereign_count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
