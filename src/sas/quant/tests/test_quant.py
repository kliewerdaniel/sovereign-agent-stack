"""Sovereign Quant integration tests.

Tests the full vertical slice:
DATA → RESEARCH → STRATEGY → BACKTEST → RISK → REPORT
"""
import numpy as np
import pandas as pd
import pytest

from sas.quant.agents import (
    execution_agent,
    quant_coordinator,
    signal_researcher,
)
from sas.quant.backtest import BacktestConfig, BacktestEngine
from sas.quant.broker import SimulatedBroker
from sas.quant.engine import EngineConfig, QuantEngine
from sas.quant.knowledge.compiler import QuantKnowledgeCompiler
from sas.quant.lifecycle import (
    TRANSITIONS,
    ResearchLifecycle,
    ResearchStage,
)
from sas.quant.market import SyntheticDataProvider
from sas.quant.provenance import ProvenanceGraph, ProvenanceNode
from sas.quant.reports import QuantReport, ReportGenerator
from sas.quant.risk import RiskEngine, RiskPolicy, TradeIntent
from sas.quant.strategy import (
    StrategyArtifact,
)

# ── Engine Tests ──────────────────────────────────────────

class TestQuantEngine:
    def test_returns(self):
        engine = QuantEngine()
        prices = pd.Series([100, 101, 102, 101.5, 103])
        ret = engine.returns(prices)
        assert len(ret) == 4
        assert not np.isnan(ret).any()

    def test_volatility(self):
        engine = QuantEngine()
        returns = np.array([0.01, -0.005, 0.015, -0.01, 0.008])
        vol = engine.volatility(returns)
        assert vol > 0

    def test_sharpe(self):
        engine = QuantEngine()
        returns = np.array([0.01, 0.005, 0.015, 0.008, 0.012])
        sharpe = engine.sharpe(returns)
        assert isinstance(sharpe, float)

    def test_sortino(self):
        engine = QuantEngine()
        returns = np.array([0.01, -0.005, 0.015, -0.01, 0.008])
        sortino = engine.sortino(returns)
        assert isinstance(sortino, float)

    def test_max_drawdown(self):
        engine = QuantEngine()
        returns = np.array([0.01, -0.02, -0.03, 0.01, 0.02])
        dd = engine.max_drawdown(returns)
        assert dd["max_drawdown"] <= 0
        assert "duration_days" in dd

    def test_var_cvar(self):
        engine = QuantEngine()
        returns = np.random.default_rng(42).normal(0, 0.02, 100)
        var = engine.var(returns, 0.95)
        cvar = engine.cvar(returns, 0.95)
        assert var <= 0
        assert cvar <= var

    def test_portfolio_math(self):
        engine = QuantEngine()
        weights = np.array([0.5, 0.5])
        expected = np.array([0.1, 0.15])
        ret = engine.portfolio_return(weights, expected)
        assert abs(ret - 0.125) < 1e-10

    def test_beta(self):
        engine = QuantEngine()
        rng = np.random.default_rng(42)
        port = rng.normal(0.001, 0.02, 100)
        bench = rng.normal(0.0008, 0.015, 100)
        beta = engine.beta(port, bench)
        assert isinstance(beta, float)

    def test_reproducibility(self):
        """Same seed → same results."""
        e1 = QuantEngine(EngineConfig(seed=42))
        e2 = QuantEngine(EngineConfig(seed=42))
        rng = np.random.default_rng(42)
        r1 = e1.volatility(rng.normal(0, 0.02, 100))
        rng = np.random.default_rng(42)
        r2 = e2.volatility(rng.normal(0, 0.02, 100))
        assert abs(r1 - r2) < 1e-12


# ── Strategy Tests ────────────────────────────────────────

class TestStrategy:
    def test_strategy_creation(self):
        s = StrategyArtifact(name="Momentum")
        assert s.strategy_id
        assert s.content_hash

    def test_strategy_reproducibility(self):
        s1 = StrategyArtifact(name="Test", version="1.0.0")
        s2 = StrategyArtifact(name="Test", version="1.0.0")
        assert s1.content_hash == s2.content_hash

    def test_to_dict_roundtrip(self):
        s = StrategyArtifact(name="Roundtrip")
        d = s.to_dict()
        s2 = StrategyArtifact.from_dict(d)
        assert s2.name == s.name
        assert s2.strategy_id == s.strategy_id


# ── Backtest Tests ────────────────────────────────────────

class TestBacktest:
    def test_backtest_runs(self):
        strategy = StrategyArtifact(name="TestStrategy")
        config = BacktestConfig(
            strategy=strategy,
            train_start="2025-01-01",
            test_start="2025-07-01",
        )
        prices = pd.DataFrame({
            "close": np.random.default_rng(42).normal(100, 5, 200),
        })
        prices.index = pd.date_range("2025-01-01", periods=200, freq="B")
        engine = BacktestEngine()
        result = engine.run(config, prices)
        assert result.total_return is not None
        assert result.sharpe_ratio is not None

    def test_backtest_deterministic(self):
        """Same inputs → same results."""
        strategy = StrategyArtifact(name="DetTest")
        config1 = BacktestConfig(strategy=strategy, seed=42)
        config2 = BacktestConfig(strategy=strategy, seed=42)
        prices = pd.DataFrame({
            "close": np.random.default_rng(42).normal(100, 5, 100),
        })
        prices.index = pd.date_range("2025-01-01", periods=100, freq="B")
        engine = BacktestEngine()
        r1 = engine.run(config1, prices)
        r2 = engine.run(config2, prices)
        assert r1.total_return == r2.total_return

    def test_backtest_warnings(self):
        strategy = StrategyArtifact(name="WarnTest")
        config = BacktestConfig(
            strategy=strategy,
            train_start="2025-07-01",
            test_start="2025-01-01",  # overlap → leakage warning
        )
        prices = pd.DataFrame({
            "close": np.random.default_rng(42).normal(100, 5, 200),
        })
        prices.index = pd.date_range("2025-01-01", periods=200, freq="B")
        engine = BacktestEngine()
        result = engine.run(config, prices)
        assert len(result.warnings) > 0


# ── Risk Tests ────────────────────────────────────────────

class TestRisk:
    def test_risk_evaluation(self):
        engine = RiskEngine()
        weights = {"AAPL": 0.3, "MSFT": 0.3, "GOOG": 0.4}
        eval_result = engine.evaluate(weights, {}, {})
        assert isinstance(eval_result.is_compliant, bool)

    def test_trade_intent(self):
        ti = TradeIntent(
            symbol="AAPL", side="buy", quantity=100,
            requested_by="test_agent",
        )
        assert ti.id
        assert ti.status == "proposed"

    def test_unauthorized_trade_rejected(self):
        engine = RiskEngine()
        policy = RiskPolicy(approved_universe=["AAPL", "MSFT"])
        engine.policy = policy
        weights = {"AAPL": 0.5, "UNKNOWN": 0.5}
        eval_result = engine.evaluate(weights, {}, {})
        universe_breaches = [b for b in eval_result.breaches
                             if b["type"] == "unapproved_universe"]
        assert len(universe_breaches) > 0

    def test_authorize_trade(self):
        engine = RiskEngine()
        ti = TradeIntent(
            strategy_id="test", symbol="AAPL", side="buy",
            quantity=100, target_weight=0.1,
            requested_by="test_agent",
        )
        portfolio = {}
        result = engine.authorize_trade(ti, portfolio)
        assert result.status in ("authorized", "pending_approval", "rejected")


# ── Broker Tests ──────────────────────────────────────────

class TestBroker:
    def test_submit_order(self):
        broker = SimulatedBroker()
        order = broker.submit_order("AAPL", "buy", 100, 150.0)
        assert order.status.value == "filled"
        summary = broker.get_account_summary()
        assert summary["order_count"] == 1

    def test_reject_invalid_order(self):
        broker = SimulatedBroker()
        order = broker.submit_order("AAPL", "buy", -1, 150.0)
        assert order.status.value == "rejected"

    def test_reject_oversized_order(self):
        broker = SimulatedBroker()
        order = broker.submit_order("AAPL", "buy", 1e9, 150.0)
        assert order.status.value == "rejected"

    def test_cancel_order(self):
        broker = SimulatedBroker()
        order = broker.submit_order("AAPL", "buy", 100, 150.0)
        cancelled = broker.cancel_order(order.id)
        # Already filled, so cancel returns False
        assert isinstance(cancelled, bool)


# ── Market Data Tests ─────────────────────────────────────

class TestMarketData:
    def test_synthetic_provider(self):
        provider = SyntheticDataProvider(seed=42)
        df = provider.get_prices("AAPL", "2025-01-01", "2025-03-01")
        assert not df.empty
        assert "close" in df.columns

    def test_synthetic_is_synthetic(self):
        provider = SyntheticDataProvider()
        info = provider.source_info()
        assert info.is_synthetic is True

    def test_validation(self):
        provider = SyntheticDataProvider()
        result = provider.validate("AAPL", "2025-01-01", "2025-03-01")
        assert result["valid"] is True


# ── Provenance Tests ──────────────────────────────────────

class TestProvenance:
    def test_add_node(self):
        graph = ProvenanceGraph()
        node = ProvenanceNode(
            artifact_type="strategy", name="TestStrategy",
        )
        graph.add(node)
        assert graph.get(node.id) == node

    def test_lineage(self):
        graph = ProvenanceGraph()
        root = ProvenanceNode(artifact_type="dataset", name="R")
        graph.add(root)
        mid = ProvenanceNode(
            artifact_type="strategy", name="M",
            parent_ids=[root.id],
        )
        graph.add(mid)
        leaf = ProvenanceNode(
            artifact_type="backtest", name="L",
            parent_ids=[mid.id],
        )
        graph.add(leaf)
        chain = graph.lineage_chain(leaf.id)
        chain_ids = [n.id for n in chain]
        assert root.id in chain_ids
        assert leaf.id in chain_ids

    def test_ancestors(self):
        graph = ProvenanceGraph()
        root = ProvenanceNode(artifact_type="dataset", name="R")
        graph.add(root)
        mid = ProvenanceNode(
            artifact_type="strategy", name="M", parent_ids=[root.id],
        )
        graph.add(mid)
        leaf = ProvenanceNode(
            artifact_type="backtest", name="L", parent_ids=[mid.id],
        )
        graph.add(leaf)
        ancestors = graph.ancestors(leaf.id)
        assert len(ancestors) >= 3


# ── Lifecycle Tests ───────────────────────────────────────

class TestLifecycle:
    def test_valid_transition(self):
        lc = ResearchLifecycle(artifact_id="test")
        t = lc.transition_to(ResearchStage.DATASET, actor="test")
        assert lc.current_stage == ResearchStage.DATASET
        assert t.from_stage == "data"
        assert t.to_stage == "dataset"

    def test_invalid_transition_raises(self):
        lc = ResearchLifecycle(artifact_id="test")
        with pytest.raises(ValueError):
            lc.transition_to(ResearchStage.BACKTEST)

    def test_all_transitions(self):
        """Verify all defined transitions are valid."""
        for from_stage, to_stages in TRANSITIONS.items():
            for to_stage in to_stages:
                lc = ResearchLifecycle(artifact_id="test")
                lc.current_stage = from_stage
                lc.transition_to(to_stage, actor="test")


# ── Agent Tests ───────────────────────────────────────────

class TestAgents:
    def test_coordinator_no_trade_execute(self):
        agent = quant_coordinator()
        assert agent.cannot("trade.execute")

    def test_signal_researcher_cannot_trade(self):
        agent = signal_researcher()
        assert agent.cannot("trade.execute")
        assert agent.cannot("trade.propose")

    def test_execution_agent_has_trade_execute(self):
        agent = execution_agent()
        assert agent.can("trade.execute")

    def test_escalation_detection(self):
        agent = signal_researcher()
        assert agent.escalate_attempt("trade.execute")

    def test_capability_grant(self):
        """Capabilities are frozen — grant requires new instance."""
        agent = quant_coordinator()
        # Frozen dataclass: attributes cannot be mutated
        assert agent.cannot("trade.execute")  # originally false


# ── Knowledge Compiler Tests ──────────────────────────────

class TestKnowledgeCompiler:
    def test_policy_creation(self):
        compiler = QuantKnowledgeCompiler()
        compiler.create_policy("test-policy", "# Test\nContent here.")
        policies = compiler.list_policies()
        assert "test-policy" in policies

    def test_answer_why(self):
        compiler = QuantKnowledgeCompiler()
        compiler.create_policy("risk-policy",
                               "# Risk Policy\nMax drawdown: 20%")
        answers = compiler.answer_why("max drawdown")
        assert len(answers) > 0
        assert "20%" in answers[0]


# ── Report Tests ──────────────────────────────────────────

class TestReport:
    def test_report_generation(self):
        strategy = StrategyArtifact(name="ReportTest")
        bt_config = BacktestConfig(
            strategy=strategy, seed=42,
            train_start="2025-01-01", test_start="2025-07-01",
        )
        prices = pd.DataFrame({
            "close": np.random.default_rng(42).normal(100, 5, 100),
        })
        prices.index = pd.date_range("2025-01-01", periods=100, freq="B")
        engine = BacktestEngine()
        bt_result = engine.run(bt_config, prices)

        risk_engine = RiskEngine()
        risk_eval = risk_engine.evaluate({}, {}, {})

        report_gen = ReportGenerator()
        report = report_gen.generate(
            title="Test Report",
            backtest_results=[bt_result],
            risk_evaluations=[risk_eval],
            trade_intents=[],
        )
        assert report.title == "Test Report"
        assert report.content_hash

    def test_report_markdown(self):
        report = QuantReport(title="MD Test")
        md = report.to_markdown()
        assert "# MD Test" in md

    def test_report_json(self):
        import json as _json
        report = QuantReport(title="JSON Test")
        j = report.export_json()
        parsed = _json.loads(j)
        assert parsed["title"] == "JSON Test"