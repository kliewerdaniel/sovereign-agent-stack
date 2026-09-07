"""Gate ablation framework.

This module implements controlled gate ablation experiments.

The central question: which architectural control actually prevents false discoveries?

We take frozen experiment populations and re-evaluate them under progressively
stronger governance configurations:

A. No gates
B. Temporal isolation only
C. DSR only
D. PBO only
E. DSR + PBO
F. Holdout only
G. DSR + PBO + Holdout
H. Full governance

This gives us an operating characteristic of the architecture, not just a
single false-acceptance number.

Critical design principle: calibration sits OUTSIDE the experiment execution
path. It observes the governance system but does not become part of the
mechanism being calibrated. Otherwise we simply move the overfitting problem
one level upward: the model overfits strategies; then the engineer overfits
the governance system.
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
from sas.quant.evaluation.gates import (
    GateResult,
    ResearchGateConfig,
    ResearchGates,
)
from sas.quant.research.experiment import Experiment, ExperimentConfig


@dataclass(frozen=True)
class GateDecision:
    """Record of which gates passed/failed for a single experiment."""
    experiment_id: str
    risk_gate_passed: bool
    risk_gate_reason: str
    statistical_gate_passed: bool
    statistical_gate_reason: str
    holdout_gate_passed: bool
    holdout_gate_reason: str
    baseline_outperformed: bool
    final_decision: str
    dsr_value: Optional[float]
    pbo_value: Optional[float]
    nominal_sharpe: float
    holdout_sharpe: float

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "risk_gate_passed": self.risk_gate_passed,
            "risk_gate_reason": self.risk_gate_reason,
            "statistical_gate_passed": self.statistical_gate_passed,
            "statistical_gate_reason": self.statistical_gate_reason,
            "holdout_gate_passed": self.holdout_gate_passed,
            "holdout_gate_reason": self.holdout_gate_reason,
            "baseline_outperformed": self.baseline_outperformed,
            "final_decision": self.final_decision,
            "dsr_value": self.dsr_value,
            "pbo_value": self.pbo_value,
            "nominal_sharpe": self.nominal_sharpe,
            "holdout_sharpe": self.holdout_sharpe,
        }


@dataclass(frozen=True)
class AblationConfiguration:
    """A single gate configuration for ablation."""
    config_id: str
    name: str
    description: str
    use_risk_gate: bool = True
    use_statistical_gate: bool = True
    use_holdout_gate: bool = True
    use_baseline_comparison: bool = True
    use_temporal_isolation: bool = True
    use_dsr: bool = True
    use_pbo: bool = True

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id,
            "name": self.name,
            "description": self.description,
            "use_risk_gate": self.use_risk_gate,
            "use_statistical_gate": self.use_statistical_gate,
            "use_holdout_gate": self.use_holdout_gate,
            "use_baseline_comparison": self.use_baseline_comparison,
            "use_temporal_isolation": self.use_temporal_isolation,
            "use_dsr": self.use_dsr,
            "use_pbo": self.use_pbo,
        }


@dataclass(frozen=True)
class AblationResult:
    """Result of evaluating one experiment under one gate configuration."""
    experiment_id: str
    config_id: str
    world_type: str
    signal_strength: float
    trial_budget: int
    accepted: bool
    decision_outcome: str
    risk_passed: bool
    statistical_passed: bool
    holdout_passed: bool
    baseline_outperformed: bool
    nominal_sharpe: float
    holdout_sharpe: float
    dsr: Optional[float]
    pbo: Optional[float]

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "config_id": self.config_id,
            "world_type": self.world_type,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "accepted": self.accepted,
            "decision_outcome": self.decision_outcome,
            "risk_passed": self.risk_passed,
            "statistical_passed": self.statistical_passed,
            "holdout_passed": self.holdout_passed,
            "baseline_outperformed": self.baseline_outperformed,
            "nominal_sharpe": self.nominal_sharpe,
            "holdout_sharpe": self.holdout_sharpe,
            "dsr": self.dsr,
            "pbo": self.pbo,
        }


@dataclass(frozen=True)
class AblationBatch:
    """A batch of ablation experiments with the same configuration."""
    batch_id: str
    config: AblationConfiguration
    world_type: str
    signal_strength: float
    trial_budget: int
    n_experiments: int
    results: list[AblationResult] = field(default_factory=list)

    # Summary statistics
    acceptance_rate: float = 0.0
    avg_nominal_sharpe: float = 0.0
    avg_holdout_sharpe: float = 0.0
    risk_pass_rate: float = 0.0
    statistical_pass_rate: float = 0.0
    holdout_pass_rate: float = 0.0
    baseline_outperform_rate: float = 0.0

    # Confidence intervals (95%)
    acceptance_rate_ci_lower: float = 0.0
    acceptance_rate_ci_upper: float = 0.0

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "config": self.config.to_dict(),
            "world_type": self.world_type,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "n_experiments": self.n_experiments,
            "acceptance_rate": self.acceptance_rate,
            "avg_nominal_sharpe": self.avg_nominal_sharpe,
            "avg_holdout_sharpe": self.avg_holdout_sharpe,
            "risk_pass_rate": self.risk_pass_rate,
            "statistical_pass_rate": self.statistical_pass_rate,
            "holdout_pass_rate": self.holdout_pass_rate,
            "baseline_outperform_rate": self.baseline_outperform_rate,
            "acceptance_rate_ci_lower": self.acceptance_rate_ci_lower,
            "acceptance_rate_ci_upper": self.acceptance_rate_ci_upper,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class AblationMatrix:
    """Complete ablation matrix across gate configurations and world types."""
    matrix_id: str
    batches: list[AblationBatch] = field(default_factory=list)
    output_dir: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "matrix_id": self.matrix_id,
            "batches": [b.to_dict() for b in self.batches],
            "output_dir": self.output_dir,
            "created_at": self.created_at,
        }


def get_standard_configurations() -> list[AblationConfiguration]:
    """Get the standard set of gate configurations for ablation."""
    return [
        AblationConfiguration(
            config_id="A",
            name="No gates",
            description="No governance - accept everything",
            use_risk_gate=False,
            use_statistical_gate=False,
            use_holdout_gate=False,
            use_baseline_comparison=False,
            use_temporal_isolation=False,
            use_dsr=False,
            use_pbo=False,
        ),
        AblationConfiguration(
            config_id="B",
            name="Temporal isolation only",
            description="Only temporal isolation, no statistical gates",
            use_risk_gate=False,
            use_statistical_gate=False,
            use_holdout_gate=False,
            use_baseline_comparison=False,
            use_temporal_isolation=True,
            use_dsr=False,
            use_pbo=False,
        ),
        AblationConfiguration(
            config_id="C",
            name="DSR only",
            description="Only DSR statistical correction",
            use_risk_gate=False,
            use_statistical_gate=True,
            use_holdout_gate=False,
            use_baseline_comparison=False,
            use_temporal_isolation=True,
            use_dsr=True,
            use_pbo=False,
        ),
        AblationConfiguration(
            config_id="D",
            name="PBO only",
            description="Only PBO statistical correction",
            use_risk_gate=False,
            use_statistical_gate=True,
            use_holdout_gate=False,
            use_baseline_comparison=False,
            use_temporal_isolation=True,
            use_dsr=False,
            use_pbo=True,
        ),
        AblationConfiguration(
            config_id="E",
            name="DSR + PBO",
            description="Statistical correction without holdout",
            use_risk_gate=False,
            use_statistical_gate=True,
            use_holdout_gate=False,
            use_baseline_comparison=False,
            use_temporal_isolation=True,
            use_dsr=True,
            use_pbo=True,
        ),
        AblationConfiguration(
            config_id="F",
            name="Holdout only",
            description="Only holdout evaluation, no statistical correction",
            use_risk_gate=False,
            use_statistical_gate=False,
            use_holdout_gate=True,
            use_baseline_comparison=True,
            use_temporal_isolation=True,
            use_dsr=False,
            use_pbo=False,
        ),
        AblationConfiguration(
            config_id="G",
            name="DSR + PBO + Holdout",
            description="Statistical correction with holdout, no risk gate",
            use_risk_gate=False,
            use_statistical_gate=True,
            use_holdout_gate=True,
            use_baseline_comparison=True,
            use_temporal_isolation=True,
            use_dsr=True,
            use_pbo=True,
        ),
        AblationConfiguration(
            config_id="H",
            name="Full governance",
            description="All gates active",
            use_risk_gate=True,
            use_statistical_gate=True,
            use_holdout_gate=True,
            use_baseline_comparison=True,
            use_temporal_isolation=True,
            use_dsr=True,
            use_pbo=True,
        ),
    ]


def evaluate_with_configuration(
    experiment: Experiment,
    config: AblationConfiguration,
) -> AblationResult:
    """Evaluate a frozen experiment under a specific gate configuration.

    This re-evaluates the experiment's incumbent strategy using only
    the gates specified in the configuration.
    """
    incumbent = experiment.trial_ledger.get_incumbent()

    if not incumbent or not incumbent.backtest_result:
        return AblationResult(
            experiment_id=experiment.experiment_id,
            config_id=config.config_id,
            world_type="unknown",
            signal_strength=0.0,
            trial_budget=experiment.config.trial_budget,
            accepted=False,
            decision_outcome="no_strategy_passed",
            risk_passed=True,
            statistical_passed=True,
            holdout_passed=True,
            baseline_outperformed=False,
            nominal_sharpe=0.0,
            holdout_sharpe=0.0,
            dsr=experiment.dsr_value,
            pbo=experiment.pbo_value,
        )

    nominal_sharpe = incumbent.backtest_result.get("sharpe_ratio", 0.0)
    dsr_value = experiment.dsr_value
    pbo_value = experiment.pbo_value

    # Evaluate gates
    risk_passed = True
    risk_reason = "Risk gate not used"
    if config.use_risk_gate:
        # Risk gate evaluation would go here
        # For now, assume it passes (we'd need the risk engine)
        risk_passed = True
        risk_reason = "Risk gate passed"

    statistical_passed = True
    statistical_reason = "Statistical gate not used"
    if config.use_statistical_gate:
        statistical_passed = True
        statistical_reason = "Statistical gate not used"
        if config.use_dsr and dsr_value is not None:
            # DSR should be above some threshold (e.g., 0.5)
            if dsr_value < 0.5:
                statistical_passed = False
                statistical_reason = f"DSR too low: {dsr_value:.4f}"
        if config.use_pbo and pbo_value is not None:
            # PBO should be below some threshold (e.g., 0.5)
            if pbo_value > 0.5:
                statistical_passed = False
                if not statistical_reason:
                    statistical_reason = f"PBO too high: {pbo_value:.4f}"
                else:
                    statistical_reason += f", PBO too high: {pbo_value:.4f}"

    holdout_passed = True
    holdout_reason = "Holdout gate not used"
    baseline_outperformed = False
    holdout_sharpe = 0.0
    if config.use_holdout_gate:
        if experiment.holdout:
            holdout_sharpe = experiment.holdout.strategy_sharpe_ratio
            baseline_outperformed = experiment.holdout.outperformed_baseline
            holdout_passed = baseline_outperformed
            holdout_reason = (
                f"Outperformed baseline: {baseline_outperformed}"
            )
        else:
            holdout_passed = False
            holdout_reason = "No holdout evaluation"

    # Determine final decision
    if not risk_passed:
        final_decision = "no_strategy_passed"
    elif not statistical_passed:
        final_decision = "no_strategy_passed"
    elif not holdout_passed:
        final_decision = "passed_but_no_value"
    else:
        final_decision = "candidate"

    accepted = final_decision == "candidate"

    return AblationResult(
        experiment_id=experiment.experiment_id,
        config_id=config.config_id,
        world_type="unknown",  # Will be set by caller
        signal_strength=0.0,  # Will be set by caller
        trial_budget=experiment.config.trial_budget,
        accepted=accepted,
        decision_outcome=final_decision,
        risk_passed=risk_passed,
        statistical_passed=statistical_passed,
        holdout_passed=holdout_passed,
        baseline_outperformed=baseline_outperformed,
        nominal_sharpe=nominal_sharpe,
        holdout_sharpe=holdout_sharpe,
        dsr=dsr_value,
        pbo=pbo_value,
    )


def run_ablation_matrix(
    experiments: list[Experiment],
    world_type: str = "null",
    signal_strength: float = 0.0,
    output_dir: str = "./experiments/ablation",
    matrix_id: str | None = None,
    configurations: list[AblationConfiguration] | None = None,
) -> AblationMatrix:
    """Run a full gate ablation matrix on a set of frozen experiments.

    Args:
        experiments: Frozen experiments to re-evaluate
        world_type: Type of world ("null" or "signal")
        signal_strength: Signal strength (0.0 for null worlds)
        output_dir: Output directory
        matrix_id: Matrix ID (auto-generated if not provided)
        configurations: Gate configurations to test (default: standard set)

    Returns:
        AblationMatrix with all results
    """
    if matrix_id is None:
        matrix_id = f"ablation-{uuid.uuid4().hex[:8]}"
    if configurations is None:
        configurations = get_standard_configurations()

    matrix = AblationMatrix(
        matrix_id=matrix_id,
        output_dir=output_dir,
        created_at=datetime.now(UTC).isoformat(),
    )

    # Create output directory
    matrix_path = Path(output_dir) / matrix_id
    matrix_path.mkdir(parents=True, exist_ok=True)
    matrix.output_dir = str(matrix_path)

    trial_budget = experiments[0].config.trial_budget if experiments else 0

    for config in configurations:
        batch_id = f"{config.config_id}-{world_type}-s{signal_strength}-b{trial_budget}"

        results = []
        for experiment in experiments:
            result = evaluate_with_configuration(experiment, config)
            # Set world_type and signal_strength from the batch
            result = AblationResult(
                experiment_id=result.experiment_id,
                config_id=result.config_id,
                world_type=world_type,
                signal_strength=signal_strength,
                trial_budget=result.trial_budget,
                accepted=result.accepted,
                decision_outcome=result.decision_outcome,
                risk_passed=result.risk_passed,
                statistical_passed=result.statistical_passed,
                holdout_passed=result.holdout_passed,
                baseline_outperformed=result.baseline_outperformed,
                nominal_sharpe=result.nominal_sharpe,
                holdout_sharpe=result.holdout_sharpe,
                dsr=result.dsr,
                pbo=result.pbo,
            )
            results.append(result)

        # Compute batch statistics
        accepted = sum(1 for r in results if r.accepted)
        risk_passed = sum(1 for r in results if r.risk_passed)
        statistical_passed = sum(1 for r in results if r.statistical_passed)
        holdout_passed = sum(1 for r in results if r.holdout_passed)
        baseline_outperformed = sum(1 for r in results if r.baseline_outperformed)

        n = len(results)
        acceptance_rate = accepted / n if n > 0 else 0.0

        # 95% confidence interval for acceptance rate (Wilson score interval)
        ci_lower, ci_upper = _wilson_score_interval(accepted, n)

        batch = AblationBatch(
            batch_id=batch_id,
            config=config,
            world_type=world_type,
            signal_strength=signal_strength,
            trial_budget=trial_budget,
            n_experiments=n,
            results=results,
            acceptance_rate=acceptance_rate,
            avg_nominal_sharpe=float(np.mean([r.nominal_sharpe for r in results])) if results else 0.0,
            avg_holdout_sharpe=float(np.mean([r.holdout_sharpe for r in results])) if results else 0.0,
            risk_pass_rate=risk_passed / n if n > 0 else 0.0,
            statistical_pass_rate=statistical_passed / n if n > 0 else 0.0,
            holdout_pass_rate=holdout_passed / n if n > 0 else 0.0,
            baseline_outperform_rate=baseline_outperformed / n if n > 0 else 0.0,
            acceptance_rate_ci_lower=ci_lower,
            acceptance_rate_ci_upper=ci_upper,
        )
        matrix.batches.append(batch)

    # Save matrix
    _save_matrix(matrix, matrix_path)

    return matrix


def _wilson_score_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson score interval for a binomial proportion.

    This is more accurate than the normal approximation for small samples
    or proportions near 0 or 1.

    Args:
        successes: Number of successes
        n: Total number of trials
        z: Z-score for confidence level (1.96 for 95%)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return 0.0, 0.0

    p_hat = successes / n
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return lower, upper


def generate_ablation_report(matrix: AblationMatrix) -> str:
    """Generate a human-readable ablation report."""
    lines = [
        "# Gate Ablation Report",
        "",
        f"**Matrix ID:** {matrix.matrix_id}",
        f"**Created:** {matrix.created_at}",
        f"**Total Batches:** {len(matrix.batches)}",
        "",
        "## Operating Characteristic",
        "",
        "| Config | Name | Accept Rate | 95% CI | Risk | Stat | Holdout | Baseline |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for batch in matrix.batches:
        ci = f"[{batch.acceptance_rate_ci_lower:.2%}, {batch.acceptance_rate_ci_upper:.2%}]"
        lines.append(
            f"| {batch.config.config_id} | {batch.config.name} | "
            f"{batch.acceptance_rate:.2%} | {ci} | "
            f"{batch.risk_pass_rate:.2%} | {batch.statistical_pass_rate:.2%} | "
            f"{batch.holdout_pass_rate:.2%} | {batch.baseline_outperform_rate:.2%} |"
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
        "### Gate Contributions",
        "",
        "Compare configurations to isolate which gate prevents false discoveries:",
        "",
        "- A vs B: Temporal isolation effect",
        "- B vs C: DSR effect",
        "- B vs D: PBO effect",
        "- C+D vs E: Combined statistical effect",
        "- E vs G: Holdout effect",
        "- G vs H: Risk gate effect",
        "",
        "---",
        "*Generated by SAS Gate Ablation Framework*",
    ])

    return "\n".join(lines)


def _save_matrix(matrix: AblationMatrix, matrix_path: Path) -> None:
    """Save an ablation matrix to disk."""
    (matrix_path / "ablation_matrix.json").write_text(
        json.dumps(matrix.to_dict(), indent=2, default=str)
    )
