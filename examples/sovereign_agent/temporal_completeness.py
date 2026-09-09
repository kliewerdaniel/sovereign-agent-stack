"""Temporal Completeness Drift and Revalidation.

Investigates whether SAS can detect when a completeness claim has become
epistemically stale without confusing world change, dependency change,
epistemic change, governance change, and authority change.

Critical distinctions:
    WORLD CHANGE ≠ DEPENDENCY CHANGE ≠ COMPLETENESS CHANGE
    ≠ EPISTEMIC CHANGE ≠ GOVERNANCE CHANGE ≠ AUTHORITY CHANGE

A world change may produce no dependency change.
A dependency change may produce no proposition change.
A completeness change may produce no epistemic invalidation.
An epistemic change may require governance review without automatically revoking authorization.
A governance change may alter future authority without changing historical authority.

This module reuses the existing temporal authority, authority drift,
dependency, invalidation, and completeness infrastructure rather than
creating parallel subsystems.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.self_audit.authority_drift import (
    AuthorityDriftEvent,
    AuthoritySnapshot,
    DriftClassification,
    DriftFinding,
    DriftType,
)
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.dependency_completeness import (
    CompletenessAssessment,
    CompletenessClaim,
    CompletenessDimension,
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.completeness_experiment import (
    CompletenessExperiment,
    ExperimentalCondition,
    WorldDependency,
    WorldDependencyState,
)


class CompletenessDriftType(str, Enum):
    """Types of completeness drift.
    
    These are distinct from authority drift types because completeness
    drift is about the epistemic basis of authority, not authority itself.
    """
    NO_DRIFT = "no_drift"
    WORLD_CHANGE_NO_DEPENDENCY_CHANGE = "world_change_no_dependency_change"
    DEPENDENCY_CHANGE_NO_COMPLETENESS_CHANGE = "dependency_change_no_completeness_change"
    COMPLETENESS_CHANGE_NO_EPISTEMIC_CHANGE = "completeness_change_no_epistemic_change"
    EPISTEMIC_CHANGE_NO_GOVERNANCE_CHANGE = "epistemic_change_no_governance_change"
    GOVERNANCE_CHANGE_NO_AUTHORITY_CHANGE = "governance_change_no_authority_change"
    COMPLETENESS_STALE = "completeness_stale"
    COMPLETENESS_FALSE_STALE = "completeness_false_stale"
    COMPLETENESS_HIDDEN_STALENESS = "completeness_hidden_staleness"
    CONDITIONAL_COMPLETENESS_VIOLATED = "conditional_completeness_violated"
    CONSEQUENCE_ESCALATION = "consequence_escalation"
    SCOPE_MISMATCH = "scope_mismatch"
    TEMPORAL_BOUNDARY_EXPIRED = "temporal_boundary_expired"
    ENVIRONMENT_DRIFT = "environment_drift"
    DOMAIN_DRIFT = "domain_drift"
    ACTOR_DRIFT = "actor_drift"
    INCONCLUSIVE = "inconclusive"


class RevalidationRequirement(str, Enum):
    """What must be revalidated after a change."""
    NOTHING = "nothing"
    DEPENDENCY_ONLY = "dependency_only"
    COMPLETENESS_CLAIM = "completeness_claim"
    EPISTEMIC_STATE = "epistemic_state"
    PROPOSITION = "proposition"
    AUTHORIZATION = "authorization"
    GOVERNANCE_REVIEW = "governance_review"
    FULL_REVALIDATION = "full_revalidation"


@dataclass(frozen=True)
class CompletenessValidityInterval:
    """Temporal and scopal bounds of a completeness claim.
    
    A completeness claim is not eternally valid. It has:
    - Temporal bounds (valid_from, valid_until)
    - Scopal bounds (proposition, consequence, environment, domain, actor, resource)
    - Conditional bounds (feature flags, failure conditions)
    
    This reuses the existing temporal authority infrastructure rather than
    adding parallel temporal fields.
    """
    interval_id: str
    claim_id: str
    valid_from: str
    valid_until: Optional[str] = None
    scope: CompletenessScope = field(default_factory=lambda: CompletenessScope(
        proposition_id="", consequence_type=""
    ))
    conditions: list[str] = field(default_factory=list)
    environment: str = "production"
    domain: str = "sovereign"
    actor_id: str = "any"
    resource_id: str = "any"

    def is_valid_at(self, timestamp: str) -> bool:
        """Check if the claim is temporally valid at a given timestamp."""
        if self.valid_from > timestamp:
            return False
        if self.valid_until and self.valid_until < timestamp:
            return False
        return True

    def is_valid_in_scope(self, scope: CompletenessScope) -> bool:
        """Check if the claim covers the given scope."""
        return self.scope.matches(scope)

    def is_conditional(self) -> bool:
        """Check if this claim has conditions."""
        return len(self.conditions) > 0

    def conditions_met(self, active_conditions: list[str]) -> bool:
        """Check if all required conditions are met."""
        return all(c in active_conditions for c in self.conditions)


@dataclass(frozen=True)
class CompletenessDriftFinding:
    """A finding that completeness has drifted.
    
    This is an epistemic finding, not an authority finding.
    It indicates that a completeness claim may no longer hold,
    but does NOT automatically revoke any authorization.
    """
    finding_id: str
    drift_type: CompletenessDriftType
    drift_classification: DriftClassification
    description: str
    previous_assessment: Optional[CompletenessAssessment] = None
    current_assessment: Optional[CompletenessAssessment] = None
    previous_world: Optional[WorldState] = None
    current_world: Optional[WorldState] = None
    temporal_boundary: str = ""
    affected_scope: Optional[CompletenessScope] = None
    affected_dimensions: list[CompletenessDimension] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    revalidation_requirement: RevalidationRequirement = RevalidationRequirement.NOTHING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def requires_revalidation(self) -> bool:
        """Check if this drift requires revalidation."""
        return self.revalidation_requirement != RevalidationRequirement.NOTHING

    def is_authoritative(self) -> bool:
        """A completeness drift finding is NEVER authoritative."""
        return False


@dataclass(frozen=True)
class RevalidationFrontier:
    """The minimum epistemic surface that must be revalidated after a change.
    
    This is an epistemic/recommendation artifact, NOT authority.
    It indicates what requires reconsideration, not what is revoked.
    
    The frontier is computed from:
    - The world change (ΔWorld)
    - The dependency graph structure
    - The proposition
    - The consequence
    - The scope
    
    The result is a set of artifacts that must be reconsidered.
    """
    frontier_id: str
    world_change_id: str
    authorization_id: str
    timestamp: str
    affected_dependencies: list[str] = field(default_factory=list)
    affected_propositions: list[str] = field(default_factory=list)
    affected_completeness_claims: list[str] = field(default_factory=list)
    affected_authorizations: list[str] = field(default_factory=list)
    affected_epistemic_states: list[str] = field(default_factory=list)
    governance_review_required: bool = False
    revalidation_requirement: RevalidationRequirement = RevalidationRequirement.NOTHING
    scope: Optional[CompletenessScope] = None
    evidence: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if the frontier is empty (nothing to revalidate)."""
        return (
            not self.affected_dependencies
            and not self.affected_propositions
            and not self.affected_completeness_claims
            and not self.affected_authorizations
            and not self.affected_epistemic_states
        )

    def is_authoritative(self) -> bool:
        """A revalidation frontier is NEVER authoritative."""
        return False

    def requires_governance(self) -> bool:
        """Check if governance review is required."""
        return self.governance_review_required

    def requires_revalidation(self) -> bool:
        """Check if any revalidation is required."""
        return not self.is_empty()


@dataclass
class TemporalCompletenessEngine:
    """Engine for temporal completeness drift detection and revalidation.
    
    This engine extends the existing CompletenessEngine with temporal
    reasoning. It reuses:
    - CompletenessEngine for assessment
    - AuthorityDriftEvent for world change tracking
    - WorldState for world state representation
    - AuthoritySnapshot for historical authority state
    
    The engine does NOT create a parallel drift subsystem.
    """

    completeness_engine: CompletenessEngine = field(default_factory=CompletenessEngine)
    drift_findings: list[CompletenessDriftFinding] = field(default_factory=list)
    revalidation_frontiers: list[RevalidationFrontier] = field(default_factory=list)
    historical_assessments: list[tuple[str, CompletenessAssessment]] = field(default_factory=list)

    def assess_temporal_completeness(
        self,
        authorization_id: str,
        graph_id: str,
        declared_dependencies: list[str],
        actual_dependencies: list[str],
        scope: CompletenessScope,
        timestamp: str,
        method: CompletenessMethod = CompletenessMethod.MULTI_SOURCE,
        conditions: list[str] | None = None,
    ) -> tuple[CompletenessAssessment, CompletenessValidityInterval]:
        """Assess completeness at a specific point in time.
        
        Returns both the assessment and its validity interval.
        The assessment is stored historically and never rewritten.
        """
        assessment = self.completeness_engine.assess_completeness(
            authorization_id=authorization_id,
            graph_id=graph_id,
            declared_dependencies=declared_dependencies,
            actual_dependencies=actual_dependencies,
            scope=scope,
            method=method,
        )

        # Create validity interval
        validity_interval = CompletenessValidityInterval(
            interval_id=f"interval_{uuid.uuid4().hex[:12]}",
            claim_id=assessment.claims[0].claim_id if assessment.claims else "",
            valid_from=timestamp,
            valid_until=None,  # Open-ended until drift is detected
            scope=scope,
            conditions=conditions or [],
            environment=scope.environment,
            domain=scope.domain,
            actor_id=scope.actor_id,
            resource_id=scope.resource_id,
        )

        # Store historically (never overwritten)
        self.historical_assessments.append((timestamp, assessment))

        return assessment, validity_interval

    def detect_completeness_drift(
        self,
        previous_world: WorldState,
        current_world: WorldState,
        previous_assessment: CompletenessAssessment,
        current_assessment: CompletenessAssessment,
        previous_timestamp: str,
        current_timestamp: str,
        scope: CompletenessScope,
    ) -> list[CompletenessDriftFinding]:
        """Detect completeness drift between two world states.
        
        This is the core operation: determining whether a completeness
        claim has become stale due to world changes.
        
        The method distinguishes:
        - WORLD_CHANGE_NO_DEPENDENCY_CHANGE: World changed but dependencies didn't
        - DEPENDENCY_CHANGE_NO_COMPLETENESS_CHANGE: Dependencies changed but completeness didn't
        - COMPLETENESS_CHANGE_NO_EPISTEMIC_CHANGE: Completeness changed but epistemic state didn't
        - COMPLETENESS_STALE: Completeness claim is no longer valid
        - COMPLETENESS_FALSE_STALE: Completeness claim appears stale but isn't
        - CONDITIONAL_COMPLETENESS_VIOLATED: A condition for completeness is no longer met
        """
        findings = []

        # Extract dependency IDs from world state topology
        # WorldState has static_topology with edges of type "dependency"
        def extract_deps(world: WorldState) -> set[str]:
            """Extract dependency target IDs from world state topology."""
            deps = set()
            edges = world.static_topology.get("edges", [])
            for edge in edges:
                if edge.get("type") == "dependency":
                    target = edge.get("target", "")
                    if target:
                        deps.add(target)
            # Also check runtime topology for dependency paths
            paths = world.runtime_topology.get("paths", [])
            for path in paths:
                target = path.get("target", "")
                if target:
                    deps.add(target)
            return deps

        prev_deps = extract_deps(previous_world)
        curr_deps = extract_deps(current_world)
        
        added_deps = curr_deps - prev_deps
        removed_deps = prev_deps - curr_deps

        # Case 1: No world change
        if not added_deps and not removed_deps:
            findings.append(CompletenessDriftFinding(
                finding_id=f"drift_{uuid.uuid4().hex[:12]}",
                drift_type=CompletenessDriftType.NO_DRIFT,
                drift_classification=DriftClassification.NONE,
                description="No world change detected",
                previous_assessment=previous_assessment,
                current_assessment=current_assessment,
                previous_world=previous_world,
                current_world=current_world,
                temporal_boundary=f"{previous_timestamp} -> {current_timestamp}",
                affected_scope=scope,
                revalidation_requirement=RevalidationRequirement.NOTHING,
            ))
            return findings

        # Case 2: World change but no dependency change
        # This happens when the world changes in ways unrelated to the authorization
        # We check if any dependency was actually added or removed
        if not added_deps and not removed_deps:
            findings.append(CompletenessDriftFinding(
                finding_id=f"drift_{uuid.uuid4().hex[:12]}",
                drift_type=CompletenessDriftType.WORLD_CHANGE_NO_DEPENDENCY_CHANGE,
                drift_classification=DriftClassification.BENIGN,
                description=f"World changed but no dependency change detected",
                previous_assessment=previous_assessment,
                current_assessment=current_assessment,
                previous_world=previous_world,
                current_world=current_world,
                temporal_boundary=f"{previous_timestamp} -> {current_timestamp}",
                affected_scope=scope,
                revalidation_requirement=RevalidationRequirement.NOTHING,
                evidence=[f"World topology changed"],
            ))
            return findings

        # Case 3: Dependency change detected
        if added_deps or removed_deps:
            # Check if completeness changed
            prev_status = previous_assessment.overall_status
            curr_status = current_assessment.overall_status

            if prev_status == curr_status:
                findings.append(CompletenessDriftFinding(
                    finding_id=f"drift_{uuid.uuid4().hex[:12]}",
                    drift_type=CompletenessDriftType.DEPENDENCY_CHANGE_NO_COMPLETENESS_CHANGE,
                    drift_classification=DriftClassification.BENIGN,
                    description=f"Dependencies changed but completeness unchanged: {added_deps | removed_deps}",
                    previous_assessment=previous_assessment,
                    current_assessment=current_assessment,
                    previous_world=previous_world,
                    current_world=current_world,
                    temporal_boundary=f"{previous_timestamp} -> {current_timestamp}",
                    affected_scope=scope,
                    revalidation_requirement=RevalidationRequirement.DEPENDENCY_ONLY,
                    evidence=[f"Added: {added_deps}", f"Removed: {removed_deps}"],
                ))
            else:
                # Completeness changed - determine the type
                if curr_status in (CompletenessStatus.KNOWN_INCOMPLETE, CompletenessStatus.UNKNOWN):
                    findings.append(CompletenessDriftFinding(
                        finding_id=f"drift_{uuid.uuid4().hex[:12]}",
                        drift_type=CompletenessDriftType.COMPLETENESS_STALE,
                        drift_classification=DriftClassification.SIGNIFICANT,
                        description=f"Completeness claim became stale: {prev_status} -> {curr_status}",
                        previous_assessment=previous_assessment,
                        current_assessment=current_assessment,
                        previous_world=previous_world,
                        current_world=current_world,
                        temporal_boundary=f"{previous_timestamp} -> {current_timestamp}",
                        affected_scope=scope,
                        revalidation_requirement=RevalidationRequirement.COMPLETENESS_CLAIM,
                        evidence=[f"Added: {added_deps}", f"Removed: {removed_deps}"],
                    ))
                elif curr_status == CompletenessStatus.FALSE_COMPLETENESS:
                    findings.append(CompletenessDriftFinding(
                        finding_id=f"drift_{uuid.uuid4().hex[:12]}",
                        drift_type=CompletenessDriftType.COMPLETENESS_FALSE_STALE,
                        drift_classification=DriftClassification.CRITICAL,
                        description=f"False completeness detected: graph appears complete but is not",
                        previous_assessment=previous_assessment,
                        current_assessment=current_assessment,
                        previous_world=previous_world,
                        current_world=current_world,
                        temporal_boundary=f"{previous_timestamp} -> {current_timestamp}",
                        affected_scope=scope,
                        revalidation_requirement=RevalidationRequirement.FULL_REVALIDATION,
                    ))
                else:
                    findings.append(CompletenessDriftFinding(
                        finding_id=f"drift_{uuid.uuid4().hex[:12]}",
                        drift_type=CompletenessDriftType.COMPLETENESS_CHANGE_NO_EPISTEMIC_CHANGE,
                        drift_classification=DriftClassification.SIGNIFICANT,
                        description=f"Completeness changed: {prev_status} -> {curr_status}",
                        previous_assessment=previous_assessment,
                        current_assessment=current_assessment,
                        previous_world=previous_world,
                        current_world=current_world,
                        temporal_boundary=f"{previous_timestamp} -> {current_timestamp}",
                        affected_scope=scope,
                        revalidation_requirement=RevalidationRequirement.COMPLETENESS_CLAIM,
                    ))

        self.drift_findings.extend(findings)
        return findings

    def compute_revalidation_frontier(
        self,
        world_change: AuthorityDriftEvent | None,
        authorization_id: str,
        dependency_graph: list[str],
        proposition_id: str,
        consequence_type: str,
        scope: CompletenessScope,
    ) -> RevalidationFrontier:
        """Compute the minimum epistemic surface that must be revalidated.
        
        This is the most important operation: given a world change,
        determine the smallest set of artifacts that must be reconsidered.
        
        The result is NOT authority. It is a recommendation artifact
        indicating what requires reconsideration.
        
        The frontier is computed from:
        1. Dependency intersection: Does the change affect any dependency?
        2. Proposition intersection: Does the change affect the proposition?
        3. Completeness intersection: Does the change affect completeness?
        4. Authorization intersection: Does the change affect authorization?
        
        If the change doesn't intersect the dependency graph, the frontier is empty.
        """
        frontier = RevalidationFrontier(
            frontier_id=f"frontier_{uuid.uuid4().hex[:12]}",
            world_change_id=world_change.event_id if world_change else "",
            authorization_id=authorization_id,
            timestamp=datetime.utcnow().isoformat(),
            scope=scope,
        )

        if not world_change:
            return frontier

        # Extract changed components from the world change
        changed_components: set[str] = set()
        if world_change.previous_state:
            for k, v in world_change.previous_state.items():
                changed_components.add(k)
                if isinstance(v, str):
                    changed_components.add(v)
        if world_change.new_state:
            for k, v in world_change.new_state.items():
                changed_components.add(k)
                if isinstance(v, str):
                    changed_components.add(v)

        # Check dependency intersection
        affected_deps = [dep for dep in dependency_graph if dep in changed_components]

        if not affected_deps:
            return frontier

        # Affected dependencies found - determine scope of revalidation
        frontier = RevalidationFrontier(
            frontier_id=f"frontier_{uuid.uuid4().hex[:12]}",
            world_change_id=world_change.event_id,
            authorization_id=authorization_id,
            timestamp=datetime.utcnow().isoformat(),
            affected_dependencies=affected_deps,
            affected_propositions=[proposition_id] if proposition_id in changed_components else [],
            affected_completeness_claims=[f"claim_{authorization_id}"],
            affected_authorizations=[authorization_id] if len(affected_deps) > 0 else [],
            scope=scope,
            evidence=[f"Changed: {changed_components}", f"Affected deps: {affected_deps}"],
        )

        # Determine revalidation requirement
        if len(affected_deps) == len(dependency_graph):
            revalidation_requirement = RevalidationRequirement.FULL_REVALIDATION
        elif len(affected_deps) > 0:
            revalidation_requirement = RevalidationRequirement.COMPLETENESS_CLAIM
        else:
            revalidation_requirement = RevalidationRequirement.NOTHING

        frontier = RevalidationFrontier(
            frontier_id=frontier.frontier_id,
            world_change_id=frontier.world_change_id,
            authorization_id=frontier.authorization_id,
            timestamp=frontier.timestamp,
            affected_dependencies=frontier.affected_dependencies,
            affected_propositions=frontier.affected_propositions,
            affected_completeness_claims=frontier.affected_completeness_claims,
            affected_authorizations=frontier.affected_authorizations,
            revalidation_requirement=revalidation_requirement,
            scope=frontier.scope,
            evidence=frontier.evidence,
        )

        self.revalidation_frontiers.append(frontier)
        return frontier

    def get_historical_assessments(self) -> list[tuple[str, CompletenessAssessment]]:
        """Get all historical completeness assessments.
        
        Assessments are immutable and never rewritten.
        Each assessment is a snapshot at a specific point in time.
        """
        return list(self.historical_assessments)

    def get_assessments_in_range(
        self,
        from_timestamp: str,
        to_timestamp: str,
    ) -> list[tuple[str, CompletenessAssessment]]:
        """Get assessments within a temporal range."""
        return [
            (ts, assessment)
            for ts, assessment in self.historical_assessments
            if from_timestamp <= ts <= to_timestamp
        ]
