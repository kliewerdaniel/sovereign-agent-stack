"""Phase 9 tests: Frontier Composition Semantics.

Tests validate that frontier composition preserves the semantic information
required for governance to make legitimate decisions.
"""

import pytest
from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.authorization_dependencies import (
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_completeness import (
    create_completeness_scope,
)
from examples.sovereign_agent.frontier_composition_semantics import (
    CompositionOperation,
    FrontierCompositionSemanticsEngine,
    ProvenancePreservingComposition,
    RichFrontier,
    SemanticDisagreementType,
    run_adversarial_empty_frontier,
    run_adversarial_scope_widened,
    run_composition_information_loss,
    run_different_frontier_granularity,
    run_different_frontier_same_world_evidence,
    run_evidence_correlation,
    run_identical_frontier_different_completeness,
    run_identical_frontier_different_evidence,
    run_identical_frontier_different_provenance,
    run_identical_frontier_different_scope,
    run_identical_frontier_different_temporal,
    run_malicious_agreement,
    run_provenance_preserving_intersection,
    run_provenance_preserving_union,
)
from examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)


class TestIdenticalFrontierDifferentEvidence:
    """Experiment 1: Identical frontier, different evidence."""

    def test_same_membership_different_evidence(self):
        """Test that same frontier membership can arise from different evidence."""
        result = run_identical_frontier_different_evidence()
        
        # Set composition shows same members
        assert result.set_composition_members == {"E1", "P1", "A1"}
        assert result.provenance_composition_members == {"E1", "P1", "A1"}
        
        # But information is lost
        assert result.information_lost is True
        assert any("Evidence disagreement" in d for d in result.information_loss_details)
        
        # Semantic disagreement is detected
        assert SemanticDisagreementType.EVIDENCE_DISAGREEMENT in result.semantic_disagreements


class TestIdenticalFrontierDifferentCompleteness:
    """Experiment 2: Identical frontier, different completeness."""

    def test_same_membership_different_completeness(self):
        """Test that same frontier membership can arise from different completeness."""
        result = run_identical_frontier_different_completeness()
        
        assert result.set_composition_members == {"E1", "P1", "A1"}
        assert result.information_lost is True
        assert any("Provenance quality disagreement" in d for d in result.information_loss_details)


class TestIdenticalFrontierDifferentScope:
    """Experiment 3: Identical frontier, different scope."""

    def test_same_membership_different_scope(self):
        """Test that same frontier membership can arise from different scopes."""
        result = run_identical_frontier_different_scope()
        
        assert result.set_composition_members == {"E1", "P1", "A1"}
        assert result.information_lost is True
        assert any("Scope disagreement" in d for d in result.information_loss_details)
        assert SemanticDisagreementType.SCOPE_DISAGREEMENT in result.semantic_disagreements


class TestIdenticalFrontierDifferentTemporal:
    """Experiment 4: Identical frontier, different temporal validity."""

    def test_same_membership_different_temporal(self):
        """Test that same frontier membership can arise from different temporal bounds."""
        result = run_identical_frontier_different_temporal()
        
        assert result.set_composition_members == {"E1", "P1", "A1"}
        assert result.information_lost is True
        assert any("Temporal disagreement" in d for d in result.information_loss_details)
        assert SemanticDisagreementType.TEMPORAL_DISAGREEMENT in result.semantic_disagreements


class TestIdenticalFrontierDifferentProvenance:
    """Experiment 5: Identical frontier, different provenance quality."""

    def test_same_membership_different_provenance(self):
        """Test that same frontier membership can arise from different provenance."""
        result = run_identical_frontier_different_provenance()
        
        assert result.set_composition_members == {"E1", "P1", "A1"}
        assert result.information_lost is True
        assert any("Provenance quality disagreement" in d for d in result.information_loss_details)
        assert SemanticDisagreementType.PROVENANCE_DISAGREEMENT in result.semantic_disagreements


class TestDifferentFrontierSameWorldEvidence:
    """Experiment 6: Different frontier, same world evidence."""

    def test_different_membership_same_world(self):
        """Test that different frontier membership can arise from same world evidence."""
        result = run_different_frontier_same_world_evidence()
        
        # Different propositions (P1 vs P2) but same evidence (E1)
        assert "P1" in result.set_composition_members
        assert "P2" in result.set_composition_members
        
        # Epistemic disagreement detected
        assert SemanticDisagreementType.EPISTEMIC_DISAGREEMENT in result.semantic_disagreements


class TestDifferentFrontierGranularity:
    """Experiment 7: Different frontier, different propagation granularity."""

    def test_different_granularity(self):
        """Test that different frontier granularity is handled."""
        result = run_different_frontier_granularity()
        
        # Agent A has {E1,P1,A1}, Agent B has {E1,P1} - different granularity
        assert result.set_composition_members == {"E1", "P1", "A1"}


class TestProvenancePreservingUnion:
    """Experiment 8: Provenance-preserving union."""

    def test_union_preserves_provenance(self):
        """Test that provenance-preserving union preserves agent identity."""
        result = run_provenance_preserving_union()
        
        assert isinstance(result, ProvenancePreservingComposition)
        assert result.operation == CompositionOperation.PROVENANCE_PRESERVING_UNION
        
        # P1 from Agent A, P2 from Agent B
        assert "P1" in result.composed_members
        assert "P2" in result.composed_members
        
        # Provenance preserved
        assert "agent_A" in result.get_member_agents("P1")
        assert "agent_B" in result.get_member_agents("P2")
        
        # Common members have both agents
        assert "agent_A" in result.get_member_agents("E1")
        assert "agent_B" in result.get_member_agents("E1")


class TestProvenancePreservingIntersection:
    """Experiment 9: Provenance-preserving intersection."""

    def test_intersection_preserves_provenance(self):
        """Test that provenance-preserving intersection preserves agent identity."""
        result = run_provenance_preserving_intersection()
        
        assert isinstance(result, ProvenancePreservingComposition)
        assert result.operation == CompositionOperation.PROVENANCE_PRESERVING_INTERSECTION
        
        # Only common members survive
        assert "E1" in result.composed_members
        assert "A1" in result.composed_members
        
        # P1 and P2 are different, so they don't survive intersection
        assert "P1" not in result.composed_members
        assert "P2" not in result.composed_members


class TestEvidenceCorrelation:
    """Experiment 10: Evidence correlation."""

    def test_same_evidence_not_independent(self):
        """Test that same evidence does not imply independent corroboration."""
        result = run_evidence_correlation()
        
        # Both agents use same evidence (E1)
        assert result.set_composition_members == {"E1", "P1", "A1"}
        
        # No information lost because evidence is the same
        assert result.information_lost is False


class TestAdversarialEmptyFrontier:
    """Experiment 11: Adversarial - empty frontier."""

    def test_empty_frontier_does_not_amplify(self):
        """Test that an empty frontier does not amplify authority through composition."""
        result = run_adversarial_empty_frontier()
        
        # Agent A has {E1,P1,A1}, Agent B has {}
        assert result.set_composition_members == {"E1", "P1", "A1"}
        
        # No authority created
        assert result.information_lost is False


class TestAdversarialScopeWidened:
    """Experiment 12: Adversarial - scope widened."""

    def test_scope_widened_detected(self):
        """Test that scope widening is detected as information loss."""
        result = run_adversarial_scope_widened()
        
        assert result.information_lost is True
        assert any("Scope disagreement" in d for d in result.information_loss_details)
        assert SemanticDisagreementType.SCOPE_DISAGREEMENT in result.semantic_disagreements


class TestMaliciousAgreement:
    """Experiment 13: Malicious agreement."""

    def test_malicious_agreement_does_not_amplify(self):
        """Test that N identical outputs do not become stronger authority."""
        result = run_malicious_agreement()
        
        assert isinstance(result, ProvenancePreservingComposition)
        
        # Both agents produce same frontier
        assert "P1" in result.composed_members
        assert "A1" in result.composed_members
        
        # But provenance shows both agents (not authority amplification)
        assert "agent_A" in result.get_member_agents("P1")
        assert "agent_B_malicious" in result.get_member_agents("P1")


class TestCompositionInformationLoss:
    """Experiment 14: Composition information-loss measurement."""

    def test_information_loss_measured(self):
        """Test that information loss is measured during composition."""
        result = run_composition_information_loss()
        
        # Information is lost in set composition
        assert result["information_lost"] is True
        
        # Rich information has more dimensions
        assert result["rich_information"]["agent_count"] == 2
        assert result["rich_information"]["evidence_bases"] == 2
        assert result["rich_information"]["scopes"] == 2
        assert result["rich_information"]["temporal_bounds"] == 2
        
        # Set representation only has member count
        assert "member_count" in result["set_information"]
        
        # Provenance-preserving has more information
        assert result["provenance_information"]["members_with_multiple_agents"] == 2
        assert result["provenance_information"]["members_with_multiple_evidence"] == 2


class TestCompositionAuthorityNonAmplification:
    """Test that composition does not amplify authority."""

    def test_no_authority_from_union(self):
        """Test that union does not create authority."""
        result = run_provenance_preserving_union()
        
        # Composition is never authorization
        assert isinstance(result, ProvenancePreservingComposition)
        # The composed_members is a set, not an authorization
        assert isinstance(result.composed_members, set)

    def test_no_authority_from_intersection(self):
        """Test that intersection does not create authority."""
        result = run_provenance_preserving_intersection()
        
        assert isinstance(result, ProvenancePreservingComposition)
        assert isinstance(result.composed_members, set)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
