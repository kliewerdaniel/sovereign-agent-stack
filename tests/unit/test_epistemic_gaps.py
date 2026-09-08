"""Tests for Epistemic Gaps module."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_gaps import (
    GapType,
    GapResolvability,
    GapClosingPotential,
    EpistemicGap,
    CandidateExperiment,
    EvidenceSufficiencyAssessment,
    analyze_evidence_gaps,
    classify_gap_closing_potential,
    design_gap_closing_experiments,
    analyze_minimal_evidence_set,
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceDimension,
    StructuredEvidenceBundle,
)
from sas.quant.experiment.typed_propositions import (
    InterventionType,
    PropositionType,
    TypedProposition,
)


# ---------------------------------------------------------------------------
# Test: Gap Types
# ---------------------------------------------------------------------------


class TestGapTypes:
    def test_all_gap_types_present(self):
        gaps = list(GapType)
        assert len(gaps) == 12
        assert GapType.INSUFFICIENT_REPLICATION in gaps
        assert GapType.DEPENDENT_EVIDENCE in gaps
        assert GapType.WRONG_INTERVENTION_TYPE in gaps

    def test_all_resolvability_present(self):
        res = list(GapResolvability)
        assert len(res) == 4
        assert GapResolvability.RESOLVABLE in res
        assert GapResolvability.UNRESOLVABLE_WITH_AVAILABLE_AUTHORITY in res

    def test_all_closing_potential_present(self):
        potentials = list(GapClosingPotential)
        assert len(potentials) == 4
        assert GapClosingPotential.GAP_CLOSING in potentials
        assert GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY in potentials


# ---------------------------------------------------------------------------
# Test: Epistemic Gap
# ---------------------------------------------------------------------------


class TestEpistemicGap:
    def test_explain(self):
        gap = EpistemicGap(
            gap_id="gap_1",
            proposition_id="p1",
            gap_type=GapType.INSUFFICIENT_REPLICATION,
            dimension=EvidenceDimension.REPLICATION,
            current_state="replication = 1",
            required_evidence_type="at least 3 independent replications",
            missing_information="Too few replications",
        )
        explanation = gap.explain()
        assert "insufficient_replication" in explanation
        assert "replication = 1" in explanation
        assert "at least 3 independent replications" in explanation


# ---------------------------------------------------------------------------
# Test: Candidate Experiment
# ---------------------------------------------------------------------------


class TestCandidateExperiment:
    def test_explain(self):
        exp = CandidateExperiment(
            experiment_id="exp_1",
            target_gap="gap_1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="New replication",
            gap_closing_potential=GapClosingPotential.GAP_CLOSING,
        )
        explanation = exp.explain()
        assert "exp_1" in explanation
        assert "gap_closing" in explanation


# ---------------------------------------------------------------------------
# Test: Evidence Sufficiency Assessment
# ---------------------------------------------------------------------------


class TestEvidenceSufficiencyAssessment:
    def test_properties(self):
        assessment = EvidenceSufficiencyAssessment(
            proposition_id="p1",
            status="INCONCLUSIVE",
            established=["magnitude"],
            unresolved=["replication"],
            epistemic_gaps=[
                EpistemicGap(
                    gap_id="gap_1",
                    proposition_id="p1",
                    gap_type=GapType.INSUFFICIENT_REPLICATION,
                    dimension=EvidenceDimension.REPLICATION,
                    current_state="replication = 1",
                    required_evidence_type="3 replications",
                    missing_information="too few",
                )
            ],
        )
        assert not assessment.is_supported
        assert assessment.has_gaps
        assert not assessment.has_unavailable_authority

    def test_explain(self):
        assessment = EvidenceSufficiencyAssessment(
            proposition_id="p1",
            status="INCONCLUSIVE",
            established=["magnitude"],
            unresolved=["replication"],
        )
        explanation = assessment.explain()
        assert "p1" in explanation
        assert "INCONCLUSIVE" in explanation
        assert "magnitude" in explanation
        assert "replication" in explanation


# ---------------------------------------------------------------------------
# Test: Gap Analysis
# ---------------------------------------------------------------------------


class TestAnalyzeEvidenceGaps:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_single_strong_evidence_has_gaps(self):
        prop = self._create_proposition()
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=42,
        ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        assert len(assessment.epistemic_gaps) > 0
        # Should have replication gap
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.INSUFFICIENT_REPLICATION in gap_types

    def test_many_independent_evidence_supported(self):
        prop = self._create_proposition()
        acc = EvidenceAccumulator()
        # Use multiple intervention types for diversity
        intervention_types = [
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        ]
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=intervention_types[i % len(intervention_types)],
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        # Core claim is SUPPORTED (magnitude, replication, independence, diversity)
        assert assessment.status == "SUPPORTED"
        # But system still reports gaps for stronger claims (temporal, generalization)
        # This is correct behavior - SUPPORTED doesn't mean "knows everything"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.TEMPORAL_ROBUSTNESS_UNESTABLISHED in gap_types
        assert GapType.GENERALIZATION_UNESTABLISHED in gap_types

    def test_many_dependent_evidence_has_gaps(self):
        prop = self._create_proposition()
        acc = EvidenceAccumulator()
        for i in range(10):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=42,  # Same seed
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.DEPENDENT_EVIDENCE in gap_types

    def test_wrong_intervention_type_gap(self):
        prop = self._create_proposition()
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target="signal",
            effect_size=0.8,
            description="Test",
            seed=42,
        ))
        assessment = analyze_evidence_gaps(prop, acc)
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.WRONG_INTERVENTION_TYPE in gap_types

    def test_identifies_gap_closing_experiments(self):
        prop = self._create_proposition()
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Test",
            seed=42,
        ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert len(assessment.available_gap_closing_experiments) > 0


# ---------------------------------------------------------------------------
# Test: Gap Closing Classification
# ---------------------------------------------------------------------------


class TestClassifyGapClosingPotential:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_mechanism_removal_closes_replication_gap(self):
        prop = self._create_proposition()
        gap = EpistemicGap(
            gap_id="gap_1",
            proposition_id="p1",
            gap_type=GapType.INSUFFICIENT_REPLICATION,
            dimension=EvidenceDimension.REPLICATION,
            current_state="replication = 1",
            required_evidence_type="3 replications",
            missing_information="too few",
        )
        result = classify_gap_closing_potential(
            gap, InterventionType.MECHANISM_REMOVAL, prop
        )
        assert result == GapClosingPotential.GAP_CLOSING

    def test_feature_ablation_cannot_close_mechanism_gap(self):
        prop = self._create_proposition()
        gap = EpistemicGap(
            gap_id="gap_1",
            proposition_id="p1",
            gap_type=GapType.INSUFFICIENT_REPLICATION,
            dimension=EvidenceDimension.REPLICATION,
            current_state="replication = 1",
            required_evidence_type="3 replications",
            missing_information="too few",
        )
        result = classify_gap_closing_potential(
            gap, InterventionType.FEATURE_ABLATION, prop
        )
        assert result == GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY

    def test_holdout_closes_generalization_gap(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.GENERALIZATION,
            target="signal_component",
            description="Signal drives returns",
        )
        gap = EpistemicGap(
            gap_id="gap_1",
            proposition_id="p1",
            gap_type=GapType.GENERALIZATION_UNESTABLISHED,
            dimension=EvidenceDimension.GENERALIZATION,
            current_state="no holdout",
            required_evidence_type="holdout evidence",
            missing_information="no generalization",
        )
        result = classify_gap_closing_potential(
            gap, InterventionType.HOLDOUT, prop
        )
        assert result == GapClosingPotential.GAP_CLOSING


# ---------------------------------------------------------------------------
# Test: Gap Closing Experiment Design
# ---------------------------------------------------------------------------


class TestDesignGapClosingExperiments:
    def test_designs_experiments_for_gaps(self):
        prop = TypedProposition(
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
        assessment = analyze_evidence_gaps(prop, acc)
        candidates = design_gap_closing_experiments(
            assessment,
            list(InterventionType),
            prop,
        )
        assert len(candidates) > 0
        # All candidates should be for actual gaps
        for c in candidates:
            assert c.gap_closing_potential in {
                GapClosingPotential.GAP_CLOSING,
                GapClosingPotential.PARTIALLY_GAP_CLOSING,
            }


# ---------------------------------------------------------------------------
# Test: Minimal Evidence Set
# ---------------------------------------------------------------------------


class TestAnalyzeMinimalEvidenceSet:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_no_evidence(self):
        prop = self._create_proposition()
        result = analyze_minimal_evidence_set(prop, [])
        assert result["minimal_subset"] == []
        assert result["is_structural"]

    def test_single_evidence_not_sufficient(self):
        prop = self._create_proposition()
        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=42,
            )
        ]
        result = analyze_minimal_evidence_set(prop, evidence)
        # Single evidence should not be sufficient (needs replication >= 3, diversity >= 2)
        assert len(result["minimal_subset"]) == 0 or result["minimal_subset"] == []

    def test_structural_dependencies(self):
        prop = self._create_proposition()
        intervention_types = [
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        ]
        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=intervention_types[i % len(intervention_types)],
                target="signal_component",
                effect_size=0.8,
                description="Test",
                seed=i + 1,
            )
            for i in range(5)
        ]
        result = analyze_minimal_evidence_set(prop, evidence)
        assert "replication" in result["structural_dependencies"]
        assert "independence" in result["structural_dependencies"]
