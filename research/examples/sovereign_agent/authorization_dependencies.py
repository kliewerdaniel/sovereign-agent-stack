"""Authorization Dependency Graph.

An explicit provenance-backed representation of what justifies an authorization.

Central question:
    What makes an authorization remain justified after the epistemic state
    that produced it changes?

Key distinctions:
    AUTHORIZATION VALIDITY ≠ EPISTEMIC VALIDITY ≠ WORLD STATE VALIDITY

But they may have explicit dependency relationships.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DependencyType(str, Enum):
    """Types of authorization dependencies."""
    EVIDENCE = "evidence"
    PROPOSITION = "proposition"
    EPISTEMIC_STATE = "epistemic_state"
    EXPERIMENT = "experiment"
    RECOMMENDATION = "governance_policy"
    GOVERNANCE_POLICY = "governance_policy"
    ACTOR_IDENTITY = "actor_identity"
    DELEGATION = "delegation"
    RESOURCE_IDENTITY = "resource_identity"
    ENVIRONMENT = "environment"
    TEMPORAL_INTERVAL = "temporal_interval"
    PROVENANCE = "provenance"
    CAPABILITY_CONSTRAINT = "capability_constraint"


class DependencyStrength(str, Enum):
    """Strength of a dependency."""
    DIRECT = "direct"
    TRANSITIVE = "transitive"
    UNKNOWN = "unknown"


class AuthorizationStatus(str, Enum):
    """Status of an authorization."""
    VALID = "valid"
    PRESERVED = "preserved"
    SUSPENDED = "suspended"
    REQUIRES_REEVALUATION = "requires_reevaluation"
    INVALIDATED = "invalidated"
    INCONCLUSIVE = "inconclusive"


class StalenessType(str, Enum):
    """Types of authorization staleness."""
    AUTHORITY_STALE = "authority_stale"
    EPISTEMICALLY_STALE = "epistemically_stale"
    RESOURCE_STALE = "resource_stale"
    GOVERNANCE_STALE = "governance_stale"
    TEMPORALLY_STALE = "temporally_stale"
    PROVENANCE_STALE = "provenance_stale"


class IntersectionResult(str, Enum):
    """Result of dependency intersection evaluation."""
    DIRECT_DEPENDENCY = "direct_dependency"
    TRANSITIVE_DEPENDENCY = "transitive_dependency"
    UNRELATED = "unrelated"
    UNKNOWN_DEPENDENCY = "unknown_dependency"
    CONTRADICTORY_DEPENDENCY = "contradictory_dependency"
    DEPENDENCY_CHANGED = "dependency_changed"


@dataclass(frozen=True)
class AuthorizationDependency:
    """A single dependency of an authorization."""
    dependency_id: str
    dependency_type: DependencyType
    target_id: str
    description: str
    strength: DependencyStrength = DependencyStrength.DIRECT
    timestamp: str = ""
    provenance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationDependencyGraph:
    """Provenance-backed dependency graph for an authorization."""
    authorization_id: str
    timestamp: str
    dependencies: list[AuthorizationDependency] = field(default_factory=list)
    status: AuthorizationStatus = AuthorizationStatus.VALID
    staleness: set[StalenessType] = field(default_factory=set)
    provenance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_dependency(self, dependency: AuthorizationDependency) -> None:
        """Add a dependency to this authorization."""
        self.dependencies.append(dependency)

    def get_dependencies_by_type(self, dep_type: DependencyType) -> list[AuthorizationDependency]:
        """Get all dependencies of a specific type."""
        return [d for d in self.dependencies if d.dependency_type == dep_type]

    def get_direct_dependencies(self) -> list[AuthorizationDependency]:
        """Get all direct dependencies."""
        return [d for d in self.dependencies if d.strength == DependencyStrength.DIRECT]

    def get_transitive_dependencies(self) -> list[AuthorizationDependency]:
        """Get all transitive dependencies."""
        return [d for d in self.dependencies if d.strength == DependencyStrength.TRANSITIVE]

    def has_dependency_on(self, target_id: str) -> bool:
        """Check if this authorization has a dependency on a specific target."""
        return any(d.target_id == target_id for d in self.dependencies)

    def has_direct_dependency_on(self, target_id: str) -> bool:
        """Check for a direct dependency on a specific target."""
        return any(
            d.target_id == target_id and d.strength == DependencyStrength.DIRECT
            for d in self.dependencies
        )

    def get_dependency_chain(self, target_id: str) -> list[AuthorizationDependency]:
        """Get the full dependency chain for a target."""
        chain = []
        visited = set()

        def traverse(tid: str) -> None:
            for dep in self.dependencies:
                if dep.target_id == tid and dep.dependency_id not in visited:
                    visited.add(dep.dependency_id)
                    chain.append(dep)
                    # Recursively find transitive dependencies
                    if dep.strength == DependencyStrength.TRANSITIVE:
                        traverse(dep.target_id)

        traverse(target_id)
        return chain

    def mark_stale(self, staleness: StalenessType) -> None:
        """Mark the authorization as stale in a specific dimension."""
        self.staleness.add(staleness)

    def is_stale(self) -> bool:
        """Check if the authorization is stale in any dimension."""
        return len(self.staleness) > 0

    def is_epistemically_stale(self) -> bool:
        """Check if the authorization is epistemically stale."""
        return StalenessType.EPISTEMICALLY_STALE in self.staleness

    def is_temporally_stale(self) -> bool:
        """Check if the authorization is temporally stale."""
        return StalenessType.TEMPORALLY_STALE in self.staleness

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "authorization_id": self.authorization_id,
            "timestamp": self.timestamp,
            "dependency_count": len(self.dependencies),
            "status": self.status.value,
            "staleness": [s.value for s in self.staleness],
            "dependencies": [
                {
                    "dependency_id": d.dependency_id,
                    "dependency_type": d.dependency_type.value,
                    "target_id": d.target_id,
                    "description": d.description,
                    "strength": d.strength.value,
                    "provenance": d.provenance,
                }
                for d in self.dependencies
            ],
        }


def build_authorization_dependency_graph(
    authorization_id: str,
    evidence_ids: list[str],
    proposition_id: str,
    epistemic_state_id: str,
    experiment_id: str,
    recommendation_id: str,
    governance_policy_id: str,
    resource_id: str,
    temporal_interval: str,
    provenance: list[str],
) -> AuthorizationDependencyGraph:
    """Build a complete authorization dependency graph."""
    graph = AuthorizationDependencyGraph(
        authorization_id=authorization_id,
        timestamp=datetime.utcnow().isoformat(),
        provenance=provenance,
    )

    # Add evidence dependencies
    for evidence_id in evidence_ids:
        graph.add_dependency(AuthorizationDependency(
            dependency_id=f"dep_evidence_{uuid.uuid4().hex[:8]}",
            dependency_type=DependencyType.EVIDENCE,
            target_id=evidence_id,
            description=f"Evidence {evidence_id} supports this authorization",
            strength=DependencyStrength.DIRECT,
            provenance=provenance,
        ))

    # Add proposition dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_proposition_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.PROPOSITION,
        target_id=proposition_id,
        description=f"Proposition {proposition_id} justifies this authorization",
        strength=DependencyStrength.DIRECT,
        provenance=provenance,
    ))

    # Add epistemic state dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_epistemic_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.EPISTEMIC_STATE,
        target_id=epistemic_state_id,
        description=f"Epistemic state {epistemic_state_id} at authorization time",
        strength=DependencyStrength.DIRECT,
        provenance=provenance,
    ))

    # Add experiment dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_experiment_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.EXPERIMENT,
        target_id=experiment_id,
        description=f"Experiment {experiment_id} produced supporting evidence",
        strength=DependencyStrength.TRANSITIVE,
        provenance=provenance,
    ))

    # Add governance policy dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_governance_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.GOVERNANCE_POLICY,
        target_id=governance_policy_id,
        description=f"Governance policy {governance_policy_id} was in effect",
        strength=DependencyStrength.DIRECT,
        provenance=provenance,
    ))

    # Add resource dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_resource_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.RESOURCE_IDENTITY,
        target_id=resource_id,
        description=f"Resource {resource_id} was the authorization target",
        strength=DependencyStrength.DIRECT,
        provenance=provenance,
    ))

    # Add temporal dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_temporal_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.TEMPORAL_INTERVAL,
        target_id=temporal_interval,
        description=f"Temporal interval {temporal_interval} for authorization validity",
        strength=DependencyStrength.DIRECT,
        provenance=provenance,
    ))

    # Add recommendation dependency
    graph.add_dependency(AuthorizationDependency(
        dependency_id=f"dep_recommendation_{uuid.uuid4().hex[:8]}",
        dependency_type=DependencyType.RECOMMENDATION,
        target_id=recommendation_id,
        description=f"Recommendation {recommendation_id} led to governance decision",
        strength=DependencyStrength.TRANSITIVE,
        provenance=provenance,
    ))

    return graph
