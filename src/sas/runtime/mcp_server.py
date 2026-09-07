"""MCP Server with tool execution.

Exposes SAS tools via MCP protocol with policy enforcement,
capability checking, and state machine tracking.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sas.core.config import SASConfig, parse_sas_yaml
from sas.core.scoring import generate_report
from sas.quant import (
    RiskEngine,
    RiskPolicy,
)
from sas.rust_bridge import (
    AgentStateMachine,
    CapabilityRegistry,
    ExecutionContext,
    PolicyEnforcer,
    SovereigntyAsserter,
)

logger = logging.getLogger(__name__)


@dataclass
class MCPToolResult:
    """Result of an MCP tool execution."""
    success: bool
    data: Any = None
    error: str | None = None


class MCPServer:
    """MCP Server with sovereign agent tool execution.
    
    Exposes tools via the Model Context Protocol with:
    - Capability-bound access control
    - Policy enforcement hooks
    - State machine tracking
    - Sovereignty verification
    
    Usage:
        server = MCPServer.from_config("sas.yaml")
        server.serve()  # Start serving MCP requests
    """
    
    def __init__(
        self,
        config: SASConfig,
        execution_context: ExecutionContext,
        capability_registry: CapabilityRegistry,
        policy_enforcer: PolicyEnforcer,
        state_machine: AgentStateMachine,
        sovereignty_asserter: SovereigntyAsserter,
    ):
        self.config = config
        self.execution_context = execution_context
        self.capability_registry = capability_registry
        self.policy_enforcer = policy_enforcer
        self.state_machine = state_machine
        self.sovereignty_asserter = sovereignty_asserter
        self._tools: dict[str, dict] = {}
        self._register_default_tools()
    
    @classmethod
    def from_config(cls, config_path: str | Path) -> MCPServer:
        """Create MCP server from config."""
        config = parse_sas_yaml(Path(config_path))
        execution_context = ExecutionContext()
        capability_registry = CapabilityRegistry()
        policy_enforcer = PolicyEnforcer("allow")
        state_machine = AgentStateMachine()
        sovereignty_asserter = SovereigntyAsserter()
        
        return cls(
            config=config,
            execution_context=execution_context,
            capability_registry=capability_registry,
            policy_enforcer=policy_enforcer,
            state_machine=state_machine,
            sovereignty_asserter=sovereignty_asserter,
        )
    
    @classmethod
    def from_defaults(cls) -> MCPServer:
        """Create MCP server with defaults."""
        from sas.core.config import SASConfig
        config = SASConfig()
        execution_context = ExecutionContext()
        capability_registry = CapabilityRegistry()
        policy_enforcer = PolicyEnforcer("allow")
        state_machine = AgentStateMachine()
        sovereignty_asserter = SovereigntyAsserter()
        
        return cls(
            config=config,
            execution_context=execution_context,
            capability_registry=capability_registry,
            policy_enforcer=policy_enforcer,
            state_machine=state_machine,
            sovereignty_asserter=sovereignty_asserter,
        )
    
    def _register_default_tools(self):
        """Register default MCP tools."""
        self.register_tool(
            "check_sovereignty",
            "Check the current sovereignty score and get layer status",
            {
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to sas.yaml",
                    }
                },
            },
            ["read_knowledge"],
        )
        
        self.register_tool(
            "query_knowledge",
            "Query the compile-time knowledge graph",
            {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query text",
                    },
                    "source": {
                        "type": "string",
                        "description": "Path to knowledge source directory",
                    },
                },
                "required": ["query"],
            },
            ["read_knowledge"],
        )
        
        self.register_tool(
            "pay_for_resource",
            "Pay for a resource using the virtual card",
            {
                "type": "object",
                "properties": {
                    "resource": {
                        "type": "string",
                        "description": "Resource identifier",
                    },
                    "price": {
                        "type": "number",
                        "description": "Price to pay",
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency (default: USD)",
                        "default": "USD",
                    },
                },
                "required": ["resource", "price"],
            },
            ["process_payments"],
        )

        # ── Quant tools ──────────────────────────────────────────
        self.register_tool(
            "quant_status",
            "Show Sovereign Quant system status",
            {"type": "object", "properties": {}},
            ["read_knowledge"],
        )

        self.register_tool(
            "quant_research",
            "Run autonomous quantitative research",
            {
                "type": "object",
                "properties": {
                    "universe": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ticker universe",
                    },
                    "horizon": {
                        "type": "string",
                        "description": "Time horizon (default: 1y)",
                    },
                },
            },
            ["research_create"],
        )

        self.register_tool(
            "quant_backtest",
            "Run a deterministic backtest",
            {
                "type": "object",
                "properties": {
                    "strategy_id": {
                        "type": "string",
                        "description": "Strategy ID to backtest",
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed (default: 42)",
                    },
                },
            },
            ["backtest_execute"],
        )

        self.register_tool(
            "quant_risk",
            "Evaluate portfolio risk against policy",
            {
                "type": "object",
                "properties": {
                    "weights": {
                        "type": "object",
                        "additionalProperties": {"type": "number"},
                        "description": "Symbol → weight mapping",
                    },
                    "max_position_weight": {
                        "type": "number",
                        "description": "Max single position weight",
                    },
                },
            },
            ["risk_evaluate"],
        )

        self.register_tool(
            "quant_provenance",
            "Inspect provenance lineage for an artifact",
            {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Provenance node ID",
                    },
                },
                "required": ["node_id"],
            },
            ["provenance_read"],
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        schema: dict,
        required_capabilities: list[str],
    ):
        """Register a tool with the MCP server."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": schema,
            "required_capabilities": required_capabilities,
        }
    
    def list_tools(self) -> list[dict]:
        """List all registered tools."""
        return [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for name, tool in self._tools.items()
        ]
    
    def call_tool(self, name: str, arguments: dict) -> MCPToolResult:
        """Call a tool with policy enforcement."""
        if name not in self._tools:
            return MCPToolResult(success=False, error=f"Unknown tool: {name}")
        
        tool = self._tools[name]
        
        # Check capabilities
        for cap in tool["required_capabilities"]:
            if not self.capability_registry.is_granted(cap):
                return MCPToolResult(
                    success=False,
                    error=f"Tool '{name}' requires capability '{cap}' which is not granted",
                )
        
        # Transition state machine
        self.state_machine.transition("Executing")
        
        try:
            result = self._execute_tool(name, arguments)
            self.state_machine.transition("Verifying")
            self.state_machine.transition("Completed")
            return MCPToolResult(success=True, data=result)
        except Exception as e:
            self.state_machine.transition("Failed")
            return MCPToolResult(success=False, error=str(e))
    
    def _execute_tool(self, name: str, arguments: dict) -> Any:
        """Execute the actual tool logic."""
        if name == "check_sovereignty":
            return self._tool_check_sovereignty(arguments)
        elif name == "query_knowledge":
            return self._tool_query_knowledge(arguments)
        elif name == "pay_for_resource":
            return self._tool_pay_for_resource(arguments)
        elif name == "quant_status":
            return self._tool_quant_status(arguments)
        elif name == "quant_research":
            return self._tool_quant_research(arguments)
        elif name == "quant_backtest":
            return self._tool_quant_backtest(arguments)
        elif name == "quant_risk":
            return self._tool_quant_risk(arguments)
        elif name == "quant_provenance":
            return self._tool_quant_provenance(arguments)
        else:
            return {"status": "ok", "tool": name, "arguments": arguments}
    
    def _tool_check_sovereignty(self, arguments: dict) -> dict:
        """Check sovereignty score."""
        config_path = arguments.get("config_path", "sas.yaml")
        try:
            config = parse_sas_yaml(Path(config_path))
            report = generate_report(config)
            return {
                "score": report.score,
                "verdict": report.verdict,
                "owned": report.owned_count,
                "total": report.total_count,
                "layers": [
                    {
                        "name": layer.name,
                        "status": layer.scored_as.value,
                        "reasoning": layer.reasoning,
                    }
                    for layer in report.layers
                ],
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_query_knowledge(self, arguments: dict) -> dict:
        """Query the knowledge graph."""
        query = arguments.get("query", "")
        source = arguments.get("source", "~/sas-knowledge")
        store = arguments.get("store", None)

        from pathlib import Path

        from sas.layers.knowledge_resolver import compile_source, resolve_knowledge_backend

        store_path = store if store else ":memory:"
        adapter, kind = resolve_knowledge_backend(store_path=store_path)

        if store:
            graph = adapter.load()
        else:
            graph = compile_source(adapter, Path(source).expanduser())

        results = adapter.query(graph, query)

        if results:
            return {
                "query": query,
                "source": source,
                "results": [{"label": r.label, "content": r.properties.get("content", "")} for r in results],
                "count": len(results),
                "backend": kind,
            }
        else:
            return {
                "query": query,
                "source": source,
                "results": [],
                "count": 0,
                "status": "empty",
                "reason": "No matching nodes found",
                "backend": kind,
            }
    
    def _tool_pay_for_resource(self, arguments: dict) -> dict:
        """Pay for a resource."""
        # Policy check
        amount = arguments.get("price", 0)
        currency = arguments.get("currency", "USD")
        resource = arguments.get("resource", "")
        
        try:
            self.policy_enforcer.check_payment(amount, currency, resource)
        except PermissionError as e:
            return {"status": "denied", "error": str(e)}
        
        return {
            "status": "completed",
            "resource": resource,
            "amount": amount,
            "currency": currency,
        }

    def _tool_quant_status(self, arguments: dict) -> dict:
        """Show quant system status."""
        return {
            "status": "operational",
            "modules": [
                "engine", "strategy", "backtest", "risk",
                "broker", "market", "provenance", "knowledge",
                "reports", "lifecycle", "agents",
            ],
        }

    def _tool_quant_research(self, arguments: dict) -> dict:
        """Run autonomous quantitative research."""
        from sas.quant.lifecycle import ResearchLifecycle, ResearchStage
        universe = arguments.get("universe", [])
        horizon = arguments.get("horizon", "1y")
        try:
            lifecycle = ResearchLifecycle()
            stage_map = {
                "DATA": ResearchStage.DATASET,
                "DATASET": ResearchStage.HYPOTHESIS,
                "HYPOTHESIS": ResearchStage.SIGNAL,
                "SIGNAL": ResearchStage.STRATEGY,
                "STRATEGY": ResearchStage.BACKTEST,
                "BACKTEST": ResearchStage.EVALUATION,
                "EVALUATION": ResearchStage.RISK_REVIEW,
                "RISK_REVIEW": ResearchStage.APPROVAL,
            }
            for to_stage in stage_map.values():
                lifecycle.transition_to(to_stage, actor="mcp_server")
            return {
                "status": "complete",
                "universe": universe,
                "horizon": horizon,
                "stages": [t.to_stage for t in lifecycle.transitions],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _tool_quant_backtest(self, arguments: dict) -> dict:
        """Run a deterministic backtest."""
        from sas.quant.backtest import BacktestConfig, BacktestEngine
        from sas.quant.strategy import SignalDefinition, StrategyArtifact
        strategy_id = arguments.get("strategy_id", "default")
        seed = arguments.get("seed", 42)
        try:
            strategy = StrategyArtifact(
                strategy_id=strategy_id,
                name=strategy_id,
                signal_definition=SignalDefinition(
                    name=f"{strategy_id}_signal",
                    type="trend",
                    parameters={},
                    lookback_periods=10,
                ),
            )
            config = BacktestConfig(
                strategy=strategy,
                seed=seed,
            )
            engine = BacktestEngine(config)
            result = engine.run()
            return {
                "status": "complete",
                "strategy_id": strategy_id,
                "seed": seed,
                "total_return": result.total_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "trades": result.total_trades,
                "warnings": result.warnings,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _tool_quant_risk(self, arguments: dict) -> dict:
        """Evaluate portfolio risk against policy."""
        weights = arguments.get("weights", {})
        max_pos = arguments.get("max_position_weight", 0.25)
        policy = RiskPolicy(max_position_weight=max_pos)
        engine = RiskEngine(policy)
        result = engine.evaluate(weights, {}, {})
        return {
            "is_compliant": result.is_compliant,
            "breaches": result.breaches,
            "gross_exposure": result.gross_exposure,
        }

    def _tool_quant_provenance(self, arguments: dict) -> dict:
        """Inspect provenance lineage for an artifact."""
        from sas.quant.provenance import ProvenanceGraph
        node_id = arguments.get("node_id", "")
        graph = ProvenanceGraph()
        node = graph.get(node_id)
        if node is None:
            return {"node_id": node_id, "lineage": [], "error": "node not found"}
        lineage = graph.lineage_chain(node_id)
        return {
            "node_id": node_id,
            "lineage": [n.to_dict() for n in lineage],
            "depth": len(lineage),
        }
    
    def serve(self):
        """Start serving MCP requests (stdio JSON-RPC)."""
        logger.info("Starting MCP server")
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = self._handle_request(request)
                # Notifications return None - don't print a response
                if response is not None:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                print(json.dumps({"error": "Invalid JSON"}), flush=True)
    
    def _handle_request(self, request: dict) -> dict | None:
        """Handle an MCP request. Returns None for notifications (no response)."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")
        
        # JSON-RPC 2.0 envelope
        def make_response(result=None, error=None):
            resp = {"jsonrpc": "2.0", "id": req_id}
            if error is not None:
                resp["error"] = error
            else:
                resp["result"] = result
            return resp
        
        # Handle notifications (no id, no response expected)
        if method == "notifications/initialized":
            # Client signals it's ready - no response needed
            return None
        
        # Handle initialize (the handshake)
        if method == "initialize":
            return make_response(result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True}
                },
                "serverInfo": {
                    "name": "sovereign-agent-stack",
                    "version": "1.0.0"
                }
            })
        
        # Handle tools/list
        if method == "tools/list":
            return make_response(result={"tools": self.list_tools()})
        
        # Handle tools/call
        if method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = self.call_tool(name, arguments)
            if result.success:
                return make_response(result={"content": [{"type": "text", "text": json.dumps(result.data)}]})
            else:
                return make_response(error={"code": -32603, "message": result.error or "Tool execution failed"})
        
        # Unknown method
        return make_response(error={"code": -32601, "message": f"Method not found: {method}"})
    
    def handle_request(self, request: dict) -> dict | None:
        """Handle an MCP request (for programmatic use)."""
        return self._handle_request(request)


def run_mcp_server(config_path: str | Path = "sas.yaml"):
    """Run the MCP server."""
    server = MCPServer.from_config(config_path)
    server.serve()


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "sas.yaml"
    run_mcp_server(config_path)
