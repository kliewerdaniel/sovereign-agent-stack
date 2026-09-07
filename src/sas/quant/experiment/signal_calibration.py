"""Signal calibration across controlled effect sizes.

This module measures the true acceptance rate: P(accept | signal_strength).

The central question: does the governance system produce a meaningful operating characteristic?

We want to know whether governance produces something resembling:

    acceptance probability

    1.0 |                         █████
        |                    █████
        |               █████
        |          █████
        |     █████
    0.0 |████
        +----------------------------
          null → weak → moderate → strong

If instead the system produces 5% false acceptance but also rejects 90% of genuinely
strong signals, we've simply built an extremely conservative system.

That is a policy choice, not necessarily a bug.
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
class SignalCalibrationResult:
    """Result of a single signal calibration experiment."""
    experiment_id: str
    world_id: str
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
class SignalCalibrationBatch:
    """A batch of signal calibration experiments."""
    batch_id: str
    signal_strength: float
    trial_budget: int
    n_observations: int
    reflection_rounds: int
    n_experiments: int
    results: list[SignalCalibrationResult] = field(default_factory=list)

    # Summary statistics
    acceptance_rate: float = 0.0
    avg_nominal_sharpe: float = 0.0
    avg_holdout_sharpe: float = 0.0
    avg_sharpe_gap: float = 0.0
    avg_max_sharpe: float = 0.0
    avg_dsr: float = 0.0
    avg_pbo: float = 0.0

    # Confidence intervals (95%)
    acceptance_rate_ci_lower: float = 0.0
    acceptance_rate_ci_upper: float = 0.0

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "n_observations": self.n_observations,
            "reflection_rounds": self.reflection_rounds,
            "n_experiments": self.n_experiments,
            "acceptance_rate": self.acceptance_rate,
            "avg_nominal_sharpe": self.avg_nominal_sharpe,
            "avg_holdout_sharpe": self.avg_holdout_sharpe,
            "avg_sharpe_gap": self.avg_sharpe_gap,
            "avg_max_sharpe": self.avg_max_sharpe,
            "avg_dsr": self.avg_dsr,
            "avg_pbo": self.avg_pbo,
            "acceptance_rate_ci_lower": self.acceptance_rate_ci_lower,
            "acceptance_rate_ci_upper": self.acceptance_rate_ci_upper,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class SignalCalibrationMatrix:
    """Complete signal calibration matrix."""
    matrix_id: str
    batches: list[SignalCalibrationBatch] = field(default_factory=list)
    output_dir: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "matrix_id": self.matrix_id,
            "batches": [b.to_dict() for b in self.batches],
            "output_dir": self.output_dir,
            "created_at": self.created_at,
        }


def run_signal_calibration(
    n_worlds: int = 25,
    signal_strengths: list[float] | None = None,
    trial_budgets: list[int] | None = None,
    n_observations_list: list[int] | None = None,
    noise_std: float = 0.02,
    reflection_rounds_list: list[int] | None = None,
    output_dir: str = "./experiments/calibration",
    matrix_id: str | None = None,
) -> SignalCalibrationMatrix:
    """Run signal calibration experiments across controlled effect sizes.

    Args:
        n_worlds: Number of independent worlds per configuration
        signal_strengths: Signal strengths to test
        trial_budgets: Trial budgets to test
        n_observations_list: Sample lengths to test
        noise_std: Standard deviation of returns
        reflection_rounds_list: Reflection settings to test
        output_dir: Output directory
        matrix_id: Matrix ID (auto-generated if not provided)

    Returns:
        SignalCalibrationMatrix with all results
    """
    if signal_strengths is None:
        signal_strengths = [0.00, 0.10, 0.25, 0.50, 1.00]
    if trial_budgets is None:
        trial_budgets = [10, 20, 50]
    if n_observations_list is None:
        n_observations_list = [252]
    if reflection_rounds_list is None:
        reflection_rounds_list = [1]
    if matrix_id is None:
        matrix_id = f"signal-cal-{uuid.uuid4().hex[:8]}"

    matrix = SignalCalibrationMatrix(
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
                    batch_id = f"s{signal_strength}-b{trial_budget}-n{n_obs}-r{reflection}"

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
                    batch = SignalCalibrationBatch(
                        batch_id=batch_id,
                        signal_strength=signal_strength,
                        trial_budget=trial_budget,
                        n_observations=n_obs,
                        reflection_rounds=reflection,
                        n_experiments=n_worlds,
                        results=results,
                        acceptance_rate=accepted / n_worlds,
                        avg_nominal_sharpe=float(np.mean([r.nominal_sharpe for r in results])),
                        avg_holdout_sharpe=float(np.mean([r.holdout_sharpe for r in results])),
                        avg_sharpe_gap=float(np.mean([r.sharpe_gap for r in results])),
                        avg_max_sharpe=float(np.mean([r.max_sharpe_in_population for r in results])),
                        avg_dsr=float(np.mean([r.dsr for r in results if r.dsr is not None]) if any(r.dsr is not None for r in results) else 0.0),
                        avg_pbo=float(np.mean([r.pbo for r in results if r.pbo is not None]) if any(r.pbo is not None for r in results) else 0.0),
                        acceptance_rate_ci_lower=_wilson_score_interval(accepted, n_worlds)[0],
                        acceptance_rate_ci_upper=_wilson_score_interval(accepted, n_worlds)[1],
                    )
                    matrix.batches.append(batch)

    # Save matrix
    _save_matrix(matrix, matrix_path)

    return matrix


def _run_single_signal_experiment(
    seed: int,
    signal_strength: float,
    trial_budget: int,
    n_observations: int,
    noise_std: float,
    reflection_rounds: int,
) -> SignalCalibrationResult:
    """Run a single signal world experiment."""
    from sas.quant.experiment.synthetic_worlds import generate_signal_world, generate_null_world

    if signal_strength == 0.0:
        signal_world = generate_null_world(
            world_id=f"null-seed{seed}",
            seed=seed,
            noise_std=noise_std,
        )
    else:
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
        world=signal_world,
    )

    return _extract_calibration_result(experiment, signal_world)


def _run_governed_experiment(
    universe: list[str],
    trial_budget: int,
    seed: int,
    research_window: tuple[str, str],
    holdout_window: tuple[str, str],
    max_reflection_rounds: int = 1,
    world: Any = None,
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

    # Use SyntheticWorldProvider if world is provided, otherwise use standard provider
    if world is not None:
        from sas.quant.experiment.synthetic_data_provider import SyntheticWorldProvider
        data_provider = SyntheticWorldProvider(world, seed=seed)
    else:
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


def _extract_calibration_result(experiment: Experiment, world) -> SignalCalibrationResult:
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

    return SignalCalibrationResult(
        experiment_id=experiment.experiment_id,
        world_id=world.world_id,
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


def _wilson_score_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson score interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0

    p_hat = successes / n
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return lower, upper


def _save_matrix(matrix: SignalCalibrationMatrix, matrix_path: Path) -> None:
    """Save a calibration matrix to disk."""
    (matrix_path / "signal_calibration_matrix.json").write_text(
        json.dumps(matrix.to_dict(), indent=2, default=str)
    )


def generate_signal_calibration_report(matrix: SignalCalibrationMatrix) -> str:
    """Generate a human-readable signal calibration report."""
    lines = [
        "# Signal Calibration Report",
        "",
        f"**Matrix ID:** {matrix.matrix_id}",
        f"**Created:** {matrix.created_at}",
        f"**Total Batches:** {len(matrix.batches)}",
        "",
        "## Operating Characteristic",
        "",
        "| Signal Strength | Accept Rate | 95% CI | Avg Nominal | Avg Holdout | Avg Gap |",
        "|---|---|---|---|---|---|",
    ]

    for batch in matrix.batches:
        ci = f"[{batch.acceptance_rate_ci_lower:.2%}, {batch.acceptance_rate_ci_upper:.2%}]"
        lines.append(
            f"| {batch.signal_strength:.2f} | {batch.acceptance_rate:.2%} | {ci} | "
            f"{batch.avg_nominal_sharpe:.3f} | {batch.avg_holdout_sharpe:.3f} | "
            f"{batch.avg_sharpe_gap:.3f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "### Ideal Operating Characteristic",
        "",
        "Acceptance probability should increase monotonically with signal strength:",
        "",
        "    1.0 |                         █████",
        "        |                    █████",
        "        |               █████",
        "        |          █████",
        "        |     █████",
        "    0.0 |████",
        "        +----------------------------",
        "          null → weak → moderate → strong",
        "",
        "### Conservative vs Liberal Systems",
        "",
        "- **Conservative**: Low false acceptance but also low true acceptance",
        "- **Liberal**: High true acceptance but also high false acceptance",
        "- **Ideal**: Low false acceptance AND high true acceptance",
        "",
        "The choice between conservative and liberal is a policy decision,",
        "not a technical one.",
        "",
        "---",
        "*Generated by SAS Signal Calibration Framework*",
    ])

    return "\n".join(lines )
