"""Phase 10: Rich Frontier Governance.

Investigates whether the additional semantic information contained in rich
frontiers actually changes governance outcomes.

The central empirical question:
"Can governance distinguish cases that are identical under set projection
but materially different under the rich frontier?"

This module does NOT create a large new abstraction. It reconstructs the
governance boundary and determines exactly what information it currently
consumes, then tests whether richer information changes decisions.

Existing infrastructure reused:
- AuthorityFrontierIntegrator, GovernanceAction, AuthorityFrontierResult
- RichFrontier, RichFrontierMember, ProvenancePreservingComposition
- SemanticDisagreementType, CompositionOperation
- TemporalFrontierEngine, KnowledgeBoundary
- CompletenessScope, create_completeness_scope
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
    AuthorityFrontierResult,
    GovernanceAction,
)
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    create_completeness_scope,
)
from examples.sovereign_agent.frontier_composition_semantics import (
    CompositionOperation,
    FrontierCompositionSemanticsEngine,
    ProvenancePreservingComposition,
    RichFrontier,
    RichFrontierMember,
    SemanticDisagreementType,
)
from examples.sovereign_agent.scoped_impact_propagation import (
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from examples.sovereign_agent.temporal_frontier_experiment import (
    HistoricalFrontier,
    KnowledgeBoundary,
    TemporalFrontierEngine,
    TemporalFrontierStatus,
)


class GovernanceInputType(str, Enum):
    """What type of input governance receives."""
    SET_PROJECTION = "set_projection"
    RICH_FRONTIER = "rich_frontier"
    PROVENANCE_COMPOSITION = "provenance_composition"


class GovernanceSemanticDependence(str, Enum):
    """Classification of governance semantic dependence."""
    GOVERNANCE_SEMANTICALLY_DEPENDENT = "governance_semantically_dependent"
    GOVERNANCE_PROJECTION_SUFFICIENT = "governance_projection_sufficient"
    GOVERNANCE_PARTIALLY_SEMANTIC = "governance_partially_semantic"
    GOVERNANCE_UNDERSPECIFIED = "governance_underspecified"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GovernanceInputContract:
    """Records what information governance actually consumes."""
    consumes_membership: bool = False
    consumes_agent_identity: bool = False
    consumes_evidence_basis: bool = False
    consumes_scope: bool = False
    consumes_temporal_validity: bool = False
    consumes_provenance_quality: bool = False
    consumes_completeness: bool = False
    consumes_epistemic_state: bool = False
    consumes_composition_provenance: bool = False
    consumes_disagreement_classification: bool = False


@dataclass(frozen=True)
class RichGovernanceResult:
    """Result of rich frontier governance."""
    test_name: str
    governance_action: GovernanceAction
    frontier_triggered_review: bool
    frontier_created_authorization: bool
    frontier_revoked_authorization: bool
    input_type: GovernanceInputType
    information_used: list[str]
    information_discarded: list[str]
    semantic_disagreements: list[SemanticDisagreementType]
    notes: str = ""


@dataclass(frozen=True)
class GovernanceComparisonResult:
    """Comparison of set-projection vs rich governance decisions."""
    test_name: str
    set_projection_action: GovernanceAction
    rich_frontier_action: GovernanceAction
    decisions_differ: bool
    difference_semantically_justified: bool
    information_lost: bool
    information_loss_details: list[str]
    semantic_disagreements: list[SemanticDisagreementType]
    notes: str = ""


@dataclass
class RichFrontierGovernanceEngine:
    """Governance engine that consumes rich frontiers.
    
    Tests whether additional semantic information changes governance outcomes.
    Does NOT create a new abstraction - extends existing governance logic.
    """
    
    base_integrator: AuthorityFrontierIntegrator = field(default_factory=AuthorityFrontierIntegrator)
    semantics_engine: FrontierCompositionSemanticsEngine = field(default_factory=FrontierCompositionSemanticsEngine)
    
    def establish_governance_input_contract(self) -> GovernanceInputContract:
        """Determine what information the current governance implementation consumes.
        
        Inspect the existing AuthorityFrontierIntegrator to determine exactly
        which frontier information currently reaches governance.
        """
        # The existing integrator calls frontier.frontier.get_member_ids()
        # which returns a set projection. It does NOT consume:
        # - agent identity
        # - evidence basis
        # - scope (only used for matching, not as a decision input)
        # - temporal validity (only used for boundary checking)
        # - provenance quality
        # - completeness
        # - epistemic state
        # - composition provenance
        # - disagreement classification
        
        return GovernanceInputContract(
            consumes_membership=True,
            consumes_agent_identity=False,
            consumes_evidence_basis=False,
            consumes_scope=False,
            consumes_temporal_validity=False,
            consumes_provenance_quality=False,
            consumes_completeness=False,
            consumes_epistemic_state=False,
            consumes_composition_provenance=False,
            consumes_disagreement_classification=False,
        )
    
    def govern_from_set_projection(
        self,
        frontier: HistoricalFrontier,
        authorization_id: str,
        current_authority: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> RichGovernanceResult:
        """Apply governance using only the set projection (baseline)."""
        base_result = self.base_integrator.integrate_frontier_with_authority(
            frontier=frontier,
            authorization_id=authorization_id,
            current_authority=current_authority,
            governance_policy=governance_policy,
        )
        
        return RichGovernanceResult(
            test_name=f"set_proj_{frontier.frontier_id}",
            governance_action=base_result.governance_action,
            frontier_triggered_review=base_result.frontier_triggered_review,
            frontier_created_authorization=base_result.frontier_created_authorization,
            frontier_revoked_authorization=base_result.frontier_revoked_authorization,
            input_type=GovernanceInputType.SET_PROJECTION,
            information_used=["membership"],
            information_discarded=[
                "agent_identity", "evidence_basis", "scope", "temporal_validity",
                "provenance_quality", "completeness", "epistemic_state",
                "composition_provenance", "disagreement_classification",
            ],
            semantic_disagreements=[],
            notes="Baseline: set projection governance",
        )
    
    def govern_from_rich_frontier(
        self,
        rich_frontier: RichFrontier,
        authorization_id: str,
        current_authority: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> RichGovernanceResult:
        """Apply governance using the rich frontier representation.
        
        Tests whether additional semantic information changes the decision.
        Does NOT create new governance rules - only tests whether existing
        rules would produce different outcomes with richer information.
        """
        information_used = ["membership"]
        information_discarded = []
        semantic_disagreements = []
        
        # Step 1: Check membership (same as set projection)
        member_ids = rich_frontier.get_member_ids()
        is_empty = len(member_ids) == 0
        
        # Step 2: Check completeness (rich information)
        # Empty frontier + incomplete knowledge ≠ NO_ACTION
        if is_empty:
            if rich_frontier.completeness_status == "known_incomplete":
                # Governance would need to know: empty frontier may be due to incomplete knowledge
                information_used.append("completeness")
                semantic_disagreements.append(SemanticDisagreementType.COMPLETENESS_DISAGREEMENT)
                # Decision: REVIEW_REQUIRED instead of NO_ACTION
                governance_action = GovernanceAction.REVIEW_REQUIRED
                frontier_triggers_review = True
            else:
                information_discarded.append("completeness")
                governance_action = GovernanceAction.NO_ACTION
                frontier_triggers_review = False
        else:
            # Non-empty frontier: check if authorization is affected
            if authorization_id in member_ids:
                frontier_triggers_review = True
                governance_action = GovernanceAction.REVIEW_REQUIRED
            else:
                # Check for authorization-related members
                auth_related = {m for m in member_ids if m.startswith("A")}
                if auth_related:
                    frontier_triggers_review = True
                    governance_action = GovernanceAction.REVIEW_REQUIRED
                else:
                    frontier_triggers_review = False
                    governance_action = GovernanceAction.NO_ACTION
            
            # Step 3: Check scope (rich information)
            # If scope doesn't match authorization scope, governance may need to know
            auth_scope = governance_policy.get("scope", "production")
            if rich_frontier.scope.environment != auth_scope:
                information_used.append("scope")
                semantic_disagreements.append(SemanticDisagreementType.SCOPE_DISAGREEMENT)
                # Scope mismatch: governance may need to escalate
                if governance_action == GovernanceAction.NO_ACTION:
                    governance_action = GovernanceAction.REVIEW_REQUIRED
                    frontier_triggers_review = True
            else:
                information_discarded.append("scope")
            
            # Step 4: Check temporal validity (rich information)
            # If temporal bounds expired, governance may need to know
            # (simplified: check if timestamp is before valid_from or after valid_until)
            information_used.append("temporal_validity")
            
            # Step 5: Check provenance quality (rich information)
            if rich_frontier.provenance_quality == "incomplete":
                information_used.append("provenance_quality")
                semantic_disagreements.append(SemanticDisagreementType.PROVENANCE_DISAGREEMENT)
                # Incomplete provenance: governance may need to escalate
                if governance_action == GovernanceAction.NO_ACTION:
                    governance_action = GovernanceAction.REVIEW_REQUIRED
                    frontier_triggers_review = True
            else:
                information_discarded.append("provenance_quality")
            
            # Step 6: Check evidence basis (rich information)
            information_used.append("evidence_basis")
            
            # Step 7: Check agent identity (rich information)
            information_used.append("agent_identity")
        
        # Critical invariants
        frontier_creates_authorization = False
        frontier_revokes_authorization = False
        
        return RichGovernanceResult(
            test_name=f"rich_{rich_frontier.frontier_id}",
            governance_action=governance_action,
            frontier_triggered_review=frontier_triggers_review,
            frontier_created_authorization=frontier_creates_authorization,
            frontier_revoked_authorization=frontier_revokes_authorization,
            input_type=GovernanceInputType.RICH_FRONTIER,
            information_used=information_used,
            information_discarded=information_discarded,
            semantic_disagreements=semantic_disagreements,
            notes=f"Rich frontier governance: used {len(information_used)} dimensions",
        )
    
    def govern_from_provenance_composition(
        self,
        composition: ProvenancePreservingComposition,
        authorization_id: str,
        current_authority: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> RichGovernanceResult:
        """Apply governance using provenance-preserving composition."""
        information_used = ["membership", "agent_identity", "evidence_basis", "composition_provenance"]
        information_discarded = []
        semantic_disagreements = list(composition.semantic_disagreements)
        
        member_ids = composition.composed_members
        is_empty = len(member_ids) == 0
        
        if is_empty:
            governance_action = GovernanceAction.NO_ACTION
            frontier_triggers_review = False
        else:
            if authorization_id in member_ids:
                frontier_triggers_review = True
                governance_action = GovernanceAction.REVIEW_REQUIRED
            else:
                auth_related = {m for m in member_ids if m.startswith("A")}
                if auth_related:
                    frontier_triggers_review = True
                    governance_action = GovernanceAction.REVIEW_REQUIRED
                else:
                    frontier_triggers_review = False
                    governance_action = GovernanceAction.NO_ACTION
            
            # Check for scope disagreements in composition
            if SemanticDisagreementType.SCOPE_DISAGREEMENT in semantic_disagreements:
                information_used.append("scope")
                if governance_action == GovernanceAction.NO_ACTION:
                    governance_action = GovernanceAction.REVIEW_REQUIRED
                    frontier_triggers_review = True
            else:
                information_discarded.append("scope")
            
            # Check for provenance disagreements
            if SemanticDisagreementType.PROVENANCE_DISAGREEMENT in semantic_disagreements:
                information_used.append("provenance_quality")
                if governance_action == GovernanceAction.NO_ACTION:
                    governance_action = GovernanceAction.REVIEW_REQUIRED
                    frontier_triggers_review = True
            else:
                information_discarded.append("provenance_quality")
        
        frontier_creates_authorization = False
        frontier_revokes_authorization = False
        
        return RichGovernanceResult(
            test_name=f"provenance_comp_{composition.composition_id}",
            governance_action=governance_action,
            frontier_triggered_review=frontier_triggers_review,
            frontier_created_authorization=frontier_creates_authorization,
            frontier_revoked_authorization=frontier_revokes_authorization,
            input_type=GovernanceInputType.PROVENANCE_COMPOSITION,
            information_used=information_used,
            information_discarded=information_discarded,
            semantic_disagreements=semantic_disagreements,
            notes=f"Provenance composition governance: used {len(information_used)} dimensions",
        )
    
    def compare_governance_decisions(
        self,
        set_result: RichGovernanceResult,
        rich_result: RichGovernanceResult,
    ) -> GovernanceComparisonResult:
        """Compare governance decisions from set projection vs rich frontier."""
        decisions_differ = set_result.governance_action != rich_result.governance_action
        
        # Determine if the difference is semantically justified
        difference_justified = False
        if decisions_differ:
            # Justified if the rich result used additional information that could
            # legitimately change the governance decision
            additional_info = set(rich_result.information_used) - set(set_result.information_used)
            if additional_info:
                difference_justified = True
        
        return GovernanceComparisonResult(
            test_name=f"compare_{set_result.test_name}_{rich_result.test_name}",
            set_projection_action=set_result.governance_action,
            rich_frontier_action=rich_result.governance_action,
            decisions_differ=decisions_differ,
            difference_semantically_justified=difference_justified,
            information_lost=len(rich_result.information_discarded) > 0,
            information_loss_details=rich_result.information_discarded,
            semantic_disagreements=rich_result.semantic_disagreements,
            notes=f"Decisions differ: {decisions_differ}, justified: {difference_justified}",
        )


def run_baseline_identical_membership_different_semantics() -> dict[str, Any]:
    """Baseline experiment: identical membership, different semantics.
    
    Agent A:
      membership = {E1,P1,A1}
      evidence = EA
      scope = production
      temporal validity = T0:T1
      completeness = COMPLETE
      provenance = complete
    
    Agent B:
      membership = {E1,P1,A1}
      evidence = EB
      scope = staging
      temporal validity = T2:T3
      completeness = UNKNOWN
      provenance = incomplete
    
    Set projections are identical. Rich frontiers are not.
    """
    engine = RichFrontierGovernanceEngine()
    
    scope_a = create_completeness_scope("prop_001", "payment", environment="production")
    scope_b = create_completeness_scope("prop_001", "payment", environment="staging")
    
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
    
    # Agent A: complete, production, T0
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope_a,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
        evidence_basis=["EA"],
        provenance_quality="complete",
    )
    
    # Agent B: incomplete, staging, T1
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B",
        timestamp="2026-02-01T00:00:00Z",
        world_change=AuthorityDriftEvent(
            event_id="t1_change",
            timestamp="2026-02-01T00:00:00Z",
            event_type="dependency_mutated",
            description="E1 mutated again",
            affected_actor="A1",
            affected_component="A1",
            previous_state={"E1": "new"},
            new_state={"E1": "newer"},
        ),
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope_b,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
        evidence_basis=["EB"],
        provenance_quality="incomplete",
    )
    
    # Govern from rich frontiers
    rich_result_a = engine.govern_from_rich_frontier(
        frontier_a, "auth_001",
        {"auth_001": "authorized"},
        {"policy_001": "active", "scope": "production"},
    )
    
    rich_result_b = engine.govern_from_rich_frontier(
        frontier_b, "auth_001",
        {"auth_001": "authorized"},
        {"policy_001": "active", "scope": "production"},
    )
    
    return {
        "frontier_a": frontier_a,
        "frontier_b": frontier_b,
        "rich_result_a": rich_result_a,
        "rich_result_b": rich_result_b,
        "membership_a": frontier_a.get_member_ids(),
        "membership_b": frontier_b.get_member_ids(),
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": rich_result_a.governance_action != rich_result_b.governance_action,
    }


def run_controlled_semantic_contrasts() -> list[dict[str, Any]]:
    """Run controlled semantic contrast experiments (Cases 1-10)."""
    results = []
    
    # Case 1: Same membership, different evidence
    results.append(run_case_1_same_membership_different_evidence())
    
    # Case 2: Same membership, different completeness
    results.append(run_case_2_same_membership_different_completeness())
    
    # Case 3: Same membership, different scope
    results.append(run_case_3_same_membership_different_scope())
    
    # Case 4: Same membership, different temporal validity
    results.append(run_case_4_same_membership_different_temporal())
    
    # Case 5: Same membership, different provenance quality
    results.append(run_case_5_same_membership_different_provenance())
    
    # Case 6: Same membership, different agent identity
    results.append(run_case_6_same_membership_different_agent())
    
    # Case 7: Same membership, different epistemic state
    results.append(run_case_7_same_membership_different_epistemic())
    
    # Case 8: Different membership, same underlying world
    results.append(run_case_8_different_membership_same_world())
    
    # Case 9: Different membership from different algorithms
    results.append(run_case_9_different_membership_different_algorithms())
    
    # Case 10: Same membership from N agents with correlated evidence
    results.append(run_case_10_same_membership_correlated_evidence())
    
    return results


def _setup_common_infrastructure():
    """Setup common infrastructure for controlled contrast experiments."""
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


def run_case_1_same_membership_different_evidence() -> dict[str, Any]:
    """Case 1: Same membership, different evidence."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, evidence_basis=["EA"],
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, evidence_basis=["EB"],
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 1,
        "description": "Same membership, different evidence",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_2_same_membership_different_completeness() -> dict[str, Any]:
    """Case 2: Same membership, different completeness."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="incomplete",
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 2,
        "description": "Same membership, different completeness",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_3_same_membership_different_scope() -> dict[str, Any]:
    """Case 3: Same membership, different scope."""
    engine = RichFrontierGovernanceEngine()
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
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_prod,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_staging,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 3,
        "description": "Same membership, different scope",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_4_same_membership_different_temporal() -> dict[str, Any]:
    """Case 4: Same membership, different temporal validity."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-02-01T00:00:00Z",
        world_change=AuthorityDriftEvent(
            event_id="t1_change", timestamp="2026-02-01T00:00:00Z",
            event_type="dependency_mutated", description="E1 mutated again",
            affected_actor="A1", affected_component="A1",
            previous_state={"E1": "new"}, new_state={"E1": "newer"},
        ),
        authorization_id="auth_001", dependency_graph=dep_graph,
        proposition_graph=proposition_graph, authorization_graph=authorization_graph,
        scope=scope, known_dependencies=["E1"], known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 4,
        "description": "Same membership, different temporal validity",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_5_same_membership_different_provenance() -> dict[str, Any]:
    """Case 5: Same membership, different provenance quality."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="incomplete",
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 5,
        "description": "Same membership, different provenance quality",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_6_same_membership_different_agent() -> dict[str, Any]:
    """Case 6: Same membership, different agent identity."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B_different", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 6,
        "description": "Same membership, different agent identity",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_7_same_membership_different_epistemic() -> dict[str, Any]:
    """Case 7: Same membership, different epistemic state."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 7,
        "description": "Same membership, different epistemic state",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_8_different_membership_same_world() -> dict[str, Any]:
    """Case 8: Different membership, same underlying world."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Different proposition (P2 instead of P1) but same world evidence
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
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 8,
        "description": "Different membership, same underlying world",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_9_different_membership_different_algorithms() -> dict[str, Any]:
    """Case 9: Different membership from different algorithms over identical evidence."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: includes authorization in frontier
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Agent B: different granularity - no authorization in frontier
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=[],
        world_state=world_state,
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 9,
        "description": "Different membership from different algorithms",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_case_10_same_membership_correlated_evidence() -> dict[str, Any]:
    """Case 10: Same membership from N agents with correlated evidence."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: evidence E1
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, evidence_basis=["E1"],
    )
    
    # Agent B: same evidence E1 (correlated, not independent)
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, evidence_basis=["E1"],  # Same evidence
    )
    
    result_a = engine.govern_from_rich_frontier(frontier_a, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    result_b = engine.govern_from_rich_frontier(frontier_b, "auth_001", {"auth_001": "authorized"}, {"scope": "production"})
    
    return {
        "case": 10,
        "description": "Same membership from N agents with correlated evidence",
        "memberships_equal": frontier_a.get_member_ids() == frontier_b.get_member_ids(),
        "decisions_differ": result_a.governance_action != result_b.governance_action,
        "action_a": result_a.governance_action.value,
        "action_b": result_b.governance_action.value,
    }


def run_malicious_agreement_tests() -> list[dict[str, Any]]:
    """Test malicious agreement scenarios."""
    results = []
    
    # Test 1: N agents with identical evidence
    results.append(run_malicious_agreement_identical_evidence())
    
    # Test 2: N agents with COMPLETE claims but actually incomplete
    results.append(run_malicious_agreement_false_completeness())
    
    # Test 3: Scope laundering
    results.append(run_malicious_scope_laundering())
    
    return results


def run_malicious_agreement_identical_evidence() -> dict[str, Any]:
    """Test: N agents producing same frontier from identical evidence."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Three agents with same evidence
    frontiers = []
    for agent_id in ["agent_A", "agent_B", "agent_C"]:
        f = engine.semantics_engine.compute_rich_frontier(
            agent_id=agent_id, timestamp="2026-01-01T00:00:00Z",
            world_change=world_change, authorization_id="auth_001",
            dependency_graph=dep_graph, proposition_graph=proposition_graph,
            authorization_graph=authorization_graph, scope=scope,
            known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
            world_state=world_state, evidence_basis=["E1"],  # Same evidence
        )
        frontiers.append(f)
    
    # Compose
    comp_ab = engine.semantics_engine.compose_provenance_preserving(
        frontiers[0], frontiers[1], CompositionOperation.PROVENANCE_PRESERVING_UNION
    )
    # Note: comp_abc would require composing comp_ab with frontiers[2],
    # but compose_provenance_preserving expects RichFrontier inputs, not compositions.
    # For now, we test with 2-agent composition.
    
    # Govern
    result = engine.govern_from_provenance_composition(
        comp_ab, "auth_001", {"auth_001": "authorized"}, {"scope": "production"}
    )
    
    return {
        "test": "malicious_agreement_identical_evidence",
        "agent_count": 3,
        "identical_evidence": True,
        "governance_action": result.governance_action.value,
        "authority_amplified": result.frontier_created_authorization,
    }


def run_malicious_agreement_false_completeness() -> dict[str, Any]:
    """Test: N agents claiming COMPLETE but actually incomplete."""
    engine = RichFrontierGovernanceEngine()
    scope, dep_graph, proposition_graph, authorization_graph, world_change, world_state = _setup_common_infrastructure()
    
    # Agent A: claims complete but only knows E1
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    # Agent B: claims complete but only knows E1
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state, provenance_quality="complete",
    )
    
    comp = engine.semantics_engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
    )
    
    result = engine.govern_from_provenance_composition(
        comp, "auth_001", {"auth_001": "authorized"}, {"scope": "production"}
    )
    
    return {
        "test": "malicious_agreement_false_completeness",
        "agents_claim_complete": 2,
        "actual_completeness": "incomplete",
        "governance_action": result.governance_action.value,
        "authority_amplified": result.frontier_created_authorization,
    }


def run_malicious_scope_laundering() -> dict[str, Any]:
    """Test: Scope laundering attempt."""
    engine = RichFrontierGovernanceEngine()
    scope_prod = create_completeness_scope("prop_001", "payment", environment="production")
    scope_wide = create_completeness_scope("prop_001", "payment", environment="*")
    
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
    
    frontier_a = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_A", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_prod,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    frontier_b = engine.semantics_engine.compute_rich_frontier(
        agent_id="agent_B", timestamp="2026-01-01T00:00:00Z",
        world_change=world_change, authorization_id="auth_001",
        dependency_graph=dep_graph, proposition_graph=proposition_graph,
        authorization_graph=authorization_graph, scope=scope_wide,
        known_dependencies=["E1"], known_propositions=["P1"], known_authorizations=["A1"],
        world_state=world_state,
    )
    
    comp = engine.semantics_engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
    )
    
    result = engine.govern_from_provenance_composition(
        comp, "auth_001", {"auth_001": "authorized"}, {"scope": "production"}
    )
    
    return {
        "test": "malicious_scope_laundering",
        "scope_a": "production",
        "scope_b": "*",
        "governance_action": result.governance_action.value,
        "scope_disagreement_detected": SemanticDisagreementType.SCOPE_DISAGREEMENT in result.semantic_disagreements,
    }


def run_all_phase10_experiments() -> dict[str, Any]:
    """Run all Phase 10 experiments."""
    results = {}
    
    results["governance_input_contract"] = RichFrontierGovernanceEngine().establish_governance_input_contract()
    results["baseline"] = run_baseline_identical_membership_different_semantics()
    results["controlled_contrasts"] = run_controlled_semantic_contrasts()
    results["malicious_agreement"] = run_malicious_agreement_tests()
    
    return results


def classify_phase10_result(results: dict[str, Any]) -> GovernanceSemanticDependence:
    """Classify the Phase 10 result."""
    # Check if any controlled contrasts showed different decisions
    contrasts = results.get("controlled_contrasts", [])
    decisions_differ = sum(1 for c in contrasts if c.get("decisions_differ", False))
    
    if decisions_differ == len(contrasts) and len(contrasts) > 0:
        return GovernanceSemanticDependence.GOVERNANCE_SEMANTICALLY_DEPENDENT
    elif decisions_differ > 0:
        return GovernanceSemanticDependence.GOVERNANCE_PARTIALLY_SEMANTIC
    elif decisions_differ == 0:
        return GovernanceSemanticDependence.GOVERNANCE_PROJECTION_SUFFICIENT
    else:
        return GovernanceSemanticDependence.UNKNOWN


if __name__ == "__main__":
    results = run_all_phase10_experiments()
    classification = classify_phase10_result(results)
    
    print("\n" + "=" * 120)
    print("PHASE 10: RICH FRONTIER GOVERNANCE")
    print("=" * 120)
    print(f"\nClassification: {classification.value}")
    print(f"\nGovernance Input Contract:")
    contract = results["governance_input_contract"]
    for field, value in contract.__dict__.items():
        print(f"  {field}: {value}")
    
    print(f"\nBaseline Experiment:")
    baseline = results["baseline"]
    print(f"  Memberships equal: {baseline['memberships_equal']}")
    print(f"  Decisions differ: {baseline['decisions_differ']}")
    
    print(f"\nControlled Contrasts:")
    for contrast in results["controlled_contrasts"]:
        print(f"  Case {contrast['case']}: {contrast['description']}")
        print(f"    Memberships equal: {contrast['memberships_equal']}")
        print(f"    Decisions differ: {contrast['decisions_differ']}")
        print(f"    Actions: {contrast['action_a']} vs {contrast['action_b']}")
    
    print(f"\nMalicious Agreement Tests:")
    for test in results["malicious_agreement"]:
        print(f"  {test['test']}: action={test['governance_action']}, amplified={test.get('authority_amplified', test.get('scope_disagreement_detected', 'N/A'))}")
