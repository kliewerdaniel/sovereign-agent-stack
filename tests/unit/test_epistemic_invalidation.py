"""Tests for Authorization Dependencies, Epistemic Invalidation, and Epistemic Cycles."""

import pytest
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    AuthorizationStatus,
    DependencyStrength,
    DependencyType,
    IntersectionResult,
    StalenessType,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_intersection import (
    DependencyIntersectionEvaluator,
    Evidence,
    EvidenceRelation,
    EvidenceType,
    evaluate_evidence_against_authorization,
)
from examples.sovereign_agent.epistemic_invalidation import (
    EpistemicInvalidationEngine,
    InvalidationDecision,
    InvalidationReason,
    run_invalidations,
)
from examples.sovereign_agent.epistemic_cycles import (
    CycleType,
    EpistemicCycleDetector,
    detect_epistemic_cycles,
)
from examples.sovereign_agent.partial_invalidation import (
    ComponentStatus,
    PartialInvalidationEngine,
    run_partial_invalidation,
)


class TestAuthorizationDependencyGraph:
    """Tests for authorization dependency graphs."""

    def test_graph_builds_with_id(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001", "ev_002"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )
        assert graph.authorization_id == "auth_001"

    def test_graph_has_multiple_dependencies(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        # Should have evidence, proposition, epistemic, experiment, governance, resource, temporal, recommendation
        assert len(graph.dependencies) >= 7

    def test_graph_has_direct_dependencies(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        direct = graph.get_direct_dependencies()
        assert len(direct) > 0

    def test_graph_has_transitive_dependencies(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        transitive = graph.get_transitive_dependencies()
        assert len(transitive) > 0

    def test_graph_detects_dependency_on_target(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        assert graph.has_dependency_on("ev_001") is True
        assert graph.has_dependency_on("nonexistent") is False

    def test_graph_marks_stale(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        graph.mark_stale(StalenessType.EPISTEMICALLY_STALE)
        assert graph.is_stale() is True
        assert graph.is_epistemically_stale() is True

    def test_graph_to_dict(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        d = graph.to_dict()
        assert d["authorization_id"] == "auth_001"
        assert d["dependency_count"] > 0


class TestDependencyIntersection:
    """Tests for dependency intersection evaluation."""

    def test_unrelated_evidence(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        unrelated_evidence = Evidence(
            evidence_id="ev_unrelated",
            evidence_type=EvidenceType.OBSERVATION,
            content="Something completely different happened",
            timestamp="2026-01-01T00:00:00Z",
            source="external",
        )
        evaluator = DependencyIntersectionEvaluator()
        result = evaluator.evaluate(unrelated_evidence, graph)
        assert result.result == IntersectionResult.UNRELATED

    def test_relevant_evidence(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        relevant_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 has new supporting data",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        evaluator = DependencyIntersectionEvaluator()
        result = evaluator.evaluate(relevant_evidence, graph)
        assert result.requires_reevaluation is True

    def test_contradictory_evidence(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        contradictory_evidence = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        evaluator = DependencyIntersectionEvaluator()
        result = evaluator.evaluate(contradictory_evidence, graph)
        assert result.requires_suspension is True


class TestEpistemicInvalidation:
    """Tests for epistemic invalidation engine."""

    def test_unrelated_evidence_preserves(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        unrelated_evidence = Evidence(
            evidence_id="ev_unrelated",
            evidence_type=EvidenceType.OBSERVATION,
            content="Something completely different",
            timestamp="2026-01-01T00:00:00Z",
            source="external",
        )
        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(graph, [unrelated_evidence])
        assert result.decision == InvalidationDecision.PRESERVE

    def test_contradictory_evidence_suspends(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        contradictory_evidence = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(graph, [contradictory_evidence])
        assert result.decision == InvalidationDecision.SUSPEND

    def test_evidence_does_not_create_revocation_authority(self):
        """EVIDENCE DOES NOT CREATE REVOCATION AUTHORITY."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        contradictory_evidence = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(graph, [contradictory_evidence])
        # Evidence triggers suspension, not automatic revocation
        assert result.requires_governance_review is True

    def test_staleness_tracks_type(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        graph.mark_stale(StalenessType.EPISTEMICALLY_STALE)
        assert graph.is_epistemically_stale() is True
        assert graph.is_temporally_stale() is False


class TestEpistemicCycles:
    """Tests for epistemic dependency cycle detection."""

    def test_no_cycle_detected(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        detector = EpistemicCycleDetector()
        result = detector.detect_cycles(graph)
        assert result.cycle_type == CycleType.NONE
        assert result.is_valid is True

    def test_cycle_classification(self):
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        # Create a cycle: experiment was permitted by the same authorization
        experiment_to_auth = {"exp_001": "auth_001"}
        detector = EpistemicCycleDetector()
        result = detector.detect_cycles(graph, experiment_to_auth)
        # Should detect some kind of cycle
        assert result.cycle_type != CycleType.NONE


class TestPartialInvalidation:
    """Tests for partial invalidation."""

    def test_partial_invalidation_preserves_independent(self):
        from examples.sovereign_agent.intent_graph import ActionProposal, build_intent_graph
        proposals = [
            ActionProposal(
                proposal_id="p1",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="backup",
                resource="database",
                arguments={},
                proposition="Backup database",
                postconditions=["database_backed_up"],
            ),
            ActionProposal(
                proposal_id="p2",
                agent_id="agent_001",
                timestamp="2026-01-01T00:00:00Z",
                action="replace",
                resource="provider",
                arguments={},
                proposition="Replace provider",
                prerequisite_actions=["database_backed_up"],
            ),
            ActionProposal(
                proposal_id="p3",
                agent_id="agent_002",
                timestamp="2026-01-01T00:00:00Z",
                action="remove",
                resource="legacy_processor",
                arguments={},
                proposition="Remove legacy processor",
            ),
        ]
        intent_graph = build_intent_graph(proposals)
        auth_graphs = {
            "p1": build_authorization_dependency_graph(
                authorization_id="auth_p1",
                evidence_ids=["ev_001"],
                proposition_id="prop_001",
                epistemic_state_id="es_001",
                experiment_id="exp_001",
                recommendation_id="rec_001",
                governance_policy_id="gov_001",
                resource_id="database",
                temporal_interval="2026-01-01/2027-01-01",
                provenance=[],
            ),
            "p2": build_authorization_dependency_graph(
                authorization_id="auth_p2",
                evidence_ids=["ev_001"],
                proposition_id="prop_001",
                epistemic_state_id="es_001",
                experiment_id="exp_001",
                recommendation_id="rec_001",
                governance_policy_id="gov_001",
                resource_id="provider",
                temporal_interval="2026-01-01/2027-01-01",
                provenance=[],
            ),
            "p3": build_authorization_dependency_graph(
                authorization_id="auth_p3",
                evidence_ids=["ev_002"],
                proposition_id="prop_002",
                epistemic_state_id="es_002",
                experiment_id="exp_002",
                recommendation_id="rec_002",
                governance_policy_id="gov_002",
                resource_id="legacy_processor",
                temporal_interval="2026-01-01/2027-01-01",
                provenance=[],
            ),
        }
        # Invalidate p1 - p2 depends on p1, p3 is independent
        new_evidence = [
            Evidence(
                evidence_id="ev_invalid",
                evidence_type=EvidenceType.OBSERVATION,
                content="prop_001 is not valid",
                timestamp="2026-01-01T00:00:00Z",
                source="experiment",
            )
        ]
        engine = PartialInvalidationEngine()
        result = engine.evaluate_partial_invalidation(
            intent_graph, auth_graphs, "p1", new_evidence
        )
        # p3 should be preserved (independent)
        p3_result = next((c for c in result.components if c.proposal_id == "p3"), None)
        assert p3_result is not None
        assert p3_result.status == ComponentStatus.VALID


class TestEpistemicInvariants:
    """Tests for epistemic invalidation invariants."""

    def test_new_evidence_does_not_auto_invalidate(self):
        """NEW EVIDENCE DOES NOT AUTOMATICALLY INVALIDATE AUTHORIZATION."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        # Unrelated evidence should not invalidate
        unrelated = Evidence(
            evidence_id="ev_other",
            evidence_type=EvidenceType.OBSERVATION,
            content="Something unrelated",
            timestamp="2026-01-01T00:00:00Z",
            source="external",
        )
        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(graph, [unrelated])
        assert result.decision == InvalidationDecision.PRESERVE

    def test_unrelated_evidence_does_not_invalidate(self):
        """UNRELATED EVIDENCE DOES NOT INVALIDATE AUTHORIZATION."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        unrelated = Evidence(
            evidence_id="ev_other",
            evidence_type=EvidenceType.OBSERVATION,
            content="Completely unrelated observation",
            timestamp="2026-01-01T00:00:00Z",
            source="external",
        )
        evaluator = DependencyIntersectionEvaluator()
        result = evaluator.evaluate(unrelated, graph)
        assert result.result == IntersectionResult.UNRELATED

    def test_relevant_evidence_evaluated_against_dependencies(self):
        """RELEVANT EVIDENCE MUST BE EVALUATED AGAINST AUTHORIZATION DEPENDENCIES."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        # Relevant evidence that weakens
        weakening = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is uncertain",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        evaluator = DependencyIntersectionEvaluator()
        result = evaluator.evaluate(weakening, graph)
        assert result.requires_reevaluation is True

    def test_evidence_does_not_create_revocation_authority(self):
        """EVIDENCE DOES NOT CREATE REVOCATION AUTHORITY."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        # Even contradictory evidence only suspends, doesn't revoke
        contradictory = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(graph, [contradictory])
        assert result.decision == InvalidationDecision.SUSPEND
        assert result.requires_governance_review is True

    def test_suspension_not_revocation(self):
        """SUSPENSION ≠ REVOCATION."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        contradictory = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )
        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(graph, [contradictory])
        assert result.decision == InvalidationDecision.SUSPEND
        # Status should be SUSPENDED, not INVALIDATED
        assert graph.status == AuthorizationStatus.SUSPENDED

    def test_epistemic_staleness_not_auto_revocation(self):
        """EPISTEMIC STALENESS ≠ AUTOMATIC REVOCATION."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        graph.mark_stale(StalenessType.EPISTEMICALLY_STALE)
        # Staleness is tracked but doesn't automatically revoke
        assert graph.is_epistemically_stale() is True
        # Status should still be valid (staleness is a flag, not a revocation)
        assert graph.status == AuthorizationStatus.VALID

    def test_historical_authority_immutable(self):
        """HISTORICAL AUTHORITY REMAINS IMMUTABLE."""
        graph = build_authorization_dependency_graph(
            authorization_id="auth_001",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="res_001",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=[],
        )
        # Historical evidence should not affect current authorization
        historical = Evidence(
            evidence_id="ev_historical",
            evidence_type=EvidenceType.OBSERVATION,
            content="historical state was different",
            timestamp="2026-01-01T00:00:00Z",
            source="historical_record",
        )
        evaluator = DependencyIntersectionEvaluator()
        result = evaluator.evaluate(historical, graph)
        assert result.result == IntersectionResult.UNRELATED
