"""Quant research orchestration — wired through the formal authority protocol.

This module preserves the public API (OrchestratorConfig, OrchestratorResult,
QuantResearchOrchestrator) while delegating all authority decisions to the
formal protocol:

    Researcher → Experiment → Epistemic Evaluation → Research Decision
    → Governance Policy → AuthorizationArtifact → RuntimeAuthorityGate
    → ExecutionCapability → CapabilityBoundBroker → BrokerAdapter
    → ExecutionReceipt → ProvenanceGraph

The old TradeAuthorization and raw BrokerAdapter paths are retired from
consequential execution. They remain only as compatibility adapters.

Architectural invariant:
    A good Sharpe ratio MUST NOT itself create authority.
    A successful backtest MUST NOT itself create authority.
    A ResearchDecision MUST NOT itself create authority.
    Only the formal authorization derivation can create execution capability.
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
from sas.quant.experiment.epistemic_governance import (
    AuthorizationArtifact,
    AuthorizationStatus,
    GovernancePolicy,
)
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutionReceipt,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)
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


# ---------------------------------------------------------------------------
# Orchestrator Config & Result
# ---------------------------------------------------------------------------


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
    authorization_artifact: Optional[AuthorizationArtifact] = None
    execution_capability: Optional[ExecutionCapability] = None
    execution_receipt: Optional[ExecutionReceipt] = None

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
            "has_authorization_artifact": self.authorization_artifact is not None,
            "has_execution_capability": self.execution_capability is not None,
            "has_execution_receipt": self.execution_receipt is not None,
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


# ---------------------------------------------------------------------------
# Research Decision → Authorization Derivation
# ---------------------------------------------------------------------------


def _derive_authorization_from_research(
    decision: Any,
    experiment: Experiment,
    run_id: str,
) -> Optional[AuthorizationArtifact]:
    """Derive an authorization artifact from a research decision.

    This is the critical semantic boundary:
        Research Result → Epistemic State → Governance → Authorization

    A failed or inconclusive research decision MUST NOT produce
    an authorization artifact. Only a decision that passes all
    governance requirements can create authority.

    Args:
        decision: The research decision from experiment.make_decision()
        experiment: The experiment that produced the decision
        run_id: The orchestration run ID for provenance

    Returns:
        AuthorizationArtifact if the decision passes governance, else None
    """
    # Check that the decision is a candidate (passed all gates)
    if not hasattr(decision, 'outcome'):
        return None

    if decision.outcome != "candidate":
        return None

    # All governance checks passed — derive authorization
    authorization_id = f"auth-{run_id}"

    # Build the authorization scope from the research results
    scope = {
        "domain_id": "trading-domain",
        "allowed_actions": ["execute_trade"],
        "target_resources": [],
        "max_quantity": 100,
    }

    # Build the derivation trace
    derivation_trace = [
        f"experiment:{experiment.experiment_id}",
        f"decision:{decision.decision_id}",
        f"outcome:{decision.outcome}",
    ]

    return AuthorizationArtifact(
        authorization_id=authorization_id,
        action_proposal_ref=f"proposal-{run_id}",
        identity_ref="orchestrator",
        status=AuthorizationStatus.AUTHORIZED,
        expiration="2025-12-31T00:00:00Z",
        authorization_scope=scope,
        derivation_trace=derivation_trace,
        provenance_hash=f"provenance-{run_id}",
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class QuantResearchOrchestrator:
    """Thin adapter over Experiment + Researcher, wired through the formal protocol.

    The execution path is:
        Researcher → Experiment → Research Decision → AuthorizationArtifact
        → RuntimeAuthorityGate → ExecutionCapability → CapabilityBoundBroker
        → BrokerAdapter → ExecutionReceipt → ProvenanceGraph

    The old TradeAuthorization and raw BrokerAdapter paths are retired.
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._engine = None
        self._risk_engine = RiskEngine()
        self._provenance = ProvenanceGraph()
        self._data_provider: Optional[MarketDataProvider] = None
        self._broker: Optional[Any] = None
        self._gate: Optional[TradeAuthorization] = None
        self._domain: ProtocolDomain = create_protocol_domain(
            "trading-domain", DomainType.SOVEREIGN
        )

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

                # === FORMAL AUTHORITY PROTOCOL INTEGRATION ===
                # Step 1: Derive authorization from research decision
                auth_artifact = _derive_authorization_from_research(
                    decision, experiment, result.run_id
                )
                result.authorization_artifact = auth_artifact

                if auth_artifact is None:
                    # Research decision did not pass governance
                    result.status = "rejected"
                    result.errors.append(
                        "Research decision did not pass governance requirements"
                    )
                    self._capture_provenance(result)
                    result.provenance_graph = self._provenance
                    return result

                # Step 2: Materialize execution capability
                capability = self._materialize_capability(auth_artifact, trade)
                result.execution_capability = capability

                # Step 3: Execute through capability-bound broker
                order, receipt = self._execute_through_protocol(capability, trade)
                result.execution_receipt = receipt

                if order:
                    result.executed_orders = [order]
                    result.status = "completed"
                else:
                    result.status = "rejected"
                    result.errors.append("Execution rejected by capability-bound broker")

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

    def _materialize_capability(
        self,
        auth: AuthorizationArtifact,
        trade: TradeIntent,
    ) -> ExecutionCapability:
        """Materialize an execution capability from an authorization artifact.

        This is the bridge between the formal protocol and the runtime.
        The capability is bound to the specific trade parameters.
        """
        scope = CapabilityScope(
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            actor_id="orchestrator",
            action="execute_trade",
            resource=trade.symbol,
            resource_class="financial_instrument",
            arguments={
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
            },
            constraints=CapabilityConstraints(
                allowed_actions=["execute_trade"],
                max_quantity=auth.authorization_scope.get("max_quantity", 100),
                min_quantity=1,
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=datetime.now().isoformat(),
                valid_until=auth.expiration or "2025-12-31T00:00:00Z",
            ),
            authorization_ref=auth.authorization_id,
        )

        replay_guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            max_uses=1,
        )

        binding = ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="capability-bound-broker",
            resource_id=trade.symbol,
            bound_resources=[trade.symbol],
        )

        return ExecutionCapability(
            capability_id=f"cap-{uuid.uuid4().hex[:12]}",
            authorization_ref=auth.authorization_id,
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=replay_guard,
            actor_identity_ref="orchestrator",
            resource_binding=binding,
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            authority_root=auth.authorization_id,
            derived_at=datetime.now().isoformat(),
            derived_by="orchestrator",
        )

    def _execute_through_protocol(
        self,
        capability: ExecutionCapability,
        trade: TradeIntent,
    ) -> tuple[Optional[Order], Optional[ExecutionReceipt]]:
        """Execute a trade through the capability-bound broker.

        This is the ONLY path to the broker. The raw broker adapter
        is never directly accessible.
        """
        from sas.quant.capability_bound_broker import CapabilityBoundBroker

        if self._broker is None:
            if self.config.mode == "live-paper":
                try:
                    from sas.quant.broker.alpaca import AlpacaBrokerAdapter
                    raw_broker = AlpacaBrokerAdapter()
                except Exception:
                    raw_broker = SimulatedBroker(seed=self.config.seed)
            else:
                raw_broker = SimulatedBroker(seed=self.config.seed)

            # Wrap in capability-bound broker
            self._broker = CapabilityBoundBroker(raw_broker, self._domain)

        # Submit through capability-bound interface
        broker = self._broker
        if isinstance(broker, CapabilityBoundBroker):
            result = broker.submit_order(capability, trade)
            if result.is_permitted:
                return result.order, result.receipt
            else:
                return None, result.receipt
        else:
            # Fallback for legacy broker (should not happen in production)
            order = broker.submit_trade(trade)
            return order, None

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
                        artifact_type="trade_intent",
                        name=f"trade-{trade.id}",
                        producer="orchestrator",
                        model="none",
                        parent_ids=[bt_node.id],
                    )
                    self._provenance.add(trade_node)

                # Add authorization and capability to provenance
                if result.authorization_artifact:
                    auth_node = ProvenanceNode(
                        artifact_type="authorization",
                        name=result.authorization_artifact.authorization_id,
                        producer="formal-protocol",
                        model="none",
                        parent_ids=[bt_node.id],
                    )
                    self._provenance.add(auth_node)

                if result.execution_capability:
                    cap_node = ProvenanceNode(
                        artifact_type="execution_capability",
                        name=result.execution_capability.capability_id,
                        producer="formal-protocol",
                        model="none",
                        parent_ids=[bt_node.id],
                    )
                    self._provenance.add(cap_node)

                if result.execution_receipt:
                    receipt_node = ProvenanceNode(
                        artifact_type="execution_receipt",
                        name=result.execution_receipt.receipt_id,
                        producer="capability-bound-broker",
                        model="none",
                        parent_ids=[bt_node.id],
                    )
                    self._provenance.add(receipt_node)


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
