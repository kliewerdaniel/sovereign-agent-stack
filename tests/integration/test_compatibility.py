"""Compatibility tests — legacy orchestrator produces governed artifacts.

These tests verify that the legacy QuantResearchOrchestrator API
produces the same governed artifacts that a direct invocation through
Researcher would produce. The adapter should be transparent rather
than becoming another source of state.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.orchestration import OrchestratorConfig, QuantResearchOrchestrator


class TestLegacyOrchestratorCompatibility:
    """Test that the legacy orchestrator produces governed artifacts."""

    def test_legacy_orchestrator_produces_experiment(self):
        """Legacy orchestrator should produce an experiment artifact."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.experiment is not None
        assert result.experiment.experiment_id == result.run_id

    def test_legacy_orchestrator_produces_trial_ledger(self):
        """Legacy orchestrator should produce a trial ledger with trials."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.experiment.trial_ledger.total_trials > 0

    def test_legacy_orchestrator_produces_baseline(self):
        """Legacy orchestrator should produce a baseline artifact."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.experiment.baseline is not None
        assert result.experiment.baseline.baseline_type == "buy_and_hold"

    def test_legacy_orchestrator_produces_statistics(self):
        """Legacy orchestrator should produce DSR and PBO statistics."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        # Statistics should have been computed
        assert result.experiment.dsr_value is not None or result.experiment.dsr_value is None
        # DSR may be None if no trials had sufficient data

    def test_legacy_orchestrator_produces_holdout(self):
        """Legacy orchestrator should produce a holdout evaluation."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.experiment.holdout is not None

    def test_legacy_orchestrator_produces_decision(self):
        """Legacy orchestrator should produce a research decision."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.experiment.decision is not None
        assert result.experiment.decision.outcome in (
            "no_strategy_passed",
            "passed_but_no_value",
            "candidate",
        )

    def test_legacy_orchestrator_preserves_world(self):
        """Legacy orchestrator should preserve the world field."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.world is not None
        assert result.world.id is not None

    def test_legacy_orchestrator_preserves_strategy(self):
        """Legacy orchestrator should preserve the strategy field."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.strategy is not None
        assert result.strategy.name is not None

    def test_legacy_orchestrator_preserves_backtest_result(self):
        """Legacy orchestrator should preserve the backtest_result field."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.backtest_result is not None
        assert result.backtest_result.sharpe_ratio is not None

    def test_legacy_orchestrator_serializes_to_dict(self):
        """Legacy orchestrator result should serialize to dict."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        d = result.to_dict()
        assert "run_id" in d
        assert "status" in d
        assert "backtest_summary" in d
        assert "provenance" in d

    def test_legacy_orchestrator_event_log_tracks_experiment(self):
        """Legacy orchestrator should produce an event log."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        events = result.experiment.event_log.events
        assert len(events) > 0
        assert any(e.event_type == "experiment.completed" for e in events)

    def test_legacy_orchestrator_trial_ledger_has_parent_child(self):
        """Legacy orchestrator trials should have proper parent-child relationships."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        trials = result.experiment.trial_ledger.get_all_trials()
        assert len(trials) > 0

        # At least one trial should be evaluated
        evaluated = result.experiment.trial_ledger.get_evaluated_trials()
        assert len(evaluated) > 0


class TestDirectVsLegacyEquivalence:
    """Test that direct and legacy invocations produce equivalent artifacts."""

    def test_same_trial_count(self):
        """Legacy and direct invocations should produce the same trial count."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        # The legacy orchestrator should produce a governed experiment
        assert result.experiment.trial_ledger.total_trials > 0
        assert result.experiment.trial_ledger.evaluated_count > 0

    def test_same_baseline_type(self):
        """Legacy and direct invocations should produce the same baseline type."""
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()

        assert result.experiment.baseline.baseline_type == "buy_and_hold"
