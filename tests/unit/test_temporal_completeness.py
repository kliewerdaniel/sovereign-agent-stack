"""Tests for Temporal Completeness Drift and Revalidation."""

import pytest
from research.examples.self_audit.authority_drift import (
    AuthorityDriftEvent,
    DriftClassification,
    DriftType,
)
from research.examples.self_audit.continuous_reconciliation import WorldState
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessMethod,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from research.examples.sovereign_agent.temporal_completeness import (
    CompletenessDriftFinding,
    CompletenessDriftType,
    CompletenessValidityInterval,
    RevalidationFrontier,
    RevalidationRequirement,
    TemporalCompletenessEngine,
)


class TestTemporalCompletenessEngine:
    """Tests for temporal completeness drift detection."""

    def test_baseline_completeness(self):
        """Test T0 baseline completeness assessment."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        world = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            static_topology={
                "nodes": [{"id": "checkout", "type": "service"}, {"id": "provider_a", "type": "external"}],
                "edges": [{"source": "checkout", "target": "provider_a", "type": "dependency"}],
            },
        )

        assessment, interval = engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a"],
            scope=scope,
            timestamp="2026-01-01T00:00:00Z",
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        assert assessment.overall_status == CompletenessStatus.KNOWN_COMPLETE
        assert interval.is_valid_at("2026-01-01T00:00:00Z")

    def test_historical_assessments_stored(self):
        """Test that historical assessments are stored and not overwritten."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        # T0
        engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a"],
            scope=scope,
            timestamp="2026-01-01T00:00:00Z",
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        # T1
        engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a", "e2_new"],
            scope=scope,
            timestamp="2026-02-01T00:00:00Z",
            method=CompletenessMethod.STATIC_ANALYSIS_DERIVED,
        )

        # Both assessments should be stored
        historical = engine.get_historical_assessments()
        assert len(historical) == 2

        # T0 assessment should still be KNOWN_COMPLETE
        assert historical[0][1].overall_status == CompletenessStatus.KNOWN_COMPLETE
        # T1 assessment should be KNOWN_INCOMPLETE
        assert historical[1][1].overall_status == CompletenessStatus.KNOWN_INCOMPLETE

    def test_irrelevant_world_change(self):
        """Test that an irrelevant world change does not affect completeness."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        world_t0 = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            static_topology={
                "nodes": [{"id": "checkout", "type": "service"}, {"id": "provider_a", "type": "external"}],
                "edges": [{"source": "checkout", "target": "provider_a", "type": "dependency"}],
            },
        )

        world_t1 = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                    {"id": "e99", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "provider_a", "type": "dependency"},
                    {"source": "some_service", "target": "e99", "type": "call"},
                ],
            },
        )

        assessment_t0, _ = engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a"],
            scope=scope,
            timestamp="2026-01-01T00:00:00Z",
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        assessment_t1, _ = engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a"],
            scope=scope,
            timestamp="2026-02-01T00:00:00Z",
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        findings = engine.detect_completeness_drift(
            world_t0, world_t1, assessment_t0, assessment_t1,
            "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", scope,
        )

        # Should detect world change but no dependency change
        assert len(findings) > 0
        assert findings[0].drift_type in (
            CompletenessDriftType.WORLD_CHANGE_NO_DEPENDENCY_CHANGE,
            CompletenessDriftType.NO_DRIFT,
        )

    def test_revalidation_frontier_empty_for_irrelevant_change(self):
        """Test that an unrelated world change produces an empty revalidation frontier."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        drift_event = AuthorityDriftEvent(
            event_id="event_001",
            timestamp="2026-02-01T00:00:00Z",
            event_type="irrelevant_change",
            description="Unrelated component added",
            affected_actor="some_service",
            affected_component="some_service",
            previous_state={"status": "old"},
            new_state={"status": "new"},
        )

        frontier = engine.compute_revalidation_frontier(
            drift_event,
            "auth_001",
            ["provider_a"],
            "prop_001",
            "payment",
            scope,
        )

        # Frontier should be empty since the change doesn't affect provider_a
        assert frontier.is_empty()
        assert not frontier.requires_governance()

    def test_revalidation_frontier_nonempty_for_relevant_change(self):
        """Test that a relevant world change produces a non-empty revalidation frontier."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        drift_event = AuthorityDriftEvent(
            event_id="event_002",
            timestamp="2026-02-01T00:00:00Z",
            event_type="provider_replacement",
            description="Provider replaced",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            previous_state={"provider": "provider_a"},
            new_state={"provider": "provider_b"},
        )

        frontier = engine.compute_revalidation_frontier(
            drift_event,
            "auth_001",
            ["provider_a"],
            "prop_001",
            "payment",
            scope,
        )

        # Frontier should NOT be empty since provider_a is affected
        assert not frontier.is_empty()
        assert "provider_a" in frontier.affected_dependencies

    def test_validity_interval_temporal_bounds(self):
        """Test that validity intervals respect temporal bounds."""
        interval = CompletenessValidityInterval(
            interval_id="interval_001",
            claim_id="claim_001",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-06-01T00:00:00Z",
            scope=create_completeness_scope("prop_001", "payment"),
        )

        assert interval.is_valid_at("2026-03-01T00:00:00Z")
        assert not interval.is_valid_at("2026-07-01T00:00:00Z")
        assert not interval.is_valid_at("2025-12-01T00:00:00Z")

    def test_validity_interval_scope_matching(self):
        """Test that validity intervals respect scope bounds."""
        interval = CompletenessValidityInterval(
            interval_id="interval_001",
            claim_id="claim_001",
            valid_from="2026-01-01T00:00:00Z",
            scope=create_completeness_scope("prop_001", "payment", environment="production"),
        )

        assert interval.is_valid_in_scope(create_completeness_scope("prop_001", "payment", environment="production"))
        assert not interval.is_valid_in_scope(create_completeness_scope("prop_002", "payment"))
        assert not interval.is_valid_in_scope(create_completeness_scope("prop_001", "read_only"))

    def test_drift_finding_not_authoritative(self):
        """Test that drift findings are never authoritative."""
        finding = CompletenessDriftFinding(
            finding_id="finding_001",
            drift_type=CompletenessDriftType.COMPLETENESS_STALE,
            drift_classification=DriftClassification.SIGNIFICANT,
            description="Completeness became stale",
        )

        assert not finding.is_authoritative()

    def test_revalidation_frontier_not_authoritative(self):
        """Test that revalidation frontiers are never authoritative."""
        frontier = RevalidationFrontier(
            frontier_id="frontier_001",
            world_change_id="event_001",
            authorization_id="auth_001",
            timestamp="2026-01-01T00:00:00Z",
        )

        assert not frontier.is_authoritative()

    def test_conditional_completeness(self):
        """Test that conditional completeness is properly scoped."""
        interval = CompletenessValidityInterval(
            interval_id="interval_001",
            claim_id="claim_001",
            valid_from="2026-01-01T00:00:00Z",
            scope=create_completeness_scope("prop_001", "payment"),
            conditions=["feature_flag_enabled"],
        )

        assert interval.is_conditional()
        assert interval.conditions_met(["feature_flag_enabled"])
        assert not interval.conditions_met(["feature_flag_disabled"])

    def test_distinction_world_vs_dependency_vs_completeness(self):
        """Test that world change, dependency change, and completeness change are distinct."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        world_t0 = WorldState(
            timestamp="2026-01-01T00:00:00Z",
            static_topology={
                "nodes": [{"id": "checkout", "type": "service"}, {"id": "provider_a", "type": "external"}],
                "edges": [{"source": "checkout", "target": "provider_a", "type": "dependency"}],
            },
        )

        # World change: add a node with no dependency relationship
        world_t1 = WorldState(
            timestamp="2026-02-01T00:00:00Z",
            static_topology={
                "nodes": [
                    {"id": "checkout", "type": "service"},
                    {"id": "provider_a", "type": "external"},
                    {"id": "unrelated", "type": "external"},
                ],
                "edges": [
                    {"source": "checkout", "target": "provider_a", "type": "dependency"},
                    {"source": "other", "target": "unrelated", "type": "call"},
                ],
            },
        )

        assessment_t0, _ = engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a"],
            scope=scope,
            timestamp="2026-01-01T00:00:00Z",
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        assessment_t1, _ = engine.assess_temporal_completeness(
            authorization_id="auth_001",
            graph_id="graph_001",
            declared_dependencies=["provider_a"],
            actual_dependencies=["provider_a"],
            scope=scope,
            timestamp="2026-02-01T00:00:00Z",
            method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        )

        # Both assessments should show completeness
        assert assessment_t0.overall_status == CompletenessStatus.KNOWN_COMPLETE
        assert assessment_t1.overall_status == CompletenessStatus.KNOWN_COMPLETE

        findings = engine.detect_completeness_drift(
            world_t0, world_t1, assessment_t0, assessment_t1,
            "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", scope,
        )

        # Should detect that completeness is preserved
        assert len(findings) > 0


class TestRevalidationFrontier:
    """Tests for the revalidation frontier computation."""

    def test_empty_frontier_for_no_change(self):
        """Test that no change produces an empty frontier."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        frontier = engine.compute_revalidation_frontier(
            None, "auth_001", ["provider_a"], "prop_001", "payment", scope,
        )

        assert frontier.is_empty()
        assert frontier.revalidation_requirement == RevalidationRequirement.NOTHING

    def test_frontier_is_recommendation_not_authority(self):
        """Test that the frontier is a recommendation, not authority."""
        engine = TemporalCompletenessEngine()
        scope = create_completeness_scope("prop_001", "payment")

        drift_event = AuthorityDriftEvent(
            event_id="event_001",
            timestamp="2026-02-01T00:00:00Z",
            event_type="provider_change",
            description="Provider changed",
            affected_actor="payment_gateway",
            affected_component="payment_gateway",
            previous_state={"provider_a": "active"},
            new_state={"provider_a": "inactive"},
        )

        frontier = engine.compute_revalidation_frontier(
            drift_event, "auth_001", ["provider_a"], "prop_001", "payment", scope,
        )

        assert not frontier.is_authoritative()
        assert frontier.requires_revalidation() or frontier.is_empty()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
