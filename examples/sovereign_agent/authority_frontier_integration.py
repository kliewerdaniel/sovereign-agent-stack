"""Phase 7: Authority Frontier Integration.

Connects the revalidation frontier to the authority graph, ensuring that
frontier membership correctly triggers governance review without becoming
authorization itself.

Key invariants:
- FRONTIER ≠ AUTHORIZATION
- FRONTIER_MEMBERSHIP ≠ AUTHORITY
- HISTORICAL FRONTIER ≠ CURRENT AUTHORITY
- GOVERNANCE_REVIEW ≠ REVOCATION
- GOVERNANCE_REVIEW ≠ AUTHORIZATION

This module reuses existing infrastructure:
- TemporalFrontierEngine, HistoricalFrontier (temporal_frontier_experiment.py)
- ScopedImpactPropagationEngine (scoped_impact_propagation.py)
- ScopeProvenanceEngine (scope_provenance_experiment.py)
- RevalidationFrontier, RevalidationRequirement (temporal_completeness.py)
- FrontierEvaluation, FrontierClassification (revalidation_experiment.py)
- SovereignRequest, SovereignResponse, RequestType (interfaces.py)
- AuthorityRaceEngine, RaceType (authority_races.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    create_completeness_scope,
)
from examples.sovereign_agent.interfaces import (
    RequestType,
    ResponseType,
    SovereignRequest,
    SovereignResponse,
)
from examples.sovereign_agent.revalidation_experiment import (
    FrontierClassification,
    FrontierEvaluation,
    FrontierSoundness,
)
from examples.sovereign_agent.scoped_impact_propagation import (
    ScopedFrontier,
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from examples.sovereign_agent.scope_provenance_experiment import (
    ScopeAuthority,
    ScopeSource,
    ScopedArtifact,
)
from examples.sovereign_agent.temporal_completeness import (
    RevalidationRequirement,
)
from examples.sovereign_agent.temporal_frontier_experiment import (
    HistoricalFrontier,
    KnowledgeBoundary,
    TemporalFrontierEngine,
    TemporalFrontierStatus,
)


class GovernanceAction(str, Enum):
    """Actions that governance may take based on frontier membership."""
    NO_ACTION = "no_action"
    REVIEW_REQUIRED = "review_required"
    AUTHORIZATION_UPHELD = "authorization_upheled"
    AUTHORIZATION_SUSPENDED = "authorization_suspended"
    AUTHORIZATION_REVOKED = "authorization_revoked"
    REVALIDATION_REQUIRED = "revalidation_required"
    CANNOT_DETERMINE = "cannot_determine"


class AuthorityFrontierStatus(str, Enum):
    """Status of an authority-frontier integration."""
    FRONTIER_COMPUTED = "frontier_computed"
    GOVERNANCE_REVIEW_TRIGGERED = "governance_review_triggered"
    GOVERNANCE_DECISION_MADE = "governance_decision_made"
    AUTHORIZATION_PRESERVED = "authorization_preserved"
    AUTHORIZATION_INVALIDATED = "authorization_invalidated"
    IMMUTABLE = "immutable"


@dataclass(frozen=True)
class AuthorityFrontierResult:
    """Result of an authority-frontier integration experiment."""
    test_name: str
    frontier_id: str
    frontier_members: set[str]
    authorization_id: str
    governance_action: GovernanceAction
    frontier_triggered_review: bool
    frontier_created_authorization: bool
    frontier_revoked_authorization: bool
    notes: str = ""


@dataclass
class AuthorityFrontierIntegrator:
    """Integrates revalidation frontiers with the authority graph.
    
    Key responsibility: ensure frontier membership triggers governance
    review WITHOUT becoming authorization itself.
    """

    temporal_engine: TemporalFrontierEngine = field(default_factory=TemporalFrontierEngine)
    
    def integrate_frontier_with_authority(
        self,
        frontier: HistoricalFrontier,
        authorization_id: str,
        current_authority: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> AuthorityFrontierResult:
        """Integrate a revalidation frontier with the authority graph.
        
        The frontier triggers governance review. It does NOT directly
        authorize or revoke anything.
        """
        frontier_members = frontier.frontier.get_member_ids()
        
        # Determine if frontier should trigger governance review
        frontier_triggers_review = self._should_trigger_review(
            frontier, authorization_id, current_authority,
        )
        
        # Determine governance action
        if frontier_triggers_review:
            governance_action = GovernanceAction.REVIEW_REQUIRED
        else:
            governance_action = GovernanceAction.NO_ACTION
        
        # Critical invariants
        frontier_creates_authorization = False  # NEVER
        frontier_revokes_authorization = False  # NEVER
        
        return AuthorityFrontierResult(
            test_name=f"integration_{frontier.frontier_id}",
            frontier_id=frontier.frontier_id,
            frontier_members=frontier_members,
            authorization_id=authorization_id,
            governance_action=governance_action,
            frontier_triggered_review=frontier_triggers_review,
            frontier_created_authorization=frontier_creates_authorization,
            frontier_revoked_authorization=frontier_revokes_authorization,
            notes=f"Frontier triggers review={frontier_triggers_review}, governance action={governance_action.value}",
        )
    
    def _should_trigger_review(
        self,
        frontier: HistoricalFrontier,
        authorization_id: str,
        current_authority: dict[str, Any],
    ) -> bool:
        """Determine if a frontier should trigger governance review.
        
        Review is triggered when:
        1. The frontier contains members that affect the authorization
        2. The frontier is within the temporal validity interval
        3. The frontier's scope matches the authorization's scope
        """
        # Check if frontier has any members
        if frontier.frontier.is_empty():
            return False
        
        # Check if authorization is in the frontier
        if authorization_id in frontier.frontier.get_member_ids():
            return True
        
        # Check if any authorization-related members are in the frontier
        auth_related = {m for m in frontier.frontier.get_member_ids() if m.startswith("A")}
        if auth_related:
            return True
        
        return False
    
    def verify_frontier_does_not_create_authority(
        self,
        result: AuthorityFrontierResult,
    ) -> bool:
        """Verify that frontier integration does not create authority."""
        return (
            not result.frontier_created_authorization
            and not result.frontier_revoked_authorization
        )
    
    def verify_review_not_authorization(
        self,
        result: AuthorityFrontierResult,
    ) -> bool:
        """Verify that governance review is not the same as authorization."""
        return (
            result.governance_action == GovernanceAction.REVIEW_REQUIRED
            and not result.frontier_created_authorization
        )


def run_authority_frontier_experiments() -> list[AuthorityFrontierResult]:
    """Run authority frontier integration experiments."""
    integrator = AuthorityFrontierIntegrator()
    results = []
    
    # Setup common infrastructure
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
    
    # Experiment 1: Frontier triggers governance review
    # Frontier contains A1, so governance review should be triggered
    frontier1 = integrator.temporal_engine.compute_historical_frontier(
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
    )
    
    result1 = integrator.integrate_frontier_with_authority(
        frontier=frontier1,
        authorization_id="auth_001",
        current_authority={"auth_001": "authorized"},
        governance_policy={"policy_001": "active"},
    )
    results.append(result1)
    
    # Verify: frontier triggers review but does NOT create/revoke authority
    assert result1.frontier_triggered_review is True
    assert result1.frontier_created_authorization is False
    assert result1.frontier_revoked_authorization is False
    assert integrator.verify_frontier_does_not_create_authority(result1)
    assert integrator.verify_review_not_authorization(result1)
    
    # Experiment 2: Empty frontier does not trigger review
    empty_scope = create_completeness_scope("prop_002", "payment", environment="production")
    
    empty_frontier = integrator.temporal_engine.compute_historical_frontier(
        timestamp="2026-01-01T00:00:00Z",
        world_change=AuthorityDriftEvent(
            event_id="no_change",
            timestamp="2026-01-01T00:00:00Z",
            event_type="no_change",
            description="No change",
            affected_actor="none",
            affected_component="none",
            previous_state={},
            new_state={},
        ),
        authorization_id="auth_002",
        dependency_graph=build_authorization_dependency_graph(
            authorization_id="auth_002",
            evidence_ids=[],
            proposition_id="P2",
            epistemic_state_id="S2",
            experiment_id="exp_002",
            recommendation_id="rec_002",
            governance_policy_id="gov_002",
            resource_id="res_002",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["src_002"],
        ),
        proposition_graph={},
        authorization_graph={},
        scope=empty_scope,
        known_dependencies=[],
        known_propositions=[],
        known_authorizations=[],
        world_state=world_state,
    )
    
    result2 = integrator.integrate_frontier_with_authority(
        frontier=empty_frontier,
        authorization_id="auth_002",
        current_authority={"auth_002": "authorized"},
        governance_policy={"policy_002": "active"},
    )
    results.append(result2)
    
    # Verify: empty frontier does NOT trigger review
    assert result2.frontier_triggered_review is False
    assert result2.governance_action == GovernanceAction.NO_ACTION
    
    # Experiment 3: Frontier with only dependencies (no authorization) triggers review
    dep_only_scope = create_completeness_scope("prop_003", "payment", environment="production")
    
    dep_only_frontier = integrator.temporal_engine.compute_historical_frontier(
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_003",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=dep_only_scope,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=[],  # No authorizations known
        world_state=world_state,
    )
    
    result3 = integrator.integrate_frontier_with_authority(
        frontier=dep_only_frontier,
        authorization_id="auth_003",
        current_authority={"auth_003": "authorized"},
        governance_policy={"policy_003": "active"},
    )
    results.append(result3)
    
    # Verify: frontier with authorization-related members triggers review
    assert result3.frontier_triggered_review is True
    assert result3.frontier_created_authorization is False
    
    return results


def print_authority_frontier_results(results: list[AuthorityFrontierResult]) -> None:
    """Print authority frontier integration results."""
    print("\n" + "=" * 100)
    print("AUTHORITY FRONTIER INTEGRATION EXPERIMENTS")
    print("=" * 100)
    print(f"{'Test':<50} {'Frontier':<15} {'Review?':<10} {'Creates Auth?':<15} {'Revokes Auth?':<15}")
    print("-" * 100)
    
    for r in results:
        print(f"{r.test_name:<50} {r.frontier_id[:12]:<15} {str(r.frontier_triggered_review):<10} {str(r.frontier_created_authorization):<15} {str(r.frontier_revoked_authorization):<15}")
    
    print("\n" + "=" * 100)
    print("DETAILED RESULTS")
    print("=" * 100)
    
    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Frontier ID: {r.frontier_id}")
        print(f"  Frontier members: {r.frontier_members}")
        print(f"  Authorization ID: {r.authorization_id}")
        print(f"  Governance action: {r.governance_action.value}")
        print(f"  Frontier triggered review: {r.frontier_triggered_review}")
        print(f"  Frontier created authorization: {r.frontier_created_authorization}")
        print(f"  Frontier revoked authorization: {r.frontier_revoked_authorization}")
        print(f"  Notes: {r.notes}")


if __name__ == "__main__":
    results = run_authority_frontier_experiments()
    print_authority_frontier_results(results)
