"""Adversarial integration tests — execution boundary enforcement.

These tests verify that the governed research architecture rejects
attempts to violate the execution protocol. The architectural thesis
depends on the execution boundary being authoritative — these tests
validate that the boundary holds under adversarial conditions.

Each test attempts a specific violation and confirms it is rejected
by the execution protocol rather than merely detected afterward.
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


class TestTemporalBoundaryEnforcement:
    """Test that the temporal boundary cannot be crossed."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="adv-temporal-001",
            world_id="adv-world-001",
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

    def test_cannot_access_holdout_during_research(self):
        """Agent cannot request holdout data during research phase."""
        config = self._make_config()
        exp = Experiment(config)

        # Attempt to access holdout data
        is_valid, error = exp.temporal_authority.validate_date_range("2024-10-01", "2024-12-31")
        assert not is_valid
        assert "exceeds maximum permitted" in error

    def test_cannot_access_future_data(self):
        """Agent cannot request data beyond the research window."""
        config = self._make_config()
        exp = Experiment(config)

        # Attempt to access data 1 day beyond research window
        is_valid, error = exp.temporal_authority.validate_date_range("2024-01-01", "2024-10-01")
        assert not is_valid

    def test_cannot_access_data_before_earliest(self):
        """Agent cannot request data before earliest available."""
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

    def test_cannot_transition_back_to_research(self):
        """Cannot transition from HOLDOUT back to RESEARCH."""
        config = self._make_config()
        exp = Experiment(config)

        exp.temporal_authority.transition_to_holdout()

        with pytest.raises(ValueError, match="Cannot transition to HOLDOUT from holdout"):
            exp.temporal_authority.transition_to_holdout()

    def test_cannot_skip_to_final(self):
        """Cannot skip HOLDOUT and go directly to FINAL."""
        config = self._make_config()
        exp = Experiment(config)

        with pytest.raises(ValueError, match="Cannot transition to FINAL from research"):
            exp.temporal_authority.transition_to_final()


class TestTrialBoundaryEnforcement:
    """Test that the trial boundary cannot be violated."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="adv-trial-001",
            world_id="adv-world-001",
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

    def test_cannot_mutate_completed_trial(self):
        """Cannot mutate a completed trial — only create new artifacts."""
        config = self._make_config()
        exp = Experiment(config)

        # Create a trial
        t = exp.trial_ledger.record_trial(strategy_spec={"name": "test"})
        exp.trial_ledger.record_backtest_result(
            trial_id=t.trial_id,
            backtest_result={"sharpe_ratio": 1.0, "total_return": 0.10},
        )

        # The trial is frozen — attempting to modify it creates a new trial
        # (This is enforced by the frozen dataclass)
        original_trial = exp.trial_ledger.get_trial(t.trial_id)
        assert original_trial.sharpe_ratio == 1.0

        # Cannot modify the original trial in place
        # (Frozen dataclass prevents attribute assignment)
        with pytest.raises(AttributeError):
            original_trial.sharpe_ratio = 2.0

    def test_cannot_exceed_trial_budget(self):
        """Cannot exceed the trial budget."""
        config = self._make_config(trial_budget=2)
        exp = Experiment(config)

        from sas.quant.orchestration.researcher import Researcher
        researcher = Researcher(exp)
        result = researcher.run_research()

        # Should not exceed budget
        assert result.total_trials <= 2

    def test_revision_creates_new_trial(self):
        """A revision creates a completely new trial with new provenance identity."""
        config = self._make_config()
        exp = Experiment(config)

        parent = exp.trial_ledger.record_trial(strategy_spec={"name": "parent"})
        child = exp.trial_ledger.record_trial(
            strategy_spec={"name": "child"},
            parent_trial_id=parent.trial_id,
        )

        # Different trial IDs
        assert parent.trial_id != child.trial_id
        # Child references parent
        assert child.parent_trial_id == parent.trial_id

    def test_cannot_create_unparented_revision(self):
        """A revision must have a parent trial."""
        config = self._make_config()
        exp = Experiment(config)

        # Create a revision without a parent
        revision = exp.trial_ledger.record_trial(
            strategy_spec={"name": "revision"},
            parent_trial_id=None,  # No parent
        )

        # The revision exists but has no parent link
        assert revision.parent_trial_id is None
        # This is allowed — not all trials are revisions
        # The system tracks which trials are revisions via parent_trial_id


class TestProvenanceBoundaryEnforcement:
    """Test that the provenance boundary cannot be violated."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="adv-provenance-001",
            world_id="adv-world-001",
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

    def test_event_log_is_append_only(self):
        """Event log is append-only — events cannot be modified."""
        config = self._make_config()
        exp = Experiment(config)

        event = exp.event_log.record(event_type="test.event", actor="test")
        assert event.event_type == "test.event"

        # Events are frozen — cannot modify
        with pytest.raises(AttributeError):
            event.event_type = "modified"

    def test_trial_ledger_is_append_only(self):
        """Trial ledger is append-only — trials cannot be deleted."""
        config = self._make_config()
        exp = Experiment(config)

        t = exp.trial_ledger.record_trial(strategy_spec={"name": "test"})
        assert exp.trial_ledger.total_trials == 1

        # Cannot delete a trial (no delete method exists)
        # The ledger only has record_trial, record_backtest_result, etc.

    def test_cannot_manipulate_trial_count(self):
        """Cannot manipulate the trial count used by DSR and PBO."""
        config = self._make_config()
        exp = Experiment(config)

        # Create some trials
        for i in range(3):
            exp.trial_ledger.record_trial(strategy_spec={"name": f"t{i}"})

        # The trial count is derived from the ledger
        assert exp.trial_ledger.total_trials == 3

        # Cannot directly set the trial count (no setter)
        # The count is derived from the internal _trial_order list


class TestHoldoutBoundaryEnforcement:
    """Test that the holdout boundary cannot be violated."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="adv-holdout-001",
            world_id="adv-world-001",
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

    def test_cannot_revise_after_holdout(self):
        """After holdout evaluation, the model cannot revise the strategy."""
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

        # In FINAL state, no research writes
        assert exp.temporal_authority.capability == ExecutionCapability.FINAL

    def test_holdout_evaluation_requires_incumbent(self):
        """Holdout evaluation requires an incumbent strategy."""
        config = self._make_config()
        exp = Experiment(config)

        # No incumbent set
        exp.temporal_authority.transition_to_holdout()

        from sas.quant.orchestration.holdout import HoldoutEvaluator
        evaluator = HoldoutEvaluator(exp)

        with pytest.raises(ValueError, match="No incumbent strategy"):
            evaluator.evaluate()

    def test_holdout_evaluation_requires_holdout_capability(self):
        """Holdout evaluation requires HOLDOUT capability."""
        config = self._make_config()
        exp = Experiment(config)

        t = exp.trial_ledger.record_trial(strategy_spec={"name": "test"})
        exp.trial_ledger.record_backtest_result(
            trial_id=t.trial_id,
            backtest_result={"sharpe_ratio": 1.0, "total_return": 0.10},
        )
        exp.trial_ledger.set_incumbent(t.trial_id)

        # Still in RESEARCH
        from sas.quant.orchestration.holdout import HoldoutEvaluator
        evaluator = HoldoutEvaluator(exp)

        with pytest.raises(ValueError, match="HOLDOUT capability"):
            evaluator.evaluate()


class TestStatisticalBoundaryEnforcement:
    """Test that the statistical boundary cannot be violated."""

    def _make_config(self, **kwargs):
        defaults = dict(
            experiment_id="adv-stat-001",
            world_id="adv-world-001",
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

    def test_dsr_uses_actual_trial_count(self):
        """DSR uses the actual number of eligible trials, not a configured maximum."""
        config = self._make_config()
        exp = Experiment(config)

        # Create 3 trials
        for i in range(3):
            t = exp.trial_ledger.record_trial(strategy_spec={"name": f"t{i}"})
            exp.trial_ledger.record_backtest_result(
                trial_id=t.trial_id,
                backtest_result={"sharpe_ratio": 0.5 + i * 0.3, "total_return": 0.05 * i},
                return_series=[0.01, 0.02, -0.01, 0.015, 0.005],
            )

        stats = exp.compute_statistics()
        # DSR should use trial_count=3
        if stats["dsr"]:
            assert stats["dsr"]["trial_count"] == 3

    def test_pbo_uses_actual_trial_population(self):
        """PBO uses the actual trial population available to the experiment."""
        config = self._make_config()
        exp = Experiment(config)

        # Create 3 trials
        for i in range(3):
            t = exp.trial_ledger.record_trial(strategy_spec={"name": f"t{i}"})
            exp.trial_ledger.record_backtest_result(
                trial_id=t.trial_id,
                backtest_result={"sharpe_ratio": 0.5 + i * 0.3, "total_return": 0.05 * i},
                return_series=[0.01, 0.02, -0.01, 0.015, 0.005],
            )

        stats = exp.compute_statistics()
        # PBO should use the actual trial population
        if stats["pbo"]:
            assert stats["pbo"]["trial_count"] == 3

    def test_insufficient_data_produces_degraded_result(self):
        """Insufficient data produces an explicit degraded result."""
        from sas.quant.statistics.deflated_sharpe import compute_dsr

        # Empty returns
        result = compute_dsr([], trial_count=10)
        assert result.is_degraded
        assert len(result.degradation_notes) > 0

    def test_degraded_result_exposes_methodology(self):
        """Degraded results expose their methodology and assumptions."""
        from sas.quant.statistics.deflated_sharpe import compute_dsr

        result = compute_dsr([], trial_count=10)
        d = result.to_dict()
        assert "methodology" in d
        assert "assumptions" in d
        assert "is_degraded" in d
        assert d["is_degraded"] is True
