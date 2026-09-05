"""
End-to-end integration: StubModelAdapter → QuantToolbox → ExecutionRun → Evaluation.

This is the critical integration test that proves the Phase 2 architecture
actually works end-to-end:
1. Create a QuantWorld + Task + Rubric
2. Build a QuantToolbox with real tool implementations
3. Run a StubModelAdapter through the loop
4. Evaluate the resulting ExecutionRun against the rubric
5. Check Pass@1, sovereignty, provenance

The stub model is scripted to call the right tools in the right order,
simulating what a real model would do once trained on the environment.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from sas.quant import (
    QuantWorld, Task, Rubric, ExecutionRun, TrajectoryStep,
    QuantToolbox, create_toolbox_from_world,
    StubModelAdapter, ToolFormatter,
    RunEvaluator, aggregate_benchmark, compute_pass_k,
    evaluate_sovereignty,
    PORTFOLIO_INTELLIGENCE_WORLD, PORTFOLIO_INTELLIGENCE_TASK,
    PORTFOLIO_INTELLIGENCE_RUBRIC,
)


# ── Synthetic Data Generator ──────────────────────────────────────────────────

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


def create_test_data_provider(world: QuantWorld) -> dict[str, pd.DataFrame]:
    """Create synthetic price data for all universe symbols."""
    start = "2024-01-02"
    end = "2024-12-31"
    data = {}
    for i, sym in enumerate(world.universe):
        data[sym] = generate_synthetic_prices(sym, start, end, seed=42 + i)
    return data


# ── Scripted Stub: Portfolio Intelligence Workflow ──────────────────────────

def create_portfolio_intelligence_script() -> list[dict]:
    """Script that simulates a model doing the portfolio intelligence workflow.

    This is what a competent model WOULD do if it understood the environment.
    Used to test the pipeline without requiring a real LLM.
    """
    return [
        # Step 1: Get portfolio
        {
            "tools": [{"name": "get_portfolio", "arguments": {}}],
            "response": "I will start by examining the portfolio holdings and then gather market data.",
        },
        # Step 2: Get prices for all positions
        {
            "tools": [
                {"name": "get_prices", "arguments": {"symbol": "AAPL", "start": "2024-01-02", "end": "2024-12-31"}},
                {"name": "get_prices", "arguments": {"symbol": "MSFT", "start": "2024-01-02", "end": "2024-12-31"}},
                {"name": "get_prices", "arguments": {"symbol": "GOOG", "start": "2024-01-02", "end": "2024-12-31"}},
            ],
            "response": "Gathered price data for top positions.",
        },
        # Step 3: Compute risk metrics
        {
            "tools": [
                {"name": "compute_risk_metrics", "arguments": {"symbol": "AAPL", "start": "2024-01-02", "end": "2024-12-31"}},
                {"name": "compute_risk_metrics", "arguments": {"symbol": "MSFT", "start": "2024-01-02", "end": "2024-12-31"}},
            ],
            "response": "Computed risk metrics for key positions.",
        },
        # Step 4: Compute portfolio returns (simulated weights)
        {
            "tools": [
                {"name": "compute_portfolio_returns", "arguments": {
                    "weights": {"AAPL": 0.30, "MSFT": 0.20, "GOOG": 0.15, "AMZN": 0.15, "NVDA": 0.10, "META": 0.10},
                    "start": "2024-01-02",
                    "end": "2024-12-31",
                }},
            ],
            "response": "Computed portfolio-level returns and risk metrics.",
        },
        # Step 5: Compute concentration
        {
            "tools": [
                {"name": "compute_concentration", "arguments": {
                    "positions": {"AAPL": 12500, "MSFT": 8200, "GOOG": 6400, "AMZN": 4800, "NVDA": 3200, "META": 5100},
                }},
            ],
            "response": "Analyzed concentration risk.",
        },
        # Step 6: Detect anomalies
        {
            "tools": [
                {"name": "detect_anomalies", "arguments": {
                    "portfolio_returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                }},
            ],
            "response": "Ran anomaly detection on portfolio returns.",
        },
        # Step 7: Compute factor exposure (with simulated factor data)
        {
            "tools": [
                {"name": "compute_factor_exposure", "arguments": {
                    "portfolio_returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                    "factor_returns": {
                        "market": [0.001, -0.001, 0.002, -0.010, 0.001, -0.002, 0.001, -0.020, 0.001, 0.000],
                        "momentum": [0.0005, -0.0015, 0.0025, -0.012, 0.0005, -0.0025, 0.0015, -0.022, 0.0005, -0.0005],
                    },
                    "factor_names": ["market", "momentum"],
                }},
            ],
            "response": "Computed factor exposures.",
        },
        # Step 8: Compute beta vs benchmark
        {
            "tools": [
                {"name": "compute_beta", "arguments": {
                    "portfolio_returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                    "benchmark_returns": [0.0008, -0.0015, 0.0025, -0.012, 0.0008, -0.0025, 0.0015, -0.022, 0.0008, -0.0008],
                }},
            ],
            "response": "Computed beta vs benchmark.",
        },
        # Step 9: Compute VaR/CVaR
        {
            "tools": [
                {"name": "compute_var_cvar", "arguments": {
                    "returns": [0.001, -0.002, 0.003, -0.015, 0.001, -0.003, 0.002, -0.025, 0.001, -0.001],
                    "confidence": 0.95,
                }},
            ],
            "response": "Computed Value at Risk and CVaR.",
        },
        # Step 10: Build the report
        {
            "tools": [
                {"name": "build_report", "arguments": {
                    "findings": [
                        {"artifact_type": "computation", "name": "portfolio_return", "value": 0.15},
                        {"artifact_type": "computation", "name": "sharpe", "value": 1.2},
                        {"artifact_type": "computation", "name": "drawdown", "value": 0.08},
                    ],
                    "risk_evaluations": [
                        {"artifact_type": "risk_evaluation", "is_compliant": True, "breaches": []},
                    ],
                    "methodology": "Deterministic quantitative analysis using SAS Quant Engine v1.0.0. All metrics computed from daily OHLCV data for the period 2024-01-02 through 2024-12-31.",
                    "title": "Apex Capital Partners — Portfolio Intelligence Report Q4 2024",
                }},
            ],
            "response": "Produced the final portfolio intelligence report with all required sections.",
        },
    ]


# ── Run the Full Pipeline ────────────────────────────────────────────────────

def run_portfolio_intelligence_pipeline() -> dict:
    """Run the full pipeline: world → toolbox → model → evaluation."""
    # 1. Load the world + task + rubric
    world = PORTFOLIO_INTELLIGENCE_WORLD
    task = PORTFOLIO_INTELLIGENCE_TASK
    rubric = PORTFOLIO_INTELLIGENCE_RUBRIC

    # 2. Create synthetic data provider
    data = create_test_data_provider(world)

    # 3. Create toolbox configured for the world
    toolbox = create_toolbox_from_world(
        world,
        seed=42,
    )

    # Inject synthetic data into toolbox
    from sas.quant.market import MarketDataProvider, DatasetInfo

    class SyntheticProvider(MarketDataProvider):
        def __init__(self, data: dict[str, pd.DataFrame]):
            self._data = data
        def get_prices(self, symbol, start, end):
            if symbol not in self._data:
                return pd.DataFrame()
            df = self._data[symbol]
            mask = (df.index >= start) & (df.index <= end)
            return df[mask]
        def get_bars(self, symbol, start, end, interval="1d"):
            return self.get_prices(symbol, start, end)
        def validate(self, symbol, start, end):
            df = self.get_prices(symbol, start, end)
            issues = []
            if df.empty:
                issues.append("No data found")
            if df.isnull().any().any():
                issues.append("Contains null values")
            if (df["high"] < df["low"]).any():
                issues.append("High < Low violations")
            return {"symbol": symbol, "valid": len(issues) == 0, "issues": issues, "rows": len(df)}
        def source_info(self):
            return DatasetInfo(
                source="synthetic", version="test-1.0",
                symbols=list(self._data.keys()),
                start_date="2024-01-02", end_date="2024-12-31",
                row_count=sum(len(d) for d in self._data.values())
            )

    toolbox.data_provider = SyntheticProvider(data)

    # 4. Create stub model with the scripted workflow
    script = create_portfolio_intelligence_script()
    model = StubModelAdapter(script=script)

    from sas.quant.agents import quant_coordinator
    agent = quant_coordinator()

    # 5. Create execution run
    run = ExecutionRun(
        run_id="e2e-test-001",
        task_id=task.id,
        world_id=world.id,
        agent_name=agent.name,
        agent_role=agent.role,
        model="stub-model",
        model_provider="local",
    )

    # 6. Prepare context and run model loop
    ctx = model.prepare_context(world, task, agent, None)
    result = model.run_loop(ctx, toolbox, run, max_steps=15)

    # 7. Mark run as completed
    run.status = result.get("status", "completed")
    run.end_time = "2024-12-31T12:00:00+00:00"
    run.tool_calls = result.get("tools_called", 0)

    # 8. Evaluate the run against the rubric
    evaluator = RunEvaluator(rubric)
    eval_result = evaluator.evaluate(run, world)

    # 9. Compute pass@k metrics
    all_evals = [eval_result]
    benchmark = aggregate_benchmark(all_evals, world.id, task.id)

    # 10. Sovereignty evaluation
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


# ── Run the pipeline ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Sovereign Quant — End-to-End Pipeline Test")
    print("=" * 60)

    result = run_portfolio_intelligence_pipeline()

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
