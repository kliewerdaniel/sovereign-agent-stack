"""Agent definitions for Sovereign Quant.

Each agent has defined capabilities and authority boundaries.
No agent has trading authority unless explicitly granted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AgentCapabilities:
    """Capabilities granted to an agent."""
    market_data_read: bool = False
    dataset_write: bool = False
    research_create: bool = False
    strategy_propose: bool = False
    backtest_execute: bool = False
    risk_evaluate: bool = False
    portfolio_propose: bool = False
    trade_propose: bool = False
    trade_execute: bool = False
    policy_read: bool = False
    policy_modify: bool = False
    provenance_read: bool = False
    provenance_write: bool = False

    def grant(self, capability: str) -> None:
        if hasattr(self, capability):
            object.__setattr__(self, capability, True)

    def has(self, capability: str) -> bool:
        return getattr(self, capability, False)


@dataclass
class QuantAgent:
    """A quant research agent with bounded authority."""
    name: str
    role: str
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    authority_level: str = "none"  # none, propose, review, execute
    model: str = "ollama"
    status: str = "idle"
    current_task: str = ""
    _can_approve_self: bool = False  # agents cannot approve their own actions

    def can(self, capability: str) -> bool:
        """Check if agent has a capability."""
        # Convert dot-notation to underscore (trade.execute → trade_execute)
        attr = capability.replace(".", "_")
        return getattr(self.capabilities, attr, False)

    def cannot(self, capability: str) -> bool:
        """Check if agent lacks a capability."""
        return not self.can(capability)

    def escalate_attempt(self, capability: str) -> bool:
        """Check if an agent is attempting to escalate beyond authority."""
        return not self.can(capability)


# Agent factory functions
def quant_coordinator() -> QuantAgent:
    """Quant Coordinator — research planning, task allocation."""
    caps = AgentCapabilities(
        market_data_read=True,
        dataset_write=True,
        research_create=True,
        strategy_propose=True,
        backtest_execute=True,
        risk_evaluate=True,
        portfolio_propose=True,
        trade_propose=True,
        # NO trade_execute
    )
    return QuantAgent(
        name="quant_coordinator",
        role="quant_coordinator",
        capabilities=caps,
        authority_level="propose",
    )


def data_researcher() -> QuantAgent:
    """Data Researcher — dataset discovery, validation."""
    caps = AgentCapabilities(
        market_data_read=True,
        dataset_write=True,
        research_create=True,
        # No trading capabilities
    )
    return QuantAgent(
        name="data_researcher",
        role="data_researcher",
        capabilities=caps,
        authority_level="research",
    )


def signal_researcher() -> QuantAgent:
    """Signal Researcher — hypothesis generation, signal discovery."""
    caps = AgentCapabilities(
        market_data_read=True,
        research_create=True,
        strategy_propose=True,
        # NO trade capabilities
    )
    return QuantAgent(
        name="signal_researcher",
        role="signal_researcher",
        capabilities=caps,
        authority_level="propose",
    )


def backtest_agent() -> QuantAgent:
    """Backtest Agent — configuring and running backtests."""
    caps = AgentCapabilities(
        market_data_read=True,
        dataset_write=True,
        backtest_execute=True,
        provenance_read=True,
        provenance_write=True,
        # Cannot modify quantitative engine
    )
    return QuantAgent(
        name="backtest_agent",
        role="backtest_agent",
        capabilities=caps,
        authority_level="execute",
    )


def risk_agent() -> QuantAgent:
    """Risk Agent — independent risk evaluation."""
    caps = AgentCapabilities(
        risk_evaluate=True,
        policy_read=True,
        provenance_read=True,
        portfolio_propose=True,
    )
    agent = QuantAgent(
        name="risk_agent",
        role="risk_agent",
        capabilities=caps,
        authority_level="review",
    )
    agent._can_approve_self = False
    return agent


def portfolio_agent() -> QuantAgent:
    """Portfolio Agent — portfolio construction, allocation."""
    caps = AgentCapabilities(
        portfolio_propose=True,
        risk_evaluate=True,
        policy_read=True,
        # No execution authority
    )
    return QuantAgent(
        name="portfolio_agent",
        role="portfolio_agent",
        capabilities=caps,
        authority_level="propose",
    )


def execution_agent() -> QuantAgent:
    """Execution Agent — highest privilege, simulated only."""
    caps = AgentCapabilities(
        trade_propose=True,
        trade_execute=True,
        risk_evaluate=True,
        policy_read=True,
        provenance_read=True,
        provenance_write=True,
        # CANNOT modify policy, strategy, provenance, capabilities
    )
    return QuantAgent(
        name="execution_agent",
        role="execution_agent",
        capabilities=caps,
        authority_level="execute",
    )