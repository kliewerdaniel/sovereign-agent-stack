"""Compile-time knowledge graph — the layer that differentiates SAS from ARGO alone.

A fact compiled once into a stable, inspectable, versionable node is an asset.
A fact re-derived at query time from a context window is a liability.
"""

from __future__ import annotations

import os
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol


@dataclass
class ParsedResult:
    """Result of parsing a single markdown file."""
    nodes: list[Node]
    edges: list[Edge]


@dataclass
class Node:
    """A node in the knowledge graph."""
    id: str
    label: str
    properties: dict
    created_at: str
    updated_at: str


@dataclass
class Edge:
    """A directed edge between two nodes."""
    source: str
    target: str
    relationship: str
    properties: dict


@dataclass
class KnowledgeGraph:
    """A compiled knowledge graph."""
    nodes: list[Node]
    edges: list[Edge]
    compiled_at: str
    source_path: str


@dataclass
class Diff:
    """Difference between two knowledge graph states."""
    added_nodes: list[Node]
    removed_nodes: list[Node]
    changed_nodes: list[Node]
    added_edges: list[Edge]
    removed_edges: list[Edge]


@dataclass
class AuditReport:
    """Audit report for a knowledge graph."""
    total_nodes: int
    total_edges: int
    orphaned_nodes: list[Node]
    stale_nodes: list[Node]
    last_compiled: datetime


class MarkdownParser:
    """Parse Obsidian-compatible markdown into structured graph data."""

    WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
    FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

    def parse(self, content: str, source: str = "") -> ParsedResult:
        """Parse markdown content into nodes and edges."""
        if not content.strip():
            return ParsedResult(nodes=[], edges=[])

        # Extract frontmatter and body
        frontmatter: dict = {}
        body = content
        fm_match = self.FRONTMATTER_RE.match(content)
        if fm_match:
            import yaml
            try:
                fm_data = yaml.safe_load(fm_match.group(1))
                # Convert date objects to strings for consistency
                if isinstance(fm_data, dict):
                    frontmatter = {
                        k: v.isoformat() if hasattr(v, 'isoformat') else v
                        for k, v in fm_data.items()
                    }
            except Exception:
                frontmatter = {}
            body = fm_match.group(2)

        # Extract title (first heading)
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if not title_match:
            return ParsedResult(nodes=[], edges=[])

        title = title_match.group(1).strip()
        node_id = self._make_id(title, source)

        # Build node properties
        props = dict(frontmatter)
        props["source"] = source
        props["content"] = body.strip()

        now = datetime.utcnow().isoformat()
        source_node = Node(
            id=node_id,
            label=title,
            properties=props,
            created_at=now,
            updated_at=now,
        )

        nodes = [source_node]
        edges = []

        # Extract wikilinks
        for match in self.WIKILINK_RE.finditer(body):
            target_label = match.group(1).strip()
            target_id = self._make_id(target_label, None)
            target_node = Node(
                id=target_id,
                label=target_label,
                properties={},
                created_at=now,
                updated_at=now,
            )
            nodes.append(target_node)
            edges.append(Edge(
                source=node_id,
                target=target_id,
                relationship="links_to",
                properties={},
            ))

        return ParsedResult(nodes=nodes, edges=edges)

    def merge(self, results: list[ParsedResult]) -> ParsedResult:
        """Merge multiple parsed results, deduplicating nodes by label."""
        node_map: dict[str, Node] = {}
        edge_map: dict[tuple, Edge] = {}

        for result in results:
            for node in result.nodes:
                if node.label in node_map:
                    # Merge properties, keep the more recent one
                    existing = node_map[node.label]
                    if node.updated_at > existing.updated_at:
                        node.properties.update(existing.properties)
                        node_map[node.label] = node
                else:
                    node_map[node.label] = node
            for edge in result.edges:
                key = (edge.source, edge.target, edge.relationship)
                if key not in edge_map:
                    edge_map[key] = edge

        return ParsedResult(
            nodes=list(node_map.values()),
            edges=list(edge_map.values()),
        )

    @staticmethod
    def _make_id(label: str, source: str | None) -> str:
        """Create a stable ID from a label."""
        import hashlib
        slug = label.lower().replace(" ", "-")
        if source:
            slug = f"{slug}-{hashlib.md5(source.encode()).hexdigest()[:8]}"
        return f"node-{slug}"


class GraphMaterializer:
    """Materialize parsed data into a queryable graph store."""

    def __init__(self, store_path: str = ":memory:") -> None:
        self.store_path = store_path
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.store_path)
            self._create_tables()
        return self._conn

    def _create_tables(self) -> None:
        conn = self._conn
        if conn is None:
            return
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                properties TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                relationship TEXT,
                properties TEXT,
                PRIMARY KEY (source, target, relationship)
            )
        """)
        conn.commit()

    def materialize(self, nodes: list[Node], edges: list[Edge]) -> KnowledgeGraph:
        """Store nodes and edges, return the materialized graph."""
        conn = self._get_conn()

        for node in nodes:
            import json
            conn.execute(
                "INSERT OR REPLACE INTO nodes (id, label, properties, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (node.id, node.label, json.dumps(node.properties), node.created_at, node.updated_at),
            )

        for edge in edges:
            import json
            conn.execute(
                "INSERT OR REPLACE INTO edges (source, target, relationship, properties) VALUES (?, ?, ?, ?)",
                (edge.source, edge.target, edge.relationship, json.dumps(edge.properties)),
            )

        conn.commit()
        self._nodes = nodes
        self._edges = edges

        return KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            compiled_at=datetime.utcnow().isoformat(),
            source_path="",
        )

    def load(self) -> KnowledgeGraph:
        """Load a graph from the SQLite store.
        Returns an empty graph if store is :memory: or does not exist.
        """
        import json
        if self.store_path == ":memory:":
            return KnowledgeGraph(nodes=[], edges=[], compiled_at="", source_path="")
        conn = self._get_conn()
        try:
            nodes_row = conn.execute("SELECT id, label, properties, created_at, updated_at FROM nodes").fetchall()
            edges_row = conn.execute("SELECT source, target, relationship, properties FROM edges").fetchall()
        except sqlite3.OperationalError:
            return KnowledgeGraph(nodes=[], edges=[], compiled_at="", source_path="")
        nodes = [
            Node(id=r[0], label=r[1], properties=json.loads(r[2]) if r[2] else {},
                 created_at=r[3], updated_at=r[4])
            for r in nodes_row
        ]
        edges = [
            Edge(source=r[0], target=r[1], relationship=r[2],
                 properties=json.loads(r[3]) if r[3] else {})
            for r in edges_row
        ]
        return KnowledgeGraph(nodes=nodes, edges=edges, compiled_at="", source_path=str(self.store_path))

    def query(self, graph: KnowledgeGraph, query_text: str, transitive: bool = False) -> list[Node]:
        """Query nodes by label or content match."""
        results = []
        query_lower = query_text.lower()

        for node in graph.nodes:
            if query_lower in node.label.lower():
                results.append(node)
                continue
            content = node.properties.get("content", "")
            if query_lower in content.lower():
                results.append(node)

        if transitive:
            # Find all nodes reachable via edges
            visited = {n.id for n in results}
            frontier = list(results)
            while frontier:
                current = frontier.pop()
                for edge in graph.edges:
                    if edge.source == current.id and edge.target not in visited:
                        target_node = next((n for n in graph.nodes if n.id == edge.target), None)
                        if target_node:
                            results.append(target_node)
                            visited.add(target_node.id)
                            frontier.append(target_node)

        return results

    def diff(self, old_graph: KnowledgeGraph, new_graph: KnowledgeGraph) -> Diff:
        """Compute the difference between two graph states."""
        old_nodes = {n.id: n for n in old_graph.nodes}
        new_nodes = {n.id: n for n in new_graph.nodes}

        added = [n for nid, n in new_nodes.items() if nid not in old_nodes]
        removed = [n for nid, n in old_nodes.items() if nid not in new_nodes]
        changed = [
            n for nid, n in new_nodes.items()
            if nid in old_nodes and n.properties != old_nodes[nid].properties
        ]

        old_edges = {(e.source, e.target, e.relationship) for e in old_graph.edges}
        new_edges = {(e.source, e.target, e.relationship) for e in new_graph.edges}

        added_edges = [
            e for e in new_graph.edges
            if (e.source, e.target, e.relationship) not in old_edges
        ]
        removed_edges = [
            e for e in old_graph.edges
            if (e.source, e.target, e.relationship) not in new_edges
        ]

        return Diff(
            added_nodes=added,
            removed_nodes=removed,
            changed_nodes=changed,
            added_edges=added_edges,
            removed_edges=removed_edges,
        )

    def audit(self, graph: KnowledgeGraph) -> AuditReport:
        """Audit the graph for orphaned nodes and other issues."""
        connected_ids = set()
        for edge in graph.edges:
            connected_ids.add(edge.source)
            connected_ids.add(edge.target)

        orphaned = [n for n in graph.nodes if n.id not in connected_ids]

        # Stale nodes: not updated in 30 days
        stale = []
        now = datetime.utcnow()
        for node in graph.nodes:
            try:
                updated = datetime.fromisoformat(node.updated_at)
                if (now - updated).days > 30:
                    stale.append(node)
            except (ValueError, TypeError):
                pass

        return AuditReport(
            total_nodes=len(graph.nodes),
            total_edges=len(graph.edges),
            orphaned_nodes=orphaned,
            stale_nodes=stale,
            last_compiled=datetime.utcnow(),
        )


class CompileTimeKnowledge:
    """Orchestrate the compile-time knowledge graph lifecycle."""

    def __init__(self, store_path: str = ":memory:") -> None:
        self.store_path = store_path
        self.parser = MarkdownParser()
        self.materializer = GraphMaterializer(store_path=store_path)

    def compile(self, source: Path) -> KnowledgeGraph:
        """Compile all markdown files in a source directory into a knowledge graph."""
        results = []

        if source.is_dir():
            for md_file in sorted(source.rglob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                result = self.parser.parse(content, str(md_file))
                results.append(result)
        elif source.is_file() and source.suffix == ".md":
            content = source.read_text(encoding="utf-8")
            results.append(self.parser.parse(content, str(source)))

        merged = self.parser.merge(results)
        graph = self.materializer.materialize(nodes=merged.nodes, edges=merged.edges)
        graph.source_path = str(source)
        return graph

    def load(self, source: Path | None = None) -> KnowledgeGraph:
        """Load a graph from the SQLite store, or compile from source if not found."""
        return self.materializer.load()

    def query(self, graph: KnowledgeGraph, query_text: str) -> list[Node]:
        """Query the knowledge graph."""
        return self.materializer.query(graph, query_text)

    def diff(self, old_graph: KnowledgeGraph, new_graph: KnowledgeGraph) -> Diff:
        """Diff two graph states."""
        return self.materializer.diff(old_graph, new_graph)

    def audit(self, graph: KnowledgeGraph) -> AuditReport:
        """Audit the knowledge graph."""
        return self.materializer.audit(graph)
