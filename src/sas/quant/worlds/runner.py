"""Canonical pipeline runner for the Quant research subsystem.

This module is the single source of truth for running end-to-end quant
pipelines. It is consumed by both the integration tests
(``tests/integration/test_quant_pipeline.py``) and the dashboard server
(``src/sas/quant/dashboard/server.py``) so that pipeline logic lives in
exactly one place.

It provides:

* Synthetic price generation (:func:`generate_synthetic_prices`)
* An in-memory :class:`MarketDataProvider` (:class:`SyntheticProvider`)
* Scripted workflow definitions for each world
  (:func:`create_portfolio_intelligence_script`,
  :func:`create_risk_parity_script`, :func:`create_momentum_script`)
* The unified :func:`run_pipeline` entry point
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure src is importable when this module is loaded directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))

from sas.quant import (  # noqa: E402
    QuantWorld,
    Task,
    Rubric,
    ExecutionRun,
    RunEvaluator,
    aggregate_benchmark,
    evaluate_sovereignty,
    create_toolbox_from_world,
    StubModelAdapter,
    quant_coordinator,
)
from sas.quant.market import MarketDataProvider, DatasetInfo  # noqa: E402

# ── Synthetic Data Generator ──────────────────────────────────────────────────

_SYNTHETIC_START = "2024-01-02"
_SYNTHETIC_END = "2024-12-31"


def generate_synthetic_prices(symbol: str, start: str, end: str,
                               seed: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic price data for testing."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="B")
    n = len(dates)
    if n == 0:
        return pd.DataFrame()
    rets = rng.normal(0.0005, 0.02, n)
    prices = 100 * np.exp(np.cumsum(rets))
    volumes = rng.lognormal(20, 1, n)
    df = pd.DataFrame({
        "date": dates,
        "open": prices * (1 + rng.normal(0, 0.005, n)),
        "high": prices * (1 + abs(rng.normal(0, 0.01, n))),
        "low": prices * (1 - abs(rng.normal(0, 0.01, n))),
        "close": prices,
        "volume": volumes,
    })
    df.index = dates
    return df


class SyntheticProvider(MarketDataProvider):
    """In-memory synthetic price source for CI / offline pipeline tests."""

    def __init__(self, data: dict[str, pd.DataFrame], source_version: str = "test-1.0"):
        self._data = data
        self._source_version = source_version

    def get_prices(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        if symbol not in self._data:
            return pd.DataFrame()
        df = self._data[symbol]
        mask = (df.index >= start) & (df.index <= end)
        return df[mask]

    def get_bars(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        return self.get_prices(symbol, start, end)

    def validate(self, symbol: str, start: str, end: str) -> dict:
        df = self.get_prices(symbol, start, end)
        issues: list[str] = []
        if df.empty:
            issues.append("No data found")
        if df.isnull().any().any():
            issues.append("Contains null values")
        if (df["high"] < df["low"]).any():
            issues.append("High < Low violations")
        return {
            "symbol": symbol,
            "valid": len(issues) == 0,
            "issues": issues,
            "rows": len(df),
        }

    def source_info(self) -> DatasetInfo:
        return DatasetInfo(
            source="synthetic",
            version=self._source_version,
            symbols=list(self._data.keys()),
            start_date=_SYNTHETIC_START,
            end_date=_SYNTHETIC_END,
            row_count=sum(len(d) for d in self._data.values()),
        )


def create_test_data_provider(world: QuantWorld) -> dict[str, pd.DataFrame]:
    """Create synthetic price data for all universe symbols."""
    data: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(world.universe):
        data[sym] = generate_synthetic_prices(
            sym, _SYNTHETIC_START, _SYNTHETIC_END, seed=42 + i
        )
    return data


# ── Scripted Workflows ────────────────────────────────────────────────────────

def create_portfolio_intelligence_script() -> list[dict]:
    """Scripted portfolio intelligence workflow."""
    return [
        {"tools": [{"name": "get_portfolio", "arguments": {}}],
         "response": "Examining portfolio holdings."},
        {"tools": [
            {"name": "get_prices", "arguments": {"symbol": "AAPL", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "MSFT", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "GOOG", "start": "2024-01-02", "end": "2024-12-31"}},
        ], "response": "Gathered price data."},
        {"tools": [
            {"name": "compute_risk_metrics", "arguments": {"symbol": "AAPL", "start": "2024-01-02", "end": "2024-12-31"}},
        ], "response": "Computed risk metrics."},
        {"tools": [
            {"name": "compute_portfolio_returns", "arguments": {
                "weights": {"AAPL": 0.30, "MSFT": 0.20, "GOOG": 0.15, "AMZN": 0.15, "NVDA": 0.10, "META": 0.10},
                "start": "2024-01-02", "end": "2024-12-31",
            }},
        ], "response": "Computed portfolio returns."},
        {"tools": [
            {"name": "compute_concentration", "arguments": {
                "positions": {"AAPL": 12500, "MSFT": 8200, "GOOG": 6400, "AMZN": 4800, "NVDA": 3200, "META": 5100},
            }},
        ], "response": "Analyzed concentration."},
        {"tools": [
            {"name": "detect_anomalies", "arguments": {
                "portfolio_returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
            }},
        ], "response": "Ran anomaly detection."},
        {"tools": [
            {"name": "compute_factor_exposure", "arguments": {
                "portfolio_returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                "factor_returns": {"market": [0.001, -0.001, 0.002, -0.010, 0.001, -0.002, 0.001, -0.020, 0.001, 0.000]},
                "factor_names": ["market"],
            }},
        ], "response": "Computed factor exposure."},
        {"tools": [
            {"name": "compute_beta", "arguments": {
                "portfolio_returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                "benchmark_returns": [0.0008, -0.0015, 0.0025, -0.012, 0.0008, -0.0025, 0.0015, -0.022, 0.0008, -0.0008],
            }},
        ], "response": "Computed beta."},
        {"tools": [
            {"name": "compute_var_cvar", "arguments": {
                "returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                "confidence": 0.95,
            }},
        ], "response": "Computed VaR/CVaR."},
        {"tools": [
            {"name": "build_report", "arguments": {
                "findings": [
                    {"artifact_type": "computation", "name": "portfolio_return", "value": 0.15},
                    {"artifact_type": "computation", "name": "sharpe", "value": 1.2},
                    {"artifact_type": "computation", "name": "max_drawdown", "value": 0.08},
                ],
                "risk_evaluations": [{"artifact_type": "risk_evaluation", "is_compliant": True, "breaches": []}],
                "methodology": "Quantitative analysis v1.0.0. Daily OHLCV 2024-01-02 to 2024-12-31.",
                "title": "Portfolio Intelligence Report Q4 2024",
            }},
        ], "response": "Report produced."},
    ]


def create_risk_parity_script() -> list[dict]:
    """Scripted risk parity workflow."""
    return [
        {"tools": [
            {"name": "get_prices", "arguments": {"symbol": "SPY", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "TLT", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "GLD", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "VNQ", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "DBC", "start": "2024-01-02", "end": "2024-12-31"}},
        ], "response": "Fetched multi-asset prices."},
        {"tools": [
            {"name": "compute_returns", "arguments": {"symbols": ["SPY", "TLT", "GLD", "VNQ", "DBC"]}},
        ], "response": "Computed returns."},
        {"tools": [
            {"name": "compute_covariance", "arguments": {"symbols": ["SPY", "TLT", "GLD", "VNQ", "DBC"]}},
        ], "response": "Computed covariance matrix."},
        {"tools": [
            {"name": "solve_risk_parity", "arguments": {"covariance": "from_previous_step"}},
        ], "response": "Solved risk-parity weights."},
        {"tools": [
            {"name": "compute_risk_contribution", "arguments": {"weights": {"SPY": 0.2, "TLT": 0.2, "GLD": 0.2, "VNQ": 0.2, "DBC": 0.2}}},
        ], "response": "Computed risk contributions."},
        {"tools": [
            {"name": "validate_weights", "arguments": {"weights": {"SPY": 0.2, "TLT": 0.2, "GLD": 0.2, "VNQ": 0.2, "DBC": 0.2}}},
        ], "response": "Validated weights."},
        {"tools": [
            {"name": "build_report", "arguments": {
                "findings": [
                    {"artifact_type": "computation", "name": "risk_parity", "value": [0.2, 0.2, 0.2, 0.2, 0.2]},
                    {"artifact_type": "computation", "name": "valid", "value": True},
                ],
                "title": "Risk Parity Portfolio Construction",
            }},
        ], "response": "Report produced."},
    ]


def create_momentum_script() -> list[dict]:
    """Scripted momentum strategy workflow."""
    return [
        {"tools": [
            {"name": "get_prices", "arguments": {"symbol": "AAPL", "start": "2024-01-02", "end": "2024-12-31"}},
            {"name": "get_prices", "arguments": {"symbol": "MSFT", "start": "2024-01-02", "end": "2024-12-31"}},
        ], "response": "Fetched equity prices."},
        {"tools": [
            {"name": "compute_returns", "arguments": {"symbols": ["AAPL", "MSFT"]}},
        ], "response": "Computed returns."},
        {"tools": [
            {"name": "compute_momentum_signal", "arguments": {"lookback": 252, "skip": 21}},
        ], "response": "Computed momentum signal."},
        {"tools": [
            {"name": "backtest_strategy", "arguments": {"strategy_id": "momentum"}},
        ], "response": "Backtest complete."},
        {"tools": [
            {"name": "compute_turnover", "arguments": {"weights_history": []}},
        ], "response": "Computed turnover."},
        {"tools": [
            {"name": "compute_transaction_costs", "arguments": {"turnover": 0.15, "cost_bps": 10}},
        ], "response": "Estimated transaction costs."},
        {"tools": [
            {"name": "build_report", "arguments": {
                "findings": [
                    {"artifact_type": "computation", "name": "momentum", "value": 0.12},
                    {"artifact_type": "computation", "name": "backtest", "value": {"sharpe": 1.5}},
                    {"artifact_type": "computation", "name": "turnover", "value": 0.15},
                    {"artifact_type": "computation", "name": "cost", "value": 0.0015},
                ],
                "title": "Momentum Strategy Research",
            }},
        ], "response": "Report produced."},
    ]


# ── Pipeline Runner ───────────────────────────────────────────────────────────

def run_pipeline(
    world: QuantWorld,
    task: Task,
    rubric: Rubric,
    script: list[dict],
    data_provider: MarketDataProvider | None = None,
) -> dict:
    """Run the full pipeline: world → toolbox → model → evaluation.

    Returns a dict with all results for assertion.
    """
    if data_provider is None:
        data = create_test_data_provider(world)
        data_provider = SyntheticProvider(data)

    toolbox = create_toolbox_from_world(world, seed=42)
    toolbox.data_provider = data_provider

    model = StubModelAdapter(script=script)
    agent = quant_coordinator()

    run = ExecutionRun(
        run_id=f"e2e-{world.id}-001",
        task_id=task.id,
        world_id=world.id,
        agent_name=agent.name,
        agent_role=agent.role,
        model="stub-model",
        model_provider="local",
    )

    ctx = model.prepare_context(world, task, agent, None)
    result = model.run_loop(ctx, toolbox, run, max_steps=15)

    run.status = result.get("status", "completed")
    run.end_time = "2024-12-31T12:00:00+00:00"
    run.tool_calls = result.get("tools_called", 0)

    evaluator = RunEvaluator(rubric)
    eval_result = evaluator.evaluate(run, world)

    all_evals = [eval_result]
    benchmark = aggregate_benchmark(all_evals, world.id, task.id)
    sov = evaluate_sovereignty(run, world)

    return {
        "world_id": world.id,
        "task_id": task.id,
        "run_id": run.run_id,
        "model_loop_result": result,
        "evaluation": eval_result.to_dict(),
        "benchmark": benchmark.to_dict(),
        "sovereignty": sov,
        "artifacts_created": list(run.artifacts.keys()),
        "tool_calls": run.tool_calls,
        "steps_in_trajectory": len(run.steps),
    }


__all__ = [
    "create_momentum_script",
    "create_portfolio_intelligence_script",
    "create_risk_parity_script",
    "run_pipeline",
    "SyntheticProvider",
    "create_test_data_provider",
    "generate_synthetic_prices",
]
