"""Proposition Evidence Matrix — evaluate evidence at the proposition level.

Compares two paths:

PATH A (current): evidence → mechanism_type → frozen evaluator
PATH B (new): evidence → proposition bundle → proposition evaluation

The key insight: the evidence may be sufficient to support a proposition
even when the intermediate mechanism classification is too lossy to
produce a categorical match.

Frozen epistemic API — DO NOT MODIFY:
- SUPPORTED / REFUTED / INCONCLUSIVE
- evaluate_hypothesis() semantics
- ObservedMechanismArtifact structure
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from sas.quant.experiment.synthetic_worlds import (
    SyntheticWorld,
    generate_signal_world,
    generate_null_world,
)
from sas.quant.experiment.mechanism_attribution import (
    StrategyResult,
    run_momentum_strategy,
    run_buy_and_hold,
    run_random_strategy,
    run_oracle_strategy,
)
from sas.quant.experiment.mechanism_investigation import (
    MechanismInvestigationResult,
    run_feature_ablation,
    run_permutation_test,
    run_competing_mechanism_test,
    run_temporal_perturbation,
)
from sas.quant.experiment.epistemic import (
    EpistemicStatus,
    EpistemicEvaluation,
    ObservedMechanismArtifact,
    evaluate_hypothesis,
)
from sas.quant.experiment.hypothesis import (
    HypothesisArtifact,
    create_signal_hypothesis,
    create_null_hypothesis,
)
from sas.quant.experiment.evidence_sufficiency import (
    ExperimentalCondition,
    ConditionResult,
    build_world_for_condition,
    build_hypothesis_for_condition,
    run_agent_search,
    run_investigations_for_condition,
    build_observed_mechanism,
    _run_mean_reversion_strategy,
    _intervention_params,
)


# ---------------------------------------------------------------------------
# Proposition Representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PropositionEvidence:
    """Evidence relevant to a specific proposition.

    Unlike ObservedMechanismArtifact which collapses evidence into a
    single categorical mechanism_type, PropositionEvidence preserves
    the full evidentiary structure.

    Attributes:
        proposition_id: The proposition being evaluated.
        proposition_text: Human-readable statement.
        feature_ablation_evidence: Evidence from removing features.
        permutation_evidence: Evidence from shuffling temporal structure.
        temporal_evidence: Evidence from shifting timing.
        competing_mechanism_evidence: Evidence from comparing mechanisms.
        replication_evidence: Evidence from multiple seeds.
        holdout_evidence: Evidence from out-of-sample testing.
    """

    proposition_id: str
    proposition_text: str
    feature_ablation_evidence: list[MechanismInvestigationResult] = field(default_factory=list)
    permutation_evidence: list[MechanismInvestigationResult] = field(default_factory=list)
    temporal_evidence: list[MechanismInvestigationResult] = field(default_factory=list)
    competing_mechanism_evidence: list[MechanismInvestigationResult] = field(default_factory=list)
    replication_evidence: list[float] = field(default_factory=list)
    holdout_evidence: Optional[float] = None


@dataclass(frozen=True)
class PropositionEvaluation:
    """Evaluation of a proposition based on evidence.

    Attributes:
        proposition_id: The proposition being evaluated.
        status: SUPPORTED, REFUTED, or INCONCLUSIVE.
        confidence: 0-1, how strongly the evidence supports the status.
        reasoning: Human-readable reasoning.
        evidence_summary: Summary of the evidence considered.
    """

    proposition_id: str
    status: str
    confidence: float
    reasoning: str
    evidence_summary: str


# ---------------------------------------------------------------------------
# Proposition Evaluator
# ---------------------------------------------------------------------------


def evaluate_proposition(
    proposition: PropositionEvidence,
    hypothesis: HypothesisArtifact,
) -> PropositionEvaluation:
    """Evaluate whether the evidence supports the proposition.

    This is a PROPOSITION-LEVEL evaluation. It does NOT require
    intermediate mechanism classification.

    The proposition is evaluated directly from the evidence bundle:
    - Feature ablation: does removing the claimed feature collapse performance?
    - Permutation: does destroying temporal structure collapse performance?
    - Temporal perturbation: does misaligning timing collapse performance?
    - Competing mechanisms: do alternative features reproduce the result?
    - Replication: does the effect persist across seeds?
    - Holdout: does the effect persist out of sample?

    Args:
        proposition: The proposition evidence bundle.
        hypothesis: The declared hypothesis.

    Returns:
        PropositionEvaluation with status and reasoning.
    """
    # --- Signal hypothesis evaluation ---
    if hypothesis.target_signal and hypothesis.target_signal != "none":
        return _evaluate_signal_proposition(proposition, hypothesis)

    # --- Null hypothesis evaluation ---
    return _evaluate_null_proposition(proposition, hypothesis)


def _evaluate_signal_proposition(
    proposition: PropositionEvidence,
    hypothesis: HypothesisArtifact,
) -> PropositionEvaluation:
    """Evaluate a signal hypothesis from proposition-level evidence."""

    evidence_pieces = []
    support_indicators = 0
    refutation_indicators = 0
    total_indicators = 0

    # 1. Feature ablation evidence
    signal_ablation_effect = 0.0
    returns_ablation_effect = 0.0
    for ablation in proposition.feature_ablation_evidence:
        if ablation.feature_affected == "signal":
            signal_ablation_effect = ablation.sharpe_drop
        elif ablation.feature_affected == "returns":
            returns_ablation_effect = ablation.sharpe_drop

    total_indicators += 1
    if signal_ablation_effect > 0.3:
        support_indicators += 1
        evidence_pieces.append(
            f"Signal ablation changed Sharpe by {signal_ablation_effect:.2f}"
        )
    elif signal_ablation_effect < 0.1:
        refutation_indicators += 1
        evidence_pieces.append(
            f"Signal ablation had minimal effect ({signal_ablation_effect:.2f})"
        )
    else:
        evidence_pieces.append(
            f"Signal ablation had moderate effect ({signal_ablation_effect:.2f})"
        )

    # 2. Permutation evidence
    for perm in proposition.permutation_evidence:
        total_indicators += 1
        if perm.sharpe_drop > 0.3:
            support_indicators += 1
            evidence_pieces.append(
                f"Permutation test: Sharpe changed by {perm.sharpe_drop:.2f}"
            )
        elif perm.sharpe_drop < 0.1:
            refutation_indicators += 1
            evidence_pieces.append(
                f"Permutation test: Sharpe unchanged ({perm.sharpe_drop:.2f})"
            )

    # 3. Temporal perturbation evidence
    for temp in proposition.temporal_evidence:
        total_indicators += 1
        if temp.sharpe_drop > 0.3:
            support_indicators += 1
            evidence_pieces.append(
                f"Temporal perturbation: Sharpe changed by {temp.sharpe_drop:.2f}"
            )
        elif temp.sharpe_drop < 0.1:
            refutation_indicators += 1
            evidence_pieces.append(
                f"Temporal perturbation: Sharpe unchanged ({temp.sharpe_drop:.2f})"
            )

    # 4. Competing mechanism evidence
    for comp in proposition.competing_mechanism_evidence:
        total_indicators += 1
        if "depending on SIGNAL" in comp.conclusion:
            support_indicators += 1
            evidence_pieces.append("Competing mechanism: signal is the driver")
        elif "depending on AUTOCORRELATION" in comp.conclusion:
            refutation_indicators += 1
            evidence_pieces.append("Competing mechanism: autocorrelation is the driver")
        elif "ambiguous" in comp.conclusion.lower():
            evidence_pieces.append("Competing mechanism: ambiguous")

    # 5. Replication evidence
    if proposition.replication_evidence:
        total_indicators += 1
        replication_rate = sum(1 for r in proposition.replication_evidence if r > 0.3) / len(proposition.replication_evidence)
        if replication_rate > 0.7:
            support_indicators += 1
            evidence_pieces.append(f"Replication: {replication_rate:.0%} of seeds show effect")
        elif replication_rate < 0.3:
            refutation_indicators += 1
            evidence_pieces.append(f"Replication: only {replication_rate:.0%} of seeds show effect")
        else:
            evidence_pieces.append(f"Replication: {replication_rate:.0%} of seeds show effect")

    # 6. Holdout evidence
    if proposition.holdout_evidence is not None:
        total_indicators += 1
        if proposition.holdout_evidence > 0.3:
            support_indicators += 1
            evidence_pieces.append(f"Holdout: effect persists ({proposition.holdout_evidence:.2f})")
        else:
            refutation_indicators += 1
            evidence_pieces.append(f"Holdout: effect does not persist ({proposition.holdout_evidence:.2f})")

    # --- Determine status ---
    if total_indicators == 0:
        return PropositionEvaluation(
            proposition_id=proposition.proposition_id,
            status=EpistemicStatus.INCONCLUSIVE,
            confidence=0.0,
            reasoning="No evidence available for evaluation",
            evidence_summary="",
        )

    support_ratio = support_indicators / total_indicators
    refutation_ratio = refutation_indicators / total_indicators

    # Strong support: multiple independent lines of evidence
    if support_ratio >= 0.6 and support_indicators >= 3:
        status = EpistemicStatus.SUPPORTED
        confidence = min(support_ratio, 0.95)
        reasoning = (
            f"Multiple independent lines of evidence ({support_indicators}/{total_indicators}) "
            f"support the proposition that {proposition.proposition_text}"
        )
    # Strong refutation: evidence contradicts the proposition
    elif refutation_ratio >= 0.6 and refutation_indicators >= 2:
        status = EpistemicStatus.REFUTED
        confidence = min(refutation_ratio, 0.95)
        reasoning = (
            f"Multiple lines of evidence ({refutation_indicators}/{total_indicators}) "
            f"contradict the proposition that {proposition.proposition_text}"
        )
    else:
        status = EpistemicStatus.INCONCLUSIVE
        confidence = 0.5
        reasoning = (
            f"Evidence is mixed: {support_indicators} support, {refutation_indicators} refute, "
            f"out of {total_indicators} indicators"
        )

    evidence_summary = "; ".join(evidence_pieces)

    return PropositionEvaluation(
        proposition_id=proposition.proposition_id,
        status=status,
        confidence=confidence,
        reasoning=reasoning,
        evidence_summary=evidence_summary,
    )


def _evaluate_null_proposition(
    proposition: PropositionEvidence,
    hypothesis: HypothesisArtifact,
) -> PropositionEvaluation:
    """Evaluate a null hypothesis from proposition-level evidence.

    The null hypothesis is supported when:
    - No feature ablation shows significant effect
    - Permutation/temporal perturbation show minimal effect
    - No competing mechanism is identified
    """

    evidence_pieces = []
    support_indicators = 0
    total_indicators = 0

    # 1. Feature ablation evidence
    for ablation in proposition.feature_ablation_evidence:
        total_indicators += 1
        if ablation.sharpe_drop < 0.2:
            support_indicators += 1
            evidence_pieces.append(
                f"{ablation.feature_affected} ablation: minimal effect ({ablation.sharpe_drop:.2f})"
            )
        else:
            evidence_pieces.append(
                f"{ablation.feature_affected} ablation: significant effect ({ablation.sharpe_drop:.2f})"
            )

    # 2. Permutation evidence
    for perm in proposition.permutation_evidence:
        total_indicators += 1
        if perm.sharpe_drop < 0.2:
            support_indicators += 1
            evidence_pieces.append(f"Permutation: minimal effect ({perm.sharpe_drop:.2f})")
        else:
            evidence_pieces.append(f"Permutation: significant effect ({perm.sharpe_drop:.2f})")

    # 3. Temporal evidence
    for temp in proposition.temporal_evidence:
        total_indicators += 1
        if temp.sharpe_drop < 0.2:
            support_indicators += 1
            evidence_pieces.append(f"Temporal: minimal effect ({temp.sharpe_drop:.2f})")
        else:
            evidence_pieces.append(f"Temporal: significant effect ({temp.sharpe_drop:.2f})")

    # 4. Competing mechanism evidence
    for comp in proposition.competing_mechanism_evidence:
        total_indicators += 1
        if "ambiguous" in comp.conclusion.lower():
            support_indicators += 1
            evidence_pieces.append("Competing mechanism: ambiguous (no clear driver)")
        elif "depending on" in comp.conclusion.lower():
            evidence_pieces.append(f"Competing mechanism: {comp.conclusion}")

    if total_indicators == 0:
        return PropositionEvaluation(
            proposition_id=proposition.proposition_id,
            status=EpistemicStatus.INCONCLUSIVE,
            confidence=0.0,
            reasoning="No evidence available for evaluation",
            evidence_summary="",
        )

    support_ratio = support_indicators / total_indicators

    if support_ratio >= 0.7:
        status = EpistemicStatus.SUPPORTED
        confidence = min(support_ratio, 0.95)
        reasoning = (
            f"Evidence supports null hypothesis: {support_indicators}/{total_indicators} "
            f"indicators show no significant effect"
        )
    elif support_ratio < 0.3:
        status = EpistemicStatus.REFUTED
        confidence = 1.0 - support_ratio
        reasoning = (
            f"Evidence contradicts null hypothesis: only {support_indicators}/{total_indicators} "
            f"indicators show no effect"
        )
    else:
        status = EpistemicStatus.INCONCLUSIVE
        confidence = 0.5
        reasoning = (
            f"Evidence is mixed on null hypothesis: {support_indicators}/{total_indicators} "
            f"indicators show no effect"
        )

    evidence_summary = "; ".join(evidence_pieces)

    return PropositionEvaluation(
        proposition_id=proposition.proposition_id,
        status=status,
        confidence=confidence,
        reasoning=reasoning,
        evidence_summary=evidence_summary,
    )


# ---------------------------------------------------------------------------
# Proposition Evidence Builder
# ---------------------------------------------------------------------------


def build_proposition_evidence(
    world: SyntheticWorld,
    investigations: list[MechanismInvestigationResult],
    agent_result: StrategyResult,
    replication_results: list[float] | None = None,
    holdout_result: float | None = None,
) -> PropositionEvidence:
    """Build a PropositionEvidence bundle from investigation results.

    This preserves the full evidentiary structure without collapsing
    into a categorical mechanism_type.
    """
    feature_ablation = []
    permutation = []
    temporal = []
    competing = []

    for inv in investigations:
        if inv.investigation_type == "feature_ablation":
            feature_ablation.append(inv)
        elif inv.investigation_type == "permutation":
            permutation.append(inv)
        elif inv.investigation_type == "temporal_perturbation":
            temporal.append(inv)
        elif inv.investigation_type == "competing_mechanism":
            competing.append(inv)

    return PropositionEvidence(
        proposition_id=f"prop-{world.world_id}",
        proposition_text="SIGNAL predicts future returns",
        feature_ablation_evidence=feature_ablation,
        permutation_evidence=permutation,
        temporal_evidence=temporal,
        competing_mechanism_evidence=competing,
        replication_evidence=replication_results or [],
        holdout_evidence=holdout_result,
    )


# ---------------------------------------------------------------------------
# Dual-Path Comparison
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DualPathResult:
    """Result of comparing Path A (mechanism) vs Path B (proposition)."""

    condition: ExperimentalCondition
    world: SyntheticWorld
    hypothesis: HypothesisArtifact
    agent_result: StrategyResult
    investigations: list[MechanismInvestigationResult]

    # Path A: mechanism → frozen evaluator
    observed_mechanism: ObservedMechanismArtifact | None
    path_a_evaluation: EpistemicEvaluation | None

    # Path B: proposition → proposition evaluation
    proposition_evidence: PropositionEvidence
    path_b_evaluation: PropositionEvaluation

    # Comparison
    path_a_status: str = "N/A"
    path_b_status: str = "N/A"
    paths_agree: bool = False
    path_b_more_informative: bool = False


def run_dual_path_comparison(
    condition: ExperimentalCondition,
    replication_worlds: list[SyntheticWorld] | None = None,
) -> DualPathResult:
    """Run both paths for a single condition and compare.

    Args:
        condition: The experimental condition.
        replication_worlds: Additional worlds for replication evidence.

    Returns:
        DualPathResult with both evaluations.
    """
    world = build_world_for_condition(condition)
    hypothesis = build_hypothesis_for_condition(condition)

    # Agent search
    best_result, all_results = run_agent_search(
        world, condition.search_budget, condition.seed
    )

    # Investigations
    mechanism_id = f"mech-{world.world_id}"
    best_lb = 5
    if "_" in best_result.strategy_name:
        parts = best_result.strategy_name.split("_")
        for p in parts:
            if p.isdigit():
                best_lb = int(p)
                break
    if best_result.strategy_name.startswith("momentum"):
        strategy_fn = lambda w: run_momentum_strategy(w, lookback=best_lb)
    else:
        strategy_fn = lambda w: _run_mean_reversion_strategy(w, lookback=best_lb)

    investigations = run_investigations_for_condition(
        world, strategy_fn, mechanism_id, condition.intervention_strength
    )

    # --- Path A: mechanism → frozen evaluator ---
    observed_mechanism = build_observed_mechanism(
        world, best_result, investigations
    )
    path_a_evaluation = None
    if observed_mechanism is not None:
        path_a_evaluation = evaluate_hypothesis(hypothesis, observed_mechanism)
    path_a_status = path_a_evaluation.status if path_a_evaluation else "N/A"

    # --- Path B: proposition → proposition evaluation ---
    # Collect replication evidence
    replication_results = []
    if replication_worlds:
        for rep_world in replication_worlds:
            rep_result = strategy_fn(rep_world)
            # Measure signal ablation effect on replication world
            rep_ablation = run_feature_ablation(
                rep_world, strategy_fn, f"mech-{rep_world.world_id}", "signal"
            )
            replication_results.append(rep_ablation.sharpe_drop)

    # Build proposition evidence
    proposition_evidence = build_proposition_evidence(
        world, investigations, best_result,
        replication_results=replication_results,
    )

    # Evaluate proposition
    path_b_evaluation = evaluate_proposition(proposition_evidence, hypothesis)
    path_b_status = path_b_evaluation.status

    # --- Compare ---
    paths_agree = path_a_status == path_b_status
    path_b_more_informative = (
        path_b_status != EpistemicStatus.INCONCLUSIVE
        and path_a_status == EpistemicStatus.INCONCLUSIVE
    )

    return DualPathResult(
        condition=condition,
        world=world,
        hypothesis=hypothesis,
        agent_result=best_result,
        investigations=investigations,
        observed_mechanism=observed_mechanism,
        path_a_evaluation=path_a_evaluation,
        proposition_evidence=proposition_evidence,
        path_b_evaluation=path_b_evaluation,
        path_a_status=path_a_status,
        path_b_status=path_b_status,
        paths_agree=paths_agree,
        path_b_more_informative=path_b_more_informative,
    )


# ---------------------------------------------------------------------------
# Experiment Runner
# ---------------------------------------------------------------------------


def run_proposition_evidence_experiment(
    sample_sizes: list[int] | None = None,
    signal_strengths: list[float] | None = None,
    search_budgets: list[int] | None = None,
    mechanism_separations: list[str] | None = None,
    intervention_strengths: list[str] | None = None,
    seeds: list[int] | None = None,
    world_types: list[str] | None = None,
    n_replications: int = 2,
) -> list[DualPathResult]:
    """Run the full proposition evidence experiment.

    For each condition, runs both Path A (mechanism) and Path B (proposition)
    and compares the results.

    Args:
        sample_sizes: List of sample sizes.
        signal_strengths: List of signal strengths.
        search_budgets: List of search budgets.
        mechanism_separations: List of mechanism separation levels.
        intervention_strengths: List of intervention strength levels.
        seeds: List of random seeds.
        world_types: List of world types.
        n_replications: Number of replication worlds per condition.

    Returns:
        List of DualPathResult.
    """
    if sample_sizes is None:
        sample_sizes = [126, 252, 504]
    if signal_strengths is None:
        signal_strengths = [0.0, 0.3, 0.7]
    if search_budgets is None:
        search_budgets = [10, 50]
    if mechanism_separations is None:
        mechanism_separations = ["clear", "moderate", "indistinguishable"]
    if intervention_strengths is None:
        intervention_strengths = ["weak", "strong"]
    if seeds is None:
        seeds = [42, 123, 456]
    if world_types is None:
        world_types = [
            "null", "known_signal", "confounded",
            "wrong_mechanism", "non_identifiable",
        ]

    # Build conditions
    from sas.quant.experiment.evidence_sufficiency import _build_conditions
    conditions = _build_conditions(
        sample_sizes, signal_strengths, search_budgets,
        mechanism_separations, intervention_strengths, seeds, world_types,
    )

    results = []
    for cond in conditions:
        # Build replication worlds
        replication_worlds = []
        for i in range(n_replications):
            rep_cond = ExperimentalCondition(
                condition_id=f"{cond.condition_id}-rep{i}",
                world_type=cond.world_type,
                sample_size=cond.sample_size,
                signal_strength=cond.signal_strength,
                search_budget=cond.search_budget,
                mechanism_separation=cond.mechanism_separation,
                intervention_strength=cond.intervention_strength,
                seed=cond.seed + 1000 + i,
            )
            rep_world = build_world_for_condition(rep_cond)
            replication_worlds.append(rep_world)

        result = run_dual_path_comparison(cond, replication_worlds)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyze_dual_path_results(
    results: list[DualPathResult],
) -> dict[str, Any]:
    """Analyze the dual-path comparison results."""
    total = len(results)
    if total == 0:
        return {"total": 0}

    # Count agreements and disagreements
    agreements = sum(1 for r in results if r.paths_agree)
    path_b_more_informative = sum(1 for r in results if r.path_b_more_informative)

    # Status distributions
    path_a_statuses = defaultdict(int)
    path_b_statuses = defaultdict(int)
    for r in results:
        path_a_statuses[r.path_a_status] += 1
        path_b_statuses[r.path_b_status] += 1

    # By world type
    by_type = defaultdict(lambda: {"total": 0, "agree": 0, "b_better": 0})
    for r in results:
        wt = r.condition.world_type
        by_type[wt]["total"] += 1
        if r.paths_agree:
            by_type[wt]["agree"] += 1
        if r.path_b_more_informative:
            by_type[wt]["b_better"] += 1

    # By signal strength
    by_signal = defaultdict(lambda: {"total": 0, "agree": 0, "b_better": 0})
    for r in results:
        sig = r.condition.signal_strength
        by_signal[sig]["total"] += 1
        if r.paths_agree:
            by_signal[sig]["agree"] += 1
        if r.path_b_more_informative:
            by_signal[sig]["b_better"] += 1

    # By sample size
    by_sample = defaultdict(lambda: {"total": 0, "agree": 0, "b_better": 0})
    for r in results:
        ss = r.condition.sample_size
        by_sample[ss]["total"] += 1
        if r.paths_agree:
            by_sample[ss]["agree"] += 1
        if r.path_b_more_informative:
            by_sample[ss]["b_better"] += 1

    return {
        "total": total,
        "agreements": agreements,
        "agreement_rate": agreements / total,
        "path_b_more_informative": path_b_more_informative,
        "path_b_informative_rate": path_b_more_informative / total,
        "path_a_statuses": dict(path_a_statuses),
        "path_b_statuses": dict(path_b_statuses),
        "by_world_type": {k: dict(v) for k, v in by_type.items()},
        "by_signal_strength": {k: dict(v) for k, v in by_signal.items()},
        "by_sample_size": {k: dict(v) for k, v in by_sample.items()},
    }


def generate_proposition_evidence_report(
    results: list[DualPathResult],
) -> str:
    """Generate the proposition evidence report."""
    analysis = analyze_dual_path_results(results)

    lines = [
        "# Proposition Evidence Matrix Report",
        "",
        "## Summary",
        "",
        f"- Total conditions: {analysis['total']}",
        f"- Path A (mechanism) and Path B (proposition) agree: {analysis['agreement_rate']:.1%}",
        f"- Path B more informative than Path A: {analysis['path_b_informative_rate']:.1%}",
        "",
        "### Path A Status Distribution (Mechanism → Frozen Evaluator)",
        "",
    ]

    for status, count in sorted(analysis['path_a_statuses'].items()):
        lines.append(f"- {status}: {count} ({count/analysis['total']:.1%})")

    lines.extend([
        "",
        "### Path B Status Distribution (Proposition → Proposition Evaluation)",
        "",
    ])

    for status, count in sorted(analysis['path_b_statuses'].items()):
        lines.append(f"- {status}: {count} ({count/analysis['total']:.1%})")

    lines.extend([
        "",
        "---",
        "",
        "## Analysis by World Type",
        "",
        "| World Type | Total | Agreement | B More Informative |",
        "|---|---|---|---|",
    ])

    for wt, data in sorted(analysis['by_world_type'].items()):
        agree_rate = data['agree'] / data['total'] if data['total'] > 0 else 0
        b_rate = data['b_better'] / data['total'] if data['total'] > 0 else 0
        lines.append(
            f"| {wt} | {data['total']} | {agree_rate:.1%} | {b_rate:.1%} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Analysis by Signal Strength",
        "",
        "| Signal Strength | Total | Agreement | B More Informative |",
        "|---|---|---|---|",
    ])

    for sig, data in sorted(analysis['by_signal_strength'].items()):
        agree_rate = data['agree'] / data['total'] if data['total'] > 0 else 0
        b_rate = data['b_better'] / data['total'] if data['total'] > 0 else 0
        lines.append(
            f"| {sig:.2f} | {data['total']} | {agree_rate:.1%} | {b_rate:.1%} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Analysis by Sample Size",
        "",
        "| Sample Size | Total | Agreement | B More Informative |",
        "|---|---|---|---|",
    ])

    for ss, data in sorted(analysis['by_sample_size'].items()):
        agree_rate = data['agree'] / data['total'] if data['total'] > 0 else 0
        b_rate = data['b_better'] / data['total'] if data['total'] > 0 else 0
        lines.append(
            f"| {ss} | {data['total']} | {agree_rate:.1%} | {b_rate:.1%} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Architectural Finding",
        "",
        "### The Semantic Impedance Mismatch",
        "",
        "The experiment compares two paths:",
        "",
        "**Path A**: Evidence → ObservedMechanismArtifact → Frozen Evaluator",
        "**Path B**: Evidence → Proposition Evidence Bundle → Proposition Evaluation",
        "",
        "If Path B produces more decisive outcomes (SUPPORTED/REFUTED) than Path A,",
        "this indicates that the mechanism classification step is **lossy** —",
        "information in the evidence is being discarded before it reaches the evaluator.",
        "",
        "### Interpretation",
        "",
    ])

    b_informative = analysis['path_b_informative_rate']
    if b_informative > 0.3:
        lines.append(
            f"Path B is more informative in {b_informative:.1%} of conditions. "
            "This strongly suggests that the mechanism classification step is "
            "discarding evidence that is relevant to the proposition."
        )
    elif b_informative > 0.1:
        lines.append(
            f"Path B is more informative in {b_informative:.1%} of conditions. "
            "This suggests a moderate semantic impedance mismatch between "
            "the evidence and the mechanism ontology."
        )
    else:
        lines.append(
            f"Path B is more informative in only {b_informative:.1%} of conditions. "
            "This suggests that the mechanism classification is NOT the primary bottleneck — "
            "the evidence itself may be insufficient."
        )

    lines.extend([
        "",
        "### Recommendation",
        "",
        "1. If Path B >> Path A: enrich the evidence representation or "
        "bypass the mechanism classification step",
        "2. If Path B ≈ Path A: the evidence itself is insufficient — "
        "investigate richer investigation types",
        "3. If Path B is worse: the mechanism classification is actually "
        "filtering noise — preserve it",
        "",
    ])

    return chr(10).join(lines)
