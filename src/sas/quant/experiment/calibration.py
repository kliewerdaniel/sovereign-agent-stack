"""Calibration framework for governed research gates.

The central question: are the statistical gates calibrated to the environment?

A gate that rejects everything has perfect false discovery control but is useless.
A gate that accepts everything is useful for finding strategies but has no false
discovery control. The calibration framework measures where the current gates
operate on this spectrum.

The key measurements:

- P(accept | null) — false acceptance rate (should be low)
- P(accept | weak signal) — true acceptance rate for weak signals
- P(accept | medium signal) — true acceptance rate for medium signals
- P(accept | strong signal) — true acceptance rate for strong signals

These give an empirical operating characteristic for the research gates.

Validation hierarchy:

- Level 1: Temporal isolation
- Level 2: Experiment reconstruction
- Level 3: In-sample to holdout degradation detection
- Level 4: DSR/PBO control false discoveries in synthetic null worlds
- Level 5: Calibrated system recovers known signals in synthetic signal worlds
- Level 6: Behavior generalizes to realistic market data

We are currently moving from Level 3 into Level 4.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.market import SyntheticDataProvider
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.orchestration.researcher import Researcher


@dataclass(frozen=True)
class CalibrationResult:
    """Result of a single calibration experiment."""
    experiment_id: str
    world_id: str
    world_type: str  # "null", "signal"
    signal_strength: float
    trial_budget: int
    n_observations: int
    seed: int
    reflection_rounds: int

    # Results
    nominal_sharpe: float = 0.0
    holdout_sharpe: float = 0.0
    dsr: Optional[float] = None
    pbo: Optional[float] = None
    accepted: bool = False
    decision_outcome: str = "no_strategy_passed"
    n_trials: int = 0
    n_evaluated: int = 0
    max_sharpe_in_population: float = 0.0
    sharpe_gap: float = 0.0

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "world_id": self.world_id,
            "world_type": self.world_type,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "n_observations": self.n_observations,
            "seed": self.seed,
            "reflection_rounds": self.reflection_rounds,
            "nominal_sharpe": self.nominal_sharpe,
            "holdout_sharpe": self.holdout_sharpe,
            "dsr": self.dsr,
            "pbo": self.pbo,
            "accepted": self.accepted,
            "decision_outcome": self.decision_outcome,
            "n_trials": self.n_trials,
            "n_evaluated": self.n_evaluated,
            "max_sharpe_in_population": self.max_sharpe_in_population,
            "sharpe_gap": self.sharpe_gap,
        }


@dataclass(frozen=True)
class CalibrationBatch:
    """A batch of calibration experiments with the same configuration."""
    batch_id: str
    world_type: str
    signal_strength: float
    trial_budget: int
    n_observations: int
    reflection_rounds: int
    n_experiments: int
    results: list[CalibrationResult] = field(default_factory=list)

    # Summary statistics
    false_acceptance_rate: float = 0.0
    true_acceptance_rate: float = 0.0
    avg_nominal_sharpe: float = 0.0
    avg_holdout_sharpe: float = 0.0
    avg_sharpe_gap: float = 0.0
    avg_max_sharpe: float = 0.0
    avg_dsr: float = 0.0
    avg_pbo: float = 0.0

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "world_type": self.world_type,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "n_observations": self.n_observations,
            "reflection_rounds": self.reflection_rounds,
            "n_experiments": self.n_experiments,
            "false_acceptance_rate": self.false_acceptance_rate,
            "true_acceptance_rate": self.true_acceptance_rate,
            "avg_nominal_sharpe": self.avg_nominal_sharpe,
            "avg_holdout_sharpe": self.avg_holdout_sharpe,
            "avg_sharpe_gap": self.avg_sharpe_gap,
            "avg_max_sharpe": self.avg_max_sharpe,
            "avg_dsr": self.avg_dsr,
            "avg_pbo": self.avg_pbo,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class CalibrationMatrix:
    """Complete calibration matrix across world types and configurations."""
    matrix_id: str
    batches: list[CalibrationBatch] = field(default_factory=list)
    output_dir: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "matrix_id": self.matrix_id,
            "batches": [b.to_dict() for b in self.batches],
            "output_dir": self.output_dir,
            "created_at": self.created_at,
        }


def run_null_calibration(
    n_worlds: int = 25,
    trial_budgets: list[int] | None = None,
    n_observations_list: list[int] | None = None,
    noise_std: float = 0.02,
    reflection_rounds_list: list[int] | None = None,
    output_dir: str = "./experiments/calibration",
    matrix_id: str | None = None,
) -> CalibrationMatrix:
    """Run calibration experiments across many null worlds.

    This measures the false acceptance rate: P(accept | null).

    Args:
        n_worlds: Number of independent null worlds to generate
        trial_budgets: Trial budgets to test
        n_observations_list: Sample lengths to test
        noise_std: Standard deviation of returns
        reflection_rounds_list: Reflection settings to test
        output_dir: Output directory
        matrix_id: Matrix ID (auto-generated if not provided)

    Returns:
        CalibrationMatrix with all results
    """
    if trial_budgets is None:
        trial_budgets = [10, 20, 50, 100]
    if n_observations_list is None:
        n_observations_list = [126, 252, 504]
    if reflection_rounds_list is None:
        reflection_rounds_list = [0, 1]
    if matrix_id is None:
        matrix_id = f"null-cal-{uuid.uuid4().hex[:8]}"

    matrix = CalibrationMatrix(
        matrix_id=matrix_id,
        output_dir=output_dir,
        created_at=datetime.now(UTC).isoformat(),
    )

    # Create output directory
    matrix_path = Path(output_dir) / matrix_id
    matrix_path.mkdir(parents=True, exist_ok=True)
    matrix.output_dir = str(matrix_path)

    for trial_budget in trial_budgets:
        for n_obs in n_observations_list:
            for reflection in reflection_rounds_list:
                batch_id = f"null-b{trial_budget}-n{n_obs}-r{reflection}"

                results = []
                for seed in range(n_worlds):
                    result = _run_single_null_experiment(
                        seed=seed,
                        trial_budget=trial_budget,
                        n_observations=n_obs,
                        noise_std=noise_std,
                        reflection_rounds=reflection,
                    )
                    results.append(result)

                # Compute batch statistics
                accepted = sum(1 for r in results if r.accepted)
                batch = CalibrationBatch(
                    batch_id=batch_id,
                    world_type="null",
                    signal_strength=0.0,
                    trial_budget=trial_budget,
                    n_observations=n_obs,
                    reflection_rounds=reflection,
                    n_experiments=n_worlds,
                    results=results,
                    false_acceptance_rate=accepted / n_worlds,
                    avg_nominal_sharpe=float(np.mean([r.nominal_sharpe for r in results])),
                    avg_holdout_sharpe=float(np.mean([r.holdout_sharpe for r in results])),
                    avg_sharpe_gap=float(np.mean([r.sharpe_gap for r in results])),
                    avg_max_sharpe=float(np.mean([r.max_sharpe_in_population for r in results])),
                    avg_dsr=float(np.mean([r.dsr for r in results if r.dsr is not None]) if any(r.dsr is not None for r in results) else 0.0),
                    avg_pbo=float(np.mean([r.pbo for r in results if r.pbo is not None]) if any(r.pbo is not None for r in results) else 0.0),
                )
                matrix.batches.append(batch)

    # Save matrix
    _save_matrix(matrix, matrix_path)

    return matrix


def run_signal_calibration(
    n_worlds: int = 25,
    signal_strengths: list[float] | None = None,
    trial_budgets: list[int] | None = None,
    n_observations_list: list[int] | None = None,
    noise_std: float = 0.02,
    reflection_rounds_list: list[int] | None = None,
    output_dir: str = "./experiments/calibration",
    matrix_id: str | None = None,
) -> CalibrationMatrix:
    """Run calibration experiments across signal worlds.

    This measures the true acceptance rate: P(accept | signal).

    Args:
        n_worlds: Number of independent signal worlds per configuration
        signal_strengths: Signal strengths to test
        trial_budgets: Trial budgets to test
        n_observations_list: Sample lengths to test
        noise_std: Standard deviation of returns
        reflection_rounds_list: Reflection settings to test
        output_dir: Output directory
        matrix_id: Matrix ID (auto-generated if not provided)

    Returns:
        CalibrationMatrix with all results
    """
    if signal_strengths is None:
        signal_strengths = [0.05, 0.10, 0.15, 0.20, 0.30]
    if trial_budgets is None:
        trial_budgets = [10, 20, 50]
    if n_observations_list is None:
        n_observations_list = [126, 252, 504]
    if reflection_rounds_list is None:
        reflection_rounds_list = [0, 1]
    if matrix_id is None:
        matrix_id = f"signal-cal-{uuid.uuid4().hex[:8]}"

    matrix = CalibrationMatrix(
        matrix_id=matrix_id,
        output_dir=output_dir,
        created_at=datetime.now(UTC).isoformat(),
    )

    # Create output directory
    matrix_path = Path(output_dir) / matrix_id
    matrix_path.mkdir(parents=True, exist_ok=True)
    matrix.output_dir = str(matrix_path)

    for signal_strength in signal_strengths:
        for trial_budget in trial_budgets:
            for n_obs in n_observations_list:
                for reflection in reflection_rounds_list:
                    batch_id = f"signal-s{signal_strength}-b{trial_budget}-n{n_obs}-r{reflection}"

                    results = []
                    for seed in range(n_worlds):
                        result = _run_single_signal_experiment(
                            seed=seed,
                            signal_strength=signal_strength,
                            trial_budget=trial_budget,
                            n_observations=n_obs,
                            noise_std=noise_std,
                            reflection_rounds=reflection,
                        )
                        results.append(result)

                    # Compute batch statistics
                    accepted = sum(1 for r in results if r.accepted)
                    batch = CalibrationBatch(
                        batch_id=batch_id,
                        world_type="signal",
                        signal_strength=signal_strength,
                        trial_budget=trial_budget,
                        n_observations=n_obs,
                        reflection_rounds=reflection,
                        n_experiments=n_worlds,
                        results=results,
                        true_acceptance_rate=accepted / n_worlds,
                        avg_nominal_sharpe=float(np.mean([r.nominal_sharpe for r in results])),
                        avg_holdout_sharpe=float(np.mean([r.holdout_sharpe for r in results])),
                        avg_sharpe_gap=float(np.mean([r.sharpe_gap for r in results])),
                        avg_max_sharpe=float(np.mean([r.max_sharpe_in_population for r in results])),
                        avg_dsr=float(np.mean([r.dsr for r in results if r.dsr is not None]) if any(r.dsr is not None for r in results) else 0.0),
                        avg_pbo=float(np.mean([r.pbo for r in results if r.pbo is not None]) if any(r.pbo is not None for r in results) else 0.0),
                    )
                    matrix.batches.append(batch)

    # Save matrix
    _save_matrix(matrix, matrix_path)

    return matrix


def _run_single_null_experiment(
    seed: int,
    trial_budget: int,
    n_observations: int,
    noise_std: float,
    reflection_rounds: int,
) -> CalibrationResult:
    """Run a single null world experiment."""
    # Generate null world
    from sas.quant.experiment.synthetic_worlds import generate_null_world

    null_world = generate_null_world(
        world_id=f"null-seed{seed}",
        seed=seed,
        noise_std=noise_std,
    )

    # Run governed experiment
    experiment = _run_governed_experiment(
        universe=[null_world.symbol],
        trial_budget=trial_budget,
        seed=seed,
        research_window=null_world.research_window,
        holdout_window=null_world.holdout_window,
        max_reflection_rounds=reflection_rounds,
    )

    return _extract_calibration_result(experiment, null_world)


def _run_single_signal_experiment(
    seed: int,
    signal_strength: float,
    trial_budget: int,
    n_observations: int,
    noise_std: float,
    reflection_rounds: int,
) -> CalibrationResult:
    """Run a single signal world experiment."""
    from sas.quant.experiment.synthetic_worlds import generate_signal_world

    signal_world = generate_signal_world(
        world_id=f"signal-s{signal_strength}-seed{seed}",
        seed=seed,
        signal_strength=signal_strength,
        noise_std=noise_std,
    )

    # Run governed experiment
    experiment = _run_governed_experiment(
        universe=[signal_world.symbol],
        trial_budget=trial_budget,
        seed=seed,
        research_window=signal_world.research_window,
        holdout_window=signal_world.holdout_window,
        max_reflection_rounds=reflection_rounds,
    )

    return _extract_calibration_result(experiment, signal_world)


def _run_governed_experiment(
    universe: list[str],
    trial_budget: int,
    seed: int,
    research_window: tuple[str, str],
    holdout_window: tuple[str, str],
    max_reflection_rounds: int = 1,
) -> Experiment:
    """Run a governed research experiment."""
    config = ExperimentConfig(
        experiment_id=f"governed-{uuid.uuid4().hex[:8]}",
        world_id=f"world-{uuid.uuid4().hex[:8]}",
        trial_budget=trial_budget,
        research_window=research_window,
        holdout_window=holdout_window,
        model_id="calibration-agent",
        task_id="calibration",
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


def _extract_calibration_result(experiment: Experiment, world) -> CalibrationResult:
    """Extract a calibration result from an experiment."""
    incumbent = experiment.trial_ledger.get_incumbent()

    nominal_sharpe = 0.0
    if incumbent and incumbent.backtest_result:
        nominal_sharpe = incumbent.backtest_result.get("sharpe_ratio", 0.0)

    holdout_sharpe = 0.0
    if experiment.holdout:
        holdout_sharpe = experiment.holdout.strategy_sharpe_ratio

    # Compute max Sharpe in population
    evaluated = experiment.trial_ledger.get_evaluated_trials()
    max_sharpe = 0.0
    if evaluated:
        sharpes = [t.sharpe_ratio for t in evaluated if t.sharpe_ratio is not None]
        if sharpes:
            max_sharpe = max(sharpes)

    return CalibrationResult(
        experiment_id=experiment.experiment_id,
        world_id=world.world_id,
        world_type="null" if isinstance(world.dgp, type(world.dgp)) and not world.dgp.has_signal else "signal",
        signal_strength=world.dgp.signal_strength,
        trial_budget=experiment.config.trial_budget,
        n_observations=world.dgp.n_observations,
        seed=world.seed,
        reflection_rounds=experiment.config.max_reflection_rounds,
        nominal_sharpe=nominal_sharpe,
        holdout_sharpe=holdout_sharpe,
        dsr=experiment.dsr_value,
        pbo=experiment.pbo_value,
        accepted=experiment.decision.outcome == "candidate" if experiment.decision else False,
        decision_outcome=experiment.decision.outcome if experiment.decision else "unknown",
        n_trials=experiment.trial_ledger.total_trials,
        n_evaluated=experiment.trial_ledger.evaluated_count,
        max_sharpe_in_population=max_sharpe,
        sharpe_gap=nominal_sharpe - holdout_sharpe,
    )


def _save_matrix(matrix: CalibrationMatrix, matrix_path: Path) -> None:
    """Save a calibration matrix to disk."""
    (matrix_path / "calibration_matrix.json").write_text(
        json.dumps(matrix.to_dict(), indent=2, default=str)
    )


def generate_calibration_report(matrix: CalibrationMatrix) -> str:
    """Generate a human-readable calibration report."""
    lines = [
        "# Calibration Report: Governed Research Gates",
        "",
        f"**Matrix ID:** {matrix.matrix_id}",
        f"**Created:** {matrix.created_at}",
        f"**Total Batches:** {len(matrix.batches)}",
        "",
        "## Summary",
        "",
        f"| Configuration | Accept Rate | Avg Nominal | Avg Holdout | Avg Gap | Avg Max |",
        f"|---|---|---|---|---|---|",
    ]

    for batch in matrix.batches:
        world_label = f"{batch.world_type}(s={batch.signal_strength})"
        config_label = f"b={batch.trial_budget}, n={batch.n_observations}, r={batch.reflection_rounds}"
        accept_rate = batch.false_acceptance_rate if batch.world_type == "null" else batch.true_acceptance_rate

        lines.append(
            f"| {world_label} {config_label} | {accept_rate:.2%} | "
            f"{batch.avg_nominal_sharpe:.3f} | {batch.avg_holdout_sharpe:.3f} | "
            f"{batch.avg_sharpe_gap:.3f} | {batch.avg_max_sharpe:.3f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "### Null World (False Acceptance Rate)",
        "",
        "P(accept | null) should be low. If it increases with trial budget,",
        "the agent is functioning as a multiple testing engine.",
        "",
        "### Signal World (True Acceptance Rate)",
        "",
        "P(accept | signal) should increase with signal strength. If it stays",
        "low even for strong signals, the gates are too conservative.",
        "",
        "---",
        "*Generated by SAS Calibration Framework*",
    ])

    return "\n".join(lines)
