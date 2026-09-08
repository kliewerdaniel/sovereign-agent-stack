"""Adversarial suite for Epistemic Gaps.

Tests whether the gap analysis system correctly identifies and classifies
epistemic gaps, and whether it can be fooled by various attack vectors.

The 12 attacks target:
1. Huge effect, zero replication
2. Huge sample, zero intervention diversity
3. 100 dependent replications
4. 100 observations from one realization
5. 100 experiments using the same invalid intervention
6. Contradictory independent evidence
7. Strong evidence against alternative but no evidence for proposition
8. Evidence sufficient for prediction but insufficient for mechanism
9. Evidence sufficient for mechanism but insufficient for causal claims
10. Evidence sufficient for hypothesis but insufficient for generalization
11. Gap for which no available intervention has authority
12. Gap that can be closed with an available intervention
"""

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
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    StructuredEvidenceBundle,
)
from sas.quant.experiment.typed_propositions import (
    InterventionType,
    PropositionType,
    TypedProposition,
)


# ---------------------------------------------------------------------------
# Test: Attack 1 - Huge effect, zero replication
# ---------------------------------------------------------------------------


class TestAttack1_HugeEffectZeroReplication:
    def test_identified_as_insufficient(self):
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
            effect_size=10.0,  # Huge effect
            description="Single huge effect",
            seed=42,
        ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.INSUFFICIENT_REPLICATION in gap_types

    def test_gap_closing_experiments_available(self):
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
            effect_size=10.0,
            description="Single huge effect",
            seed=42,
        ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert len(assessment.available_gap_closing_experiments) > 0


# ---------------------------------------------------------------------------
# Test: Attack 2 - Huge sample, zero intervention diversity
# ---------------------------------------------------------------------------


class TestAttack2_HugeSampleZeroDiversity:
    def test_identified_as_insufficient(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Same intervention",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.INSUFFICIENT_INTERVENTION_DIVERSITY in gap_types


# ---------------------------------------------------------------------------
# Test: Attack 3 - 100 dependent replications
# ---------------------------------------------------------------------------


class TestAttack3_HundredDependentReplications:
    def test_identified_as_insufficient(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Dependent replications",
                seed=42,  # Same seed = dependent
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.DEPENDENT_EVIDENCE in gap_types


# ---------------------------------------------------------------------------
# Test: Attack 4 - 100 observations from one realization
# ---------------------------------------------------------------------------


class TestAttack4_HundredObservationsOneRealization:
    def test_identified_as_insufficient(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Same realization",
                seed=42,
                realization_id="r1",  # Same realization
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.DEPENDENT_EVIDENCE in gap_types


# ---------------------------------------------------------------------------
# Test: Attack 5 - 100 experiments using same invalid intervention
# ---------------------------------------------------------------------------


class TestAttack5_HundredInvalidInterventions:
    def test_identified_as_insufficient(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.FEATURE_ABLATION,  # Wrong type
                target="signal",
                effect_size=0.8,
                description="Invalid intervention",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.WRONG_INTERVENTION_TYPE in gap_types


# ---------------------------------------------------------------------------
# Test: Attack 6 - Contradictory independent evidence
# ---------------------------------------------------------------------------


class TestAttack6_ContradictoryIndependentEvidence:
    def test_identified_as_inconclusive(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(10):
            effect = 0.8 if i % 2 == 0 else -0.8
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=effect,
                description="Contradictory",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        # Contradictory evidence should not produce SUPPORTED
        assert assessment.status != "SUPPORTED"


# ---------------------------------------------------------------------------
# Test: Attack 7 - Strong evidence against alternative but no evidence for
# ---------------------------------------------------------------------------


class TestAttack7_EvidenceAgainstAlternativeOnly:
    def test_identified_as_inconclusive(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        # Evidence that autocorrelation is NOT the mechanism
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="autocorrelation",  # Different target
                effect_size=-0.8,
                description="Against autocorrelation",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        # No evidence FOR signal_component - system correctly identifies
        # that evidence against alternative is not evidence for proposition
        assert assessment.status in {"INCONCLUSIVE", "REFUTED"}


# ---------------------------------------------------------------------------
# Test: Attack 8 - Evidence sufficient for prediction but not mechanism
# ---------------------------------------------------------------------------


class TestAttack8_PredictionNotMechanism:
    def test_mechanism_requires_mechanism_evidence(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        # Only holdout evidence (prediction, not mechanism)
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.HOLDOUT,
                target="returns",
                effect_size=0.8,
                description="Holdout only",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        assert assessment.status == "INCONCLUSIVE"


# ---------------------------------------------------------------------------
# Test: Attack 9 - Evidence sufficient for mechanism but not causal
# ---------------------------------------------------------------------------


class TestAttack9_MechanismNotCausal:
    def test_causal_requires_mechanism_authority(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.CAUSAL_CLAIM,
            target="signal_component",
            description="Signal causes returns",
        )
        acc = EvidenceAccumulator()
        # Only feature-level evidence (not mechanism-level)
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Feature evidence only",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        # Causal claim requires mechanism authority - should have gap
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.CAUSAL_AUTHORITY_UNAVAILABLE in gap_types


# ---------------------------------------------------------------------------
# Test: Attack 10 - Evidence sufficient for hypothesis but not generalization
# ---------------------------------------------------------------------------


class TestAttack10_HypothesisNotGeneralization:
    def test_generalization_requires_holdout(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        # Strong mechanism evidence but no holdout
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            ))
        assessment = analyze_evidence_gaps(prop, acc)
        # Should be SUPPORTED for mechanism but have generalization gap
        gap_types = [g.gap_type for g in assessment.epistemic_gaps]
        assert GapType.GENERALIZATION_UNESTABLISHED in gap_types


# ---------------------------------------------------------------------------
# Test: Attack 11 - Gap for which no available intervention has authority
# ---------------------------------------------------------------------------


class TestAttack11_UnavailableAuthority:
    def test_unavailable_authority_identified(self):
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.CAUSAL_CLAIM,
            target="signal_component",
            description="Signal causes returns",
        )
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target="signal",
            effect_size=0.8,
            description="Wrong type",
            seed=42,
        ))
        # Only feature ablation available - no mechanism interventions
        available = [InterventionType.FEATURE_ABLATION]
        assessment = analyze_evidence_gaps(prop, acc, available_interventions=available)
        assert assessment.has_unavailable_authority


# ---------------------------------------------------------------------------
# Test: Attack 12 - Gap that can be closed with available intervention
# ---------------------------------------------------------------------------


class TestAttack12_ClosableGap:
    def test_gap_closing_potential_identified(self):
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
            description="Single evidence",
            seed=42,
        ))
        assessment = analyze_evidence_gaps(prop, acc)
        # Should have closable gaps
        assert len(assessment.resolvable_gaps) > 0
        # Should have available experiments
        assert len(assessment.available_gap_closing_experiments) > 0


# ---------------------------------------------------------------------------
# Test: Full Adversarial Suite
# ---------------------------------------------------------------------------


class TestAdversarialSuite:
    def test_all_attacks_blocked(self):
        """All 12 attacks should result in INCONCLUSIVE status."""
        attacks = [
            self._attack1(),
            self._attack2(),
            self._attack3(),
            self._attack4(),
            self._attack5(),
            self._attack6(),
            self._attack7(),
            self._attack8(),
            self._attack9(),
            self._attack10(),
            self._attack11(),
            self._attack12(),
        ]
        for assessment in attacks:
            assert assessment.status != "SUPPORTED", \
                f"Attack produced SUPPORTED status"

    def _attack1(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1", intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component", effect_size=10.0, description="Huge effect", seed=42,
        ))
        return analyze_evidence_gaps(prop, acc)

    def _attack2(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component", effect_size=0.8, description="Same", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack3(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component", effect_size=0.8, description="Dependent", seed=42,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack4(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component", effect_size=0.8, description="Same realization",
                seed=42, realization_id="r1",
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack5(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(100):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal", effect_size=0.8, description="Invalid", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack6(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(10):
            effect = 0.8 if i % 2 == 0 else -0.8
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component", effect_size=effect, description="Contradictory", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack7(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="autocorrelation", effect_size=-0.8, description="Against alternative", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack8(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.HOLDOUT,
                target="returns", effect_size=0.8, description="Holdout only", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack9(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.CAUSAL_CLAIM,
            target="signal_component", description="Signal causes returns",
        )
        acc = EvidenceAccumulator()
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component", effect_size=0.8, description="Mechanism", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack10(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}", intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component", effect_size=0.8, description="Mechanism", seed=i + 1,
            ))
        return analyze_evidence_gaps(prop, acc)

    def _attack11(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.CAUSAL_CLAIM,
            target="signal_component", description="Signal causes returns",
        )
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1", intervention_type=InterventionType.FEATURE_ABLATION,
            target="signal", effect_size=0.8, description="Wrong type", seed=42,
        ))
        return analyze_evidence_gaps(
            prop, acc,
            available_interventions=[InterventionType.FEATURE_ABLATION],
        )

    def _attack12(self):
        prop = TypedProposition(
            proposition_id="p1", proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component", description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        acc.add(StructuredEvidenceBundle(
            evidence_id="e1", intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component", effect_size=0.8, description="Single", seed=42,
        ))
        return analyze_evidence_gaps(prop, acc)
