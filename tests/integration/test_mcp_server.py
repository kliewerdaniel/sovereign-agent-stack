"""Tests for MCP Server."""
from __future__ import annotations

import json
import pytest

from sas.runtime.mcp_server import MCPServer, MCPToolResult


class TestMCPServer:
    """Tests for MCPServer."""
    
    def test_from_defaults(self):
        server = MCPServer.from_defaults()
        assert server.config is not None
        assert server.execution_context is not None
    
    def test_list_tools(self):
        server = MCPServer.from_defaults()
        tools = server.list_tools()
        assert len(tools) >= 3  # At least the default tools
        tool_names = [t["name"] for t in tools]
        assert "check_sovereignty" in tool_names
        assert "query_knowledge" in tool_names
        assert "pay_for_resource" in tool_names
    
    def test_register_tool(self):
        server = MCPServer.from_defaults()
        server.register_tool(
            "my_tool",
            "My custom tool",
            {"type": "object", "properties": {}},
            ["read_filesystem"],
        )
        tools = server.list_tools()
        assert any(t["name"] == "my_tool" for t in tools)
    
    def test_call_tool_success(self):
        server = MCPServer.from_defaults()
        server.capability_registry.grant("read_knowledge")
        result = server.call_tool("check_sovereignty", {})
        assert result.success
        assert result.data is not None
    
    def test_call_tool_unknown(self):
        server = MCPServer.from_defaults()
        result = server.call_tool("nonexistent_tool", {})
        assert not result.success
        assert result.error is not None
        assert "Unknown tool" in result.error
    
    def test_call_tool_missing_capability(self):
        server = MCPServer.from_defaults()
        # Don't grant process_payments
        result = server.call_tool("pay_for_resource", {
            "resource": "test",
            "price": 10.0,
        })
        assert not result.success
        assert result.error is not None
        assert "requires capability" in result.error
    
    def test_handle_request_tools_list(self):
        server = MCPServer.from_defaults()
        response = server.handle_request({"method": "tools/list"})
        assert "tools" in response
        assert len(response["tools"]) >= 3
    
    def test_handle_request_tools_call(self):
        server = MCPServer.from_defaults()
        server.capability_registry.grant("read_knowledge")
        response = server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "check_sovereignty",
                "arguments": {},
            },
        })
        assert "content" in response
    
    def test_handle_request_unknown_method(self):
        server = MCPServer.from_defaults()
        response = server.handle_request({"method": "unknown"})
        assert "error" in response


class TestMCPToolResult:
    """Tests for MCPToolResult."""
    
    def test_success_result(self):
        result = MCPToolResult(success=True, data={"key": "value"})
        assert result.success
        assert result.data == {"key": "value"}
        assert result.error is None
    
    def test_error_result(self):
        result = MCPToolResult(success=False, error="Something went wrong")
        assert not result.success
        assert result.error == "Something went wrong"
        assert result.data is None
