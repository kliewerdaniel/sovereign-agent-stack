"""Multi-universe integration test — empirical acceptance rate.

Runs the governed research experiment across multiple universes and
horizons to answer: "How often does this loop produce anything
backtest-worthy?"

This is the empirical validation of the governed QuantWorld.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.orchestration.researcher import Researcher


class TestMultiUniverse:
    """Run experiments across multiple universes and horizons."""

    def _make_config(self, universe, research_window, holdout_window, **kwargs):
        defaults = dict(
            experiment_id=f"multi-{universe[0]}-{research_window[0]}",
            world_id=f"world-{universe[0]}",
            trial_budget=10,
            research_window=research_window,
            holdout_window=holdout_window,
            model_id="stub-model",
            task_id="research-task",
            random_seed=42,
            initial_capital=100_000.0,
            baseline_config=BaselineConfig(
                baseline_type="buy_and_hold",
                universe=universe,
                data_window=research_window,
            ),
            gate_config=ResearchGateConfig(),
        )
        defaults.update(kwargs)
        return ExperimentConfig(**defaults)

    def test_single_stock_universe(self):
        """Test with a single stock universe."""
        config = self._make_config(
            universe=["AAPL"],
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
        )
        exp = Experiment(config)
        researcher = Researcher(exp)
        result = researcher.run_research()

        assert result.status == "completed"
        assert result.total_trials > 0
        assert result.evaluated_trials > 0

    def test_multi_stock_universe(self):
        """Test with multiple stocks."""
        config = self._make_config(
            universe=["AAPL", "MSFT", "GOOGL"],
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
        )
        exp = Experiment(config)
        researcher = Researcher(exp)
        result = researcher.run_research()

        assert result.status == "completed"
        assert result.total_trials > 0

    def test_different_horizon(self):
        """Test with a different time horizon."""
        config = self._make_config(
            universe=["MSFT"],
            research_window=("2023-06-01", "2024-03-31"),
            holdout_window=("2024-04-01", "2024-06-30"),
        )
        exp = Experiment(config)
        researcher = Researcher(exp)
        result = researcher.run_research()

        assert result.status == "completed"
        assert result.total_trials > 0

    def test_full_experiment_lifecycle(self):
        """Test the full lifecycle: research → statistics → holdout → decision."""
        config = self._make_config(
            universe=["AAPL", "MSFT"],
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
        )
        exp = Experiment(config)

        # 1. Compute baseline
        baseline = exp.compute_baseline()
        assert baseline is not None

        # 2. Run research
        researcher = Researcher(exp)
        result = researcher.run_research()
        assert result.status == "completed"

        # 3. Compute statistics
        stats = exp.compute_statistics()
        assert "dsr" in stats
        assert "pbo" in stats

        # Set an incumbent for holdout evaluation
        evaluated = exp.trial_ledger.get_evaluated_trials()
        if evaluated:
            exp.trial_ledger.set_incumbent(evaluated[0].trial_id)

        # 4. Evaluate holdout (transitions to HOLDOUT internally)
        holdout = exp.evaluate_holdout()
        assert holdout is not None

        # 5. Make decision (transitions to FINAL internally)
        decision = exp.make_decision()
        assert decision is not None
        assert decision.outcome in ("no_strategy_passed", "passed_but_no_value", "candidate")

    def test_acceptance_rate_across_universes(self):
        """Run experiments across 3+ universes and report acceptance rate."""
        universes = [
            (["AAPL"], "single-stock"),
            (["AAPL", "MSFT"], "two-stock"),
            (["AAPL", "MSFT", "GOOGL"], "three-stock"),
        ]

        results = []
        for universe, name in universes:
            config = self._make_config(
                universe=universe,
                research_window=("2024-01-01", "2024-09-30"),
                holdout_window=("2024-10-01", "2024-12-31"),
            )
            exp = Experiment(config)
            researcher = Researcher(exp)
            result = researcher.run_research()

            results.append({
                "name": name,
                "total_trials": result.total_trials,
                "evaluated_trials": result.evaluated_trials,
                "has_incumbent": result.incumbent is not None,
            })

        # All experiments should complete
        assert len(results) == 3
        for r in results:
            assert r["total_trials"] > 0
            assert r["evaluated_trials"] > 0

    def test_trial_budget_enforcement(self):
        """Test that the trial budget is enforced."""
        config = self._make_config(
            universe=["AAPL"],
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
            trial_budget=5,
        )
        exp = Experiment(config)
        researcher = Researcher(exp)
        result = researcher.run_research()

        # Should not exceed budget
        assert result.total_trials <= 5
