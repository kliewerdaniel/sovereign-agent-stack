"""Dependency Epistemic Status.

Tracks the epistemic status of each dependency in an authorization's dependency graph.

Central distinction:
    DECLARED DEPENDENCY ≠ OBSERVED DEPENDENCY ≠ INFERRED DEPENDENCY ≠ VALIDATED DEPENDENCY ≠ AUTHORITATIVE DEPENDENCY

A dependency is not merely present or absent. It has an epistemic history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DependencyDiscoveryMethod(str, Enum):
    """How a dependency was discovered."""
    DIRECT_DECLARATION = "direct_declaration"
    STATIC_ANALYSIS = "static_analysis"
    RUNTIME_TRACE = "runtime_trace"
    CONTROLLED_INTERVENTION = "controlled_intervention"
    COUNTERFACTUAL_TEST = "counterfactual_test"
    DOCUMENTATION = "documentation"
    MODEL_HYPOTHESIS = "model_hypothesis"
    EXPERIMENT = "experiment"
    GOVERNANCE_APPROVAL = "governance_approval"
    POST_AUTHORIZATION_DISCOVERY = "post_authorization_discovery"


class DependencyEpistemicStatus(str, Enum):
    """Epistemic status of a dependency."""
    DECLARED = "declared"
    OBSERVED = "observed"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"
    VALIDATED = "validated"
    REJECTED = "rejected"
    CONTRADICTED = "contradicted"
    STALE = "stale"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


class DependencyScope(str, Enum):
    """Scope of a dependency's validity."""
    PROPOSITION_SCOPED = "proposition_scoped"
    TEMPORALLY_BOUNDED = "temporally_bounded"
    ENVIRONMENT_BOUNDED = "environment_bounded"
    DOMAIN_BOUNDED = "domain_bounded"
    ACTOR_SCOPED = "actor_scoped"
    RESOURCE_SCOPED = "resource_scoped"
    UNCONSTRAINED = "unconstrained"


@dataclass(frozen=True)
class DependencyAttestation:
    """An attestation of a dependency's validity."""
    attestation_id: str
    timestamp: str
    attestor: str
    method: DependencyDiscoveryMethod
    status: DependencyEpistemicStatus
    confidence: float = 0.0
    provenance: list[str] = field(default_factory=list)
    scope: list[DependencyScope] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyEpistemicState:
    """Epistemic state of a single dependency."""
    dependency_id: str
    target_id: str
    current_status: DependencyEpistemicStatus
    discovery_method: DependencyDiscoveryMethod
    attestations: list[DependencyAttestation] = field(default_factory=list)
    scope: list[DependencyScope] = field(default_factory=list)
    discovered_at: str = ""
    last_validated: str = ""
    contradictions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_attestation(self, attestation: DependencyAttestation) -> None:
        """Add an attestation to this dependency."""
        self.attestations.append(attestation)
        self.last_validated = attestation.timestamp
        # Update status based on attestation
        if attestation.status == DependencyEpistemicStatus.REJECTED:
            self.current_status = DependencyEpistemicStatus.REJECTED
        elif attestation.status == DependencyEpistemicStatus.CONTRADICTED:
            self.current_status = DependencyEpistemicStatus.CONTRADICTED
        elif attestation.status == DependencyEpistemicStatus.VALIDATED:
            self.current_status = DependencyEpistemicStatus.VALIDATED

    def is_validated(self) -> bool:
        """Check if the dependency has been validated."""
        if self.current_status == DependencyEpistemicStatus.VALIDATED:
            return True
        return any(
            a.status == DependencyEpistemicStatus.VALIDATED
            for a in self.attestations
        )

    def is_rejected(self) -> bool:
        """Check if the dependency has been rejected."""
        return self.current_status == DependencyEpistemicStatus.REJECTED

    def is_stale(self) -> bool:
        """Check if the dependency is stale."""
        return self.current_status == DependencyEpistemicStatus.STALE

    def has_contradiction(self) -> bool:
        """Check if the dependency has been contradicted."""
        return len(self.contradictions) > 0

    def is_proposition_scoped(self) -> bool:
        """Check if the dependency is scoped to a proposition."""
        return DependencyScope.PROPOSITION_SCOPED in self.scope

    def is_temporally_bounded(self) -> bool:
        """Check if the dependency is temporally bounded."""
        return DependencyScope.TEMPORALLY_BOUNDED in self.scope

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependency_id": self.dependency_id,
            "target_id": self.target_id,
            "current_status": self.current_status.value,
            "discovery_method": self.discovery_method.value,
            "attestation_count": len(self.attestations),
            "scope": [s.value for s in self.scope],
            "discovered_at": self.discovered_at,
            "last_validated": self.last_validated,
            "is_validated": self.is_validated(),
            "is_rejected": self.is_rejected(),
            "is_stale": self.is_stale(),
            "has_contradiction": self.has_contradiction(),
        }


@dataclass
class DependencyGraphEpistemicState:
    """Epistemic state of an entire dependency graph."""
    graph_id: str
    authorization_id: str
    dependency_states: dict[str, DependencyEpistemicState] = field(default_factory=dict)
    overall_completeness: float = 0.0
    overall_confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_dependency_state(self, state: DependencyEpistemicState) -> None:
        """Add a dependency state."""
        self.dependency_states[state.dependency_id] = state

    def get_state(self, dependency_id: str) -> Optional[DependencyEpistemicState]:
        """Get the epistemic state of a specific dependency."""
        return self.dependency_states.get(dependency_id)

    def get_validated_dependencies(self) -> list[DependencyEpistemicState]:
        """Get all validated dependencies."""
        return [s for s in self.dependency_states.values() if s.is_validated()]

    def get_rejected_dependencies(self) -> list[DependencyEpistemicState]:
        """Get all rejected dependencies."""
        return [s for s in self.dependency_states.values() if s.is_rejected()]

    def get_stale_dependencies(self) -> list[DependencyEpistemicState]:
        """Get all stale dependencies."""
        return [s for s in self.dependency_states.values() if s.is_stale()]

    def get_unvalidated_dependencies(self) -> list[DependencyEpistemicState]:
        """Get all dependencies that have not been validated."""
        return [s for s in self.dependency_states.values() if not s.is_validated()]

    def compute_completeness(self) -> float:
        """Compute overall completeness of the dependency graph."""
        if not self.dependency_states:
            return 0.0
        validated = len(self.get_validated_dependencies())
        total = len(self.dependency_states)
        self.overall_completeness = validated / total
        return self.overall_completeness

    def has_unvalidated_dependencies(self) -> bool:
        """Check if there are unvalidated dependencies."""
        return len(self.get_unvalidated_dependencies()) > 0

    def has_rejected_dependencies(self) -> bool:
        """Check if there are rejected dependencies."""
        return len(self.get_rejected_dependencies()) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "graph_id": self.graph_id,
            "authorization_id": self.authorization_id,
            "dependency_count": len(self.dependency_states),
            "validated_count": len(self.get_validated_dependencies()),
            "rejected_count": len(self.get_rejected_dependencies()),
            "stale_count": len(self.get_stale_dependencies()),
            "unvalidated_count": len(self.get_unvalidated_dependencies()),
            "overall_completeness": self.overall_completeness,
            "overall_confidence": self.overall_confidence,
            "has_unvalidated": self.has_unvalidated_dependencies(),
            "has_rejected": self.has_rejected_dependencies(),
        }


def create_attestation(
    attestor: str,
    method: DependencyDiscoveryMethod,
    status: DependencyEpistemicStatus,
    confidence: float = 0.0,
    provenance: list[str] | None = None,
    scope: list[DependencyScope] | None = None,
    evidence: list[str] | None = None,
) -> DependencyAttestation:
    """Create a dependency attestation."""
    return DependencyAttestation(
        attestation_id=f"attestation_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.utcnow().isoformat(),
        attestor=attestor,
        method=method,
        status=status,
        confidence=confidence,
        provenance=provenance or [],
        scope=scope or [],
        evidence=evidence or [],
    )
