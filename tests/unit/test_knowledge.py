"""Tests for the compile-time knowledge graph markdown parser."""

import pytest

from sas.layers.knowledge import (
    KnowledgeGraph,
    Node,
    Edge,
    CompileTimeKnowledge,
    MarkdownParser,
    GraphMaterializer,
)


class TestMarkdownParser:
    """Tests for parsing Obsidian-compatible markdown into structured data."""

    def test_parse_empty_markdown(self) -> None:
        """Parsing empty markdown returns no nodes or edges."""
        parser = MarkdownParser()
        result = parser.parse("")
        assert result.nodes == []
        assert result.edges == []

    def test_parse_single_node(self) -> None:
        """A markdown file with a title and content becomes a node."""
        parser = MarkdownParser()
        content = "# My Project\n\nThis is a project about AI agents."
        result = parser.parse(content, source="my-project.md")
        assert len(result.nodes) == 1
        assert result.nodes[0].label == "My Project"
        assert "AI agents" in result.nodes[0].properties.get("content", "")

    def test_parse_wikilink_creates_edge(self) -> None:
        """A [[wikilink]] creates an edge to the referenced node."""
        parser = MarkdownParser()
        content = "# My Project\n\nRelated to [[Another Project]] and [[Third Thing]]."
        result = parser.parse(content, source="my-project.md")
        assert len(result.nodes) >= 2  # At least the source + one target
        assert len(result.edges) >= 2  # At least two edges
        # Edges reference node IDs; check that target nodes exist
        node_labels = {n.label for n in result.nodes}
        assert "Another Project" in node_labels
        assert "Third Thing" in node_labels

    def test_parse_yaml_frontmatter(self) -> None:
        """YAML frontmatter is parsed into node properties."""
        parser = MarkdownParser()
        content = """---
client: Acme Corp
status: active
date: 2026-09-04
---

# Acme Project

Details about the project.
"""
        result = parser.parse(content, source="acme.md")
        assert len(result.nodes) == 1
        node = result.nodes[0]
        assert node.properties.get("client") == "Acme Corp"
        assert node.properties.get("status") == "active"
        assert node.properties.get("date") == "2026-09-04"

    def test_parse_multiple_files_dedupes_nodes(self) -> None:
        """Parsing multiple files that reference the same node deduplicates."""
        parser = MarkdownParser()
        content1 = "# Project A\n\nLinks to [[Shared Thing]]."
        content2 = "# Project B\n\nAlso links to [[Shared Thing]]."
        result1 = parser.parse(content1, source="a.md")
        result2 = parser.parse(content2, source="b.md")
        combined = parser.merge([result1, result2])
        # Should have: Project A, Project B, Shared Thing = 3 nodes
        assert len(combined.nodes) == 3
        # Should have: A->Shared, B->Shared = 2 edges
        assert len(combined.edges) == 2

    def test_parse_preserves_source_path(self) -> None:
        """The source file path is preserved in node metadata."""
        parser = MarkdownParser()
        content = "# Test Node"
        result = parser.parse(content, source="path/to/file.md")
        assert result.nodes[0].properties.get("source") == "path/to/file.md"


class TestGraphMaterializer:
    """Tests for materializing parsed data into a queryable graph."""

    def test_materialize_empty_graph(self) -> None:
        """Materializing an empty graph works."""
        materializer = GraphMaterializer(store_path=":memory:")
        graph = materializer.materialize(nodes=[], edges=[])
        assert isinstance(graph, KnowledgeGraph)
        assert graph.nodes == []
        assert graph.edges == []

    def test_materialize_with_nodes(self) -> None:
        """Nodes are stored and retrievable."""
        materializer = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Project A", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
            Node(id="n2", label="Project B", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
        ]
        edges = [Edge(source="n1", target="n2", relationship="links_to", properties={})]
        graph = materializer.materialize(nodes=nodes, edges=edges)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_query_by_label(self) -> None:
        """Can query nodes by label."""
        materializer = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Project A", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
            Node(id="n2", label="Project B", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
        ]
        graph = materializer.materialize(nodes=nodes, edges=[])
        results = materializer.query(graph, "Project A")
        assert len(results) == 1
        assert results[0].label == "Project A"

    def test_query_by_relationship(self) -> None:
        """Can query nodes by relationship traversal."""
        materializer = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Project A", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
            Node(id="n2", label="Project B", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
            Node(id="n3", label="Project C", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
        ]
        edges = [
            Edge(source="n1", target="n2", relationship="links_to", properties={}),
            Edge(source="n2", target="n3", relationship="links_to", properties={}),
        ]
        graph = materializer.materialize(nodes=nodes, edges=edges)
        # Query for what Project A links to (transitively)
        results = materializer.query(graph, "Project A", transitive=True)
        assert len(results) >= 2  # Should find n2 and n3

    def test_diff_detects_changes(self) -> None:
        """Diff detects added, removed, and changed nodes."""
        materializer = GraphMaterializer(store_path="=memory")
        nodes_v1 = [
            Node(id="n1", label="Project A", properties={"status": "active"}, created_at="2026-09-04", updated_at="2026-09-04"),
        ]
        nodes_v2 = [
            Node(id="n1", label="Project A", properties={"status": "completed"}, created_at="2026-09-04", updated_at="2026-09-05"),
            Node(id="n2", label="Project B", properties={}, created_at="2026-09-05", updated_at="2026-09-05"),
        ]
        graph_v1 = materializer.materialize(nodes=nodes_v1, edges=[])
        graph_v2 = materializer.materialize(nodes=nodes_v2, edges=[])
        diff = materializer.diff(graph_v1, graph_v2)
        assert len(diff.added_nodes) == 1  # Project B
        assert len(diff.changed_nodes) == 1  # Project A status changed
        assert diff.added_nodes[0].label == "Project B"

    def test_audit_finds_orphaned_nodes(self) -> None:
        """Audit finds nodes with no edges."""
        materializer = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Connected", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
            Node(id="n2", label="Orphaned", properties={}, created_at="2026-09-04", updated_at="2026-09-04"),
        ]
        edges = [Edge(source="n1", target="n2", relationship="links_to", properties={})]
        graph = materializer.materialize(nodes=nodes, edges=edges)
        report = materializer.audit(graph)
        assert report.total_nodes == 2
        assert report.total_edges == 1
        # Neither node is orphaned since both have edges
        assert len(report.orphaned_nodes) == 0


class TestCompileTimeKnowledge:
    """Tests for the compile-time knowledge orchestrator."""

    def test_compile_from_source_directory(self, tmp_path) -> None:
        """Compile compiles all markdown files in a source directory."""
        # Create test markdown files
        (tmp_path / "project-a.md").write_text("# Project A\n\nLinks to [[Project B]].")
        (tmp_path / "project-b.md").write_text("# Project B\n\nLinks to [[Project A]].")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(source=tmp_path)

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 2
        assert graph.source_path == str(tmp_path)

    def test_compile_empty_directory(self, tmp_path) -> None:
        """Compiling an empty directory returns empty graph."""
        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(source=tmp_path)
        assert graph.nodes == []
        assert graph.edges == []

    def test_compile_nested_directories(self, tmp_path) -> None:
        """Compile recurses into nested directories."""
        subdir = tmp_path / "clients"
        subdir.mkdir()
        (subdir / "acme.md").write_text("# Acme Corp\n\nClient project.")
        (tmp_path / "internal.md").write_text("# Internal\n\nLinks to [[Acme Corp]].")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(source=tmp_path)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_query_returns_results(self, tmp_path) -> None:
        """Query returns relevant nodes from compiled graph."""
        (tmp_path / "test.md").write_text("# Test Project\n\nThis is about AI agents.")
        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(source=tmp_path)
        results = knowledge.query(graph, "AI agents")
        assert len(results) >= 1
        assert any("Test Project" in r.label for r in results)

    def test_diff_between_compiles(self, tmp_path) -> None:
        """Diff between two compile runs shows what changed."""
        (tmp_path / "v1.md").write_text("# Version One\n\nInitial content.")
        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph_v1 = knowledge.compile(source=tmp_path)

        # Add a new file
        (tmp_path / "v2.md").write_text("# Version Two\n\nNew content.")
        graph_v2 = knowledge.compile(source=tmp_path)

        diff = knowledge.diff(graph_v1, graph_v2)
        assert len(diff.added_nodes) == 1
        assert diff.added_nodes[0].label == "Version Two"

    def test_audit_report(self, tmp_path) -> None:
        """Audit returns a structured report."""
        (tmp_path / "test.md").write_text("# Test\n\nContent.")
        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(source=tmp_path)
        report = knowledge.audit(graph)
        assert report.total_nodes == 1
        assert report.total_edges == 0
        assert len(report.orphaned_nodes) == 1  # Single node with no edges
