"""Quant research orchestration.

Wires the full research loop:
  strategy proposal (LLM) → backtest → risk evaluation → authorization gate → broker → provenance

The orchestrator is the ONLY component that can submit trades to the broker.
The LLM proposes strategies through the toolbox; the orchestrator validates,
backtests, risk-checks, gates, and (on approval) executes them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from sas.quant.backtest import BacktestConfig, BacktestEngine, BacktestResult
from sas.quant.broker import Order, OrderStatus, SimulatedBroker
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.engine import QuantEngine
from sas.quant.market import MarketDataProvider, SyntheticDataProvider
from sas.quant.orchestration.gate import (
    AuthorizationResult,
    SessionLimits,
    TradeAuthorization,
)
from sas.quant.provenance import ProvenanceGraph, ProvenanceNode
from sas.quant.risk import RiskEngine, TradeIntent
from sas.quant.strategy import (
    PositionSizing,
    SignalDefinition,
    StrategyArtifact,
)
from sas.quant.toolbox import create_toolbox_from_world
from sas.quant.world import (
    ExecutionRun,
    QuantWorld,
    QuantWorldBuilder,
    Task,
)


@dataclass
class OrchestratorConfig:
    """Configuration for the quant research orchestrator."""
    universe: list[str] = field(default_factory=list)
    horizon: str = "1y"
    start_date: str = "2024-01-02"
    end_date: str = "2024-12-31"
    initial_capital: float = 100_000.0
    seed: int = 42
    mode: str = "backtest-only"  # "backtest-only" or "live-paper"
    auto_approve: bool = False
    max_trades_per_session: int = 10
    max_order_value_usd: float = 10_000.0
    model_provider: str = "stub"  # "stub", "ollama", "openai"
    model_name: str = "stub-model"


@dataclass
class OrchestratorResult:
    """Result of a full orchestration run."""
    run_id: str = ""
    status: str = "pending"
    world: Optional[QuantWorld] = None
    strategy: Optional[StrategyArtifact] = None
    backtest_result: Optional[BacktestResult] = None
    trade_intents: list[TradeIntent] = field(default_factory=list)
    executed_orders: list[Order] = field(default_factory=list)
    authorization_results: list[AuthorizationResult] = field(default_factory=list)
    provenance_graph: Optional[ProvenanceGraph] = None
    artifacts: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

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


class QuantResearchOrchestrator:
    """Orchestrates the full quant research loop.

    1. Assemble QuantWorld from config
    2. Run LLM research loop (proposes strategy)
    3. Backtest proposed strategy
    4. Risk evaluation
    5. Authorization gate (human-in-the-loop)
    6. Broker submission (if approved)
    7. Provenance capture
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._engine = QuantEngine()
        self._risk_engine = RiskEngine()
        self._provenance = ProvenanceGraph()
        self._data_provider: Optional[MarketDataProvider] = None
        self._broker: Optional[BrokerAdapter] = None
        self._gate: Optional[TradeAuthorization] = None

    def run(self) -> OrchestratorResult:
        """Execute the full research loop.

        Returns:
            ``OrchestratorResult`` with all artifacts and provenance.
        """
        result = OrchestratorResult(
            run_id=str(uuid.uuid4())[:12],
            status="running",
        )

        try:
            # Step 1: Assemble world
            world, task = self._build_world()
            result.world = world

            # Step 2: Set up data provider
            data_provider = self._build_data_provider(world)

            # Step 3: Run LLM research loop
            strategy = self._run_research_loop(world, task, data_provider, result)
            result.strategy = strategy

            if strategy is None:
                result.status = "failed"
                result.errors.append("No strategy proposed by LLM")
                return result

            # Step 4: Backtest
            bt_result = self._run_backtest(strategy, data_provider)
            result.backtest_result = bt_result

            # Step 5: Create trade intent from strategy
            trade = self._create_trade_intent(strategy, bt_result)
            result.trade_intents = [trade]

            # Step 6: Authorization gate
            auth_result = self._run_authorization(trade, world)
            result.authorization_results = [auth_result]

            if auth_result.approved:
                # Step 7: Submit to broker
                order = self._submit_to_broker(trade)
                result.executed_orders = [order]
                result.status = "completed"
            else:
                result.status = "rejected"

            # Step 8: Capture provenance
            self._capture_provenance(result)
            result.provenance_graph = self._provenance

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))

        return result

    def _build_world(self) -> tuple[QuantWorld, Task]:
        """Build a QuantWorld and Task from the orchestrator config."""
        builder = QuantWorldBuilder(world_id=f"qw-orch-{str(uuid.uuid4())[:8]}")
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

        builder.add_policy(
            "risk-policy",
            "1.0.0",
            "pol-hash-orchestrator",
            "Max position 25%, max leverage 1.5x, max daily loss 5%",
        )

        builder.portfolio({
            "cash": self.config.initial_capital,
            "positions": {},
            "benchmark": self.config.universe[0] if self.config.universe else "SPY",
            "mandate": "Autonomous research",
        })

        builder.add_strategy(
            "strat-orchestrator",
            "1.0.0",
            "Strategy proposed by LLM research loop",
        )

        # Add all tools
        tool_names = [
            "get_prices", "get_portfolio", "get_positions", "validate_data",
            "compute_returns", "compute_risk_metrics", "compute_portfolio_returns",
            "compute_factor_exposure", "compute_attribution", "compute_concentration",
            "detect_anomalies", "compute_beta", "compute_var_cvar",
            "compute_backtest", "evaluate_risk", "build_report", "get_provenance",
        ]
        for t in tool_names:
            builder.add_tool(t, f"Tool: {t}", None)

        # Add agent
        from sas.quant.agents import quant_coordinator
        builder.add_agent(quant_coordinator())

        builder.constraints({
            "max_drawdown_limit": 0.20,
            "max_single_name_concentration": 0.25,
            "approved_universe": list(self.config.universe),
        })

        # Set task prompt
        task_prompt = (
            f"Research the universe {', '.join(self.config.universe)} and propose "
            f"a trading strategy. Backtest it and evaluate risk."
        )
        builder.task(task_prompt)

        world = builder.build()

        # Create Task object for the model adapter
        task = Task(
            world_id=world.id,
            prompt=task_prompt,
            expected_output_type="report",
        )

        return world, task

    def _build_data_provider(self, world: QuantWorld) -> MarketDataProvider:
        """Build the market data provider."""
        if self.config.mode == "live-paper":
            try:
                from sas.quant.market.alpaca import AlpacaProvider
                provider = AlpacaProvider(
                    symbols=list(world.universe),
                    start=self.config.start_date,
                    end=self.config.end_date,
                )
                # Test if credentials are available
                test_data = provider.get_prices(
                    world.universe[0], self.config.start_date, self.config.end_date
                )
                if not test_data.empty:
                    self._data_provider = provider
                    return provider
            except Exception:
                pass
            # Fallback to synthetic
            self._data_provider = SyntheticDataProvider(seed=self.config.seed)
            return self._data_provider
        else:
            self._data_provider = SyntheticDataProvider(seed=self.config.seed)
            return self._data_provider

    def _run_research_loop(
        self,
        world: QuantWorld,
        task: Task,
        data_provider: MarketDataProvider,
        result: OrchestratorResult,
    ) -> Optional[StrategyArtifact]:
        """Run the LLM research loop to propose a strategy."""
        from sas.quant.model import create_model_adapter
        from sas.quant.agents import quant_coordinator

        # Build toolbox
        toolbox = create_toolbox_from_world(world, data_provider=data_provider, seed=self.config.seed)

        # Create model adapter
        model_config = {
            "provider": self.config.model_provider,
            "name": self.config.model_name,
        }
        if self.config.model_provider == "stub":
            # Use a default script that proposes a momentum strategy
            model_config["script"] = self._default_strategy_script(world)

        model = create_model_adapter(model_config)
        agent = quant_coordinator()

        # Create execution run
        run = ExecutionRun(
            task_id=task.id,
            world_id=world.id,
            agent_name=agent.name,
            agent_role=agent.role,
            model=self.config.model_name,
            model_provider=self.config.model_provider,
        )

        # Prepare context and run loop
        ctx = model.prepare_context(world, task, agent, self._provenance)
        loop_result = model.run_loop(ctx, toolbox, run, max_steps=50)

        # Extract strategy from artifacts
        result.artifacts = run.artifacts
        for artifact in run.artifacts.values():
            if artifact.get("artifact_type") == "strategy_proposal":
                return self._parse_strategy_artifact(artifact, world)

        # If no explicit strategy proposal, create one from the backtest tool result
        for artifact in run.artifacts.values():
            if artifact.get("artifact_type") == "backtest_result":
                return self._strategy_from_backtest(artifact, world)

        # Fallback: create a default momentum strategy
        return self._default_strategy(world)

    def _default_strategy_script(self, world: QuantWorld) -> list[dict]:
        """Create a default scripted strategy proposal for stub model."""
        return [
            {
                "tools": [
                    {
                        "name": "get_prices",
                        "arguments": {
                            "symbol": world.universe[0],
                            "start": self.config.start_date,
                            "end": self.config.end_date,
                        },
                    },
                ],
                "response": f"Fetched price data for {world.universe[0]}",
            },
            {
                "tools": [
                    {
                        "name": "compute_returns",
                        "arguments": {
                            "symbol": world.universe[0],
                            "start": self.config.start_date,
                            "end": self.config.end_date,
                        },
                    },
                ],
                "response": "Computed returns",
            },
            {
                "tools": [
                    {
                        "name": "compute_backtest",
                        "arguments": {"strategy_id": "momentum-001", "prices": "from_previous"},
                    },
                ],
                "response": "Backtest complete",
            },
            {
                "tools": [
                    {
                        "name": "build_report",
                        "arguments": {
                            "findings": [
                                {"artifact_type": "computation", "name": "momentum", "value": 0.15},
                            ],
                            "title": "Orchestrator Research Report",
                        },
                    },
                ],
                "response": "Report produced",
            },
        ]

    def _parse_strategy_artifact(self, artifact: dict, world: QuantWorld) -> StrategyArtifact:
        """Parse a strategy proposal artifact into a StrategyArtifact."""
        strategy_data = artifact.get("result", {})
        if isinstance(strategy_data, dict):
            return StrategyArtifact(
                name=strategy_data.get("name", "llm-proposed"),
                universe=list(strategy_data.get("universe", world.universe)),
                signal_definition=SignalDefinition(
                    name=strategy_data.get("signal_name", "momentum"),
                    type=strategy_data.get("signal_type", "momentum"),
                    parameters=strategy_data.get("signal_params", {}),
                ),
                position_sizing=PositionSizing(
                    method=strategy_data.get("sizing_method", "fixed_weight"),
                    target_weight=strategy_data.get("target_weight", 0.10),
                ),
                created_by="llm-research-loop",
            )
        return self._default_strategy(world)

    def _strategy_from_backtest(self, artifact: dict, world: QuantWorld) -> StrategyArtifact:
        """Create a strategy from a backtest result artifact."""
        return StrategyArtifact(
            name="backtest-derived",
            universe=list(world.universe),
            signal_definition=SignalDefinition(
                name="momentum",
                type="momentum",
                parameters={"lookback": 252, "skip": 21},
            ),
            position_sizing=PositionSizing(
                method="fixed_weight",
                target_weight=0.10,
            ),
            created_by="orchestrator",
        )

    def _default_strategy(self, world: QuantWorld) -> StrategyArtifact:
        """Create a default momentum strategy."""
        return StrategyArtifact(
            name="default-momentum",
            universe=list(world.universe),
            signal_definition=SignalDefinition(
                name="momentum",
                type="momentum",
                parameters={"lookback": 252, "skip": 21},
            ),
            position_sizing=PositionSizing(
                method="fixed_weight",
                target_weight=0.10,
            ),
            created_by="orchestrator-default",
        )

    def _run_backtest(
        self,
        strategy: StrategyArtifact,
        data_provider: MarketDataProvider,
    ) -> BacktestResult:
        """Run a backtest for the proposed strategy."""
        import pandas as pd
        import numpy as np

        # Get price data for the first universe symbol
        prices = data_provider.get_prices(
            strategy.universe[0],
            self.config.start_date,
            self.config.end_date,
        )

        if prices.empty:
            # Create minimal price data
            dates = pd.date_range(self.config.start_date, self.config.end_date, freq="B")
            n = len(dates)
            rng = np.random.default_rng(self.config.seed)
            prices = pd.DataFrame(
                {"close": 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, n)))},
                index=dates,
            )

        config = BacktestConfig(
            strategy=strategy,
            seed=self.config.seed,
            initial_capital=self.config.initial_capital,
            train_start=self.config.start_date,
            train_end=self.config.end_date,
        )
        engine = BacktestEngine(config)
        return engine.run(config, prices)

    def _create_trade_intent(
        self,
        strategy: StrategyArtifact,
        bt_result: BacktestResult,
    ) -> TradeIntent:
        """Create a trade intent from a backtested strategy."""
        # Determine position size based on backtest results
        target_weight = strategy.position_sizing.target_weight
        if bt_result.sharpe_ratio > 1.0:
            target_weight = min(target_weight * 1.5, 0.25)  # Increase for good Sharpe
        elif bt_result.sharpe_ratio < 0:
            target_weight = target_weight * 0.5  # Decrease for negative Sharpe

        quantity = (self.config.initial_capital * target_weight) / 100  # Simplified

        return TradeIntent(
            strategy_id=strategy.strategy_id,
            symbol=strategy.universe[0],
            side="buy",
            quantity=round(quantity, 2),
            target_weight=target_weight,
            price_assumption=100.0,  # Simplified
            reason=f"Strategy {strategy.name} passed backtest (Sharpe: {bt_result.sharpe_ratio:.2f})",
            requested_by="orchestrator",
        )

    def _run_authorization(
        self,
        trade: TradeIntent,
        world: QuantWorld,
    ) -> AuthorizationResult:
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

        # Get current portfolio weights (simplified)
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

    def _capture_provenance(self, result: OrchestratorResult) -> None:
        """Capture provenance for the full orchestration run."""
        # Root: dataset node
        root = ProvenanceNode(
            artifact_type="dataset",
            name=f"market-data-{self.config.start_date}-{self.config.end_date}",
            producer="orchestrator",
            model="none",
        )
        self._provenance.add(root)

        # Strategy node
        strategy_node = None
        if result.strategy:
            strategy_node = ProvenanceNode(
                artifact_type="strategy",
                name=result.strategy.name,
                producer="llm-research-loop",
                model=self.config.model_name,
                parent_ids=[root.id],
            )
            self._provenance.add(strategy_node)

        # Backtest node
        bt_node = None
        if result.backtest_result:
            bt_node = ProvenanceNode(
                artifact_type="backtest",
                name=f"backtest-{result.strategy.strategy_id}" if result.strategy else "backtest",
                producer="orchestrator",
                model="none",
                parent_ids=[strategy_node.id] if strategy_node else [root.id],
            )
            self._provenance.add(bt_node)

        # Trade node
        for trade in result.trade_intents:
            trade_node = ProvenanceNode(
                artifact_type="trade",
                name=f"{trade.side}-{trade.symbol}",
                producer="orchestrator",
                model="none",
                parent_ids=[bt_node.id] if bt_node else [root.id],
            )
            self._provenance.add(trade_node)

        # Order node
        for order in result.executed_orders:
            order_node = ProvenanceNode(
                artifact_type="order",
                name=f"order-{order.id}",
                producer=self._broker.name if self._broker else "unknown",
                model="none",
                parent_ids=[t.id for t in result.trade_intents],
            )
            self._provenance.add(order_node)
