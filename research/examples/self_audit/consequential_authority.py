"""Consequential Authority Graph.

Integrates static topology, runtime behavior, consequence observation,
epistemic evidence, authority reconstruction, boundary adjudication,
and governance into a unified model.

Central question:
    WHAT ACTORS, COMPONENTS, PROCESSES, CREDENTIALS, SUBSYSTEMS,
    AND PROTOCOL PATHS CAN ACTUALLY CAUSE CONSEQUENCES IN A REAL SYSTEM,
    UNDER WHAT CONDITIONS, AND WITH WHAT RECONSTRUCTIBLE AUTHORITY?

Central thesis:
    The important property of a sovereign system is not that every action
    is controlled by a central authority. It is that every consequential
    action has an identifiable authority boundary whose provenance, scope,
    conditions, and governance can be independently reconstructed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class EdgeType(str, Enum):
    """Types of edges in the consequential authority graph."""
    CALL = "call"
    DEPENDENCY = "dependency"
    CONSEQUENCE = "consequence"
    AUTHORITY = "authority"
    DELEGATION = "delegation"
    TRUST = "trust"
    GOVERNANCE = "governance"
    CAPABILITY = "capability"
    PROVENANCE = "provenance"
    TEMPORAL = "temporal"
    ENVIRONMENT = "environment"
    CREDENTIAL = "credential"
    BOUNDARY = "boundary"


class ReachabilityType(str, Enum):
    """Types of reachability - NOT interchangeable."""
    STATIC_REACHABILITY = "static_reachability"
    RUNTIME_REACHABILITY = "runtime_reachability"
    CONSEQUENTIAL_REACHABILITY = "consequential_reachability"
    AUTHORIZED_REACHABILITY = "authorized_reachability"


class ConsequenceType(str, Enum):
    """Types of consequences."""
    PAYMENT = "payment"
    REFUND = "refund"
    SETTLEMENT = "settlement"
    NOTIFICATION = "notification"
    LEDGER_MUTATION = "ledger_mutation"
    CREDENTIAL_ACCESS = "credential_access"
    IDENTITY_MUTATION = "identity_mutation"
    DATA_EXFILTRATION = "data_exfiltration"
    SERVICE_DEGRADATION = "service_degradation"
    CONFIGURATION_MUTATION = "configuration_mutation"
    EXTERNAL_EFFECT = "external_effect"
    INTERNAL_EFFECT = "internal_effect"


class AuthorityDisposition(str, Enum):
    """Authority disposition of a path."""
    AUTHORIZED = "authorized"
    DELEGATED = "delegated"
    TRUSTED = "trusted"
    LEGACY = "legacy"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"


class EpistemicState(str, Enum):
    """Epistemic state of a claim."""
    OBSERVED = "observed"
    INFERRED = "inferred"
    SUPPORTED = "supported"
    INCONCLUSIVE = "inconclusive"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Authority Conditions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityCondition:
    """A condition under which authority applies."""

    condition_id: str
    condition_type: str  # feature_flag, environment, actor, time, etc.
    description: str
    value: Any
    negated: bool = False

    def to_dict(self) -> dict:
        return {
            "condition_id": self.condition_id,
            "condition_type": self.condition_type,
            "description": self.description,
            "value": str(self.value),
            "negated": self.negated,
        }


@dataclass(frozen=True)
class ConditionalAuthority:
    """Authority that applies only under certain conditions."""

    authority_id: str
    authority_type: str
    conditions: list[AuthorityCondition]
    authority_basis: str
    provenance_id: Optional[str] = None

    @property
    def is_unconditional(self) -> bool:
        return len(self.conditions) == 0

    def to_dict(self) -> dict:
        return {
            "authority_id": self.authority_id,
            "authority_type": self.authority_type,
            "conditions": [c.to_dict() for c in self.conditions],
            "authority_basis": self.authority_basis,
            "provenance_id": self.provenance_id,
            "is_unconditional": self.is_unconditional,
        }


# ---------------------------------------------------------------------------
# Consequential Authority
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsequentialAuthority:
    """Records who can cause what consequences under which authority."""

    authority_id: str
    actor: str
    component: str
    operation: str
    resource: str
    consequence_type: ConsequenceType
    authority_owner: Optional[str] = None
    authority_basis: Optional[str] = None
    authorization_id: Optional[str] = None
    capability_id: Optional[str] = None
    delegation_id: Optional[str] = None
    policy_id: Optional[str] = None
    domain: Optional[str] = None
    lineage: list[str] = field(default_factory=list)
    temporal_scope: str = "unbounded"
    runtime_path: list[str] = field(default_factory=list)
    static_hypothesis_id: Optional[str] = None
    evidence: list[str] = field(default_factory=list)
    provenance_id: Optional[str] = None
    limitations: list[str] = field(default_factory=list)
    conditions: list[AuthorityCondition] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "authority_id": self.authority_id,
            "actor": self.actor,
            "component": self.component,
            "operation": self.operation,
            "resource": self.resource,
            "consequence_type": self.consequence_type.value,
            "authority_owner": self.authority_owner,
            "authority_basis": self.authority_basis,
            "authorization_id": self.authorization_id,
            "capability_id": self.capability_id,
            "delegation_id": self.delegation_id,
            "policy_id": self.policy_id,
            "domain": self.domain,
            "lineage": self.lineage,
            "temporal_scope": self.temporal_scope,
            "runtime_path": self.runtime_path,
            "static_hypothesis_id": self.static_hypothesis_id,
            "evidence": self.evidence,
            "provenance_id": self.provenance_id,
            "limitations": self.limitations,
            "conditions": [c.to_dict() for c in self.conditions],
        }


# ---------------------------------------------------------------------------
# Authority Path
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityPath:
    """A path through the system with authority semantics at each edge."""

    path_id: str
    edges: list["PathEdge"]
    source: str
    target: str
    consequence_type: ConsequenceType
    authority_disposition: AuthorityDisposition
    conditions: list[AuthorityCondition] = field(default_factory=list)
    authority_gaps: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "edges": [e.to_dict() for e in self.edges],
            "source": self.source,
            "target": self.target,
            "consequence_type": self.consequence_type.value,
            "authority_disposition": self.authority_disposition.value,
            "conditions": [c.to_dict() for c in self.conditions],
            "authority_gaps": self.authority_gaps,
            "provenance_chain": self.provenance_chain,
        }


@dataclass(frozen=True)
class PathEdge:
    """An edge in an authority path."""

    edge_id: str
    source: str
    target: str
    edge_type: EdgeType
    authority_basis: Optional[str] = None
    authorization_id: Optional[str] = None
    delegation_id: Optional[str] = None
    trust_id: Optional[str] = None
    credential_id: Optional[str] = None
    capability_id: Optional[str] = None
    conditions: list[AuthorityCondition] = field(default_factory=list)
    epistemic_state: EpistemicState = EpistemicState.INCONCLUSIVE
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.value,
            "authority_basis": self.authority_basis,
            "authorization_id": self.authorization_id,
            "delegation_id": self.delegation_id,
            "trust_id": self.trust_id,
            "credential_id": self.credential_id,
            "capability_id": self.capability_id,
            "conditions": [c.to_dict() for c in self.conditions],
            "epistemic_state": self.epistemic_state.value,
            "evidence": self.evidence,
            "limitations": self.limitations,
        }


# ---------------------------------------------------------------------------
# Authority Cut Set
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityCutSet:
    """A minimal set of boundaries whose control prevents a consequential path."""

    cut_set_id: str
    target_consequence: str
    boundaries: list[str]
    cut_type: str  # "actor", "credential", "capability", "delegation"
    authority_basis: str
    conditions: list[AuthorityCondition] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cut_set_id": self.cut_set_id,
            "target_consequence": self.target_consequence,
            "boundaries": self.boundaries,
            "cut_type": self.cut_type,
            "authority_basis": self.authority_basis,
            "conditions": [c.to_dict() for c in self.conditions],
            "provenance_chain": self.provenance_chain,
            "limitations": self.limitations,
        }


# ---------------------------------------------------------------------------
# Consequential Authority Graph
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GraphEdge:
    """An edge in the consequential authority graph."""

    edge_id: str
    source: str
    target: str
    edge_type: EdgeType
    authority_basis: Optional[str] = None
    authorization_id: Optional[str] = None
    delegation_id: Optional[str] = None
    trust_id: Optional[str] = None
    governance_policy_id: Optional[str] = None
    capability_id: Optional[str] = None
    provenance_id: Optional[str] = None
    credential_id: Optional[str] = None
    temporal_scope: str = "unbounded"
    environment: Optional[str] = None
    conditions: list[AuthorityCondition] = field(default_factory=list)
    epistemic_state: EpistemicState = EpistemicState.INCONCLUSIVE
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.value,
            "authority_basis": self.authority_basis,
            "authorization_id": self.authorization_id,
            "delegation_id": self.delegation_id,
            "trust_id": self.trust_id,
            "governance_policy_id": self.governance_policy_id,
            "capability_id": self.capability_id,
            "provenance_id": self.provenance_id,
            "credential_id": self.credential_id,
            "temporal_scope": self.temporal_scope,
            "environment": self.environment,
            "conditions": [c.to_dict() for c in self.conditions],
            "epistemic_state": self.epistemic_state.value,
            "evidence": self.evidence,
            "limitations": self.limitations,
        }


@dataclass(frozen=True)
class GraphNode:
    """A node in the consequential authority graph."""

    node_id: str
    node_type: str  # "actor", "component", "credential", "resource", "consequence"
    name: str
    description: str = ""
    authority_owner: Optional[str] = None
    trust_basis: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "description": self.description,
            "authority_owner": self.authority_owner,
            "trust_basis": self.trust_basis,
            "metadata": self.metadata,
        }


class ConsequentialAuthorityGraph:
    """The Consequential Authority Graph.

    Integrates:
    - Static topology (dependency edges)
    - Runtime behavior (runtime edges)
    - Consequence observation (consequence edges)
    - Epistemic evidence (epistemic states on edges)
    - Authority reconstruction (authority edges)
    - Boundary adjudication (boundary edges)
    - Governance (governance edges)
    """

    def __init__(self):
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.paths: list[AuthorityPath] = []
        self.cut_sets: list[AuthorityCutSet] = []
        self.consequential_authorities: list[ConsequentialAuthority] = []

    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self.nodes.append(node)

    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)

    def add_path(self, path: AuthorityPath):
        """Add an authority path."""
        self.paths.append(path)

    def add_cut_set(self, cut_set: AuthorityCutSet):
        """Add an authority cut set."""
        self.cut_sets.append(cut_set)

    def add_consequential_authority(self, authority: ConsequentialAuthority):
        """Add a consequential authority record."""
        self.consequential_authorities.append(authority)

    # --- Query methods ---

    def get_edges_by_type(self, edge_type: EdgeType) -> list[GraphEdge]:
        """Get edges by type."""
        return [e for e in self.edges if e.edge_type == edge_type]

    def get_edges_by_source(self, source: str) -> list[GraphEdge]:
        """Get edges by source."""
        return [e for e in self.edges if e.source == source]

    def get_edges_by_target(self, target: str) -> list[GraphEdge]:
        """Get edges by target."""
        return [e for e in self.edges if e.target == target]

    def get_edges_by_authority_basis(self, basis: str) -> list[GraphEdge]:
        """Get edges by authority basis."""
        return [e for e in self.edges if e.authority_basis == basis]

    def get_consequence_edges(self) -> list[GraphEdge]:
        """Get all consequence edges."""
        return self.get_edges_by_type(EdgeType.CONSEQUENCE)

    def get_authority_edges(self) -> list[GraphEdge]:
        """Get all authority edges."""
        return self.get_edges_by_type(EdgeType.AUTHORITY)

    def get_delegation_edges(self) -> list[GraphEdge]:
        """Get all delegation edges."""
        return self.get_edges_by_type(EdgeType.DELEGATION)

    def get_credential_edges(self) -> list[GraphEdge]:
        """Get all credential edges."""
        return self.get_edges_by_type(EdgeType.CREDENTIAL)

    def get_boundary_edges(self) -> list[GraphEdge]:
        """Get all boundary edges."""
        return self.get_edges_by_type(EdgeType.BOUNDARY)

    def get_paths_by_consequence(self, consequence_type: ConsequenceType) -> list[AuthorityPath]:
        """Get paths by consequence type."""
        return [p for p in self.paths if p.consequence_type == consequence_type]

    def get_paths_by_disposition(self, disposition: AuthorityDisposition) -> list[AuthorityPath]:
        """Get paths by authority disposition."""
        return [p for p in self.paths if p.authority_disposition == disposition]

    def get_cut_sets_for_target(self, target: str) -> list[AuthorityCutSet]:
        """Get cut sets for a target consequence."""
        return [c for c in self.cut_sets if c.target_consequence == target]

    def get_authority_for_actor(self, actor: str) -> list[ConsequentialAuthority]:
        """Get consequential authority for an actor."""
        return [a for a in self.consequential_authorities if a.actor == actor]

    def get_authority_for_resource(self, resource: str) -> list[ConsequentialAuthority]:
        """Get consequential authority for a resource."""
        return [a for a in self.consequential_authorities if a.resource == resource]

    # --- Serialization ---

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "total_paths": len(self.paths),
                "total_cut_sets": len(self.cut_sets),
                "total_consequential_authorities": len(self.consequential_authorities),
            },
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "paths": [p.to_dict() for p in self.paths],
            "cut_sets": [c.to_dict() for c in self.cut_sets],
            "consequential_authorities": [a.to_dict() for a in self.consequential_authorities],
            "summary": {
                "edge_types": self._count_edge_types(),
                "consequence_types": self._count_consequence_types(),
                "authority_dispositions": self._count_dispositions(),
                "epistemic_states": self._count_epistemic_states(),
            },
        }

    def _count_edge_types(self) -> dict:
        counts = {}
        for e in self.edges:
            t = e.edge_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _count_consequence_types(self) -> dict:
        counts = {}
        for a in self.consequential_authorities:
            t = a.consequence_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _count_dispositions(self) -> dict:
        counts = {}
        for p in self.paths:
            d = p.authority_disposition.value
            counts[d] = counts.get(d, 0) + 1
        return counts

    def _count_epistemic_states(self) -> dict:
        counts = {}
        for e in self.edges:
            s = e.epistemic_state.value
            counts[s] = counts.get(s, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Invariant Checks
# ---------------------------------------------------------------------------


class ConsequentialAuthorityInvariants:
    """Invariant checks for the Consequential Authority Graph."""

    @staticmethod
    def check_dependency_not_authority(graph: ConsequentialAuthorityGraph) -> dict:
        """DEPENDENCY ≠ AUTHORITY."""
        issues = []
        for edge in graph.get_edges_by_type(EdgeType.DEPENDENCY):
            if edge.authority_basis and edge.edge_type == EdgeType.DEPENDENCY:
                issues.append(
                    f"Dependency edge {edge.edge_id} has authority_basis: {edge.authority_basis}"
                )
        return {
            "invariant": "DEPENDENCY_NOT_AUTHORITY",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_reachability_not_authority(graph: ConsequentialAuthorityGraph) -> dict:
        """REACHABILITY ≠ AUTHORITY."""
        issues = []
        for edge in graph.get_edges_by_type(EdgeType.CALL):
            if edge.authority_basis and not edge.authorization_id:
                issues.append(
                    f"Call edge {edge.edge_id} has authority_basis without authorization"
                )
        return {
            "invariant": "REACHABILITY_NOT_AUTHORITY",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_consequence_not_authorization(graph: ConsequentialAuthorityGraph) -> dict:
        """CONSEQUENCE ≠ AUTHORIZATION."""
        issues = []
        for edge in graph.get_edges_by_type(EdgeType.CONSEQUENCE):
            if edge.authorization_id:
                issues.append(
                    f"Consequence edge {edge.edge_id} has authorization_id"
                )
        return {
            "invariant": "CONSEQUENCE_NOT_AUTHORIZATION",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_credential_not_authorization(graph: ConsequentialAuthorityGraph) -> dict:
        """CREDENTIAL POSSESSION ≠ AUTHORIZATION."""
        issues = []
        for edge in graph.get_edges_by_type(EdgeType.CREDENTIAL):
            if edge.authority_basis == "protocol_derivation":
                issues.append(
                    f"Credential edge {edge.edge_id} claims protocol authority"
                )
        return {
            "invariant": "CREDENTIAL_NOT_AUTHORIZATION",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_runtime_not_governance(graph: ConsequentialAuthorityGraph) -> dict:
        """RUNTIME EXECUTION ≠ GOVERNANCE APPROVAL."""
        issues = []
        for edge in graph.get_edges_by_type(EdgeType.CALL):
            if edge.governance_policy_id and edge.epistemic_state == EpistemicState.OBSERVED:
                issues.append(
                    f"Runtime edge {edge.edge_id} has governance_policy_id from observation alone"
                )
        return {
            "invariant": "RUNTIME_NOT_GOVERNANCE",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_trust_not_authority(graph: ConsequentialAuthorityGraph) -> dict:
        """TRUST ≠ AUTHORITY."""
        issues = []
        for edge in graph.get_edges_by_type(EdgeType.TRUST):
            if edge.edge_type == EdgeType.TRUST and edge.authority_basis == "protocol_derivation":
                issues.append(
                    f"Trust edge {edge.edge_id} claims protocol derivation"
                )
        return {
            "invariant": "TRUST_NOT_AUTHORITY",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_consequential_reachable_not_authoritative(graph: ConsequentialAuthorityGraph) -> dict:
        """CONSEQUENTIALLY REACHABLE DOES NOT IMPLY AUTHORITATIVELY REACHABLE."""
        issues = []
        for path in graph.paths:
            if path.consequence_type and path.authority_disposition == AuthorityDisposition.UNKNOWN:
                if not path.authority_gaps:
                    issues.append(
                        f"Path {path.path_id} has unknown disposition but no authority_gaps documented"
                    )
        return {
            "invariant": "CONSEQUENTIAL_REACHABLE_NOT_AUTHORITATIVE",
            "held": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def check_all(graph: ConsequentialAuthorityGraph) -> list[dict]:
        """Run all invariant checks."""
        return [
            ConsequentialAuthorityInvariants.check_dependency_not_authority(graph),
            ConsequentialAuthorityInvariants.check_reachability_not_authority(graph),
            ConsequentialAuthorityInvariants.check_consequence_not_authorization(graph),
            ConsequentialAuthorityInvariants.check_credential_not_authorization(graph),
            ConsequentialAuthorityInvariants.check_runtime_not_governance(graph),
            ConsequentialAuthorityInvariants.check_trust_not_authority(graph),
            ConsequentialAuthorityInvariants.check_consequential_reachable_not_authoritative(graph),
        ]
