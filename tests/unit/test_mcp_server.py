"""Tests for the MCP server."""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from sas.mcp_server import (
    MCP_TOOLS,
    check_sovereignty,
    handle_mcp_request,
    pay_for_resource,
    query_knowledge,
)


class TestCheckSovereignty:
    """Tests for the check_sovereignty tool."""

    def test_returns_score_and_verdict(self) -> None:
        """Returns score, verdict, and layer status."""
        result = check_sovereignty()
        assert "score" in result
        assert "verdict" in result
        assert "layers" in result
        assert isinstance(result["layers"], list)

    def test_all_layers_present(self) -> None:
        """All 8 layers are reported."""
        result = check_sovereignty()
        assert len(result["layers"]) == 8


class TestQueryKnowledge:
    """Tests for the query_knowledge tool."""

    def test_returns_results(self, tmp_path) -> None:
        """Returns matching results."""
        (tmp_path / "test.md").write_text("""
# Test Node
This is a test node with content.
""")
        # Explicitly test the built-in backend (no plugin)
        with patch("sas.plugins.discover_plugins", return_value=[]):
            results = query_knowledge("test", source=str(tmp_path))
        assert len(results) >= 1
        assert any("Test Node" in r["label"] for r in results)

    def test_no_results(self, tmp_path) -> None:
        """Returns empty list when no matches."""
        (tmp_path / "test.md").write_text("""
# Test Node
Some content.
""")
        # Explicitly test the built-in backend (no plugin)
        with patch("sas.plugins.discover_plugins", return_value=[]):
            results = query_knowledge("nonexistent", source=str(tmp_path))
        assert results == []

    def test_with_plugin_uses_plugin(self, tmp_path) -> None:
        """With a plugin registered, query_knowledge uses the plugin backend."""
        from sas.plugins import LayerPlugin, PluginSource
        from sas_tie_knowledge.adapter import TIEKnowledgeAdapter

        # Create a TIE graph export
        import json
        (tmp_path / "tie_graph.json").write_text(json.dumps({
            "nodes": [
                {"id": "content:test", "label": "Test Content", "group": "content", "color": "#4fc3f7", "size": 15},
            ],
            "edges": [],
        }))

        mock_plugin = LayerPlugin(
            name="tie-knowledge",
            layer_id="layer_6_long_term_knowledge",
            version="0.1.0",
            source=PluginSource.LOCAL,
            factory=lambda store_path=":memory:": TIEKnowledgeAdapter(store_path=store_path),
        )

        with patch("sas.plugins.discover_plugins", return_value=[mock_plugin]):
            results = query_knowledge("Test Content", source=str(tmp_path / "tie_graph.json"))

        assert len(results) >= 1
        assert any("Test Content" in r["label"] for r in results)


class TestPayForResource:
    """Tests for the pay_for_resource tool."""

    def test_returns_receipt(self) -> None:
        """Returns payment receipt."""
        result = pay_for_resource("test.com", 10.0)
        assert result["status"] == "completed"
        assert result["amount"] == 10.0
        assert "payment_id" in result

    def test_exceeds_limit(self) -> None:
        """Raises when exceeding limit."""
        with pytest.raises(ValueError):
            pay_for_resource("expensive.com", 1000.0)


class TestHandleMcpRequest:
    """Tests for the MCP request handler."""

    def test_known_tool(self) -> None:
        """Handles a known tool request."""
        request = {"tool": "check_sovereignty", "params": {}}
        response = handle_mcp_request(request)
        assert "result" in response
        assert "error" not in response

    def test_unknown_tool(self) -> None:
        """Returns error for unknown tool."""
        request = {"tool": "unknown_tool", "params": {}}
        response = handle_mcp_request(request)
        assert "error" in response

    def test_tool_error(self) -> None:
        """Returns error when tool raises."""
        request = {"tool": "pay_for_resource", "params": {"resource": "x", "price": 10000.0}}
        response = handle_mcp_request(request)
        assert "error" in response


class TestMcpToolsRegistry:
    """Tests for the MCP tools registry."""

    def test_all_tools_present(self) -> None:
        """All expected tools are registered."""
        assert "check_sovereignty" in MCP_TOOLS
        assert "query_knowledge" in MCP_TOOLS
        assert "pay_for_resource" in MCP_TOOLS

    def test_tool_has_function(self) -> None:
        """Each tool has a callable function."""
        for name, tool in MCP_TOOLS.items():
            assert "function" in tool
            assert callable(tool["function"])

    def test_tool_has_description(self) -> None:
        """Each tool has a description."""
        for name, tool in MCP_TOOLS.items():
            assert "description" in tool
            assert len(tool["description"]) > 0
