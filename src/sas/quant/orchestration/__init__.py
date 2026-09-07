"""Quant research orchestration — thin adapter over Experiment + Researcher.

This module preserves the existing public API (OrchestratorConfig,
OrchestratorResult, QuantResearchOrchestrator) while delegating all
execution to the new governed research architecture.

The old orchestrator does NOT maintain a second implementation of the
research lifecycle. It translates its inputs into an ExperimentConfig,
invokes the Researcher, and translates the resulting experiment artifacts
back into the legacy result shape.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from sas.quant.backtest import BacktestResult
from sas.quant.broker import Order, OrderStatus, SimulatedBroker
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.evaluation.baseline import BaselineConfig
from sas.quant.evaluation.gates import ResearchGateConfig
from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.orchestration.gate import (
    AuthorizationResult,
    SessionLimits,
    TradeAuthorization,
)
from sas.quant.provenance import ProvenanceGraph, ProvenanceNode
from sas.quant.research.experiment import Experiment, ExperimentConfig
from sas.quant.orchestration.researcher import Researcher, ResearchResult
from sas.quant.risk import RiskEngine, TradeIntent
from sas.quant.strategy import StrategyArtifact


@dataclass
class OrchestratorConfig:
    """Configuration for the quant research orchestrator."""
    universe: list[str] = field(default_factory=list)
    horizon: str = "1y"
    start_date: str = "2024-01-02"
    end_date: str = "2024-12-31"
    initial_capital: float = 100_000.0
    seed: int = 42
    mode: str = "backtest-only"
    auto_approve: bool = False
    max_trades_per_session: int = 10
    max_order_value_usd: float = 10_000.0
    model_provider: str = "stub"
    model_name: str = "stub-model"


@dataclass
class OrchestratorResult:
    """Result of a full orchestration run."""
    run_id: str = ""
    status: str = "pending"
    world: Any = None
    strategy: Optional[StrategyArtifact] = None
    backtest_result: Optional[BacktestResult] = None
    trade_intents: list[TradeIntent] = field(default_factory=list)
    executed_orders: list[Order] = field(default_factory=list)
    authorization_results: list[AuthorizationResult] = field(default_factory=list)
    provenance_graph: Optional[ProvenanceGraph] = None
    artifacts: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    experiment: Experiment | None = None

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "world_id": self.world.id if self.world else None,
            "strategy_id": self.strategy.strategy_id if self.strategy else None,
            "backtest_summary": self._backtest_summary(),
            "trades_proposed": len(self.trade_intents),
            "trades_executed": len(self.executed_orders),
            "authorization_results": [
                {
                    "trade_id": r.trade.id,
                    "approved": r.approved,
                    "reason": r.reason,
                }
                for r in self.authorization_results
            ],
            "provenance": (
                self.provenance_graph.to_dict() if self.provenance_graph else None
            ),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def _backtest_summary(self) -> Optional[dict]:
        if not self.backtest_result:
            return None
        r = self.backtest_result
        return {
            "total_return": r.total_return,
            "sharpe_ratio": r.sharpe_ratio,
            "max_drawdown": r.max_drawdown,
            "total_trades": r.total_trades,
            "final_value": r.final_value,
        }


def _compute_research_holdout_split(start_date: str, end_date: str) -> tuple[tuple[str, str], tuple[str, str]]:
    """Split the full date range into research (80%) and holdout (20%) windows."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days
    research_days = int(total_days * 0.8)
    research_end = start + timedelta(days=research_days)
    holdout_start = research_end + timedelta(days=1)
    return (
        (start_date, research_end.strftime("%Y-%m-%d")),
        (holdout_start.strftime("%Y-%m-%d"), end_date),
    )


class QuantResearchOrchestrator:
    """Thin adapter over Experiment + Researcher.

    Preserves the existing public API while delegating all execution
    to the governed research architecture.
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._engine = None
        self._risk_engine = RiskEngine()
        self._provenance = ProvenanceGraph()
        self._data_provider: Optional[MarketDataProvider] = None
        self._broker: Optional[BrokerAdapter] = None
        self._gate: Optional[TradeAuthorization] = None

    def run(self) -> OrchestratorResult:
        """Execute the full research loop via the governed architecture."""
        result = OrchestratorResult(
            run_id=str(uuid.uuid4())[:12],
            status="running",
        )

        try:
            # Split date range into research and holdout windows
            research_window, holdout_window = _compute_research_holdout_split(
                self.config.start_date, self.config.end_date
            )

            # Build experiment config from orchestrator config
            experiment_config = ExperimentConfig(
                experiment_id=result.run_id,
                world_id=f"qw-orch-{str(uuid.uuid4())[:8]}",
                trial_budget=10,
                research_window=research_window,
                holdout_window=holdout_window,
                model_id=self.config.model_name,
                task_id="auto-research-task",
                random_seed=self.config.seed,
                initial_capital=self.config.initial_capital,
                baseline_config=BaselineConfig(
                    baseline_type="buy_and_hold",
                    universe=self.config.universe,
                    data_window=research_window,
                ),
                gate_config=ResearchGateConfig(),
            )

            # Create experiment
            experiment = Experiment(experiment_config)
            result.experiment = experiment

            # Build a QuantWorld for the legacy result.world field
            from sas.quant.world import QuantWorldBuilder
            builder = QuantWorldBuilder(world_id=experiment_config.world_id)
            builder.customer("Sas Orchestrator").objective(
                "Autonomous quantitative research: propose, backtest, and execute a trading strategy"
            )
            for sym in self.config.universe:
                builder.universe(sym)
            builder.add_dataset(
                "ds-research",
                "synthetic" if self.config.mode == "backtest-only" else "alpaca",
                "1.0.0",
                f"Market data for {', '.join(self.config.universe)}",
            )
            builder.portfolio({
                "cash": self.config.initial_capital,
                "positions": {},
                "benchmark": self.config.universe[0] if self.config.universe else "SPY",
                "mandate": "Autonomous research",
            })
            result.world = builder.build()

            # Build data provider
            data_provider = self._build_data_provider()

            # Compute baseline
            experiment.compute_baseline(data_provider)

            # Run research loop
            researcher = Researcher(experiment, data_provider=data_provider)
            research_result = researcher.run_research()

            # Compute statistics
            experiment.compute_statistics()

            # Evaluate holdout
            evaluated = experiment.trial_ledger.get_evaluated_trials()
            if evaluated:
                experiment.trial_ledger.set_incumbent(evaluated[0].trial_id)
            experiment.evaluate_holdout(data_provider)

            # Make decision (transitions to FINAL internally)
            decision = experiment.make_decision()

            # Translate back to legacy result shape
            incumbent = experiment.trial_ledger.get_incumbent()
            if incumbent:
                result.strategy = StrategyArtifact(
                    strategy_id=incumbent.trial_id,
                    name=incumbent.strategy_spec.get("name", "unknown"),
                    signal_definition=incumbent.strategy_spec.get("signal_definition", {}),
                    universe=incumbent.strategy_spec.get("universe", self.config.universe),
                    created_by="governed-research-loop",
                )
                if incumbent.backtest_result:
                    br = incumbent.backtest_result
                    result.backtest_result = BacktestResult(
                        strategy_id=incumbent.trial_id,
                        strategy_version="1.0.0",
                        engine_version="1.0.0",
                        dataset_version="1.0.0",
                        seed=incumbent.random_seed,
                        total_return=br.get("total_return", 0.0),
                        annualized_return=br.get("annualized_return", 0.0),
                        annualized_volatility=br.get("annualized_volatility", 0.0),
                        sharpe_ratio=br.get("sharpe_ratio", 0.0),
                        sortino_ratio=br.get("sortino_ratio", 0.0),
                        max_drawdown=br.get("max_drawdown", 0.0),
                        max_drawdown_duration=br.get("max_drawdown_duration", 0),
                        var_95=br.get("var_95", 0.0),
                        cvar_95=br.get("cvar_95", 0.0),
                        win_rate=br.get("win_rate", 0.0),
                        profit_factor=br.get("profit_factor", 0.0),
                        total_trades=br.get("total_trades", 0),
                        avg_trade_return=br.get("avg_trade_return", 0.0),
                        monthly_returns=br.get("monthly_returns", []),
                        equity_curve=br.get("equity_curve", []),
                        drawdown_series=br.get("drawdown_series", []),
                        transaction_costs=br.get("transaction_costs", 0.0),
                        final_value=br.get("final_value", 0.0),
                        train_period=(research_window[0], research_window[1]),
                        validation_period=(research_window[0], research_window[1]),
                        test_period=(holdout_window[0], holdout_window[1]),
                        assumptions={},
                    )

                # Create trade intent from incumbent strategy
                trade = self._create_trade_intent_from_incumbent(incumbent, result.backtest_result)
                result.trade_intents = [trade]

                # Run authorization gate
                auth_result = self._run_authorization(trade)
                result.authorization_results = [auth_result]

                if auth_result.approved:
                    # Submit to broker
                    order = self._submit_to_broker(trade)
                    result.executed_orders = [order]
                    result.status = "completed"
                else:
                    result.status = "rejected"
            else:
                result.status = "rejected"
                result.errors.append("No incumbent strategy produced")

            # Capture provenance
            self._capture_provenance(result)
            result.provenance_graph = self._provenance

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))

        return result

    def _create_trade_intent_from_incumbent(self, incumbent, bt_result: BacktestResult) -> TradeIntent:
        """Create a trade intent from the incumbent strategy."""
        assert bt_result is not None
        target_weight = incumbent.strategy_spec.get("target_weight", 0.10)
        if bt_result.sharpe_ratio > 1.0:
            target_weight = min(target_weight * 1.5, 0.25)
        elif bt_result.sharpe_ratio < 0:
            target_weight = target_weight * 0.5

        quantity = (self.config.initial_capital * target_weight) / 100

        return TradeIntent(
            strategy_id=incumbent.trial_id,
            symbol=incumbent.strategy_spec.get("universe", self.config.universe)[0],
            side="buy",
            quantity=round(quantity, 2),
            target_weight=target_weight,
            price_assumption=100.0,
            reason=f"Strategy {incumbent.strategy_spec.get('name', 'unknown')} passed research (Sharpe: {bt_result.sharpe_ratio:.2f})",
            requested_by="orchestrator",
        )

    def _run_authorization(self, trade: TradeIntent) -> AuthorizationResult:
        """Run the authorization gate."""
        if self._gate is None:
            limits = SessionLimits(
                max_trades_per_session=self.config.max_trades_per_session,
                max_order_value_usd=self.config.max_order_value_usd,
                auto_approve=self.config.auto_approve,
            )
            self._gate = TradeAuthorization(
                risk_engine=self._risk_engine,
                session_limits=limits,
            )

        portfolio_weights = {trade.symbol: trade.target_weight}
        return self._gate.authorize(trade, portfolio_weights)

    def _submit_to_broker(self, trade: TradeIntent) -> Order:
        """Submit an authorized trade to the broker."""
        if self._broker is None:
            if self.config.mode == "live-paper":
                try:
                    from sas.quant.broker.alpaca import AlpacaBrokerAdapter
                    self._broker = AlpacaBrokerAdapter()
                except Exception:
                    self._broker = SimulatedBroker(seed=self.config.seed)
            else:
                self._broker = SimulatedBroker(seed=self.config.seed)

        order = self._broker.submit_trade(trade)
        if self._gate:
            self._gate.record_trade()
        return order

    def _build_data_provider(self) -> MarketDataProvider:
        """Build the market data provider."""
        if self.config.mode == "live-paper":
            try:
                from sas.quant.market.alpaca import AlpacaProvider
                provider = AlpacaProvider(
                    symbols=list(self.config.universe),
                    start=self.config.start_date,
                    end=self.config.end_date,
                )
                test_data = provider.get_prices(
                    self.config.universe[0], self.config.start_date, self.config.end_date
                )
                if not test_data.empty:
                    self._data_provider = provider
                    return provider
            except Exception:
                pass
            self._data_provider = SyntheticDataProvider(seed=self.config.seed)
            return self._data_provider
        else:
            self._data_provider = SyntheticDataProvider(seed=self.config.seed)
            return self._data_provider

    def _capture_provenance(self, result: OrchestratorResult) -> None:
        """Capture provenance for the full orchestration run."""
        root = ProvenanceNode(
            artifact_type="dataset",
            name=f"market-data-{self.config.start_date}-{self.config.end_date}",
            producer="orchestrator",
            model="none",
        )
        self._provenance.add(root)

        if result.strategy:
            strategy_node = ProvenanceNode(
                artifact_type="strategy",
                name=result.strategy.name,
                producer="governed-research-loop",
                model=self.config.model_name,
                parent_ids=[root.id],
            )
            self._provenance.add(strategy_node)

            if result.backtest_result:
                bt_node = ProvenanceNode(
                    artifact_type="backtest",
                    name=f"backtest-{result.strategy.strategy_id}",
                    producer="orchestrator",
                    model="none",
                    parent_ids=[strategy_node.id],
                )
                self._provenance.add(bt_node)

                for trade in result.trade_intents:
                    trade_node = ProvenanceNode(
                        artifact_type="trade",
                        name=f"{trade.side}-{trade.symbol}",
                        producer="orchestrator",
                        model="none",
                        parent_ids=[bt_node.id],
                    )
                    self._provenance.add(trade_node)

                for order in result.executed_orders:
                    order_node = ProvenanceNode(
                        artifact_type="order",
                        name=f"order-{order.id}",
                        producer=self._broker.name if self._broker else "unknown",
                        model="none",
                        parent_ids=[t.id for t in result.trade_intents],
                    )
                    self._provenance.add(order_node)
