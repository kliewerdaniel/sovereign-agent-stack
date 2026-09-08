"""Tests for Evidence Structure module."""

from __future__ import annotations

import pytest

from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceDimension,
    EvidenceIndependence,
    EvidenceProfile,
    EvidenceSufficiency,
    ReplicationRecord,
    StructuredEvidenceBundle,
    evaluate_structured_proposition,
    flat_to_structured,
)
from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
)


# ---------------------------------------------------------------------------
# Test: Evidence Dimension
# ---------------------------------------------------------------------------


class TestEvidenceDimension:
    def test_all_dimensions_present(self):
        dims = list(EvidenceDimension)
        assert len(dims) == 8
        assert EvidenceDimension.MAGNITUDE in dims
        assert EvidenceDimension.CONSISTENCY in dims
        assert EvidenceDimension.REPLICATION in dims
        assert EvidenceDimension.INDEPENDENCE in dims
        assert EvidenceDimension.INTERVENTION_DIVERSITY in dims
        assert EvidenceDimension.TEMPORAL_ROBUSTNESS in dims
        assert EvidenceDimension.GENERALIZATION in dims
        assert EvidenceDimension.ALTERNATIVE_EXCLUSION in dims


# ---------------------------------------------------------------------------
# Test: Evidence Independence
# ---------------------------------------------------------------------------


class TestEvidenceIndependence:
    def test_independent(self):
        ind = EvidenceIndependence(
            evidence_id_a="e1",
            evidence_id_b="e2",
            correlation=0.1,
            shared_seed=False,
            shared_intervention=False,
        )
        assert ind.is_independent
        assert not ind.is_dependent

    def test_dependent(self):
        ind = EvidenceIndependence(
            evidence_id_a="e1",
            evidence_id_b="e2",
            correlation=0.9,
            shared_seed=True,
            shared_intervention=True,
        )
        assert not ind.is_independent
        assert ind.is_dependent

    def test_shared_seed_dependent(self):
        ind = EvidenceIndependence(
            evidence_id_a="e1",
            evidence_id_b="e2",
            correlation=0.1,
            shared_seed=True,
        )
        assert not ind.is_independent


# ---------------------------------------------------------------------------
# Test: Replication Record
# ---------------------------------------------------------------------------


class TestReplicationRecord:
    def test_effective_evidence(self):
        record = ReplicationRecord(
            n_replications=10,
            n_seeds=5,
            n_independent=5,
            consistency_score=0.9,
            independence_score=0.8,
        )
        # effective = 5 * 0.9 * 0.8 = 3.6
        assert record.effective_evidence == pytest.approx(3.6)

    def test_perfect_replication(self):
        record = ReplicationRecord(
            n_replications=10,
            n_seeds=10,
            n_independent=10,
            consistency_score=1.0,
            independence_score=1.0,
        )
        assert record.effective_evidence == 10.0

    def test_zero_replication(self):
        record = ReplicationRecord(
            n_replications=0,
            n_seeds=0,
            n_independent=0,
            consistency_score=0.0,
            independence_score=0.0,
        )
        assert record.effective_evidence == 0.0


# ---------------------------------------------------------------------------
# Test: Structured Evidence Bundle
# ---------------------------------------------------------------------------


class TestStructuredEvidenceBundle:
    def test_correlation_same_seed(self):
        e1 = StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=42,
        )
        e2 = StructuredEvidenceBundle(
            evidence_id="e2",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=42,
        )
        assert e1.correlation_with(e2) == 1.0

    def test_correlation_different_seed(self):
        e1 = StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=1,
        )
        e2 = StructuredEvidenceBundle(
            evidence_id="e2",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=2,
        )
        assert e1.correlation_with(e2) == 0.3  # Same intervention type

    def test_correlation_different_intervention(self):
        e1 = StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=1,
        )
        e2 = StructuredEvidenceBundle(
            evidence_id="e2",
            intervention_type=InterventionType.HOLDOUT,
            target="returns",
            effect_size=0.5,
            description="Test",
            seed=2,
        )
        assert e1.correlation_with(e2) == 0.0  # Independent

    def test_can_inform(self):
        bundle = StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
        )
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        assert bundle.can_inform(proposition)

    def test_cannot_inform(self):
        bundle = StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target="signal",
            effect_size=0.8,
            description="Test",
        )
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        assert not bundle.can_inform(proposition)


# ---------------------------------------------------------------------------
# Test: Evidence Profile
# ---------------------------------------------------------------------------


class TestEvidenceProfile:
    def test_is_sufficient(self):
        profile = EvidenceProfile(
            magnitude=0.8,
            consistency=0.9,
            replication=5,
            independence=0.8,
            intervention_diversity=3,
            temporal_robustness=True,
            generalization=True,
            alternative_exclusion=0.8,
        )
        assert profile.is_sufficient

    def test_not_sufficient_low_magnitude(self):
        profile = EvidenceProfile(
            magnitude=0.3,
            replication=5,
            independence=0.8,
            intervention_diversity=3,
        )
        assert not profile.is_sufficient

    def test_not_sufficient_low_replication(self):
        profile = EvidenceProfile(
            magnitude=0.8,
            replication=1,
            independence=0.8,
            intervention_diversity=3,
        )
        assert not profile.is_sufficient

    def test_not_sufficient_low_independence(self):
        profile = EvidenceProfile(
            magnitude=0.8,
            replication=5,
            independence=0.2,
            intervention_diversity=3,
        )
        assert not profile.is_sufficient

    def test_not_sufficient_low_diversity(self):
        profile = EvidenceProfile(
            magnitude=0.8,
            replication=5,
            independence=0.8,
            intervention_diversity=1,
        )
        assert not profile.is_sufficient

    def test_is_strong(self):
        profile = EvidenceProfile(
            magnitude=0.8,
            consistency=0.9,
            replication=10,
            independence=0.9,
            intervention_diversity=5,
            temporal_robustness=True,
            generalization=True,
            alternative_exclusion=0.9,
        )
        assert profile.is_strong

    def test_effective_evidence_count(self):
        profile = EvidenceProfile(
            replication=10,
            independence=0.8,
            consistency=0.9,
        )
        assert profile.effective_evidence_count == pytest.approx(7.2)


# ---------------------------------------------------------------------------
# Test: Evidence Accumulator
# ---------------------------------------------------------------------------


class TestEvidenceAccumulator:
    def test_add_single(self):
        acc = EvidenceAccumulator()
        bundle = StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=42,
        )
        acc.add(bundle)
        assert len(acc.bundles) == 1
        assert len(acc.independence_records) == 0

    def test_add_multiple(self):
        acc = EvidenceAccumulator()
        for i in range(3):
            bundle = StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=i + 1,
            )
            acc.add(bundle)
        assert len(acc.bundles) == 3
        # 3 bundles → 3 independence records (0 + 1 + 2)
        assert len(acc.independence_records) == 3

    def test_compute_profile(self):
        acc = EvidenceAccumulator()
        for i in range(5):
            bundle = StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=i + 1,
            )
            acc.add(bundle)
        profile = acc.compute_profile()
        assert profile.magnitude == pytest.approx(0.8)
        assert profile.replication == 5
        assert profile.consistency == pytest.approx(1.0)

    def test_compute_replication_record(self):
        acc = EvidenceAccumulator()
        for i in range(5):
            bundle = StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=i + 1,
            )
            acc.add(bundle)
        record = acc.compute_replication_record()
        assert record.n_replications == 5
        assert record.n_seeds == 5
        assert record.n_independent == 5


# ---------------------------------------------------------------------------
# Test: Structured Proposition Evaluator
# ---------------------------------------------------------------------------


class TestStructuredPropositionEvaluator:
    def test_supported_with_strong_evidence(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        # Use multiple intervention types for diversity
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=1,
        ))
        acc.add(StructuredEvidenceBundle(
            evidence_id="e2",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target="signal_component",
            effect_size=0.7,
            description="Test",
            seed=2,
        ))
        acc.add(StructuredEvidenceBundle(
            evidence_id="e3",
            intervention_type=InterventionType.MECHANISM_DECORRELATION,
            target="signal_component",
            effect_size=0.6,
            description="Test",
            seed=3,
        ))
        result = evaluate_structured_proposition(proposition, acc)
        assert result.status == "SUPPORTED"
        assert len(result.established) > 0

    def test_inconclusive_with_weak_evidence(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.3,
            description="Test",
            seed=42,
        ))
        result = evaluate_structured_proposition(proposition, acc)
        assert result.status == "INCONCLUSIVE"

    def test_inconclusive_with_single_evidence(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=42,
        ))
        result = evaluate_structured_proposition(proposition, acc)
        # Single evidence should be INCONCLUSIVE (needs replication >= 3)
        assert result.status == "INCONCLUSIVE"

    def test_refuted_with_negative_effect(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=-0.8,
                description="Test",
                seed=i + 1,
            ))
        result = evaluate_structured_proposition(proposition, acc)
        assert result.status == "REFUTED"


# ---------------------------------------------------------------------------
# Test: Flat to Structured Conversion
# ---------------------------------------------------------------------------


class TestFlatToStructured:
    def test_conversion(self):
        flat = EvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
        )
        structured = flat_to_structured(flat, seed=42, time_period="2020")
        assert structured.evidence_id == "e1"
        assert structured.seed == 42
        assert structured.time_period == "2020"
        assert structured.effect_size == 0.8


# ---------------------------------------------------------------------------
# Test: Evidence Sufficiency
# ---------------------------------------------------------------------------


class TestEvidenceSufficiency:
    def test_explain(self):
        sufficiency = EvidenceSufficiency(
            proposition_id="p1",
            status="SUPPORTED",
            profile=EvidenceProfile(),
            established=["effect magnitude", "replication"],
            not_established=["temporal robustness"],
            limitations=["single intervention type"],
        )
        explanation = sufficiency.explain()
        assert "Proposition: p1" in explanation
        assert "Status: SUPPORTED" in explanation
        assert "effect magnitude" in explanation
        assert "temporal robustness" in explanation
