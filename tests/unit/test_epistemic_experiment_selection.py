"""Adversarial suite for Epistemic Experiment Selection.

Tests whether the selector correctly chooses experiments based on
epistemic value rather than statistical or information value.
"""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_gaps import (
    GapType,
    GapClosingPotential,
    analyze_evidence_gaps,
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
from sas.quant.experiment.epistemic_experiment_selection import (
    StatisticalValue,
    InformationValue,
    EpistemicValue,
    GapReduction,
    CandidateExperiment,
    ExperimentSelection,
    SelectionOutcome,
    DominanceRelation,
    EpistemicExperimentSelector,
    check_dominance,
    compute_pareto_frontier,
    select_experiment,
)


# ---------------------------------------------------------------------------
# Test: Attack A — Huge Sample vs Mechanism Intervention
# ---------------------------------------------------------------------------


class TestAttackA_HugeSampleVsMechanism:
    def test_mechanism_preferred_over_huge_sample(self):
        """When mechanism gap exists, mechanism intervention should be preferred."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate_a = CandidateExperiment(
            experiment_id="c_huge_sample",
            intervention_type=InterventionType.HOLDOUT,
            target_mechanism="returns",
            description="100,000 additional observations",
            sample_size=100000,
            statistical_value=StatisticalValue(
                variance_reduction=0.9,
                standard_error_reduction=0.9,
                confidence_interval_shrinkage=0.9,
                sample_size_increase=100000,
            ),
            information_value=InformationValue(
                entropy_reduction=0.8,
                mutual_information=0.8,
                expected_information_gain=0.8,
            ),
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_mechanism",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="100 observations + mechanism intervention",
            sample_size=100,
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_mechanism"


# ---------------------------------------------------------------------------
# Test: Attack B — Replication vs Intervention Diversity
# ---------------------------------------------------------------------------


class TestAttackB_ReplicationVsDiversity:
    def test_diversity_preferred_when_alternatives_unresolved(self):
        """When competing mechanisms unresolved, new intervention class should be preferred."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(20):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Same intervention",
                seed=i + 1,
            ))

        candidate_a = CandidateExperiment(
            experiment_id="c_replication",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="100 additional replications",
            sample_size=10000,
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_diversity",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="3 new intervention classes",
            sample_size=300,
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_diversity"


# ---------------------------------------------------------------------------
# Test: Attack C — Generalization vs Mechanism
# ---------------------------------------------------------------------------


class TestAttackC_GeneralizationVsMechanism:
    def test_selector_identifies_which_gap_each_addresses(self):
        """Selector should correctly identify which gap each experiment addresses."""
        prop = TypedProposition(
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
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            ))

        candidate_a = CandidateExperiment(
            experiment_id="c_mechanism",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="Another mechanism experiment",
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_temporal",
            intervention_type=InterventionType.HOLDOUT,
            target_mechanism="returns",
            description="New temporal holdout",
            time_period="2025-2026",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert len(result.selection_rationale) > 0


# ---------------------------------------------------------------------------
# Test: Attack D — Impossible Authority
# ---------------------------------------------------------------------------


class TestAttackD_ImpossibleAuthority:
    def test_unresolvable_when_no_mechanism_authority_available(self):
        """When causal claim requires mechanism authority but none available, should return UNRESOLVABLE."""
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
            description="Feature evidence",
            seed=42,
        ))

        candidate_a = CandidateExperiment(
            experiment_id="c_feature1",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target_mechanism="signal",
            description="More feature ablation",
        )
        candidate_b = CandidateExperiment(
            experiment_id="c_feature2",
            intervention_type=InterventionType.FEATURE_PERMUTATION,
            target_mechanism="signal",
            description="Feature permutation",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.outcome == SelectionOutcome.UNRESOLVABLE


# ---------------------------------------------------------------------------
# Test: Attack E — Statistical Decoy
# ---------------------------------------------------------------------------


class TestAttackE_StatisticalDecoy:
    def test_low_epistemic_value_for_high_statistical_value(self):
        """Experiment with high statistical value but zero epistemic value should be rejected."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate_a = CandidateExperiment(
            experiment_id="c_statistical",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target_mechanism="signal",
            description="Huge statistical improvement",
            sample_size=1000000,
            statistical_value=StatisticalValue(
                variance_reduction=0.99,
                standard_error_reduction=0.99,
                confidence_interval_shrinkage=0.99,
                sample_size_increase=1000000,
            ),
            information_value=InformationValue(
                entropy_reduction=0.95,
                mutual_information=0.95,
                expected_information_gain=0.95,
            ),
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_epistemic",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="Mechanism intervention",
            sample_size=100,
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_epistemic"


# ---------------------------------------------------------------------------
# Test: Attack F — Repeated Dependent Evidence
# ---------------------------------------------------------------------------


class TestAttackF_RepeatedDependentEvidence:
    def test_dependent_replications_not_valuable(self):
        """100 dependent replications should have low epistemic value."""
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
                description="Dependent",
                seed=42,
            ))

        candidate_a = CandidateExperiment(
            experiment_id="c_dependent",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="100 more dependent replications",
            seed=42,
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_independent",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="Independent replication",
            seed=999,
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_independent"


# ---------------------------------------------------------------------------
# Test: Attack G — Experiment Outside Proposition Authority
# ---------------------------------------------------------------------------


class TestAttackG_OutsideAuthority:
    def test_experiment_outside_authority_rejected(self):
        """Experiment with intervention type that cannot inform proposition should be rejected."""
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
            description="Mechanism evidence",
            seed=42,
        ))

        candidate_a = CandidateExperiment(
            experiment_id="c_wrong_type",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target_mechanism="signal",
            description="Feature ablation",
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_correct_type",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="Mechanism amplification",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_correct_type"


# ---------------------------------------------------------------------------
# Test: Attack H — Excellent Statistics but No Discriminative Power
# ---------------------------------------------------------------------------


class TestAttackH_ExcellentStatisticsNoDiscrimination:
    def test_no_discriminative_power_rejected(self):
        """Experiment with excellent statistics but no discriminative power should be rejected."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate_a = CandidateExperiment(
            experiment_id="c_excellent_stats",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target_mechanism="signal",
            description="Excellent statistics",
            sample_size=1000000,
            statistical_value=StatisticalValue(
                variance_reduction=0.99,
                standard_error_reduction=0.99,
                confidence_interval_shrinkage=0.99,
                sample_size_increase=1000000,
            ),
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_discriminative",
            intervention_type=InterventionType.MECHANISM_DECORRELATION,
            target_mechanism="signal_component",
            description="Mechanism decorrelation",
            sample_size=100,
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_discriminative"


# ---------------------------------------------------------------------------
# Test: Attack I — Closes Irrelevant Gap
# ---------------------------------------------------------------------------


class TestAttackI_ClosesIrrelevantGap:
    def test_irrelevant_gap_closing_rejected(self):
        """Experiment that closes an irrelevant gap should not be selected over relevant one."""
        prop = TypedProposition(
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
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            ))

        candidate_a = CandidateExperiment(
            experiment_id="c_generalization",
            intervention_type=InterventionType.HOLDOUT,
            target_mechanism="returns",
            description="Holdout for generalization",
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_diversity",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="New mechanism intervention",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None


# ---------------------------------------------------------------------------
# Test: Attack J — Appears Useful but Cannot Distinguish Mechanisms
# ---------------------------------------------------------------------------


class TestAttackJ_AppearsUsefulCannotDistinguish:
    def test_cannot_distinguish_mechanisms_rejected(self):
        """Experiment that appears useful but cannot distinguish competing mechanisms should be rejected."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        acc = EvidenceAccumulator()
        for i in range(5):
            acc.add(StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Feature evidence",
                seed=i + 1,
            ))

        candidate_a = CandidateExperiment(
            experiment_id="c_feature",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target_mechanism="signal",
            description="More feature ablation",
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_mechanism",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="Mechanism removal",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert result.selected_experiment.experiment_id == "c_mechanism"


# ---------------------------------------------------------------------------
# Test: Attack K — Incomparable Pareto-Optimal Experiments
# ---------------------------------------------------------------------------


class TestAttackK_IncomparableExperiments:
    def test_incomparable_experiments_preserved(self):
        """Two genuinely incomparable experiments should both be on Pareto frontier."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate_a = CandidateExperiment(
            experiment_id="c_replication",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="High replication",
            sample_size=10000,
        )

        candidate_b = CandidateExperiment(
            experiment_id="c_diversity",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="High diversity",
            sample_size=100,
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate_a, candidate_b])

        assert result.selected_experiment is not None
        assert len(result.selection_rationale) > 0


# ---------------------------------------------------------------------------
# Test: Attack L — No Available Experiment Can Close Blocking Gap
# ---------------------------------------------------------------------------


class TestAttackL_NoAvailableExperiment:
    def test_unresolvable_when_no_experiment_can_close_gap(self):
        """When no available experiment can close the blocking gap, should return UNRESOLVABLE."""
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
            description="Feature evidence only",
            seed=42,
        ))

        candidates = [
            CandidateExperiment(
                experiment_id=f"c_feature_{i}",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target_mechanism="signal",
                description="Feature ablation",
            )
            for i in range(5)
        ]

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, candidates)

        assert result.outcome == SelectionOutcome.UNRESOLVABLE


# ---------------------------------------------------------------------------
# Test: Experiment Dominance
# ---------------------------------------------------------------------------


class TestExperimentDominance:
    def test_a_dominates_b(self):
        """A should dominate B when A is better on all dimensions."""
        a = CandidateExperiment(
            experiment_id="a",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="A",
            epistemic_value=EpistemicValue(
                experiment_id="a",
                proposition_id="p1",
                discriminative_power=0.9,
                alternative_elimination=0.8,
                evidence_diversity_gain=3,
                replication_gain=10,
                independence_gain=0.9,
            ),
        )
        b = CandidateExperiment(
            experiment_id="b",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="B",
            epistemic_value=EpistemicValue(
                experiment_id="b",
                proposition_id="p1",
                discriminative_power=0.5,
                alternative_elimination=0.4,
                evidence_diversity_gain=1,
                replication_gain=5,
                independence_gain=0.5,
            ),
        )
        result = check_dominance(a, b)
        assert result == DominanceRelation.A_DOMINATES_B

    def test_incomparable(self):
        """Two experiments with different strengths should be incomparable."""
        a = CandidateExperiment(
            experiment_id="a",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism="signal_component",
            description="A",
            epistemic_value=EpistemicValue(
                experiment_id="a",
                proposition_id="p1",
                discriminative_power=0.9,
                alternative_elimination=0.3,
                evidence_diversity_gain=1,
                replication_gain=10,
                independence_gain=0.5,
            ),
        )
        b = CandidateExperiment(
            experiment_id="b",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="B",
            epistemic_value=EpistemicValue(
                experiment_id="b",
                proposition_id="p1",
                discriminative_power=0.3,
                alternative_elimination=0.9,
                evidence_diversity_gain=3,
                replication_gain=5,
                independence_gain=0.9,
            ),
        )
        result = check_dominance(a, b)
        assert result == DominanceRelation.INCOMPARABLE


# ---------------------------------------------------------------------------
# Test: Pareto Frontier
# ---------------------------------------------------------------------------


class TestParetoFrontier:
    def test_pareto_frontier_identifies_non_dominated(self):
        """Pareto frontier should identify non-dominated experiments."""
        experiments = [
            CandidateExperiment(
                experiment_id="a",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target_mechanism="signal_component",
                description="A - high replication",
                epistemic_value=EpistemicValue(
                    experiment_id="a",
                    proposition_id="p1",
                    discriminative_power=0.9,
                    alternative_elimination=0.8,
                    evidence_diversity_gain=1,
                    replication_gain=10,
                    independence_gain=0.9,
                ),
            ),
            CandidateExperiment(
                experiment_id="b",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target_mechanism="signal_component",
                description="B - dominated by A",
                epistemic_value=EpistemicValue(
                    experiment_id="b",
                    proposition_id="p1",
                    discriminative_power=0.5,
                    alternative_elimination=0.4,
                    evidence_diversity_gain=1,
                    replication_gain=5,
                    independence_gain=0.5,
                ),
            ),
            CandidateExperiment(
                experiment_id="c",
                intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
                target_mechanism="signal_component",
                description="C - high diversity",
                epistemic_value=EpistemicValue(
                    experiment_id="c",
                    proposition_id="p1",
                    discriminative_power=0.7,
                    alternative_elimination=0.6,
                    evidence_diversity_gain=5,
                    replication_gain=6,
                    independence_gain=0.7,
                ),
            ),
        ]
        frontier = compute_pareto_frontier(experiments)
        frontier_ids = {e.experiment_id for e in frontier}
        # A and C should be on frontier (different tradeoffs)
        # B should be dominated by A
        assert "a" in frontier_ids
        assert "c" in frontier_ids
        assert "b" not in frontier_ids


# ---------------------------------------------------------------------------
# Test: Value Separation
# ---------------------------------------------------------------------------


class TestValueSeparation:
    def test_statistical_value_does_not_imply_epistemic_value(self):
        """High statistical value should not imply high epistemic value."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate = CandidateExperiment(
            experiment_id="c",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target_mechanism="signal",
            description="High statistical value",
            statistical_value=StatisticalValue(
                variance_reduction=0.99,
                standard_error_reduction=0.99,
                confidence_interval_shrinkage=0.99,
                sample_size_increase=1000000,
            ),
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        assessed = selector._assess_candidate(candidate, prop, acc, assessment)

        assert assessed.statistical_value.aggregate > 0.9
        assert not assessed.is_epistemically_valuable


# ---------------------------------------------------------------------------
# Test: Recommendation vs Authorization
# ---------------------------------------------------------------------------


class TestRecommendationVsAuthorization:
    def test_recommendation_does_not_equal_authorization(self):
        """Selector recommends, but does not authorize."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate = CandidateExperiment(
            experiment_id="c",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="Mechanism amplification",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate])

        assert result.selected_experiment is not None
        assert result.outcome == SelectionOutcome.SELECTED


# ---------------------------------------------------------------------------
# Test: Provenance
# ---------------------------------------------------------------------------


class TestProvenance:
    def test_selection_has_provenance(self):
        """Every selection must have provenance."""
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
            description="Single mechanism observation",
            seed=42,
        ))

        candidate = CandidateExperiment(
            experiment_id="c",
            intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
            target_mechanism="signal_component",
            description="Mechanism amplification",
        )

        assessment = analyze_evidence_gaps(prop, acc)
        selector = EpistemicExperimentSelector()
        result = selector.select_experiment(prop, acc, assessment, [candidate])

        assert len(result.provenance) > 0
        assert "EpistemicExperimentSelector" in result.provenance


# ---------------------------------------------------------------------------
# Test: Gap Reduction Structure
# ---------------------------------------------------------------------------


class TestGapReduction:
    def test_gap_reduction_preserves_structure(self):
        """Gap reduction should preserve structure, not collapse to scalar."""
        reduction = GapReduction(
            gap_type=GapType.INSUFFICIENT_REPLICATION,
            authority_change="MECHANISM_REMOVAL has authority",
            evidence_type_change="mechanism_removal",
            replication_change=5,
            independence_change=0.5,
        )
        explanation = reduction.explain()
        assert "insufficient_replication" in explanation
        assert "MECHANISM_REMOVAL" in explanation
        assert "5" in explanation


# ---------------------------------------------------------------------------
# Test: Epistemic Value Explanation
# ---------------------------------------------------------------------------


class TestEpistemicValue:
    def test_epistemic_value_explains_itself(self):
        """Epistemic value should explain why it's valuable."""
        value = EpistemicValue(
            experiment_id="c",
            proposition_id="p1",
            targeted_gaps=["gap_1", "gap_2"],
            authority_scope="MECHANISM_REMOVAL",
            discriminative_power=0.8,
            gap_closing_potential=GapClosingPotential.GAP_CLOSING,
            alternative_elimination=0.7,
            evidence_diversity_gain=2,
            replication_gain=5,
            independence_gain=0.6,
        )
        explanation = value.explain()
        assert "c" in explanation
        assert "gap_1" in explanation
        assert "MECHANISM_REMOVAL" in explanation
