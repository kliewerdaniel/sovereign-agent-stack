"""Integration tests for the quant research orchestrator.

Tests the full loop: world assembly → research → backtest → risk → authorization → broker → provenance.
Uses StubModelAdapter + SyntheticProvider for deterministic, offline execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.orchestration import OrchestratorConfig, QuantResearchOrchestrator
from sas.quant.provenance import ProvenanceGraph


class TestOrchestratorBasics:
    """Basic orchestrator tests."""

    def test_config_defaults(self):
        config = OrchestratorConfig()
        assert config.universe == []
        assert config.mode == "backtest-only"
        assert config.auto_approve is False
        assert config.max_trades_per_session == 10
        assert config.max_order_value_usd == 10_000.0

    def test_config_with_universe(self):
        config = OrchestratorConfig(universe=["AAPL", "MSFT"])
        assert config.universe == ["AAPL", "MSFT"]


class TestOrchestratorRunBacktestOnly:
    """Test full orchestration in backtest-only mode."""

    def test_runs_successfully(self):
        config = OrchestratorConfig(
            universe=["AAPL", "MSFT"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert result.status in ("completed", "rejected")
        assert result.run_id != ""
        assert result.world is not None

    def test_produces_strategy(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert result.strategy is not None
        assert result.strategy.name != ""

    def test_produces_backtest_result(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert result.backtest_result is not None
        assert result.backtest_result.total_return is not None

    def test_produces_trade_intent(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert len(result.trade_intents) > 0
        assert result.trade_intents[0].symbol == "AAPL"

    def test_produces_authorization_result(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert len(result.authorization_results) > 0

    def test_produces_provenance(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert result.provenance_graph is not None
        assert len(result.provenance_graph._nodes) > 0

    def test_serializes_to_dict(self):
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


class TestOrchestratorWithAutoApprove:
    """Test that auto_approve allows execution without human input."""

    def test_executes_trade_with_auto_approve(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        assert result.status == "completed"
        assert len(result.executed_orders) > 0

    def test_order_has_fill_details(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        order = result.executed_orders[0]
        assert order.symbol == "AAPL"
        assert order.status.value in ("filled", "partial", "pending")


class TestOrchestratorProvenance:
    """Test provenance capture from orchestration."""

    def test_provenance_has_dataset_node(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        nodes = result.provenance_graph.query(artifact_type="dataset")
        assert len(nodes) > 0

    def test_provenance_has_strategy_node(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        nodes = result.provenance_graph.query(artifact_type="strategy")
        assert len(nodes) > 0

    def test_provenance_has_backtest_node(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        nodes = result.provenance_graph.query(artifact_type="backtest")
        assert len(nodes) > 0

    def test_provenance_has_trade_node(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        nodes = result.provenance_graph.query(artifact_type="trade")
        assert len(nodes) > 0

    def test_provenance_has_order_node(self):
        config = OrchestratorConfig(
            universe=["AAPL"],
            mode="backtest-only",
            auto_approve=True,
            seed=42,
        )
        orchestrator = QuantResearchOrchestrator(config)
        result = orchestrator.run()
        nodes = result.provenance_graph.query(artifact_type="order")
        assert len(nodes) > 0
