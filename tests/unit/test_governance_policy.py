"""Phase 12 tests: Governance Policy Semantics.

Tests validate that governance policies can be represented declaratively
without collapsing the separation between policy, epistemic state,
governance decision, and authority.
"""

import pytest
from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.self_audit.continuous_reconciliation import WorldState
from research.examples.sovereign_agent.authorization_dependencies import (
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    create_completeness_scope,
)
from research.examples.sovereign_agent.governance_policy import (
    GovernanceDisposition,
    GovernancePolicyEngine,
    Policy,
    PolicyCompositionType,
    PolicyPredicate,
    PolicyPredicateType,
    create_combined_policy,
    create_provenance_policy,
    create_scope_policy,
    run_all_phase12_experiments,
    run_policy_composition,
    run_policy_non_amplification,
    run_policy_provenance_deficiency,
    run_policy_scope_mismatch,
)
from research.examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)


class TestPolicyScopeMismatch:
    """Test: Policy detects scope mismatch."""

    def test_scope_mismatch_changes_disposition(self):
        """Test that scope mismatch changes governance disposition."""
        result = run_policy_scope_mismatch()
        
        assert result["dispositions_differ"] is True
        assert result["disposition_prod"] == "review_required"
        assert result["disposition_staging"] == "hold"
        assert result["authority_created"] is False

    def test_scope_widening_does_not_authorize(self):
        """Test that wider scope does not create authority."""
        result = run_policy_scope_mismatch()
        
        assert result["authority_created"] is False


class TestPolicyProvenanceDeficiency:
    """Test: Policy detects provenance deficiency."""

    def test_provenance_deficiency_changes_disposition(self):
        """Test that provenance deficiency changes governance disposition."""
        result = run_policy_provenance_deficiency()
        
        assert result["dispositions_differ"] is True
        assert result["disposition_complete"] == "review_required"
        assert result["disposition_incomplete"] == "hold"
        assert result["authority_created"] is False


class TestPolicyComposition:
    """Test: Policy composition (AND)."""

    def test_combined_policy_satisfies_all(self):
        """Test that combined policy requires all predicates."""
        result = run_policy_composition()
        
        assert result["dispositions_differ"] is True
        assert result["disposition_satisfies"] == "review_required"
        assert result["disposition_fails"] == "hold"
        assert result["authority_created"] is False


class TestPolicyNonAmplification:
    """Test: Policy composition does not amplify authority."""

    def test_multiple_policies_no_authority(self):
        """Test that multiple policies do not create authority."""
        result = run_policy_non_amplification()
        
        assert result["policy_count"] == 3
        assert result["authority_created_any"] is False
        assert result["authority_revoked_any"] is False

    def test_all_policies_produce_dispositions(self):
        """Test that all policies produce valid dispositions."""
        result = run_policy_non_amplification()
        
        for d in result["dispositions"]:
            assert d in ["review_required", "hold", "escalate", "cannot_determine", "deny"]


class TestPolicyPredicateEvaluation:
    """Test individual policy predicate evaluation."""

    def test_scope_match_predicate(self):
        """Test scope match predicate."""
        engine = GovernancePolicyEngine()
        scope = create_completeness_scope("prop_001", "payment", environment="production")
        
        dep_graph = build_authorization_dependency_graph(
            authorization_id="auth_001", evidence_ids=["E1"], proposition_id="P1",
            epistemic_state_id="S1", experiment_id="exp_001", recommendation_id="rec_001",
            governance_policy_id="gov_001", resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01", provenance=["src_001"],
        )
        
        frontier = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
            agent_id="agent_test", timestamp="2026-01-01T00:00:00Z",
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
        
        predicate = PolicyPredicate(
            predicate_type=PolicyPredicateType.SCOPE_MATCH,
            required=True,
        )
        
        # Should match production scope
        result = engine.evaluate_predicate(
            predicate, frontier, "auth_001", {"scope": "production"}
        )
        assert result is True
        
        # Should not match staging scope
        result = engine.evaluate_predicate(
            predicate, frontier, "auth_001", {"scope": "staging"}
        )
        assert result is False

    def test_provenance_sufficient_predicate(self):
        """Test provenance sufficiency predicate."""
        engine = GovernancePolicyEngine()
        scope = create_completeness_scope("p1", "payment", environment="production")
        
        dep_graph = build_authorization_dependency_graph(
            authorization_id="auth_001", evidence_ids=["E1"], proposition_id="P1",
            epistemic_state_id="S1", experiment_id="exp_001", recommendation_id="rec_001",
            governance_policy_id="gov_001", resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01", provenance=["src_001"],
        )
        
        frontier = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
            agent_id="agent_test", timestamp="2026-01-01T00:00:00Z",
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
            provenance_quality="complete",
        )
        
        predicate = PolicyPredicate(
            predicate_type=PolicyPredicateType.PROVENANCE_SUFFICIENT,
            required=True,
            parameters={"required_quality": "complete"},
        )
        
        # Should pass with complete provenance
        result = engine.evaluate_predicate(
            predicate, frontier, "auth_001", {"scope": "production"}
        )
        assert result is True


class TestPolicyDoesNotCreateAuthority:
    """Test the invariant: POLICY ≠ AUTHORITY."""

    def test_policy_evaluation_never_creates_authority(self):
        """Test that policy evaluation never creates authority."""
        results = run_all_phase12_experiments()
        
        for name, result in results.items():
            assert result.get("authority_created", result.get("authority_created_any", False)) is False, \
                f"Policy created authority in {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
