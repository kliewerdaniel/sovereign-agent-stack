"""Provenance for Sovereign Quant — first-class artifact ancestry.

Every research conclusion traces back through:
  Conclusion → Strategy → Backtest → Dataset → Agent → Model → Policy → Provenance
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any, Optional


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def content_hash(data: dict | str | bytes) -> str:
    if isinstance(data, dict):
        raw = json.dumps(data, sort_keys=True, default=str)
        raw = raw.encode()
    elif isinstance(data, str):
        raw = data.encode()
    elif isinstance(data, bytes):
        raw = data
    else:
        raw = str(data).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class ProvenanceNode:
    """A node in the provenance graph — one artifact with full ancestry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str = "unknown"       # strategy, backtest, dataset, trade, report, etc.
    name: str = ""
    version: str = "1.0.0"
    content_hash: str = ""
    parent_ids: list[str] = field(default_factory=list)
    producer: str = "unknown"            # agent name
    model: str = "unknown"
    policy_version: str = ""
    engine_version: str = "sas-quant"
    dataset_version: str = ""
    assumptions: dict = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = content_hash(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "artifact_type": self.artifact_type,
            "name": self.name, "version": self.version,
            "content_hash": self.content_hash,
            "parent_ids": self.parent_ids, "producer": self.producer,
            "model": self.model, "policy_version": self.policy_version,
            "engine_version": self.engine_version,
            "dataset_version": self.dataset_version,
            "assumptions": self.assumptions,
            "created_at": self.created_at, "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ProvenanceNode:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ProvenanceGraph:
    """Directed acyclic graph of artifact provenance."""

    def __init__(self):
        self._nodes: dict[str, ProvenanceNode] = {}
        self._edges: list[tuple[str, str]] = []  # (child_id, parent_id)

    def add(self, node: ProvenanceNode) -> None:
        self._nodes[node.id] = node
        for pid in node.parent_ids:
            self._edges.append((node.id, pid))

    def get(self, node_id: str) -> ProvenanceNode | None:
        return self._nodes.get(node_id)

    def ancestors(self, node_id: str, max_depth: int = 50) -> list[ProvenanceNode]:
        """Walk backward from a node to all ancestors."""
        result = []
        visited: set[str] = set()
        frontier = [node_id]
        depth = {node_id: 0}
        while frontier:
            current = frontier.pop(0)
            if current in visited or depth.get(current, 0) > max_depth:
                continue
            visited.add(current)
            node = self._nodes.get(current)
            if node:
                result.append(node)
                for pid in node.parent_ids:
                    if pid not in visited:
                        depth[pid] = depth[current] + 1
                        frontier.append(pid)
        return result

    def lineage_chain(self, node_id: str) -> list[ProvenanceNode]:
        """Return the lineage chain from root to node.

        Walks backward from node to root via parent_ids, then reverses.
        """
        chain: list[ProvenanceNode] = []
        current_id = node_id
        visited: set[str] = set()
        while current_id:
            if current_id in visited:
                break
            visited.add(current_id)
            node = self._nodes.get(current_id)
            if node is None:
                break
            chain.append(node)
            if not node.parent_ids:
                break
            current_id = node.parent_ids[0]
        chain.reverse()
        return chain

    def query(self, artifact_type: str | None = None, producer: str | None = None) -> list[ProvenanceNode]:
        results = list(self._nodes.values())
        if artifact_type:
            results = [n for n in results if n.artifact_type == artifact_type]
        if producer:
            results = [n for n in results if n.producer == producer]
        return results

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": self._edges,
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }