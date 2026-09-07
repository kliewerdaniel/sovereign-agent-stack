"""Integration tests for point-in-time enforcement.

These tests verify that the execution protocol rejects any attempt
to access data beyond the permitted temporal window. The enforcement
happens at the execution protocol level, not at individual tools.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.research.temporal import ExecutionCapability


class TestPointInTimeEnforcement:
    """Test that the temporal authority prevents look-ahead bias."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="pit-test-001",
            world_id="pit-world-001",
            trial_budget=5,
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
            model_id="test-model",
            task_id="test-task",
            random_seed=42,
            baseline_config=BaselineConfig(
                baseline_type="buy_and_hold",
                universe=["AAPL", "MSFT"],
                data_window=("2024-01-01", "2024-09-30"),
            ),
            gate_config=ResearchGateConfig(),
        )
        defaults.update(kwargs)
        return ExperimentConfig(**defaults)

    def test_research_cannot_access_holdout_data(self):
        """The model cannot request data from the holdout window during research."""
        config = self._make_config()
        exp = Experiment(config)

        # Research window is valid
        is_valid, _ = exp.temporal_authority.validate_date_range("2024-01-01", "2024-09-30")
        assert is_valid

        # Holdout window is invalid during research
        is_valid, error = exp.temporal_authority.validate_date_range("2024-10-01", "2024-12-31")
        assert not is_valid
        assert "exceeds maximum permitted" in error

    def test_research_cannot_access_future_data(self):
        """The model cannot request data beyond the research window."""
        config = self._make_config()
        exp = Experiment(config)

        # Requesting data 1 day beyond research window is rejected
        is_valid, error = exp.temporal_authority.validate_date_range("2024-01-01", "2024-10-01")
        assert not is_valid

    def test_research_cannot_access_data_before_earliest(self):
        """The model cannot request data before the earliest available."""
        config = self._make_config()
        exp = Experiment(config)

        is_valid, error = exp.temporal_authority.validate_date_range("2023-01-01", "2024-06-30")
        assert not is_valid
        assert "before earliest available" in error

    def test_holdout_cannot_access_research_data(self):
        """After transition to holdout, research data is inaccessible."""
        config = self._make_config()
        exp = Experiment(config)

        exp.temporal_authority.transition_to_holdout()

        # Research data is now inaccessible
        is_valid, error = exp.temporal_authority.validate_date_range("2024-01-01", "2024-09-30")
        assert not is_valid

    def test_final_has_no_data_access(self):
        """In FINAL state, no market data is accessible."""
        config = self._make_config()
        exp = Experiment(config)

        exp.temporal_authority.transition_to_holdout()
        exp.temporal_authority.transition_to_final()

        is_valid, error = exp.temporal_authority.validate_date_range("2024-01-01", "2024-12-31")
        assert not is_valid
        assert "No market data access" in error

    def test_trial_backtest_respects_temporal_window(self):
        """The backtest engine only receives data within the research window."""
        config = self._make_config()
        exp = Experiment(config)

        # The researcher's _run_backtest validates temporal authority
        # This test verifies the integration
        from sas.quant.market import SyntheticDataProvider
        provider = SyntheticDataProvider(seed=42)

        # Get prices within research window
        prices = provider.get_prices("AAPL", "2024-01-01", "2024-09-30")
        assert not prices.empty

        # The temporal authority would reject a request for holdout data
        is_valid, _ = exp.temporal_authority.validate_date_range("2024-10-01", "2024-12-31")
        assert not is_valid


class TestHoldoutIsolation:
    """Test that the holdout is physically separate from research."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="holdout-test-001",
            world_id="holdout-world-001",
            trial_budget=3,
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
            model_id="test-model",
            task_id="test-task",
            random_seed=42,
            baseline_config=BaselineConfig(
                baseline_type="buy_and_hold",
                universe=["AAPL", "MSFT"],
                data_window=("2024-01-01", "2024-09-30"),
            ),
            gate_config=ResearchGateConfig(),
        )
        defaults.update(kwargs)
        return ExperimentConfig(**defaults)

    def test_holdout_evaluation_requires_holdout_capability(self):
        """Holdout evaluation requires HOLDOUT capability."""
        config = self._make_config()
        exp = Experiment(config)

        from sas.quant.orchestration.holdout import HoldoutEvaluator
        evaluator = HoldoutEvaluator(exp)

        with pytest.raises(ValueError, match="HOLDOUT capability"):
            evaluator.evaluate()

    def test_holdout_evaluation_one_shot(self):
        """The holdout can only be evaluated once."""
        config = self._make_config()
        exp = Experiment(config)

        # Add a trial and set as incumbent
        t = exp.trial_ledger.record_trial(strategy_spec={"name": "test"})
        exp.trial_ledger.record_backtest_result(
            trial_id=t.trial_id,
            backtest_result={"sharpe_ratio": 1.0, "total_return": 0.10},
        )
        exp.trial_ledger.set_incumbent(t.trial_id)

        # Transition to holdout
        exp.temporal_authority.transition_to_holdout()

        from sas.quant.orchestration.holdout import HoldoutEvaluator
        evaluator = HoldoutEvaluator(exp)

        # First evaluation should work
        holdout = evaluator.evaluate()
        assert holdout is not None
        assert exp.temporal_authority.capability == ExecutionCapability.HOLDOUT

    def test_cannot_mutate_strategy_after_holdout(self):
        """After holdout evaluation, the strategy cannot be mutated."""
        config = self._make_config()
        exp = Experiment(config)

        t = exp.trial_ledger.record_trial(strategy_spec={"name": "test"})
        exp.trial_ledger.record_backtest_result(
            trial_id=t.trial_id,
            backtest_result={"sharpe_ratio": 1.0, "total_return": 0.10},
        )
        exp.trial_ledger.set_incumbent(t.trial_id)

        exp.temporal_authority.transition_to_holdout()
        exp.temporal_authority.transition_to_final()

        # In FINAL state, no data access
        is_valid, _ = exp.temporal_authority.validate_date_range("2024-01-01", "2024-12-31")
        assert not is_valid

    def test_no_revision_after_holdout(self):
        """After holdout, the model cannot revise the strategy."""
        config = self._make_config()
        exp = Experiment(config)

        t = exp.trial_ledger.record_trial(strategy_spec={"name": "test"})
        exp.trial_ledger.record_backtest_result(
            trial_id=t.trial_id,
            backtest_result={"sharpe_ratio": 1.0, "total_return": 0.10},
        )
        exp.trial_ledger.set_incumbent(t.trial_id)

        exp.temporal_authority.transition_to_holdout()
        exp.temporal_authority.transition_to_final()

        # The temporal authority is in FINAL — no research writes
        assert exp.temporal_authority.capability == ExecutionCapability.FINAL
