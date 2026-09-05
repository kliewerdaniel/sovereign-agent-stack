"""Quant module init — exports all public interfaces."""
from sas.quant.engine import QuantEngine, EngineConfig
from sas.quant.strategy import (
    StrategyArtifact, SignalDefinition, PositionSizing,
    TransactionCosts, RiskConstraints,
)
from sas.quant.backtest import BacktestEngine, BacktestConfig, BacktestResult
from sas.quant.risk import RiskEngine, RiskPolicy, RiskEvaluation, TradeIntent
from sas.quant.broker import SimulatedBroker, BrokerConfig, Order, Fill, Account
from sas.quant.market import (
    MarketDataProvider, LocalCSVDataset, SyntheticDataProvider,
    MarketDataPoint, DatasetInfo,
)
from sas.quant.provenance import ProvenanceNode, ProvenanceGraph
from sas.quant.reports import ReportGenerator, QuantReport
from sas.quant.lifecycle import ResearchLifecycle, ResearchStage, TRANSITIONS
from sas.quant.agents import (
    QuantAgent, AgentCapabilities,
    quant_coordinator, data_researcher, signal_researcher,
    backtest_agent, risk_agent, portfolio_agent, execution_agent,
)
from sas.quant.knowledge.compiler import QuantKnowledgeCompiler
from sas.quant.cli import register  # noqa: F401

__version__ = "0.1.0a0"
__all__ = [
    "QuantEngine", "EngineConfig",
    "StrategyArtifact", "SignalDefinition", "PositionSizing",
    "TransactionCosts", "RiskConstraints",
    "BacktestEngine", "BacktestConfig", "BacktestResult",
    "RiskEngine", "RiskPolicy", "RiskEvaluation", "TradeIntent",
    "SimulatedBroker", "BrokerConfig", "Order", "Fill", "Account",
    "MarketDataProvider", "LocalCSVDataset", "SyntheticDataProvider",
    "MarketDataPoint", "DatasetInfo",
    "ProvenanceNode", "ProvenanceGraph",
    "ReportGenerator", "QuantReport",
    "ResearchLifecycle", "ResearchStage", "TRANSITIONS",
    "QuantAgent", "AgentCapabilities",
    "quant_coordinator", "data_researcher", "signal_researcher",
    "backtest_agent", "risk_agent", "portfolio_agent", "execution_agent",
    "QuantKnowledgeCompiler",
    "register",
]