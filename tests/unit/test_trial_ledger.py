"""Unit tests for the trial ledger."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.research.trial import TrialLedger


class TestTrialLedger:
    """Test the trial ledger's append-only semantics."""

    def setup_method(self):
        self.ledger = TrialLedger(experiment_id="test-exp-001")

    def test_record_trial(self):
        trial = self.ledger.record_trial(
            strategy_spec={"name": "test-strategy", "signal_type": "momentum"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )
        assert trial.trial_id is not None
        assert trial.trial_number == 1
        assert trial.experiment_id == "test-exp-001"
        assert trial.strategy_spec["name"] == "test-strategy"

    def test_trial_ordering(self):
        t1 = self.ledger.record_trial(strategy_spec={"name": "t1"})
        t2 = self.ledger.record_trial(strategy_spec={"name": "t2"})
        t3 = self.ledger.record_trial(strategy_spec={"name": "t3"})

        all_trials = self.ledger.get_all_trials()
        assert len(all_trials) == 3
        assert all_trials[0].trial_id == t1.trial_id
        assert all_trials[1].trial_id == t2.trial_id
        assert all_trials[2].trial_id == t3.trial_id

    def test_record_backtest_result(self):
        trial = self.ledger.record_trial(strategy_spec={"name": "test"})
        self.ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 1.5, "total_return": 0.10},
            return_series=[0.01, 0.02, -0.01],
        )

        updated = self.ledger.get_trial(trial.trial_id)
        assert updated.backtest_result is not None
        assert updated.backtest_result["sharpe_ratio"] == 1.5
        assert updated.return_series == [0.01, 0.02, -0.01]
        assert updated.was_evaluated

    def test_proposed_but_not_evaluated(self):
        trial = self.ledger.record_trial(strategy_spec={"name": "test"})
        assert not trial.was_evaluated
        assert trial.backtest_result is None

    def test_record_rejection(self):
        trial = self.ledger.record_trial(strategy_spec={"name": "test"})
        self.ledger.record_rejection(trial.trial_id, "Failed risk gate")

        updated = self.ledger.get_trial(trial.trial_id)
        assert updated.rejection_reason == "Failed risk gate"

    def test_set_incumbent(self):
        t1 = self.ledger.record_trial(strategy_spec={"name": "t1"})
        t2 = self.ledger.record_trial(strategy_spec={"name": "t2"})

        self.ledger.set_incumbent(t1.trial_id)
        assert self.ledger.get_incumbent().trial_id == t1.trial_id

        # Change incumbent
        self.ledger.set_incumbent(t2.trial_id)
        assert self.ledger.get_incumbent().trial_id == t2.trial_id
        # Previous incumbent is no longer incumbent
        assert not self.ledger.get_trial(t1.trial_id).is_incumbent

    def test_parent_child_relationship(self):
        parent = self.ledger.record_trial(strategy_spec={"name": "parent"})
        child = self.ledger.record_trial(
            strategy_spec={"name": "child"},
            parent_trial_id=parent.trial_id,
        )

        assert child.parent_trial_id == parent.trial_id

        # Get trial tree
        tree = self.ledger.get_trial_tree(child.trial_id)
        assert len(tree) == 2
        assert tree[0].trial_id == parent.trial_id
        assert tree[1].trial_id == child.trial_id

    def test_get_evaluated_trials(self):
        t1 = self.ledger.record_trial(strategy_spec={"name": "t1"})
        t2 = self.ledger.record_trial(strategy_spec={"name": "t2"})
        t3 = self.ledger.record_trial(strategy_spec={"name": "t3"})

        self.ledger.record_backtest_result(
            trial_id=t1.trial_id,
            backtest_result={"sharpe_ratio": 1.0},
        )
        # t2 not evaluated
        self.ledger.record_backtest_result(
            trial_id=t3.trial_id,
            backtest_result={"sharpe_ratio": 0.5},
        )

        evaluated = self.ledger.get_evaluated_trials()
        assert len(evaluated) == 2
        assert evaluated[0].trial_id == t1.trial_id
        assert evaluated[1].trial_id == t3.trial_id

    def test_total_trials_count(self):
        assert self.ledger.total_trials == 0
        self.ledger.record_trial(strategy_spec={"name": "t1"})
        assert self.ledger.total_trials == 1
        self.ledger.record_trial(strategy_spec={"name": "t2"})
        assert self.ledger.total_trials == 2

    def test_to_dict(self):
        trial = self.ledger.record_trial(strategy_spec={"name": "test"})
        d = self.ledger.to_dict()
        assert d["experiment_id"] == "test-exp-001"
        assert d["total_trials"] == 1
        assert len(d["trials"]) == 1
