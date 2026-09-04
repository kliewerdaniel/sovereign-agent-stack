"""Layer 6: Long-term Knowledge — Compile-time knowledge graph.

The layer that most differentiates SAS from ARGO alone.
A fact compiled once into a stable, inspectable, versionable node is an asset.
A fact re-derived at query time is a liability.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol


@dataclass
class Node:
    id: str
    label: str
    properties: dict
    created_at: str
    updated_at: str


@dataclass
class Edge:
    source: str
    target: str
    relationship: str
    properties: dict


@dataclass
class KnowledgeGraph:
    nodes: list[Node]
    edges: list[Edge]
    compiled_at: str
    source_path: str


@dataclass
class Diff:
    added_nodes: list[Node]
    removed_nodes: list[Node]
    changed_nodes: list[Node]
    added_edges: list[Edge]
    removed_edges: list[Edge]
    since: datetime


@dataclass
class AuditReport:
    total_nodes: int
    total_edges: int
    orphaned_nodes: list[Node]
    stale_nodes: list[Node]
    last_compiled: datetime


class CompileTimeKnowledge(Protocol):
    async def compile(self, source: Path) -> KnowledgeGraph: ...
    async def query(self, graph: KnowledgeGraph, query: str) -> list[Node]: ...
    async def diff(self, graph: KnowledgeGraph, since: datetime) -> Diff: ...
    async def audit(self, graph: KnowledgeGraph) -> AuditReport: ...
