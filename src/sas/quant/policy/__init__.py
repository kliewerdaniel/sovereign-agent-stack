"""Quant MCP tools — read-only and controlled write tools.

Exposes useful tools for integration with agent harnesses.
Mutation tools require explicit capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: dict
    requires_capability: str | None = None
    read_only: bool = True


# Read-only tools
READ_ONLY_TOOLS = [
    MCPTool(
        name="get_portfolio",
        description="Get current portfolio holdings and exposure.",
        input_schema={
            "type": "object",
            "properties": {
                "include_risk": {"type": "boolean", "default": False},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_positions",
        description="Get current positions.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_strategy",
        description="Get strategy by ID.",
        input_schema={
            "type": "object",
            "properties": {
                "strategy_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_strategy_provenance",
        description="Get strategy provenance chain.",
        input_schema={
            "type": "object",
            "properties": {
                "strategy_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_backtest",
        description="Get backtest results.",
        input_schema={
            "type": "object",
            "properties": {
                "strategy_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_risk_report",
        description="Get risk report.",
        input_schema={
            "type": "object",
            "properties": {
                "strategy_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_trade_intent",
        description="Get trade intent by ID.",
        input_schema={
            "type": "object",
            "properties": {
                "trade_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_pending_approvals",
        description="Get pending trade approvals.",
        input_schema={
            "type": "object",
            "properties": {},
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_agent_capabilities",
        description="Get agent capabilities.",
        input_schema={
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_policy_decision",
        description="Get policy decision for a trade.",
        input_schema={
            "type": "object",
            "properties": {
                "trade_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_provenance",
        description="Get provenance for an artifact.",
        input_schema={
            "type": "object",
            "properties": {
                "artifact_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
    MCPTool(
        name="get_research_report",
        description="Get a research report.",
        input_schema={
            "type": "object",
            "properties": {
                "report_id": {"type": "string"},
            },
        },
        requires_capability=None,
        read_only=True,
    ),
]

# Mutation tools (require capabilities)
MUTATION_TOOLS = [
    MCPTool(
        name="propose_trade",
        description="Propose a trade (requires trade_propose).",
        input_schema={
            "type": "object",
            "properties": {
                "strategy_id": {"type": "string"},
                "symbol": {"type": "string"},
                "side": {"type": "string"},
                "quantity": {"type": "number"},
            },
        },
        requires_capability="trade.propose",
        read_only=False,
    ),
    MCPTool(
        name="execute_trade",
        description="Execute a trade (requires trade.execute).",
        input_schema={
            "type": "object",
            "properties": {
                "trade_id": {"type": "string"},
            },
        },
        requires_capability="trade.execute",
        read_only=False,
    ),
    MCPTool(
        name="approve_trade",
        description="Approve a trade (requires policy.modify).",
        input_schema={
            "type": "object",
            "properties": {
                "trade_id": {"type": "string"},
            },
        },
        requires_capability="policy.modify",
        read_only=False,
    ),
]


def get_all_tools() -> list[MCPTool]:
    """Get all registered MCP tools."""
    return READ_ONLY_TOOLS + MUTATION_TOOLS


def get_tool(name: str) -> MCPTool | None:
    """Get a tool by name."""
    for tool in get_all_tools():
        if tool.name == name:
            return tool
    return None