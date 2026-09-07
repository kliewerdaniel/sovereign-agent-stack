"""End-to-end integration tests for the Quant research pipeline.

Covers the full pipeline: world → toolbox → model → execution → evaluation.
Runs against multiple worlds including portfolio intelligence, risk parity,
momentum, and adversarial worlds.

These tests use StubModelAdapter (scripted) so they pass deterministically
without requiring a real LLM or internet access.
"""

from __future__ import annotations

import sys
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant import (
    QuantWorld, Task, Rubric, Criterion, CriterionResult,
    Evidence, ExecutionRun, TrajectoryStep, RunEvaluation,
    QuantWorldBuilder, ModelAdapter, CapabilityComposition,
    RunEvaluator, BenchmarkResult, BenchmarkRunner,
    compute_pass_k, aggregate_benchmark,
    evaluate_sovereignty,
    QuantToolbox, create_toolbox_from_world,
    StubModelAdapter, ToolFormatter,
    quant_coordinator,
)
from sas.quant.market import MarketDataProvider, DatasetInfo
from sas.quant.worlds import (
    PORTFOLIO_INTELLIGENCE_WORLD, PORTFOLIO_INTELLIGENCE_TASK,
    PORTFOLIO_INTELLIGENCE_RUBRIC, PORTFOLIO_INTELLIGENCE_GOLD,
    RISK_PARITY_WORLD, RISK_PARITY_TASK, RISK_PARITY_RUBRIC,
    MOMENTUM_WORLD, MOMENTUM_TASK, MOMENTUM_RUBRIC,
    ADVERSTIONAL_WORLDS,
)


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


# ── Pytest Tests ──────────────────────────────────────────────────────────────

class TestPortfolioIntelligencePipeline:
    """Tests for the portfolio intelligence end-to-end pipeline."""

    def test_pipeline_runs_successfully(self):
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
        )
        assert result["run_id"] != ""
        assert result["tool_calls"] > 0
        assert result["steps_in_trajectory"] > 0
        assert len(result["artifacts_created"]) > 0

    def test_model_loop_completes(self):
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
        )
        assert result["model_loop_result"].get("status") == "completed"

    def test_evaluation_produces_results(self):
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
        )
        eval_data = result["evaluation"]
        assert len(eval_data["criterion_results"]) == len(PORTFOLIO_INTELLIGENCE_RUBRIC.criteria)
        assert eval_data["mean_score"] > 0.0

    def test_pass_at_1_computed(self):
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
        )
        bench = result["benchmark"]
        assert 0.0 <= bench["pass_at_1"] <= 1.0
        assert bench["pass_k"] in (True, False)

    def test_sovereignty_evaluated(self):
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
        )
        sov = result["sovereignty"]
        assert "passed" in sov
        assert isinstance(sov["passed"], bool)

    def test_provenance_required(self):
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
        )
        eval_data = result["evaluation"]
        assert "provenance_complete" in eval_data


class TestRiskParityPipeline:
    """Tests for the risk parity world pipeline."""

    def test_pipeline_runs(self):
        result = run_pipeline(
            RISK_PARITY_WORLD,
            RISK_PARITY_TASK,
            RISK_PARITY_RUBRIC,
            create_risk_parity_script(),
        )
        assert result["run_id"] != ""
        assert result["tool_calls"] > 0

    def test_evaluation_has_all_criteria(self):
        result = run_pipeline(
            RISK_PARITY_WORLD,
            RISK_PARITY_TASK,
            RISK_PARITY_RUBRIC,
            create_risk_parity_script(),
        )
        eval_data = result["evaluation"]
        assert len(eval_data["criterion_results"]) == len(RISK_PARITY_RUBRIC.criteria)

    def test_report_artifact_created(self):
        result = run_pipeline(
            RISK_PARITY_WORLD,
            RISK_PARITY_TASK,
            RISK_PARITY_RUBRIC,
            create_risk_parity_script(),
        )
        # Artifacts are hash-based IDs; just verify they were created
        assert len(result["artifacts_created"]) > 0


class TestMomentumPipeline:
    """Tests for the momentum strategy world pipeline."""

    def test_pipeline_runs(self):
        result = run_pipeline(
            MOMENTUM_WORLD,
            MOMENTUM_TASK,
            MOMENTUM_RUBRIC,
            create_momentum_script(),
        )
        assert result["run_id"] != ""
        assert result["tool_calls"] > 0

    def test_evaluation_has_all_criteria(self):
        result = run_pipeline(
            MOMENTUM_WORLD,
            MOMENTUM_TASK,
            MOMENTUM_RUBRIC,
            create_momentum_script(),
        )
        eval_data = result["evaluation"]
        assert len(eval_data["criterion_results"]) == len(MOMENTUM_RUBRIC.criteria)


class TestAdversarialWorlds:
    """Tests for adversarial world loading and structure."""

    def test_adversarial_worlds_loaded(self):
        assert "prompt_injection" in ADVERSTIONAL_WORLDS
        assert "capability_escalation" in ADVERSTIONAL_WORLDS
        assert "data_poisoning" in ADVERSTIONAL_WORLDS
        assert "policy_manipulation" in ADVERSTIONAL_WORLDS

    def test_adversarial_worlds_have_rubrics(self):
        for name, world_data in ADVERSTIONAL_WORLDS.items():
            assert "world" in world_data
            assert "task" in world_data
            assert "rubric" in world_data
            assert len(world_data["rubric"].criteria) > 0

    def test_adversarial_worlds_have_gold(self):
        for name, world_data in ADVERSTIONAL_WORLDS.items():
            assert "gold" in world_data
            assert "expected_behavior" in world_data["gold"]


class TestSyntheticProvider:
    """Tests for the synthetic data provider."""

    def test_returns_data_for_known_symbol(self):
        data = {"AAPL": generate_synthetic_prices("AAPL", "2024-01-02", "2024-12-31")}
        provider = SyntheticProvider(data)
        df = provider.get_prices("AAPL", "2024-01-02", "2024-12-31")
        assert not df.empty
        assert "close" in df.columns

    def test_returns_empty_for_unknown_symbol(self):
        provider = SyntheticProvider({})
        df = provider.get_prices("UNKNOWN", "2024-01-02", "2024-12-31")
        assert df.empty

    def test_validate_passes_for_good_data(self):
        data = {"AAPL": generate_synthetic_prices("AAPL", "2024-01-02", "2024-12-31")}
        provider = SyntheticProvider(data)
        result = provider.validate("AAPL", "2024-01-02", "2024-12-31")
        assert result["valid"]

    def test_source_info(self):
        data = {"AAPL": generate_synthetic_prices("AAPL", "2024-01-02", "2024-12-31")}
        provider = SyntheticProvider(data)
        info = provider.source_info()
        assert info.source == "synthetic"
        assert "AAPL" in info.symbols


class TestPipelineWithRealDataProviders:
    """Tests that the pipeline works with different data provider types."""

    def test_with_synthetic_provider(self):
        data = create_test_data_provider(PORTFOLIO_INTELLIGENCE_WORLD)
        provider = SyntheticProvider(data)
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
            data_provider=provider,
        )
        assert result["tool_calls"] > 0

    def test_with_local_csv_provider(self, tmp_path):
        """Test with a LocalCSVDataset provider."""
        # Write synthetic data to CSV
        for sym in ["AAPL", "MSFT", "GOOG"]:
            df = generate_synthetic_prices(sym, "2024-01-02", "2024-12-31")
            df.to_csv(tmp_path / f"{sym}.csv")

        from sas.quant.market import LocalCSVDataset
        provider = LocalCSVDataset(tmp_path)
        result = run_pipeline(
            PORTFOLIO_INTELLIGENCE_WORLD,
            PORTFOLIO_INTELLIGENCE_TASK,
            PORTFOLIO_INTELLIGENCE_RUBRIC,
            create_portfolio_intelligence_script(),
            data_provider=provider,
        )
        assert result["tool_calls"] > 0


# ── Main entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Sovereign Quant — End-to-End Pipeline Test")
    print("=" * 60)

    provider = SyntheticProvider(
        create_test_data_provider(PORTFOLIO_INTELLIGENCE_WORLD)
    )
    result = run_pipeline(
        PORTFOLIO_INTELLIGENCE_WORLD,
        PORTFOLIO_INTELLIGENCE_TASK,
        PORTFOLIO_INTELLIGENCE_RUBRIC,
        create_portfolio_intelligence_script(),
        data_provider=provider,
    )

    print(f"\nWorld: {result['world_id']}")
    print(f"Task: {result['task_id']}")
    print(f"Run: {result['run_id']}")
    print(f"\nModel Loop:")
    print(f"  Status: {result['model_loop_result'].get('status')}")
    print(f"  Steps taken: {result['model_loop_result'].get('steps_taken')}")
    print(f"  Tools called: {result['model_loop_result'].get('tools_called')}")
    print(f"\nEvaluation:")
    print(f"  Passed (Pass@1): {result['evaluation']['passed']}")
    print(f"  Mean Criterion Score: {result['evaluation']['mean_score']:.4f}")
    print(f"  Sovereignty Passed: {result['evaluation']['sovereignty_passed']}")
    print(f"  Sovereignty Violations: {result['evaluation']['sovereignty_violations']}")
    print(f"  Provenance Complete: {result['evaluation']['provenance_complete']}")
    print(f"\nBenchmark:")
    print(f"  Pass@1: {result['benchmark']['pass_at_1']:.4f}")
    print(f"  Pass@8: {result['benchmark']['pass_at_8']:.4f}")
    print(f"  Pass^k (all pass): {result['benchmark']['pass_k']}")
    print(f"\nArtifacts Created: {result['artifacts_created']}")
    print(f"\nCriterion Results:")
    for cr in result['evaluation']['criterion_results']:
        status = "✓" if cr['passed'] else "✗"
        print(f"  {status} {cr['criterion_name']}: {cr['score']:.1f} — {cr['note'][:60]}")

    print(f"\nSovereignty Checks:")
    sov = result['sovereignty']
    print(f"  Passed: {sov['passed']}")
    print(f"  Violations: {sov['violation_count']}")
    for check in sov['checks_performed']:
        print(f"  ✓ {check}")

    # Verify pipeline integrity
    print(f"\n{'='*60}")
    print("Pipeline Integrity Check:")
    print(f"{'='*60}")

    checks = []
    checks.append(("Run created", result['run_id'] != ""))
    checks.append(("Model loop ran", result['model_loop_result'].get('steps_taken', 0) > 0))
    checks.append(("Tools called", result['tool_calls'] > 0))
    checks.append(("Trajectory populated",
                   len(result.get('model_loop_result', {}).get('trajectory', [])) > 0))
    checks.append(("Artifacts created", len(result['artifacts_created']) > 0))
    checks.append(("Evaluation produced",
                   len(result['evaluation']['criterion_results']) == len(
                       PORTFOLIO_INTELLIGENCE_RUBRIC.criteria)))
    checks.append(("Sovereignty evaluated", 'passed' in result['sovereignty']))

    for name, ok in checks:
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")

    all_ok = all(ok for _, ok in checks)
    print(f"\n{'ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED'}")
