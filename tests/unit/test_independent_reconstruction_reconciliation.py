"""Tests for Phase 35: Independent Authority Reconstruction Reconciliation."""

import pytest
from research.examples.sovereign_agent.independent_reconstruction_reconciliation import (
    AdversarialWorldGenerator,
    ConflictType,
    EvidenceReconciliationEngine,
    Phase35Experiment,
    ReconciliationDisposition,
    ReconciliationStatus,
    ReconciliationWorld,
    ReconstructionIndependence,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> EvidenceReconciliationEngine:
    return EvidenceReconciliationEngine("test-engine")


@pytest.fixture
def worlds() -> list[ReconciliationWorld]:
    return AdversarialWorldGenerator().generate_all_worlds()


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------


class TestWorldGeneration:
    def test_generates_45_worlds(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        assert len(worlds) == 45

    def test_worlds_have_unique_ids(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_world_01_independent_agreement(self, worlds):
        world = worlds[0]
        assert world.world_id == "world_01_independent_agreement"
        assert world.expected_status == ReconciliationStatus.CONSISTENT

    def test_world_05_shared_source(self, worlds):
        world = worlds[4]
        assert world.world_id == "world_05_shared_source_correlated_failure"
        assert world.expected_status == ReconciliationStatus.CORRELATED_AGREEMENT

    def test_world_11_future_authority(self, worlds):
        world = worlds[10]
        assert world.world_id == "world_11_future_authority_laundering"
        assert world.expected_status == ReconciliationStatus.FUTURE_AUTHORITY_LAUNDERING

    def test_world_16_empty(self, worlds):
        world = worlds[15]
        assert world.world_id == "world_16_empty_reconstructions"
        assert len(world.reconstructions) == 0
        assert world.expected_status == ReconciliationStatus.EVIDENCE_INSUFFICIENT


# ---------------------------------------------------------------------------
# Reconciliation engine tests
# ---------------------------------------------------------------------------


class TestReconciliationEngine:
    def test_empty_reconstructions(self, engine):
        world = ReconciliationWorld(
            world_id="test-empty",
            description="Empty",
            effect_id="eff-test",
            observation_id="obs-test",
            reconstructions=(),
            expected_status=ReconciliationStatus.EVIDENCE_INSUFFICIENT,
            expected_disposition=ReconciliationDisposition.INSUFFICIENT_EVIDENCE,
            expected_conflict_type=ConflictType.NONE,
            expected_minority_correct=False,
            expected_majority_hallucination=False,
            expected_correlated_agreement=False,
            expected_future_authority_detected=False,
            expected_temporal_mismatch_detected=False,
            expected_identifier_collision_detected=False,
            expected_prefix_agreement=False,
            expected_suffix_conflict=False,
            expected_cryptographic_conflict=False,
            expected_authority_created=False,
        )
        result = engine.reconcile(world)
        assert result.reconciliation_status == ReconciliationStatus.EVIDENCE_INSUFFICIENT

    def test_single_reconstruction(self, engine):
        gen = AdversarialWorldGenerator()
        world = ReconciliationWorld(
            world_id="test-single",
            description="Single",
            effect_id="eff-test",
            observation_id="obs-test",
            reconstructions=(
                gen._make_reconstruction("r1", "eff-test", "obs-test", ("A", "B", "C")),
            ),
            expected_status=ReconciliationStatus.UNRESOLVED,
            expected_disposition=ReconciliationDisposition.DEFERRED,
            expected_conflict_type=ConflictType.NONE,
            expected_minority_correct=False,
            expected_majority_hallucination=False,
            expected_correlated_agreement=False,
            expected_future_authority_detected=False,
            expected_temporal_mismatch_detected=False,
            expected_identifier_collision_detected=False,
            expected_prefix_agreement=False,
            expected_suffix_conflict=False,
            expected_cryptographic_conflict=False,
            expected_authority_created=False,
        )
        result = engine.reconcile(world)
        assert result.reconciliation_status == ReconciliationStatus.UNRESOLVED

    def test_independent_agreement(self, engine):
        world = AdversarialWorldGenerator()._world_01_independent_agreement()
        result = engine.reconcile(world)
        assert result.reconciliation_status == ReconciliationStatus.CONSISTENT
        assert result.disposition.value == "corroborated"

    def test_future_authority_rejected(self, engine):
        world = AdversarialWorldGenerator()._world_11_future_authority_laundering()
        result = engine.reconcile(world)
        assert result.reconciliation_status == ReconciliationStatus.FUTURE_AUTHORITY_LAUNDERING
        assert result.disposition.value == "rejected"

    def test_correlated_agreement_rejected(self, engine):
        world = AdversarialWorldGenerator()._world_05_shared_source_correlated_failure()
        result = engine.reconcile(world)
        assert result.reconciliation_status == ReconciliationStatus.CORRELATED_AGREEMENT
        assert result.disposition.value == "consensus_rejected"

    def test_no_authority_created(self, engine):
        """The reconciliator must never create authority."""
        for world in AdversarialWorldGenerator().generate_all_worlds():
            result = engine.reconcile(world)
            assert result.authority_created is False, f"Authority created in {world.world_id}"


# ---------------------------------------------------------------------------
# Phase 35 experiment tests
# ---------------------------------------------------------------------------


class TestPhase35Experiment:
    def test_runs_all_worlds(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert summary["total_worlds"] == 45
        assert summary["total_reconciliations"] == 45

    def test_false_authority_from_consensus_rate_is_0_percent(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert summary["false_authority_from_consensus_rate"] == 0.0

    def test_false_authority_from_confidence_rate_is_0_percent(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert summary["false_authority_from_confidence_rate"] == 0.0

    def test_false_authority_from_majority_rate_is_0_percent(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert summary["false_authority_from_majority_rate"] == 0.0

    def test_correlated_evidence_misclassification_rate_is_0_percent(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert summary["correlated_evidence_misclassification_rate"] == 0.0

    def test_reconciliation_soundness_is_100_percent(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert summary["reconciliation_soundness"] == 1.0

    def test_summary_generated(self):
        exp = Phase35Experiment()
        summary = exp.run_all()
        assert "status_accuracy" in summary
        assert "disposition_accuracy" in summary
        assert "conflict_accuracy" in summary
        assert "reconciliation_soundness" in summary
