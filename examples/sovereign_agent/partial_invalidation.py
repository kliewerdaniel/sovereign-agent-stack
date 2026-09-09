"""Partial Invalidation Engine.

Handles cases where only part of a plan becomes invalid.

Distinguishes:
- INVALID_COMPONENT
- INVALID_DEPENDENT_COMPONENT
- UNRELATED_COMPONENT
- HISTORICALLY_VALID_COMPONENT
- REQUIRES_REEVALUATION

Does not assume transitive invalidation without explicit dependency semantics.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    AuthorizationStatus,
)
from examples.sovereign_agent.epistemic_invalidation import (
    EpistemicInvalidationEngine,
    InvalidationDecision,
    InvalidationResult,
)
from examples.sovereign_agent.intent_graph import ActionProposal, IntentGraph


class ComponentStatus(str, Enum):
    """Status of a component in a plan."""
    VALID = "valid"
    INVALID = "invalid"
    SUSPENDED = "suspended"
    REQUIRES_REEVALUATION = "requires_reevaluation"
    HISTORICALLY_VALID = "historically_valid"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class ComponentResult:
    """Result for a single component."""
    proposal_id: str
    status: ComponentStatus
    reason: str
    affected_by: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PartialInvalidationResult:
    """Result of partial invalidation evaluation."""
    result_id: str
    timestamp: str
    plan_id: str
    components: list[ComponentResult]
    plan_status: str
    description: str = ""


@dataclass
class PartialInvalidationEngine:
    """Engine for partial invalidation of plans."""

    invalidation_engine: EpistemicInvalidationEngine = field(
        default_factory=EpistemicInvalidationEngine
    )

    def evaluate_partial_invalidation(
        self,
        intent_graph: IntentGraph,
        auth_graphs: dict[str, AuthorizationDependencyGraph],
        invalid_proposal_id: str,
        new_evidence: list[Any],
    ) -> PartialInvalidationResult:
        """Evaluate partial invalidation of a plan.

        When one component becomes invalid, determine what happens to
        dependent and independent components.
        """
        components = []

        # Find the invalid proposal
        invalid_proposal = intent_graph.proposals.get(invalid_proposal_id)
        if not invalid_proposal:
            return PartialInvalidationResult(
                result_id=f"partial_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.utcnow().isoformat(),
                plan_id=intent_graph.graph_id,
                components=[],
                plan_status="unknown",
                description=f"Proposal {invalid_proposal_id} not found",
            )

        # Evaluate the invalid component
        invalid_auth = auth_graphs.get(invalid_proposal_id)
        if invalid_auth:
            inv_result = self.invalidation_engine.evaluate_invalidation(
                invalid_auth, new_evidence
            )
            components.append(ComponentResult(
                proposal_id=invalid_proposal_id,
                status=self._map_decision_to_status(inv_result.decision),
                reason=inv_result.description,
                affected_by=inv_result.new_evidence_ids,
            ))

        # Evaluate dependent components
        dependent_ids = intent_graph.get_dependencies(invalid_proposal_id)
        for dep_id in dependent_ids:
            dep_proposal = intent_graph.proposals.get(dep_id)
            if dep_proposal:
                dep_auth = auth_graphs.get(dep_id)
                if dep_auth:
                    # Dependent components may need reevaluation
                    components.append(ComponentResult(
                        proposal_id=dep_id,
                        status=ComponentStatus.REQUIRES_REEVALUATION,
                        reason=f"Depends on {invalid_proposal_id} which is invalid",
                        affected_by=[invalid_proposal_id],
                    ))

        # Evaluate independent components
        for pid, proposal in intent_graph.proposals.items():
            if pid != invalid_proposal_id and pid not in dependent_ids:
                components.append(ComponentResult(
                    proposal_id=pid,
                    status=ComponentStatus.VALID,
                    reason="Independent of invalid component",
                ))

        # Determine overall plan status
        plan_status = self._determine_plan_status(components)

        return PartialInvalidationResult(
            result_id=f"partial_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            plan_id=intent_graph.graph_id,
            components=components,
            plan_status=plan_status,
            description=f"Partial invalidation: {invalid_proposal_id} is invalid",
        )

    def _map_decision_to_status(
        self,
        decision: InvalidationDecision,
    ) -> ComponentStatus:
        """Map invalidation decision to component status."""
        mapping = {
            InvalidationDecision.PRESERVE: ComponentStatus.VALID,
            InvalidationDecision.SUSPEND: ComponentStatus.SUSPENDED,
            InvalidationDecision.REQUIRE_REEVALUATION: ComponentStatus.REQUIRES_REEVALUATION,
            InvalidationDecision.INVALIDATE: ComponentStatus.INVALID,
            InvalidationDecision.INCONCLUSIVE: ComponentStatus.INCONCLUSIVE,
        }
        return mapping.get(decision, ComponentStatus.INCONCLUSIVE)

    def _determine_plan_status(self, components: list[ComponentResult]) -> str:
        """Determine overall plan status from component statuses."""
        statuses = [c.status for c in components]
        if all(s == ComponentStatus.VALID for s in statuses):
            return "valid"
        if any(s == ComponentStatus.INVALID for s in statuses):
            return "partially_invalid"
        if any(s == ComponentStatus.SUSPENDED for s in statuses):
            return "suspended"
        if any(s == ComponentStatus.REQUIRES_REEVALUATION for s in statuses):
            return "requires_reevaluation"
        return "unknown"


def run_partial_invalidation(
    intent_graph: IntentGraph,
    auth_graphs: dict[str, AuthorizationDependencyGraph],
    invalid_proposal_id: str,
    new_evidence: list[Any],
) -> PartialInvalidationResult:
    """Convenience function to run partial invalidation."""
    engine = PartialInvalidationEngine()
    return engine.evaluate_partial_invalidation(
        intent_graph, auth_graphs, invalid_proposal_id, new_evidence
    )
