"""Quant report generator."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sas.quant.agents import (
    AgentCapabilities,
    QuantAgent,
    backtest_agent,
    data_researcher,
    execution_agent,
    portfolio_agent,
    quant_coordinator,
    risk_agent,
    signal_researcher,
)
from sas.quant.backtest import BacktestConfig, BacktestEngine, BacktestResult
from sas.quant.broker import Account, BrokerConfig, Fill, Order, SimulatedBroker
from sas.quant.cli import register
from sas.quant.engine import EngineConfig, QuantEngine
from sas.quant.evaluation import (
    BenchmarkResult,
    BenchmarkRunner,
    RunEvaluator,
    aggregate_benchmark,
    artifact_has_field,
    computation_has_hash,
    compute_pass_k,
    evaluate_sovereignty,
    has_artifact_type,
    report_contains_findings,
    report_has_provenance,
    result_in_range,
)
from sas.quant.knowledge.compiler import QuantKnowledgeCompiler
from sas.quant.lifecycle import TRANSITIONS, ResearchLifecycle, ResearchStage
from sas.quant.market import (
    DatasetInfo,
    LocalCSVDataset,
    MarketDataPoint,
    MarketDataProvider,
    SyntheticDataProvider,
)
from sas.quant.model import (
    ModelAdapter,
    ModelResponse,
    OllamaModelAdapter,
    OpenAIModelAdapter,
    StubModelAdapter,
    ToolCallRequest,
    ToolCallResult,
    ToolFormatter,
    create_model_adapter,
)
from sas.quant.provenance import ProvenanceGraph, ProvenanceNode
from sas.quant.reports import QuantReport, ReportGenerator
from sas.quant.risk import RiskEngine, RiskEvaluation, RiskPolicy, TradeIntent
from sas.quant.strategy import (
    PositionSizing,
    RiskConstraints,
    SignalDefinition,
    StrategyArtifact,
    TransactionCosts,
)
from sas.quant.toolbox import QuantToolbox, ToolDefinition, create_toolbox_from_world
from sas.quant.world import (
    CapabilityComposition,
    Criterion,
    CriterionResult,
    Evidence,
    ExecutionRun,
    ModelAdapter,
    QuantWorld,
    QuantWorldBuilder,
    Rubric,
    RunEvaluation,
    Task,
    TrajectoryStep,
)
from sas.quant.worlds.adversarial import ADVERSTIONAL_WORLDS
from sas.quant.worlds.portfolio_intelligence import (
    PORTFOLIO_INTELLIGENCE_GOLD,
    PORTFOLIO_INTELLIGENCE_RUBRIC,
    PORTFOLIO_INTELLIGENCE_TASK,
    PORTFOLIO_INTELLIGENCE_WORLD,
)

__version__ = "0.1.0a0"
__all__ = [
    "ADVERSTIONAL_WORLDS",
    "PORTFOLIO_INTELLIGENCE_GOLD",
    "PORTFOLIO_INTELLIGENCE_RUBRIC",
    "PORTFOLIO_INTELLIGENCE_TASK",
    "PORTFOLIO_INTELLIGENCE_WORLD",
    "TRANSITIONS",
    "Account",
    "AgentCapabilities",
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BrokerConfig",
    "CapabilityComposition",
    "Criterion",
    "CriterionResult",
    "DatasetInfo",
    "EngineConfig",
    "Evidence",
    "ExecutionRun",
    "Fill",
    "LocalCSVDataset",
    "MarketDataPoint",
    "MarketDataProvider",
    "ModelAdapter",
    "ModelResponse",
    "OllamaModelAdapter",
    "OpenAIModelAdapter",
    "Order",
    "PositionSizing",
    "ProvenanceGraph",
    "ProvenanceNode",
    "QuantAgent",
    "QuantEngine",
    "QuantKnowledgeCompiler",
    "QuantReport",
    "QuantToolbox",
    "QuantWorld",
    "QuantWorldBuilder",
    "ReportGenerator",
    "ResearchLifecycle",
    "ResearchStage",
    "RiskConstraints",
    "RiskEngine",
    "RiskEvaluation",
    "RiskPolicy",
    "Rubric",
    "RunEvaluation",
    "RunEvaluator",
    "SignalDefinition",
    "SimulatedBroker",
    "StrategyArtifact",
    "StubModelAdapter",
    "SyntheticDataProvider",
    "Task",
    "ToolCallRequest",
    "ToolCallResult",
    "ToolDefinition",
    "ToolFormatter",
    "TradeIntent",
    "TrajectoryStep",
    "TransactionCosts",
    "aggregate_benchmark",
    "artifact_has_field",
    "backtest_agent",
    "computation_has_hash",
    "compute_pass_k",
    "create_model_adapter",
    "create_toolbox_from_world",
    "data_researcher",
    "evaluate_sovereignty",
    "execution_agent",
    "has_artifact_type",
    "portfolio_agent",
    "quant_coordinator",
    "register",
    "report_contains_findings",
    "report_has_provenance",
    "result_in_range",
    "risk_agent",
    "signal_researcher",
]
