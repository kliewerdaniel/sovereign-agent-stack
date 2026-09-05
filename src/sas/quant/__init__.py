"""Quant report generator."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sas.quant.backtest import BacktestEngine, BacktestConfig, BacktestResult
from sas.quant.risk import RiskEngine, RiskPolicy, RiskEvaluation, TradeIntent
from sas.quant.broker import SimulatedBroker, BrokerConfig, Order, Fill, Account
from sas.quant.market import (
    MarketDataProvider, LocalCSVDataset, SyntheticDataProvider,
    MarketDataPoint, DatasetInfo,
)
from sas.quant.engine import QuantEngine, EngineConfig
from sas.quant.strategy import (
    StrategyArtifact, SignalDefinition, PositionSizing,
    TransactionCosts, RiskConstraints,
)
from sas.quant.reports import ReportGenerator, QuantReport
from sas.quant.provenance import ProvenanceNode, ProvenanceGraph
from sas.quant.world import (
    QuantWorld, Task, Rubric, Criterion, CriterionResult,
    Evidence, ExecutionRun, TrajectoryStep, RunEvaluation,
    QuantWorldBuilder, ModelAdapter, CapabilityComposition,
)
from sas.quant.evaluation import (
    RunEvaluator, BenchmarkResult, BenchmarkRunner,
    compute_pass_k, aggregate_benchmark,
    has_artifact_type, artifact_has_field, report_contains_findings,
    report_has_provenance, computation_has_hash, result_in_range,
    evaluate_sovereignty,
)
from sas.quant.worlds.portfolio_intelligence import (
    PORTFOLIO_INTELLIGENCE_WORLD,
    PORTFOLIO_INTELLIGENCE_TASK,
    PORTFOLIO_INTELLIGENCE_RUBRIC,
    PORTFOLIO_INTELLIGENCE_GOLD,
)
from sas.quant.worlds.adversarial import ADVERSTIONAL_WORLDS
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
    "QuantWorld", "Task", "Rubric", "Criterion", "CriterionResult",
    "Evidence", "ExecutionRun", "TrajectoryStep", "RunEvaluation",
    "QuantWorldBuilder", "ModelAdapter", "CapabilityComposition",
    "RunEvaluator", "BenchmarkResult", "BenchmarkRunner",
    "compute_pass_k", "aggregate_benchmark",
    "has_artifact_type", "artifact_has_field", "report_contains_findings",
    "report_has_provenance", "computation_has_hash", "result_in_range",
    "evaluate_sovereignty",
    "PORTFOLIO_INTELLIGENCE_WORLD",
    "PORTFOLIO_INTELLIGENCE_TASK",
    "PORTFOLIO_INTELLIGENCE_RUBRIC",
    "PORTFOLIO_INTELLIGENCE_GOLD",
    "ADVERSTIONAL_WORLDS",
    "register",
]
