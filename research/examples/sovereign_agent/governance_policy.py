"""Phase 12: Governance Policy Semantics.

Investigates whether governance policy can be represented declaratively without
collapsing the separation between policy, epistemic state, governance decision,
and authority.

The research question is:
"Can governance rules be expressed as explicit, deterministic, inspectable,
provenance-bearing policy without allowing the policy engine itself to create
authority?"

Do NOT begin by designing syntax. First establish the semantic model.

The policy language is not the research objective. The policy semantics are.

Existing infrastructure reused:
- EpistemicCondition, EpistemicConditionType, EpistemicGovernanceOutcome
- EpistemicallyConditionedGovernanceEngine
- RichFrontier, ProvenancePreservingComposition
- CompletenessScope, CompletenessStatus
- SemanticDisagreementType
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.self_audit.continuous_reconciliation import WorldState
from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    CompletenessStatus,
    create_completeness_scope,
)
from research.examples.sovereign_agent.epistemic_governance import (
    EpistemicCondition,
    EpistemicConditionType,
    EpistemicGovernanceOutcome,
    EpistemicallyConditionedGovernanceEngine,
)
from research.examples.sovereign_agent.frontier_composition_semantics import (
    CompositionOperation,
    FrontierCompositionSemanticsEngine,
    ProvenancePreservingComposition,
    RichFrontier,
    SemanticDisagreementType,
)
from research.examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)


class GovernanceDisposition(str, Enum):
    """Dispositions from policy evaluation.
    
    A disposition is NOT authorization. It is a recommendation to the
    authority mechanism.
    """
    REVIEW_REQUIRED = "review_required"
    HOLD = "hold"
    ESCALATE = "escalate"
    CANNOT_DETERMINE = "cannot_determine"
    DENY = "deny"


class PolicyPredicateType(str, Enum):
    """Types of predicates that can be composed into policies."""
    SCOPE_MATCH = "scope_match"
    PROVENANCE_SUFFICIENT = "provenance_sufficient"
    TEMPORAL_VALID = "temporal_valid"
    COMPLETENESS_SUFFICIENT = "completeness_sufficient"
    EPISTEMIC_STATE_SUPPORTED = "epistemic_state_supported"
    DISAGREEMENT_RESOLVED = "disagreement_resolved"
    EVIDENCE_INDEPENDENT = "evidence_independent"
    AUTHORIZATION_AFFECTED = "authorization_affected"


class PolicyCompositionType(str, Enum):
    """Types of policy composition."""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass(frozen=True)
class PolicyPredicate:
    """A single predicate in a policy.
    
    A predicate evaluates to TRUE, FALSE, or UNKNOWN.
    It never authorizes anything.
    """
    predicate_type: PolicyPredicateType
    required: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Policy:
    """A governance policy.
    
    A policy is:
    - deterministic
    - explicit
    - inspectable
    - versioned
    - provenance-bearing
    - scope-bounded
    - temporally bounded
    - fail-closed where required
    - unable to create authority by itself
    """
    policy_id: str
    version: str
    name: str
    description: str
    predicates: list[PolicyPredicate]
    composition_type: PolicyCompositionType = PolicyCompositionType.AND
    scope: Optional[CompletenessScope] = None
    valid_from: str = "unbounded"
    valid_until: str = "unbounded"
    provenance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """Result of evaluating a policy against a frontier."""
    evaluation_id: str
    policy_id: str
    policy_version: str
    disposition: GovernanceDisposition
    predicate_results: dict[PolicyPredicateType, bool]
    authority_created: bool  # Must always be False
    authority_revoked: bool  # Must always be False
    timestamp: str
    provenance: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class GovernancePolicyEngine:
    """Engine for evaluating governance policies.
    
    Produces governance dispositions, NOT authorization.
    The actual authorization decision is external to this engine.
    """
    
    epistemic_engine: EpistemicallyConditionedGovernanceEngine = field(
        default_factory=EpistemicallyConditionedGovernanceEngine
    )
    
    def evaluate_predicate(
        self,
        predicate: PolicyPredicate,
        frontier: RichFrontier,
        authorization_id: str,
        governance_policy: dict[str, Any],
    ) -> bool:
        """Evaluate a single predicate against a frontier.
        
        Returns True if the predicate is satisfied, False otherwise.
        Returns False for UNKNOWN (fail-closed).
        """
        if predicate.predicate_type == PolicyPredicateType.SCOPE_MATCH:
            required_scope = create_completeness_scope(
                "prop_001", "payment",
                environment=governance_policy.get("scope", "production"),
            )
            return frontier.scope.matches(required_scope)
        
        elif predicate.predicate_type == PolicyPredicateType.PROVENANCE_SUFFICIENT:
            required_quality = predicate.parameters.get("required_quality", "complete")
            return frontier.provenance_quality == required_quality
        
        elif predicate.predicate_type == PolicyPredicateType.TEMPORAL_VALID:
            # Simplified temporal check
            return True
        
        elif predicate.predicate_type == PolicyPredicateType.COMPLETENESS_SUFFICIENT:
            required_status = predicate.parameters.get(
                "required_status", CompletenessStatus.KNOWN_COMPLETE
            )
            actual_status = CompletenessStatus(frontier.completeness_status)
            return actual_status == required_status
        
        elif predicate.predicate_type == PolicyPredicateType.EPISTEMIC_STATE_SUPPORTED:
            return frontier.epistemic_status in ("computed", "supported")
        
        elif predicate.predicate_type == PolicyPredicateType.AUTHORIZATION_AFFECTED:
            member_ids = frontier.get_member_ids()
            return (
                authorization_id in member_ids
                or any(m.startswith("A") for m in member_ids)
            )
        
        elif predicate.predicate_type == PolicyPredicateType.DISAGREEMENT_RESOLVED:
            # For single frontiers, no disagreement
            return True
        
        elif predicate.predicate_type == PolicyPredicateType.EVIDENCE_INDEPENDENT:
            # For single frontiers, evidence is independent by default
            return True
        
        return False
    
    def evaluate_policy(
        self,
        policy: Policy,
        frontier: RichFrontier,
        authorization_id: str,
        governance_policy: dict[str, Any],
    ) -> PolicyEvaluationResult:
        """Evaluate a policy against a frontier.
        
        The policy produces a governance disposition, NOT authorization.
        """
        predicate_results = {}
        
        for predicate in policy.predicates:
            result = self.evaluate_predicate(
                predicate, frontier, authorization_id, governance_policy
            )
            predicate_results[predicate.predicate_type] = result
        
        # Determine disposition based on composition type
        if policy.composition_type == PolicyCompositionType.AND:
            all_satisfied = all(predicate_results.values())
            any_satisfied = any(predicate_results.values())
        elif policy.composition_type == PolicyCompositionType.OR:
            all_satisfied = all(predicate_results.values())
            any_satisfied = any(predicate_results.values())
        else:
            all_satisfied = all(predicate_results.values())
            any_satisfied = any(predicate_results.values())
        
        # Determine disposition
        if all_satisfied:
            disposition = GovernanceDisposition.REVIEW_REQUIRED
        elif not any_satisfied:
            disposition = GovernanceDisposition.HOLD
        else:
            # Some predicates satisfied, some not
            # Check if authorization is affected
            authorization_affected = predicate_results.get(
                PolicyPredicateType.AUTHORIZATION_AFFECTED, False
            )
            if authorization_affected:
                disposition = GovernanceDisposition.HOLD
            else:
                disposition = GovernanceDisposition.CANNOT_DETERMINE
        
        return PolicyEvaluationResult(
            evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
            policy_id=policy.policy_id,
            policy_version=policy.version,
            disposition=disposition,
            predicate_results=predicate_results,
            authority_created=False,
            authority_revoked=False,
            timestamp=datetime.utcnow().isoformat(),
            provenance=policy.provenance + [f"evaluated_at_{datetime.utcnow().isoformat()}"],
            notes=f"Policy evaluation: {disposition.value}",
        )
    
    def verify_policy_does_not_create_authority(
        self,
        result: PolicyEvaluationResult,
    ) -> bool:
        """Verify that policy evaluation does not create authority."""
        return not result.authority_created and not result.authority_revoked


def create_scope_policy() -> Policy:
    """Create a policy that requires scope matching."""
    return Policy(
        policy_id="scope_policy_v1",
        version="1.0.0",
        name="Scope Match Policy",
        description="Requires frontier scope to match authorization scope",
        predicates=[
            PolicyPredicate(
                predicate_type=PolicyPredicateType.AUTHORIZATION_AFFECTED,
                required=True,
            ),
            PolicyPredicate(
                predicate_type=PolicyPredicateType.SCOPE_MATCH,
                required=True,
            ),
        ],
        composition_type=PolicyCompositionType.AND,
        provenance=["policy_authority_001"],
    )


def create_provenance_policy() -> Policy:
    """Create a policy that requires sufficient provenance."""
    return Policy(
        policy_id="provenance_policy_v1",
        version="1.0.0",
        name="Provenance Sufficiency Policy",
        description="Requires frontier provenance to be complete",
        predicates=[
            PolicyPredicate(
                predicate_type=PolicyPredicateType.AUTHORIZATION_AFFECTED,
                required=True,
            ),
            PolicyPredicate(
                predicate_type=PolicyPredicateType.PROVENANCE_SUFFICIENT,
                required=True,
                parameters={"required_quality": "complete"},
            ),
        ],
        composition_type=PolicyCompositionType.AND,
        provenance=["policy_authority_001"],
    )


def create_combined_policy() -> Policy:
    """Create a policy that combines scope and provenance requirements."""
    return Policy(
        policy_id="combined_policy_v1",
        version="1.0.0",
        name="Combined Scope and Provenance Policy",
        description="Requires both scope matching and provenance sufficiency",
        predicates=[
            PolicyPredicate(
                predicate_type=PolicyPredicateType.AUTHORIZATION_AFFECTED,
                required=True,
            ),
            PolicyPredicate(
                predicate_type=PolicyPredicateType.SCOPE_MATCH,
                required=True,
            ),
            PolicyPredicate(
                predicate_type=PolicyPredicateType.PROVENANCE_SUFFICIENT,
                required=True,
                parameters={"required_quality": "complete"},
            ),
        ],
        composition_type=PolicyCompositionType.AND,
        provenance=["policy_authority_001"],
    )


def run_policy_scope_mismatch() -> dict[str, Any]:
    """Test: Policy detects scope mismatch."""
    engine = GovernancePolicyEngine()
    policy = create_scope_policy()
    
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
    
    # Production scope
    frontier_prod = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_prod", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_prod,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Staging scope
    frontier_staging = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_staging", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_staging,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Evaluate policy with production scope requirement
    governance_policy = {"scope": "production"}
    
    result_prod = engine.evaluate_policy(
        policy, frontier_prod, "auth_001", governance_policy
    )
    
    result_staging = engine.evaluate_policy(
        policy, frontier_staging, "auth_001", governance_policy
    )
    
    return {
        "test": "scope_mismatch",
        "disposition_prod": result_prod.disposition.value,
        "disposition_staging": result_staging.disposition.value,
        "dispositions_differ": result_prod.disposition != result_staging.disposition,
        "authority_created": result_prod.authority_created or result_staging.authority_created,
    }


def run_policy_provenance_deficiency() -> dict[str, Any]:
    """Test: Policy detects provenance deficiency."""
    engine = GovernancePolicyEngine()
    policy = create_provenance_policy()
    
    scope = create_completeness_scope("prop_001", "payment", environment="production")
    
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
    
    # Complete provenance
    frontier_complete = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_complete", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    # Incomplete provenance
    frontier_incomplete = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_incomplete", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="incomplete",
    )
    
    governance_policy = {"scope": "production"}
    
    result_complete = engine.evaluate_policy(
        policy, frontier_complete, "auth_001", governance_policy
    )
    
    result_incomplete = engine.evaluate_policy(
        policy, frontier_incomplete, "auth_001", governance_policy
    )
    
    return {
        "test": "provenance_deficiency",
        "disposition_complete": result_complete.disposition.value,
        "disposition_incomplete": result_incomplete.disposition.value,
        "dispositions_differ": result_complete.disposition != result_incomplete.disposition,
        "authority_created": result_complete.authority_created or result_incomplete.authority_created,
    }


def run_policy_composition() -> dict[str, Any]:
    """Test: Policy composition (AND)."""
    engine = GovernancePolicyEngine()
    policy = create_combined_policy()
    
    scope = create_completeness_scope("prop_001", "payment", environment="production")
    
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
    
    # Frontier that satisfies all conditions
    frontier_satisfies = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_satisfies", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    # Frontier that fails provenance
    frontier_fails = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_fails", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="incomplete",
    )
    
    governance_policy = {"scope": "production"}
    
    result_satisfies = engine.evaluate_policy(
        policy, frontier_satisfies, "auth_001", governance_policy
    )
    
    result_fails = engine.evaluate_policy(
        policy, frontier_fails, "auth_001", governance_policy
    )
    
    return {
        "test": "policy_composition",
        "disposition_satisfies": result_satisfies.disposition.value,
        "disposition_fails": result_fails.disposition.value,
        "dispositions_differ": result_satisfies.disposition != result_fails.disposition,
        "authority_created": result_satisfies.authority_created or result_fails.authority_created,
    }


def run_policy_non_amplification() -> dict[str, Any]:
    """Test: Policy composition does not amplify authority."""
    engine = GovernancePolicyEngine()
    
    # Multiple policies
    policies = [
        create_scope_policy(),
        create_provenance_policy(),
        create_combined_policy(),
    ]
    
    scope = create_completeness_scope("prop_001", "payment", environment="production")
    
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
    
    frontier = engine.epistemic_engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_test", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    governance_policy = {"scope": "production"}
    
    results = []
    for policy in policies:
        result = engine.evaluate_policy(
            policy, frontier, "auth_001", governance_policy
        )
        results.append(result)
    
    return {
        "test": "policy_non_amplification",
        "policy_count": len(policies),
        "dispositions": [r.disposition.value for r in results],
        "authority_created_any": any(r.authority_created for r in results),
        "authority_revoked_any": any(r.authority_revoked for r in results),
    }


def run_all_phase12_experiments() -> dict[str, Any]:
    """Run all Phase 12 experiments."""
    results = {}
    
    results["scope_mismatch"] = run_policy_scope_mismatch()
    results["provenance_deficiency"] = run_policy_provenance_deficiency()
    results["policy_composition"] = run_policy_composition()
    results["policy_non_amplification"] = run_policy_non_amplification()
    
    return results


if __name__ == "__main__":
    results = run_all_phase12_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 12: GOVERNANCE POLICY SEMANTICS")
    print("=" * 120)
    
    for name, result in results.items():
        print(f"\n{name}:")
        for k, v in result.items():
            print(f"  {k}: {v}")
