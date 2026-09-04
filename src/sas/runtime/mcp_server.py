"""MCP Server with tool execution.

Exposes SAS tools via MCP protocol with policy enforcement,
capability checking, and state machine tracking.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from sas.core.config import parse_sas_yaml, SASConfig
from sas.core.scoring import generate_report
from sas.rust_bridge import (
    ExecutionContext,
    AgentStateMachine,
    CapabilityRegistry,
    PolicyEnforcer,
    SovereigntyAsserter,
)

logger = logging.getLogger(__name__)


@dataclass
class MCPToolResult:
    """Result of an MCP tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None


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
    def from_config(cls, config_path: str | Path) -> "MCPServer":
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
    def from_defaults(cls) -> "MCPServer":
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
        # In a real implementation, this would query the knowledge graph
        return {
            "query": query,
            "source": source,
            "results": [],
            "status": "ok",
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
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                print(json.dumps({"error": "Invalid JSON"}), flush=True)
    
    def _handle_request(self, request: dict) -> dict:
        """Handle an MCP request."""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {"tools": self.list_tools()}
        elif method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = self.call_tool(name, arguments)
            if result.success:
                return {"content": [{"type": "text", "text": json.dumps(result.data)}]}
            else:
                return {"error": {"message": result.error}}
        else:
            return {"error": {"message": f"Unknown method: {method}"}}
    
    def handle_request(self, request: dict) -> dict:
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
