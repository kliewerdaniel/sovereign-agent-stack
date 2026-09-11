"""Integration layer: Payment Dependency Auditor + Authority Topology.

Connects dependency observations to authority reconstruction.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from research.examples.self_audit.consequential_authority import (
    AuthorityCutSet,
    AuthorityDisposition,
    AuthorityPath,
    ConsequenceType,
    ConsequentialAuthority,
    ConsequentialAuthorityGraph,
    EdgeType,
    EpistemicState,
    GraphEdge,
    GraphNode,
    PathEdge,
    ReachabilityType,
)


@dataclass
class DependencyObservation:
    """A dependency observation from the auditor."""

    source: str
    target: str
    dependency_type: str
    epistemic_state: str
    evidence: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    environment: Optional[str] = None


@dataclass
class RuntimeObservation:
    """A runtime observation."""

    actor: str
    operation: str
    resource: str
    result: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AuthorityDeclaration:
    """An authority declaration."""

    declaration_id: str
    declaration_type: str
    actor: str
    operation: str
    scope: dict[str, Any]
    basis: str
    provenance_id: Optional[str] = None


class AuthorityTopologyIntegrator:
    """Integrates dependency observations with authority analysis."""

    def __init__(self):
        self.graph = ConsequentialAuthorityGraph()

    def integrate_dependencies(
        self,
        dependencies: list[DependencyObservation],
    ):
        """Integrate dependency observations into the graph."""
        for dep in dependencies:
            # Add nodes if they don't exist
            self._ensure_node(dep.source, "component", dep.source)
            self._ensure_node(dep.target, "component", dep.target)

            # Add dependency edge
            edge = GraphEdge(
                edge_id=f"dep_{uuid.uuid4().hex[:12]}",
                source=dep.source,
                target=dep.target,
                edge_type=EdgeType.DEPENDENCY,
                epistemic_state=self._map_epistemic_state(dep.epistemic_state),
                evidence=dep.evidence,
                environment=dep.environment,
                conditions=[],  # TODO: map conditions
            )
            self.graph.add_edge(edge)

    def integrate_runtime(
        self,
        observations: list[RuntimeObservation],
    ):
        """Integrate runtime observations into the graph."""
        for obs in observations:
            self._ensure_node(obs.actor, "actor", obs.actor)
            self._ensure_node(obs.resource, "resource", obs.resource)

            edge = GraphEdge(
                edge_id=f"runtime_{uuid.uuid4().hex[:12]}",
                source=obs.actor,
                target=obs.resource,
                edge_type=EdgeType.CALL,
                epistemic_state=EpistemicState.OBSERVED,
                evidence=[f"Runtime: {obs.operation} -> {obs.result}"],
            )
            self.graph.add_edge(edge)

    def integrate_authority(
        self,
        declarations: list[AuthorityDeclaration],
    ):
        """Integrate authority declarations into the graph."""
        for decl in declarations:
            edge = GraphEdge(
                edge_id=f"auth_{uuid.uuid4().hex[:12]}",
                source=decl.actor,
                target=decl.scope.get("resource", "unknown"),
                edge_type=EdgeType.AUTHORITY,
                authority_basis=decl.basis,
                authorization_id=decl.declaration_id,
                epistemic_state=EpistemicState.SUPPORTED,
                evidence=[f"Declaration: {decl.declaration_type}"],
            )
            self.graph.add_edge(edge)

    def _ensure_node(self, node_id: str, node_type: str, name: str):
        """Ensure a node exists in the graph."""
        existing = [n for n in self.graph.nodes if n.node_id == node_id]
        if not existing:
            self.graph.add_node(GraphNode(
                node_id=node_id,
                node_type=node_type,
                name=name,
            ))

    def _map_epistemic_state(self, state: str) -> EpistemicState:
        """Map epistemic state string to enum."""
        mapping = {
            "observed": EpistemicState.OBSERVED,
            "inferred": EpistemicState.INFERRED,
            "supported": EpistemicState.SUPPORTED,
            "inconclusive": EpistemicState.INCONCLUSIVE,
            "rejected": EpistemicState.REJECTED,
        }
        return mapping.get(state.lower(), EpistemicState.INCONCLUSIVE)

    def get_graph(self) -> ConsequentialAuthorityGraph:
        """Get the integrated graph."""
        return self.graph
