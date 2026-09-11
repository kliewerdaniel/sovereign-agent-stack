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


from sas.quant.worlds.runner import (
    SyntheticProvider,
    create_test_data_provider,
    generate_synthetic_prices,
    create_portfolio_intelligence_script,
    create_risk_parity_script,
    create_momentum_script,
    run_pipeline,
)


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
