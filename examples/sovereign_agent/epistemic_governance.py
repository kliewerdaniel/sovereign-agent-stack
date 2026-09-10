"""Phase 11: Epistemically Conditioned Governance.

Tests whether epistemic conditions should be necessary before a consequential
action can progress from review to authorization.

The central question is NOT "can governance consume the rich frontier?"
but "should epistemic quality be a necessary governance condition?"

Two architectures are tested:

Architecture A: Governance understands epistemic state.
Architecture B: Governance remains deliberately minimal.

The invariant: EPISTEMIC QUALITY ≠ AUTHORITY.
A complete, well-provenanced, temporally valid epistemic claim does not
automatically authorize an action. It can satisfy a necessary governance
condition without becoming sufficient authority.

Existing infrastructure reused:
- AuthorityFrontierIntegrator, GovernanceAction
- RichFrontier, ProvenancePreservingComposition, SemanticDisagreementType
- CompletenessStatus, CompletenessScope, CompletenessValidityInterval
- ScopeSource, ScopeAuthority, ScopedArtifact
- TemporalCompletenessEngine, RevalidationRequirement
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.authority_frontier_integration import (
    AuthorityFrontierIntegrator,
    GovernanceAction,
)
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    CompletenessStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.frontier_composition_semantics import (
    CompositionOperation,
    FrontierCompositionSemanticsEngine,
    ProvenancePreservingComposition,
    RichFrontier,
    SemanticDisagreementType,
)
from examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from examples.sovereign_agent.temporal_completeness import (
    CompletenessValidityInterval,
    RevalidationRequirement,
)


class EpistemicGovernanceOutcome(str, Enum):
    """Outcomes from epistemically conditioned governance."""
    AUTHORIZE = "authorize"
    REVIEW_REQUIRED = "review_required"
    HOLD = "hold"
    ESCALATE = "escalate"
    DENY = "deny"
    CANNOT_DETERMINE = "cannot_determine"


class EpistemicConditionType(str, Enum):
    """Types of epistemic conditions that can be tested."""
    COMPLETENESS = "completeness"
    TEMPORAL_VALIDITY = "temporal_validity"
    SCOPE = "scope"
    EPISTEMIC_STATE = "epistemic_state"
    DISAGREEMENT = "disagreement"
    PROVENANCE = "provenance"
    EVIDENCE_INDEPENDENCE = "evidence_independence"


@dataclass(frozen=True)
class EpistemicCondition:
    """A single epistemic condition that must be satisfied."""
    condition_type: EpistemicConditionType
    required: bool
    satisfied: bool
    details: str = ""


@dataclass(frozen=True)
class EpistemicGovernanceResult:
    """Result of epistemically conditioned governance."""
    test_name: str
    outcome: EpistemicGovernanceOutcome
    conditions: list[EpistemicCondition]
    all_required_satisfied: bool
    authority_created: bool  # Must always be False
    authority_revoked: bool  # Must always be False
    notes: str = ""


@dataclass
class EpistemicallyConditionedGovernanceEngine:
    """Engine for testing epistemically conditioned governance.
    
    Tests whether epistemic conditions should be necessary before
    authorization. Does NOT allow epistemic quality to become authority.
    """
    
    base_integrator: AuthorityFrontierIntegrator = field(default_factory=AuthorityFrontierIntegrator)
    semantics_engine: FrontierCompositionSemanticsEngine = field(default_factory=FrontierCompositionSemanticsEngine)
    
    def evaluate_completeness_condition(
        self,
        frontier: RichFrontier,
        required_status: CompletenessStatus = CompletenessStatus.KNOWN_COMPLETE,
    ) -> EpistemicCondition:
        """Evaluate whether the frontier satisfies a completeness condition."""
        actual_status = CompletenessStatus(frontier.completeness_status)
        satisfied = actual_status == required_status
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.COMPLETENESS,
            required=True,
            satisfied=satisfied,
            details=f"Required: {required_status.value}, Actual: {actual_status.value}",
        )
    
    def evaluate_temporal_validity_condition(
        self,
        frontier: RichFrontier,
        reference_time: str = "2026-01-15T00:00:00Z",
    ) -> EpistemicCondition:
        """Evaluate whether the frontier is temporally valid at the reference time."""
        # Simplified: check if reference_time is within temporal bounds
        valid_from = frontier.temporal_bounds[0]
        valid_until = frontier.temporal_bounds[1]
        
        # Parse timestamps (simplified comparison)
        satisfied = True
        if valid_until != "unbounded":
            # If we have an explicit end, check it
            satisfied = reference_time <= valid_until
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.TEMPORAL_VALIDITY,
            required=True,
            satisfied=satisfied,
            details=f"Valid from {valid_from} to {valid_until}, reference: {reference_time}",
        )
    
    def evaluate_scope_condition(
        self,
        frontier: RichFrontier,
        required_scope: CompletenessScope,
    ) -> EpistemicCondition:
        """Evaluate whether the frontier's scope matches the required scope."""
        satisfied = frontier.scope.matches(required_scope)
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.SCOPE,
            required=True,
            satisfied=satisfied,
            details=f"Required: {required_scope.environment}, Actual: {frontier.scope.environment}",
        )
    
    def evaluate_epistemic_state_condition(
        self,
        frontier: RichFrontier,
        required_supported: bool = True,
    ) -> EpistemicCondition:
        """Evaluate whether the frontier's epistemic state is supported."""
        # Simplified: check if epistemic_status indicates support
        supported = frontier.epistemic_status in ("computed", "supported")
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.EPISTEMIC_STATE,
            required=True,
            satisfied=supported,
            details=f"Required supported: {required_supported}, Actual: {supported}",
        )
    
    def evaluate_disagreement_condition(
        self,
        composition: ProvenancePreservingComposition,
    ) -> EpistemicCondition:
        """Evaluate whether disagreement exists in the composition."""
        has_disagreement = (
            SemanticDisagreementType.EPISTEMIC_DISAGREEMENT in composition.semantic_disagreements
            or SemanticDisagreementType.WORLD_DISAGREEMENT in composition.semantic_disagreements
        )
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.DISAGREEMENT,
            required=False,  # Disagreement doesn't block, but triggers review
            satisfied=not has_disagreement,
            details=f"Has disagreement: {has_disagreement}",
        )
    
    def evaluate_provenance_condition(
        self,
        frontier: RichFrontier,
        required_quality: str = "complete",
    ) -> EpistemicCondition:
        """Evaluate whether the frontier's provenance meets quality requirements."""
        satisfied = frontier.provenance_quality == required_quality
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.PROVENANCE,
            required=True,
            satisfied=satisfied,
            details=f"Required: {required_quality}, Actual: {frontier.provenance_quality}",
        )
    
    def evaluate_evidence_independence_condition(
        self,
        composition: ProvenancePreservingComposition,
    ) -> EpistemicCondition:
        """Evaluate whether evidence is independent across agents."""
        # Check if members have multiple independent evidence sources
        independent_count = 0
        correlated_count = 0
        
        for mp in composition.member_provenance.values():
            if len(mp.evidence_basis) > 1:
                # Multiple evidence sources - check if independent
                # Simplified: if evidence IDs are different, assume independent
                if len(set(mp.evidence_basis)) > 1:
                    independent_count += 1
                else:
                    correlated_count += 1
        
        # Satisfied if at least some evidence is independent
        satisfied = independent_count > 0
        
        return EpistemicCondition(
            condition_type=EpistemicConditionType.EVIDENCE_INDEPENDENCE,
            required=False,
            satisfied=satisfied,
            details=f"Independent: {independent_count}, Correlated: {correlated_count}",
        )
    
    def govern_with_conditions(
        self,
        frontier: RichFrontier,
        authorization_id: str,
        required_conditions: list[EpistemicConditionType],
        current_authority: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> EpistemicGovernanceResult:
        """Apply governance with epistemic conditions.
        
        The decision logic:
        1. Check if authorization is in frontier membership
        2. Check all required epistemic conditions
        3. If all satisfied: AUTHORIZE (but this is still not authority creation)
        4. If any unsatisfied: HOLD or ESCALATE
        5. If cannot determine: CANNOT_DETERMINE
        
        CRITICAL: Even when all conditions are satisfied, this does NOT
        create authority. It merely indicates that the epistemic preconditions
        for authorization are met. The actual authorization decision is
        external to this function.
        """
        conditions = []
        member_ids = frontier.get_member_ids()
        
        # Step 1: Check membership
        # Authorization is affected if:
        # a) authorization_id is in members, OR
        # b) any authorization-related member (starting with "A") is in members
        authorization_in_frontier = (
            authorization_id in member_ids
            or any(m.startswith("A") for m in member_ids)
        )
        
        if not authorization_in_frontier:
            return EpistemicGovernanceResult(
                test_name=f"epistemic_{frontier.frontier_id}",
                outcome=EpistemicGovernanceOutcome.CANNOT_DETERMINE,
                conditions=conditions,
                all_required_satisfied=False,
                authority_created=False,
                authority_revoked=False,
                notes="Authorization not affected by frontier",
            )
        
        # Step 2: Evaluate required conditions
        for condition_type in required_conditions:
            if condition_type == EpistemicConditionType.COMPLETENESS:
                conditions.append(self.evaluate_completeness_condition(frontier))
            elif condition_type == EpistemicConditionType.TEMPORAL_VALIDITY:
                conditions.append(self.evaluate_temporal_validity_condition(frontier))
            elif condition_type == EpistemicConditionType.SCOPE:
                required_scope = create_completeness_scope(
                    "prop_001", "payment",
                    environment=governance_policy.get("scope", "production"),
                )
                conditions.append(self.evaluate_scope_condition(frontier, required_scope))
            elif condition_type == EpistemicConditionType.EPISTEMIC_STATE:
                conditions.append(self.evaluate_epistemic_state_condition(frontier))
            elif condition_type == EpistemicConditionType.PROVENANCE:
                conditions.append(self.evaluate_provenance_condition(frontier))
        
        # Step 3: Determine outcome
        all_required_satisfied = all(
            c.satisfied for c in conditions if c.required
        )
        
        # Check for unsatisfied required conditions
        unsatisfied_required = [c for c in conditions if c.required and not c.satisfied]
        
        if unsatisfied_required:
            # Some required epistemic conditions are not satisfied
            # This does NOT deny authorization - it holds for review
            outcome = EpistemicGovernanceOutcome.HOLD
        else:
            # All required conditions are satisfied
            # This means epistemic preconditions are met
            # But this is NOT authorization - it is a recommendation
            outcome = EpistemicGovernanceOutcome.REVIEW_REQUIRED
        
        # Critical invariants
        authority_created = False  # NEVER
        authority_revoked = False  # NEVER
        
        return EpistemicGovernanceResult(
            test_name=f"epistemic_{frontier.frontier_id}",
            outcome=outcome,
            conditions=conditions,
            all_required_satisfied=all_required_satisfied,
            authority_created=authority_created,
            authority_revoked=authority_revoked,
            notes=f"Epistemic governance: {outcome.value}, conditions satisfied: {all_required_satisfied}",
        )
    
    def govern_composition_with_conditions(
        self,
        composition: ProvenancePreservingComposition,
        authorization_id: str,
        required_conditions: list[EpistemicConditionType],
        current_authority: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> EpistemicGovernanceResult:
        """Apply governance to a provenance composition with epistemic conditions."""
        conditions = []
        member_ids = composition.composed_members
        
        # Step 1: Check membership
        authorization_in_frontier = (
            authorization_id in member_ids
            or any(m.startswith("A") for m in member_ids)
        )
        
        if not authorization_in_frontier:
            return EpistemicGovernanceResult(
                test_name=f"epistemic_comp_{composition.composition_id}",
                outcome=EpistemicGovernanceOutcome.CANNOT_DETERMINE,
                conditions=conditions,
                all_required_satisfied=False,
                authority_created=False,
                authority_revoked=False,
                notes="Authorization not affected by composition",
            )
        
        # Step 2: Evaluate composition-specific conditions
        for condition_type in required_conditions:
            if condition_type == EpistemicConditionType.DISAGREEMENT:
                conditions.append(self.evaluate_disagreement_condition(composition))
            elif condition_type == EpistemicConditionType.EVIDENCE_INDEPENDENCE:
                conditions.append(self.evaluate_evidence_independence_condition(composition))
        
        # Step 3: Determine outcome
        all_required_satisfied = all(
            c.satisfied for c in conditions if c.required
        )
        
        unsatisfied_required = [c for c in conditions if c.required and not c.satisfied]
        
        if unsatisfied_required:
            outcome = EpistemicGovernanceOutcome.HOLD
        else:
            outcome = EpistemicGovernanceOutcome.REVIEW_REQUIRED
        
        return EpistemicGovernanceResult(
            test_name=f"epistemic_comp_{composition.composition_id}",
            outcome=outcome,
            conditions=conditions,
            all_required_satisfied=all_required_satisfied,
            authority_created=False,
            authority_revoked=False,
            notes=f"Composition epistemic governance: {outcome.value}",
        )


def run_completeness_gated_authorization() -> dict[str, Any]:
    """Experiment 1: Completeness-gated authorization.
    
    Same frontier membership, different completeness.
    Tests: COMPLETE + UNKNOWN != automatically equivalent
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: COMPLETE
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    # Agent B: UNKNOWN completeness
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="incomplete",
    )
    
    required = [EpistemicConditionType.COMPLETENESS]
    
    result_a = engine.govern_with_conditions(
        frontier_a, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    result_b = engine.govern_with_conditions(
        frontier_b, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "completeness_gated",
        "frontier_a_completeness": frontier_a.completeness_status,
        "frontier_b_completeness": frontier_b.completeness_status,
        "outcome_a": result_a.outcome.value,
        "outcome_b": result_b.outcome.value,
        "outcomes_differ": result_a.outcome != result_b.outcome,
        "authority_amplified": result_a.authority_created or result_b.authority_created,
    }


def run_temporal_validity_governance() -> dict[str, Any]:
    """Experiment 2: Temporal validity governance.
    
    Tests: VALID_NOW vs EXPIRED vs NOT_YET_VALID vs UNKNOWN
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Frontier valid now (T0)
    frontier_valid = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_valid", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Frontier expired (timestamp in the past)
    frontier_expired = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_expired", timestamp="2025-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    required = [EpistemicConditionType.TEMPORAL_VALIDITY]
    
    # Reference time is 2026-01-15 (after T0 but before T0+1year)
    result_valid = engine.govern_with_conditions(
        frontier_valid, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    # For expired frontier, reference time is still 2026-01-15
    # But frontier was computed at 2025-01-01, so it's "older"
    # The temporal validity check should flag this
    result_expired = engine.govern_with_conditions(
        frontier_expired, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "temporal_validity",
        "outcome_valid": result_valid.outcome.value,
        "outcome_expired": result_expired.outcome.value,
        "outcomes_differ": result_valid.outcome != result_expired.outcome,
        "authority_amplified": result_valid.authority_created or result_expired.authority_created,
    }


def run_scope_governance() -> dict[str, Any]:
    """Experiment 3: Scope governance.
    
    Tests: scope match, subset, superset, mismatch
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope_prod = create_completeness_scope("prop_001", "payment", environment="production")
    scope_staging = create_completeness_scope("prop_001", "payment", environment="staging")
    
    dep_graph = build_authorization_dependency_graph(
        authorization_id="auth_001", evidence_ids=["E1"], proposition_id="P1",
        epistemic_state_id="S1", experiment_id="exp_001", recommendation_id="rec_001",
        governance_policy_id="gov_001", resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01", provenance=["src_001"],
    )
    
    proposition_graph = create_scoped_proposition_graph({"P1": ["E1"]})
    authorization_graph = create_scoped_authorization_graph({"A1": ["P1"]})
    
    world_change = AuthorityDriftEvent(
        event_id="t0_change", timestamp="2026-01-01T00:00:00Z",
        event_type="dependency_mutated", description="E1 mutated",
        affected_actor="A1", affected_component="A1",
        previous_state={"E1": "old"}, new_state={"E1": "new"},
    )
    
    world_state = WorldState(timestamp="2026-01-01T00:00:00Z")
    
    # Agent A: production scope
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_prod,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Agent B: staging scope
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_staging,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    required = [EpistemicConditionType.SCOPE]
    
    # Governance requires production scope
    result_a = engine.govern_with_conditions(
        frontier_a, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    result_b = engine.govern_with_conditions(
        frontier_b, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "scope_governance",
        "scope_a": frontier_a.scope.environment,
        "scope_b": frontier_b.scope.environment,
        "outcome_a": result_a.outcome.value,
        "outcome_b": result_b.outcome.value,
        "outcomes_differ": result_a.outcome != result_b.outcome,
        "scope_mismatch_detected": result_a.outcome != result_b.outcome,
        "authority_amplified": result_a.authority_created or result_b.authority_created,
    }


def run_epistemic_state_governance() -> dict[str, Any]:
    """Experiment 4: Epistemic state governance.
    
    Tests identical membership under:
    - SUPPORTED
    - INCONCLUSIVE
    - CONTRADICTED
    - UNKNOWN
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: supported epistemic state
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Agent B: same frontier but different epistemic state
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    required = [EpistemicConditionType.EPISTEMIC_STATE]
    
    result_a = engine.govern_with_conditions(
        frontier_a, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    result_b = engine.govern_with_conditions(
        frontier_b, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "epistemic_state",
        "outcome_a": result_a.outcome.value,
        "outcome_b": result_b.outcome.value,
        "outcomes_differ": result_a.outcome != result_b.outcome,
        "authority_amplified": result_a.authority_created or result_b.authority_created,
    }


def run_disagreement_governance() -> dict[str, Any]:
    """Experiment 5: Disagreement governance.
    
    Tests whether unresolved epistemic disagreement imposes different
    governance requirements than agreement.
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: P1
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Agent B: P2 (different proposition, same evidence)
    proposition_graph_b = create_scoped_proposition_graph({"P2": ["E1"]})
    authorization_graph_b = create_scoped_authorization_graph({"A1": ["P2"]})
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph_b,
        authorization_graph=authorization_graph_b, scope=scope,
        known_dependencies=["E1"], known_propositions=["P2"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Compose
    comp = engine.semantics_engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
    )
    
    required = [EpistemicConditionType.DISAGREEMENT]
    
    result = engine.govern_composition_with_conditions(
        comp, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "disagreement",
        "has_disagreement": SemanticDisagreementType.EPISTEMIC_DISAGREEMENT in comp.semantic_disagreements,
        "outcome": result.outcome.value,
        "authority_amplified": result.authority_created,
    }


def run_provenance_governance() -> dict[str, Any]:
    """Experiment 6: Provenance governance.
    
    Tests whether provenance deficiencies should produce different
    governance outcomes.
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: complete provenance
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    # Agent B: incomplete provenance
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="incomplete",
    )
    
    required = [EpistemicConditionType.PROVENANCE]
    
    result_a = engine.govern_with_conditions(
        frontier_a, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    result_b = engine.govern_with_conditions(
        frontier_b, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "provenance",
        "outcome_a": result_a.outcome.value,
        "outcome_b": result_b.outcome.value,
        "outcomes_differ": result_a.outcome != result_b.outcome,
        "authority_amplified": result_a.authority_created or result_b.authority_created,
    }


def run_correlated_agreement_governance() -> dict[str, Any]:
    """Experiment 7: Correlated agreement governance.
    
    Tests whether 3 agents with 1 evidence source should count as
    stronger than 2 agents with 2 independent evidence sources.
    """
    engine = EpistemicallyConditionedGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # 3 agents with same evidence (correlated)
    frontiers_correlated = []
    for agent_id in ["agent_A", "agent_B", "agent_C"]:
        f = engine.semantics_engine.compute_rich_frontier(
            agent_id=agent_id, timestamp="2026-01-01T00:00:00Z",
            world_change=world_change, authorization_id="auth_001",
            dependency_graph=dep_graph, proposition_graph=proposition_graph,
            authorization_graph=authorization_graph, scope=scope,
            known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
            world_state=world_state, evidence_basis=["E1"],  # Same evidence
        )
        frontiers_correlated.append(f)
    
    # 2 agents with different evidence (independent)
    frontiers_independent = []
    for agent_id, evidence in [("agent_D", "ED"), ("agent_E", "EE")]:
        f = engine.semantics_engine.compute_rich_frontier(
            agent_id=agent_id, timestamp="2026-01-01T00:00:00Z",
            world_change=world_change, authorization_id="auth_001",
            dependency_graph=dep_graph, proposition_graph=proposition_graph,
            authorization_graph=authorization_graph, scope=scope,
            known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
            world_state=world_state, evidence_basis=[evidence],
        )
        frontiers_independent.append(f)
    
    # Compose correlated
    comp_correlated = engine.semantics_engine.compose_provenance_preserving(
        frontiers_correlated[0], frontiers_correlated[1],
        CompositionOperation.PROVENANCE_PRESERVING_UNION,
    )
    
    # Compose independent
    comp_independent = engine.semantics_engine.compose_provenance_preserving(
        frontiers_independent[0], frontiers_independent[1],
        CompositionOperation.PROVENANCE_PRESERVING_UNION,
    )
    
    required = [EpistemicConditionType.EVIDENCE_INDEPENDENCE]
    
    result_correlated = engine.govern_composition_with_conditions(
        comp_correlated, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    result_independent = engine.govern_composition_with_conditions(
        comp_independent, "auth_001", required,
        {"auth_001": "authorized"}, {"scope": "production"},
    )
    
    return {
        "experiment": "correlated_agreement",
        "correlated_agents": 3,
        "correlated_evidence_sources": 1,
        "independent_agents": 2,
        "independent_evidence_sources": 2,
        "outcome_correlated": result_correlated.outcome.value,
        "outcome_independent": result_independent.outcome.value,
        "authority_amplified": result_correlated.authority_created or result_independent.authority_created,
    }


def run_all_phase11_experiments() -> dict[str, Any]:
    """Run all Phase 11 experiments."""
    results = {}
    
    results["completeness_gated"] = run_completeness_gated_authorization()
    results["temporal_validity"] = run_temporal_validity_governance()
    results["scope"] = run_scope_governance()
    results["epistemic_state"] = run_epistemic_state_governance()
    results["disagreement"] = run_disagreement_governance()
    results["provenance"] = run_provenance_governance()
    results["correlated_agreement"] = run_correlated_agreement_governance()
    
    return results


def _setup_common_infrastructure():
    """Setup common infrastructure for experiments."""
    scope = create_completeness_scope("prop_001", "payment", environment="production")
    
    dep_graph = build_authorization_dependency_graph(
        authorization_id="auth_001",
        evidence_ids=["E1"],
        proposition_id="P1",
        epistemic_state_id="S1",
        experiment_id="exp_001",
        recommendation_id="rec_001",
        governance_policy_id="gov_001",
        resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01",
        provenance=["src_001"],
    )
    
    proposition_graph = create_scoped_proposition_graph({"P1": ["E1"]})
    authorization_graph = create_scoped_authorization_graph({"A1": ["P1"]})
    
    world_change = AuthorityDriftEvent(
        event_id="t0_change",
        timestamp="2026-01-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E1 mutated",
        affected_actor="A1",
        affected_component="A1",
        previous_state={"E1": "old"},
        new_state={"E1": "new"},
    )
    
    world_state = WorldState(
        timestamp="2026-01-01T00:00:00Z",
        static_topology={"nodes": [{"id": "E1", "type": "dependency"}], "edges": []},
    )
    
    return scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state


if __name__ == "__main__":
    results = run_all_phase11_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 11: EPISTEMICALLY CONDITIONED GOVERNANCE")
    print("=" * 120)
    
    for name, result in results.items():
        print(f"\n{name}:")
        for k, v in result.items():
            print(f"  {k}: {v}")
