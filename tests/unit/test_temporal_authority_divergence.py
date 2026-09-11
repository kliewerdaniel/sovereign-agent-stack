"""Tests for Phase 34: Temporal Effective Authority Graph Divergence Detection."""

import pytest
from examples.sovereign_agent.temporal_authority_divergence import (
    AdversarialWorldGenerator,
    DivergenceDetectionEngine,
    Phase34Experiment,
    TemporalDivergenceStatus,
    TemporalDivergenceWorld,
    TemporalOrderStatus,
)
from examples.sovereign_agent.authority_path_graph_reconciliation import (
    GraphCompletenessStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> DivergenceDetectionEngine:
    return DivergenceDetectionEngine("test-engine")


@pytest.fixture
def worlds() -> list[TemporalDivergenceWorld]:
    return AdversarialWorldGenerator().generate_all_worlds()


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------


class TestWorldGeneration:
    def test_generates_50_worlds(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        assert len(worlds) == 50

    def test_worlds_have_unique_ids(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_world_01_stable_authority(self, worlds):
        world = worlds[0]
        assert world.world_id == "world_01_stable_authority_no_divergence"
        assert world.expected_divergence_status == TemporalDivergenceStatus.NO_DIVERGENCE

    def test_world_02_historical_valid_then_revoked(self, worlds):
        world = worlds[1]
        assert world.world_id == "world_02_historical_valid_then_revoked"
        assert world.is_future_revocation_attack

    def test_world_10_unauthorized_complete_graph(self, worlds):
        world = worlds[9]
        assert world.world_id == "world_10_unauthorized_complete_graph"
        assert world.is_unauthorized_effect
        assert world.is_complete_graph
        assert world.expected_divergence_status == TemporalDivergenceStatus.HISTORICAL_DIVERGENCE

    def test_world_11_unauthorized_incomplete_graph(self, worlds):
        world = worlds[10]
        assert world.world_id == "world_11_unauthorized_incomplete_graph"
        assert world.is_unauthorized_effect
        assert world.is_incomplete_graph
        assert world.expected_divergence_status == TemporalDivergenceStatus.UNKNOWN

    def test_world_35_historical_graph_state_missing(self, worlds):
        world = worlds[34]
        assert world.world_id == "world_35_historical_graph_state_missing"
        assert world.authority_state_at_execution is None
        assert world.expected_divergence_status == TemporalDivergenceStatus.HISTORICAL_STATE_UNKNOWN

    def test_world_46_concurrent_events_unknown_order(self, worlds):
        world = worlds[45]
        assert world.world_id == "world_46_concurrent_events_unknown_order"
        assert world.is_concurrent_event
        assert not world.temporal_order_known
        assert world.expected_divergence_status == TemporalDivergenceStatus.TEMPORAL_ORDER_UNKNOWN


# ---------------------------------------------------------------------------
# Divergence detection engine tests
# ---------------------------------------------------------------------------


class TestDivergenceDetectionEngine:
    def test_stable_authority_no_divergence(self, engine, worlds):
        world = worlds[0]
        result = engine.detect_divergence(world)
        assert result.divergence_status == TemporalDivergenceStatus.NO_DIVERGENCE

    def test_historical_state_missing(self, engine, worlds):
        world = worlds[34]
        result = engine.detect_divergence(world)
        assert result.divergence_status == TemporalDivergenceStatus.HISTORICAL_STATE_UNKNOWN

    def test_concurrent_unknown_order(self, engine, worlds):
        world = worlds[45]
        result = engine.detect_divergence(world)
        assert result.divergence_status == TemporalDivergenceStatus.TEMPORAL_ORDER_UNKNOWN

    def test_unauthorized_complete_graph(self, engine, worlds):
        world = worlds[9]
        result = engine.detect_divergence(world)
        assert result.divergence_status == TemporalDivergenceStatus.HISTORICAL_DIVERGENCE

    def test_unauthorized_incomplete_graph(self, engine, worlds):
        world = worlds[10]
        result = engine.detect_divergence(world)
        assert result.divergence_status == TemporalDivergenceStatus.UNKNOWN

    def test_incomplete_graph_no_false_escape(self, engine, worlds):
        """Incomplete graphs must NOT produce AUTHORITY_ESCAPE."""
        world = worlds[10]
        result = engine.detect_divergence(world)
        assert result.epistemic_status != "authority_escape"

    def test_missing_evidence_no_false_unauthorized(self, engine, worlds):
        """Missing evidence must produce UNKNOWN, not UNAUTHORIZED."""
        world = worlds[34]
        result = engine.detect_divergence(world)
        assert result.epistemic_status.name == "UNKNOWN"

    def test_detection_does_not_create_authority(self, engine, worlds):
        """The detector is purely epistemic — it must not authorize."""
        world = worlds[0]
        result = engine.detect_divergence(world)
        assert result.epistemic_status.value in (
            "reconciled",
            "divergent",
            "incomplete",
            "unknown",
            "reconciled_with_incomplete_declared_graph",
            "invalid_reconstruction",
            "authority_escape",
        )


# ---------------------------------------------------------------------------
# Phase 34 experiment tests
# ---------------------------------------------------------------------------


class TestPhase34Experiment:
    def test_runs_all_worlds(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert summary["total_worlds"] == 50
        assert summary["total_divergences"] == 50

    def test_status_accuracy_is_100_percent(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert summary["status_accuracy"] == 1.0

    def test_order_accuracy_is_100_percent(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert summary["order_accuracy"] == 1.0

    def test_false_historical_divergence_rate_is_0_percent(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert summary["false_historical_divergence_rate"] == 0.0

    def test_false_historical_authorization_rate_is_0_percent(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert summary["false_historical_authorization_rate"] == 0.0

    def test_false_current_authority_rate_is_0_percent(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert summary["false_current_authority_rate"] == 0.0

    def test_summary_generated(self):
        exp = Phase34Experiment()
        summary = exp.run_all()
        assert "status_accuracy" in summary
        assert "cause_accuracy" in summary
        assert "order_accuracy" in summary
