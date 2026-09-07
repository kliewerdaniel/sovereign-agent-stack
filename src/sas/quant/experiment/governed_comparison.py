"""Governed vs ungoverned research comparison.

This module implements the four experimental conditions:

- Experiment A: Ungoverned agent (unrestricted optimization)
- Experiment B: Governed agent (bounded trials, provenance, DSR/PBO, holdout)
- Experiment C: Synthetic world with known signal
- Experiment D: Synthetic null world (no exploitable signal)

The null world is the critical control: if an agent can consistently
manufacture high nominal Sharpe strategies in a world where no predictive
structure exists, we have a direct measurement of the agent's optimization
pressure.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.market import SyntheticDataProvider
from sas.quant.provenance.artifacts import ResearchDecision
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.orchestration.researcher import Researcher, ResearchResult


@dataclass
class ComparisonResult:
    """Result of a governed vs ungoverned comparison."""
    experiment_id: str
    condition: str  # "governed", "ungoverned"
    world_type: str  # "signal", "null"
    nominal_sharpe: float = 0.0
    holdout_sharpe: float = 0.0
    dsr: Optional[float] = None
    pbo: Optional[float] = None
    acceptance: bool = False
    n_trials: int = 0
    n_evaluated: int = 0
    sharpe_gap: float = 0.0

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "condition": self.condition,
            "world_type": self.world_type,
            "nominal_sharpe": self.nominal_sharpe,
            "holdout_sharpe": self.holdout_sharpe,
            "dsr": self.dsr,
            "pbo": self.pbo,
            "acceptance": self.acceptance,
            "n_trials": self.n_trials,
            "n_evaluated": self.n_evaluated,
            "sharpe_gap": self.sharpe_gap,
        }


def run_governed_experiment(
    universe: list[str],
    trial_budget: int = 10,
    seed: int = 42,
    research_window: tuple[str, str] = ("2024-01-01", "2024-09-30"),
    holdout_window: tuple[str, str] = ("2024-10-01", "2024-12-31"),
    max_reflection_rounds: int = 1,
) -> Experiment:
    """Run a governed research experiment with full constraints."""
    config = ExperimentConfig(
        experiment_id=f"governed-{uuid.uuid4().hex[:8]}",
        world_id=f"world-{uuid.uuid4().hex[:8]}",
        trial_budget=trial_budget,
        research_window=research_window,
        holdout_window=holdout_window,
        model_id="experimental-agent",
        task_id="governed-research",
        random_seed=seed,
        max_reflection_rounds=max_reflection_rounds,
        baseline_config=BaselineConfig(
            baseline_type="buy_and_hold",
            universe=universe,
            data_window=research_window,
        ),
        gate_config=ResearchGateConfig(),
    )

    experiment = Experiment(config)
    data_provider = SyntheticDataProvider(seed=seed)

    experiment.compute_baseline(data_provider)

    researcher = Researcher(experiment, data_provider=data_provider)
    researcher.run_research()

    experiment.compute_statistics()

    evaluated = experiment.trial_ledger.get_evaluated_trials()
    if evaluated:
        best = max(evaluated, key=lambda t: t.sharpe_ratio or float("-inf"))
        experiment.trial_ledger.set_incumbent(best.trial_id)

    experiment.evaluate_holdout(data_provider)
    experiment.make_decision()

    return experiment


def run_ungoverned_experiment(
    universe: list[str],
    trial_budget: int = 10,
    seed: int = 42,
    research_window: tuple[str, str] = ("2024-01-01", "2024-09-30"),
    holdout_window: tuple[str, str] = ("2024-10-01", "2024-12-31"),
) -> Experiment:
    """Run an ungoverned research experiment (no constraints).

    This simulates a conventional agentic quant system:
    - No temporal authority (can access all data)
    - No trial budget enforcement
    - No provenance requirements
    - No DSR/PBO statistical correction
    - No mandatory baseline
    - No deterministic gates
    """
    config = ExperimentConfig(
        experiment_id=f"ungoverned-{uuid.uuid4().hex[:8]}",
        world_id=f"world-{uuid.uuid4().hex[:8]}",
        trial_budget=trial_budget,
        research_window=research_window,
        holdout_window=holdout_window,
        model_id="experimental-agent",
        task_id="ungoverned-research",
        random_seed=seed,
        max_reflection_rounds=0,  # No reflection in ungoverned mode
        baseline_config=BaselineConfig(
            baseline_type="buy_and_hold",
            universe=universe,
            data_window=research_window,
        ),
        gate_config=ResearchGateConfig(),
    )

    experiment = Experiment(config)
    data_provider = SyntheticDataProvider(seed=seed)

    # Compute baseline (but don't enforce comparison)
    experiment.compute_baseline(data_provider)

    # Run research loop (same as governed, but without constraints)
    researcher = Researcher(experiment, data_provider=data_provider)
    researcher.run_research()

    # Skip DSR/PBO computation (ungoverned)
    # Skip statistical gates

    evaluated = experiment.trial_ledger.get_evaluated_trials()
    best = None
    if evaluated:
        best = max(evaluated, key=lambda t: t.sharpe_ratio or float("-inf"))
        experiment.trial_ledger.set_incumbent(best.trial_id)

    # Evaluate holdout (but don't enforce it)
    experiment.evaluate_holdout(data_provider)

    # Make decision without gates
    experiment._decision = ResearchDecision(
        experiment_id=experiment.experiment_id,
        outcome="candidate",  # Always accept in ungoverned mode
        incumbent_trial_id=best.trial_id if best else None,
        baseline_id=experiment.baseline.baseline_id if experiment.baseline else "",
        holdout_id=experiment.holdout.holdout_id if experiment.holdout else "",
        rationale="Ungoverned: no gates applied",
        trial_count=experiment.trial_ledger.total_trials,
        evaluated_count=len(evaluated),
    )
    experiment._is_complete = True

    return experiment


def run_comparison(
    universe: list[str],
    trial_budget: int = 10,
    seed: int = 42,
    research_window: tuple[str, str] = ("2024-01-01", "2024-09-30"),
    holdout_window: tuple[str, str] = ("2024-10-01", "2024-12-31"),
) -> tuple[ComparisonResult, ComparisonResult]:
    """Run a governed vs ungoverned comparison on the same data."""
    # Governed experiment
    governed = run_governed_experiment(
        universe=universe,
        trial_budget=trial_budget,
        seed=seed,
        research_window=research_window,
        holdout_window=holdout_window,
    )

    # Ungoverned experiment
    ungoverned = run_ungoverned_experiment(
        universe=universe,
        trial_budget=trial_budget,
        seed=seed,
        research_window=research_window,
        holdout_window=holdout_window,
    )

    # Extract results
    governed_result = _extract_comparison_result(governed, "governed")
    ungoverned_result = _extract_comparison_result(ungoverned, "ungoverned")

    return governed_result, ungoverned_result


def _extract_comparison_result(experiment: Experiment, condition: str) -> ComparisonResult:
    """Extract a comparison result from an experiment."""
    incumbent = experiment.trial_ledger.get_incumbent()

    nominal_sharpe = 0.0
    if incumbent and incumbent.backtest_result:
        nominal_sharpe = incumbent.backtest_result.get("sharpe_ratio", 0.0)

    holdout_sharpe = 0.0
    if experiment.holdout:
        holdout_sharpe = experiment.holdout.strategy_sharpe_ratio

    return ComparisonResult(
        experiment_id=experiment.experiment_id,
        condition=condition,
        world_type="unknown",  # Set by caller
        nominal_sharpe=nominal_sharpe,
        holdout_sharpe=holdout_sharpe,
        dsr=experiment.dsr_value,
        pbo=experiment.pbo_value,
        acceptance=experiment.decision.outcome == "candidate" if experiment.decision else False,
        n_trials=experiment.trial_ledger.total_trials,
        n_evaluated=experiment.trial_ledger.evaluated_count,
        sharpe_gap=nominal_sharpe - holdout_sharpe,
    )
