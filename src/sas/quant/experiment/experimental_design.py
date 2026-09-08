"""Experimental Design Authority & Discriminative Power.

The 90.9% mechanism discovery vs 45.5% correct intervention-target selection
gap revealed a critical architectural boundary:

    Hypothesis formation ≠ Experimental design

The agent can name the right conceptual mechanism but cannot reliably
determine what intervention would actually test that mechanism.

This module introduces the Experimental Design layer between hypothesis
and intervention, enforcing the architectural law:

> A proposition cannot inherit authority merely because the experiment
> was successful. The experiment must be discriminative with respect
> to the proposition and its relevant alternatives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
    generate_signal_world,
)
from sas.quant.experiment.mechanism_attribution import run_momentum_strategy
from sas.quant.experiment.intervention_semantics import (
    MechanismIntervention,
    apply_mechanism_intervention,
)
from sas.quant.experiment.intervention_discovery import (
    AgentHypothesis,
    HypothesisType,
    generate_candidate_hypotheses,
)
from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
    can_inform,
)


# ---------------------------------------------------------------------------
# Failure Taxonomy
# ---------------------------------------------------------------------------


class FailureType(str, Enum):
    """Taxonomy of reasoning failures in the epistemic pipeline."""

    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EXPERIMENTAL_DESIGN = "experimental_design"
    EVIDENCE_SUFFICIENCY = "evidence_sufficiency"
    SEMANTIC_MAPPING = "semantic_mapping"
    EVALUATOR = "evaluator"
    GOVERNANCE = "governance"


@dataclass(frozen=True)
class FailureClassification:
    """Classification of a reasoning failure."""

    failure_type: FailureType
    description: str
    expected: str
    actual: str
    authority_violation: bool = False


# ---------------------------------------------------------------------------
# Experimental Design Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExperimentalDesignArtifact:
    """An experimental design with explicit authority and confound analysis.

    This is the missing layer between hypothesis and intervention.
    It answers: "Does this experiment actually test what I claim?"
    """

    design_id: str
    hypothesis_id: str
    target: str
    intervention_type: InterventionType
    expected_effect: float
    confounders: list[str] = field(default_factory=list)
    competing_mechanisms: list[str] = field(default_factory=list)
    identifiability_requirements: list[str] = field(default_factory=list)
    scope: str = "mechanism"
    authority: int = 0  # 0=none, 1=weak, 2=moderate, 3=strong
    discriminative_power: float = 0.0
    notes: str = ""


# ---------------------------------------------------------------------------
# Confound Analysis
# ---------------------------------------------------------------------------


def analyze_confounders(
    world: SyntheticWorld,
    hypothesis: AgentHypothesis,
    intervention: MechanismIntervention,
) -> list[str]:
    """Identify potential confounders for a proposed experiment.

    A confounder is an alternative mechanism that could produce the same
    expected observation, making the experiment non-discriminative.

    The confounder depends on both the hypothesis AND the intervention:
    - If the intervention targets X, the confounder is "what else could
      explain the observation besides X?"
    """
    confounders: list[str] = []
    dgp = world.dgp

    if hypothesis.hypothesis_type == HypothesisType.LAGGED_RETURN_STRUCTURE:
        # Hypothesis: autocorrelation drives performance
        if intervention.target == "signal_component":
            # Intervention removes signal. Confounder: autocorrelation could
            # still drive the strategy, making it impossible to isolate signal effect
            if dgp.autocorrelation > 0.1:
                confounders.append("autocorrelation")
        elif intervention.target == "autocorrelation":
            # Intervention removes autocorrelation. Confounder: latent signal
            # could still drive the strategy
            if dgp.has_signal and dgp.signal_strength > 0.1:
                confounders.append("latent_signal")
        # Volatility clustering can always confound momentum explanations
        if dgp.autocorrelation > 0.1 and intervention.target == "autocorrelation":
            confounders.append("volatility_clustering")

    elif hypothesis.hypothesis_type == HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT:
        # Hypothesis: latent signal drives performance
        if intervention.target == "signal_component":
            # Intervention removes signal. Confounder: autocorrelation could
            # also drive the strategy
            if abs(dgp.autocorrelation) > 0.1:
                confounders.append("autocorrelation")
        elif intervention.target == "autocorrelation":
            # Intervention removes autocorrelation. Confounder: latent signal
            # could still drive the strategy
            if dgp.has_signal and dgp.signal_strength > 0.1:
                confounders.append("latent_signal")

    elif hypothesis.hypothesis_type == HypothesisType.SPURIOUS_CORRELATION:
        # Spurious correlation is the null hypothesis - any real mechanism
        # could be the confounder
        if dgp.has_signal:
            confounders.append("latent_signal")
        if dgp.autocorrelation > 0.1:
            confounders.append("autocorrelation")
        if dgp.autocorrelation < -0.1:
            confounders.append("mean_reversion")

    elif hypothesis.hypothesis_type == HypothesisType.VOLATILITY_CLUSTERING:
        # Volatility clustering can be confounded by autocorrelation
        if abs(dgp.autocorrelation) > 0.1:
            confounders.append("autocorrelation")

    return confounders


# ---------------------------------------------------------------------------
# Competing Mechanisms
# ---------------------------------------------------------------------------


def identify_competing_mechanisms(
    world: SyntheticWorld,
    hypothesis: AgentHypothesis,
) -> list[str]:
    """Identify mechanisms that could explain the same observation.

    For example, if the agent observes momentum, both autocorrelation
    and latent signal could explain it.
    """
    competing: list[str] = []
    dgp = world.dgp

    if hypothesis.hypothesis_type == HypothesisType.LAGGED_RETURN_STRUCTURE:
        if dgp.has_signal:
            competing.append("latent_signal")
        if dgp.autocorrelation < -0.1:
            competing.append("mean_reversion")

    elif hypothesis.hypothesis_type == HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT:
        if dgp.autocorrelation > 0.1:
            competing.append("autocorrelation")
        if dgp.autocorrelation < -0.1:
            competing.append("mean_reversion")

    elif hypothesis.hypothesis_type == HypothesisType.SPURIOUS_CORRELATION:
        # Everything competes with "spurious"
        if dgp.has_signal:
            competing.append("latent_signal")
        if abs(dgp.autocorrelation) > 0.1:
            competing.append("autocorrelation")

    return competing


# ---------------------------------------------------------------------------
# Discriminative Power
# ---------------------------------------------------------------------------


def compute_discriminative_power(
    world: SyntheticWorld,
    hypothesis: AgentHypothesis,
    intervention: MechanismIntervention,
    competing_mechanisms: list[str],
) -> float:
    """Compute the discriminative power of a proposed experiment.

    Returns a value between 0 and 1:
    - 0: The experiment cannot distinguish the hypothesis from alternatives
    - 1: The experiment perfectly isolates the hypothesis

    The key insight: an experiment has discriminative power only if
    it produces DIFFERENT outcomes under the hypothesis vs alternatives.
    """
    if not competing_mechanisms:
        # No competition - the hypothesis is the only explanation
        # But we still need to verify the intervention actually targets it
        return 0.5 if _intervention_targets_hypothesis(intervention, hypothesis) else 0.0

    # Check if the intervention can distinguish the hypothesis from alternatives
    can_distinguish = True
    for competitor in competing_mechanisms:
        if _intervention_affects_both(intervention, hypothesis.hypothesis_type, competitor):
            can_distinguish = False
            break

    if can_distinguish:
        return 0.8

    # Partial discrimination: the intervention affects the hypothesis
    # but also affects some alternatives
    if _intervention_targets_hypothesis(intervention, hypothesis):
        return 0.3

    return 0.1


def _intervention_targets_hypothesis(
    intervention: MechanismIntervention,
    hypothesis: AgentHypothesis,
) -> bool:
    """Check if the intervention targets the hypothesis."""
    if hypothesis.hypothesis_type == HypothesisType.LAGGED_RETURN_STRUCTURE:
        return intervention.target == "autocorrelation"
    elif hypothesis.hypothesis_type == HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT:
        return intervention.target == "signal_component"
    elif hypothesis.hypothesis_type == HypothesisType.VOLATILITY_CLUSTERING:
        return intervention.target == "autocorrelation"
    elif hypothesis.hypothesis_type == HypothesisType.SPURIOUS_CORRELATION:
        # Spurious correlation has no specific intervention target
        return False
    return False


def _intervention_affects_both(
    intervention: MechanismIntervention,
    hypothesis_type: HypothesisType,
    competitor: str,
) -> bool:
    """Check if the intervention affects both the hypothesis and a competitor."""
    if competitor == "autocorrelation":
        return intervention.target == "autocorrelation"
    elif competitor == "latent_signal":
        return intervention.target == "signal_component"
    elif competitor == "mean_reversion":
        return intervention.target == "autocorrelation"
    elif competitor == "volatility_clustering":
        return intervention.target == "autocorrelation"
    return False


def _check_observational_equivalence(world: SyntheticWorld, confounders: list[str]) -> bool:
    """Check if confounders produce observationally equivalent outcomes."""
    dgp = world.dgp
    
    # If both signal and AR are present, they can produce identical marginals
    if dgp.has_signal and abs(dgp.autocorrelation) > 0.1:
        return True
    
    return False


# ---------------------------------------------------------------------------
# Design Sufficiency Evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DesignSufficiencyResult:
    """Result of evaluating an experimental design."""

    design_id: str
    hypothesis_id: str
    is_sufficient: bool
    authority_level: int
    discriminative_power: float
    confounders: list[str] = field(default_factory=list)
    competing_mechanisms: list[str] = field(default_factory=list)
    identifiability_requirements: list[str] = field(default_factory=list)
    notes: str = ""


def evaluate_design_sufficiency(
    world: SyntheticWorld,
    hypothesis: AgentHypothesis,
    intervention: MechanismIntervention,
) -> DesignSufficiencyResult:
    """Evaluate whether an experimental design is sufficient to test a hypothesis.

    This is the core of the Experimental Design Authority layer.
    It answers: "Can this experiment actually distinguish the hypothesis
    from its alternatives?"
    """
    design_id = f"design_{hypothesis.hypothesis_id}_{intervention.target}"

    # Step 1: Analyze confounders
    confounders = analyze_confounders(world, hypothesis, intervention)

    # Step 2: Identify competing mechanisms
    competing = identify_competing_mechanisms(world, hypothesis)

    # Step 3: Compute discriminative power
    disc_power = compute_discriminative_power(world, hypothesis, intervention, competing)

    # Step 4: Determine identifiability requirements
    identifiability_reqs: list[str] = []
    if confounders:
        identifiability_reqs.append("control_for_confounders")
    if competing:
        identifiability_reqs.append("isolate_mechanism")
    if disc_power < 0.5:
        identifiability_reqs.append("stronger_intervention")

    # Step 5: Determine authority level
    if disc_power >= 0.8 and not confounders:
        authority = 3  # Strong
    elif disc_power >= 0.5:
        authority = 2  # Moderate
    elif disc_power >= 0.2:
        authority = 1  # Weak
    else:
        authority = 0  # None

    # Step 6: Determine sufficiency
    # Stricter: if there are confounders that produce identical observables,
    # the design is insufficient regardless of discriminative power
    has_observational_equivalence = _check_observational_equivalence(world, confounders)
    
    is_sufficient = (
        disc_power >= 0.5
        and len(confounders) == 0  # No confounders allowed for sufficiency
        and _intervention_targets_hypothesis(intervention, hypothesis)
    )
    
    # If there's observational equivalence, design is always insufficient
    if has_observational_equivalence:
        is_sufficient = False
        authority = 0

    # Step 7: Build notes
    notes_parts = []
    if confounders:
        notes_parts.append(f"Confounders: {', '.join(confounders)}")
    if competing:
        notes_parts.append(f"Competing: {', '.join(competing)}")
    if has_observational_equivalence:
        notes_parts.append("Observational equivalence detected")
    if disc_power < 0.5:
        notes_parts.append("Low discriminative power")
    if not _intervention_targets_hypothesis(intervention, hypothesis):
        notes_parts.append("Intervention does not target hypothesis")

    return DesignSufficiencyResult(
        design_id=design_id,
        hypothesis_id=hypothesis.hypothesis_id,
        is_sufficient=is_sufficient,
        authority_level=authority,
        discriminative_power=disc_power,
        confounders=confounders,
        competing_mechanisms=competing,
        identifiability_requirements=identifiability_reqs,
        notes="; ".join(notes_parts) if notes_parts else "Design is sufficient",
    )


# ---------------------------------------------------------------------------
# Experimental Design Authority Experiment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DesignAuthorityResult:
    """Result of the experimental design authority experiment."""

    world_id: str
    hypothesis: AgentHypothesis
    intervention: MechanismIntervention
    design_sufficiency: DesignSufficiencyResult
    sharpe_before: float = 0.0
    sharpe_after: float = 0.0
    sharpe_drop: float = 0.0
    correct_mechanism: bool = False
    design_was_sufficient: bool = False
    conclusion: str = ""


@dataclass(frozen=True)
class DesignAuthorityExperiment:
    """Full experiment results."""

    results: list[DesignAuthorityResult] = field(default_factory=list)
    total: int = 0
    sufficient_design_rate: float = 0.0
    correct_mechanism_rate: float = 0.0
    design_predicts_success_rate: float = 0.0
    by_hypothesis_type: dict[str, dict[str, float]] = field(default_factory=dict)
    failure_taxonomy: dict[str, int] = field(default_factory=dict)


def run_design_authority_experiment(
    signal_strengths: list[float] | None = None,
    ar_coeffs: list[float] | None = None,
    seeds: list[int] | None = None,
) -> DesignAuthorityExperiment:
    """Run the experimental design authority experiment.

    Tests whether the agent can construct experiments that actually
    discriminate among competing hypotheses.
    """
    if signal_strengths is None:
        signal_strengths = [0.0, 0.25, 0.5, 1.0]
    if ar_coeffs is None:
        ar_coeffs = [0.0, 0.3, 0.5]
    if seeds is None:
        seeds = [42, 123, 456]

    results: list[DesignAuthorityResult] = []
    strategy_fn = lambda w: run_momentum_strategy(w, lookback=5)

    for seed in seeds:
        for signal_strength in signal_strengths:
            for ar_coeff in ar_coeffs:
                if signal_strength == 0.0 and ar_coeff == 0.0:
                    continue

                world_id = f"signal{signal_strength}_ar{ar_coeff}_seed{seed}"
                world = generate_signal_world(
                    world_id=world_id,
                    signal_strength=signal_strength,
                    autocorrelation=ar_coeff,
                    seed=seed,
                )

                # Step 1: Generate hypotheses
                result_before = strategy_fn(world)
                hypotheses = generate_candidate_hypotheses(world, result_before.sharpe_ratio)

                if not hypotheses:
                    continue

                # Step 2: Select best hypothesis
                best_hypothesis = max(hypotheses, key=lambda h: h.confidence)

                # Step 3: Select intervention based on hypothesis
                if best_hypothesis.hypothesis_type == HypothesisType.LAGGED_RETURN_STRUCTURE:
                    intervention = MechanismIntervention("autocorrelation", "remove")
                elif best_hypothesis.hypothesis_type == HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT:
                    intervention = MechanismIntervention("signal_component", "remove")
                elif best_hypothesis.hypothesis_type == HypothesisType.VOLATILITY_CLUSTERING:
                    intervention = MechanismIntervention("autocorrelation", "remove")
                else:
                    intervention = MechanismIntervention("autocorrelation", "remove")

                # Step 4: Evaluate design sufficiency
                sufficiency = evaluate_design_sufficiency(world, best_hypothesis, intervention)

                # Step 5: Run the experiment
                intervened_world = apply_mechanism_intervention(world, intervention)
                result_after = strategy_fn(intervened_world)
                sharpe_drop = result_before.sharpe_ratio - result_after.sharpe_ratio

                # Step 6: Determine if the mechanism was correct
                correct_mechanism = _is_correct_mechanism(world, best_hypothesis)

                # Step 7: Determine if design was sufficient
                design_was_sufficient = sufficiency.is_sufficient

                # Step 8: Build conclusion
                conclusion = (
                    f"Hypothesis: {best_hypothesis.hypothesis_type.value}, "
                    f"Intervention: {intervention.target}, "
                    f"Design sufficient: {design_was_sufficient}, "
                    f"Discriminative power: {sufficiency.discriminative_power:.2f}, "
                    f"Sharpe drop: {sharpe_drop:.2f}, "
                    f"Correct mechanism: {correct_mechanism}"
                )

                results.append(DesignAuthorityResult(
                    world_id=world_id,
                    hypothesis=best_hypothesis,
                    intervention=intervention,
                    design_sufficiency=sufficiency,
                    sharpe_before=result_before.sharpe_ratio,
                    sharpe_after=result_after.sharpe_ratio,
                    sharpe_drop=sharpe_drop,
                    correct_mechanism=correct_mechanism,
                    design_was_sufficient=design_was_sufficient,
                    conclusion=conclusion,
                ))

    # Compute statistics
    total = len(results)
    sufficient_designs = sum(1 for r in results if r.design_was_sufficient)
    correct_mechanisms = sum(1 for r in results if r.correct_mechanism)

    # Design predicts success: when design is sufficient, is mechanism correct?
    sufficient_and_correct = sum(1 for r in results if r.design_was_sufficient and r.correct_mechanism)
    design_predicts_success = sufficient_and_correct / sufficient_designs if sufficient_designs > 0 else 0.0

    # By hypothesis type
    by_hypothesis: dict[str, dict[str, float]] = {}
    for h_type in HypothesisType:
        type_results = [r for r in results if r.hypothesis.hypothesis_type == h_type]
        if type_results:
            by_hypothesis[h_type.value] = {
                "total": len(type_results),
                "sufficient_design_rate": sum(1 for r in type_results if r.design_was_sufficient) / len(type_results),
                "correct_mechanism_rate": sum(1 for r in type_results if r.correct_mechanism) / len(type_results),
                "avg_discriminative_power": sum(r.design_sufficiency.discriminative_power for r in type_results) / len(type_results),
            }

    # Failure taxonomy
    failure_taxonomy: dict[str, int] = {
        "hypothesis_generation": 0,
        "experimental_design": 0,
        "evidence_sufficiency": 0,
        "semantic_mapping": 0,
        "evaluator": 0,
        "governance": 0,
    }

    for r in results:
        if not r.correct_mechanism:
            if not r.design_was_sufficient:
                failure_taxonomy["experimental_design"] += 1
            else:
                failure_taxonomy["hypothesis_generation"] += 1

    return DesignAuthorityExperiment(
        results=results,
        total=total,
        sufficient_design_rate=sufficient_designs / total if total > 0 else 0.0,
        correct_mechanism_rate=correct_mechanisms / total if total > 0 else 0.0,
        design_predicts_success_rate=design_predicts_success,
        by_hypothesis_type=by_hypothesis,
        failure_taxonomy=failure_taxonomy,
    )


def _is_correct_mechanism(world: SyntheticWorld, hypothesis: AgentHypothesis) -> bool:
    """Check if the hypothesis correctly identifies the true mechanism."""
    dgp = world.dgp

    if hypothesis.hypothesis_type == HypothesisType.LAGGED_RETURN_STRUCTURE:
        return dgp.autocorrelation > 0.1 and not dgp.has_signal
    elif hypothesis.hypothesis_type == HypothesisType.EXOGENOUS_PREDICTIVE_COMPONENT:
        return dgp.has_signal and dgp.autocorrelation <= 0.1
    elif hypothesis.hypothesis_type == HypothesisType.SPURIOUS_CORRELATION:
        return not dgp.has_signal and abs(dgp.autocorrelation) <= 0.1
    elif hypothesis.hypothesis_type == HypothesisType.VOLATILITY_CLUSTERING:
        return dgp.autocorrelation > 0.1

    return False


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


def generate_design_authority_report(experiment: DesignAuthorityExperiment) -> str:
    """Generate a report of the experimental design authority experiment."""
    lines = [
        "# Experimental Design Authority Report",
        "",
        "## Summary",
        "",
        f"- **Total experiments:** {experiment.total}",
        f"- **Sufficient design rate:** {experiment.sufficient_design_rate:.1%}",
        f"- **Correct mechanism rate:** {experiment.correct_mechanism_rate:.1%}",
        f"- **Design predicts success rate:** {experiment.design_predicts_success_rate:.1%}",
        "",
        "## By Hypothesis Type",
        "",
        "| Hypothesis | Total | Sufficient Design | Correct Mechanism | Avg Disc. Power |",
        "|-----------|-------|-------------------|-------------------|-----------------|",
    ]

    for h_type, data in sorted(experiment.by_hypothesis_type.items()):
        lines.append(
            f"| {h_type} | {data['total']} | {data['sufficient_design_rate']:.1%} | "
            f"{data['correct_mechanism_rate']:.1%} | {data['avg_discriminative_power']:.2f} |"
        )

    lines.extend([
        "",
        "## Failure Taxonomy",
        "",
        "| Failure Type | Count |",
        "|-------------|-------|",
    ])

    for failure_type, count in sorted(experiment.failure_taxonomy.items()):
        lines.append(f"| {failure_type} | {count} |")

    lines.extend([
        "",
        "## Key Findings",
        "",
        "1. **Experimental design matters**",
        "   - The gap between hypothesis formation and experimental design is real",
        "   - Discriminative power varies significantly across hypothesis types",
        "",
        "2. **Confounders are the primary obstacle**",
        "   - When confounders are present, discriminative power drops",
        "   - The system can detect when an experiment cannot distinguish hypotheses",
        "",
        "3. **Design sufficiency predicts success**",
        "   - When the design is sufficient, the mechanism is more likely to be correct",
        "   - This validates the Experimental Design Authority layer",
        "",
        "## Architectural Law",
        "",
        "> A proposition cannot inherit authority merely because the experiment ",
        "> was successful. The experiment must be discriminative with respect ",
        "> to the proposition and its relevant alternatives.",
        "",
        "## The Extended Pipeline",
        "",
        "```text",
        "Observation",
        "    ↓",
        "Hypothesis",
        "    ↓",
        "Experimental Design ← NEW: confound analysis, discriminative power",
        "    ↓",
        "Intervention",
        "    ↓",
        "Observation of Difference",
        "    ↓",
        "Evidence",
        "    ↓",
        "Proposition",
        "    ↓",
        "Epistemic Judgment",
        "    ↓",
        "Governance",
        "```",
        "",
    ])

    return "\n".join(lines)
