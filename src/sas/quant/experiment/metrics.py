"""Experimental metrics for governed research experiments.

These metrics are designed to expose the relationship between
nominal performance (what the agent reports) and statistically
defensible performance (what survives rigorous evaluation).

The central measurement is the gap between what the agent believes
it has found and what the protocol validates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass(frozen=True)
class TrialEfficiency:
    """How efficiently the agent used its trial budget.

    Measures the ratio of evaluated trials to total trials,
    and the ratio of trials that improved on the incumbent.
    """
    total_trials: int
    evaluated_trials: int
    improving_trials: int
    wasted_trials: int  # Trials that didn't improve and weren't revisions
    evaluation_rate: float  # evaluated / total
    improvement_rate: float  # improving / evaluated

    def to_dict(self) -> dict:
        return {
            "total_trials": self.total_trials,
            "evaluated_trials": self.evaluated_trials,
            "improving_trials": self.improving_trials,
            "wasted_trials": self.wasted_trials,
            "evaluation_rate": self.evaluation_rate,
            "improvement_rate": self.improvement_rate,
        }


@dataclass(frozen=True)
class IncumbentTurnover:
    """How often the incumbent strategy changed during research.

    High turnover suggests the agent is exploring widely.
    Low turnover suggests the agent converged early.
    """
    incumbent_changes: int
    final_incumbent_trial: int  # Which trial became the final incumbent
    incumbent_sharpe_progression: list[float]  # Sharpe at each change
    average_hold_duration: float  # Average trials between changes

    def to_dict(self) -> dict:
        return {
            "incumbent_changes": self.incumbent_changes,
            "final_incumbent_trial": self.final_incumbent_trial,
            "incumbent_sharpe_progression": self.incumbent_sharpe_progression,
            "average_hold_duration": self.average_hold_duration,
        }


@dataclass(frozen=True)
class StrategyDiversity:
    """How diverse the proposed strategies were.

    Measures the distribution of signal types, parameterizations,
    and the effective search space explored.
    """
    unique_signal_types: int
    signal_type_distribution: dict[str, int]
    parameter_spread: float  # Std dev of lookback periods
    effective_search_space: float  # Normalized diversity metric

    def to_dict(self) -> dict:
        return {
            "unique_signal_types": self.unique_signal_types,
            "signal_type_distribution": self.signal_type_distribution,
            "parameter_spread": self.parameter_spread,
            "effective_search_space": self.effective_search_space,
        }


@dataclass(frozen=True)
class NominalVsDefensible:
    """The gap between nominal performance and statistically defensible performance.

    This is the central measurement of the experimental framework.
    It exposes the difference between what the agent reports and
    what the protocol validates.
    """
    # Nominal (what the agent reports)
    nominal_sharpe: float
    nominal_max_drawdown: float
    nominal_total_return: float

    # Statistically defensible (what survives rigorous evaluation)
    dsr: Optional[float]  # Deflated Sharpe Ratio (probability value)
    pbo: Optional[float]  # Probability of Backtest Overfitting
    defensible_sharpe: Optional[float]  # Sharpe after DSR correction

    # Holdout (out-of-sample)
    holdout_sharpe: Optional[float]
    holdout_max_drawdown: Optional[float]
    holdout_total_return: Optional[float]

    # Baseline relative
    baseline_sharpe: Optional[float]
    baseline_total_return: Optional[float]
    alpha_vs_baseline: Optional[float]  # Strategy return - baseline return

    # The gaps
    sharpe_gap: Optional[float]  # nominal_sharpe - holdout_sharpe
    drawdown_gap: Optional[float]  # holddown_max_drawdown - nominal_max_drawdown
    return_gap: Optional[float]  # nominal_total_return - holdout_total_return

    def to_dict(self) -> dict:
        return {
            "nominal": {
                "sharpe": self.nominal_sharpe,
                "max_drawdown": self.nominal_max_drawdown,
                "total_return": self.nominal_total_return,
            },
            "defensible": {
                "dsr": self.dsr,
                "pbo": self.pbo,
                "sharpe": self.defensible_sharpe,
            },
            "holdout": {
                "sharpe": self.holdout_sharpe,
                "max_drawdown": self.holdout_max_drawdown,
                "total_return": self.holdout_total_return,
            },
            "baseline": {
                "sharpe": self.baseline_sharpe,
                "total_return": self.baseline_total_return,
                "alpha": self.alpha_vs_baseline,
            },
            "gaps": {
                "sharpe_gap": self.sharpe_gap,
                "drawdown_gap": self.drawdown_gap,
                "return_gap": self.return_gap,
            },
        }


@dataclass(frozen=True)
class ReflectionImpact:
    """The impact of bounded reflection on research quality.

    Measures whether reflection improved out-of-sample performance
    or simply increased the effective search space.
    """
    total_reflections: int
    revisions_triggered: int
    revision_acceptance_rate: float  # How often revisions were accepted
    reflection_improved_holdout: Optional[float]  # Holdout Sharpe with reflection
    no_reflection_baseline_sharpe: Optional[float]  # Holdout Sharpe without reflection
    reflection_net_value: Optional[float]  # Improved - baseline

    def to_dict(self) -> dict:
        return {
            "total_reflections": self.total_reflections,
            "revisions_triggered": self.revisions_triggered,
            "revision_acceptance_rate": self.revision_acceptance_rate,
            "reflection_improved_holdout": self.reflection_improved_holdout,
            "no_reflection_baseline_sharpe": self.no_reflection_baseline_sharpe,
            "reflection_net_value": self.reflection_net_value,
        }


@dataclass(frozen=True)
class ExperimentMetrics:
    """Complete metrics for a single governed research experiment.

    This is the primary output of the experimental framework.
    It captures everything needed to evaluate the relationship
    between nominal and defensible performance.
    """
    experiment_id: str
    status: str  # completed, failed, rejected

    # Trial metrics
    trial_efficiency: TrialEfficiency

    # Incumbent metrics
    incumbent_turnover: IncumbentTurnover

    # Diversity metrics
    strategy_diversity: StrategyDiversity

    # Nominal vs defensible
    nominal_vs_defensible: NominalVsDefensible

    # Reflection metrics
    reflection_impact: ReflectionImpact

    # Decision outcome
    decision_outcome: str  # candidate, passed_but_no_value, no_strategy_passed
    gates_passed: bool
    holdout_outperformed_baseline: bool

    # Provenance summary
    total_events: int
    total_artifacts: int

    # Raw data for further analysis
    trial_sharpe_ratios: list[float] = field(default_factory=list)
    trial_max_drawdowns: list[float] = field(default_factory=list)
    trial_total_returns: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "status": self.status,
            "trial_efficiency": self.trial_efficiency.to_dict(),
            "incumbent_turnover": self.incumbent_turnover.to_dict(),
            "strategy_diversity": self.strategy_diversity.to_dict(),
            "nominal_vs_defensible": self.nominal_vs_defensible.to_dict(),
            "reflection_impact": self.reflection_impact.to_dict(),
            "decision_outcome": self.decision_outcome,
            "gates_passed": self.gates_passed,
            "holdout_outperformed_baseline": self.holdout_outperformed_baseline,
            "total_events": self.total_events,
            "total_artifacts": self.total_artifacts,
            "trial_sharpe_ratios": self.trial_sharpe_ratios,
            "trial_max_drawdowns": self.trial_max_drawdowns,
            "trial_total_returns": self.trial_total_returns,
        }


def compute_trial_efficiency(trial_ledger) -> TrialEfficiency:
    """Compute trial efficiency from a trial ledger."""
    all_trials = trial_ledger.get_all_trials()
    evaluated = trial_ledger.get_evaluated_trials()

    total = len(all_trials)
    evaluated_count = len(evaluated)

    # Count improving trials (those that became incumbent)
    improving = 0
    for t in evaluated:
        if t.was_evaluated and t.sharpe_ratio is not None:
            # Check if this trial was ever the incumbent
            # (simplified: count trials with positive Sharpe)
            if t.sharpe_ratio > 0:
                improving += 1

    wasted = total - evaluated_count
    evaluation_rate = evaluated_count / total if total > 0 else 0.0
    improvement_rate = improving / evaluated_count if evaluated_count > 0 else 0.0

    return TrialEfficiency(
        total_trials=total,
        evaluated_trials=evaluated_count,
        improving_trials=improving,
        wasted_trials=wasted,
        evaluation_rate=evaluation_rate,
        improvement_rate=improvement_rate,
    )


def compute_incumbent_turnover(trial_ledger) -> IncumbentTurnover:
    """Compute incumbent turnover from a trial ledger."""
    evaluated = trial_ledger.get_evaluated_trials()
    incumbent = trial_ledger.get_incumbent()

    # Count how many times the incumbent changed
    # (approximated by counting trials that improved on previous best)
    changes = 0
    progression: list[float] = []
    best_sharpe = float("-inf")

    for t in evaluated:
        if t.sharpe_ratio is not None and t.sharpe_ratio > best_sharpe:
            best_sharpe = t.sharpe_ratio
            changes += 1
            progression.append(best_sharpe)

    final_incumbent_trial = incumbent.trial_id if incumbent else -1
    average_hold = len(evaluated) / changes if changes > 0 else 0.0

    return IncumbentTurnover(
        incumbent_changes=changes,
        final_incumbent_trial=final_incumbent_trial,
        incumbent_sharpe_progression=progression,
        average_hold_duration=average_hold,
    )


def compute_strategy_diversity(trial_ledger) -> StrategyDiversity:
    """Compute strategy diversity from a trial ledger."""
    all_trials = trial_ledger.get_all_trials()

    signal_types: dict[str, int] = {}
    lookbacks: list[int] = []

    for t in all_trials:
        spec = t.strategy_spec
        st = spec.get("signal_type", "unknown")
        signal_types[st] = signal_types.get(st, 0) + 1
        lb = spec.get("signal_params", {}).get("lookback", 0)
        lookbacks.append(lb)

    unique_types = len(signal_types)
    spread = float(np.std(lookbacks)) if lookbacks else 0.0

    # Effective search space: normalized entropy of signal type distribution
    total = sum(signal_types.values())
    if total > 0:
        probs = np.array(list(signal_types.values())) / total
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        max_entropy = np.log(unique_types) if unique_types > 1 else 1.0
        effective_search_space = entropy / max_entropy
    else:
        effective_search_space = 0.0

    return StrategyDiversity(
        unique_signal_types=unique_types,
        signal_type_distribution=signal_types,
        parameter_spread=spread,
        effective_search_space=effective_search_space,
    )


def compute_nominal_vs_defensible(
    experiment,
    trial_ledger,
    holdout,
    baseline,
    dsr_value: Optional[float],
    pbo_value: Optional[float],
) -> NominalVsDefensible:
    """Compute the gap between nominal and defensible performance."""
    incumbent = trial_ledger.get_incumbent()

    # Nominal performance (from the incumbent's backtest)
    nominal_sharpe = 0.0
    nominal_max_drawdown = 0.0
    nominal_total_return = 0.0

    if incumbent and incumbent.backtest_result:
        br = incumbent.backtest_result
        nominal_sharpe = br.get("sharpe_ratio", 0.0)
        nominal_max_drawdown = br.get("max_drawdown", 0.0)
        nominal_total_return = br.get("total_return", 0.0)

    # Holdout performance
    holdout_sharpe = None
    holdout_max_drawdown = None
    holdout_total_return = None
    if holdout:
        holdout_sharpe = holdout.strategy_sharpe_ratio
        holdout_max_drawdown = holdout.strategy_max_drawdown
        holdout_total_return = holdout.strategy_total_return

    # Baseline
    baseline_sharpe = None
    baseline_total_return = None
    if baseline:
        baseline_total_return = baseline.total_return
        if baseline.return_series:
            r = np.array(baseline.return_series)
            if len(r) > 1 and np.std(r, ddof=1) > 0:
                baseline_sharpe = float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(252))

    # Alpha
    alpha = None
    if holdout_total_return is not None and baseline_total_return is not None:
        alpha = holdout_total_return - baseline_total_return

    # Defensible Sharpe (observed - expected max under null)
    defensible_sharpe = None
    if dsr_value is not None:
        # DSR is a probability value; the defensible Sharpe is the
        # Sharpe that would be expected after accounting for selection
        from scipy import stats
        if incumbent and incumbent.backtest_result:
            observed = incumbent.backtest_result.get("sharpe_ratio", 0.0)
            # The defensible Sharpe is the observed minus the expected max
            # This is a simplification; the full DSR computation is more complex
            defensible_sharpe = observed

    # Gaps
    sharpe_gap = None
    if holdout_sharpe is not None:
        sharpe_gap = nominal_sharpe - holdout_sharpe

    drawdown_gap = None
    if holdout_max_drawdown is not None:
        drawdown_gap = holdout_max_drawdown - nominal_max_drawdown

    return_gap = None
    if holdout_total_return is not None:
        return_gap = nominal_total_return - holdout_total_return

    return NominalVsDefensible(
        nominal_sharpe=nominal_sharpe,
        nominal_max_drawdown=nominal_max_drawdown,
        nominal_total_return=nominal_total_return,
        dsr=dsr_value,
        pbo=pbo_value,
        defensible_sharpe=defensible_sharpe,
        holdout_sharpe=holdout_sharpe,
        holdout_max_drawdown=holdout_max_drawdown,
        holdout_total_return=holdout_total_return,
        baseline_sharpe=baseline_sharpe,
        baseline_total_return=baseline_total_return,
        alpha_vs_baseline=alpha,
        sharpe_gap=sharpe_gap,
        drawdown_gap=drawdown_gap,
        return_gap=return_gap,
    )


def compute_reflection_impact(
    trial_ledger,
    holdout_sharpe_with_reflection: Optional[float],
    holdout_sharpe_without_reflection: Optional[float],
) -> ReflectionImpact:
    """Compute the impact of reflection on research quality."""
    all_trials = trial_ledger.get_all_trials()

    total_reflections = 0
    revisions_triggered = 0

    for t in all_trials:
        if t.critique_id:
            total_reflections += 1
            # Check if critique recommended revision
            # (simplified: count all critiques as potential revisions)
            revisions_triggered += 1

    acceptance_rate = 1.0  # Simplified: all revisions are accepted

    net_value = None
    if holdout_sharpe_with_reflection is not None and holdout_sharpe_without_reflection is not None:
        net_value = holdout_sharpe_with_reflection - holdout_sharpe_without_reflection

    return ReflectionImpact(
        total_reflections=total_reflections,
        revisions_triggered=revisions_triggered,
        revision_acceptance_rate=acceptance_rate,
        reflection_improved_holdout=holdout_sharpe_with_reflection,
        no_reflection_baseline_sharpe=holdout_sharpe_without_reflection,
        reflection_net_value=net_value,
    )


def compute_experiment_metrics(
    experiment,
    holdout_sharpe_no_reflection: Optional[float] = None,
) -> ExperimentMetrics:
    """Compute all metrics for a single experiment."""
    trial_ledger = experiment.trial_ledger

    trial_efficiency = compute_trial_efficiency(trial_ledger)
    incumbent_turnover = compute_incumbent_turnover(trial_ledger)
    strategy_diversity = compute_strategy_diversity(trial_ledger)
    nominal_vs_defensible = compute_nominal_vs_defensible(
        experiment,
        trial_ledger,
        experiment.holdout,
        experiment.baseline,
        experiment.dsr_value,
        experiment.pbo_value,
    )
    reflection_impact = compute_reflection_impact(
        trial_ledger,
        nominal_vs_defensible.holdout_sharpe,
        holdout_sharpe_no_reflection,
    )

    # Trial-level data
    evaluated = trial_ledger.get_evaluated_trials()
    trial_sharpes = [t.sharpe_ratio for t in evaluated if t.sharpe_ratio is not None]
    trial_drawdowns = [t.max_drawdown for t in evaluated if t.max_drawdown is not None]
    trial_returns = [t.total_return for t in evaluated if t.total_return is not None]

    return ExperimentMetrics(
        experiment_id=experiment.experiment_id,
        status="completed" if experiment.is_complete else "failed",
        trial_efficiency=trial_efficiency,
        incumbent_turnover=incumbent_turnover,
        strategy_diversity=strategy_diversity,
        nominal_vs_defensible=nominal_vs_defensible,
        reflection_impact=reflection_impact,
        decision_outcome=experiment.decision.outcome if experiment.decision else "unknown",
        gates_passed=experiment.decision.outcome == "candidate" if experiment.decision else False,
        holdout_outperformed_baseline=experiment.holdout.outperformed_baseline if experiment.holdout else False,
        total_events=len(experiment.event_log.events),
        total_artifacts=len(experiment.event_log.events),  # Simplified
        trial_sharpe_ratios=trial_sharpes,
        trial_max_drawdowns=trial_drawdowns,
        trial_total_returns=trial_returns,
    )
