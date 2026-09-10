"""Phase 5.5: Scoped Impact Propagation.

Implements and validates the smallest principled runtime semantics combining
Phase 4.5 (semantic impact propagation) and Phase 5 (scope preservation).

Architectural law under validation:
  FRONTIER = DEPENDENCY_INTERSECTION + SEMANTIC_IMPACT_PROPAGATION + SCOPE_PRESERVATION

This module does NOT create a generic graph engine. It uses existing types:
- DependencyType, DependencyStrength (authorization_dependencies.py)
- CompletenessScope, CompletenessStatus, IntersectionStatus (dependency_completeness.py)
- RevalidationFrontier, RevalidationRequirement (temporal_completeness.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    DependencyStrength,
    DependencyType,
)
from examples.sovereign_agent.dependency_completeness import (
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.temporal_completeness import (
    RevalidationFrontier,
    RevalidationRequirement,
    TemporalCompletenessEngine,
)


class PropagationAction(str, Enum):
    """What happens when impact reaches an artifact."""
    INCLUDE = "include"           # Artifact enters frontier
    EXCLUDE = "exclude"           # Artifact does not enter frontier
    REQUIRE_EVALUATION = "require_evaluation"  # Needs epistemic check
    UNKNOWN = "unknown"           # Cannot determine


class SemanticEdgeType(str, Enum):
    """Types of semantic edges in the impact propagation graph.
    
    Each edge type has different propagation semantics.
    """
    EVIDENCE_TO_PROPOSITION = "evidence_to_proposition"
    PROPOSITION_TO_EPISTEMIC = "proposition_to_epistemic"
    EPISTEMIC_TO_AUTHORIZATION = "epistemic_to_authorization"
    AUTHORIZATION_TO_CONSEQUENCE = "authorization_to_consequence"
    GOVERNANCE_TO_AUTHORIZATION = "governance_to_authorization"
    OBSERVABILITY_REFERENCE = "observability_reference"
    AUDIT_REFERENCE = "audit_reference"
    PROVENANCE_REFERENCE = "provenance_reference"


# Propagation rules for each edge type
EDGE_PROPAGATION_RULES: dict[SemanticEdgeType, PropagationAction] = {
    SemanticEdgeType.EVIDENCE_TO_PROPOSITION: PropagationAction.INCLUDE,
    SemanticEdgeType.PROPOSITION_TO_EPISTEMIC: PropagationAction.INCLUDE,
    SemanticEdgeType.EPISTEMIC_TO_AUTHORIZATION: PropagationAction.REQUIRE_EVALUATION,
    SemanticEdgeType.AUTHORIZATION_TO_CONSEQUENCE: PropagationAction.REQUIRE_EVALUATION,
    SemanticEdgeType.GOVERNANCE_TO_AUTHORIZATION: PropagationAction.REQUIRE_EVALUATION,
    SemanticEdgeType.OBSERVABILITY_REFERENCE: PropagationAction.EXCLUDE,
    SemanticEdgeType.AUDIT_REFERENCE: PropagationAction.EXCLUDE,
    SemanticEdgeType.PROVENANCE_REFERENCE: PropagationAction.EXCLUDE,
}


@dataclass(frozen=True)
class ScopedFrontierMember:
    """An artifact in the revalidation frontier with its scope conditions.
    
    Each member carries the scope under which it is affected, preserving
    conditional semantics.
    """
    artifact_id: str
    artifact_type: str  # "dependency", "proposition", "authorization", etc.
    scope: CompletenessScope
    conditions: list[str] = field(default_factory=list)
    propagation_path: list[str] = field(default_factory=list)  # Path from changed dep
    notes: str = ""


@dataclass(frozen=True)
class ScopedFrontier:
    """A revalidation frontier that preserves scope information.
    
    Unlike the flat RevalidationFrontier, this preserves the scope conditions
    under which each artifact is affected.
    """
    frontier_id: str
    world_change_id: str
    authorization_id: str
    timestamp: str
    members: list[ScopedFrontierMember] = field(default_factory=list)
    scope: Optional[CompletenessScope] = None
    completeness_status: CompletenessStatus = CompletenessStatus.UNKNOWN
    intersection_status: IntersectionStatus = IntersectionStatus.CANNOT_DETERMINE
    revalidation_requirement: RevalidationRequirement = RevalidationRequirement.NOTHING
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def get_member_ids(self) -> set[str]:
        """Get all artifact IDs in the frontier."""
        return {m.artifact_id for m in self.members}

    def get_members_by_type(self, artifact_type: str) -> list[ScopedFrontierMember]:
        """Get members of a specific type."""
        return [m for m in self.members if m.artifact_type == artifact_type]

    def is_empty(self) -> bool:
        """Check if the frontier is empty."""
        return len(self.members) == 0

    def is_authoritative(self) -> bool:
        """A scoped frontier is NEVER authoritative."""
        return False


@dataclass
class ScopedImpactPropagationEngine:
    """Engine for scoped semantic impact propagation.
    
    Computes revalidation frontiers that preserve scope conditions and
    propagate through typed semantic relationships.
    
    Reuses:
    - CompletenessEngine for completeness assessment
    - DependencyType/DependencyStrength for edge semantics
    - CompletenessScope for scope matching
    - IntersectionStatus for frontier confidence
    """

    completeness_engine: CompletenessEngine = field(default_factory=CompletenessEngine)
    temporal_engine: TemporalCompletenessEngine = field(default_factory=TemporalCompletenessEngine)

    def compute_scoped_frontier(
        self,
        world_change: AuthorityDriftEvent,
        authorization_id: str,
        dependency_graph: AuthorizationDependencyGraph,
        proposition_graph: dict[str, list[str]],
        authorization_graph: dict[str, list[str]],
        scope: CompletenessScope,
        actual_dependencies: list[str] | None = None,
    ) -> ScopedFrontier:
        """Compute a scoped revalidation frontier.
        
        This is the core operation: given a world change, determine which
        artifacts are semantically affected, respecting scope boundaries.
        
        Args:
            world_change: The change event
            authorization_id: The authorization being evaluated
            dependency_graph: The dependency graph (protocol knowledge)
            proposition_graph: Proposition → dependencies mapping
            authorization_graph: Authorization → propositions mapping
            scope: The scope in which to evaluate
            actual_dependencies: Ground truth dependencies (for completeness assessment only)
        
        Returns:
            A ScopedFrontier with scope-preserved members
        """
        # Step 1: Assess completeness
        declared_deps = [d.target_id for d in dependency_graph.dependencies]
        if actual_dependencies is not None:
            completeness = self.completeness_engine.assess_completeness(
                authorization_id, dependency_graph.authorization_id,
                declared_deps, actual_dependencies, scope, CompletenessMethod.MULTI_SOURCE,
            )
        else:
            completeness = None

        # Step 2: Find changed dependencies
        changed_deps = self._extract_changed_dependencies(world_change)

        # Step 3: Find affected dependencies (intersection with known graph)
        affected_deps = self._find_affected_dependencies(changed_deps, declared_deps)

        # Step 4: Check intersection status
        intersection = IntersectionStatus.CANNOT_DETERMINE
        if completeness is not None and affected_deps:
            intersection = self.completeness_engine.check_intersection_status(
                affected_deps[0], declared_deps, completeness,
            )

        # Step 5: Propagate through semantic chain with scope preservation
        members: list[ScopedFrontierMember] = []

        # Add affected dependencies
        for dep_id in affected_deps:
            members.append(ScopedFrontierMember(
                artifact_id=dep_id,
                artifact_type="dependency",
                scope=scope,
                propagation_path=[dep_id],
            ))

        # Propagate to propositions
        affected_props = self._propagate_to_propositions(
            affected_deps, proposition_graph, scope,
        )
        members.extend(affected_props)

        # Propagate to authorizations
        affected_auths = self._propagate_to_authorizations(
            [m.artifact_id for m in affected_props], authorization_graph, scope,
        )
        members.extend(affected_auths)

        # Step 6: Determine revalidation requirement
        requirement = self._determine_requirement(members, completeness, intersection)

        # Step 7: Build scoped frontier
        return ScopedFrontier(
            frontier_id=f"scoped_{uuid.uuid4().hex[:12]}",
            world_change_id=world_change.event_id,
            authorization_id=authorization_id,
            timestamp=datetime.utcnow().isoformat(),
            members=members,
            scope=scope,
            completeness_status=completeness.overall_status if completeness else CompletenessStatus.UNKNOWN,
            intersection_status=intersection,
            revalidation_requirement=requirement,
            provenance_chain=["scoped_impact_propagation"],
            limitations=self._identify_limitations(completeness, intersection),
        )

    def _extract_changed_dependencies(self, world_change: AuthorityDriftEvent) -> list[str]:
        """Extract changed dependency IDs from a world change.
        
        Looks at the keys in previous_state/new_state that differ between them.
        The keys are dependency IDs, not the values.
        """
        changed = []
        
        # Find keys that changed between previous and new state
        if world_change.previous_state and world_change.new_state:
            for key in world_change.previous_state:
                if key in world_change.new_state:
                    if world_change.previous_state[key] != world_change.new_state[key]:
                        changed.append(key)
                else:
                    changed.append(key)
            for key in world_change.new_state:
                if key not in world_change.previous_state:
                    changed.append(key)
        elif world_change.previous_state:
            changed.extend(world_change.previous_state.keys())
        elif world_change.new_state:
            changed.extend(world_change.new_state.keys())
        
        return list(set(changed))

    def _find_affected_dependencies(
        self,
        changed_deps: list[str],
        declared_deps: list[str],
    ) -> list[str]:
        """Find dependencies that are both changed and in the declared graph."""
        return [dep for dep in changed_deps if dep in declared_deps]

    def _propagate_to_propositions(
        self,
        affected_deps: list[str],
        proposition_graph: dict[str, list[str]],
        scope: CompletenessScope,
        dependency_graph: AuthorizationDependencyGraph | None = None,
    ) -> list[ScopedFrontierMember]:
        """Propagate impact to propositions with scope checking and edge type awareness."""
        members = []
        for prop_id, deps in proposition_graph.items():
            # Check if any affected dependency is in this proposition's dependencies
            if any(dep in affected_deps for dep in deps):
                # Check scope match
                if self._scope_matches(prop_id, scope):
                    # Check edge type (observability/audit edges don't propagate)
                    if self._edge_propagates(deps, dependency_graph):
                        members.append(ScopedFrontierMember(
                            artifact_id=prop_id,
                            artifact_type="proposition",
                            scope=scope,
                            propagation_path=affected_deps + [prop_id],
                        ))
        return members

    def _edge_propagates(
        self,
        deps: list[str],
        dependency_graph: AuthorizationDependencyGraph | None,
    ) -> bool:
        """Check if impact propagates through the edges to these dependencies.
        
        Observability/audit/provenance edges should NOT propagate impact.
        """
        if dependency_graph is None:
            return True  # No graph to check, assume propagation OK
        
        for dep in deps:
            # Find the dependency in the graph
            for auth_dep in dependency_graph.dependencies:
                if auth_dep.target_id == dep:
                    # Check if this is an edge type that doesn't propagate
                    if auth_dep.dependency_type in (
                        DependencyType.PROVENANCE,
                        DependencyType.GOVERNANCE_POLICY,
                    ):
                        return False
                    if auth_dep.strength == DependencyStrength.TRANSITIVE:
                        # Transitive dependencies may not propagate automatically
                        # Only propagate if it's a semantic transitive dependency
                        if auth_dep.dependency_type in (
                            DependencyType.PROVENANCE,
                            DependencyType.GOVERNANCE_POLICY,
                        ):
                            return False
        
        return True

    def _propagate_to_authorizations(
        self,
        affected_props: list[str],
        authorization_graph: dict[str, list[str]],
        scope: CompletenessScope,
    ) -> list[ScopedFrontierMember]:
        """Propagate impact to authorizations with scope checking."""
        members = []
        for auth_id, props in authorization_graph.items():
            if any(prop in affected_props for prop in props):
                if self._scope_matches(auth_id, scope):
                    members.append(ScopedFrontierMember(
                        artifact_id=auth_id,
                        artifact_type="authorization",
                        scope=scope,
                        propagation_path=affected_props + [auth_id],
                    ))
        return members

    def _scope_matches(self, artifact_id: str, scope: CompletenessScope) -> bool:
        """Check if an artifact is within the given scope.
        
        For now, check if the scope has any "unknown" values.
        If the scope is unknown, return False (cannot determine match).
        If the scope is partially specified, check what we can.
        """
        # Check for unknown scope dimensions
        if scope.environment == "unknown":
            return False
        if scope.domain == "unknown":
            return False
        if scope.actor_id == "unknown":
            return False
        if scope.resource_id == "unknown":
            return False
        if scope.temporal_interval == "unknown":
            return False
        
        # For known scopes, assume match (artifact-specific scope checking TODO)
        return True

    def _is_unknown_scope(self, scope: CompletenessScope) -> bool:
        """Check if the scope has unknown dimensions."""
        return (
            scope.environment == "unknown"
            or scope.domain == "unknown"
            or scope.actor_id == "unknown"
            or scope.resource_id == "unknown"
            or scope.temporal_interval == "unknown"
        )

    def _determine_requirement(
        self,
        members: list[ScopedFrontierMember],
        completeness: Any,
        intersection: IntersectionStatus,
    ) -> RevalidationRequirement:
        """Determine the revalidation requirement."""
        if not members:
            if completeness and completeness.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
                return RevalidationRequirement.FULL_REVALIDATION
            return RevalidationRequirement.NOTHING

        has_auth = any(m.artifact_type == "authorization" for m in members)
        has_prop = any(m.artifact_type == "proposition" for m in members)
        has_dep = any(m.artifact_type == "dependency" for m in members)

        if has_auth:
            return RevalidationRequirement.AUTHORIZATION
        elif has_prop:
            return RevalidationRequirement.PROPOSITION
        elif has_dep:
            return RevalidationRequirement.DEPENDENCY_ONLY

        return RevalidationRequirement.NOTHING

    def _identify_limitations(
        self,
        completeness: Any,
        intersection: IntersectionStatus,
    ) -> list[str]:
        """Identify limitations of the frontier assessment."""
        limitations = []
        if completeness is None:
            limitations.append("Completeness unknown")
        elif completeness.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
            limitations.append("Dependency graph incomplete")
        if intersection == IntersectionStatus.CANNOT_DETERMINE:
            limitations.append("Intersection cannot be determined")
        return limitations


def create_scoped_proposition_graph(
    propositions: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Create a proposition graph from a mapping of proposition → dependencies."""
    return propositions


def create_scoped_authorization_graph(
    authorizations: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Create an authorization graph from a mapping of authorization → propositions."""
    return authorizations
