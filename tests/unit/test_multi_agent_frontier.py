"""Phase 8 tests: Multi-Agent Frontier Composition.

Tests validate that independently produced frontier computations can be
reconciled without amplifying authority or discarding epistemically
relevant disagreement.
"""

import pytest
from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.self_audit.continuous_reconciliation import WorldState
from research.examples.sovereign_agent.agent_composition import CompositionType
from research.examples.sovereign_agent.authorization_dependencies import (
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    create_completeness_scope,
)
from research.examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from research.examples.sovereign_agent.multi_agent_frontier_composition import (
    AgentFrontier,
    CompositionOperation,
    FrontierAgreement,
    FrontierCompositionResult,
    MultiAgentFrontierComposer,
    run_multi_agent_frontier_experiments,
)


class TestFrontierAgreement:
    """Tests for frontier agreement classification."""

    def test_same_frontier_same_basis_is_agreement(self):
        """Test that same frontier with same basis is agreement."""
        composer = MultiAgentFrontierComposer()
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
        
        agent_a = composer.compute_agent_frontier(
            agent_id="agent_A",
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
        
        agent_b = composer.compute_agent_frontier(
            agent_id="agent_B",
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
        
        agreement = composer.classify_agreement(agent_a, agent_b)
        assert agreement == FrontierAgreement.AGREEMENT

    def test_different_frontier_is_disagreement(self):
        """Test that different frontiers are classified as disagreement."""
        composer = MultiAgentFrontierComposer()
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
        
        agent_a = composer.compute_agent_frontier(
            agent_id="agent_A",
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
        
        # Agent B has different proposition (P2 instead of P1)
        agent_b = composer.compute_agent_frontier(
            agent_id="agent_B",
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
            proposition_graph=create_scoped_proposition_graph({"P2": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P2"]}),
            scope=scope,
            known_dependencies=["E1"],
            known_propositions=["P2"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        agreement = composer.classify_agreement(agent_a, agent_b)
        assert agreement in (FrontierAgreement.DISAGREEMENT, FrontierAgreement.PARTIAL)


class TestCompositionNonAmplification:
    """Tests that composition does not amplify authority."""

    def test_union_does_not_create_authority(self):
        """Test that union operation does not create authority."""
        composer = MultiAgentFrontierComposer()
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
        
        agent_a = composer.compute_agent_frontier(
            agent_id="agent_A",
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
        
        agent_b = composer.compute_agent_frontier(
            agent_id="agent_B",
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
            proposition_graph=create_scoped_proposition_graph({"P2": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P2"]}),
            scope=scope,
            known_dependencies=["E1"],
            known_propositions=["P2"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = composer.compose_frontiers(agent_a, agent_b, CompositionOperation.UNION)
        
        # Critical: union does NOT create authority
        assert result.composed_authority is False
        assert composer.verify_non_amplification(result)

    def test_intersection_does_not_create_authority(self):
        """Test that intersection operation does not create authority."""
        composer = MultiAgentFrontierComposer()
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
        
        agent_a = composer.compute_agent_frontier(
            agent_id="agent_A",
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
        
        agent_b = composer.compute_agent_frontier(
            agent_id="agent_B",
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
            proposition_graph=create_scoped_proposition_graph({"P2": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P2"]}),
            scope=scope,
            known_dependencies=["E1"],
            known_propositions=["P2"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = composer.compose_frontiers(agent_a, agent_b, CompositionOperation.INTERSECTION)
        
        # Critical: intersection does NOT create authority
        assert result.composed_authority is False
        assert composer.verify_non_amplification(result)


class TestDisagreementPreservation:
    """Tests that disagreement is preserved in composition."""

    def test_union_preserves_disagreement(self):
        """Test that union preserves all members from both frontiers."""
        composer = MultiAgentFrontierComposer()
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
        
        agent_a = composer.compute_agent_frontier(
            agent_id="agent_A",
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
        
        agent_b = composer.compute_agent_frontier(
            agent_id="agent_B",
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
            proposition_graph=create_scoped_proposition_graph({"P2": ["E1"]}),
            authorization_graph=create_scoped_authorization_graph({"A1": ["P2"]}),
            scope=scope,
            known_dependencies=["E1"],
            known_propositions=["P2"],
            known_authorizations=["A1"],
            world_state=WorldState(timestamp="2026-01-01T00:00:00Z"),
        )
        
        result = composer.compose_frontiers(agent_a, agent_b, CompositionOperation.UNION)
        
        # Union should include all members
        assert result.composed_members is not None
        assert "P1" in result.composed_members
        assert "P2" in result.composed_members
        assert result.disagreement_preserved is True


class TestMultiAgentFrontierExperiments:
    """Tests for the full multi-agent frontier experiment suite."""

    def test_all_experiments_produce_results(self):
        """Test that all experiments produce results."""
        results = run_multi_agent_frontier_experiments()
        assert len(results) >= 6

    def test_all_compositions_do_not_create_authority(self):
        """Test that no composition creates authority."""
        results = run_multi_agent_frontier_experiments()
        for r in results:
            assert r.composed_authority is False, \
                f"Composition created authority in {r.test_name}"

    def test_all_results_have_valid_agreement(self):
        """Test that all results have valid agreement classification."""
        results = run_multi_agent_frontier_experiments()
        for r in results:
            assert isinstance(r.agreement, FrontierAgreement)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
