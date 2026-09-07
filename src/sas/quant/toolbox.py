
"""
QuantToolbox — real tool implementations for Sovereign Quant.

Connects world tool names to actual quant engine, data providers,
backtest engine, risk engine, and provenance.  Every tool call is
optionally provenance-tracked.

This is the bridge between the evaluation framework (worlds, tasks,
rubrics) and the actual deterministic computation.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from sas.quant.backtest import BacktestConfig, BacktestEngine, BacktestResult
from sas.quant.engine import EngineConfig, QuantEngine
from sas.quant.market import MarketDataProvider
from sas.quant.provenance import ProvenanceGraph, content_hash, now_iso
from sas.quant.risk import RiskEngine, RiskEvaluation, RiskPolicy
from sas.quant.world import ExecutionRun, TrajectoryStep

# ── ToolDefinition ───────────────────────────────────────────────────────────

@dataclass
class ToolDefinition:
    """A tool that the agent can call, with its real implementation."""

    name: str
    description: str
    capability_required: str | None = None
    read_only: bool = True
    handler: Callable[..., Any] = field(default=lambda **kw: None)
    produces_artifact_type: str | None = None  # e.g. "computation", "report", "factor_analysis"

    def __call__(self, run: ExecutionRun, **kwargs) -> Any:
        """Call the tool, record the step in the trajectory, optionally emit provenance."""
        # Check capability if required
        if self.capability_required:
            agent_caps = self._agent_capabilities(run)
            if not agent_caps.get(self.capability_required, False):
                step = TrajectoryStep(
                    step=len(run.steps),
                    agent=run.agent_name,
                    model=run.model,
                    action="denial",
                    tool=self.name,
                    tool_arguments=kwargs,
                    capability=self.capability_required,
                    policy_decision="denied",
                    denial_reason=f"agent lacks capability: {self.capability_required}",
                )
                run.add_step(step)
                run.record_authority_violation(
                    agent=run.agent_name,
                    capability=self.capability_required,
                    attempted_action=self.name,
                    reason=f"agent lacks capability: {self.capability_required}",
                )
                raise PermissionError(f"Capability required: {self.capability_required}")

        # Record the tool call step
        step = TrajectoryStep(
            step=len(run.steps),
            agent=run.agent_name,
            model=run.model,
            action="tool_call",
            tool=self.name,
            tool_arguments=kwargs,
            capability=self.capability_required or "",
            policy_decision="allowed",
        )
        run.add_step(step)
        run.tool_calls += 1

        # Execute
        try:
            result = self.handler(**kwargs)
            step.tool_result = result
            step.action = "tool_result"

            # If this tool produces an artifact, track it
            if self.produces_artifact_type and result is not None:
                artifact_id = self._register_artifact(run, self.produces_artifact_type, result)
                step.artifact_created = artifact_id

            return result
        except Exception as e:
            step.action = "error"
            step.tool_result = str(e)[:2000]
            run.errors.append(str(e))
            raise


    def _agent_capabilities(self, run: ExecutionRun) -> dict:
        """Extract agent capabilities from the world (if available)."""
        # The run doesn't carry capabilities directly — they come from the world.
        # For now, check against the agent's known capabilities.
        # In production, the ModelAdapter would pass capabilities in context.
        from sas.quant.agents import quant_coordinator
        # Default to quant_coordinator capabilities for testing
        caps = quant_coordinator().capabilities.__dict__
        return {k: v for k, v in caps.items() if v}

    def _register_artifact(self, run: ExecutionRun, artifact_type: str, result: Any) -> str:
        """Register a produced artifact in the run's artifact store."""
        artifact_id = str(uuid.uuid4())[:12]
        artifact_dict = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "producer": run.agent_name,
            "model": run.model,
            "created_at": now_iso(),
            "result": result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result),
            "content_hash": content_hash(result if isinstance(result, dict) else {"value": str(result)}),
        }
        run.artifacts[artifact_id] = artifact_dict
        return artifact_id


# ── Toolbox ──────────────────────────────────────────────────────────────────

class QuantToolbox:
    """Collection of real quant tool implementations.

    Tools are organized by domain:
    - market_data: price retrieval, validation
    - computation: returns, risk metrics, factor exposure, attribution
    - backtest: strategy backtesting
    - risk: policy evaluation
    - report: report generation
    - provenance: provenance tracing
    """

    def __init__(self,
                 data_provider: MarketDataProvider | None = None,
                 engine: QuantEngine | None = None,
                 backtest_engine: BacktestEngine | None = None,
                 risk_engine: RiskEngine | None = None,
                 provenance_graph: ProvenanceGraph | None = None,
                 portfolio: dict | None = None,
                 ):
        self.data_provider = data_provider
        self.engine = engine or QuantEngine()
        self.backtest_engine = backtest_engine or BacktestEngine()
        self.risk_engine = risk_engine or RiskEngine()
        self.provenance_graph = provenance_graph or ProvenanceGraph()
        self.portfolio = portfolio or {}

        self._tools: dict[str, ToolDefinition] = {}
        self._build_tools()

    def _build_tools(self) -> None:
        """Register all available tools with their implementations."""

        # ── Market Data Tools ──

        self.register(
            ToolDefinition(
                name="get_prices",
                description="Get historical price data for a symbol",
                capability_required=None,
                read_only=True,
                produces_artifact_type="market_data",
                handler=self._get_prices,
            )
        )

        self.register(
            ToolDefinition(
                name="get_portfolio",
                description="Get current portfolio holdings and exposure",
                capability_required=None,
                read_only=True,
                produces_artifact_type="portfolio_snapshot",
                handler=self._get_portfolio,
            )
        )

        self.register(
            ToolDefinition(
                name="get_positions",
                description="Get current positions for a symbol",
                capability_required=None,
                read_only=True,
                handler=self._get_positions,
            )
        )

        self.register(
            ToolDefinition(
                name="validate_data",
                description="Validate market data quality for a symbol",
                capability_required=None,
                read_only=True,
                produces_artifact_type="data_validation",
                handler=self._validate_data,
            )
        )

        self.register(
            ToolDefinition(
                name="dataset_info",
                description="Get information about a dataset",
                capability_required=None,
                read_only=True,
                handler=self._dataset_info,
            )
        )

        # ── Computation Tools ──

        self.register(
            ToolDefinition(
                name="compute_returns",
                description="Compute return series from price data",
                capability_required=None,
                read_only=True,
                produces_artifact_type="computation",
                handler=self._compute_returns,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_risk_metrics",
                description="Compute Sharpe, volatility, drawdown, VaR, beta for a return series",
                capability_required=None,
                read_only=True,
                produces_artifact_type="computation",
                handler=self._compute_risk_metrics,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_portfolio_returns",
                description="Compute portfolio weighted returns from constituent returns",
                capability_required=None,
                read_only=True,
                produces_artifact_type="computation",
                handler=self._compute_portfolio_returns,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_factor_exposure",
                description="Run factor regression on portfolio returns",
                capability_required=None,
                read_only=True,
                produces_artifact_type="factor_analysis",
                handler=self._compute_factor_exposure,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_attribution",
                description="Compute performance attribution by position and factor",
                capability_required=None,
                read_only=True,
                produces_artifact_type="attribution",
                handler=self._compute_attribution,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_concentration",
                description="Compute single-name and sector concentration vs policy limits",
                capability_required=None,
                read_only=True,
                produces_artifact_type="concentration_analysis",
                handler=self._compute_concentration,
            )
        )

        self.register(
            ToolDefinition(
                name="detect_anomalies",
                description="Detect anomalies in portfolio behavior (drawdowns, volume spikes, etc.)",
                capability_required=None,
                read_only=True,
                produces_artifact_type="anomaly_report",
                handler=self._detect_anomalies,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_beta",
                description="Compute beta of portfolio returns vs benchmark",
                capability_required=None,
                read_only=True,
                produces_artifact_type="computation",
                handler=self._compute_beta,
            )
        )

        self.register(
            ToolDefinition(
                name="compute_var_cvar",
                description="Compute Value at Risk and Conditional VaR",
                capability_required=None,
                read_only=True,
                produces_artifact_type="computation",
                handler=self._compute_var_cvar,
            )
        )

        # ── Backtest Tool ──

        self.register(
            ToolDefinition(
                name="compute_backtest",
                description="Run a deterministic backtest for a strategy",
                capability_required="backtest_execute",
                read_only=False,
                produces_artifact_type="backtest_result",
                handler=self._compute_backtest,
            )
        )

        # ── Risk Tool ──

        self.register(
            ToolDefinition(
                name="evaluate_risk",
                description="Evaluate portfolio or strategy against risk policy",
                capability_required="risk_evaluate",
                read_only=False,
                produces_artifact_type="risk_evaluation",
                handler=self._evaluate_risk,
            )
        )

        # ── Report Tool ──

        self.register(
            ToolDefinition(
                name="build_report",
                description="Generate a research report from findings and artifacts",
                capability_required=None,
                read_only=False,
                produces_artifact_type="report",
                handler=self._build_report,
            )
        )

        # ── Provenance Tool ──

        self.register(
            ToolDefinition(
                name="get_provenance",
                description="Trace provenance of an artifact",
                capability_required=None,
                read_only=True,
                handler=self._get_provenance,
            )
        )

        # ── Strategy Proposal Tool ──

        self.register(
            ToolDefinition(
                name="propose_strategy",
                description="Propose a trading strategy with full parameters. Call this to formalize a strategy idea before backtesting.",
                capability_required="strategy_propose",
                read_only=False,
                produces_artifact_type="strategy_proposal",
                handler=self._propose_strategy,
            )
        )

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """List all registered tools as dicts for model context."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "capability_required": t.capability_required or "",
                "read_only": t.read_only,
                "produces_artifact_type": t.produces_artifact_type or "",
            }
            for t in self._tools.values()
        ]

    def call(self, run: ExecutionRun, tool_name: str, **kwargs) -> Any:
        """Call a tool through the toolbox, with trajectory recording."""
        tool = self._tools.get(tool_name)
        if tool is None:
            run.errors.append(f"Unknown tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")
        return tool(run, **kwargs)

    # ── Tool Implementations ────────────────────────────────────────────────

    def _get_prices(self, symbol: str, start: str, end: str) -> dict:
        """Get historical prices for a symbol."""
        if self.data_provider is None:
            return {"error": "no data provider configured"}
        df = self.data_provider.get_prices(symbol, start, end)
        if df.empty:
            return {"symbol": symbol, "start": start, "end": end, "rows": 0, "data": []}
        records = df.reset_index().to_dict("records")
        # Convert timestamps to strings
        for r in records:
            if "date" in r and not isinstance(r["date"], str):
                r["date"] = str(r["date"].date())
        return {
            "symbol": symbol,
            "start": start,
            "end": end,
            "rows": len(records),
            "data": records,
        }

    def _get_portfolio(self) -> dict:
        """Get current portfolio holdings."""
        return {
            "portfolio": self.portfolio,
            "total_value": self._compute_portfolio_value(),
        }

    def _get_positions(self, symbol: str | None = None) -> dict:
        """Get positions, optionally filtered by symbol."""
        positions = self.portfolio.get("positions", {})
        if symbol:
            return {"symbol": symbol, "position": positions.get(symbol, 0)}
        return {"positions": positions}

    def _validate_data(self, symbol: str, start: str, end: str) -> dict:
        """Validate data quality."""
        if self.data_provider is None:
            return {"error": "no data provider configured", "valid": False}
        result = self.data_provider.validate(symbol, start, end)
        # Add our own checks
        if self.data_provider.get_prices(symbol, start, end).empty:
            result["issues"].append("No data returned for range")
            result["valid"] = False
        return result

    def _dataset_info(self, dataset_id: str) -> dict:
        """Get dataset information."""
        if self.data_provider:
            info = self.data_provider.source_info()
            return info.to_dict() if hasattr(info, "to_dict") else dict(info)
        return {"error": "no data provider", "dataset_id": dataset_id}

    def _compute_returns(self, symbol: str, start: str, end: str) -> dict:
        """Compute returns for a symbol."""
        if self.data_provider is None:
            return {"error": "no data provider"}
        df = self.data_provider.get_prices(symbol, start, end)
        if df.empty or "close" not in df.columns:
            return {"symbol": symbol, "error": "no price data", "returns": []}
        closes = df["close"].values
        rets = self.engine.returns(closes)
        return {
            "symbol": symbol,
            "start": start,
            "end": end,
            "n_returns": len(rets),
            "first_close": float(closes[0]),
            "last_close": float(closes[-1]),
            "total_return": float(closes[-1] / closes[0] - 1) if len(closes) > 1 else 0.0,
            "returns": [float(r) for r in rets],
        }

    def _compute_risk_metrics(self, symbol: str, start: str, end: str) -> dict:
        """Compute risk metrics for a symbol."""
        if self.data_provider is None:
            return {"error": "no data provider"}
        df = self.data_provider.get_prices(symbol, start, end)
        if df.empty or "close" not in df.columns:
            return {"symbol": symbol, "error": "no price data"}
        closes = df["close"].values
        rets = self.engine.returns(closes)
        dd = self.engine.max_drawdown(rets)
        return {
            "symbol": symbol,
            "start": start,
            "end": end,
            "n_days": len(rets),
            "total_return": round(float(self.engine.annualized_return(rets)), 6),
            "cagr": round(float(self.engine.annualized_return(rets)), 6),
            "volatility": round(float(self.engine.volatility(rets)), 6),
            "sharpe": round(float(self.engine.sharpe(rets)), 4),
            "sortino": round(float(self.engine.sortino(rets)), 4),
            "max_drawdown": round(float(dd["max_drawdown"]), 6),
            "max_drawdown_duration": int(dd["duration_days"]),
            "var_95": round(float(self.engine.var(rets, 0.95)), 6),
            "cvar_95": round(float(self.engine.cvar(rets, 0.95)), 6),
            "computation_hash": content_hash({
                "symbol": symbol, "start": start, "end": end,
                "n_days": len(rets), "returns": [float(r) for r in rets],
            }),
        }

    def _compute_portfolio_returns(self, weights: dict[str, float],
                                   start: str, end: str) -> dict:
        """Compute portfolio weighted returns."""
        if self.data_provider is None:
            return {"error": "no data provider"}
        symbols = list(weights.keys())
        dfs = {}
        for sym in symbols:
            df = self.data_provider.get_prices(sym, start, end)
            if not df.empty and "close" in df.columns:
                dfs[sym] = df["close"]
        if not dfs:
            return {"error": "no price data", "portfolio_returns": []}
        # Align all series
        common_idx = None
        for sym, s in dfs.items():
            if common_idx is None:
                common_idx = s.index
            else:
                common_idx = common_idx.intersection(s.index)
        if common_idx is None or len(common_idx) == 0:
            return {"error": "no overlapping dates"}
        series = pd.DataFrame({sym: dfs[sym].reindex(common_idx) for sym in symbols})
        series = series.dropna()
        if len(series) < 2:
            return {"error": "insufficient overlapping data"}
        port_returns = series.apply(lambda col: col / col.shift(1) - 1, axis=0)
        port_returns = port_returns.dropna()
        weighted = port_returns.dot(pd.Series(weights))
        rets = self.engine.returns(weighted.values)
        dd = self.engine.max_drawdown(rets)
        return {
            "n_days": len(rets),
            "portfolio_returns": [float(r) for r in rets],
            "weighted_returns": weighted.tolist(),
            "total_return": round(float(weighted.iloc[-1] - 1) if len(weighted) > 1 else 0.0, 6),
            "cagr": round(float(self.engine.annualized_return(rets)), 6),
            "volatility": round(float(self.engine.volatility(rets)), 6),
            "sharpe": round(float(self.engine.sharpe(rets)), 4),
            "sortino": round(float(self.engine.sortino(rets)), 4),
            "max_drawdown": round(float(dd["max_drawdown"]), 6),
            "computation_hash": content_hash({
                "symbols": symbols, "start": start, "end": end,
                "weights": weights, "n_days": len(rets),
            }),
        }

    def _compute_factor_exposure(self, portfolio_returns: list[float],
                                  factor_returns: dict[str, list[float]],
                                  factor_names: list[str] | None = None) -> dict:
        """Run factor regression on portfolio returns."""
        if not portfolio_returns or len(portfolio_returns) < 2:
            return {"error": "insufficient portfolio returns"}
        pr = np.array(portfolio_returns)
        factor_matrix = []
        names = factor_names or list(factor_returns.keys())
        for name in names:
            fr = np.array(factor_returns.get(name, []))
            if len(fr) != len(pr):
                return {"error": f"factor {name} length mismatch: {len(fr)} vs {len(pr)}"}
            factor_matrix.append(fr)
        if not factor_matrix:
            return {"error": "no factor returns provided"}
        F = np.column_stack(factor_matrix)
        try:
            beta = np.linalg.lstsq(F, pr, rcond=None)[0]
        except np.linalg.LinAlgError:
            return {"error": "factor regression failed"}
        residuals = pr - F @ beta
        return {
            "factor_names": names,
            "exposures": {name: round(float(b), 6) for name, b in zip(names, beta)},
            "r_squared": round(float(1 - np.var(residuals) / np.var(pr)), 6) if np.var(pr) > 0 else 0.0,
            "residual_vol": round(float(np.std(residuals, ddof=1)), 6),
            "n_obs": len(pr),
            "computation_hash": content_hash({
                "portfolio_returns_len": len(pr),
                "factor_names": names,
                "exposures": {name: float(b) for name, b in zip(names, beta)},
            }),
        }

    def _compute_attribution(self, portfolio_returns: list[float],
                             position_returns: dict[str, list[float]],
                             weights: dict[str, float]) -> dict:
        """Compute performance attribution by position."""
        if not portfolio_returns:
            return {"error": "no portfolio returns"}
        pr = np.array(portfolio_returns)
        total_ret = float(self.engine.annualized_return(pr)) if len(pr) > 1 else 0.0
        attribution = {}
        for sym, pos_rets in position_returns.items():
            if len(pos_rets) != len(pr):
                continue
            p = np.array(pos_rets)
            w = weights.get(sym, 0)
            contrib = round(float(w * np.mean(p) * 252), 6) if len(p) > 0 else 0.0
            sharpe = round(float(self.engine.sharpe(p)), 4) if len(p) > 1 else 0.0
            attribution[sym] = {
                "weight": w,
                "contribution": contrib,
                "sharpe": sharpe,
                "n_days": len(p),
            }
        return {
            "total_portfolio_return": round(total_ret, 6),
            "attribution": attribution,
            "n_positions": len(attribution),
            "computation_hash": content_hash({
                "n_positions": len(attribution),
                "total_return": total_ret,
            }),
        }

    def _compute_concentration(self, positions: dict[str, float],
                                prices: dict[str, float] | None = None,
                                sector_map: dict[str, str] | None = None,
                                max_single_name: float = 0.25,
                                max_sector: float = 0.40) -> dict:
        """Compute single-name and sector concentration."""
        if not positions:
            return {"error": "no positions"}
        total_value = sum(positions.values())
        if total_value == 0:
            return {"error": "zero portfolio value"}
        name_concentration = {}
        sector_concentration: dict[str, float] = {}
        for sym, qty in positions.items():
            value = qty * (prices.get(sym, 1.0) if prices else qty)
            pct = value / total_value
            name_concentration[sym] = {
                "value": round(value, 2),
                "weight": round(pct, 6),
                "exceeds_limit": pct > max_single_name,
            }
            sector = sector_map.get(sym, "unknown") if sector_map else "unknown"
            sector_concentration[sector] = sector_concentration.get(sector, 0) + pct
        sector_result = {}
        for sect, pct in sector_concentration.items():
            sector_result[sect] = {
                "weight": round(pct, 6),
                "exceeds_limit": pct > max_sector,
            }
        breaches = [sym for sym, info in name_concentration.items() if info["exceeds_limit"]]
        sector_breaches = [s for s, info in sector_result.items() if info["exceeds_limit"]]
        return {
            "total_value": round(total_value, 2),
            "n_positions": len(positions),
            "name_concentration": name_concentration,
            "sector_concentration": sector_result,
            "max_single_name_limit": max_single_name,
            "max_sector_limit": max_sector,
            "single_name_breaches": breaches,
            "sector_breaches": sector_breaches,
            "computation_hash": content_hash({
                "total_value": total_value,
                "n_positions": len(positions),
                "name_breaches": breaches,
                "sector_breaches": sector_breaches,
            }),
        }

    def _detect_anomalies(self, portfolio_returns: list[float],
                          benchmark_returns: list[float] | None = None,
                          volume_data: dict[str, list[float]] | None = None,
                          window: int = 20) -> dict:
        """Detect anomalies in portfolio behavior."""
        if not portfolio_returns or len(portfolio_returns) < window + 1:
            return {"error": "insufficient data", "anomalies": []}
        pr = np.array(portfolio_returns)
        anomalies = []

        # 1. Drawdown anomalies — drawdowns exceeding 2x average
        cum = np.cumsum(pr)
        peak = np.maximum.accumulate(cum)
        dd = (cum - peak) / np.maximum(peak, 1e-10)
        avg_dd = np.mean(dd[dd < 0]) if np.any(dd < 0) else 0
        for i, d in enumerate(dd):
            if d < avg_dd * 3 and d < -0.02:
                anomalies.append({
                    "type": "severe_drawdown",
                    "index": i,
                    "drawdown": round(float(d), 6),
                    "severity": "high" if d < -0.10 else "medium",
                })

        # 2. Return volatility anomalies
        if len(pr) > window:
            rolling_vol = pd.Series(pr).rolling(window).std().dropna().values
            if len(rolling_vol) > 0:
                mean_vol = np.mean(rolling_vol)
                for i, v in enumerate(rolling_vol):
                    if v > mean_vol * 3 and v > 0.05:
                        anomalies.append({
                            "type": "volatility_spike",
                            "index": i + window,
                            "volatility": round(float(v), 6),
                            "severity": "medium",
                        })

        # 3. Concentration risk (if positions available — handled by other tool)

        return {
            "n_returns": len(pr),
            "n_anomalies": len(anomalies),
            "anomalies": anomalies,
            "computation_hash": content_hash({
                "n_returns": len(pr),
                "n_anomalies": len(anomalies),
            }),
        }

    def _compute_beta(self, portfolio_returns: list[float],
                       benchmark_returns: list[float]) -> dict:
        """Compute beta of portfolio vs benchmark."""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return {"error": "length mismatch or insufficient data"}
        pr = np.array(portfolio_returns)
        br = np.array(benchmark_returns)
        beta = self.engine.beta(pr, br)
        # Correlation
        corr = float(np.corrcoef(pr, br)[0, 1]) if len(pr) > 2 else 0.0
        return {
            "beta": round(float(beta), 6),
            "correlation": round(float(corr), 6),
            "n_obs": len(pr),
            "computation_hash": content_hash({
                "n_obs": len(pr),
                "beta": float(beta),
                "correlation": float(corr),
            }),
        }

    def _compute_var_cvar(self, returns: list[float], confidence: float = 0.95) -> dict:
        """Compute Value at Risk and Conditional VaR."""
        if not returns or len(returns) < 2:
            return {"error": "insufficient data"}
        r = np.array(returns)
        var = self.engine.var(r, confidence)
        cvar = self.engine.cvar(r, confidence)
        return {
            "confidence": confidence,
            "n_obs": len(r),
            "var": round(float(var), 6),
            "cvar": round(float(cvar), 6),
            "mean": round(float(np.mean(r)), 6),
            "std": round(float(np.std(r, ddof=1)), 6),
            "computation_hash": content_hash({
                "n_obs": len(r),
                "confidence": confidence,
                "var": float(var),
                "cvar": float(cvar),
            }),
        }

    def _compute_backtest(self, strategy_id: str, prices: pd.DataFrame | None = None,
                          **kwargs) -> dict:
        """Run a deterministic backtest."""
        if prices is None or prices.empty:
            return {"error": "no price data for backtest"}
        config = BacktestConfig(
            strategy=sas.quant.strategy.StrategyArtifact(
                strategy_id=strategy_id,
                name=strategy_id,
                signal_definition=sas.quant.strategy.SignalDefinition(
                    name="default", type="trend", parameters={}, lookback_periods=10
                ),
                universe=list(prices.columns) if hasattr(prices, "columns") else ["DEFAULT"],
                training_period=(kwargs.get("train_start", "2020-01-01"),
                                 kwargs.get("train_end", "2022-12-31")),
                validation_period=(kwargs.get("val_start", "2023-01-01"),
                                   kwargs.get("val_end", "2023-06-30")),
                test_period=(kwargs.get("test_start", "2023-07-01"),
                              kwargs.get("test_end", "2024-12-31")),
            ),
            initial_capital=kwargs.get("initial_capital", 100_000),
            seed=kwargs.get("seed", 42),
        )
        result = self.backtest_engine.run(config, prices)
        return result.to_dict()

    def _evaluate_risk(self, weights: dict[str, float],
                       positions: dict[str, float] | None = None,
                       prices: dict[str, float] | None = None) -> dict:
        """Evaluate risk against policy."""
        eval_result = self.risk_engine.evaluate(weights, positions or {}, prices or {})
        return eval_result.to_dict()

    def _build_report(self, findings: list[dict] | None = None,
                      risk_evaluations: list[dict] | None = None,
                      methodology: str = "",
                      **kwargs) -> dict:
        """Build a research report from findings."""
        from sas.quant.reports import ReportGenerator

        # Convert backtest result dicts to BacktestResult objects (simplified)
        backtest_results = []
        for f in (findings or []):
            if f.get("artifact_type") == "backtest_result":
                # Minimal BacktestResult reconstruction
                br = BacktestResult(
                    strategy_id=f.get("strategy_id", ""),
                    strategy_version=f.get("strategy_version", "1.0.0"),
                    engine_version=f.get("engine_version", "1.0.0"),
                    dataset_version=f.get("dataset_version", "1.0.0"),
                    seed=f.get("seed", 42),
                    total_return=f.get("total_return", 0.0),
                    annualized_return=f.get("annualized_return", 0.0),
                    annualized_volatility=f.get("annualized_volatility", 0.0),
                    sharpe_ratio=f.get("sharpe_ratio", 0.0),
                    sortino_ratio=f.get("sortino_ratio", 0.0),
                    max_drawdown=f.get("max_drawdown", 0.0),
                    max_drawdown_duration=f.get("max_drawdown_duration", 0),
                    var_95=f.get("var_95", 0.0),
                    cvar_95=f.get("cvar_95", 0.0),
                    win_rate=f.get("win_rate", 0.0),
                    profit_factor=f.get("profit_factor", 0.0),
                    total_trades=f.get("total_trades", 0),
                    avg_trade_return=f.get("avg_trade_return", 0.0),
                    monthly_returns=f.get("monthly_returns", []),
                    equity_curve=f.get("equity_curve", []),
                    drawdown_series=f.get("drawdown_series", []),
                    transaction_costs=f.get("transaction_costs", 0.0),
                    final_value=f.get("final_value", 0.0),
                    train_period=(f.get("train_start", ""), f.get("train_end", "")),
                    validation_period=(f.get("val_start", ""), f.get("val_end", "")),
                    test_period=(f.get("test_start", ""), f.get("test_end", "")),
                    assumptions=f.get("assumptions", {}),
                    warnings=f.get("warnings", []),
                )
                backtest_results.append(br)

        risk_evals = []
        for re in (risk_evaluations or []):
            r = RiskEvaluation()
            for k, v in re.items():
                if hasattr(r, k) and k != "content_hash":
                    setattr(r, k, v)
            risk_evals.append(r)

        generator = ReportGenerator()
        report = generator.generate(
            title=kwargs.get("title", "Quantitative Research Report"),
            backtest_results=backtest_results,
            risk_evaluations=risk_evals,
            trade_intents=[],
            methodology=methodology or "Deterministic quantitative analysis using SAS Quant Engine v1.0.0.",
            data_sources=kwargs.get("data_sources", []),
            assumptions=kwargs.get("assumptions", {}),
            findings=findings,
        )
        return {
            "report_id": report.report_id,
            "title": report.title,
            "generated_at": report.generated_at,
            "executive_summary": report.executive_summary,
            "quantitative_findings": report.quantitative_findings,
            "risk_analysis": report.risk_analysis,
            "strategy_results": report.strategy_results,
            "warnings": report.warnings,
            "provenance": report.provenance,
            "content_hash": report.content_hash,
        }

    def _get_provenance(self, artifact_id: str) -> dict:
        """Get provenance for an artifact."""
        if self.provenance_graph:
            node = self.provenance_graph.get(artifact_id)
            if node:
                ancestors = self.provenance_graph.lineage_chain(artifact_id)
                return {
                    "artifact_id": artifact_id,
                    "artifact_type": node.artifact_type,
                    "producer": node.producer,
                    "model": node.model,
                    "created_at": node.created_at,
                    "lineage": [a.to_dict() for a in ancestors],
                }
        return {"artifact_id": artifact_id, "error": "not found in provenance graph"}

    def _compute_portfolio_value(self) -> float:
        """Compute total portfolio value."""
        positions = self.portfolio.get("positions", {})
        cash = self.portfolio.get("cash", 0)
        # For synthetic positions, use quantity as value proxy
        pos_value = sum(abs(q) for q in positions.values())
        return cash + pos_value

    def _propose_strategy(
        self,
        name: str = "",
        signal_name: str = "momentum",
        signal_type: str = "momentum",
        signal_params: dict | None = None,
        sizing_method: str = "fixed_weight",
        target_weight: float = 0.10,
        max_position: float = 0.25,
        rebalance_frequency: str = "monthly",
        entry_rules: dict | None = None,
        exit_rules: dict | None = None,
        assumptions: dict | None = None,
        **kwargs,
    ) -> dict:
        """Propose a trading strategy with full parameters.

        This tool formalizes a strategy idea into a structured artifact
        that can be backtested and evaluated. Call this before running
        compute_backtest.
        """
        strategy_data = {
            "name": name or f"strategy-{signal_type}",
            "signal_name": signal_name,
            "signal_type": signal_type,
            "signal_params": signal_params or {},
            "sizing_method": sizing_method,
            "target_weight": target_weight,
            "max_position": max_position,
            "rebalance_frequency": rebalance_frequency,
            "entry_rules": entry_rules or {},
            "exit_rules": exit_rules or {},
            "assumptions": assumptions or {},
        }
        return strategy_data


# Need to import sas.quant.strategy inside methods to avoid circular import
import sas.quant.strategy

# ── Toolbox Factory ──────────────────────────────────────────────────────────

def create_toolbox_from_world(world, data_provider=None, **kwargs):
    """Create a QuantToolbox configured for a QuantWorld."""

    engine = QuantEngine(EngineConfig(
        risk_free_rate=0.02,
        trading_days=252,
        min_periods=20,
        seed=kwargs.get("seed", 42),
    ))

    portfolio = dict(world.portfolio)

    risk_policy = RiskPolicy(
        max_position_weight=world.constraints.get("max_single_name_concentration", 0.15),
        max_gross_exposure=world.constraints.get("max_gross_exposure", 1.0),
        max_sector_exposure=world.constraints.get("max_sector_exposure", 0.40),
        max_drawdown=world.constraints.get("max_drawdown_limit", 0.20),
        approved_universe=world.constraints.get("approved_universe", []),
    )
    risk_engine = RiskEngine(risk_policy)

    toolbox = QuantToolbox(
        data_provider=data_provider,
        engine=engine,
        risk_engine=risk_engine,
        portfolio=portfolio,
    )

    return toolbox


# ── Export ───────────────────────────────────────────────────────────────────

__all__ = [
    "QuantToolbox", "ToolDefinition", "create_toolbox_from_world",
]
