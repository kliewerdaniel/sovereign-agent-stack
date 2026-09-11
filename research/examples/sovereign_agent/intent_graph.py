"""Sovereign Intent Graph.

A planning and reasoning artifact that represents joint intent
without becoming an authority root.

Central distinction:
    PROPOSAL ≠ INTENT GRAPH ≠ GOVERNANCE ≠ AUTHORIZATION ≠ CAPABILITY ≠ EXECUTION

The intent graph organizes consequences but does not authorize them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class IntentRelation(str, Enum):
    """Relations between proposed actions in an intent graph."""
    INDEPENDENT = "independent"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    CONFLICTING = "conflicting"
    COMPLEMENTARY = "complementary"
    RESOURCE_DEPENDENT = "resource_dependent"
    EPISTEMIC_DEPENDENT = "epistemic_dependent"
    TEMPORALLY_DEPENDENT = "temporally_dependent"
    GOVERNANCE_DEPENDENT = "governance_dependent"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"


class ProposalStatus(str, Enum):
    """Status of a proposal within the intent graph."""
    PROPOSED = "proposed"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    INVALIDATED = "invalidated"


class ConflictType(str, Enum):
    """Types of conflicts between proposals."""
    RESOURCE = "resource"
    EPISTEMIC = "epistemic"
    TEMPORAL = "temporal"
    GOVERNANCE = "governance"
    DOMAIN = "domain"
    ASSUMPTION = "assumption"
    NONE = "none"


@dataclass(frozen=True)
class ActionProposal:
    """A single proposed action within an intent graph."""
    proposal_id: str
    agent_id: str
    timestamp: str
    action: str
    resource: str
    arguments: dict[str, Any]
    proposition: str
    evidence_dependencies: list[str] = field(default_factory=list)
    resource_dependencies: list[str] = field(default_factory=list)
    governance_dependencies: list[str] = field(default_factory=list)
    temporal_constraints: dict[str, Any] = field(default_factory=dict)
    authority_requirements: list[str] = field(default_factory=list)
    prerequisite_actions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    requested_consequence: str = ""
    authorization_ref: Optional[str] = None
    capability_ref: Optional[str] = None
    status: str = ProposalStatus.PROPOSED.value
    provenance: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IntentEdge:
    """An edge representing a relationship between two proposals."""
    edge_id: str
    source_id: str
    target_id: str
    relation: IntentRelation
    condition: Optional[str] = None
    description: str = ""
    conflict_type: Optional[ConflictType] = None
    resolution: Optional[str] = None


@dataclass(frozen=True)
class ExecutionNode:
    """A node in an execution partial order."""
    node_id: str
    proposal_id: str
    execution_phase: int = 0
    predecessors: list[str] = field(default_factory=list)
    successors: list[str] = field(default_factory=list)
    parallel_group: Optional[int] = None


@dataclass
class IntentGraph:
    """A graph representing joint intent between autonomous proposals."""
    graph_id: str
    timestamp: str
    proposals: dict[str, ActionProposal] = field(default_factory=dict)
    edges: list[IntentEdge] = field(default_factory=list)
    execution_order: list[ExecutionNode] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_proposal(self, proposal: ActionProposal) -> None:
        """Add a proposal to the intent graph."""
        self.proposals[proposal.proposal_id] = proposal

    def add_edge(self, edge: IntentEdge) -> None:
        """Add an edge between proposals."""
        self.edges.append(edge)

    def get_proposals_by_agent(self, agent_id: str) -> list[ActionProposal]:
        """Get all proposals from a specific agent."""
        return [p for p in self.proposals.values() if p.agent_id == agent_id]

    def get_relations(self, proposal_id: str) -> list[IntentEdge]:
        """Get all relations involving a specific proposal."""
        return [e for e in self.edges if e.source_id == proposal_id or e.target_id == proposal_id]

    def get_dependencies(self, proposal_id: str) -> list[str]:
        """Get all proposals that the given proposal depends on."""
        deps = []
        for edge in self.edges:
            if edge.target_id == proposal_id and edge.relation in (
                IntentRelation.SEQUENTIAL,
                IntentRelation.CONDITIONAL,
                IntentRelation.EPISTEMIC_DEPENDENT,
                IntentRelation.RESOURCE_DEPENDENT,
                IntentRelation.GOVERNANCE_DEPENDENT,
                IntentRelation.TEMPORALLY_DEPENDENT,
            ):
                deps.append(edge.source_id)
        return deps

    def get_conflicts(self, proposal_id: str) -> list[str]:
        """Get all proposals that conflict with the given proposal."""
        conflicts = []
        for edge in self.edges:
            if edge.relation == IntentRelation.CONFLICTING:
                if edge.source_id == proposal_id:
                    conflicts.append(edge.target_id)
                elif edge.target_id == proposal_id:
                    conflicts.append(edge.source_id)
        return conflicts

    def get_independent_proposals(self) -> list[str]:
        """Get proposals with no dependencies."""
        dependent = set()
        for edge in self.edges:
            if edge.relation in (
                IntentRelation.SEQUENTIAL,
                IntentRelation.CONDITIONAL,
                IntentRelation.EPISTEMIC_DEPENDENT,
                IntentRelation.RESOURCE_DEPENDENT,
            ):
                dependent.add(edge.target_id)
        return [pid for pid in self.proposals if pid not in dependent]

    def get_sequential_chains(self) -> list[list[str]]:
        """Get all sequential chains in the graph."""
        chains = []
        visited = set()

        def follow_chain(pid: str, current_chain: list[str]) -> None:
            current_chain.append(pid)
            visited.add(pid)
            for edge in self.edges:
                if edge.source_id == pid and edge.relation == IntentRelation.SEQUENTIAL:
                    if edge.target_id not in visited:
                        follow_chain(edge.target_id, current_chain)

        for pid in self.get_independent_proposals():
            chain = []
            follow_chain(pid, chain)
            if chain:
                chains.append(chain)

        return chains

    def detect_conflicts(self) -> list[dict[str, Any]]:
        """Detect conflicts between proposals."""
        conflicts = []

        # Check for resource conflicts
        resource_map: dict[str, list[str]] = {}
        for pid, proposal in self.proposals.items():
            resource = proposal.resource
            if resource not in resource_map:
                resource_map[resource] = []
            resource_map[resource].append(pid)

        for resource, pids in resource_map.items():
            if len(pids) > 1:
                # Multiple proposals target the same resource
                for i in range(len(pids)):
                    for j in range(i + 1, len(pids)):
                        p1 = self.proposals[pids[i]]
                        p2 = self.proposals[pids[j]]
                        if self._proposals_conflict(p1, p2):
                            conflicts.append({
                                "type": ConflictType.RESOURCE.value,
                                "proposals": [pids[i], pids[j]],
                                "resource": resource,
                                "description": f"Both proposals target resource: {resource}",
                            })

        # Check for assumption conflicts
        for pid, proposal in self.proposals.items():
            for assumption in proposal.assumptions:
                for other_pid, other_proposal in self.proposals.items():
                    if other_pid != pid:
                        # Check if other proposal's postconditions violate this assumption
                        for postcondition in other_proposal.postconditions:
                            if self._assumption_violated(assumption, postcondition):
                                conflicts.append({
                                    "type": ConflictType.ASSUMPTION.value,
                                    "proposals": [pid, other_pid],
                                    "assumption": assumption,
                                    "violated_by": postcondition,
                                    "description": f"Assumption '{assumption}' violated by postcondition '{postcondition}'",
                                })

        self.conflicts = conflicts
        return conflicts

    def _proposals_conflict(self, p1: ActionProposal, p2: ActionProposal) -> bool:
        """Determine if two proposals conflict."""
        # Conflicting actions on same resource
        conflicting_actions = [
            ("replace", "disable"),
            ("replace", "remove"),
            ("enable", "disable"),
            ("add", "remove"),
        ]
        for a1, a2 in conflicting_actions:
            if (p1.action == a1 and p2.action == a2) or (p1.action == a2 and p2.action == a1):
                return True
        return False

    def _assumption_violated(self, assumption: str, postcondition: str) -> bool:
        """Check if a postcondition violates an assumption."""
        # Simple heuristic: if postcondition negates assumption
        negations = {
            "provider_active": "provider_inactive",
            "feature_enabled": "feature_disabled",
            "dependency_present": "dependency_removed",
        }
        for key, negation in negations.items():
            if key in assumption and negation in postcondition:
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "graph_id": self.graph_id,
            "timestamp": self.timestamp,
            "proposal_count": len(self.proposals),
            "edge_count": len(self.edges),
            "conflict_count": len(self.conflicts),
            "proposals": {
                pid: {
                    "proposal_id": p.proposal_id,
                    "agent_id": p.agent_id,
                    "action": p.action,
                    "resource": p.resource,
                    "proposition": p.proposition,
                    "status": p.status,
                    "evidence_dependencies": p.evidence_dependencies,
                    "resource_dependencies": p.resource_dependencies,
                    "prerequisite_actions": p.prerequisite_actions,
                    "postconditions": p.postconditions,
                    "assumptions": p.assumptions,
                }
                for pid, p in self.proposals.items()
            },
            "edges": [
                {
                    "edge_id": e.edge_id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation.value,
                    "condition": e.condition,
                    "description": e.description,
                    "conflict_type": e.conflict_type.value if e.conflict_type else None,
                }
                for e in self.edges
            ],
            "conflicts": self.conflicts,
            "independent_proposals": self.get_independent_proposals(),
            "sequential_chains": self.get_sequential_chains(),
        }


def build_intent_graph(agent_proposals: list[ActionProposal]) -> IntentGraph:
    """Build an intent graph from a list of agent proposals."""
    graph = IntentGraph(
        graph_id=f"intent_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.utcnow().isoformat(),
    )

    for proposal in agent_proposals:
        graph.add_proposal(proposal)

    # Auto-detect relations
    _detect_sequential_dependencies(graph)
    _detect_resource_conflicts(graph)
    _detect_epistemic_dependencies(graph)

    # Detect conflicts
    graph.detect_conflicts()

    return graph


def _detect_sequential_dependencies(graph: IntentGraph) -> None:
    """Detect sequential dependencies between proposals."""
    proposals = list(graph.proposals.values())

    for i, p1 in enumerate(proposals):
        for j, p2 in enumerate(proposals):
            if i != j:
                # Check if p1's postconditions satisfy p2's prerequisites
                for postcondition in p1.postconditions:
                    for prerequisite in p2.prerequisite_actions:
                        if postcondition in prerequisite or prerequisite in postcondition:
                            edge = IntentEdge(
                                edge_id=f"edge_{uuid.uuid4().hex[:12]}",
                                source_id=p1.proposal_id,
                                target_id=p2.proposal_id,
                                relation=IntentRelation.SEQUENTIAL,
                                description=f"{p1.proposal_id} must complete before {p2.proposal_id}",
                            )
                            graph.add_edge(edge)


def _detect_resource_conflicts(graph: IntentGraph) -> None:
    """Detect resource conflicts between proposals."""
    proposals = list(graph.proposals.values())

    for i, p1 in enumerate(proposals):
        for j, p2 in enumerate(proposals):
            if i < j and p1.resource == p2.resource:
                if graph._proposals_conflict(p1, p2):
                    edge = IntentEdge(
                        edge_id=f"edge_{uuid.uuid4().hex[:12]}",
                        source_id=p1.proposal_id,
                        target_id=p2.proposal_id,
                        relation=IntentRelation.CONFLICTING,
                        conflict_type=ConflictType.RESOURCE,
                        description=f"Resource conflict on {p1.resource}",
                    )
                    graph.add_edge(edge)


def _detect_epistemic_dependencies(graph: IntentGraph) -> None:
    """Detect epistemic dependencies between proposals."""
    proposals = list(graph.proposals.values())

    for i, p1 in enumerate(proposals):
        for j, p2 in enumerate(proposals):
            if i != j:
                # Check if p1's evidence is a dependency for p2
                for evidence in p1.evidence_dependencies:
                    if evidence in p2.evidence_dependencies:
                        edge = IntentEdge(
                            edge_id=f"edge_{uuid.uuid4().hex[:12]}",
                            source_id=p1.proposal_id,
                            target_id=p2.proposal_id,
                            relation=IntentRelation.EPISTEMIC_DEPENDENT,
                            description=f"Shared epistemic dependency: {evidence}",
                        )
                        graph.add_edge(edge)
