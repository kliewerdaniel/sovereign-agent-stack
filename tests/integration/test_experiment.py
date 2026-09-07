"""Integration tests for the governed research experiment."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.research.experiment import Experiment, ExperimentConfig


class TestExperiment:
    """Test the full experiment lifecycle."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="test-exp-001",
            world_id="test-world-001",
            trial_budget=5,
            research_window=("2024-01-01", "2024-09-30"),
            holdout_window=("2024-10-01", "2024-12-31"),
            model_id="test-model",
            task_id="test-task",
            random_seed=42,
            initial_capital=100_000.0,
            baseline_config=BaselineConfig(
                baseline_type="buy_and_hold",
                universe=["AAPL", "MSFT"],
                data_window=("2024-01-01", "2024-09-30"),
            ),
            gate_config=ResearchGateConfig(),
        )
        defaults.update(kwargs)
        return ExperimentConfig(**defaults)

    def test_experiment_creation(self):
        config = self._make_config()
        exp = Experiment(config)
        assert exp.experiment_id == "test-exp-001"
        assert exp.config.trial_budget == 5
        assert not exp.is_complete

    def test_compute_baseline(self):
        config = self._make_config()
        exp = Experiment(config)
        baseline = exp.compute_baseline()
        assert baseline is not None
        assert baseline.baseline_type == "buy_and_hold"
        assert baseline.universe == ["AAPL", "MSFT"]

    def test_temporal_enforcement_during_research(self):
        config = self._make_config()
        exp = Experiment(config)

        # Research window should be valid
        is_valid, error = exp.temporal_authority.validate_date_range(
            "2024-01-01", "2024-09-30"
        )
        assert is_valid

        # Holdout window should be invalid during research
        is_valid, error = exp.temporal_authority.validate_date_range(
            "2024-10-01", "2024-12-31"
        )
        assert not is_valid

    def test_transition_to_holdout(self):
        config = self._make_config()
        exp = Experiment(config)

        exp.temporal_authority.transition_to_holdout()
        assert exp.temporal_authority.capability.value == "holdout"

        # Now holdout data is accessible
        is_valid, error = exp.temporal_authority.validate_date_range(
            "2024-10-01", "2024-12-31"
        )
        assert is_valid

        # Research data is no longer accessible
        is_valid, error = exp.temporal_authority.validate_date_range(
            "2024-01-01", "2024-09-30"
        )
        assert not is_valid

    def test_one_way_transitions(self):
        config = self._make_config()
        exp = Experiment(config)

        exp.temporal_authority.transition_to_holdout()
        exp.temporal_authority.transition_to_final()

        with pytest.raises(ValueError):
            exp.temporal_authority.transition_to_holdout()

    def test_event_log_tracks_transitions(self):
        config = self._make_config()
        exp = Experiment(config)

        # Record events for transitions
        exp.event_log.record(event_type="research.started", actor="researcher")
        exp.temporal_authority.transition_to_holdout()
        exp.event_log.record(event_type="holdout.opened", actor="system")
        exp.temporal_authority.transition_to_final()
        exp.event_log.record(event_type="experiment.completed", actor="system")

        events = exp.event_log.events
        assert len(events) > 0
        assert any(e.event_type == "research.started" for e in events)
        assert any(e.event_type == "holdout.opened" for e in events)
        assert any(e.event_type == "experiment.completed" for e in events)

    def test_trial_ledger_integration(self):
        config = self._make_config(trial_budget=3)
        exp = Experiment(config)

        t1 = exp.trial_ledger.record_trial(strategy_spec={"name": "t1"})
        t2 = exp.trial_ledger.record_trial(strategy_spec={"name": "t2"})

        assert exp.trial_ledger.total_trials == 2

        exp.trial_ledger.record_backtest_result(
            trial_id=t1.trial_id,
            backtest_result={"sharpe_ratio": 1.5, "total_return": 0.10},
        )
        exp.trial_ledger.record_backtest_result(
            trial_id=t2.trial_id,
            backtest_result={"sharpe_ratio": 0.8, "total_return": 0.05},
        )

        evaluated = exp.trial_ledger.get_evaluated_trials()
        assert len(evaluated) == 2

    def test_statistics_computation(self):
        config = self._make_config(trial_budget=5)
        exp = Experiment(config)

        # Add some trials with return series
        for i in range(3):
            t = exp.trial_ledger.record_trial(strategy_spec={"name": f"t{i}"})
            exp.trial_ledger.record_backtest_result(
                trial_id=t.trial_id,
                backtest_result={"sharpe_ratio": 0.5 + i * 0.3, "total_return": 0.05 * i},
                return_series=[0.01, 0.02, -0.01, 0.015, 0.005],
            )

        stats = exp.compute_statistics()
        assert "dsr" in stats
        assert "pbo" in stats

    def test_experiment_to_dict(self):
        config = self._make_config()
        exp = Experiment(config)
        d = exp.to_dict()
        assert d["experiment_id"] == "test-exp-001"
        assert d["config"]["trial_budget"] == 5
