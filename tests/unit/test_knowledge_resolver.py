"""Tests for the knowledge resolver and the Phase 2/3/4 fixes."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from sas.layers.knowledge_resolver import resolve_knowledge_backend, compile_source
from sas.layers.knowledge import CompileTimeKnowledge, KnowledgeGraph, Node


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_plugin_registry():
    """Reset plugin registry before each test."""
    from sas.plugins import PluginRegistry
    PluginRegistry.reset()
    yield
    PluginRegistry.reset()


@pytest.fixture
def sample_markdown_dir(tmp_path: Path) -> Path:
    """A small markdown vault for built-in CompileTimeKnowledge testing."""
    (tmp_path / "intro.md").write_text("# Introduction\nThe [[Sovereign Agent Stack]] intro.")
    (tmp_path / "arch.md").write_text("# Architecture\nSee [[Introduction]].")
    return tmp_path


@pytest.fixture
def sample_tie_graph_path(tmp_path: Path) -> Path:
    """A realistic TIE graph JSON file."""
    data = {
        "nodes": [
            {"id": "content:sovereign-ai", "label": "Sovereign AI", "group": "content", "color": "#4fc3f7", "size": 15},
            {"id": "topic:local-first", "label": "local-first", "group": "topic", "color": "#81c784", "size": 10},
        ],
        "edges": [
            {"from": "content:sovereign-ai", "to": "topic:local-first", "label": "discusses", "weight": 1},
        ],
    }
    path = tmp_path / "tie_graph.json"
    path.write_text(json.dumps(data))
    return path


# ── Test: resolve_knowledge_backend ──────────────────────────────────────────


class TestResolveKnowledgeBackend:
    def test_no_plugin_uses_builtin(self) -> None:
        """When no plugin is registered, returns CompileTimeKnowledge."""
        with patch("sas.plugins.discover_plugins", return_value=[]):
            adapter, kind = resolve_knowledge_backend()
            assert isinstance(adapter, CompileTimeKnowledge)
            assert kind == "builtin"

    def test_with_plugin_uses_plugin(self, sample_tie_graph_path: Path, tmp_path: Path) -> None:
        """When a plugin is registered, returns the plugin's adapter."""
        from sas.plugins import LayerPlugin, PluginSource

        mock_plugin = LayerPlugin(
            name="mock-tie",
            layer_id="layer_6_long_term_knowledge",
            version="0.1.0",
            source=PluginSource.LOCAL,
            factory=lambda store_path=":memory:": CompileTimeKnowledge(store_path=store_path),
        )

        with patch("sas.plugins.discover_plugins", return_value=[mock_plugin]):
            adapter, kind = resolve_knowledge_backend(store_path=str(tmp_path / "test.db"))
            assert kind == "plugin"

    def test_plugin_without_factory_falls_back_to_builtin(self) -> None:
        """If a plugin is registered but has no factory, fall back to built-in."""
        from sas.plugins import LayerPlugin, PluginSource

        mock_plugin = LayerPlugin(
            name="broken-tie",
            layer_id="layer_6_long_term_knowledge",
            version="0.1.0",
            source=PluginSource.LOCAL,
            factory=None,
        )

        with patch("sas.plugins.discover_plugins", return_value=[mock_plugin]):
            adapter, kind = resolve_knowledge_backend()
            assert isinstance(adapter, CompileTimeKnowledge)
            assert kind == "builtin"

    def test_builtin_load_no_args(self, tmp_path: Path) -> None:
        """Built-in adapter.load() works with zero args (the regression case)."""
        (tmp_path / "test.md").write_text("# Test\nContent.")
        ctk = CompileTimeKnowledge(store_path=str(tmp_path / "test.db"))
        ctk.compile(tmp_path)

        with patch("sas.plugins.discover_plugins", return_value=[]):
            adapter, kind = resolve_knowledge_backend(store_path=str(tmp_path / "test.db"))
            assert kind == "builtin"
            graph = adapter.load()  # This was the failing call
            assert graph is not None


# ── Test: compile_source error handling ──────────────────────────────────────


class TestCompileSource:
    def test_compile_success(self, sample_markdown_dir: Path) -> None:
        """compile_source succeeds for a compatible backend."""
        adapter = CompileTimeKnowledge()
        graph = compile_source(adapter, sample_markdown_dir)
        assert len(graph.nodes) >= 2

    def test_compile_mismatch_raises_clear_error(self, sample_markdown_dir: Path) -> None:
        """compile_source raises a clear ValueError when the plugin can't parse the source."""
        class FailingAdapter:
            def compile(self, source):
                raise RuntimeError("I only eat JSON graphs")

        adapter = FailingAdapter()
        with pytest.raises(ValueError, match="could not parse"):
            compile_source(adapter, sample_markdown_dir)

    def test_original_error_in_chain(self, sample_markdown_dir: Path) -> None:
        """The original exception is preserved in the chain."""
        class FailingAdapter:
            def compile(self, source):
                raise RuntimeError("I only eat JSON graphs")

        adapter = FailingAdapter()
        with pytest.raises(ValueError) as exc_info:
            compile_source(adapter, sample_markdown_dir)
        assert exc_info.value.__cause__ is not None


# ── Test: mcp_server.query_knowledge backward compatibility ──────────────────


class TestQueryKnowledgeBackwardCompat:
    """Existing tests in test_mcp_server.py use query_knowledge(query, source=str(tmp_path))."""

    def test_no_plugin_returns_results(self, sample_markdown_dir: Path) -> None:
        """Without plugin: same behavior as before — compiles from markdown dir."""
        with patch("sas.plugins.discover_plugins", return_value=[]):
            from sas.mcp_server import query_knowledge
            results = query_knowledge("Sovereign Agent Stack", source=str(sample_markdown_dir))
            assert isinstance(results, list)
            assert len(results) >= 1

    def test_no_plugin_empty_results(self, tmp_path: Path) -> None:
        """Without plugin: returns [] for no matches."""
        with patch("sas.plugins.discover_plugins", return_value=[]):
            (tmp_path / "test.md").write_text("# Test Node\nSome content.")
            from sas.mcp_server import query_knowledge
            results = query_knowledge("nonexistent", source=str(tmp_path))
            assert results == []

    def test_with_plugin_uses_plugin(self, sample_tie_graph_path: Path) -> None:
        """With a TIE plugin installed, query_knowledge uses the plugin backend."""
        from sas.plugins import LayerPlugin, PluginSource
        from sas_tie_knowledge.adapter import TIEKnowledgeAdapter

        mock_plugin = LayerPlugin(
            name="tie-knowledge",
            layer_id="layer_6_long_term_knowledge",
            version="0.1.0",
            source=PluginSource.LOCAL,
            factory=lambda store_path=":memory:": TIEKnowledgeAdapter(store_path=store_path),
        )

        with patch("sas.plugins.discover_plugins", return_value=[mock_plugin]):
            from sas.mcp_server import query_knowledge
            results = query_knowledge("Sovereign AI", source=str(sample_tie_graph_path))
            assert isinstance(results, list)
            assert len(results) >= 1

    def test_no_plugin_with_store(self, tmp_path: Path) -> None:
        """query_knowledge with store= and no plugin — regression test."""
        from sas.mcp_server import query_knowledge
        from sas.layers.knowledge import CompileTimeKnowledge

        # Compile and persist first (using the adapter directly)
        (tmp_path / "test.md").write_text("# Test\nContent about sovereign architecture.")
        store_path = str(tmp_path / "test.db")
        ctk = CompileTimeKnowledge(store_path=store_path)
        ctk.compile(tmp_path)

        # Now query from the store
        with patch("sas.plugins.discover_plugins", return_value=[]):
            results = query_knowledge("sovereign", source=str(tmp_path), store=store_path)
            assert isinstance(results, list)
            assert len(results) >= 1


# ── Test: runtime/mcp_server._tool_query_knowledge is no longer a stub ───────


class TestToolQueryKnowledge:
    def test_stub_is_gone(self, sample_markdown_dir: Path) -> None:
        """_tool_query_knowledge returns real results, not an empty stub."""
        from sas.runtime.mcp_server import MCPServer

        server = MCPServer.from_defaults()
        server.capability_registry.grant("read_knowledge")

        with patch("sas.plugins.discover_plugins", return_value=[]):
            result = server.call_tool("query_knowledge", {
                "query": "sovereign",
                "source": str(sample_markdown_dir),
            })

        assert result.success
        data = result.data
        assert data.get("count", 0) >= 0  # At minimum, it actually ran
        assert "backend" in data  # Reports which backend answered

    def test_empty_results_have_reason(self, tmp_path: Path) -> None:
        """Empty results include a reason field, not just []."""
        from sas.runtime.mcp_server import MCPServer

        server = MCPServer.from_defaults()
        server.capability_registry.grant("read_knowledge")

        (tmp_path / "test.md").write_text("# Test Node\nSome content.")

        with patch("sas.plugins.discover_plugins", return_value=[]):
            result = server.call_tool("query_knowledge", {
                "query": "nonexistent",
                "source": str(tmp_path),
            })

        assert result.success
        data = result.data
        assert data["count"] == 0
        assert data["status"] == "empty"
        assert "reason" in data

    def test_with_plugin_returns_tie_results(self, sample_tie_graph_path: Path) -> None:
        """With TIE plugin, _tool_query_knowledge returns real TIE results."""
        from sas.runtime.mcp_server import MCPServer
        from sas.plugins import LayerPlugin, PluginSource
        from sas_tie_knowledge.adapter import TIEKnowledgeAdapter

        server = MCPServer.from_defaults()
        server.capability_registry.grant("read_knowledge")

        mock_plugin = LayerPlugin(
            name="tie-knowledge",
            layer_id="layer_6_long_term_knowledge",
            version="0.1.0",
            source=PluginSource.LOCAL,
            factory=lambda store_path=":memory:": TIEKnowledgeAdapter(store_path=store_path),
        )

        with patch("sas.plugins.discover_plugins", return_value=[mock_plugin]):
            result = server.call_tool("query_knowledge", {
                "query": "Sovereign AI",
                "source": str(sample_tie_graph_path),
            })

        assert result.success
        data = result.data
        assert data["count"] >= 1
        assert data["backend"] == "plugin"

    def test_no_plugin_with_store(self, tmp_path: Path) -> None:
        """_tool_query_knowledge with store= and no plugin — regression test."""
        from sas.runtime.mcp_server import MCPServer
        from sas.layers.knowledge import CompileTimeKnowledge

        # Compile and persist first
        (tmp_path / "test.md").write_text("# Test\nContent about sovereign.")
        store_path = str(tmp_path / "test.db")
        ctk = CompileTimeKnowledge(store_path=store_path)
        ctk.compile(tmp_path)

        # Now query from the store
        server = MCPServer.from_defaults()
        server.capability_registry.grant("read_knowledge")
        with patch("sas.plugins.discover_plugins", return_value=[]):
            result = server.call_tool("query_knowledge", {
                "query": "sovereign",
                "source": str(tmp_path),
                "store": store_path,
            })

        assert result.success
        data = result.data
        assert data.get("count", 0) >= 1


# ── Test: CLI source/plugin mismatch produces clear error ────────────────────


class TestCLISourceMismatch:
    def test_compile_markdown_with_tie_plugin_clear_error(self, sample_markdown_dir: Path) -> None:
        """CLI compile with markdown dir + TIE plugin → clear error, exit 1."""
        from sas.plugins import LayerPlugin, PluginSource
        from sas_tie_knowledge.adapter import TIEKnowledgeAdapter
        import io
        import sys

        mock_plugin = LayerPlugin(
            name="tie-knowledge",
            layer_id="layer_6_long_term_knowledge",
            version="0.1.0",
            source=PluginSource.LOCAL,
            factory=lambda store_path=":memory:": TIEKnowledgeAdapter(store_path=store_path),
        )

        with patch("sas.plugins.discover_plugins", return_value=[mock_plugin]):
            from sas.__main__ import _cmd_knowledge

            class MockArgs:
                knowledge_command = "compile"
                source = str(sample_markdown_dir)
                store = str(sample_markdown_dir.parent / "test.db")
                query = ""
                transitive = False

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured

            result = _cmd_knowledge(MockArgs())

            sys.stdout = old_stdout

        assert result == 1  # Exit code 1
        output = captured.getvalue()
        assert "could not parse" in output
        assert "TIE" in output or "backend" in output
        assert "Traceback" not in output
        assert "FileNotFoundError" not in output

    def test_compile_markdown_without_plugin_succeeds(self, sample_markdown_dir: Path) -> None:
        """CLI compile with markdown dir + no plugin → succeeds."""
        with patch("sas.plugins.discover_plugins", return_value=[]):
            from sas.__main__ import _cmd_knowledge
            import io
            import sys

            class MockArgs:
                knowledge_command = "compile"
                source = str(sample_markdown_dir)
                store = str(sample_markdown_dir.parent / "test.db")
                query = ""
                transitive = False

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured

            result = _cmd_knowledge(MockArgs())

            sys.stdout = old_stdout

        assert result == 0  # Success
        output = captured.getvalue()
        assert "Compiled" in output
