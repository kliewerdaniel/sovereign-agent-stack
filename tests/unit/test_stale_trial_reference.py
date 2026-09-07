"""Regression tests for the stale trial reference bug.

The append-only trial ledger creates new TrialArtifact instances on each
mutation. Callers must not use previously materialized references.

Invariant: The ledger is the state. Objects are views of ledger state.
"""

from __future__ import annotations

import uuid

import pytest

from sas.quant.provenance.artifacts import TrialArtifact
from sas.quant.research.trial import TrialLedger


class TestStaleTrialReference:
    """Tests that the ledger prevents stale reference bugs."""

    def _make_ledger(self) -> TrialLedger:
        return TrialLedger(experiment_id=f"test-{uuid.uuid4().hex[:8]}")

    def test_record_trial_returns_artifact(self, ledger: TrialLedger | None = None):
        """record_trial returns the created artifact."""
        ledger = ledger or self._make_ledger()
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )
        assert trial is not None
        assert trial.trial_id is not None
        assert trial.was_evaluated is False
        assert trial.backtest_result is None

    def test_record_backtest_result_returns_authoritative_trial(self):
        """record_backtest_result returns the updated authoritative trial."""
        ledger = self._make_ledger()
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )
        original_trial = trial

        # Append backtest result
        updated = ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 1.5, "total_return": 0.1},
            return_series=[0.01, 0.02],
        )

        # The returned artifact is the authoritative current state
        assert updated is not None
        assert updated.was_evaluated is True
        assert updated.backtest_result is not None
        assert updated.backtest_result["sharpe_ratio"] == 1.5

        # The original object remains unevaluated (immutability)
        assert original_trial.was_evaluated is False
        assert original_trial.backtest_result is None

    def test_get_trial_returns_authoritative_state(self):
        """get_trial always returns the current authoritative state."""
        ledger = self._make_ledger()
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )

        # Before backtest
        t1 = ledger.get_trial(trial.trial_id)
        assert t1 is not None
        assert t1.was_evaluated is False

        # After backtest
        ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 2.0},
        )
        t2 = ledger.get_trial(trial.trial_id)
        assert t2 is not None
        assert t2.was_evaluated is True
        assert t2.backtest_result["sharpe_ratio"] == 2.0

    def test_stale_reference_does_not_affect_incumbent_selection(self):
        """The critical regression: stale trial objects must not be used for incumbent selection."""
        ledger = self._make_ledger()

        # Create two trials
        trial1 = ledger.record_trial(
            strategy_spec={"name": "t1"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )
        trial2 = ledger.record_trial(
            strategy_spec={"name": "t2"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=43,
        )

        # Backtest trial1 with lower Sharpe
        ledger.record_backtest_result(
            trial_id=trial1.trial_id,
            backtest_result={"sharpe_ratio": 1.0},
        )

        # Backtest trial2 with higher Sharpe
        ledger.record_backtest_result(
            trial_id=trial2.trial_id,
            backtest_result={"sharpe_ratio": 2.0},
        )

        # Get authoritative state
        auth1 = ledger.get_trial(trial1.trial_id)
        auth2 = ledger.get_trial(trial2.trial_id)

        # Both should be evaluated
        assert auth1.was_evaluated is True
        assert auth2.was_evaluated is True

        # The stale original objects should remain unevaluated
        assert trial1.was_evaluated is False
        assert trial2.was_evaluated is False

        # Set incumbent using authoritative state
        ledger.set_incumbent(auth2.trial_id)
        incumbent = ledger.get_incumbent()
        assert incumbent is not None
        assert incumbent.trial_id == auth2.trial_id
        assert incumbent.backtest_result["sharpe_ratio"] == 2.0

    def test_record_rejection_returns_authoritative_trial(self):
        """record_rejection also returns the updated trial."""
        ledger = self._make_ledger()
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )

        updated = ledger.record_rejection(
            trial_id=trial.trial_id,
            reason="Backtest failed",
        )

        assert updated is not None
        assert updated.rejection_reason == "Backtest failed"
        assert updated.was_evaluated is False

    def test_link_critique_returns_authoritative_trial(self):
        """link_critique returns the updated trial."""
        ledger = self._make_ledger()
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )

        critique_id = "critique-123"
        updated = ledger.link_critique(
            trial_id=trial.trial_id,
            critique_id=critique_id,
        )

        assert updated is not None
        assert updated.critique_id == critique_id

    def test_get_evaluated_trials_returns_authoritative_state(self):
        """get_evaluated_trials returns trials with backtest results using authoritative state."""
        ledger = self._make_ledger()

        # Create 3 trials, backtest only 2
        t1 = ledger.record_trial(
            strategy_spec={"name": "t1"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )
        t2 = ledger.record_trial(
            strategy_spec={"name": "t2"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=43,
        )
        t3 = ledger.record_trial(
            strategy_spec={"name": "t3"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=44,
        )

        ledger.record_backtest_result(
            trial_id=t1.trial_id,
            backtest_result={"sharpe_ratio": 1.0},
        )
        ledger.record_backtest_result(
            trial_id=t3.trial_id,
            backtest_result={"sharpe_ratio": 1.5},
        )

        evaluated = ledger.get_evaluated_trials()
        assert len(evaluated) == 2
        evaluated_ids = {t.trial_id for t in evaluated}
        assert t1.trial_id in evaluated_ids
        assert t3.trial_id in evaluated_ids
        assert t2.trial_id not in evaluated_ids

    def test_multiple_backtest_results_use_latest(self):
        """If backtest is recorded multiple times, the latest is authoritative."""
        ledger = self._make_ledger()
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )

        # First backtest
        ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 1.0},
        )

        # Second backtest (revision)
        ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 2.0},
        )

        # Authoritative state should reflect the latest
        auth = ledger.get_trial(trial.trial_id)
        assert auth is not None
        assert auth.backtest_result["sharpe_ratio"] == 2.0

        # Original stale object should remain unevaluated
        assert trial.was_evaluated is False


class TestLedgerInvariants:
    """Tests for ledger-level invariants."""

    def test_immutability_of_original_trial(self):
        """Original trial objects must not be mutated after creation."""
        ledger = TrialLedger(experiment_id="test")
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )

        # Store original state
        original_id = trial.trial_id
        original_evaluated = trial.was_evaluated

        # Mutate ledger
        ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 5.0},
        )

        # Original object unchanged
        assert trial.trial_id == original_id
        assert trial.was_evaluated == original_evaluated

    def test_ledger_is_authoritative_source_of_truth(self):
        """The ledger dict is the single source of truth, not materialized objects."""
        ledger = TrialLedger(experiment_id="test")
        trial = ledger.record_trial(
            strategy_spec={"name": "test"},
            model_id="test-model",
            task_id="test-task",
            data_window=("2024-01-01", "2024-12-31"),
            random_seed=42,
        )

        # Get a reference
        ref1 = ledger.get_trial(trial.trial_id)
        assert ref1 is not None
        assert ref1.was_evaluated is False

        # Mutate
        ledger.record_backtest_result(
            trial_id=trial.trial_id,
            backtest_result={"sharpe_ratio": 3.0},
        )

        # Get a new reference
        ref2 = ledger.get_trial(trial.trial_id)
        assert ref2 is not None

        # ref2 is the authoritative current state
        assert ref2.was_evaluated is True
        assert ref2.backtest_result is not None
        assert ref2.backtest_result["sharpe_ratio"] == 3.0

        # ref1 is now a stale view - it still points to the old immutable artifact
        assert ref1.was_evaluated is False
        assert ref1.backtest_result is None

        # The latest get_trial call returns the updated artifact
        assert ref2 is not ref1
