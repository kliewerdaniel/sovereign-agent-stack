"""Comparative analysis across experimental conditions.

Generates the analysis that exposes how the relationship between
nominal and defensible performance changes across experimental
conditions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np


@dataclass
class ComparativeFinding:
    """A single comparative finding."""
    metric: str  # e.g., "sharpe_gap", "dsr", "holdout_sharpe"
    condition: str  # e.g., "budget=10", "reflection=1"
    value: float
    comparison: str  # e.g., "budget=20", "reflection=0"
    comparison_value: float
    delta: float  # value - comparison_value
    interpretation: str

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "condition": self.condition,
            "value": self.value,
            "comparison": self.comparison,
            "comparison_value": self.comparison_value,
            "delta": self.delta,
            "interpretation": self.interpretation,
        }


@dataclass
class ComparativeAnalysis:
    """Complete comparative analysis across experimental conditions."""
    matrix_id: str
    total_experiments: int
    findings: list[ComparativeFinding] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "matrix_id": self.matrix_id,
            "total_experiments": self.total_experiments,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }


def compare_trial_budgets(results: list[dict]) -> list[ComparativeFinding]:
    """Compare metrics across different trial budgets."""
    findings: list[ComparativeFinding] = []

    # Group by budget
    by_budget: dict[int, list[dict]] = {}
    for r in results:
        budget = r.get("trial_budget", 0)
        by_budget.setdefault(budget, []).append(r)

    budgets = sorted(by_budget.keys())
    if len(budgets) < 2:
        return findings

    # Compare each pair
    for i in range(len(budgets)):
        for j in range(i + 1, len(budgets)):
            b1, b2 = budgets[i], budgets[j]
            group1 = by_budget[b1]
            group2 = by_budget[b2]

            # Compare average Sharpe gap
            gap1 = np.mean([r.get("sharpe_gap", 0) or 0 for r in group1])
            gap2 = np.mean([r.get("sharpe_gap", 0) or 0 for r in group2])

            findings.append(ComparativeFinding(
                metric="sharpe_gap",
                condition=f"budget={b1}",
                value=float(gap1),
                comparison=f"budget={b2}",
                comparison_value=float(gap2),
                delta=float(gap1 - gap2),
                interpretation=(
                    f"Increasing trial budget from {b1} to {b2} "
                    f"{'increased' if gap2 > gap1 else 'decreased'} "
                    f"the average Sharpe gap by {abs(gap2 - gap1):.4f}"
                ),
            ))

            # Compare average DSR
            dsr1 = np.mean([r.get("dsr") or 0 for r in group1])
            dsr2 = np.mean([r.get("dsr") or 0 for r in group2])

            findings.append(ComparativeFinding(
                metric="dsr",
                condition=f"budget={b1}",
                value=float(dsr1),
                comparison=f"budget={b2}",
                comparison_value=float(dsr2),
                delta=float(dsr1 - dsr2),
                interpretation=(
                    f"Increasing trial budget from {b1} to {b2} "
                    f"{'increased' if dsr2 > dsr1 else 'decreased'} "
                    f"the average DSR by {abs(dsr2 - dsr1):.4f}"
                ),
            ))

            # Compare average holdout Sharpe
            hs1 = np.mean([r.get("holdout_sharpe") or 0 for r in group1])
            hs2 = np.mean([r.get("holdout_sharpe") or 0 for r in group2])

            findings.append(ComparativeFinding(
                metric="holdout_sharpe",
                condition=f"budget={b1}",
                value=float(hs1),
                comparison=f"budget={b2}",
                comparison_value=float(hs2),
                delta=float(hs1 - hs2),
                interpretation=(
                    f"Increasing trial budget from {b1} to {b2} "
                    f"{'increased' if hs2 > hs1 else 'decreased'} "
                    f"the average holdout Sharpe by {abs(hs2 - hs1):.4f}"
                ),
            ))

    return findings


def compare_reflection_settings(results: list[dict]) -> list[ComparativeFinding]:
    """Compare metrics across different reflection settings."""
    findings: list[ComparativeFinding] = []

    # Group by reflection rounds
    by_reflection: dict[int, list[dict]] = {}
    for r in results:
        ref = r.get("max_reflection_rounds", 0)
        by_reflection.setdefault(ref, []).append(r)

    reflections = sorted(by_reflection.keys())
    if len(reflections) < 2:
        return findings

    for i in range(len(reflections)):
        for j in range(i + 1, len(reflections)):
            r1, r2 = reflections[i], reflections[j]
            group1 = by_reflection[r1]
            group2 = by_reflection[r2]

            # Compare holdout Sharpe
            hs1 = np.mean([r.get("holdout_sharpe") or 0 for r in group1])
            hs2 = np.mean([r.get("holdout_sharpe") or 0 for r in group2])

            findings.append(ComparativeFinding(
                metric="holdout_sharpe",
                condition=f"reflection={r1}",
                value=float(hs1),
                comparison=f"reflection={r2}",
                comparison_value=float(hs2),
                delta=float(hs1 - hs2),
                interpretation=(
                    f"Changing reflection from {r1} to {r2} "
                    f"{'increased' if hs2 > hs1 else 'decreased'} "
                    f"the average holdout Sharpe by {abs(hs2 - hs1):.4f}"
                ),
            ))

    return findings


def compare_universes(results: list[dict]) -> list[ComparativeFinding]:
    """Compare metrics across different universes."""
    findings: list[ComparativeFinding] = []

    # Group by universe (as string key)
    by_universe: dict[str, list[dict]] = {}
    for r in results:
        u = ",".join(r.get("universe", []))
        by_universe.setdefault(u, []).append(r)

    universes = sorted(by_universe.keys())
    if len(universes) < 2:
        return findings

    for i in range(len(universes)):
        for j in range(i + 1, len(universes)):
            u1, u2 = universes[i], universes[j]
            group1 = by_universe[u1]
            group2 = by_universe[u2]

            # Compare acceptance rate
            ar1 = np.mean([1 if r.get("gates_passed") else 0 for r in group1])
            ar2 = np.mean([1 if r.get("gates_passed") else 0 for r in group2])

            findings.append(ComparativeFinding(
                metric="acceptance_rate",
                condition=f"universe={u1}",
                value=float(ar1),
                comparison=f"universe={u2}",
                comparison_value=float(ar2),
                delta=float(ar1 - ar2),
                interpretation=(
                    f"Universe {u1} had {ar1:.0%} acceptance vs "
                    f"{u2} had {ar2:.0%} acceptance"
                ),
            ))

    return findings


def analyze_matrix(matrix_summary_path: str) -> ComparativeAnalysis:
    """Analyze a completed experiment matrix."""
    path = Path(matrix_summary_path)
    summary = json.loads(path.read_text())

    experiments = summary.get("experiments", [])

    # Generate findings
    findings: list[ComparativeFinding] = []
    findings.extend(compare_trial_budgets(experiments))
    findings.extend(compare_reflection_settings(experiments))
    findings.extend(compare_universes(experiments))

    # Summary statistics
    summary_stats = {
        "total_experiments": len(experiments),
        "acceptance_rate": float(np.mean([
            1 if e.get("gates_passed") else 0 for e in experiments
        ])),
        "holdout_outperformance_rate": float(np.mean([
            1 if e.get("holdout_outperformed_baseline") else 0 for e in experiments
        ])),
        "average_nominal_sharpe": float(np.mean([
            e.get("nominal_sharpe", 0) for e in experiments
        ])),
        "average_holdout_sharpe": float(np.mean([
            e.get("holdout_sharpe") or 0 for e in experiments
        ])),
        "average_sharpe_gap": float(np.mean([
            e.get("sharpe_gap") or 0 for e in experiments
        ])),
        "average_dsr": float(np.mean([
            e.get("dsr") or 0 for e in experiments
        ])),
    }

    analysis = ComparativeAnalysis(
        matrix_id=summary.get("matrix_id", "unknown"),
        total_experiments=len(experiments),
        findings=findings,
        summary=summary_stats,
    )

    # Save analysis
    analysis_path = path.parent / "comparative_analysis.json"
    analysis_path.write_text(json.dumps(analysis.to_dict(), indent=2, default=str))

    return analysis


def generate_report(analysis: ComparativeAnalysis) -> str:
    """Generate a human-readable comparative report."""
    lines = [
        "# Experimental Analysis: Governed Research Performance",
        "",
        f"**Matrix ID:** {analysis.matrix_id}",
        f"**Total Experiments:** {analysis.total_experiments}",
        "",
        "## Summary Statistics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
    ]

    for k, v in analysis.summary.items():
        if isinstance(v, float):
            lines.append(f"| {k} | {v:.4f} |")
        else:
            lines.append(f"| {k} | {v} |")

    lines.extend(["", "## Findings", ""])

    if not analysis.findings:
        lines.append("No comparative findings available.")
    else:
        for f in analysis.findings:
            lines.extend([
                f"### {f.metric}",
                "",
                f"**{f.condition}** vs **{f.comparison}**",
                "",
                f"- {f.condition}: {f.value:.4f}",
                f"- {f.comparison}: {f.comparison_value:.4f}",
                f"- Delta: {f.delta:+.4f}",
                f"- {f.interpretation}",
                "",
            ])

    lines.extend(["", "---", "*Generated by SAS Experimental Analysis*"])

    return "\n".join(lines)
