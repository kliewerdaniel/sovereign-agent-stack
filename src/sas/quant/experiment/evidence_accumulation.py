"""Evidence Accumulation Experiment.

Tests whether evidence accumulation preserves epistemically relevant structure,
or whether the current scalar representation collapses distinct evidence
regimes into the same authority state.

The required invariant is:
    more evidence ≠ stronger evidence
    more observations ≠ more independent evidence
    larger effect ≠ greater epistemic authority

Architecture:
    Experiment A: single strong effect
    Experiment B: many independent moderate effects
    Experiment C: many dependent strong effects
    Experiment D: many contradictory effects
    Experiment E: many convergent non-discriminative effects
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


# ---------------------------------------------------------------------------
# Experiment Types
# ---------------------------------------------------------------------------


class ExperimentType(str, Enum):
    """Types of evidence accumulation experiments."""
    SINGLE_STRONG = "single_strong"
    MANY_INDEPENDENT = "many_independent"
    MANY_DEPENDENT = "many_dependent"
    MANY_CONTRADICTORY = "many_contradictory"
    MANY_CONVERGENT = "many_convergent"


@dataclass(frozen=True)
class ExperimentResult:
    """Result of a single evidence accumulation experiment."""
    experiment_type: ExperimentType
    n_evidence: int
    scalar_status: str  # From the old scalar evaluator
    structured_status: str  # From the new structured evaluator
    profile: EvidenceProfile
    replication: ReplicationRecord
    established: list[str] = field(default_factory=list)
    not_established: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Experiment Constructors
# ---------------------------------------------------------------------------


def _create_proposition() -> TypedProposition:
    """Create a standard proposition for testing."""
    return TypedProposition(
        proposition_id="p_test",
        proposition_type=PropositionType.MECHANISM_DEPENDENCY,
        target="signal_component",
        description="Signal component drives returns",
    )


def _create_single_strong() -> list[StructuredEvidenceBundle]:
    """Create a single strong piece of evidence."""
    return [
        StructuredEvidenceBundle(
            evidence_id="e1",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description="Single strong mechanism removal",
            seed=42,
            time_period="2020-2021",
            realization_id="r1",
        )
    ]


def _create_many_independent(n: int = 10) -> list[StructuredEvidenceBundle]:
    """Create many independent pieces of evidence."""
    bundles = []
    intervention_types = [
        InterventionType.MECHANISM_REMOVAL,
        InterventionType.MECHANISM_AMPLIFICATION,
        InterventionType.MECHANISM_DECORRELATION,
    ]
    for i in range(n):
        bundles.append(StructuredEvidenceBundle(
            evidence_id=f"e{i}",
            intervention_type=intervention_types[i % len(intervention_types)],
            target="signal_component",
            effect_size=0.6 + np.random.RandomState(i).normal(0, 0.05),
            description=f"Independent replication {i}",
            seed=i + 1,
            time_period=f"2020-{2021 + i}",
            realization_id=f"r{i}",
        ))
    return bundles


def _create_many_dependent(n: int = 10) -> list[StructuredEvidenceBundle]:
    """Create many dependent pieces of evidence (same seed)."""
    bundles = []
    for i in range(n):
        bundles.append(StructuredEvidenceBundle(
            evidence_id=f"e{i}",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=0.8,
            description=f"Dependent replication {i}",
            seed=42,  # Same seed = perfectly correlated
            time_period="2020-2021",
            realization_id="r1",  # Same realization
        ))
    return bundles


def _create_many_contradictory(n: int = 10) -> list[StructuredEvidenceBundle]:
    """Create many contradictory pieces of evidence."""
    bundles = []
    for i in range(n):
        effect = 0.8 if i % 2 == 0 else -0.8
        bundles.append(StructuredEvidenceBundle(
            evidence_id=f"e{i}",
            intervention_type=InterventionType.MECHANISM_REMOVAL,
            target="signal_component",
            effect_size=effect,
            description=f"Contradictory evidence {i}",
            seed=i + 1,
            time_period=f"2020-{2021 + i}",
            realization_id=f"r{i}",
        ))
    return bundles


def _create_many_convergent(n: int = 10) -> list[StructuredEvidenceBundle]:
    """Create many convergent but non-discriminative pieces of evidence."""
    bundles = []
    for i in range(n):
        bundles.append(StructuredEvidenceBundle(
            evidence_id=f"e{i}",
            intervention_type=InterventionType.FEATURE_ABLATION,  # Wrong type
            target="signal",
            effect_size=0.8,
            description=f"Convergent non-discriminative {i}",
            seed=i + 1,
            time_period=f"2020-{2021 + i}",
            realization_id=f"r{i}",
        ))
    return bundles


# ---------------------------------------------------------------------------
# Experiment Runner
# ---------------------------------------------------------------------------


def run_experiment(
    experiment_type: ExperimentType,
    n_evidence: int = 10,
) -> ExperimentResult:
    """Run a single evidence accumulation experiment."""
    proposition = _create_proposition()

    # Create evidence based on type
    if experiment_type == ExperimentType.SINGLE_STRONG:
        evidence = _create_single_strong()
    elif experiment_type == ExperimentType.MANY_INDEPENDENT:
        evidence = _create_many_independent(n_evidence)
    elif experiment_type == ExperimentType.MANY_DEPENDENT:
        evidence = _create_many_dependent(n_evidence)
    elif experiment_type == ExperimentType.MANY_CONTRADICTORY:
        evidence = _create_many_contradictory(n_evidence)
    elif experiment_type == ExperimentType.MANY_CONVERGENT:
        evidence = _create_many_convergent(n_evidence)
    else:
        raise ValueError(f"Unknown experiment type: {experiment_type}")

    # Evaluate with scalar evaluator (old)
    flat_bundles = [
        EvidenceBundle(
            evidence_id=e.evidence_id,
            intervention_type=e.intervention_type,
            target=e.target,
            effect_size=e.effect_size,
            description=e.description,
        )
        for e in evidence
    ]
    scalar_result = evaluate_typed_proposition(proposition, flat_bundles)

    # Evaluate with structured evaluator (new)
    accumulator = EvidenceAccumulator()
    for e in evidence:
        accumulator.add(e)
    structured_result = evaluate_structured_proposition(proposition, accumulator)

    return ExperimentResult(
        experiment_type=experiment_type,
        n_evidence=len(evidence),
        scalar_status=scalar_result.status,
        structured_status=structured_result.status,
        profile=structured_result.profile,
        replication=accumulator.compute_replication_record(),
        established=structured_result.established,
        not_established=structured_result.not_established,
        limitations=structured_result.limitations,
    )


# ---------------------------------------------------------------------------
# Full Experiment Suite
# ---------------------------------------------------------------------------


def run_evidence_accumulation_experiment(
    n_evidence: int = 10,
    output_dir: Optional[str] = None,
) -> list[ExperimentResult]:
    """Run the full evidence accumulation experiment suite."""
    results = []

    for exp_type in ExperimentType:
        result = run_experiment(exp_type, n_evidence=n_evidence)
        results.append(result)

    if output_dir:
        _save_results(results, output_dir)

    return results


def _save_results(
    results: list[ExperimentResult],
    output_dir: str,
) -> None:
    """Save results to disk."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    data = []
    for r in results:
        data.append({
            "experiment_type": r.experiment_type.value,
            "n_evidence": r.n_evidence,
            "scalar_status": r.scalar_status,
            "structured_status": r.structured_status,
            "profile": r.profile.to_dict(),
            "replication": {
                "n_replications": r.replication.n_replications,
                "n_seeds": r.replication.n_seeds,
                "n_independent": r.replication.n_independent,
                "consistency_score": r.replication.consistency_score,
                "independence_score": r.replication.independence_score,
            },
            "established": r.established,
            "not_established": r.not_established,
            "limitations": r.limitations,
        })

    with open(path / "evidence_accumulation_results.json", "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


def generate_experiment_report(results: list[ExperimentResult]) -> str:
    """Generate a human-readable report."""
    lines = []
    lines.append("# Evidence Accumulation Experiment Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Experiments:** {len(results)}")
    lines.append("")

    lines.append("## Results")
    lines.append("")
    lines.append("| Experiment | N | Scalar Status | Structured Status | Magnitude | Replication | Independence |")
    lines.append("|------------|---|---------------|-------------------|-----------|-------------|--------------|")

    for r in results:
        lines.append(
            f"| {r.experiment_type.value} | {r.n_evidence} | "
            f"{r.scalar_status} | {r.structured_status} | "
            f"{r.profile.magnitude:.2f} | {r.profile.replication} | "
            f"{r.profile.independence:.2f} |"
        )

    lines.append("")
    lines.append("## Key Findings")
    lines.append("")

    # Check if scalar and structured agree
    agree = sum(1 for r in results if r.scalar_status == r.structured_status)
    lines.append(f"- **Agreement:** {agree}/{len(results)} experiments")

    # Check if scalar collapses distinct regimes
    scalar_statuses = set(r.scalar_status for r in results)
    structured_statuses = set(r.structured_status for r in results)
    lines.append(f"- **Scalar unique statuses:** {len(scalar_statuses)}")
    lines.append(f"- **Structured unique statuses:** {len(structured_statuses)}")

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")

    for r in results:
        lines.append(f"### {r.experiment_type.value}")
        lines.append("")
        lines.append(f"- **N evidence:** {r.n_evidence}")
        lines.append(f"- **Scalar status:** {r.scalar_status}")
        lines.append(f"- **Structured status:** {r.structured_status}")
        lines.append(f"- **Magnitude:** {r.profile.magnitude:.2f}")
        lines.append(f"- **Replication:** {r.profile.replication}")
        lines.append(f"- **Independence:** {r.profile.independence:.2f}")
        lines.append(f"- **Intervention diversity:** {r.profile.intervention_diversity}")
        lines.append(f"- **Temporal robustness:** {r.profile.temporal_robustness}")
        lines.append(f"- **Generalization:** {r.profile.generalization}")
        lines.append("")
        if r.established:
            lines.append("**Established:**")
            for e in r.established:
                lines.append(f"  - {e}")
            lines.append("")
        if r.not_established:
            lines.append("**Not established:**")
            for e in r.not_established:
                lines.append(f"  - {e}")
            lines.append("")
        if r.limitations:
            lines.append("**Limitations:**")
            for e in r.limitations:
                lines.append(f"  - {e}")
            lines.append("")

    lines.append("## Architectural Laws")
    lines.append("")
    lines.append("> **Evidence is not scalar.**")
    lines.append("")
    lines.append("> **Evidence accumulation must preserve the structure by which evidence was obtained.**")
    lines.append("")
    lines.append("## Invariant Verification")
    lines.append("")

    # Verify: more evidence ≠ stronger evidence
    single_strong = next(r for r in results if r.experiment_type == ExperimentType.SINGLE_STRONG)
    many_dependent = next(r for r in results if r.experiment_type == ExperimentType.MANY_DEPENDENT)

    if single_strong.structured_status == many_dependent.structured_status:
        lines.append("- **more evidence = stronger evidence:** NOT VIOLATED (statuses agree)")
    else:
        lines.append("- **more evidence ≠ stronger evidence:** VIOLATED (statuses differ)")

    # Verify: more observations ≠ more independent evidence
    many_independent = next(r for r in results if r.experiment_type == ExperimentType.MANY_INDEPENDENT)
    if many_independent.profile.independence > many_dependent.profile.independence:
        lines.append("- **more observations ≠ more independent evidence:** NOT VIOLATED")
    else:
        lines.append("- **more observations ≠ more independent evidence:** VIOLATED")

    # Verify: larger effect ≠ greater epistemic authority
    if single_strong.profile.magnitude > many_independent.profile.magnitude:
        if single_strong.structured_status == many_independent.structured_status:
            lines.append("- **larger effect ≠ greater authority:** INCONCLUSIVE")
        else:
            lines.append("- **larger effect ≠ greater authority:** NOT VIOLATED")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    results = run_evidence_accumulation_experiment(
        n_evidence=10,
        output_dir="./experiments/evidence-accumulation",
    )
    report = generate_experiment_report(results)
    print(report)
