"""Phase 10 tests: Rich Frontier Governance.

Tests validate that governance decisions are investigated for semantic
dependence on rich frontier information.
"""

import pytest
from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.authority_frontier_integration import (
    AuthorityFrontierIntegrator,
    GovernanceAction,
)
from examples.sovereign_agent.authorization_dependencies import (
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_completeness import (
    create_completeness_scope,
)
from examples.sovereign_agent.frontier_composition_semantics import (
    CompositionOperation,
    FrontierCompositionSemanticsEngine,
    SemanticDisagreementType,
)
from examples.sovereign_agent.rich_frontier_governance import (
    GovernanceInputContract,
    GovernanceInputType,
    GovernanceSemanticDependence,
    RichFrontierGovernanceEngine,
    classify_phase10_result,
    run_baseline_identical_membership_different_semantics,
    run_case_1_same_membership_different_evidence,
    run_case_2_same_membership_different_completeness,
    run_case_3_same_membership_different_scope,
    run_case_4_same_membership_different_temporal,
    run_case_5_same_membership_different_provenance,
    run_case_6_same_membership_different_agent,
    run_case_7_same_membership_different_epistemic,
    run_case_8_different_membership_same_world,
    run_case_9_different_membership_different_algorithms,
    run_case_10_same_membership_correlated_evidence,
    run_controlled_semantic_contrasts,
    run_malicious_agreement_tests,
)
from examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)


class TestGovernanceInputContract:
    """Test that the governance input contract is correctly established."""

    def test_current_governance_consumes_only_membership(self):
        """Test that current governance only consumes membership."""
        engine = RichFrontierGovernanceEngine()
        contract = engine.establish_governance_input_contract()
        
        assert contract.consumes_membership is True
        assert contract.consumes_agent_identity is False
        assert contract.consumes_evidence_basis is False
        assert contract.consumes_scope is False
        assert contract.consumes_temporal_validity is False
        assert contract.consumes_provenance_quality is False
        assert contract.consumes_completeness is False


class TestBaselineExperiment:
    """Test the baseline experiment: identical membership, different semantics."""

    def test_memberships_are_equal(self):
        """Test that the two frontiers have equal membership."""
        result = run_baseline_identical_membership_different_semantics()
        
        assert result["memberships_equal"] is True
        assert result["membership_a"] == {"E1", "P1", "A1"}
        assert result["membership_b"] == {"E1", "P1", "A1"}

    def test_governance_decisions_are_same(self):
        """Test that governance produces the same decisions for both."""
        result = run_baseline_identical_membership_different_semantics()
        
        # Both produce REVIEW_REQUIRED because both contain A1
        assert result["decisions_differ"] is False
        assert result["rich_result_a"].governance_action == GovernanceAction.REVIEW_REQUIRED
        assert result["rich_result_b"].governance_action == GovernanceAction.REVIEW_REQUIRED


class TestControlledSemanticContrasts:
    """Test controlled semantic contrast experiments."""

    def test_case_1_same_membership_different_evidence(self):
        """Case 1: Same membership, different evidence."""
        result = run_case_1_same_membership_different_evidence()
        
        assert result["memberships_equal"] is True
        # Governance produces same decision because membership is the same
        assert result["decisions_differ"] is False

    def test_case_2_same_membership_different_completeness(self):
        """Case 2: Same membership, different completeness."""
        result = run_case_2_same_membership_different_completeness()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_case_3_same_membership_different_scope(self):
        """Case 3: Same membership, different scope."""
        result = run_case_3_same_membership_different_scope()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_case_4_same_membership_different_temporal(self):
        """Case 4: Same membership, different temporal validity."""
        result = run_case_4_same_membership_different_temporal()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_case_5_same_membership_different_provenance(self):
        """Case 5: Same membership, different provenance quality."""
        result = run_case_5_same_membership_different_provenance()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_case_6_same_membership_different_agent(self):
        """Case 6: Same membership, different agent identity."""
        result = run_case_6_same_membership_different_agent()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_case_7_same_membership_different_epistemic(self):
        """Case 7: Same membership, different epistemic state."""
        result = run_case_7_same_membership_different_epistemic()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_case_8_different_membership_same_world(self):
        """Case 8: Different membership, same underlying world."""
        result = run_case_8_different_membership_same_world()
        
        assert result["memberships_equal"] is False
        assert result["decisions_differ"] is False

    def test_case_9_different_membership_different_algorithms(self):
        """Case 9: Different membership from different algorithms."""
        result = run_case_9_different_membership_different_algorithms()
        
        # Agent A has A1, Agent B doesn't - but both trigger review
        assert result["decisions_differ"] is False

    def test_case_10_same_membership_correlated_evidence(self):
        """Case 10: Same membership from N agents with correlated evidence."""
        result = run_case_10_same_membership_correlated_evidence()
        
        assert result["memberships_equal"] is True
        assert result["decisions_differ"] is False

    def test_all_contrasts_produce_results(self):
        """Test that all contrasts produce results."""
        results = run_controlled_semantic_contrasts()
        
        assert len(results) == 10
        for r in results:
            assert "case" in r
            assert "memberships_equal" in r
            assert "decisions_differ" in r


class TestMaliciousAgreement:
    """Test malicious agreement scenarios."""

    def test_malicious_agreement_identical_evidence(self):
        """Test: N agents producing same frontier from identical evidence."""
        results = run_malicious_agreement_tests()
        test = [r for r in results if r["test"] == "malicious_agreement_identical_evidence"][0]
        
        assert test["governance_action"] == "review_required"
        assert test["authority_amplified"] is False

    def test_malicious_agreement_false_completeness(self):
        """Test: N agents claiming COMPLETE but actually incomplete."""
        results = run_malicious_agreement_tests()
        test = [r for r in results if r["test"] == "malicious_agreement_false_completeness"][0]
        
        assert test["governance_action"] == "review_required"
        assert test["authority_amplified"] is False

    def test_malicious_scope_laundering(self):
        """Test: Scope laundering attempt."""
        results = run_malicious_agreement_tests()
        test = [r for r in results if r["test"] == "malicious_scope_laundering"][0]
        
        assert test["governance_action"] == "review_required"
        assert test["scope_disagreement_detected"] is True


class TestGovernanceAuthorityNonAmplification:
    """Test that governance does not amplify authority."""

    def test_no_authority_from_rich_frontier(self):
        """Test that rich frontier governance does not create authority."""
        engine = RichFrontierGovernanceEngine()
        scope = create_completeness_scope("p1", "payment")
        
        dep_graph = build_authorization_dependency_graph(
            authorization_id="auth_001", evidence_ids=["E1"], proposition_id="P1",
            epistemic_state_id="S1", experiment_id="exp_001", recommendation_id="rec_001",
            governance_policy_id="gov_001", resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01", provenance=["src_001"],
        )
        
        frontier = engine.semantics_engine.compute_rich_frontier(
            agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="t0_change", timestamp="2026-01-01T00:00:00Z",
                event_type="dependency_mutated", description="E1 mutated",
                affected_actor="A1", affected_component="A1",
                previous_state={"E1": "old"}, new_state={"E1": "new"},
            ),
            authorization_id="auth_001", dependency_graph=dep_graph,
            proposition_graph=create_scoped_proposition_graph({"P1": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P1"]}),
            scope=scope, known_dependencies=["E1"], known_propositions=["P1"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = engine.govern_from_rich_frontier(
            frontier, "auth_001", {"auth_001": "authorized"}, {"scope": "production"}
        )
        
        assert result.frontier_created_authorization is False
        assert result.frontier_revoked_authorization is False

    def test_no_authority_from_provenance_composition(self):
        """Test that provenance composition governance does not create authority."""
        engine = RichFrontierGovernanceEngine()
        scope = create_completeness_scope("p1", "payment")
        
        dep_graph = build_authorization_dependency_graph(
            authorization_id="auth_001", evidence_ids=["E1"], proposition_id="P1",
            epistemic_state_id="S1", experiment_id="exp_001", recommendation_id="rec_001",
            governance_policy_id="gov_001", resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01", provenance=["src_001"],
        )
        
        frontier_a = engine.semantics_engine.compute_rich_frontier(
            agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="t0_change", timestamp="2026-01-01T00:00:00Z",
                event_type="dependency_mutated", description="E1 mutated",
                affected_actor="A1", affected_component="A1",
                previous_state={"E1": "old"}, new_state={"E1": "new"},
            ),
            authorization_id="auth_001", dependency_graph=dep_graph,
            proposition_graph=create_scoped_proposition_graph({"P1": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P1"]}),
            scope=scope, known_dependencies=["E1"], known_propositions=["P1"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        frontier_b = engine.semantics_engine.compute_rich_frontier(
            agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="t0_change", timestamp="2026-01-01T00:00:00Z",
                event_type="dependency_mutated", description="E1 mutated",
                affected_actor="A1", affected_component="A1",
                previous_state={"E1": "old"}, new_state={"E1": "new"},
            ),
            authorization_id="auth_001", dependency_graph=dep_graph,
            proposition_graph=create_scoped_proposition_graph({"P1": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P1"]}),
            scope=scope, known_dependencies=["E1"], known_propositions=["P1"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        comp = engine.semantics_engine.compose_provenance_preserving(
            frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
        )
        
        result = engine.govern_from_provenance_composition(
            comp, "auth_001", {"auth_001": "authorized"}, {"scope": "production"}
        )
        
        assert result.frontier_created_authorization is False
        assert result.frontier_revoked_authorization is False


class TestPhase10Classification:
    """Test the Phase 10 classification."""

    def test_classification_is_projection_sufficient(self):
        """Test that the classification is GOVERNANCE_PROJECTION_SUFFICIENT."""
        from examples.sovereign_agent.rich_frontier_governance import run_all_phase10_experiments
        
        results = run_all_phase10_experiments()
        classification = classify_phase10_result(results)
        
        # The current governance model produces the same decisions regardless
        # of rich frontier information
        assert classification == GovernanceSemanticDependence.GOVERNANCE_PROJECTION_SUFFICIENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
