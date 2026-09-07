"""Gate-level operating characteristic analysis.

This module decomposes false acceptance behavior to understand which gate
is responsible for the observed patterns.

For every experiment, we record:

- trial_budget
- nominal_sharpe
- holdout_sharpe
- dsr
- pbo
- baseline_outperformance
- risk_gate result
- statistical_gate result
- holdout_gate result
- final_decision

Then we calculate:

- P(accept | null) — overall false acceptance rate
- P(each gate passes | null) — individual gate pass rates
- P(all prior gates pass | null) — cumulative pass rates

This tells us whether the 5% result at 50 trials is genuinely caused by
DSR/PBO becoming more conservative, by holdout behavior, by the risk gate,
or by some interaction between them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np


@dataclass(frozen=True)
class GateRecord:
    """Record of gate decisions for a single experiment."""
    experiment_id: str
    world_type: str
    signal_strength: float
    trial_budget: int
    seed: int

    # Gate results
    risk_gate_passed: bool = True
    risk_gate_reason: str = ""
    statistical_gate_passed: bool = True
    statistical_gate_reason: str = ""
    holdout_gate_passed: bool = True
    holdout_gate_reason: str = ""

    # Values
    nominal_sharpe: float = 0.0
    holdout_sharpe: float = 0.0
    dsr: Optional[float] = None
    pbo: Optional[float] = None
    baseline_outperformed: bool = False

    # Final decision
    final_decision: str = "no_strategy_passed"
    accepted: bool = False

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "world_type": self.world_type,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "seed": self.seed,
            "risk_gate_passed": self.risk_gate_passed,
            "risk_gate_reason": self.risk_gate_reason,
            "statistical_gate_passed": self.statistical_gate_passed,
            "statistical_gate_reason": self.statistical_gate_reason,
            "holdout_gate_passed": self.holdout_gate_passed,
            "holdout_gate_reason": self.holdout_gate_reason,
            "nominal_sharpe": self.nominal_sharpe,
            "holdout_sharpe": self.holdout_sharpe,
            "dsr": self.dsr,
            "pbo": self.pbo,
            "baseline_outperformed": self.baseline_outperformed,
            "final_decision": self.final_decision,
            "accepted": self.accepted,
        }


@dataclass(frozen=True)
class GateOperatingCharacteristic:
    """Operating characteristic for a single gate."""
    gate_name: str
    n_experiments: int
    n_passed: int
    pass_rate: float
    ci_lower: float
    ci_upper: float

    # Conditional probabilities
    p_pass_given_null: float = 0.0
    p_pass_given_signal: float = 0.0

    def to_dict(self) -> dict:
        return {
            "gate_name": self.gate_name,
            "n_experiments": self.n_experiments,
            "n_passed": self.n_passed,
            "pass_rate": self.pass_rate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "p_pass_given_null": self.p_pass_given_null,
            "p_pass_given_signal": self.p_pass_given_signal,
        }


@dataclass(frozen=True)
class GateAnalysisResult:
    """Complete gate analysis for a set of experiments."""
    analysis_id: str
    world_type: str
    signal_strength: float
    trial_budget: int
    n_experiments: int

    # Overall acceptance
    acceptance_rate: float = 0.0
    acceptance_ci_lower: float = 0.0
    acceptance_ci_upper: float = 0.0

    # Individual gate characteristics
    risk_gate: Optional[GateOperatingCharacteristic] = None
    statistical_gate: Optional[GateOperatingCharacteristic] = None
    holdout_gate: Optional[GateOperatingCharacteristic] = None

    # Cumulative pass rates (P(all prior gates pass | null))
    p_pass_risk: float = 0.0
    p_pass_risk_and_statistical: float = 0.0
    p_pass_risk_statistical_and_holdout: float = 0.0

    # Decomposition
    false_acceptance_explained_by_risk: float = 0.0
    false_acceptance_explained_by_statistical: float = 0.0
    false_acceptance_explained_by_holdout: float = 0.0

    def to_dict(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "world_type": self.world_type,
            "signal_strength": self.signal_strength,
            "trial_budget": self.trial_budget,
            "n_experiments": self.n_experiments,
            "acceptance_rate": self.acceptance_rate,
            "acceptance_ci_lower": self.acceptance_ci_lower,
            "acceptance_ci_upper": self.acceptance_ci_upper,
            "risk_gate": self.risk_gate.to_dict() if self.risk_gate else None,
            "statistical_gate": self.statistical_gate.to_dict() if self.statistical_gate else None,
            "holdout_gate": self.holdout_gate.to_dict() if self.holdout_gate else None,
            "p_pass_risk": self.p_pass_risk,
            "p_pass_risk_and_statistical": self.p_pass_risk_and_statistical,
            "p_pass_risk_statistical_and_holdout": self.p_pass_risk_statistical_and_holdout,
            "false_acceptance_explained_by_risk": self.false_acceptance_explained_by_risk,
            "false_acceptance_explained_by_statistical": self.false_acceptance_explained_by_statistical,
            "false_acceptance_explained_by_holdout": self.false_acceptance_explained_by_holdout,
        }


def analyze_gate_operating_characteristics(
    records: list[GateRecord],
    world_type: str = "null",
) -> list[GateAnalysisResult]:
    """Analyze gate operating characteristics across trial budgets.

    Args:
        records: List of gate records from experiments
        world_type: Type of world ("null" or "signal")

    Returns:
        List of GateAnalysisResult, one per trial budget
    """
    # Group by trial budget
    by_budget: dict[int, list[GateRecord]] = {}
    for record in records:
        by_budget.setdefault(record.trial_budget, []).append(record)

    results = []
    for budget, budget_records in sorted(by_budget.items()):
        result = _analyze_single_budget(budget_records, world_type, budget)
        results.append(result)

    return results


def _analyze_single_budget(
    records: list[GateRecord],
    world_type: str,
    trial_budget: int,
) -> GateAnalysisResult:
    """Analyze gate characteristics for a single trial budget."""
    n = len(records)
    if n == 0:
        return GateAnalysisResult(
            analysis_id=f"gate-analysis-{world_type}-b{trial_budget}",
            world_type=world_type,
            signal_strength=records[0].signal_strength if records else 0.0,
            trial_budget=trial_budget,
            n_experiments=0,
        )

    signal_strength = records[0].signal_strength

    # Overall acceptance
    accepted = sum(1 for r in records if r.accepted)
    acceptance_rate = accepted / n
    ci_lower, ci_upper = _wilson_score_interval(accepted, n)

    # Individual gate pass rates
    risk_passed = sum(1 for r in records if r.risk_gate_passed)
    statistical_passed = sum(1 for r in records if r.statistical_gate_passed)
    holdout_passed = sum(1 for r in records if r.holdout_gate_passed)

    risk_rate = risk_passed / n
    statistical_rate = statistical_passed / n
    holdout_rate = holdout_passed / n

    # Cumulative pass rates
    p_pass_risk = risk_rate
    p_pass_risk_and_statistical = sum(
        1 for r in records if r.risk_gate_passed and r.statistical_gate_passed
    ) / n
    p_pass_risk_statistical_and_holdout = sum(
        1 for r in records if r.risk_gate_passed and r.statistical_gate_passed and r.holdout_gate_passed
    ) / n

    # Decomposition: how much does each gate contribute to false acceptance prevention?
    # If a gate passes 100% of the time, it's not preventing any false acceptances
    # If a gate passes 0% of the time, it's preventing all false acceptances
    false_acceptance_explained_by_risk = 1.0 - p_pass_risk
    false_acceptance_explained_by_statistical = p_pass_risk * (1.0 - p_pass_risk_and_statistical / p_pass_risk if p_pass_risk > 0 else 0.0)
    false_acceptance_explained_by_holdout = p_pass_risk_and_statistical * (1.0 - p_pass_risk_statistical_and_holdout / p_pass_risk_and_statistical if p_pass_risk_and_statistical > 0 else 0.0)

    return GateAnalysisResult(
        analysis_id=f"gate-analysis-{world_type}-b{trial_budget}",
        world_type=world_type,
        signal_strength=signal_strength,
        trial_budget=trial_budget,
        n_experiments=n,
        acceptance_rate=acceptance_rate,
        acceptance_ci_lower=ci_lower,
        acceptance_ci_upper=ci_upper,
        risk_gate=GateOperatingCharacteristic(
            gate_name="risk",
            n_experiments=n,
            n_passed=risk_passed,
            pass_rate=risk_rate,
            ci_lower=_wilson_score_interval(risk_passed, n)[0],
            ci_upper=_wilson_score_interval(risk_passed, n)[1],
        ),
        statistical_gate=GateOperatingCharacteristic(
            gate_name="statistical",
            n_experiments=n,
            n_passed=statistical_passed,
            pass_rate=statistical_rate,
            ci_lower=_wilson_score_interval(statistical_passed, n)[0],
            ci_upper=_wilson_score_interval(statistical_passed, n)[1],
        ),
        holdout_gate=GateOperatingCharacteristic(
            gate_name="holdout",
            n_experiments=n,
            n_passed=holdout_passed,
            pass_rate=holdout_rate,
            ci_lower=_wilson_score_interval(holdout_passed, n)[0],
            ci_upper=_wilson_score_interval(holdout_passed, n)[1],
        ),
        p_pass_risk=p_pass_risk,
        p_pass_risk_and_statistical=p_pass_risk_and_statistical,
        p_pass_risk_statistical_and_holdout=p_pass_risk_statistical_and_holdout,
        false_acceptance_explained_by_risk=false_acceptance_explained_by_risk,
        false_acceptance_explained_by_statistical=false_acceptance_explained_by_statistical,
        false_acceptance_explained_by_holdout=false_acceptance_explained_by_holdout,
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


def generate_gate_analysis_report(analysis_results: list[GateAnalysisResult]) -> str:
    """Generate a human-readable gate analysis report."""
    lines = [
        "# Gate Operating Characteristic Analysis",
        "",
        f"**Analysis Date:** {datetime.now(UTC).isoformat()}",
        f"**Configurations:** {len(analysis_results)}",
        "",
        "## Acceptance Rate by Trial Budget",
        "",
        "| Budget | Accept Rate | 95% CI | P(Risk) | P(Stat) | P(Holdout) |",
        "|---|---|---|---|---|---|",
    ]

    for result in analysis_results:
        ci = f"[{result.acceptance_ci_lower:.2%}, {result.acceptance_ci_upper:.2%}]"
        lines.append(
            f"| {result.trial_budget} | {result.acceptance_rate:.2%} | {ci} | "
            f"{result.p_pass_risk:.2%} | {result.p_pass_risk_and_statistical:.2%} | "
            f"{result.p_pass_risk_statistical_and_holdout:.2%} |"
        )

    lines.extend([
        "",
        "## Gate Decomposition",
        "",
        "| Budget | Risk Explained | Stat Explained | Holdout Explained |",
        "|---|---|---|---|",
    ])

    for result in analysis_results:
        lines.append(
            f"| {result.trial_budget} | "
            f"{result.false_acceptance_explained_by_risk:.2%} | "
            f"{result.false_acceptance_explained_by_statistical:.2%} | "
            f"{result.false_acceptance_explained_by_holdout:.2%} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "### Cumulative Pass Rates",
        "",
        "- P(Risk): Probability the risk gate passes",
        "- P(Risk ∩ Stat): Probability both risk and statistical gates pass",
        "- P(Risk ∩ Stat ∩ Holdout): Probability all three gates pass",
        "",
        "### Decomposition",
        "",
        "Each 'Explained' column shows the fraction of false acceptances",
        "prevented by that gate. A gate that passes 100% of the time explains",
        "0% of false acceptance prevention (it's not filtering anything).",
        "",
        "---",
        "*Generated by SAS Gate Analysis Framework*",
    ])

    return "\n".join(lines)
