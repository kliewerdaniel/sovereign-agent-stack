"""Epistemic Invalidation Engine.

Determines what happens when the epistemic basis of an authorization changes.

Distinguishes:
- AUTHORIZATION VALIDITY
- EPISTEMIC VALIDITY
- WORLD STATE VALIDITY

These are different failure modes. An authorization may be temporally valid
while epistemically stale.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    AuthorizationStatus,
    DependencyType,
    IntersectionResult,
    StalenessType,
)
from research.examples.sovereign_agent.dependency_intersection import (
    DependencyIntersectionEvaluator,
    Evidence,
    EvidenceType,
    IntersectionEvaluation,
)


class InvalidationDecision(str, Enum):
    """Decision about what to do with an authorization."""
    PRESERVE = "preserve"
    SUSPEND = "suspend"
    REQUIRE_REEVALUATION = "require_reevaluation"
    INVALIDATE = "invalidate"
    INCONCLUSIVE = "inconclusive"


class InvalidationReason(str, Enum):
    """Reason for invalidation."""
    EPISTEMIC_CONTRADICTION = "epistemic_contradiction"
    EPISTEMIC_WEAKENING = "epistemic_weakening"
    EXPERIMENT_INVALIDATED = "experiment_invalidated"
    RESOURCE_CHANGED = "resource_changed"
    GOVERNANCE_CHANGED = "governance_changed"
    TEMPORAL_EXPIRED = "temporal_expired"
    PROVENANCE_BROKEN = "provenance_broken"
    NONE = "none"


@dataclass(frozen=True)
class InvalidationResult:
    """Result of an invalidation evaluation."""
    result_id: str
    timestamp: str
    authorization_id: str
    decision: InvalidationDecision
    reason: InvalidationReason
    staleness: set[StalenessType] = field(default_factory=set)
    description: str = ""
    affected_dependencies: list[str] = field(default_factory=list)
    requires_governance_review: bool = False
    new_evidence_ids: list[str] = field(default_factory=list)


@dataclass
class EpistemicInvalidationEngine:
    """Engine for determining epistemic invalidation of authorizations."""

    intersection_evaluator: DependencyIntersectionEvaluator = field(
        default_factory=DependencyIntersectionEvaluator
    )

    def evaluate_invalidation(
        self,
        auth_graph: AuthorizationDependencyGraph,
        new_evidence: list[Evidence],
    ) -> InvalidationResult:
        """Evaluate whether an authorization should be invalidated based on new evidence."""
        all_staleness: set[StalenessType] = set()
        all_affected: list[str] = []
        all_requires_review = False
        all_requires_suspension = False
        decision = InvalidationDecision.PRESERVE
        reason = InvalidationReason.NONE

        for evidence in new_evidence:
            evaluation = self.intersection_evaluator.evaluate(evidence, auth_graph)

            if evaluation.requires_suspension:
                all_requires_suspension = True
                all_requires_review = True

            if evaluation.requires_reevaluation:
                all_requires_review = True

            if evaluation.staleness:
                all_staleness.add(evaluation.staleness)

            if evaluation.affected_dependencies:
                all_affected.extend(evaluation.affected_dependencies)

            # Determine decision based on intersection result
            evidence_decision = self._decision_from_intersection(evaluation)
            decision = self._upgrade_decision(decision, evidence_decision)
            reason = self._reason_from_decision(decision, evidence, auth_graph)

        # Apply decision to auth graph
        if decision == InvalidationDecision.INVALIDATE:
            auth_graph.status = AuthorizationStatus.INVALIDATED
        elif decision == InvalidationDecision.SUSPEND:
            auth_graph.status = AuthorizationStatus.SUSPENDED
        elif decision == InvalidationDecision.REQUIRE_REEVALUATION:
            auth_graph.status = AuthorizationStatus.REQUIRES_REEVALUATION

        # Update staleness
        for staleness in all_staleness:
            auth_graph.mark_stale(staleness)

        return InvalidationResult(
            result_id=f"inv_result_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            authorization_id=auth_graph.authorization_id,
            decision=decision,
            reason=reason,
            staleness=all_staleness,
            description=self._describe_decision(decision, reason, all_staleness),
            affected_dependencies=list(set(all_affected)),
            requires_governance_review=all_requires_review,
            new_evidence_ids=[e.evidence_id for e in new_evidence],
        )

    def _decision_from_intersection(
        self,
        evaluation: IntersectionEvaluation,
    ) -> InvalidationDecision:
        """Determine invalidation decision from intersection evaluation."""
        if evaluation.result == IntersectionResult.UNRELATED:
            return InvalidationDecision.PRESERVE

        if evaluation.result == IntersectionResult.TRANSITIVE_DEPENDENCY:
            return InvalidationDecision.REQUIRE_REEVALUATION

        if evaluation.result == IntersectionResult.DEPENDENCY_CHANGED:
            if evaluation.requires_suspension:
                return InvalidationDecision.SUSPEND
            return InvalidationDecision.REQUIRE_REEVALUATION

        if evaluation.result == IntersectionResult.CONTRADICTORY_DEPENDENCY:
            return InvalidationDecision.SUSPEND

        if evaluation.result == IntersectionResult.UNKNOWN_DEPENDENCY:
            return InvalidationDecision.INCONCLUSIVE

        if evaluation.result == IntersectionResult.DIRECT_DEPENDENCY:
            return InvalidationDecision.SUSPEND

        return InvalidationDecision.PRESERVE

    def _upgrade_decision(
        self,
        current: InvalidationDecision,
        new: InvalidationDecision,
    ) -> InvalidationDecision:
        """Upgrade to the more severe decision."""
        severity = {
            InvalidationDecision.PRESERVE: 0,
            InvalidationDecision.INCONCLUSIVE: 1,
            InvalidationDecision.REQUIRE_REEVALUATION: 2,
            InvalidationDecision.SUSPEND: 3,
            InvalidationDecision.INVALIDATE: 4,
        }
        if severity[new] > severity[current]:
            return new
        return current

    def _reason_from_decision(
        self,
        decision: InvalidationDecision,
        evidence: Evidence,
        auth_graph: AuthorizationDependencyGraph,
    ) -> InvalidationReason:
        """Determine the reason for a decision."""
        if decision == InvalidationDecision.PRESERVE:
            return InvalidationReason.NONE

        if decision == InvalidationDecision.INVALIDATE:
            if auth_graph.is_epistemically_stale():
                return InvalidationReason.EPISTEMIC_CONTRADICTION
            if StalenessType.RESOURCE_STALE in auth_graph.staleness:
                return InvalidationReason.RESOURCE_CHANGED
            if StalenessType.GOVERNANCE_STALE in auth_graph.staleness:
                return InvalidationReason.GOVERNANCE_CHANGED

        if decision == InvalidationDecision.SUSPEND:
            if StalenessType.EPISTEMICALLY_STALE in auth_graph.staleness:
                return InvalidationReason.EPISTEMIC_CONTRADICTION
            if StalenessType.RESOURCE_STALE in auth_graph.staleness:
                return InvalidationReason.RESOURCE_CHANGED

        if decision == InvalidationDecision.REQUIRE_REEVALUATION:
            if StalenessType.EPISTEMICALLY_STALE in auth_graph.staleness:
                return InvalidationReason.EPISTEMIC_WEAKENING

        return InvalidationReason.NONE

    def _describe_decision(
        self,
        decision: InvalidationDecision,
        reason: InvalidationReason,
        staleness: set[StalenessType],
    ) -> str:
        """Create a human-readable description of the decision."""
        staleness_str = ", ".join(s.value for s in staleness) if staleness else "none"
        return (
            f"Decision: {decision.value}. "
            f"Reason: {reason.value}. "
            f"Staleness: {staleness_str}."
        )


def run_invalidations(
    auth_graph: AuthorizationDependencyGraph,
    new_evidence: list[Evidence],
) -> InvalidationResult:
    """Convenience function to run invalidation evaluation."""
    engine = EpistemicInvalidationEngine()
    return engine.evaluate_invalidation(auth_graph, new_evidence)
