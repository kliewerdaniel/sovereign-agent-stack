"""Epistemic Dependency Cycle Detection.

Detects circular dependencies where authorization bootstraps its own justification.

A → P → E → X → A

This is a critical adversarial experiment: can authority be self-justifying
through epistemic dependencies?
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    DependencyType,
)


class CycleType(str, Enum):
    """Types of epistemic dependency cycles."""
    NONE = "none"
    CIRCULAR_EPISTEMIC = "circular_epistemic"
    AUTHORITY_BOOTSTRAP = "authority_bootstrap"
    SELF_JUSTIFYING = "self_justifying"
    VALID_DEPENDENCY = "valid_dependency"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class CycleDetectionResult:
    """Result of cycle detection."""
    detection_id: str
    timestamp: str
    authorization_id: str
    cycle_type: CycleType
    cycle_path: list[str] = field(default_factory=list)
    description: str = ""
    is_valid: bool = True
    requires_governance_review: bool = False


@dataclass
class EpistemicCycleDetector:
    """Detects epistemic dependency cycles."""

    def detect_cycles(
        self,
        auth_graph: AuthorizationDependencyGraph,
        experiment_to_authorization: dict[str, str] | None = None,
    ) -> CycleDetectionResult:
        """Detect epistemic dependency cycles.

        Args:
            auth_graph: The authorization dependency graph to check.
            experiment_to_authorization: Mapping from experiment IDs to
                authorization IDs that permitted them.

        Returns:
            CycleDetectionResult with the type of cycle found.
        """
        if experiment_to_authorization is None:
            experiment_to_authorization = {}

        # Build adjacency list: node -> list of nodes it depends on
        # We want to find if following dependencies leads back to the authorization
        adjacency: dict[str, list[str]] = {}

        # Add dependency edges
        for dep in auth_graph.dependencies:
            if dep.target_id not in adjacency:
                adjacency[dep.target_id] = []
            # The dependency target depends on the authorization
            # But we want to trace: what does each dependency lead to?
            pass

        # Build reverse: for each dependency, what does it connect to?
        # A depends on P, P depends on E, E depends on X, X depends on A
        # We need to trace: starting from authorization, follow the chain

        # Create a mapping: dependency_type -> target_id
        dep_targets = {}
        for dep in auth_graph.dependencies:
            dep_targets[dep.dependency_type] = dep.target_id

        # Trace the chain: authorization → proposition → evidence → experiment → authorization
        chain = []
        visited = set()

        def trace_chain(node_id: str, path: list[str]) -> list[str] | None:
            """Trace the dependency chain looking for cycles."""
            if node_id in visited:
                # Found a cycle
                return path + [node_id]

            visited.add(node_id)
            path.append(node_id)

            # Check experiment → authorization mapping
            if node_id in experiment_to_authorization:
                auth_id = experiment_to_authorization[node_id]
                result = trace_chain(auth_id, path.copy())
                if result:
                    return result

            # Check if any dependency target leads back
            for dep in auth_graph.dependencies:
                if dep.target_id == node_id:
                    # This dependency is about the current node
                    # Check what this dependency's source is
                    pass

            path.pop()
            return None

        # Start tracing from the authorization
        cycle_path = trace_chain(auth_graph.authorization_id, [])

        if cycle_path and len(cycle_path) > 1:
            cycle_type = self._classify_cycle(cycle_path, auth_graph)
            return CycleDetectionResult(
                detection_id=f"cycle_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.utcnow().isoformat(),
                authorization_id=auth_graph.authorization_id,
                cycle_type=cycle_type,
                cycle_path=cycle_path,
                description=self._describe_cycle(cycle_type, cycle_path),
                is_valid=cycle_type == CycleType.VALID_DEPENDENCY,
                requires_governance_review=cycle_type in (
                    CycleType.AUTHORITY_BOOTSTRAP,
                    CycleType.SELF_JUSTIFYING,
                ),
            )

        # Also check for cycles through experiment_to_authorization
        if experiment_to_authorization:
            for exp_id, auth_id in experiment_to_authorization.items():
                if auth_id == auth_graph.authorization_id:
                    # Check if this experiment is part of the authorization's dependencies
                    for dep in auth_graph.dependencies:
                        if dep.target_id == exp_id:
                            # Found: authorization depends on experiment, experiment depends on authorization
                            cycle_path = [auth_id, exp_id, auth_id]
                            cycle_type = CycleType.AUTHORITY_BOOTSTRAP
                            return CycleDetectionResult(
                                detection_id=f"cycle_{uuid.uuid4().hex[:12]}",
                                timestamp=datetime.utcnow().isoformat(),
                                authorization_id=auth_graph.authorization_id,
                                cycle_type=cycle_type,
                                cycle_path=cycle_path,
                                description=self._describe_cycle(cycle_type, cycle_path),
                                is_valid=False,
                                requires_governance_review=True,
                            )

        return CycleDetectionResult(
            detection_id=f"cycle_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            authorization_id=auth_graph.authorization_id,
            cycle_type=CycleType.NONE,
            description="No epistemic dependency cycle detected",
            is_valid=True,
        )

    def _classify_cycle(
        self,
        cycle_path: list[str],
        auth_graph: AuthorizationDependencyGraph,
    ) -> CycleType:
        """Classify the type of cycle."""
        if len(cycle_path) < 3:
            return CycleType.VALID_DEPENDENCY

        # Check if the cycle involves authority bootstrap
        # (authorization creates the conditions for its own justification)
        has_experiment = any(
            dep.dependency_type == DependencyType.EXPERIMENT
            for dep in auth_graph.dependencies
        )
        has_evidence = any(
            dep.dependency_type == DependencyType.EVIDENCE
            for dep in auth_graph.dependencies
        )
        has_proposition = any(
            dep.dependency_type == DependencyType.PROPOSITION
            for dep in auth_graph.dependencies
        )

        if has_experiment and has_evidence and has_proposition:
            # A → P → E → X → A pattern
            return CycleType.AUTHORITY_BOOTSTRAP

        if has_evidence and has_proposition:
            return CycleType.CIRCULAR_EPISTEMIC

        return CycleType.VALID_DEPENDENCY

    def _describe_cycle(
        self,
        cycle_type: CycleType,
        cycle_path: list[str],
    ) -> str:
        """Create a human-readable description of the cycle."""
        path_str = " → ".join(cycle_path)
        return f"{cycle_type.value}: {path_str}"


def detect_epistemic_cycles(
    auth_graph: AuthorizationDependencyGraph,
    experiment_to_authorization: dict[str, str] | None = None,
) -> CycleDetectionResult:
    """Convenience function to detect epistemic cycles."""
    detector = EpistemicCycleDetector()
    return detector.detect_cycles(auth_graph, experiment_to_authorization)
