"""Epistemic Gaps — structured representation of what evidence is missing.

Implements the architectural transition from "evaluate evidence" to
"reason about what evidence is required."

The central research question:
    Can an epistemic system reason not only about the evidence it has,
    but about the specific evidence it lacks and the experiments required
    to obtain it?

Architecture:
    Observation → Candidate Proposition → Typed Proposition → Evidence
        → Evidence Structure → Epistemic Gaps → Experimental Design
        → New Evidence → Sufficiency Assessment → Epistemic Authority
        → Governance

Invariants:
    An epistemic gap is a statement about missing authority, not merely
    missing data.

    Resolvable insufficiency must be distinguished from unavailable authority.

    Evidence quantity cannot substitute for missing evidence type.
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
    evaluate_typed_proposition,
)
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
from sas.quant.experiment.experimental_design import (
    AgentHypothesis,
    DesignSufficiencyResult,
    evaluate_design_sufficiency,
)
from sas.quant.experiment.intervention_semantics import (
    MechanismIntervention,
    apply_mechanism_intervention,
)
from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
)


# ---------------------------------------------------------------------------
# Gap Classification
# ---------------------------------------------------------------------------


class GapType(str, Enum):
    """Types of epistemic gaps.

    Each gap type represents a specific kind of insufficiency.
    Gaps are NOT confidence scores — they are structural statements
    about what evidence is missing and why it matters.
    """
    INSUFFICIENT_REPLICATION = "insufficient_replication"
    DEPENDENT_EVIDENCE = "dependent_evidence"
    INSUFFICIENT_INTERVENTION_DIVERSITY = "insufficient_intervention_diversity"
    COMPETING_MECHANISM_UNRESOLVED = "competing_mechanism_unresolved"
    TEMPORAL_ROBUSTNESS_UNESTABLISHED = "temporal_robustness_unestablished"
    GENERALIZATION_UNESTABLISHED = "generalization_unestablished"
    CAUSAL_AUTHORITY_UNAVAILABLE = "causal_authority_unavailable"
    PROPOSITION_EXPERIMENT_TYPE_MISMATCH = "proposition_experiment_type_mismatch"
    OBSERVATIONAL_EQUIVALENCE_UNRESOLVED = "observational_equivalence_unresolved"
    INSUFFICIENT_EFFECT_MAGNITUDE = "insufficient_effect_magnitude"
    WRONG_INTERVENTION_TYPE = "wrong_intervention_type"
    INSUFFICIENT_INDEPENDENCE = "insufficient_independence"


class GapResolvability(str, Enum):
    """Whether a gap can be closed with available authority."""
    RESOLVABLE = "resolvable"
    PARTIALLY_RESOLVABLE = "partially_resolvable"
    UNRESOLVABLE_WITH_AVAILABLE_AUTHORITY = "unresolvable_with_available_authority"
    UNKNOWN = "unknown"


class GapClosingPotential(str, Enum):
    """Classification of an experiment's potential to close a gap."""
    GAP_CLOSING = "gap_closing"
    PARTIALLY_GAP_CLOSING = "partially_gap_closing"
    NON_GAP_CLOSING = "non_gap_closing"
    IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY = "impossible_with_available_authority"


# ---------------------------------------------------------------------------
# Epistemic Gap
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicGap:
    """Immutable representation of why a proposition is not yet established.

    Each gap explains:
    1. What evidence exists.
    2. What it establishes.
    3. What it does not establish.
    4. Why the missing evidence matters.
    5. Which experiment or intervention could potentially close the gap.

    A gap is NOT a confidence score. It is a structural statement about
    missing authority.
    """
    gap_id: str
    proposition_id: str
    gap_type: GapType
    dimension: EvidenceDimension
    current_state: str  # Human-readable description of current evidence
    required_evidence_type: str  # What kind of evidence is needed
    missing_information: str  # What specific information is missing
    blocking_alternatives: list[str] = field(default_factory=list)
    authority_boundary: str = ""  # Which authority boundary blocks
    resolvability: GapResolvability = GapResolvability.UNKNOWN
    provenance: str = ""  # How this gap was identified

    def explain(self) -> str:
        """Generate human-readable explanation of the gap."""
        lines = [
            f"Gap: {self.gap_type.value}",
            f"  Current: {self.current_state}",
            f"  Required: {self.required_evidence_type}",
            f"  Missing: {self.missing_information}",
            f"  Resolvability: {self.resolvability.value}",
        ]
        if self.blocking_alternatives:
            lines.append(f"  Blocking alternatives: {', '.join(self.blocking_alternatives)}")
        if self.authority_boundary:
            lines.append(f"  Authority boundary: {self.authority_boundary}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Candidate Experiment for Gap Closing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateExperiment:
    """An experiment that could potentially close an epistemic gap."""
    experiment_id: str
    target_gap: str
    intervention_type: InterventionType
    target_mechanism: str
    description: str
    gap_closing_potential: GapClosingPotential = GapClosingPotential.NON_GAP_CLOSING
    authority_basis: str = ""  # Why this intervention has authority
    expected_effect: str = ""  # What effect this experiment would have

    def explain(self) -> str:
        lines = [
            f"Candidate: {self.experiment_id}",
            f"  Target gap: {self.target_gap}",
            f"  Intervention: {self.intervention_type.value}",
            f"  Potential: {self.gap_closing_potential.value}",
        ]
        if self.authority_basis:
            lines.append(f"  Authority: {self.authority_basis}")
        if self.expected_effect:
            lines.append(f"  Expected: {self.expected_effect}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evidence Sufficiency Assessment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceSufficiencyAssessment:
    """Complete assessment of evidence sufficiency for a proposition.

    Contains:
    - What is established
    - What is unresolved
    - What gaps exist
    - What alternatives block
    - What experiments could close gaps
    - What authority is unavailable
    """
    proposition_id: str
    status: str  # SUPPORTED, REFUTED, INCONCLUSIVE
    established: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    epistemic_gaps: list[EpistemicGap] = field(default_factory=list)
    blocking_alternatives: list[str] = field(default_factory=list)
    available_gap_closing_experiments: list[CandidateExperiment] = field(default_factory=list)
    unavailable_authority: list[str] = field(default_factory=list)
    provenance: str = ""

    @property
    def is_supported(self) -> bool:
        return self.status == "SUPPORTED"

    @property
    def has_gaps(self) -> bool:
        return len(self.epistemic_gaps) > 0

    @property
    def has_unavailable_authority(self) -> bool:
        return len(self.unavailable_authority) > 0

    @property
    def resolvable_gaps(self) -> list[EpistemicGap]:
        return [
            g for g in self.epistemic_gaps
            if g.resolvability == GapResolvability.RESOLVABLE
        ]

    @property
    def unresolvable_gaps(self) -> list[EpistemicGap]:
        return [
            g for g in self.epistemic_gaps
            if g.resolvability == GapResolvability.UNRESOLVABLE_WITH_AVAILABLE_AUTHORITY
        ]

    def explain(self) -> str:
        """Generate comprehensive explanation."""
        lines = [
            f"Proposition: {self.proposition_id}",
            f"Status: {self.status}",
            "",
        ]
        if self.established:
            lines.append("Established:")
            for e in self.established:
                lines.append(f"  [+] {e}")
            lines.append("")
        if self.unresolved:
            lines.append("Unresolved:")
            for u in self.unresolved:
                lines.append(f"  [-] {u}")
            lines.append("")
        if self.epistemic_gaps:
            lines.append("Epistemic Gaps:")
            for g in self.epistemic_gaps:
                lines.append(g.explain())
            lines.append("")
        if self.blocking_alternatives:
            lines.append("Blocking Alternatives:")
            for b in self.blocking_alternatives:
                lines.append(f"  [-] {b}")
            lines.append("")
        if self.available_gap_closing_experiments:
            lines.append("Available Gap-Closing Experiments:")
            for e in self.available_gap_closing_experiments:
                lines.append(e.explain())
            lines.append("")
        if self.unavailable_authority:
            lines.append("Unavailable Authority:")
            for u in self.unavailable_authority:
                lines.append(f"  [-] {u}")
            lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evidence Gap Analyzer
# ---------------------------------------------------------------------------


def analyze_evidence_gaps(
    proposition: TypedProposition,
    accumulator: EvidenceAccumulator,
    available_interventions: Optional[list[InterventionType]] = None,
    known_alternatives: Optional[list[str]] = None,
) -> EvidenceSufficiencyAssessment:
    """Analyze evidence gaps for a proposition.

    This is the core function that transitions from "evaluate evidence"
    to "reason about what evidence is required."

    It distinguishes between:
    - insufficient evidence (more evidence of the right type could help)
    - evidence that cannot possibly establish the proposition under
      currently available experimental authority
    """
    if available_interventions is None:
        available_interventions = list(InterventionType)
    if known_alternatives is None:
        known_alternatives = []

    profile = accumulator.compute_profile()
    replication = accumulator.compute_replication_record()

    established: list[str] = []
    unresolved: list[str] = []
    gaps: list[EpistemicGap] = []
    blocking_alternatives: list[str] = []
    available_experiments: list[CandidateExperiment] = []
    unavailable_authority: list[str] = []

    # --- Check magnitude ---
    if profile.magnitude > 0.5:
        established.append(f"effect magnitude ({profile.magnitude:.2f})")
    else:
        unresolved.append(f"effect magnitude ({profile.magnitude:.2f})")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_magnitude",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.INSUFFICIENT_EFFECT_MAGNITUDE,
            dimension=EvidenceDimension.MAGNITUDE,
            current_state=f"magnitude = {profile.magnitude:.2f}",
            required_evidence_type="larger effect or more evidence",
            missing_information="Effect size is below the threshold for meaningful evidence",
            resolvability=GapResolvability.RESOLVABLE,
        ))

    # --- Check replication ---
    if profile.replication >= 3:
        established.append(f"replication ({profile.replication} trials)")
    else:
        unresolved.append(f"replication ({profile.replication} trials)")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_replication",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.INSUFFICIENT_REPLICATION,
            dimension=EvidenceDimension.REPLICATION,
            current_state=f"replication = {profile.replication}",
            required_evidence_type="at least 3 independent replications",
            missing_information="Too few replications to establish consistency",
            resolvability=GapResolvability.RESOLVABLE,
        ))
        # Suggest gap-closing experiment
        available_experiments.append(CandidateExperiment(
            experiment_id=f"exp_{proposition.proposition_id}_replication",
            target_gap=f"gap_{proposition.proposition_id}_replication",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism=proposition.target,
            description="New replication with different seed",
            gap_closing_potential=GapClosingPotential.GAP_CLOSING,
            authority_basis="MECHANISM_REMOVAL has authority over MECHANISM_DEPENDENCY",
            expected_effect="Increases replication count",
        ))

    # --- Check independence ---
    if profile.independence >= 0.5:
        established.append(f"independence ({profile.independence:.2f})")
    else:
        unresolved.append(f"independence ({profile.independence:.2f})")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_independence",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.DEPENDENT_EVIDENCE,
            dimension=EvidenceDimension.INDEPENDENCE,
            current_state=f"independence = {profile.independence:.2f}",
            required_evidence_type="evidence from different seeds or realizations",
            missing_information="Evidence items are correlated (same seed/realization)",
            resolvability=GapResolvability.RESOLVABLE,
        ))
        available_experiments.append(CandidateExperiment(
            experiment_id=f"exp_{proposition.proposition_id}_independence",
            target_gap=f"gap_{proposition.proposition_id}_independence",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target_mechanism=proposition.target,
            description="Replication with different random seed",
            gap_closing_potential=GapClosingPotential.GAP_CLOSING,
            authority_basis="Different seed breaks correlation",
            expected_effect="Increases independence score",
        ))

    # --- Check intervention diversity ---
    if profile.intervention_diversity >= 2:
        established.append(f"intervention diversity ({profile.intervention_diversity} types)")
    else:
        unresolved.append(f"intervention diversity ({profile.intervention_diversity} types)")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_diversity",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.INSUFFICIENT_INTERVENTION_DIVERSITY,
            dimension=EvidenceDimension.INTERVENTION_DIVERSITY,
            current_state=f"diversity = {profile.intervention_diversity}",
            required_evidence_type="evidence from multiple intervention classes",
            missing_information="All evidence comes from the same intervention type",
            resolvability=GapResolvability.RESOLVABLE,
        ))
        # Suggest additional intervention types
        if InterventionType.MECHANISM_AMPLIFICATION in available_interventions:
            available_experiments.append(CandidateExperiment(
                experiment_id=f"exp_{proposition.proposition_id}_amplification",
                target_gap=f"gap_{proposition.proposition_id}_diversity",
                intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
                target_mechanism=proposition.target,
                description="Mechanism amplification intervention",
                gap_closing_potential=GapClosingPotential.GAP_CLOSING,
                authority_basis="MECHANISM_AMPLIFICATION has authority over MECHANISM_DEPENDENCY",
                expected_effect="Adds new intervention class",
            ))
        if InterventionType.MECHANISM_DECORRELATION in available_interventions:
            available_experiments.append(CandidateExperiment(
                experiment_id=f"exp_{proposition.proposition_id}_decorrelation",
                target_gap=f"gap_{proposition.proposition_id}_diversity",
                intervention_type=InterventionType.MECHANISM_DECORRELATION,
                target_mechanism=proposition.target,
                description="Mechanism decorrelation intervention",
                gap_closing_potential=GapClosingPotential.GAP_CLOSING,
                authority_basis="MECHANISM_DECORRELATION has authority over MECHANISM_DEPENDENCY",
                expected_effect="Adds new intervention class",
            ))

    # --- Check temporal robustness ---
    if profile.temporal_robustness:
        established.append("temporal robustness")
    else:
        unresolved.append("temporal robustness")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_temporal",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.TEMPORAL_ROBUSTNESS_UNESTABLISHED,
            dimension=EvidenceDimension.TEMPORAL_ROBUSTNESS,
            current_state="single time period",
            required_evidence_type="evidence from multiple time periods",
            missing_information="All evidence from same time period",
            resolvability=GapResolvability.RESOLVABLE,
        ))

    # --- Check generalization ---
    if profile.generalization:
        established.append("generalization")
    else:
        unresolved.append("generalization")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_generalization",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.GENERALIZATION_UNESTABLISHED,
            dimension=EvidenceDimension.GENERALIZATION,
            current_state="no holdout evidence",
            required_evidence_type="holdout or out-of-sample evidence",
            missing_information="No evidence from holdout or bootstrap",
            resolvability=GapResolvability.RESOLVABLE,
        ))
        if InterventionType.HOLDOUT in available_interventions:
            available_experiments.append(CandidateExperiment(
                experiment_id=f"exp_{proposition.proposition_id}_holdout",
                target_gap=f"gap_{proposition.proposition_id}_generalization",
                intervention_type=InterventionType.HOLDOUT,
                target_mechanism=proposition.target,
                description="Holdout replication",
                gap_closing_potential=GapClosingPotential.GAP_CLOSING,
                authority_basis="HOLDOUT has authority over GENERALIZATION",
                expected_effect="Establishes generalization",
            ))

    # --- Check alternative exclusion ---
    if profile.alternative_exclusion > 0.5:
        established.append(f"alternative exclusion ({profile.alternative_exclusion:.2f})")
    else:
        unresolved.append(f"alternative exclusion ({profile.alternative_exclusion:.2f})")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_alternatives",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.COMPETING_MECHANISM_UNRESOLVED,
            dimension=EvidenceDimension.ALTERNATIVE_EXCLUSION,
            current_state=f"exclusion = {profile.alternative_exclusion:.2f}",
            required_evidence_type="interventions that exclude competing mechanisms",
            missing_information="Competing mechanisms not adequately tested",
            blocking_alternatives=known_alternatives,
            resolvability=GapResolvability.PARTIALLY_RESOLVABLE,
        ))

    # --- Check proposition-specific authority requirements ---
    if proposition.proposition_type == PropositionType.CAUSAL_CLAIM:
        # Causal claims require mechanism-level evidence
        has_mechanism_evidence = any(
            b.intervention_type in {
                InterventionType.MECHANISM_REMOVAL,
                InterventionType.MECHANISM_AMPLIFICATION,
                InterventionType.MECHANISM_DECORRELATION,
            }
            for b in accumulator.bundles
        )
        if not has_mechanism_evidence:
            gaps.append(EpistemicGap(
                gap_id=f"gap_{proposition.proposition_id}_causal",
                proposition_id=proposition.proposition_id,
                gap_type=GapType.CAUSAL_AUTHORITY_UNAVAILABLE,
                dimension=EvidenceDimension.INTERVENTION_DIVERSITY,
                current_state="no mechanism-level evidence",
                required_evidence_type="mechanism intervention (removal, amplification, or decorrelation)",
                missing_information="Causal claims require mechanism-level authority",
                authority_boundary="CAUSAL_CLAIM requires MECHANISM_* interventions",
                resolvability=GapResolvability.RESOLVABLE,
            ))

    # --- Check for wrong intervention type ---
    wrong_type_evidence = [
        b for b in accumulator.bundles
        if not b.can_inform(proposition)
    ]
    if wrong_type_evidence:
        unresolved.append("wrong intervention type evidence")
        gaps.append(EpistemicGap(
            gap_id=f"gap_{proposition.proposition_id}_wrong_type",
            proposition_id=proposition.proposition_id,
            gap_type=GapType.WRONG_INTERVENTION_TYPE,
            dimension=EvidenceDimension.INTERVENTION_DIVERSITY,
            current_state=f"{len(wrong_type_evidence)} evidence items from wrong intervention type",
            required_evidence_type=f"evidence from {proposition.proposition_type.value}-authorized interventions",
            missing_information="Evidence cannot inform this proposition type",
            authority_boundary=f"{wrong_type_evidence[0].intervention_type.value} cannot inform {proposition.proposition_type.value}",
            resolvability=GapResolvability.RESOLVABLE,
        ))

    # --- Determine overall status ---
    if (
        profile.magnitude > 0.5
        and profile.replication >= 3
        and profile.independence >= 0.5
        and profile.intervention_diversity >= 2
        and not wrong_type_evidence
    ):
        status = "SUPPORTED"
    elif profile.magnitude < -0.5:
        status = "REFUTED"
    else:
        status = "INCONCLUSIVE"

    # --- Identify unavailable authority ---
    # Check if any required intervention types are not available
    required_for_proposition = set()
    if proposition.proposition_type == PropositionType.MECHANISM_DEPENDENCY:
        required_for_proposition = {
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        }
    elif proposition.proposition_type == PropositionType.CAUSAL_CLAIM:
        required_for_proposition = {
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        }
    elif proposition.proposition_type == PropositionType.GENERALIZATION:
        required_for_proposition = {
            InterventionType.HOLDOUT,
            InterventionType.BOOTSTRAP,
            InterventionType.SUBSAMPLE,
        }

    missing_interventions = required_for_proposition - set(available_interventions)
    for mi in missing_interventions:
        unavailable_authority.append(
            f"{mi.value} not available in current experimental environment"
        )

    return EvidenceSufficiencyAssessment(
        proposition_id=proposition.proposition_id,
        status=status,
        established=established,
        unresolved=unresolved,
        epistemic_gaps=gaps,
        blocking_alternatives=blocking_alternatives,
        available_gap_closing_experiments=available_experiments,
        unavailable_authority=unavailable_authority,
        provenance="analyze_evidence_gaps v1.0",
    )


# ---------------------------------------------------------------------------
# Gap-Closing Experiment Classifier
# ---------------------------------------------------------------------------


def classify_gap_closing_potential(
    gap: EpistemicGap,
    candidate_intervention: InterventionType,
    proposition: TypedProposition,
) -> GapClosingPotential:
    """Classify whether an intervention can close a specific gap.

    This connects the gap representation to the experimental-design
    subsystem by determining whether a candidate experiment has
    authority over the gap.
    """
    # Check if intervention has authority over the proposition
    if not proposition.accepts_evidence_from(candidate_intervention):
        return GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY

    # Check gap-specific logic
    if gap.gap_type == GapType.INSUFFICIENT_REPLICATION:
        # Any authorized intervention can increase replication
        if proposition.accepts_evidence_from(candidate_intervention):
            return GapClosingPotential.GAP_CLOSING
        return GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY

    elif gap.gap_type == GapType.DEPENDENT_EVIDENCE:
        # Need a different seed/realization
        if proposition.accepts_evidence_from(candidate_intervention):
            return GapClosingPotential.GAP_CLOSING
        return GapClosingPotential.NON_GAP_CLOSING

    elif gap.gap_type == GapType.INSUFFICIENT_INTERVENTION_DIVERSITY:
        # Need a different intervention type
        if candidate_intervention != gap.current_state:
            return GapClosingPotential.GAP_CLOSING
        return GapClosingPotential.NON_GAP_CLOSING

    elif gap.gap_type == GapType.WRONG_INTERVENTION_TYPE:
        # Need the right intervention type
        if proposition.accepts_evidence_from(candidate_intervention):
            return GapClosingPotential.GAP_CLOSING
        return GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY

    elif gap.gap_type == GapType.CAUSAL_AUTHORITY_UNAVAILABLE:
        # Need mechanism-level authority
        if candidate_intervention in {
            InterventionType.MECHANISM_REMOVAL,
            InterventionType.MECHANISM_AMPLIFICATION,
            InterventionType.MECHANISM_DECORRELATION,
        }:
            return GapClosingPotential.GAP_CLOSING
        return GapClosingPotential.IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY

    elif gap.gap_type == GapType.GENERALIZATION_UNESTABLISHED:
        if candidate_intervention in {
            InterventionType.HOLDOUT,
            InterventionType.BOOTSTRAP,
            InterventionType.SUBSAMPLE,
        }:
            return GapClosingPotential.GAP_CLOSING
        return GapClosingPotential.NON_GAP_CLOSING

    elif gap.gap_type == GapType.TEMPORAL_ROBUSTNESS_UNESTABLISHED:
        # Need evidence from a different time period
        if proposition.accepts_evidence_from(candidate_intervention):
            return GapClosingPotential.PARTIALLY_GAP_CLOSING
        return GapClosingPotential.NON_GAP_CLOSING

    elif gap.gap_type == GapType.COMPETING_MECHANISM_UNRESOLVED:
        # Need interventions that exclude competing mechanisms
        if proposition.accepts_evidence_from(candidate_intervention):
            return GapClosingPotential.PARTIALLY_GAP_CLOSING
        return GapClosingPotential.NON_GAP_CLOSING

    return GapClosingPotential.NON_GAP_CLOSING


# ---------------------------------------------------------------------------
# Counterfactual Experimental Design
# ---------------------------------------------------------------------------


def design_gap_closing_experiments(
    assessment: EvidenceSufficiencyAssessment,
    available_interventions: list[InterventionType],
    proposition: TypedProposition,
) -> list[CandidateExperiment]:
    """Generate candidate experiments for each epistemic gap.

    For each gap, determine whether there exists an experiment
    capable of addressing it.
    """
    candidates: list[CandidateExperiment] = []

    for gap in assessment.epistemic_gaps:
        for intervention in available_interventions:
            potential = classify_gap_closing_potential(gap, intervention, proposition)
            if potential in {
                GapClosingPotential.GAP_CLOSING,
                GapClosingPotential.PARTIALLY_GAP_CLOSING,
            }:
                candidates.append(CandidateExperiment(
                    experiment_id=f"exp_{gap.gap_id}_{intervention.value}",
                    target_gap=gap.gap_id,
                    intervention_type=intervention,
                    target_mechanism=proposition.target,
                    description=f"Address {gap.gap_type.value} via {intervention.value}",
                    gap_closing_potential=potential,
                    authority_basis=f"{intervention.value} has authority over {proposition.proposition_type.value}",
                    expected_effect=f"Closes {gap.gap_type.value}",
                ))

    return candidates


# ---------------------------------------------------------------------------
# Minimal Evidence Set Analysis
# ---------------------------------------------------------------------------


def analyze_minimal_evidence_set(
    proposition: TypedProposition,
    evidence_items: list[StructuredEvidenceBundle],
) -> dict:
    """Determine whether a subset of evidence establishes the proposition.

    The objective is NOT to find a universal numeric threshold.
    The objective is to determine whether sufficiency is fundamentally
    a property of the structure and provenance of the evidence set.

    Returns a dict with:
    - minimal_subset: the smallest subset that satisfies the proposition
    - is_structural: whether sufficiency depends on structure vs quantity
    - structural_dependencies: which dimensions are required
    """
    if not evidence_items:
        return {
            "minimal_subset": [],
            "is_structural": True,
            "structural_dependencies": ["replication", "independence", "intervention_diversity"],
            "reasoning": "No evidence provided",
        }

    # Try all subsets (for small sets) to find minimal sufficient subset
    from itertools import combinations

    best_subset: list[StructuredEvidenceBundle] = []
    found_sufficient = False

    for size in range(1, len(evidence_items) + 1):
        for subset in combinations(evidence_items, size):
            acc = EvidenceAccumulator()
            for item in subset:
                acc.add(item)
            result = evaluate_structured_proposition(proposition, acc)
            if result.status == "SUPPORTED":
                if not found_sufficient or len(subset) < len(best_subset):
                    best_subset = list(subset)
                    found_sufficient = True
                    break
        if found_sufficient:
            break

    # Analyze structural dependencies
    structural_deps: list[str] = []
    if found_sufficient:
        acc = EvidenceAccumulator()
        for item in best_subset:
            acc.add(item)
        profile = acc.compute_profile()

        if profile.replication >= 3:
            structural_deps.append("replication")
        if profile.independence >= 0.5:
            structural_deps.append("independence")
        if profile.intervention_diversity >= 2:
            structural_deps.append("intervention_diversity")
        if profile.temporal_robustness:
            structural_deps.append("temporal_robustness")
        if profile.generalization:
            structural_deps.append("generalization")

    return {
        "minimal_subset": [b.evidence_id for b in best_subset],
        "is_structural": True,
        "structural_dependencies": structural_deps,
        "reasoning": (
            f"Minimal sufficient subset has {len(best_subset)} items "
            f"(from {len(evidence_items)} total)"
            if found_sufficient
            else "No sufficient subset found",
        ),
    }
