"""Evidence Sufficiency Characterization experiment.

Determines whether epistemic transitions exhibit stable, monotonic
relationships with evidence quality across 6 experimental dimensions.

Frozen epistemic API — DO NOT MODIFY:
- SUPPORTED / REFUTED / INCONCLUSIVE
- evaluate_hypothesis() semantics
- ObservedMechanismArtifact structure

This module only characterizes. It does not optimize.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

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


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExperimentalCondition:
    """A single experimental condition with all dimensions specified."""

    condition_id: str
    world_type: str
    sample_size: int
    signal_strength: float
    search_budget: int
    mechanism_separation: str
    intervention_strength: str
    seed: int

    @property
    def key(self) -> str:
        """Key for aggregating across seeds."""
        return (
            f"{self.world_type}|{self.sample_size}|{self.signal_strength}|"
            f"{self.search_budget}|{self.mechanism_separation}|{self.intervention_strength}"
        )


@dataclass(frozen=True)
class ConditionResult:
    """Complete result for one experimental condition."""

    condition: ExperimentalCondition
    world: SyntheticWorld
    hypothesis: HypothesisArtifact
    strategy_type: str
    strategy_lookback: int
    strategy_results: dict[str, StrategyResult]
    investigations: list[MechanismInvestigationResult]
    observed_mechanism: ObservedMechanismArtifact | None
    epistemic_evaluation: EpistemicEvaluation | None
    agent_sharpe: float = 0.0
    agent_total_return: float = 0.0
    predictability: bool = False
    epistemic_status: str = "N/A"
    governance_decision: str = "N/A"
    mechanism_identified: bool = False
    false_positive: bool = False
    false_negative: bool = False


# ---------------------------------------------------------------------------
# World Construction
# ---------------------------------------------------------------------------


def _dates_from_sample_size(n_observations: int) -> tuple[str, str]:
    """Compute start_date and end_date that produce approximately n_observations.

    Uses daily data with ~252 trading days per year.
    """
    start = "2024-01-01"
    # Add buffer for weekends/holidays (~365 calendar days per 252 trading days)
    years = max(1, (n_observations // 252) + 1)
    end_year = 2024 + years
    end = f"{end_year}-01-01"
    return start, end


def build_world_for_condition(condition: ExperimentalCondition) -> SyntheticWorld:
    """Construct a synthetic world matching the experimental condition."""
    wt = condition.world_type
    seed = condition.seed
    start, end = _dates_from_sample_size(condition.sample_size)

    if wt == "null":
        return generate_null_world(
            world_id=f"null-{condition.condition_id}",
            seed=seed,
            start_date=start,
            end_date=end,
            autocorrelation=0.05,
        )

    if wt == "known_signal":
        return generate_signal_world(
            world_id=f"ks-{condition.condition_id}",
            signal_type="momentum",
            signal_strength=condition.signal_strength,
            noise_std=0.02,
            autocorrelation=0.0,
            seed=seed,
            start_date=start,
            end_date=end,
        )

    if wt == "confounded":
        ar = 0.2 + condition.signal_strength * 0.3
        return generate_signal_world(
            world_id=f"cf-{condition.condition_id}",
            signal_type="momentum",
            signal_strength=condition.signal_strength,
            noise_std=0.02,
            autocorrelation=ar,
            seed=seed,
            start_date=start,
            end_date=end,
        )

    if wt == "wrong_mechanism":
        return generate_null_world(
            world_id=f"wm-{condition.condition_id}",
            seed=seed,
            start_date=start,
            end_date=end,
            autocorrelation=0.5 + condition.signal_strength * 0.3,
        )

    if wt == "non_identifiable":
        w = generate_signal_world(
            world_id=f"ni-{condition.condition_id}",
            signal_type="momentum",
            signal_strength=condition.signal_strength,
            noise_std=0.02,
            autocorrelation=0.4,
            seed=seed,
            start_date=start,
            end_date=end,
        )
        data = w.research_data.copy()
        data["signal"] = data["returns"].shift(1).fillna(0.0)
        return SyntheticWorld(
            world_id=w.world_id,
            symbol=w.symbol,
            research_window=w.research_window,
            holdout_window=w.holdout_window,
            research_data=data,
            holdout_data=w.holdout_data,
            dgp=w.dgp,
            seed=w.seed,
            research_signal=w.research_signal,
            holdout_signal=w.holdout_signal,
        )

    raise ValueError(f"Unknown world type: {wt}")


def build_hypothesis_for_condition(
    condition: ExperimentalCondition,
) -> HypothesisArtifact:
    """Build the declared hypothesis for the condition."""
    if condition.world_type == "null":
        return create_null_hypothesis(f"hyp-{condition.condition_id}")
    return create_signal_hypothesis(
        f"hyp-{condition.condition_id}",
        "momentum",
        condition.signal_strength,
    )


# ---------------------------------------------------------------------------
# Agent Search
# ---------------------------------------------------------------------------


def _search_strategy_configs(
    budget: int, rng: np.random.Generator
) -> list[dict[str, Any]]:
    """Generate strategy configurations for the search."""
    lookbacks = [3, 5, 10, 15, 20, 30, 50, 75, 100]
    configs = []
    for _ in range(budget):
        lb = int(rng.choice(lookbacks))
        strat_type = rng.choice(["momentum", "mean_reversion"], p=[0.7, 0.3])
        configs.append({"type": strat_type, "lookback": lb})
    return configs


def _run_mean_reversion_strategy(
    world: SyntheticWorld, lookback: int = 10
) -> StrategyResult:
    """Simple mean-reversion strategy: buy when price drops below MA."""
    data = world.research_data
    if len(data) < lookback + 2:
        return StrategyResult(
            strategy_name=f"mean_rev_{lookback}",
            world_id=world.world_id,
            sharpe_ratio=0.0,
            total_return=0.0,
            max_drawdown=0.0,
            note="Insufficient data",
        )

    ma = data["close"].rolling(lookback).mean()
    signal = (data["close"] < ma).astype(float)
    position = signal.shift(1).fillna(0.0)

    returns = data["returns"].fillna(0.0)
    strategy_returns = position * returns

    total_return = float(strategy_returns.sum())

    mean_ret = strategy_returns.mean()
    std_ret = strategy_returns.std()
    sharpe = float(mean_ret / std_ret * np.sqrt(252)) if std_ret > 1e-10 else 0.0

    return StrategyResult(
        strategy_name=f"mean_rev_{lookback}",
        world_id=world.world_id,
        sharpe_ratio=sharpe,
        total_return=total_return,
        max_drawdown=0.0,
        note="",
    )


def run_agent_search(
    world: SyntheticWorld, search_budget: int, seed: int
) -> tuple[StrategyResult, list[StrategyResult]]:
    """Run agent search over strategy configurations."""
    rng = np.random.default_rng(seed)
    configs = _search_strategy_configs(search_budget, rng)

    results = []
    for config in configs:
        if config["type"] == "mean_reversion":
            result = _run_mean_reversion_strategy(world, lookback=config["lookback"])
        else:
            result = run_momentum_strategy(world, lookback=config["lookback"])
        results.append(result)

    best = max(results, key=lambda r: r.sharpe_ratio)
    return best, results


# ---------------------------------------------------------------------------
# Investigation Adapter
# ---------------------------------------------------------------------------


def _intervention_params(strength: str) -> dict[str, Any]:
    """Map intervention strength to investigation parameters."""
    if strength == "weak":
        return {"shift_max": 2, "permutation_repeats": 5}
    if strength == "moderate":
        return {"shift_max": 5, "permutation_repeats": 10}
    if strength == "strong":
        return {"shift_max": 10, "permutation_repeats": 20}
    return {"shift_max": 5, "permutation_repeats": 10}


def run_investigations_for_condition(
    world: SyntheticWorld,
    strategy_fn: Callable[[SyntheticWorld], Any],
    mechanism_id: str,
    intervention_strength: str,
) -> list[MechanismInvestigationResult]:
    """Run all mechanism investigations with the given intervention strength."""
    params = _intervention_params(intervention_strength)
    results = []

    results.append(
        run_feature_ablation(world, strategy_fn, mechanism_id, "returns")
    )
    results.append(
        run_feature_ablation(world, strategy_fn, mechanism_id, "signal")
    )
    results.append(
        run_permutation_test(
            world,
            strategy_fn,
            mechanism_id,
            "returns",
            n_permutations=params["permutation_repeats"],
        )
    )
    results.append(
        run_competing_mechanism_test(world, strategy_fn, mechanism_id)
    )
    results.append(
        run_temporal_perturbation(
            world,
            strategy_fn,
            mechanism_id,
            "returns",
            max_shift=params["shift_max"],
        )
    )

    return results


# ---------------------------------------------------------------------------
# Observed Mechanism Builder
# ---------------------------------------------------------------------------


def build_observed_mechanism(
    world: SyntheticWorld,
    agent_result: StrategyResult | None,
    investigations: list[MechanismInvestigationResult],
) -> ObservedMechanismArtifact | None:
    """Build an ObservedMechanismArtifact from investigation results."""
    if agent_result is None:
        return None

    sharpe = agent_result.sharpe_ratio
    n_obs = len(world.research_data)

    ablation_returns: MechanismInvestigationResult | None = None
    ablation_signal: MechanismInvestigationResult | None = None
    permutation: MechanismInvestigationResult | None = None
    competing: MechanismInvestigationResult | None = None
    temporal: MechanismInvestigationResult | None = None

    for inv in investigations:
        if inv.investigation_type == "feature_ablation":
            if inv.feature_affected == "returns":
                ablation_returns = inv
            elif inv.feature_affected == "signal":
                ablation_signal = inv
        elif inv.investigation_type == "permutation":
            permutation = inv
        elif inv.investigation_type == "competing_mechanism":
            competing = inv
        elif inv.investigation_type == "temporal_perturbation":
            temporal = inv

    mechanism_type = "unknown"
    features_used: list[str] = ["close"]
    dependency_measure = 0.0
    evidence: list[str] = []

    if competing:
        if "depending on SIGNAL" in competing.conclusion:
            mechanism_type = "momentum"
            features_used = ["close", "returns", "signal"]
            dependency_measure = 0.3
        elif "depending on AUTOCORRELATION" in competing.conclusion:
            mechanism_type = "autocorrelation"
            features_used = ["close", "returns"]
            dependency_measure = 0.2
        elif "ambiguous" in competing.conclusion.lower():
            mechanism_type = "unknown"
            dependency_measure = 0.1

    if ablation_returns and ablation_returns.sharpe_drop > 0.5:
        if mechanism_type == "unknown":
            mechanism_type = "momentum"
            features_used = ["close", "returns"]
            dependency_measure = max(dependency_measure, 0.2)

    if ablation_signal and ablation_signal.sharpe_drop > 0.3:
        if mechanism_type == "unknown":
            mechanism_type = "momentum"
            if "signal" not in features_used:
                features_used.append("signal")
            dependency_measure = max(dependency_measure, 0.15)

    if sharpe < 0.2 and all(
        abs(inv.sharpe_drop) < 0.2 for inv in investigations
    ):
        mechanism_type = "none"
        dependency_measure = 0.0

    for inv in investigations:
        evidence.append(inv.conclusion)

    return ObservedMechanismArtifact(
        mechanism_id=f"mech-{world.world_id}",
        experiment_id=world.world_id,
        mechanism_type=mechanism_type,
        features_used=features_used,
        information_horizon="t+1",
        dependency_measure=dependency_measure,
        evidence=evidence,
        competing_mechanisms=["autocorrelation", "optimization_pressure"],
        confidence=0.5 if sharpe > 0.5 else 0.1,
        sharpe_ratio=sharpe,
        n_observations=n_obs,
        n_trades=0,
    )


# ---------------------------------------------------------------------------
# Single Condition Runner
# ---------------------------------------------------------------------------


def run_single_condition(condition: ExperimentalCondition) -> ConditionResult:
    """Run one experimental condition end-to-end."""
    world = build_world_for_condition(condition)
    hypothesis = build_hypothesis_for_condition(condition)

    best_result, all_results = run_agent_search(
        world, condition.search_budget, condition.seed
    )

    strategy_results = {
        "random": run_random_strategy(world),
        "buyhold": run_buy_and_hold(world),
        "oracle": run_oracle_strategy(world),
        "agent": best_result,
    }

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

    observed_mechanism = build_observed_mechanism(
        world, best_result, investigations
    )

    epistemic_evaluation = evaluate_hypothesis(hypothesis, observed_mechanism)

    epistemic_status = (
        epistemic_evaluation.status if epistemic_evaluation else "N/A"
    )
    governance_decision = "rejected"
    if epistemic_evaluation and epistemic_evaluation.status == EpistemicStatus.SUPPORTED:
        governance_decision = "accepted"

    agent_sharpe = best_result.sharpe_ratio
    agent_return = best_result.total_return
    predictability = agent_sharpe > 0.5

    false_positive = (
        epistemic_evaluation is not None
        and epistemic_evaluation.status == EpistemicStatus.SUPPORTED
        and condition.world_type in ("null", "wrong_mechanism", "non_identifiable")
    )

    false_negative = (
        epistemic_evaluation is not None
        and epistemic_evaluation.status != EpistemicStatus.SUPPORTED
        and condition.world_type == "known_signal"
        and condition.signal_strength >= 0.5
        and condition.sample_size >= 252
    )

    mechanism_identified = (
        observed_mechanism is not None
        and observed_mechanism.mechanism_type != "unknown"
        and observed_mechanism.mechanism_type != "none"
    )

    return ConditionResult(
        condition=condition,
        world=world,
        hypothesis=hypothesis,
        strategy_type=best_result.strategy_name.split("_")[0],
        strategy_lookback=best_lb,
        strategy_results=strategy_results,
        investigations=investigations,
        observed_mechanism=observed_mechanism,
        epistemic_evaluation=epistemic_evaluation,
        agent_sharpe=agent_sharpe,
        agent_total_return=agent_return,
        predictability=predictability,
        epistemic_status=epistemic_status,
        governance_decision=governance_decision,
        mechanism_identified=mechanism_identified,
        false_positive=false_positive,
        false_negative=false_negative,
    )


# ---------------------------------------------------------------------------
# Experiment Runner
# ---------------------------------------------------------------------------


def _build_conditions(
    sample_sizes: list[int],
    signal_strengths: list[float],
    search_budgets: list[int],
    mechanism_separations: list[str],
    intervention_strengths: list[str],
    seeds: list[int],
    world_types: list[str],
) -> list[ExperimentalCondition]:
    """Build all experimental conditions from the factorial design."""
    conditions = []
    counter = 0

    for wt in world_types:
        for ss in sample_sizes:
            for sig in signal_strengths:
                if wt == "null" and sig > 0.0:
                    continue
                if wt == "wrong_mechanism" and sig > 0.0:
                    continue
                if wt == "known_signal" and sig == 0.0:
                    continue

                for sb in search_budgets:
                    for ms in mechanism_separations:
                        for ist in intervention_strengths:
                            for seed in seeds:
                                conditions.append(
                                    ExperimentalCondition(
                                        condition_id=f"c{counter:04d}",
                                        world_type=wt,
                                        sample_size=ss,
                                        signal_strength=sig,
                                        search_budget=sb,
                                        mechanism_separation=ms,
                                        intervention_strength=ist,
                                        seed=seed,
                                    )
                                )
                                counter += 1

    return conditions


def run_evidence_sufficiency_experiment(
    sample_sizes: list[int] | None = None,
    signal_strengths: list[float] | None = None,
    search_budgets: list[int] | None = None,
    mechanism_separations: list[str] | None = None,
    intervention_strengths: list[str] | None = None,
    seeds: list[int] | None = None,
    world_types: list[str] | None = None,
) -> list[ConditionResult]:
    """Run the full evidence sufficiency experiment."""
    if sample_sizes is None:
        sample_sizes = [126, 252, 504]
    if signal_strengths is None:
        signal_strengths = [0.0, 0.3, 0.7]
    if search_budgets is None:
        search_budgets = [10, 50]
    if mechanism_separations is None:
        mechanism_separations = ["clear", "moderate", "indistinguishable"]
    if intervention_strengths is None:
        intervention_strengths = ["moderate", "strong"]
    if seeds is None:
        seeds = [42, 123, 456]
    if world_types is None:
        world_types = [
            "null", "known_signal", "confounded",
            "wrong_mechanism", "non_identifiable",
        ]

    conditions = _build_conditions(
        sample_sizes, signal_strengths, search_budgets,
        mechanism_separations, intervention_strengths, seeds, world_types,
    )

    results = []
    for cond in conditions:
        result = run_single_condition(cond)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Metrics Computation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AggregateMetrics:
    """Aggregate metrics computed across conditions."""

    total_conditions: int
    total_worlds: int

    supported_count: int = 0
    refuted_count: int = 0
    inconclusive_count: int = 0

    false_positive_count: int = 0
    false_negative_count: int = 0

    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    inconclusive_rate: float = 0.0
    support_rate: float = 0.0
    refutation_rate: float = 0.0

    mechanism_identification_count: int = 0
    mechanism_identification_rate: float = 0.0

    governance_acceptance_count: int = 0
    governance_acceptance_rate: float = 0.0

    predictable_count: int = 0
    predictable_rate: float = 0.0


def compute_aggregate_metrics(
    results: list[ConditionResult],
) -> AggregateMetrics:
    """Compute aggregate metrics across all conditions."""
    total = len(results)
    if total == 0:
        return AggregateMetrics(total_conditions=0, total_worlds=0)

    supported = sum(1 for r in results if r.epistemic_status == EpistemicStatus.SUPPORTED)
    refuted = sum(1 for r in results if r.epistemic_status == EpistemicStatus.REFUTED)
    inconclusive = sum(1 for r in results if r.epistemic_status == EpistemicStatus.INCONCLUSIVE)
    false_pos = sum(1 for r in results if r.false_positive)
    false_neg = sum(1 for r in results if r.false_negative)
    mech_id = sum(1 for r in results if r.mechanism_identified)
    gov_accept = sum(1 for r in results if r.governance_decision == "accepted")
    predictable = sum(1 for r in results if r.predictability)

    return AggregateMetrics(
        total_conditions=total,
        total_worlds=total,
        supported_count=supported,
        refuted_count=refuted,
        inconclusive_count=inconclusive,
        false_positive_count=false_pos,
        false_negative_count=false_neg,
        false_positive_rate=false_pos / total,
        false_negative_rate=false_neg / total,
        inconclusive_rate=inconclusive / total,
        support_rate=supported / total,
        refutation_rate=refuted / total,
        mechanism_identification_count=mech_id,
        mechanism_identification_rate=mech_id / total,
        governance_acceptance_count=gov_accept,
        governance_acceptance_rate=gov_accept / total,
        predictable_count=predictable,
        predictable_rate=predictable / total,
    )


def compute_conditional_metrics(
    results: list[ConditionResult],
    group_by: str,
) -> dict[str, AggregateMetrics]:
    """Compute metrics grouped by a condition dimension."""
    groups: dict[str, list[ConditionResult]] = defaultdict(list)
    for r in results:
        key = str(getattr(r.condition, group_by))
        groups[key].append(r)

    return {key: compute_aggregate_metrics(group) for key, group in groups.items()}


# ---------------------------------------------------------------------------
# Monotonicity Analysis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MonotonicityResult:
    """Result of a monotonicity analysis along one dimension."""

    dimension: str
    levels: list[Any]
    support_rates: list[float]
    is_monotonic_increasing: bool
    is_monotonic_decreasing: bool
    is_monotonic: bool
    notes: str


def analyze_monotonicity(
    results: list[ConditionResult],
    dimension: str,
    levels: list[Any],
) -> MonotonicityResult:
    """Analyze whether epistemic outcomes are monotonic along a dimension."""
    support_rates = []
    inconclusive_rates = []
    refutation_rates = []

    for level in levels:
        level_results = [
            r for r in results
            if getattr(r.condition, dimension) == level
        ]
        if not level_results:
            support_rates.append(0.0)
            inconclusive_rates.append(0.0)
            refutation_rates.append(0.0)
            continue

        total = len(level_results)
        supported = sum(1 for r in level_results if r.epistemic_status == EpistemicStatus.SUPPORTED)
        inconclusive = sum(1 for r in level_results if r.epistemic_status == EpistemicStatus.INCONCLUSIVE)
        refuted = sum(1 for r in level_results if r.epistemic_status == EpistemicStatus.REFUTED)

        support_rates.append(supported / total)
        inconclusive_rates.append(inconclusive / total)
        refutation_rates.append(refuted / total)

    is_inc = all(
        support_rates[i] <= support_rates[i + 1]
        for i in range(len(support_rates) - 1)
    )
    is_dec = all(
        support_rates[i] >= support_rates[i + 1]
        for i in range(len(support_rates) - 1)
    )

    notes = ""
    if is_inc:
        notes = "Support rate is monotonically increasing."
    elif is_dec:
        notes = "Support rate is monotonically decreasing."
    else:
        notes = "Support rate is NOT monotonic — transitions are not stable across levels."

    return MonotonicityResult(
        dimension=dimension,
        levels=levels,
        support_rates=support_rates,
        is_monotonic_increasing=is_inc,
        is_monotonic_decreasing=is_dec,
        is_monotonic=is_inc or is_dec,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


def generate_evidence_sufficiency_matrix(
    results: list[ConditionResult],
) -> str:
    """Generate the evidence sufficiency matrix."""
    lines = [
        "# Evidence Sufficiency Matrix",
        "",
        "Epistemic outcomes across experimental dimensions.",
        "Cells show: support% / inconclusive% / refutation% (n worlds).",
        "",
    ]

    sample_sizes = sorted({r.condition.sample_size for r in results})
    signal_strengths = sorted({r.condition.signal_strength for r in results})

    for ss in sample_sizes:
        lines.append(f"## Sample Size: {ss}")
        lines.append("")
        lines.append("| Signal Strength | Support % | Inconclusive % | Refutation % | n |")
        lines.append("|---|---|---|---|---|")

        for sig in signal_strengths:
            level_results = [
                r for r in results
                if r.condition.sample_size == ss and r.condition.signal_strength == sig
            ]
            if not level_results:
                lines.append(f"| {sig:.2f} | — | — | — | 0 |")
                continue

            total = len(level_results)
            supported = sum(1 for r in level_results if r.epistemic_status == EpistemicStatus.SUPPORTED)
            inconclusive = sum(1 for r in level_results if r.epistemic_status == EpistemicStatus.INCONCLUSIVE)
            refuted = sum(1 for r in level_results if r.epistemic_status == EpistemicStatus.REFUTED)

            lines.append(
                f"| {sig:.2f} | {supported/total:.1%} | {inconclusive/total:.1%} | "
                f"{refuted/total:.1%} | {total} |"
            )

        lines.append("")

    return chr(10).join(lines)


def generate_operating_envelope(
    results: list[ConditionResult],
) -> str:
    """Identify regions where different epistemic outcomes dominate."""
    lines = [
        "# Epistemic Operating Envelope",
        "",
        "Regions where different epistemic outcomes dominate.",
        "",
    ]

    world_types = sorted({r.condition.world_type for r in results})

    for wt in world_types:
        wt_results = [r for r in results if r.condition.world_type == wt]
        if not wt_results:
            continue

        total = len(wt_results)
        supported = sum(1 for r in wt_results if r.epistemic_status == EpistemicStatus.SUPPORTED)
        inconclusive = sum(1 for r in wt_results if r.epistemic_status == EpistemicStatus.INCONCLUSIVE)
        refuted = sum(1 for r in wt_results if r.epistemic_status == EpistemicStatus.REFUTED)
        fp = sum(1 for r in wt_results if r.false_positive)

        lines.extend([
            f"## World Type: {wt}",
            "",
            f"- Total conditions: {total}",
            f"- Support rate: {supported/total:.1%}",
            f"- Inconclusive rate: {inconclusive/total:.1%}",
            f"- Refutation rate: {refuted/total:.1%}",
            f"- False positive rate: {fp/total:.1%}",
            "",
        ])

        sample_sizes = sorted({r.condition.sample_size for r in wt_results})
        if len(sample_sizes) > 1:
            lines.append("### By Sample Size")
            lines.append("")
            lines.append("| n | Support % | Inconclusive % | Refutation % |")
            lines.append("|---|---|---|---|")
            for ss in sample_sizes:
                ss_results = [r for r in wt_results if r.condition.sample_size == ss]
                n = len(ss_results)
                s = sum(1 for r in ss_results if r.epistemic_status == EpistemicStatus.SUPPORTED)
                ic = sum(1 for r in ss_results if r.epistemic_status == EpistemicStatus.INCONCLUSIVE)
                rf = sum(1 for r in ss_results if r.epistemic_status == EpistemicStatus.REFUTED)
                lines.append(f"| {ss} | {s/n:.1%} | {ic/n:.1%} | {rf/n:.1%} |")
            lines.append("")

    return chr(10).join(lines)


def generate_monotonicity_report(
    monotonicity_results: list[MonotonicityResult],
) -> str:
    """Generate the monotonicity analysis report."""
    lines = [
        "# Monotonicity Analysis",
        "",
        "Do stronger evidence conditions produce more decisive epistemic outcomes?",
        "",
    ]

    for mr in monotonicity_results:
        lines.extend([
            f"## Dimension: {mr.dimension}",
            "",
            f"**Monotonic**: {'YES' if mr.is_monotonic else 'NO'}",
            "",
            f"**Notes**: {mr.notes}",
            "",
            "| Level | Support Rate |",
            "|---|---|",
        ])
        for level, rate in zip(mr.levels, mr.support_rates):
            lines.append(f"| {level} | {rate:.1%} |")
        lines.append("")

    return chr(10).join(lines)


def generate_failure_analysis(results: list[ConditionResult]) -> str:
    """Analyze surprising transitions and their causes."""
    lines = [
        "# Failure Analysis",
        "",
        "For every surprising transition, identify the likely cause.",
        "",
    ]

    surprising = []
    for r in results:
        if r.epistemic_status == EpistemicStatus.SUPPORTED and r.condition.world_type in (
            "null", "wrong_mechanism", "non_identifiable"
        ):
            surprising.append(("unexpected_support", r))

        if (
            r.epistemic_status != EpistemicStatus.SUPPORTED
            and r.condition.world_type == "known_signal"
            and r.condition.signal_strength >= 0.5
            and r.condition.sample_size >= 252
        ):
            surprising.append(("unexpected_non_support", r))

        if (
            r.epistemic_status == EpistemicStatus.REFUTED
            and r.condition.world_type == "known_signal"
        ):
            surprising.append(("unexpected_refutation", r))

    if not surprising:
        lines.append("No surprising transitions detected.")
        return chr(10).join(lines)

    lines.append(f"Found {len(surprising)} surprising transitions.")
    lines.append("")

    for category, r in surprising[:20]:
        lines.extend([
            f"### {category}: {r.condition.condition_id}",
            "",
            f"- World: {r.condition.world_type}",
            f"- Sample size: {r.condition.sample_size}",
            f"- Signal strength: {r.condition.signal_strength}",
            f"- Agent Sharpe: {r.agent_sharpe:.2f}",
            f"- Epistemic status: {r.epistemic_status}",
            "",
        ])

        if r.observed_mechanism:
            lines.extend([
                f"- Mechanism type: {r.observed_mechanism.mechanism_type}",
                f"- Features used: {r.observed_mechanism.features_used}",
                f"- Dependency measure: {r.observed_mechanism.dependency_measure:.2f}",
                "",
            ])

        lines.append("**Investigation evidence**:")
        for inv in r.investigations:
            lines.append(f"- {inv.conclusion}")
        lines.append("")

    return chr(10).join(lines)


def generate_evidence_sufficiency_report(
    results: list[ConditionResult],
    monotonicity: list[MonotonicityResult] | None = None,
) -> str:
    """Generate the full evidence sufficiency report."""
    metrics = compute_aggregate_metrics(results)

    sections = [
        "# Evidence Sufficiency Characterization Report",
        "",
        "## Aggregate Metrics",
        "",
        f"- Total conditions: {metrics.total_conditions}",
        f"- Support rate: {metrics.support_rate:.1%} ({metrics.supported_count})",
        f"- Inconclusive rate: {metrics.inconclusive_rate:.1%} ({metrics.inconclusive_count})",
        f"- Refutation rate: {metrics.refutation_rate:.1%} ({metrics.refuted_count})",
        f"- False positive rate: {metrics.false_positive_rate:.1%} ({metrics.false_positive_count})",
        f"- False negative rate: {metrics.false_negative_rate:.1%} ({metrics.false_negative_count})",
        f"- Mechanism identification rate: {metrics.mechanism_identification_rate:.1%}",
        f"- Governance acceptance rate: {metrics.governance_acceptance_rate:.1%}",
        "",
        "---",
        "",
        generate_evidence_sufficiency_matrix(results),
        "",
        "---",
        "",
        generate_operating_envelope(results),
    ]

    if monotonicity:
        sections.extend([
            "",
            "---",
            "",
            generate_monotonicity_report(monotonicity),
        ])

    sections.extend([
        "",
        "---",
        "",
        generate_failure_analysis(results),
    ])

    return chr(10).join(sections)
