"""Epistemic Experiment Selection — choosing experiments by epistemic value.

Implements the architectural transition from "identify gaps" to
"select the experiment that most efficiently reduces the proposition's
epistemic boundary."

The central research question:
    Given multiple possible experiments, can the system select the
    experiment that most effectively reduces the proposition's epistemic
    gap while respecting intervention authority?

This is NOT active learning.
This is NOT Bayesian optimization.
This is NOT maximizing predictive performance.
This is NOT maximizing statistical significance.
This is NOT maximizing raw information gain.

The objective is epistemic:
    select the experiment that most efficiently reduces
    the proposition's epistemic boundary while remaining
    within authorized intervention space

Architecture:
    Proposition → Evidence → Epistemic Gaps → Candidate Experiments
        → Epistemic Selection → Governance → Authorization
        → Execution → Evidence → Epistemic Assessment

Invariants:
    Information gain != epistemic value.
    Statistical precision != increased authority.
    An experiment can be highly informative while being epistemically irrelevant.
    Recommendation != authorization.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceDimension,
    EvidenceProfile,
    StructuredEvidenceBundle,
    evaluate_structured_proposition,
)
from sas.quant.experiment.epistemic_gaps import (
    EpistemicGap,
    GapType,
    GapResolvability,
    GapClosingPotential,
    EvidenceSufficiencyAssessment,
    analyze_evidence_gaps,
    classify_gap_closing_potential,
)


# ---------------------------------------------------------------------------
# Value Types
# ---------------------------------------------------------------------------


class ValueDimension(str, Enum):
    """Three distinct value dimensions.

    These are NOT assumed to be correlated.
    An experiment can be high on one and low on others.
    """
    STATISTICAL = "statistical"
    INFORMATION = "information"
    EPISTEMIC = "epistemic"


@dataclass(frozen=True)
class StatisticalValue:
    """Statistical value of an experiment.

    Measures reduction in estimator variance, standard error, etc.
    Does NOT imply epistemic progress.
    """
    variance_reduction: float = 0.0
    standard_error_reduction: float = 0.0
    confidence_interval_shrinkage: float = 0.0
    sample_size_increase: int = 0

    @property
    def aggregate(self) -> float:
        """Aggregate statistical value (for comparison only)."""
        return (
            self.variance_reduction
            + self.standard_error_reduction
            + self.confidence_interval_shrinkage
        ) / 3.0


@dataclass(frozen=True)
class InformationValue:
    """Information-theoretic value of an experiment.

    Measures reduction in uncertainty over observations.
    Does NOT imply epistemic progress.
    """
    entropy_reduction: float = 0.0
    mutual_information: float = 0.0
    expected_information_gain: float = 0.0

    @property
    def aggregate(self) -> float:
        """Aggregate information value (for comparison only)."""
        return (
            self.entropy_reduction
            + self.mutual_information
            + self.expected_information_gain
        ) / 3.0


@dataclass(frozen=True)
class EpistemicValue:
    """Epistemic value of an experiment.

    Measures reduction in an authority-relevant epistemic gap.
    This is the primary value dimension for experiment selection.

    Does NOT collapse into a single scalar.
    The system explains WHY an experiment is valuable.
    """
    experiment_id: str
    proposition_id: str
    targeted_gaps: list[str] = field(default_factory=list)
    authority_scope: str = ""
    discriminative_power: float = 0.0
    gap_closing_potential: GapClosingPotential = GapClosingPotential.NON_GAP_CLOSING
    alternative_elimination: float = 0.0
    evidence_diversity_gain: int = 0
    temporal_coverage_gain: bool = False
    replication_gain: int = 0
    independence_gain: float = 0.0
    generalization_gain: bool = False
    provenance: str = ""

    def explain(self) -> str:
        """Explain why this experiment is valuable."""
        lines = [f"Epistemic Value for {self.experiment_id}:"]
        if self.targeted_gaps:
            lines.append(f"  Targets: {', '.join(self.targeted_gaps)}")
        if self.authority_scope:
            lines.append(f"  Authority: {self.authority_scope}")
        if self.discriminative_power > 0:
            lines.append(f"  Discriminative power: {self.discriminative_power:.2f}")
        if self.gap_closing_potential != GapClosingPotential.NON_GAP_CLOSING:
            lines.append(f"  Gap closing: {self.gap_closing_potential.value}")
        if self.alternative_elimination > 0:
            lines.append(f"  Alternative elimination: {self.alternative_elimination:.2f}")
        if self.evidence_diversity_gain > 0:
            lines.append(f"  Diversity gain: +{self.evidence_diversity_gain}")
        if self.temporal_coverage_gain:
            lines.append("  Temporal coverage: new period")
        if self.replication_gain > 0:
            lines.append(f"  Replication gain: +{self.replication_gain}")
        if self.independence_gain > 0:
            lines.append(f"  Independence gain: +{self.independence_gain:.2f}")
        if self.generalization_gain:
            lines.append("  Generalization: new environment")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gap Reduction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GapReduction:
    """Structured representation of how an experiment reduces a gap.

    Two experiments that both eliminate one gap may have very different
    epistemic consequences. This preserves that structure.
    """
    gap_type: GapType
    authority_change: str = ""
    evidence_type_change: str = ""
    intervention_scope_change: str = ""
    alternative_set_change: list[str] = field(default_factory=list)
    replication_change: int = 0
    independence_change: float = 0.0
    temporal_scope_change: str = ""
    generalization_scope_change: str = ""

    def explain(self) -> str:
        """Explain the gap reduction."""
        lines = [f"Gap Reduction: {self.gap_type.value}"]
        if self.authority_change:
            lines.append(f"  Authority: {self.authority_change}")
        if self.evidence_type_change:
            lines.append(f"  Evidence type: {self.evidence_type_change}")
        if self.intervention_scope_change:
            lines.append(f"  Intervention scope: {self.intervention_scope_change}")
        if self.alternative_set_change:
            lines.append(f"  Alternatives: {', '.join(self.alternative_set_change)}")
        if self.replication_change != 0:
            lines.append(f"  Replication: {self.replication_change:+d}")
        if self.independence_change != 0:
            lines.append(f"  Independence: {self.independence_change:+.2f}")
        if self.temporal_scope_change:
            lines.append(f"  Temporal: {self.temporal_scope_change}")
        if self.generalization_scope_change:
            lines.append(f"  Generalization: {self.generalization_scope_change}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Candidate Experiment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateExperiment:
    """A candidate experiment for selection."""
    experiment_id: str
    intervention_type: InterventionType
    target_mechanism: str
    description: str
    sample_size: int = 100
    seed: int = 0
    time_period: str = ""
    realization_id: str = ""

    # Value assessments
    statistical_value: StatisticalValue = field(default_factory=StatisticalValue)
    information_value: InformationValue = field(default_factory=InformationValue)
    epistemic_value: Optional[EpistemicValue] = None

    # Gap reduction
    gap_reductions: list[GapReduction] = field(default_factory=list)

    @property
    def is_epistemically_valuable(self) -> bool:
        """Check if experiment has epistemic value."""
        if self.epistemic_value is None:
            return False
        return self.epistemic_value.gap_closing_potential in {
            GapClosingPotential.GAP_CLOSING,
            GapClosingPotential.PARTIALLY_GAP_CLOSING,
        }


# ---------------------------------------------------------------------------
# Experiment Selection
# ---------------------------------------------------------------------------


class SelectionOutcome(str, Enum):
    """Outcome of experiment selection."""
    SELECTED = "selected"
    REJECTED = "rejected"
    INCOMPARABLE = "incomparable"
    UNRESOLVABLE = "unresolvable"


@dataclass(frozen=True)
class ExperimentSelection:
    """Result of experiment selection.

    Contains the selected experiment, rejected experiments,
    and full rationale.
    """
    selected_experiment: Optional[CandidateExperiment]
    rejected_experiments: list[CandidateExperiment] = field(default_factory=list)
    incomparable_experiments: list[CandidateExperiment] = field(default_factory=list)
    selection_rationale: str = ""
    targeted_gaps: list[str] = field(default_factory=list)
    authority_basis: str = ""
    expected_gap_reduction: list[GapReduction] = field(default_factory=list)
    unresolved_gaps_after_experiment: list[str] = field(default_factory=list)
    outcome: SelectionOutcome = SelectionOutcome.SELECTED
    provenance: str = ""

    def explain(self) -> str:
        """Generate comprehensive explanation."""
        lines = ["Experiment Selection Report"]
        lines.append("=" * 50)
        lines.append("")

        if self.outcome == SelectionOutcome.UNRESOLVABLE:
            lines.append("Outcome: UNRESOLVABLE_WITH_AVAILABLE_AUTHORITY")
            lines.append("")
            lines.append("No available experiment can close the blocking gap.")
            return "\n".join(lines)

        if self.selected_experiment:
            lines.append(f"Selected: {self.selected_experiment.experiment_id}")
            lines.append(f"  Intervention: {self.selected_experiment.intervention_type.value}")
            lines.append(f"  Target: {self.selected_experiment.target_mechanism}")
            lines.append("")

        if self.selection_rationale:
            lines.append(f"Rationale: {self.selection_rationale}")
            lines.append("")

        if self.targeted_gaps:
            lines.append("Targeted Gaps:")
            for g in self.targeted_gaps:
                lines.append(f"  - {g}")
            lines.append("")

        if self.authority_basis:
            lines.append(f"Authority Basis: {self.authority_basis}")
            lines.append("")

        if self.expected_gap_reduction:
            lines.append("Expected Gap Reduction:")
            for g in self.expected_gap_reduction:
                lines.append(g.explain())
            lines.append("")

        if self.rejected_experiments:
            lines.append("Rejected Experiments:")
            for r in self.rejected_experiments:
                lines.append(f"  - {r.experiment_id}: {r.description}")
            lines.append("")

        if self.incomparable_experiments:
            lines.append("Incomparable Experiments (Pareto-optimal):")
            for i in self.incomparable_experiments:
                lines.append(f"  - {i.experiment_id}: {i.description}")
            lines.append("")

        if self.unresolved_gaps_after_experiment:
            lines.append("Unresolved Gaps After Experiment:")
            for g in self.unresolved_gaps_after_experiment:
                lines.append(f"  - {g}")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Experiment Dominance
# ---------------------------------------------------------------------------


class DominanceRelation(str, Enum):
    """Dominance relation between two experiments."""
    A_DOMINATES_B = "a_dominates_b"
    B_DOMINATES_A = "b_dominates_a"
    INCOMPARABLE = "incomparable"
    EQUIVALENT = "equivalent"


def check_dominance(
    a: CandidateExperiment,
    b: CandidateExperiment,
) -> DominanceRelation:
    """Check whether experiment A dominates experiment B.

    A dominates B if A is at least as capable as B across all
    epistemically relevant dimensions and strictly better in at least
    one dimension, while remaining within the same authority boundary.
    """
    if a.epistemic_value is None or b.epistemic_value is None:
        return DominanceRelation.INCOMPARABLE

    a_val = a.epistemic_value
    b_val = b.epistemic_value

    # Check dimensions
    a_scores = [
        a_val.discriminative_power,
        a_val.alternative_elimination,
        float(a_val.evidence_diversity_gain),
        float(a_val.replication_gain),
        a_val.independence_gain,
    ]
    b_scores = [
        b_val.discriminative_power,
        b_val.alternative_elimination,
        float(b_val.evidence_diversity_gain),
        float(b_val.replication_gain),
        b_val.independence_gain,
    ]

    # Check if A >= B in all dimensions
    a_at_least_as_good = all(
        a_s >= b_s - 0.01 for a_s, b_s in zip(a_scores, b_scores)
    )
    # Check if A > B in at least one dimension
    a_strictly_better = any(
        a_s > b_s + 0.01 for a_s, b_s in zip(a_scores, b_scores)
    )

    # Check if B >= A in all dimensions
    b_at_least_as_good = all(
        b_s >= a_s - 0.01 for a_s, b_s in zip(a_scores, b_scores)
    )
    # Check if B > A in at least one dimension
    b_strictly_better = any(
        b_s > a_s + 0.01 for a_s, b_s in zip(a_scores, b_scores)
    )

    if a_at_least_as_good and a_strictly_better:
        return DominanceRelation.A_DOMINATES_B
    if b_at_least_as_good and b_strictly_better:
        return DominanceRelation.B_DOMINATES_A
    if a_at_least_as_good and b_at_least_as_good:
        return DominanceRelation.EQUIVALENT
    return DominanceRelation.INCOMPARABLE


# ---------------------------------------------------------------------------
# Pareto Frontier
# ---------------------------------------------------------------------------


def compute_pareto_frontier(
    experiments: list[CandidateExperiment],
) -> list[CandidateExperiment]:
    """Compute the epistemic Pareto frontier.

    Returns experiments that are non-dominated.
    Does not arbitrarily collapse the frontier into one scalar score.
    """
    if not experiments:
        return []

    frontier: list[CandidateExperiment] = []

    for exp in experiments:
        dominated = False
        for other in experiments:
            if exp.experiment_id == other.experiment_id:
                continue
            relation = check_dominance(other, exp)
            if relation == DominanceRelation.A_DOMINATES_B:
                dominated = True
                break
        if not dominated:
            frontier.append(exp)

    return frontier


# ---------------------------------------------------------------------------
# Epistemic Experiment Selector
# ---------------------------------------------------------------------------


class EpistemicExperimentSelector:
    """Selects experiments based on epistemic value.

    The selector:
    1. Analyzes epistemic gaps
    2. Assesses candidate experiments
    3. Computes Pareto frontier
    4. Selects the experiment that most reduces the blocking gap
    5. Explains the decision

    The selector does NOT authorize execution.
    It recommends. Governance authorizes.
    """

    def __init__(self, selection_policy: str = "gap_closing_priority"):
        self.selection_policy = selection_policy
        self.version = "1.0.0"

    def select_experiment(
        self,
        proposition: TypedProposition,
        evidence: EvidenceAccumulator,
        assessment: EvidenceSufficiencyAssessment,
        candidates: list[CandidateExperiment],
    ) -> ExperimentSelection:
        """Select the most valuable experiment.

        Returns an ExperimentSelection with full rationale.
        """
        if not candidates:
            return ExperimentSelection(
                selected_experiment=None,
                outcome=SelectionOutcome.UNRESOLVABLE,
                selection_rationale="No candidate experiments provided",
            )

        # Assess epistemic value for each candidate
        assessed_candidates = []
        for candidate in candidates:
            assessed = self._assess_candidate(
                candidate, proposition, evidence, assessment
            )
            assessed_candidates.append(assessed)

        # Filter out candidates with no epistemic value
        valuable = [c for c in assessed_candidates if c.is_epistemically_valuable]

        if not valuable:
            return ExperimentSelection(
                selected_experiment=None,
                rejected_experiments=assessed_candidates,
                outcome=SelectionOutcome.UNRESOLVABLE,
                selection_rationale=(
                    "No candidate experiment has epistemic value for "
                    "the current proposition and gaps."
                ),
            )

        # Compute Pareto frontier
        frontier = compute_pareto_frontier(valuable)

        # Select from frontier based on policy
        if len(frontier) == 1:
            selected = frontier[0]
            rejected = [c for c in assessed_candidates if c.experiment_id != selected.experiment_id]
            incomparable = []
        else:
            # Multiple Pareto-optimal experiments
            # Apply selection policy
            selected, incomparable = self._break_ties(frontier, assessment)
            rejected = [c for c in assessed_candidates if c.experiment_id != selected.experiment_id]
            rejected = [c for c in rejected if c not in incomparable]

        # Build rationale
        rationale = self._build_rationale(selected, assessment)

        # Identify expected gap reduction
        gap_reductions = selected.gap_reductions if selected else []

        # Identify unresolved gaps after experiment
        unresolved = self._identify_unresolved_gaps(selected, assessment)

        return ExperimentSelection(
            selected_experiment=selected,
            rejected_experiments=rejected,
            incomparable_experiments=incomparable,
            selection_rationale=rationale,
            targeted_gaps=selected.epistemic_value.targeted_gaps if selected and selected.epistemic_value else [],
            authority_basis=selected.epistemic_value.authority_scope if selected and selected.epistemic_value else "",
            expected_gap_reduction=gap_reductions,
            unresolved_gaps_after_experiment=unresolved,
            outcome=SelectionOutcome.SELECTED,
            provenance=f"EpistemicExperimentSelector v{self.version}",
        )

    def _assess_candidate(
        self,
        candidate: CandidateExperiment,
        proposition: TypedProposition,
        evidence: EvidenceAccumulator,
        assessment: EvidenceSufficiencyAssessment,
    ) -> CandidateExperiment:
        """Assess the epistemic value of a candidate experiment."""
        # Check if intervention has authority over proposition
        if not proposition.accepts_evidence_from(candidate.intervention_type):
            return CandidateExperiment(
                experiment_id=candidate.experiment_id,
                intervention_type=candidate.intervention_type,
                target_mechanism=candidate.target_mechanism,
                description=candidate.description,
                sample_size=candidate.sample_size,
                seed=candidate.seed,
                statistical_value=candidate.statistical_value,
                information_value=candidate.information_value,
                epistemic_value=EpistemicValue(
                    experiment_id=candidate.experiment_id,
                    proposition_id=proposition.proposition_id,
                    authority_scope="NONE - intervention lacks authority",
                    gap_closing_potential=GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY,
                ),
            )

        # Identify which gaps this experiment could close
        targeted_gaps = []
        gap_reductions = []
        for gap in assessment.epistemic_gaps:
            potential = classify_gap_closing_potential(
                gap, candidate.intervention_type, proposition
            )
            if potential in {
                GapClosingPotential.GAP_CLOSING,
                GapClosingPotential.PARTIALLY_GAP_CLOSING,
            }:
                targeted_gaps.append(gap.gap_id)
                gap_reductions.append(GapReduction(
                    gap_type=gap.gap_type,
                    authority_change=f"{candidate.intervention_type.value} has authority",
                    evidence_type_change=candidate.intervention_type.value,
                    intervention_scope_change=candidate.intervention_type.value,
                ))

        # Compute discriminative power
        disc_power = self._compute_discriminative_power(
            candidate, proposition, evidence
        )

        # Compute alternative elimination
        alt_elimination = self._compute_alternative_elimination(
            candidate, proposition, assessment
        )

        # Compute diversity gain
        current_diversity = len(set(
            b.intervention_type for b in evidence.bundles
        ))
        new_type = candidate.intervention_type
        diversity_gain = 1 if new_type not in {
            b.intervention_type for b in evidence.bundles
        } else 0

        # Compute temporal coverage gain
        current_periods = set(
            b.time_period for b in evidence.bundles if b.time_period
        )
        temporal_gain = candidate.time_period not in current_periods if candidate.time_period else False

        # Compute replication gain
        replication_gain = 1  # Each experiment adds one replication

        # Compute independence gain
        independence_gain = 0.0
        if candidate.seed != 0:
            current_seeds = set(b.seed for b in evidence.bundles if b.seed != 0)
            if candidate.seed not in current_seeds:
                independence_gain = 0.5

        # Compute generalization gain
        generalization_gain = candidate.intervention_type in {
            InterventionType.HOLDOUT,
            InterventionType.BOOTSTRAP,
            InterventionType.SUBSAMPLE,
        }

        epistemic_value = EpistemicValue(
            experiment_id=candidate.experiment_id,
            proposition_id=proposition.proposition_id,
            targeted_gaps=targeted_gaps,
            authority_scope=candidate.intervention_type.value,
            discriminative_power=disc_power,
            gap_closing_potential=(
                GapClosingPotential.GAP_CLOSING if targeted_gaps
                else GapClosingPotential.NON_GAP_CLOSING
            ),
            alternative_elimination=alt_elimination,
            evidence_diversity_gain=diversity_gain,
            temporal_coverage_gain=temporal_gain,
            replication_gain=replication_gain,
            independence_gain=independence_gain,
            generalization_gain=generalization_gain,
        )

        return CandidateExperiment(
            experiment_id=candidate.experiment_id,
            intervention_type=candidate.intervention_type,
            target_mechanism=candidate.target_mechanism,
            description=candidate.description,
            sample_size=candidate.sample_size,
            seed=candidate.seed,
            time_period=candidate.time_period,
            realization_id=candidate.realization_id,
            statistical_value=candidate.statistical_value,
            information_value=candidate.information_value,
            epistemic_value=epistemic_value,
            gap_reductions=gap_reductions,
        )

    def _compute_discriminative_power(
        self,
        candidate: CandidateExperiment,
        proposition: TypedProposition,
        evidence: EvidenceAccumulator,
    ) -> float:
        """Compute the discriminative power of a candidate experiment."""
        # Mechanism interventions have high discriminative power
        if candidate.intervention_type in {
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        }:
            return 0.8
        # Holdout has moderate discriminative power
        if candidate.intervention_type in {
            InterventionType.HOLDOUT,
            InterventionType.BOOTSTRAP,
        }:
            return 0.5
        # Feature interventions have low discriminative power for mechanism claims
        if candidate.intervention_type in {
            InterventionType.FEATURE_ABLATION,
            InterventionType.FEATURE_PERMUTATION,
        }:
            return 0.2
        return 0.3

    def _compute_alternative_elimination(
        self,
        candidate: CandidateExperiment,
        proposition: TypedProposition,
        assessment: EvidenceSufficiencyAssessment,
    ) -> float:
        """Compute how well a candidate eliminates competing alternatives."""
        # Check if any gaps are about competing mechanisms
        competing_gaps = [
            g for g in assessment.epistemic_gaps
            if g.gap_type == GapType.COMPETING_MECHANISM_UNRESOLVED
        ]
        if not competing_gaps:
            return 0.0

        # Mechanism interventions can eliminate alternatives
        if candidate.intervention_type in {
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        }:
            return 0.7
        return 0.1

    def _break_ties(
        self,
        frontier: list[CandidateExperiment],
        assessment: EvidenceSufficiencyAssessment,
    ) -> tuple[CandidateExperiment, list[CandidateExperiment]]:
        """Break ties among Pareto-optimal experiments.

        Uses the selection policy to choose.
        """
        if self.selection_policy == "gap_closing_priority":
            # Prioritize experiments that close the most gaps
            frontier.sort(
                key=lambda e: len(e.epistemic_value.targeted_gaps) if e.epistemic_value else 0,
                reverse=True,
            )
            selected = frontier[0]
            incomparable = frontier[1:]
            return selected, incomparable
        elif self.selection_policy == "discriminative_priority":
            # Prioritize experiments with highest discriminative power
            frontier.sort(
                key=lambda e: e.epistemic_value.discriminative_power if e.epistemic_value else 0,
                reverse=True,
            )
            selected = frontier[0]
            incomparable = frontier[1:]
            return selected, incomparable
        else:
            # Default: select first
            selected = frontier[0]
            incomparable = frontier[1:]
            return selected, incomparable

    def _build_rationale(
        self,
        selected: CandidateExperiment,
        assessment: EvidenceSufficiencyAssessment,
    ) -> str:
        """Build selection rationale."""
        if selected.epistemic_value is None:
            return "No epistemic value assessment available."

        parts = []
        if selected.epistemic_value.targeted_gaps:
            parts.append(
                f"Targets gaps: {', '.join(selected.epistemic_value.targeted_gaps)}"
            )
        if selected.epistemic_value.authority_scope:
            parts.append(
                f"Authority: {selected.epistemic_value.authority_scope}"
            )
        if selected.epistemic_value.discriminative_power > 0:
            parts.append(
                f"Discriminative power: {selected.epistemic_value.discriminative_power:.2f}"
            )

        return "; ".join(parts) if parts else "Selected by policy."

    def _identify_unresolved_gaps(
        self,
        selected: Optional[CandidateExperiment],
        assessment: EvidenceSufficiencyAssessment,
    ) -> list[str]:
        """Identify gaps that will remain after the experiment."""
        if selected is None or selected.epistemic_value is None:
            return [g.gap_id for g in assessment.epistemic_gaps]

        targeted = set(selected.epistemic_value.targeted_gaps)
        unresolved = [
            g.gap_id for g in assessment.epistemic_gaps
            if g.gap_id not in targeted
        ]
        return unresolved


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def select_experiment(
    proposition: TypedProposition,
    evidence: EvidenceAccumulator,
    candidates: list[CandidateExperiment],
    selection_policy: str = "gap_closing_priority",
) -> ExperimentSelection:
    """Convenience function to select an experiment."""
    assessment = analyze_evidence_gaps(proposition, evidence)
    selector = EpistemicExperimentSelector(selection_policy=selection_policy)
    return selector.select_experiment(proposition, evidence, assessment, candidates)


def generate_selection_report(selection: ExperimentSelection) -> str:
    """Generate a human-readable selection report."""
    return selection.explain()
