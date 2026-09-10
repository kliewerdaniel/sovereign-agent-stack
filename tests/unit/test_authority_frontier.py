"""Phase 7 tests: Authority Frontier Integration.

Tests validate that frontier membership correctly triggers governance
review without becoming authorization itself.
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
from examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from examples.sovereign_agent.authority_frontier_integration import (
    AuthorityFrontierIntegrator,
    AuthorityFrontierResult,
    GovernanceAction,
    run_authority_frontier_experiments,
)
from examples.sovereign_agent.temporal_frontier_experiment import (
    TemporalFrontierEngine,
)


class TestFrontierDoesNotCreateAuthority:
    """Tests that frontier integration does not create authority."""

    def test_frontier_triggers_review_not_authorization(self):
        """Test that frontier triggers review, not authorization."""
        integrator = AuthorityFrontierIntegrator()
        scope = create_completeness_scope("p1", "payment")
        
        dep_graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["E1"],
            proposition_id="P1",
            epistemic_state_id="S1",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["src_001"],
        )
        
        frontier = integrator.temporal_engine.compute_historical_frontier(
            timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="t0_change",
                timestamp="2026-01-01T00:00:00Z",
                event_type="dependency_mutated",
                description="E1 mutated",
                affected_actor="A1",
                affected_component="A1",
                previous_state={"E1": "old"},
                new_state={"E1": "new"},
            ),
            authorization_id="auth_001",
            dependency_graph=dep_graph,
            proposition_graph=create_scoped_proposition_graph({"P1": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P1"]}),
            scope=scope,
            known_dependencies=["E1"],
            known_propositions=["P1"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = integrator.integrate_frontier_with_authority(
            frontier=frontier,
            authorization_id="auth_001",
            current_authority={"auth_001": "authorized"},
            governance_policy={"policy_001": "active"},
        )
        
        # Frontier triggers review
        assert result.frontier_triggered_review is True
        assert result.governance_action == GovernanceAction.REVIEW_REQUIRED
        
        # But does NOT create or revoke authority
        assert result.frontier_created_authorization is False
        assert result.frontier_revoked_authorization is False
        
        # Verify invariants
        assert integrator.verify_frontier_does_not_create_authority(result)
        assert integrator.verify_review_not_authorization(result)

    def test_empty_frontier_does_not_trigger_review(self):
        """Test that empty frontier does not trigger governance review."""
        integrator = AuthorityFrontierIntegrator()
        scope = create_completeness_scope("p1", "payment")
        
        empty_frontier = integrator.temporal_engine.compute_historical_frontier(
            timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="no_change",
                timestamp="2026-01-01T00:00:00Z",
                event_type="no_change",
                description="No change",
                affected_actor="none",
                affected_component="none",
                previous_state={},
                new_state={},
            ),
            authorization_id="auth_002",
            dependency_graph=build_authorization_dependency_graph(
                authorization_id="auth_002",
                evidence_ids=[],
                proposition_id="P2",
                epistemic_state_id="S2",
                experiment_id="exp_002",
                recommendation_id="rec_002",
                governance_policy_id="gov_002",
                resource_id="res_002",
                temporal_interval="2026-01-01/2027-01-01",
                provenance=["src_002"],
            ),
            proposition_graph={},
            authorization_graph={},
            scope=scope,
            known_dependencies=[],
            known_propositions=[],
            known_authorizations=[],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = integrator.integrate_frontier_with_authority(
            frontier=empty_frontier,
            authorization_id="auth_002",
            current_authority={"auth_002": "authorized"},
            governance_policy={"policy_002": "active"},
        )
        
        # Empty frontier does NOT trigger review
        assert result.frontier_triggered_review is False
        assert result.governance_action == GovernanceAction.NO_ACTION
        assert result.frontier_created_authorization is False
        assert result.frontier_revoked_authorization is False


class TestFrontierReviewNotRevocation:
    """Tests that frontier review is not the same as revocation."""

    def test_review_d_not_revoke(self):
        """Test that governance review D does not revoke authorization."""
        integrator = AuthorityFrontierIntegrator()
        scope = create_completeness_scope("p1", "payment")
        
        dep_graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["E1"],
            proposition_id="P1",
            epistemic_state_id="S1",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["src_001"],
        )
        
        frontier = integrator.temporal_engine.compute_historical_frontier(
            timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="t0_change",
                timestamp="2026-01-01T00:00:00Z",
                event_type="dependency_mutated",
                description="E1 mutated",
                affected_actor="A1",
                affected_component="A1",
                previous_state={"E1": "old"},
                new_state={"E1": "new"},
            ),
            authorization_id="auth_001",
            dependency_graph=dep_graph,
            proposition_graph=create_scoped_proposition_graph({"P1": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P1"]}),
            scope=scope,
            known_dependencies=["E1"],
            known_propositions=["P1"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = integrator.integrate_frontier_with_authority(
            frontier=frontier,
            authorization_id="auth_001",
            current_authority={"auth_001": "authorized"},
            governance_policy={"policy_001": "active"},
        )
        
        # Review is triggered
        assert result.governance_action == GovernanceAction.REVIEW_REQUIRED
        
        # But authorization is NOT revoked
        assert result.frontier_revoked_authorization is False


class TestAuthorityFrontierExperiments:
    """Tests for the full authority frontier experiment suite."""

    def test_all_experiments_produce_results(self):
        """Test that all experiments produce results."""
        results = run_authority_frontier_experiments()
        assert len(results) >= 3

    def test_all_frontiers_do_not_create_authority(self):
        """Test that no frontier creates authority."""
        results = run_authority_frontier_experiments()
        for r in results:
            assert r.frontier_created_authorization is False, \
                f"Frontier created authorization in {r.test_name}"

    def test_all_frontiers_do_not_revoke_authority(self):
        """Test that no frontier revokes authority."""
        results = run_authority_frontier_experiments()
        for r in results:
            assert r.frontier_revoked_authorization is False, \
                f"Frontier revoked authorization in {r.test_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
