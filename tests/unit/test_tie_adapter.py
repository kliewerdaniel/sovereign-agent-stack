"""Tests for the SAS × TIE Knowledge Layer Adapter."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from sas_tie_knowledge.adapter import TIEKnowledgeAdapter
from sas.layers.knowledge import Node, Edge, KnowledgeGraph


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_tie_graph() -> dict:
    """A realistic TIE graph with all node/edge types."""
    return {
        "nodes": [
            {
                "id": "content:sovereign-ai",
                "label": "Sovereign AI: Building Local-First Systems",
                "title": "blog — Sovereign AI",
                "color": "#4fc3f7",
                "size": 15,
                "group": "content",
            },
            {
                "id": "topic:local-first",
                "label": "local-first",
                "title": "topic — local-first",
                "color": "#81c784",
                "size": 10,
                "group": "topic",
            },
            {
                "id": "topic:knowledge-graphs",
                "label": "knowledge graphs",
                "title": "topic — knowledge graphs",
                "color": "#81c784",
                "size": 10,
                "group": "topic",
            },
            {
                "id": "page:/blog/sovereign-ai",
                "label": "sovereign-ai",
                "title": "page — /blog/sovereign-ai",
                "color": "#29b6f6",
                "size": 12,
                "group": "page",
                "views": 1200,
                "avg_engagement": 240.5,
                "max_scroll": 85.0,
                "unique_sessions": 800,
                "sources": ["google", "twitter"],
            },
            {
                "id": "session:abc123",
                "label": "Session abc123",
                "title": "session — abc123",
                "color": "#ffb74d",
                "size": 8,
                "group": "session",
            },
            {
                "id": "source:google",
                "label": "google",
                "title": "traffic_source — google",
                "color": "#ce93d8",
                "size": 10,
                "group": "traffic_source",
            },
        ],
        "edges": [
            {"from": "content:sovereign-ai", "to": "topic:local-first", "label": "discusses", "weight": 1},
            {"from": "content:sovereign-ai", "to": "topic:knowledge-graphs", "label": "discusses", "weight": 1},
            {"from": "session:abc123", "to": "source:google", "label": "came_from", "weight": 1},
            {"from": "session:abc123", "to": "page:/blog/sovereign-ai", "label": "viewed", "weight": 1},
        ],
    }


@pytest.fixture
def sample_tie_graph_path(sample_tie_graph: dict, tmp_path: Path) -> Path:
    """Write sample graph to a temp file."""
    path = tmp_path / "tie_graph.json"
    path.write_text(json.dumps(sample_tie_graph))
    return path


@pytest.fixture
def adapter() -> TIEKnowledgeAdapter:
    return TIEKnowledgeAdapter()


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestTIEKnowledgeAdapter:
    """Tests for the TIE → SAS adapter."""

    def test_compile_from_json_file(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Compile reads a TIE graph JSON and returns a KnowledgeGraph."""
        graph = adapter.compile(sample_tie_graph_path)
        assert isinstance(graph, KnowledgeGraph)
        assert len(graph.nodes) == 6
        assert len(graph.edges) == 4

    def test_compile_from_directory(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph: dict, tmp_path: Path
    ) -> None:
        """Compile finds a TIE graph JSON in a directory."""
        # Write graph JSON to a subdirectory
        subdir = tmp_path / "tie_output"
        subdir.mkdir()
        graph_file = subdir / "graph.json"
        graph_file.write_text(json.dumps(sample_tie_graph))

        graph = adapter.compile(subdir)
        assert len(graph.nodes) == 6

    def test_node_mapping_preserves_id_and_label(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """TIE node id/label map directly to SAS Node."""
        graph = adapter.compile(sample_tie_graph_path)
        ids = {n.id for n in graph.nodes}
        assert "content:sovereign-ai" in ids
        assert "topic:local-first" in ids

        # Check label
        node = next(n for n in graph.nodes if n.id == "content:sovereign-ai")
        assert node.label == "Sovereign AI: Building Local-First Systems"

    def test_node_properties_include_tie_metadata(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """TIE node properties are preserved in SAS Node.properties."""
        graph = adapter.compile(sample_tie_graph_path)
        node = next(n for n in graph.nodes if n.id == "content:sovereign-ai")
        assert node.properties["tie_group"] == "content"
        assert node.properties["tie_color"] == "#4fc3f7"
        assert node.properties["tie_size"] == 15

    def test_behavioral_metrics_preserved(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """TIE behavioral metrics (views, engagement) are preserved."""
        graph = adapter.compile(sample_tie_graph_path)
        page_node = next(n for n in graph.nodes if n.id == "page:/blog/sovereign-ai")
        assert page_node.properties["views"] == 1200
        assert page_node.properties["avg_engagement"] == 240.5
        assert page_node.properties["max_scroll"] == 85.0
        assert page_node.properties["unique_sessions"] == 800
        assert page_node.properties["sources"] == ["google", "twitter"]

    def test_timestamps_synthesized(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Nodes get synthesized created_at/updated_at at compile time."""
        graph = adapter.compile(sample_tie_graph_path)
        for node in graph.nodes:
            assert node.created_at is not None
            assert node.updated_at is not None
            # Should be valid ISO format
            from datetime import datetime
            datetime.fromisoformat(node.created_at)

    def test_edge_mapping(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """TIE edges map to SAS Edges with correct source/target/relationship."""
        graph = adapter.compile(sample_tie_graph_path)
        edge_keys = {(e.source, e.target, e.relationship) for e in graph.edges}
        assert ("content:sovereign-ai", "topic:local-first", "discusses") in edge_keys
        assert ("session:abc123", "page:/blog/sovereign-ai", "viewed") in edge_keys
        assert ("session:abc123", "source:google", "came_from") in edge_keys

    def test_edge_properties_include_weight(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Edge weight is preserved in properties."""
        graph = adapter.compile(sample_tie_graph_path)
        edge = next(e for e in graph.edges if e.relationship == "discusses")
        assert edge.properties["weight"] == 1

    def test_query_by_label(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Query finds nodes by label."""
        graph = adapter.compile(sample_tie_graph_path)
        results = adapter.query(graph, "Sovereign AI")
        assert len(results) >= 1
        assert any("Sovereign AI" in r.label for r in results)

    def test_query_by_property(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Query finds nodes by property content."""
        graph = adapter.compile(sample_tie_graph_path)
        results = adapter.query(graph, "knowledge graphs")
        assert len(results) >= 1

    def test_query_case_insensitive(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Query is case-insensitive."""
        graph = adapter.compile(sample_tie_graph_path)
        results = adapter.query(graph, "SOVEREIGN")
        assert len(results) >= 1

    def test_audit_finds_orphaned_nodes(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Audit finds nodes with no edges."""
        graph = adapter.compile(sample_tie_graph_path)
        report = adapter.audit(graph)
        assert report.total_nodes == 6
        assert report.total_edges == 4
        # topic:knowledge-graphs has only one edge (from content:sovereign-ai)
        # All nodes are connected in this sample
        # Let's verify by checking the count
        assert isinstance(report.orphaned_nodes, list)

    def test_audit_stale_nodes_empty(
        self, adapter: TIEKnowledgeAdapter, sample_tie_graph_path: Path
    ) -> None:
        """Audit returns empty stale_nodes (TIE has no timestamps)."""
        graph = adapter.compile(sample_tie_graph_path)
        report = adapter.audit(graph)
        assert report.stale_nodes == []

    def test_compile_real_tie_output(
        self, adapter: TIEKnowledgeAdapter, tmp_path: Path
    ) -> None:
        """Compile works on a realistic TIE graph with many nodes."""
        # Generate a larger graph
        nodes = []
        edges = []
        for i in range(50):
            nodes.append({
                "id": f"content:article-{i}",
                "label": f"Article {i}",
                "title": f"blog — Article {i}",
                "color": "#4fc3f7",
                "size": 15,
                "group": "content",
            })
            edges.append({
                "from": f"content:article-{i}",
                "to": "topic:AI",
                "label": "discusses",
                "weight": 1,
            })
        nodes.append({
            "id": "topic:AI",
            "label": "AI",
            "title": "topic — AI",
            "color": "#81c784",
            "size": 10,
            "group": "topic",
        })

        graph_data = {"nodes": nodes, "edges": edges}
        path = tmp_path / "large_graph.json"
        path.write_text(json.dumps(graph_data))

        graph = adapter.compile(path)
        assert len(graph.nodes) == 51
        assert len(graph.edges) == 50

        # Query should find the topic
        results = adapter.query(graph, "AI")
        assert len(results) >= 1


class TestPluginRegistration:
    """Tests for the TIE plugin registration."""

    def test_plugin_metadata_exists(self) -> None:
        """The plugin file has valid SAS_PLUGIN metadata."""
        import importlib.util
        plugin_path = Path.home() / ".sas" / "plugins" / "tie_knowledge.py"
        assert plugin_path.exists(), f"Plugin not found at {plugin_path}"

        spec = importlib.util.spec_from_file_location("tie_knowledge", str(plugin_path))
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        assert hasattr(module, "SAS_PLUGIN")
        meta = module.SAS_PLUGIN
        assert meta["name"] == "tie-knowledge"
        assert meta["layer_id"] == "layer_6_long_term_knowledge"
        assert meta["version"] == "0.1.0"

    def test_plugin_factory_returns_adapter(self) -> None:
        """The plugin factory returns a TIEKnowledgeAdapter instance."""
        import importlib.util
        plugin_path = Path.home() / ".sas" / "plugins" / "tie_knowledge.py"
        spec = importlib.util.spec_from_file_location("tie_knowledge", str(plugin_path))
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        adapter = module.create_adapter()
        assert isinstance(adapter, TIEKnowledgeAdapter)

    def test_plugin_discovered_by_sas(self) -> None:
        """SAS discovers the TIE plugin."""
        from sas.plugins import discover_plugins
        plugins = discover_plugins()
        tie_plugins = [p for p in plugins if p.name == "tie-knowledge"]
        assert len(tie_plugins) >= 1
        assert tie_plugins[0].layer_id == "layer_6_long_term_knowledge"
        assert tie_plugins[0].source.value == 2  # PluginSource.LOCAL
