"""Evidence Structure — structured representation of epistemic evidence.

Implements the architectural law:
    Evidence is not scalar.

The previous representation reduced evidence to a single float (effect_size).
This module models evidence as a structured object with multiple dimensions:

    Evidence
       │
       ├── magnitude
       ├── consistency
       ├── replication
       ├── independence
       ├── intervention diversity
       ├── temporal robustness
       ├── generalization
       └── alternative exclusion
              │
              ▼
       Evidence Sufficiency
              │
              ▼
       Proposition Status

Invariant:
    Evidence accumulation must preserve the structure by which evidence
    was obtained. 10 correlated observations are not equivalent to 3
    independent replications.
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


# ---------------------------------------------------------------------------
# Evidence Dimensions
# ---------------------------------------------------------------------------


class EvidenceDimension(str, Enum):
    """Dimensions along which evidence can vary.

    Each dimension captures a distinct aspect of evidence quality.
    A proposition's evidence contract may require specific thresholds
    on specific dimensions.
    """
    MAGNITUDE = "magnitude"
    CONSISTENCY = "consistency"
    REPLICATION = "replication"
    INDEPENDENCE = "independence"
    INTERVENTION_DIVERSITY = "intervention_diversity"
    TEMPORAL_ROBUSTNESS = "temporal_robustness"
    GENERALIZATION = "generalization"
    ALTERNATIVE_EXCLUSION = "alternative_exclusion"


# ---------------------------------------------------------------------------
# Evidence Independence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceIndependence:
    """Measures the independence between two pieces of evidence.

    Two evidence items are independent if they were obtained from:
    - Different random seeds
    - Different time periods
    - Different interventions
    - Different underlying realizations

    Correlation is measured as a float in [0, 1] where:
    - 0.0 = perfectly independent
    - 1.0 = perfectly correlated (identical copies)
    """
    evidence_id_a: str
    evidence_id_b: str
    correlation: float  # 0 = independent, 1 = perfectly correlated
    shared_seed: bool = False
    shared_intervention: bool = False
    shared_time_period: bool = False

    @property
    def is_independent(self) -> bool:
        """Check if evidence is effectively independent."""
        return self.correlation < 0.3 and not self.shared_seed

    @property
    def is_dependent(self) -> bool:
        """Check if evidence is effectively dependent."""
        return not self.is_independent


# ---------------------------------------------------------------------------
# Replication Record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReplicationRecord:
    """Records the replication structure of evidence.

    Tracks:
    - How many independent replications exist
    - How many seeds were used
    - Whether replications agree (consistency)
    - Whether replications are truly independent
    """
    n_replications: int
    n_seeds: int
    n_independent: int  # Number of independent replications
    consistency_score: float  # 0 = contradictory, 1 = perfectly consistent
    independence_score: float  # 0 = all correlated, 1 = all independent
    seed_ids: list[int] = field(default_factory=list)

    @property
    def effective_evidence(self) -> float:
        """Compute effective evidence count.

        This is the number of independent, consistent replications.
        Correlated replications count for less than 1.0 each.
        Contradictory replications reduce the count.
        """
        return self.n_independent * self.consistency_score * self.independence_score


# ---------------------------------------------------------------------------
# Structured Evidence Bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StructuredEvidenceBundle:
    """Evidence with full structural provenance.

    Unlike the flat EvidenceBundle, this preserves:
    - The intervention that produced it
    - The seed used
    - The time period
    - The underlying realization
    - The relationship to other evidence
    """
    evidence_id: str
    intervention_type: InterventionType
    target: str
    effect_size: float
    description: str
    seed: int = 0
    time_period: str = ""
    realization_id: str = ""
    proposition_types_informed: set[PropositionType] = field(default_factory=set)
    authority_level: int = 0

    # Structural metadata
    is_replication: bool = False
    parent_evidence_id: Optional[str] = None
    independence_from_others: float = 1.0  # 1.0 = fully independent

    def can_inform(self, proposition: TypedProposition) -> bool:
        """Check whether this evidence can inform a proposition."""
        return proposition.accepts_evidence_from(self.intervention_type)

    def correlation_with(self, other: "StructuredEvidenceBundle") -> float:
        """Compute correlation with another evidence bundle."""
        if self.seed == other.seed and self.seed != 0:
            return 1.0  # Same seed = perfectly correlated
        if self.realization_id and self.realization_id == other.realization_id:
            return 0.9  # Same realization
        if self.intervention_type == other.intervention_type:
            return 0.3  # Same intervention type
        return 0.0  # Independent


# ---------------------------------------------------------------------------
# Evidence Profile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceProfile:
    """Multi-dimensional evidence assessment.

    Captures the full structure of evidence across all relevant dimensions,
    rather than reducing it to a scalar.
    """
    magnitude: float = 0.0
    consistency: float = 0.0
    replication: int = 0
    independence: float = 0.0
    intervention_diversity: int = 0
    temporal_robustness: bool = False
    generalization: bool = False
    alternative_exclusion: float = 0.0

    @property
    def is_sufficient(self) -> bool:
        """Check if evidence is sufficient for a basic claim.

        This is intentionally conservative. Strong claims require
        stronger evidence across more dimensions.
        """
        return (
            self.magnitude > 0.5
            and self.replication >= 3
            and self.independence >= 0.5
            and self.intervention_diversity >= 2
        )

    @property
    def is_strong(self) -> bool:
        """Check if evidence is strong across all dimensions."""
        return (
            self.magnitude > 0.5
            and self.consistency > 0.8
            and self.replication >= 5
            and self.independence >= 0.7
            and self.intervention_diversity >= 3
            and self.temporal_robustness
            and self.generalization
            and self.alternative_exclusion > 0.7
        )

    @property
    def effective_evidence_count(self) -> float:
        """Compute effective evidence count.

        Unlike raw replication count, this accounts for:
        - Independence (correlated replications count less)
        - Consistency (contradictory replications reduce count)
        """
        return self.replication * self.independence * self.consistency

    def to_dict(self) -> dict:
        return {
            "magnitude": self.magnitude,
            "consistency": self.consistency,
            "replication": self.replication,
            "independence": self.independence,
            "intervention_diversity": self.intervention_diversity,
            "temporal_robustness": self.temporal_robustness,
            "generalization": self.generalization,
            "alternative_exclusion": self.alternative_exclusion,
        }


# ---------------------------------------------------------------------------
# Evidence Sufficiency Assessment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceSufficiency:
    """Assessment of whether evidence satisfies a proposition's contract.

    This replaces the scalar threshold (effect > 0.5) with a structured
    assessment that explains:
    - What evidence establishes
    - What evidence does not establish
    - Why the boundary exists
    """
    proposition_id: str
    status: str  # SUPPORTED, REFUTED, INCONCLUSIVE
    profile: EvidenceProfile
    established: list[str] = field(default_factory=list)
    not_established: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    reasoning: str = ""

    @property
    def is_supported(self) -> bool:
        return self.status == "SUPPORTED"

    @property
    def is_inconclusive(self) -> bool:
        return self.status == "INCONCLUSIVE"

    def explain(self) -> str:
        """Generate human-readable explanation."""
        lines = [f"Proposition: {self.proposition_id}"]
        lines.append(f"Status: {self.status}")
        lines.append("")
        if self.established:
            lines.append("Established:")
            for e in self.established:
                lines.append(f"  ✓ {e}")
            lines.append("")
        if self.not_established:
            lines.append("Not established:")
            for e in self.not_established:
                lines.append(f"  ✗ {e}")
            lines.append("")
        if self.limitations:
            lines.append("Limitations:")
            for e in self.limitations:
                lines.append(f"  ⚠ {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evidence Accumulator
# ---------------------------------------------------------------------------


@dataclass
class EvidenceAccumulator:
    """Accumulates evidence while preserving structural provenance.

    Unlike a scalar sum, this accumulator:
    - Tracks independence between evidence items
    - Computes consistency across replications
    - Measures intervention diversity
    - Distinguishes effective evidence from raw count
    """
    bundles: list[StructuredEvidenceBundle] = field(default_factory=list)
    independence_records: list[EvidenceIndependence] = field(default_factory=list)

    def add(self, bundle: StructuredEvidenceBundle) -> None:
        """Add evidence bundle and update independence records."""
        for existing in self.bundles:
            corr = bundle.correlation_with(existing)
            self.independence_records.append(EvidenceIndependence(
                evidence_id_a=bundle.evidence_id,
                evidence_id_b=existing.evidence_id,
                correlation=corr,
                shared_seed=bundle.seed == existing.seed and bundle.seed != 0,
                shared_intervention=bundle.intervention_type == existing.intervention_type,
                shared_time_period=bundle.time_period == existing.time_period,
            ))
        self.bundles.append(bundle)

    def compute_profile(self) -> EvidenceProfile:
        """Compute the multi-dimensional evidence profile."""
        if not self.bundles:
            return EvidenceProfile()

        # Magnitude: mean effect size
        magnitude = float(np.mean([b.effect_size for b in self.bundles]))

        # Consistency: how much do effect sizes agree?
        if len(self.bundles) > 1:
            effects = [b.effect_size for b in self.bundles]
            # Consistency = 1 - normalized standard deviation
            std = np.std(effects)
            mean = np.mean(np.abs(effects))
            consistency = 1.0 - (std / (mean + 1e-8))
            consistency = float(np.clip(consistency, 0.0, 1.0))
        else:
            consistency = 1.0  # Single evidence is perfectly consistent with itself

        # Replication: raw count
        replication = len(self.bundles)

        # Independence: mean independence score
        if self.independence_records:
            independence = 1.0 - float(np.mean([
                r.correlation for r in self.independence_records
            ]))
        else:
            independence = 1.0  # Single evidence is independent by default

        # Intervention diversity: number of unique intervention types
        intervention_diversity = len(set(
            b.intervention_type for b in self.bundles
        ))

        # Temporal robustness: evidence from multiple time periods
        time_periods = set(b.time_period for b in self.bundles if b.time_period)
        temporal_robustness = len(time_periods) > 1

        # Generalization: evidence from holdout or generalization interventions
        generalization = any(
            b.intervention_type in {
                InterventionType.HOLDOUT,
                InterventionType.BOOTSTRAP,
                InterventionType.SUBSAMPLE,
            }
            for b in self.bundles
        )

        # Alternative exclusion: how well are competing mechanisms tested?
        # This is a placeholder - in practice, this would track which
        # competing mechanisms have been excluded
        alternative_exclusion = float(intervention_diversity) / max(
            len(InterventionType), 1
        )

        return EvidenceProfile(
            magnitude=magnitude,
            consistency=consistency,
            replication=replication,
            independence=independence,
            intervention_diversity=intervention_diversity,
            temporal_robustness=temporal_robustness,
            generalization=generalization,
            alternative_exclusion=alternative_exclusion,
        )

    def compute_replication_record(self) -> ReplicationRecord:
        """Compute the replication structure."""
        if not self.bundles:
            return ReplicationRecord(
                n_replications=0,
                n_seeds=0,
                n_independent=0,
                consistency_score=0.0,
                independence_score=0.0,
            )

        seeds = set(b.seed for b in self.bundles if b.seed != 0)
        n_seeds = len(seeds)

        # Count independent replications
        n_independent = 0
        for b in self.bundles:
            # Check if this bundle is independent from all others
            is_independent = True
            for other in self.bundles:
                if b.evidence_id == other.evidence_id:
                    continue
                if b.seed == other.seed and b.seed != 0:
                    is_independent = False
                    break
                if b.realization_id and b.realization_id == other.realization_id:
                    is_independent = False
                    break
            if is_independent:
                n_independent += 1

        # Consistency
        if len(self.bundles) > 1:
            effects = [b.effect_size for b in self.bundles]
            std = np.std(effects)
            mean = np.mean(np.abs(effects))
            consistency = float(np.clip(1.0 - (std / (mean + 1e-8)), 0.0, 1.0))
        else:
            consistency = 1.0

        # Independence
        if self.independence_records:
            independence = 1.0 - float(np.mean([
                r.correlation for r in self.independence_records
            ]))
        else:
            independence = 1.0

        return ReplicationRecord(
            n_replications=len(self.bundles),
            n_seeds=n_seeds,
            n_independent=n_independent,
            consistency_score=consistency,
            independence_score=independence,
            seed_ids=list(seeds),
        )


# ---------------------------------------------------------------------------
# Structured Proposition Evaluator
# ---------------------------------------------------------------------------


def evaluate_structured_proposition(
    proposition: TypedProposition,
    accumulator: EvidenceAccumulator,
) -> EvidenceSufficiency:
    """Evaluate a proposition using structured evidence.

    This replaces the scalar threshold with a structured assessment
    that explains what evidence establishes and what it does not.
    """
    profile = accumulator.compute_profile()
    replication = accumulator.compute_replication_record()

    # Determine status based on profile
    established: list[str] = []
    not_established: list[str] = []
    limitations: list[str] = []

    # Check magnitude
    if profile.magnitude > 0.5:
        established.append(f"effect magnitude ({profile.magnitude:.2f})")
    else:
        not_established.append(f"effect magnitude ({profile.magnitude:.2f})")

    # Check replication
    if profile.replication >= 3:
        established.append(f"replication ({profile.replication} trials)")
    else:
        not_established.append(f"replication ({profile.replication} trials)")

    # Check independence
    if profile.independence >= 0.5:
        established.append(f"independence ({profile.independence:.2f})")
    else:
        not_established.append(f"independence ({profile.independence:.2f})")
        limitations.append("evidence may be correlated")

    # Check intervention diversity
    if profile.intervention_diversity >= 2:
        established.append(f"intervention diversity ({profile.intervention_diversity} types)")
    else:
        not_established.append(f"intervention diversity ({profile.intervention_diversity} types)")
        limitations.append("single intervention type")

    # Check temporal robustness
    if profile.temporal_robustness:
        established.append("temporal robustness")
    else:
        not_established.append("temporal robustness")

    # Check generalization
    if profile.generalization:
        established.append("generalization")
    else:
        not_established.append("generalization")

    # Check alternative exclusion
    if profile.alternative_exclusion > 0.5:
        established.append(f"alternative exclusion ({profile.alternative_exclusion:.2f})")
    else:
        not_established.append(f"alternative exclusion ({profile.alternative_exclusion:.2f})")
        limitations.append("competing mechanisms not adequately tested")

    # Determine overall status
    # For SUPPORTED, need: magnitude, replication, independence, intervention diversity
    if (
        profile.magnitude > 0.5
        and profile.replication >= 3
        and profile.independence >= 0.5
        and profile.intervention_diversity >= 2
    ):
        status = "SUPPORTED"
    elif profile.magnitude < -0.5:
        status = "REFUTED"
    else:
        status = "INCONCLUSIVE"

    # Build reasoning
    reasoning_parts = []
    if established:
        reasoning_parts.append(
            f"Established: {', '.join(established)}."
        )
    if not_established:
        reasoning_parts.append(
            f"Not established: {', '.join(not_established)}."
        )
    if limitations:
        reasoning_parts.append(
            f"Limitations: {', '.join(limitations)}."
        )

    return EvidenceSufficiency(
        proposition_id=proposition.proposition_id,
        status=status,
        profile=profile,
        established=established,
        not_established=not_established,
        limitations=limitations,
        reasoning=" ".join(reasoning_parts),
    )


# ---------------------------------------------------------------------------
# Conversion from flat EvidenceBundle
# ---------------------------------------------------------------------------


def flat_to_structured(
    bundle: EvidenceBundle,
    seed: int = 0,
    time_period: str = "",
    realization_id: str = "",
) -> StructuredEvidenceBundle:
    """Convert a flat EvidenceBundle to a StructuredEvidenceBundle."""
    return StructuredEvidenceBundle(
        evidence_id=bundle.evidence_id,
        intervention_type=bundle.intervention_type,
        target=bundle.target,
        effect_size=bundle.effect_size,
        description=bundle.description,
        seed=seed,
        time_period=time_period,
        realization_id=realization_id,
        proposition_types_informed=bundle.proposition_types_informed,
        authority_level=bundle.authority_level,
    )
