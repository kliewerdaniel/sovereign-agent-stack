# — Unit tests for the Compile-Time Knowledge Graph (Phase 2) —

import pytest
from pathlib import Path
import tempfile

from sas.layers.knowledge import (
    CompileTimeKnowledge,
    GraphMaterializer,
    KnowledgeGraph,
    MarkdownParser,
    Node,
    Edge,
    ParsedResult,
)


# ── MarkdownParser ────────────────────────────────────────────────────────────

class TestMarkdownParser:
    def test_parse_basic_wikilinks(self):
        parser = MarkdownParser()
        result = parser.parse("# Hello World\n\nThis is a [[test link]].", "test.md")
        assert len(result.nodes) == 2  # Hello + test link
        assert len(result.edges) == 1
        assert result.edges[0].relationship == "links_to"

    def test_parse_no_heading_returns_empty(self):
        parser = MarkdownParser()
        result = parser.parse("No heading here, just text.", "test.md")
        assert result.nodes == []
        assert result.edges == []

    def test_parse_empty_content(self):
        parser = MarkdownParser()
        result = parser.parse("", "test.md")
        assert result.nodes == []
        assert result.edges == []

    def test_parse_multiple_wikilinks(self):
        parser = MarkdownParser()
        content = "# Main\n\nLinks to [[A]] and [[B]] and [[C]]."
        result = parser.parse(content, "test.md")
        assert len(result.nodes) == 4  # Main + A + B + C
        assert len(result.edges) == 3

    def test_parse_frontmatter(self):
        parser = MarkdownParser()
        content = "---\ntags: [sovereignty]\n---\n# Test"
        result = parser.parse(content, "test.md")
        assert len(result.nodes) == 1
        assert "tags" in result.nodes[0].properties

    def test_parse_preserves_source(self):
        parser = MarkdownParser()
        result = parser.parse("# My Doc", "notes/my-doc.md")
        assert result.nodes[0].properties["source"] == "notes/my-doc.md"

    def test_merge_deduplicates_by_label(self):
        parser = MarkdownParser()
        r1 = parser.parse("# Doc\n\n[[Link]]", "a.md")
        r2 = parser.parse("# Doc\n\n[[Link]]", "b.md")
        merged = parser.merge([r1, r2])
        # Same label → deduplicated
        labels = [n.label for n in merged.nodes]
        assert labels.count("Doc") == 1
        assert labels.count("Link") == 1


# ── GraphMaterializer ──────────────────────────────────────────────────────────

class TestGraphMaterializer:
    def test_materialize_returns_graph(self):
        mat = GraphMaterializer(store_path=":memory:")
        nodes = [Node(id="n1", label="Test", properties={}, created_at="2024-01-01", updated_at="2024-01-01")]
        edges = []
        graph = mat.materialize(nodes, edges)
        assert isinstance(graph, KnowledgeGraph)
        assert len(graph.nodes) == 1

    def test_query_by_label(self):
        mat = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Apple", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
            Node(id="n2", label="Banana", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ]
        graph = mat.materialize(nodes, [])
        results = mat.query(graph, "apple")
        assert len(results) == 1
        assert results[0].label == "Apple"

    def test_query_by_content(self):
        mat = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Doc", properties={"content": "sovereign agent stack"}, created_at="2024-01-01", updated_at="2024-01-01"),
        ]
        graph = mat.materialize(nodes, [])
        results = mat.query(graph, "sovereign")
        assert len(results) == 1

    def test_query_transitive(self):
        mat = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="A", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
            Node(id="n2", label="B", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
            Node(id="n3", label="C", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ]
        edges = [
            Edge(source="n1", target="n2", relationship="links_to", properties={}),
            Edge(source="n2", target="n3", relationship="links_to", properties={}),
        ]
        graph = mat.materialize(nodes, edges)
        results = mat.query(graph, "A", transitive=True)
        # Should find A (direct) + B (1 hop) + C (2 hops)
        assert len(results) == 3

    def test_diff_added_nodes(self):
        mat = GraphMaterializer(store_path=":memory:")
        old = mat.materialize([
            Node(id="n1", label="A", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ], [])
        new = mat.materialize([
            Node(id="n1", label="A", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
            Node(id="n2", label="B", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ], [])
        diff = mat.diff(old, new)
        assert len(diff.added_nodes) == 1
        assert diff.added_nodes[0].label == "B"

    def test_diff_removed_nodes(self):
        mat = GraphMaterializer(store_path=":memory:")
        old = mat.materialize([
            Node(id="n1", label="A", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
            Node(id="n2", label="B", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ], [])
        new = mat.materialize([
            Node(id="n1", label="A", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ], [])
        diff = mat.diff(old, new)
        assert len(diff.removed_nodes) == 1
        assert diff.removed_nodes[0].label == "B"

    def test_audit_finds_orphaned(self):
        mat = GraphMaterializer(store_path=":memory:")
        nodes = [
            Node(id="n1", label="Connected", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
            Node(id="n2", label="Orphaned", properties={}, created_at="2024-01-01", updated_at="2024-01-01"),
        ]
        edges = [Edge(source="n1", target="n2", relationship="links_to", properties={})]
        graph = mat.materialize(nodes, edges)
        report = mat.audit(graph)
        assert report.total_nodes == 2
        assert report.total_edges == 1
        # Both n1 and n2 are connected (n1 as source, n2 as target)
        assert len(report.orphaned_nodes) == 0


# ── CompileTimeKnowledge (integration) ─────────────────────────────────────────

class TestCompileTimeKnowledge:
    def test_compile_single_file(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Hello\n\n[[World]]")
        ctk = CompileTimeKnowledge(store_path=":memory:")
        graph = ctk.compile(md)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_compile_directory(self, tmp_path):
        (tmp_path / "a.md").write_text("# Doc A\n\n[[B]]")
        (tmp_path / "b.md").write_text("# Doc B\n\n[[A]]")
        ctk = CompileTimeKnowledge(store_path=":memory:")
        graph = ctk.compile(tmp_path)
        # Should have: Doc A, B (from a.md), Doc B, A (from b.md)
        # After merge: Doc A, Doc B, A, B — but A and B labels dedupe
        assert len(graph.nodes) >= 2

    def test_query_after_compile(self, tmp_path):
        md = tmp_path / "sovereignty.md"
        md.write_text("# Sovereign Stack\n\nA [[local-first]] architecture.")
        ctk = CompileTimeKnowledge(store_path=":memory:")
        graph = ctk.compile(md)
        results = ctk.query(graph, "sovereign")
        assert len(results) >= 1

    def test_diff_after_compile(self, tmp_path):
        md = tmp_path / "v1.md"
        md.write_text("# Version One\n\n[[Alpha]]")
        ctk = CompileTimeKnowledge(store_path=":memory:")
        g1 = ctk.compile(md)

        md.write_text("# Version One\n\n[[Alpha]] and [[Beta]]")
        g2 = ctk.compile(md)

        diff = ctk.diff(g1, g2)
        assert len(diff.added_nodes) >= 1

    def test_audit_after_compile(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# Root\n\n[[Child]]")
        ctk = CompileTimeKnowledge(store_path=":memory:")
        graph = ctk.compile(md)
        report = ctk.audit(graph)
        assert report.total_nodes == 2
        assert report.total_edges == 1

    def test_compile_non_md_file_ignored(self, tmp_path):
        (tmp_path / "notes.txt").write_text("Not markdown")
        (tmp_path / "doc.md").write_text("# Valid")
        ctk = CompileTimeKnowledge(store_path=":memory:")
        graph = ctk.compile(tmp_path)
        assert len(graph.nodes) == 1
        assert graph.nodes[0].label == "Valid"
