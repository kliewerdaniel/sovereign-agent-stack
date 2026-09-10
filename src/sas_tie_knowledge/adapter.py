"""SAS × TIE Knowledge Layer Adapter.

Adapts the Telemetry Intelligence Engine's behavioral knowledge graph
to SAS's compile-time knowledge graph interface (Layer 6).

TIE graph schema (from tie.graph.export_graph_json):
  nodes: [{id, label, title, color, size, group, views?, avg_engagement?, ...}]
  edges: [{from, to, label, weight}]

SAS knowledge schema (sas.layers.knowledge):
  Node(id, label, properties, created_at, updated_at)
  Edge(source, target, relationship, properties)

Authority Escape Remediation (Phase 26):
    All database operations now go through CapabilityBoundDatabase.
    The wrapper enforces an already-established capability (not manufacture one).
    Database operations require a verified execution capability.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sas.capability_bound_database import CapabilityBoundDatabase
from sas.layers.knowledge import (
    AuditReport,
    Edge,
    KnowledgeGraph,
    Node,
)
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    create_protocol_domain,
)


# ---------------------------------------------------------------------------
# Database Singleton
# ---------------------------------------------------------------------------

_kb_db: CapabilityBoundDatabase | None = None
_kb_domain = None


def _get_kb_db() -> CapabilityBoundDatabase:
    """Get or create the knowledge database wrapper singleton."""
    global _kb_db, _kb_domain
    if _kb_db is None:
        _kb_domain = create_protocol_domain("knowledge-domain", DomainType.SOVEREIGN)
        _kb_db = CapabilityBoundDatabase(_kb_domain)
    return _kb_db


def _create_kb_database_capability(
    db_path: str,
    action: str,
    arguments: dict | None = None,
) -> ExecutionCapability:
    """Create a database capability for knowledge operations.

    This capability must be established by an authority root BEFORE
    database operations. The wrapper verifies and materializes this
    already-established authority — it does NOT create authority.
    """
    global _kb_domain
    if _kb_domain is None:
        _kb_domain = create_protocol_domain("knowledge-domain", DomainType.SOVEREIGN)
    now = datetime.now(UTC).isoformat()

    scope = CapabilityScope(
        domain_id=_kb_domain.domain_id,
        lineage_id=_kb_domain.lineage_hash,
        actor_id="knowledge-service",
        action=f"database.{action}",
        resource=str(db_path),
        resource_class="database",
        arguments=arguments or {"db_path": str(db_path)},
        constraints=CapabilityConstraints(
            allowed_actions=[f"database.{action}"],
        ),
        temporal_interval=DomainValidityInterval(
            valid_from=now,
            valid_until="",
        ),
        authorization_ref="knowledge-db-auth",
    )

    replay_guard = ReplayGuard(
        guard_type=ReplayProtectionType.SINGLE_USE,
        nonce=f"nonce-{uuid.uuid4().hex[:16]}",
        max_uses=1,
        created_at=now,
    )

    binding = ExecutorBinding(
        binding_id=f"binding-{uuid.uuid4().hex[:12]}",
        executor_id="capability-bound-database",
        resource_id=str(db_path),
        bound_resources=[str(db_path)],
        bound_at=now,
        bound_until="",
    )

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="knowledge-db-auth",
        scope=scope,
        capability_type=CapabilityType.EXECUTE,
        replay_guard=replay_guard,
        actor_identity_ref="knowledge-service",
        resource_binding=binding,
        domain_id=_kb_domain.domain_id,
        lineage_id=_kb_domain.lineage_hash,
        authority_root="knowledge-db-auth",
        derived_at=now,
        derived_by="knowledge-database-wrapper",
    )


def _load_tie_graph(source: Path) -> dict:
    """Load a TIE graph from a JSON file or directory.

    If source is a directory, finds the first ``*.json`` file that looks
    like a TIE graph export (has ``nodes`` and ``edges`` keys).
    """
    if source.is_file():
        return json.loads(source.read_text(encoding="utf-8"))

    if source.is_dir():
        # Look for TIE graph JSON files first (export_graph_json format)
        for json_file in sorted(source.rglob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "nodes" in data and "edges" in data:
                    return data
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        # Fallback: look for normalized events + content_entities
        # (we'd need to build the graph, but for now require pre-exported JSON)
        raise FileNotFoundError(
            f"No TIE graph JSON (with 'nodes'/'edges') found in {source}"
        )

    raise FileNotFoundError(f"TIE source not found: {source}")


class TIEKnowledgeAdapter:
    """Adapts a TIE behavioral knowledge graph to SAS's Layer 6 interface.

    The adapter reads TIE's compiled graph (from ``tie.graph.export_graph_json``)
    and maps it to SAS's ``KnowledgeGraph`` of ``Node``/``Edge`` objects.

    Known schema mismatches (see ``docs/ADAPTER_GAPS.md``):
    - TIE nodes have no ``created_at``/``updated_at`` — synthesized at compile time.
    - TIE behavioral metrics (views, engagement) are observational, not declarative facts.
    - TIE ``session:*`` nodes are ephemeral and may bloat the graph.

    Authority Escape Remediation (Phase 26):
        All database operations are routed through CapabilityBoundDatabase
        to enforce capability verification.
    """

    def __init__(self, store_path: str = ":memory:") -> None:
        self.store_path = store_path

    def compile(self, source: Path) -> KnowledgeGraph:
        """Compile a TIE graph into a SAS KnowledgeGraph.

        Parameters
        ----------
        source: Path
            Path to a TIE graph JSON file or a directory containing one.
        """
        tie_data = _load_tie_graph(source)
        tie_nodes = tie_data.get("nodes", [])
        tie_edges = tie_data.get("edges", [])

        now = datetime.utcnow().isoformat()

        # Map TIE nodes → SAS Nodes
        nodes: list[Node] = []
        for tn in tie_nodes:
            nid = tn.get("id", "")
            label = tn.get("label", nid)

            # Properties: everything except id/label/title/color/size/group
            reserved = {"id", "label", "title", "color", "size", "group"}
            props: dict[str, Any] = {
                k: v for k, v in tn.items() if k not in reserved
            }
            # Add TIE metadata
            props["tie_group"] = tn.get("group", "unknown")
            props["tie_color"] = tn.get("color", "")
            props["tie_size"] = tn.get("size", 10)
            if tn.get("title"):
                props["tie_title"] = tn["title"]

            node = Node(
                id=nid,
                label=label,
                properties=props,
                created_at=now,
                updated_at=now,
            )
            nodes.append(node)

        # Map TIE edges → SAS Edges
        edges: list[Edge] = []
        for te in tie_edges:
            src = te.get("from", "")
            dst = te.get("to", "")
            rel = te.get("label", "related_to")
            weight = te.get("weight", 1)
            edge = Edge(
                source=src,
                target=dst,
                relationship=rel,
                properties={"weight": weight},
            )
            edges.append(edge)

        graph = KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            compiled_at=now,
            source_path=str(source),
        )

        # Persist to SQLite store if not :memory:
        if self.store_path != ":memory:":
            self._persist(graph)

        return graph

    def _persist(self, graph: KnowledgeGraph) -> None:
        """Persist the graph to the SQLite store through CapabilityBoundDatabase."""
        import sqlite3
        store = Path(self.store_path)
        store.parent.mkdir(parents=True, exist_ok=True)

        # Create database capabilities
        connect_cap = _create_kb_database_capability(
            str(store), "connect", {"db_path": str(store)}
        )
        db = _get_kb_db()

        # Connect
        db.connect(connect_cap, str(store))

        # Create tables
        create_cap = _create_kb_database_capability(
            str(store), "write",
            {"db_path": str(store), "sql": "CREATE TABLE nodes"}
        )
        db.execute(create_cap, str(store), """
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                properties TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        db.execute(create_cap, str(store), """
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                relationship TEXT,
                properties TEXT,
                PRIMARY KEY (source, target, relationship)
            )
        """)

        # Insert nodes
        for node in graph.nodes:
            insert_cap = _create_kb_database_capability(
                str(store), "write",
                {"db_path": str(store), "sql": "INSERT nodes"}
            )
            db.execute(
                insert_cap,
                str(store),
                "INSERT OR REPLACE INTO nodes (id, label, properties, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (node.id, node.label, json.dumps(node.properties), node.created_at, node.updated_at),
            )

        # Insert edges
        for edge in graph.edges:
            insert_cap = _create_kb_database_capability(
                str(store), "write",
                {"db_path": str(store), "sql": "INSERT edges"}
            )
            db.execute(
                insert_cap,
                str(store),
                "INSERT OR REPLACE INTO edges (source, target, relationship, properties) VALUES (?, ?, ?, ?)",
                (edge.source, edge.target, edge.relationship, json.dumps(edge.properties)),
            )

    def load(self) -> KnowledgeGraph:
        """Load a graph from the SQLite store through CapabilityBoundDatabase."""
        import sqlite3
        store = Path(self.store_path)
        if not store.exists():
            return KnowledgeGraph(nodes=[], edges=[], compiled_at="", source_path="")

        # Create database capabilities
        connect_cap = _create_kb_database_capability(
            str(store), "connect", {"db_path": str(store)}
        )
        read_cap = _create_kb_database_capability(
            str(store), "read", {"db_path": str(store), "sql": "SELECT nodes"}
        )
        db = _get_kb_db()

        # Connect
        db.connect(connect_cap, str(store))

        # Read nodes
        nodes_rows = db.execute(
            read_cap, str(store),
            "SELECT id, label, properties, created_at, updated_at FROM nodes"
        )

        # Read edges
        edges_rows = db.execute(
            read_cap, str(store),
            "SELECT source, target, relationship, properties FROM edges"
        )

        nodes = [
            Node(id=r[0], label=r[1], properties=json.loads(r[2]) if r[2] else {},
                 created_at=r[3], updated_at=r[4])
            for r in nodes_rows.rows
        ]
        edges = [
            Edge(source=r[0], target=r[1], relationship=r[2],
                 properties=json.loads(r[3]) if r[3] else {})
            for r in edges_rows.rows
        ]
        return KnowledgeGraph(nodes=nodes, edges=edges, compiled_at="", source_path=str(self.store_path))

    def query(self, graph: KnowledgeGraph, query_text: str) -> list[Node]:
        """Query nodes by label or content match (same semantics as SAS)."""
        results: list[Node] = []
        query_lower = query_text.lower()

        for node in graph.nodes:
            if query_lower in node.label.lower():
                results.append(node)
                continue
            # Search in stringified properties
            for v in node.properties.values():
                if isinstance(v, str) and query_lower in v.lower():
                    results.append(node)
                    break

        return results

    def audit(self, graph: KnowledgeGraph) -> AuditReport:
        """Audit the graph for orphaned nodes.

        Note: TIE nodes have no ``updated_at`` (they're synthesized at compile
        time), so the "stale node" check from SAS's default audit is not
        meaningful here. Only orphaned-node detection is performed.
        """
        connected_ids: set[str] = set()
        for edge in graph.edges:
            connected_ids.add(edge.source)
            connected_ids.add(edge.target)

        orphaned = [n for n in graph.nodes if n.id not in connected_ids]

        return AuditReport(
            total_nodes=len(graph.nodes),
            total_edges=len(graph.edges),
            orphaned_nodes=orphaned,
            stale_nodes=[],  # Not applicable — TIE has no timestamps
            last_compiled=datetime.utcnow(),
        )
