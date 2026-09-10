"""Phase 6 tests: Temporal Frontier Validation.

Tests validate that historical frontiers remain immutable while their
epistemic adequacy may be challenged by new knowledge.
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
from examples.sovereign_agent.temporal_frontier_experiment import (
    KnowledgeBoundary,
    TemporalFrontierEngine,
    TemporalFrontierResult,
    TemporalFrontierStatus,
    run_temporal_frontier_experiments,
)


class TestHistoricalFrontierImmutability:
    """Tests for historical frontier immutability."""

    def test_historical_frontier_remains_unchanged_after_new_knowledge(self):
        """Test that historical frontier is not modified when new knowledge is discovered."""
        engine = TemporalFrontierEngine()
        scope = create_completeness_scope("p1", "payment", environment="production")
        
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
        
        # T0: Compute frontier with E1
        historical = engine.compute_historical_frontier(
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
        
        original_members = historical.frontier.get_member_ids()
        
        # T1: Discover E2
        result = engine.discover_new_knowledge(
            historical_frontier=historical,
            new_dependencies=["E2"],
            new_propositions=["P2"],
            discovery_timestamp="2026-02-01T00:00:00Z",
            world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
        )
        
        # Historical frontier unchanged
        assert result.frontier_unchanged is True
        assert historical.frontier.get_member_ids() == original_members
        assert engine.verify_immutability(historical)

    def test_historical_frontier_status_is_immutable(self):
        """Test that historical frontier status is IMMUTABLE."""
        engine = TemporalFrontierEngine()
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
        
        historical = engine.compute_historical_frontier(
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
        
        assert historical.status == TemporalFrontierStatus.IMMUTABLE


class TestTemporalKnowledgeMonotonicity:
    """Tests for temporal knowledge monotonicity."""

    def test_knowledge_monotonicity_preserves_historical(self):
        """Test that K0 ⊂ K1 ⊂ K2 preserves historical frontier."""
        engine = TemporalFrontierEngine()
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
        
        # T0: K0 = {E1}
        historical_k0 = engine.compute_historical_frontier(
            timestamp="2026-01-01T00:00:00Z",
            world_change=AuthorityDriftEvent(
                event_id="k0_change",
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
        
        k0_members = historical_k0.frontier.get_member_ids()
        
        # T1: K1 = {E1, E2}
        result_t1 = engine.discover_new_knowledge(
            historical_frontier=historical_k0,
            new_dependencies=["E2"],
            new_propositions=["P2"],
            discovery_timestamp="2026-02-01T00:00:00Z",
            world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
        )
        
        # T2: K2 = {E1, E2, E3}
        result_t2 = engine.discover_new_knowledge(
            historical_frontier=historical_k0,
            new_dependencies=["E2", "E3"],
            new_propositions=["P2", "P3"],
            discovery_timestamp="2026-03-01T00:00:00Z",
            world_state=WorldState(timestamp="2026-03-01T00:00:00Z"),
        )
        
        # Historical frontier K0 remains unchanged
        assert engine.verify_immutability(historical_k0)
        assert historical_k0.frontier.get_member_ids() == k0_members
        assert result_t1.frontier_unchanged is True
        assert result_t2.frontier_unchanged is True


class TestHistoricalInadequacy:
    """Tests for historical inadequacy detection."""

    def test_historical_frontier_can_be_inadequate(self):
        """Test that a historical frontier can be inadequate but still immutable."""
        engine = TemporalFrontierEngine()
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
        
        # T0: Frontier computed with only E1 (graph appears complete)
        historical = engine.compute_historical_frontier(
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
        
        # T2: Discover E2 (latent dependency that existed but was unknown)
        result = engine.discover_new_knowledge(
            historical_frontier=historical,
            new_dependencies=["E2"],
            new_propositions=["P2"],
            discovery_timestamp="2026-02-01T00:00:00Z",
            world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
        )
        
        # Historical frontier is unchanged (immutable)
        assert result.frontier_unchanged is True
        assert "E2" not in historical.frontier.get_member_ids()
        
        # But new knowledge would produce a different frontier
        assert result.later_members is not None
        assert "E2" in result.later_members


class TestKnowledgeBoundary:
    """Tests for knowledge boundary."""

    def test_knowledge_boundary_records_available_knowledge(self):
        """Test that knowledge boundary records what was known at computation time."""
        engine = TemporalFrontierEngine()
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
        
        historical = engine.compute_historical_frontier(
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
        
        kb = historical.knowledge_boundary
        assert kb.timestamp == "2026-01-01T00:00:00Z"
        assert "E1" in kb.known_dependencies
        assert "P1" in kb.known_propositions
        assert "A1" in kb.known_authorizations


class TestTemporalFrontierExperiments:
    """Tests for the full temporal frontier experiment suite."""

    def test_all_experiments_produce_results(self):
        """Test that all experiments produce results."""
        results = run_temporal_frontier_experiments()
        assert len(results) >= 3

    def test_all_frontiers_remain_unchanged(self):
        """Test that all frontiers remain unchanged after new knowledge."""
        results = run_temporal_frontier_experiments()
        for r in results:
            assert r.frontier_unchanged is True, f"Frontier changed in {r.test_name}"

    def test_all_statuses_are_immutable(self):
        """Test that all frontier statuses are immutable."""
        results = run_temporal_frontier_experiments()
        for r in results:
            assert r.status == TemporalFrontierStatus.IMMUTABLE, f"Status not immutable in {r.test_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
