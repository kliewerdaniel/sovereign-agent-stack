"""Experiment runner for governed research experiments.

The runner executes a matrix of experimental configurations,
preserves all artifacts, and generates comparative analysis.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.experiment.metrics import (
    ExperimentMetrics,
    compute_experiment_metrics,
)
from sas.quant.market import SyntheticDataProvider
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.orchestration.researcher import Researcher


@dataclass
class ExperimentSpec:
    """A single experimental configuration."""
    spec_id: str = ""
    universe: list[str] = field(default_factory=lambda: ["AAPL", "MSFT"])
    trial_budget: int = 10
    max_reflection_rounds: int = 1
    seed: int = 42
    research_window: tuple[str, str] = ("2024-01-01", "2024-09-30")
    holdout_window: tuple[str, str] = ("2024-10-01", "2024-12-31")
    initial_capital: float = 100_000.0
    baseline_type: str = "buy_and_hold"
    description: str = ""


@dataclass
class ExperimentResult:
    """Result of a single experiment execution."""
    spec: ExperimentSpec
    experiment: Experiment
    metrics: ExperimentMetrics
    artifacts_dir: str = ""


@dataclass
class ExperimentMatrix:
    """A matrix of experimental configurations."""
    matrix_id: str = ""
    specs: list[ExperimentSpec] = field(default_factory=list)
    results: list[ExperimentResult] = field(default_factory=list)
    output_dir: str = ""
    created_at: str = ""


def generate_experiment_matrix(
    matrix_id: str,
    universes: list[list[str]],
    trial_budgets: list[int],
    reflection_rounds: list[int],
    seeds: list[int],
    output_dir: str,
) -> ExperimentMatrix:
    """Generate a full factorial experiment matrix."""
    specs: list[ExperimentSpec] = []

    for universe in universes:
        for budget in trial_budgets:
            for reflection in reflection_rounds:
                for seed in seeds:
                    spec = ExperimentSpec(
                        spec_id=f"exp-{matrix_id}-{len(specs):04d}",
                        universe=universe,
                        trial_budget=budget,
                        max_reflection_rounds=reflection,
                        seed=seed,
                        description=(
                            f"universe={universe}, budget={budget}, "
                            f"reflection={reflection}, seed={seed}"
                        ),
                    )
                    specs.append(spec)

    return ExperimentMatrix(
        matrix_id=matrix_id,
        specs=specs,
        output_dir=output_dir,
        created_at=datetime.now(UTC).isoformat(),
    )


class ExperimentRunner:
    """Runs a matrix of governed research experiments."""

    def __init__(
        self,
        output_dir: str = "./experiments",
        save_artifacts: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.save_artifacts = save_artifacts
        self._current_matrix: Optional[ExperimentMatrix] = None

    def run_matrix(
        self,
        matrix: ExperimentMatrix,
        progress_callback: Optional[Any] = None,
    ) -> ExperimentMatrix:
        """Run all experiments in a matrix."""
        self._current_matrix = matrix
        matrix.results = []

        # Create output directory
        matrix_path = self.output_dir / matrix.matrix_id
        matrix_path.mkdir(parents=True, exist_ok=True)
        matrix.output_dir = str(matrix_path)

        for i, spec in enumerate(matrix.specs):
            if progress_callback:
                progress_callback(i, len(matrix.specs), spec)

            result = self._run_single_experiment(spec, matrix_path)
            matrix.results.append(result)

        # Save matrix summary
        self._save_matrix_summary(matrix, matrix_path)

        return matrix

    def _run_single_experiment(
        self,
        spec: ExperimentSpec,
        matrix_path: Path,
    ) -> ExperimentResult:
        """Run a single experiment and compute metrics."""
        # Create experiment config
        config = ExperimentConfig(
            experiment_id=spec.spec_id,
            world_id=f"exp-world-{spec.spec_id}",
            trial_budget=spec.trial_budget,
            research_window=spec.research_window,
            holdout_window=spec.holdout_window,
            model_id="experimental-agent",
            task_id="governed-research",
            random_seed=spec.seed,
            initial_capital=spec.initial_capital,
            max_reflection_rounds=spec.max_reflection_rounds,
            baseline_config=BaselineConfig(
                baseline_type=spec.baseline_type,
                universe=spec.universe,
                data_window=spec.research_window,
            ),
            gate_config=ResearchGateConfig(),
        )

        # Create experiment
        experiment = Experiment(config)

        # Create data provider
        data_provider = SyntheticDataProvider(seed=spec.seed)

        # Compute baseline
        experiment.compute_baseline(data_provider)

        # Run research loop
        researcher = Researcher(experiment, data_provider=data_provider)
        researcher.run_research()

        # Compute statistics
        experiment.compute_statistics()

        # Set incumbent (best evaluated trial)
        evaluated = experiment.trial_ledger.get_evaluated_trials()
        if evaluated:
            best = max(evaluated, key=lambda t: t.sharpe_ratio or float("-inf"))
            experiment.trial_ledger.set_incumbent(best.trial_id)

        # Evaluate holdout
        experiment.evaluate_holdout(data_provider)

        # Make decision
        experiment.make_decision()

        # Compute metrics
        metrics = compute_experiment_metrics(experiment)

        # Validate experiment
        from sas.quant.experiment.validation import validate_experiment
        validation_report = validate_experiment(experiment)

        # Save artifacts
        artifacts_dir = matrix_path / spec.spec_id
        if self.save_artifacts:
            self._save_experiment_artifacts(experiment, metrics, artifacts_dir, validation_report)

        return ExperimentResult(
            spec=spec,
            experiment=experiment,
            metrics=metrics,
            artifacts_dir=str(artifacts_dir),
        )

    def _save_experiment_artifacts(
        self,
        experiment: Experiment,
        metrics: ExperimentMetrics,
        artifacts_dir: Path,
        validation_report: Any = None,
    ) -> None:
        """Save all experiment artifacts to disk."""
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Save experiment config
        (artifacts_dir / "config.json").write_text(
            json.dumps(experiment.config.to_dict(), indent=2, default=str)
        )

        # Save trial ledger
        (artifacts_dir / "trials.json").write_text(
            json.dumps(experiment.trial_ledger.to_dict(), indent=2, default=str)
        )

        # Save incumbent ID separately for reconstruction
        incumbent_data = {
            "incumbent_id": experiment.trial_ledger._incumbent_id,
        }
        (artifacts_dir / "incumbent.json").write_text(
            json.dumps(incumbent_data, indent=2)
        )

        # Save event log
        (artifacts_dir / "events.json").write_text(
            json.dumps(experiment.event_log.to_dict(), indent=2, default=str)
        )

        # Save baseline
        if experiment.baseline:
            (artifacts_dir / "baseline.json").write_text(
                json.dumps(experiment.baseline.to_dict(), indent=2, default=str)
            )

        # Save holdout
        if experiment.holdout:
            (artifacts_dir / "holdout.json").write_text(
                json.dumps(experiment.holdout.to_dict(), indent=2, default=str)
            )

        # Save decision
        if experiment.decision:
            (artifacts_dir / "decision.json").write_text(
                json.dumps(experiment.decision.to_dict(), indent=2, default=str)
            )

        # Save metrics
        (artifacts_dir / "metrics.json").write_text(
            json.dumps(metrics.to_dict(), indent=2, default=str)
        )

        # Save validation report
        if validation_report:
            (artifacts_dir / "validation.json").write_text(
                json.dumps(validation_report.to_dict(), indent=2, default=str)
            )

        # Save experiment summary
        (artifacts_dir / "summary.json").write_text(
            json.dumps(experiment.to_dict(), indent=2, default=str)
        )

    def _save_matrix_summary(
        self,
        matrix: ExperimentMatrix,
        matrix_path: Path,
    ) -> None:
        """Save a summary of all experiments in the matrix."""
        summary = {
            "matrix_id": matrix.matrix_id,
            "created_at": matrix.created_at,
            "total_experiments": len(matrix.results),
            "experiments": [],
        }

        for result in matrix.results:
            exp_summary = {
                "spec_id": result.spec.spec_id,
                "universe": result.spec.universe,
                "trial_budget": result.spec.trial_budget,
                "max_reflection_rounds": result.spec.max_reflection_rounds,
                "seed": result.spec.seed,
                "decision_outcome": result.metrics.decision_outcome,
                "gates_passed": result.metrics.gates_passed,
                "holdout_outperformed_baseline": result.metrics.holdout_outperformed_baseline,
                "nominal_sharpe": result.metrics.nominal_vs_defensible.nominal_sharpe,
                "holdout_sharpe": result.metrics.nominal_vs_defensible.holdout_sharpe,
                "dsr": result.metrics.nominal_vs_defensible.dsr,
                "pbo": result.metrics.nominal_vs_defensible.pbo,
                "sharpe_gap": result.metrics.nominal_vs_defensible.sharpe_gap,
                "total_trials": result.metrics.trial_efficiency.total_trials,
                "evaluated_trials": result.metrics.trial_efficiency.evaluated_trials,
                "artifacts_dir": result.artifacts_dir,
            }
            summary["experiments"].append(exp_summary)

        (matrix_path / "matrix_summary.json").write_text(
            json.dumps(summary, indent=2, default=str)
        )


def run_experimental_suite(
    output_dir: str = "./experiments",
    matrix_id: Optional[str] = None,
    universes: Optional[list[list[str]]] = None,
    trial_budgets: Optional[list[int]] = None,
    reflection_rounds: Optional[list[int]] = None,
    seeds: Optional[list[int]] = None,
) -> ExperimentMatrix:
    """Run a complete experimental suite with sensible defaults."""
    if matrix_id is None:
        matrix_id = f"suite-{uuid.uuid4().hex[:8]}"

    if universes is None:
        universes = [["AAPL", "MSFT"]]

    if trial_budgets is None:
        trial_budgets = [10]

    if reflection_rounds is None:
        reflection_rounds = [1]

    if seeds is None:
        seeds = [42]

    # Generate matrix
    matrix = generate_experiment_matrix(
        matrix_id=matrix_id,
        universes=universes,
        trial_budgets=trial_budgets,
        reflection_rounds=reflection_rounds,
        seeds=seeds,
        output_dir=output_dir,
    )

    # Run experiments
    runner = ExperimentRunner(output_dir=output_dir)
    return runner.run_matrix(matrix)
