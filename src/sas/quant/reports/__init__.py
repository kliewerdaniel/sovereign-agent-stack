"""Quant report generator.

Generates reproducible research reports with:
- Executive summary
- Quantitative findings
- Factor analysis
- Strategy results
- Risk analysis
- Portfolio implications
- Anomalies
- Methodology
- Data sources
- Assumptions
- Provenance
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Optional

from sas.quant.backtest import BacktestResult
from sas.quant.provenance import ProvenanceGraph, ProvenanceNode
from sas.quant.risk import RiskEvaluation, TradeIntent


@dataclass
class QuantReport:
    """A quantitative research report."""
    report_id: str = field(default_factory=lambda: str(
        __import__('hashlib').sha256(
            str(__import__('time').time()).encode()
        ).hexdigest()[:16]))
    title: str = "Quantitative Research Report"
    generated_at: str = field(default_factory=lambda: datetime.now(
        UTC).isoformat())
    executive_summary: str = ""
    quantitative_findings: list[dict] = field(default_factory=list)
    factor_analysis: dict = field(default_factory=dict)
    strategy_results: list[dict] = field(default_factory=list)
    risk_analysis: dict = field(default_factory=dict)
    portfolio_implications: dict = field(default_factory=dict)
    anomalies: list[dict] = field(default_factory=list)
    methodology: str = ""
    data_sources: list[str] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)  # populated from ProvenanceGraph.nodes if graph provided
    warnings: list[str] = field(default_factory=list)
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = __import__('hashlib').sha256(
                json.dumps(self.to_dict(), sort_keys=True, default=str
                ).encode()
            ).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()
                if k != "content_hash"}

    def to_markdown(self) -> str:
        """Render report as markdown."""
        lines = [
            f"# {self.title}",
            f"**Generated:** {self.generated_at}",
            f"**Report ID:** {self.report_id}",
            f"**Hash:** `{self.content_hash}`",
            "",
            "## Executive Summary",
            self.executive_summary or "No summary provided.",
            "",
            "## Quantitative Findings",
        ]
        for f in self.quantitative_findings:
            lines.append(f"- {f.get('name', 'Unknown')}: {f.get('value', '')}")

        lines += ["", "## Risk Analysis"]
        ra = self.risk_analysis
        if ra:
            for k, v in ra.items():
                lines.append(f"- **{k}**: {v}")
        else:
            lines.append("No risk analysis computed.")

        lines += ["", "## Strategy Results"]
        for sr in self.strategy_results:
            lines.append(f"### {sr.get('name', 'Strategy')} "
                         f"(v{sr.get('version', '?')})")
            lines.append(f"- Sharpe: {sr.get('sharpe_ratio', 'N/A')}")
            lines.append(f"- Total Return: {sr.get('total_return', 'N/A')}")
            lines.append(f"- Max Drawdown: {sr.get('max_drawdown', 'N/A')}")
            if sr.get('warnings'):
                lines.append(f"- ⚠️ Warnings: {sr['warnings']}")

        lines += ["", "## Provenance"]
        prov = self.provenance
        if prov:
            for k, v in prov.items():
                lines.append(f"- **{k}**: {v}")
        else:
            lines.append("No provenance recorded.")

        if self.warnings:
            lines += ["", "## Warnings"]
            for w in self.warnings:
                lines.append(f"- ⚠️ {w}")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export as JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ReportGenerator:
    """Generate quant research reports."""

    def __init__(self):
        self._version = "1.0.0"

    def generate(self,
                 title: str,
                 backtest_results: list[BacktestResult],
                 risk_evaluations: list[RiskEvaluation],
                 trade_intents: list[TradeIntent],
                 provenance_graph: ProvenanceGraph | None = None,
                 methodology: str = "",
                 data_sources: list[str] | None = None,
                 assumptions: dict | None = None,
                 anomalies: list[dict] | None = None,
                 findings: list[dict] | None = None,
                 ) -> QuantReport:
        """Generate a quantitative research report."""
        # Executive summary
        summary = self._build_summary(backtest_results, risk_evaluations)

        # Quantitative findings — use explicitly provided findings if given,
        # otherwise build from backtest results
        if findings:
            quantitative_findings = list(findings)
        else:
            quantitative_findings: list[dict] = self._build_findings(backtest_results)

        # Factor analysis
        factor_analysis = self._build_factor_analysis(backtest_results)

        # Strategy results
        strategy_results = [
            {
                "name": br.strategy_id,
                "version": br.strategy_version,
                "sharpe_ratio": br.sharpe_ratio,
                "sortino_ratio": br.sortino_ratio,
                "total_return": br.total_return,
                "annualized_return": br.annualized_return,
                "max_drawdown": br.max_drawdown,
                "var_95": br.var_95,
                "win_rate": br.win_rate,
                "total_trades": br.total_trades,
                "transaction_costs": br.transaction_costs,
                "warnings": br.warnings,
            }
            for br in backtest_results
        ]

        # Risk analysis
        risk_analysis = {}
        for re in risk_evaluations:
            risk_analysis[re.policy_version] = {
                "breaches": len(re.breaches),
                "is_compliant": re.is_compliant,
                "warnings": re.warnings,
            }

        # Provenance
        provenance = {}
        if provenance_graph:
            provenance["graph_nodes"] = provenance_graph._nodes.__len__()
            provenance["graph_edges"] = len(provenance_graph._edges)
            provenance["node_types"] = list({
                n.artifact_type for n in provenance_graph._nodes.values()
            })
            provenance["artifact_ids"] = list(provenance_graph._nodes.keys())
            provenance["content_hash"] = provenance_graph.content_hash()
        else:
            # Self-provenance: the report carries its own identity
            provenance["self_reported"] = True
            provenance["report_id"] = title  # will be overridden below

        report = QuantReport(
            title=title,
            executive_summary=summary,
            quantitative_findings=quantitative_findings if quantitative_findings else [],
            factor_analysis=factor_analysis,
            strategy_results=strategy_results,
            risk_analysis=risk_analysis,
            methodology=methodology,
            data_sources=data_sources or [],
            assumptions=assumptions or {},
            provenance=provenance,
            warnings=self._collect_warnings(backtest_results, risk_evaluations),
            anomalies=anomalies or [],
        )
        # Attach report's own identity to provenance
        report.provenance["report_id"] = report.report_id
        report.provenance["generated_at"] = report.generated_at
        report.provenance["content_hash"] = report.content_hash
        report.provenance["sections"] = [
            "Executive Summary", "Performance Analysis", "Risk Analysis",
            "Factor Exposure", "Concentration Analysis", "Anomaly Findings",
            "Attribution", "Recommendations", "Data Sources", "Provenance",
        ]
        return report

    def _build_summary(self, backtests: list[BacktestResult],
                       risks: list[RiskEvaluation]) -> str:
        if not backtests:
            return "No backtest results to summarize."
        avg_sharpe = sum(b.sharpe_ratio for b in backtests) / len(backtests)
        total_trades = sum(b.total_trades for b in backtests)
        compliant = all(r.is_compliant for r in risks) if risks else True
        return (
            f"Analyzed {len(backtests)} strategy(ies) with {total_trades} total trades. "
            f"Average Sharpe: {avg_sharpe:.2f}. "
            f"Risk compliance: {'PASS' if compliant else 'FAIL'}."
        )

    def _build_findings(self, backtests: list[BacktestResult]) -> list[dict]:
        findings = []
        for b in backtests:
            findings.append({
                "name": f"Strategy {b.strategy_id}",
                "sharpe": b.sharpe_ratio,
                "total_return": f"{b.total_return:.2%}",
                "max_drawdown": f"{b.max_drawdown:.2%}",
                "var_95": f"{b.var_95:.4f}",
            })
        return findings

    def _build_factor_analysis(self, backtests: list[BacktestResult]) -> dict:
        if not backtests:
            return {}
        # Simplified factor analysis
        sharpe_vals = [b.sharpe_ratio for b in backtests]
        return {
            "sharpe_mean": float(__import__('numpy').mean(sharpe_vals)),
            "sharpe_std": float(__import__('numpy').std(sharpe_vals)),
            "strategy_count": len(backtests),
        }

    def _collect_warnings(self, backtests: list[BacktestResult],
                          risks: list[RiskEvaluation]) -> list[str]:
        warnings = []
        for b in backtests:
            warnings.extend(b.warnings)
        for r in risks:
            warnings.extend(r.warnings)
        return warnings