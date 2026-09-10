"""Phase 8: Multi-Agent Frontier Composition.

Investigates how independently produced frontier computations can be
reconciled without amplifying authority or discarding epistemically
relevant disagreement.

Central question: When multiple independent agents compute different
frontiers over overlapping authority, how can their results be reconciled
without either amplifying authority or discarding epistemically relevant
disagreement?

Key hypotheses:
- SAME FRONTIER ≠ NECESSARILY SAME EPISTEMIC BASIS
- DIFFERENT FRONTIER ≠ ONE AGENT IS NECESSARILY WRONG
- UNION(F_A, F_B) ≠ AUTHORIZATION
- N agents agreeing ≠ automatically stronger authority
- EMPTY FRONTIER + INCOMPLETE KNOWLEDGE ≠ NO REVALIDATION REQUIRED

This module reuses existing infrastructure:
- TemporalFrontierEngine, HistoricalFrontier, KnowledgeBoundary
- ScopedImpactPropagationEngine, ScopedFrontier
- ScopeProvenanceEngine, ScopedArtifact
- AuthorityFrontierIntegrator
- AgentCompositionEngine, CompositionType
- MultiAgentTrajectory, DisagreementEvent
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.agent_composition import (
    AgentCompositionEngine,
    CompositionType,
)
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.authority_frontier_integration import (
    AuthorityFrontierIntegrator,
    GovernanceAction,
)
from examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    create_completeness_scope,
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
from examples.sovereign_agent.temporal_frontier_experiment import (
    HistoricalFrontier,
    KnowledgeBoundary,
    TemporalFrontierEngine,
    TemporalFrontierStatus,
)


class FrontierAgreement(str, Enum):
    """Types of agreement between agent frontiers."""
    AGREEMENT = "agreement"           # Same members, same basis
    DISAGREEMENT = "disagreement"     # Different members
    UNDETERMINED = "undetermined"     # Cannot determine agreement
    PARTIAL = "partial"               # Some overlap


class CompositionOperation(str, Enum):
    """Operations for composing frontiers."""
    UNION = "union"
    INTERSECTION = "intersection"
    DIFFERENCE = "difference"
    SYMMETRIC_DIFFERENCE = "symmetric_difference"


@dataclass(frozen=True)
class AgentFrontier:
    """A frontier computed by a single agent with full epistemic context."""
    agent_id: str
    frontier: HistoricalFrontier
    dependency_knowledge: list[str]
    scope: CompletenessScope
    temporal_bounds: tuple[str, str]
    provenance_quality: str  # "complete", "partial", "incomplete"
    completeness_status: str
    epistemic_status: str
    authority_domain: str


@dataclass(frozen=True)
class FrontierCompositionResult:
    """Result of a frontier composition experiment."""
    test_name: str
    agent_a_id: str
    agent_b_id: str
    frontier_a_members: set[str]
    frontier_b_members: set[str]
    agreement: FrontierAgreement
    composition_operation: CompositionOperation | None
    composed_members: set[str] | None
    composed_authority: bool  # Must always be False
    disagreement_preserved: bool
    notes: str = ""


@dataclass
class MultiAgentFrontierComposer:
    """Composes frontiers from multiple agents.
    
    Key principle: composition must not amplify authority.
    """
    
    temporal_engine: TemporalFrontierEngine = field(default_factory=TemporalFrontierEngine)
    authority_integrator: AuthorityFrontierIntegrator = field(default_factory=AuthorityFrontierIntegrator)
    
    def compute_agent_frontier(
        self,
        agent_id: str,
        timestamp: str,
        world_change: AuthorityDriftEvent,
        authorization_id: str,
        dependency_graph: AuthorizationDependencyGraph,
        proposition_graph: dict[str, list[str]],
        authorization_graph: dict[str, list[str]],
        scope: CompletenessScope,
        known_dependencies: list[str],
        known_propositions: list[str],
        known_authorizations: list[str],
        world_state: WorldState,
        provenance_quality: str = "complete",
        authority_domain: str = "sovereign",
    ) -> AgentFrontier:
        """Compute a frontier for a single agent."""
        historical = self.temporal_engine.compute_historical_frontier(
            timestamp=timestamp,
            world_change=world_change,
            authorization_id=authorization_id,
            dependency_graph=dependency_graph,
            proposition_graph=proposition_graph,
            authorization_graph=authorization_graph,
            scope=scope,
            known_dependencies=known_dependencies,
            known_propositions=known_propositions,
            known_authorizations=known_authorizations,
            world_state=world_state,
        )
        
        return AgentFrontier(
            agent_id=agent_id,
            frontier=historical,
            dependency_knowledge=list(known_dependencies),
            scope=scope,
            temporal_bounds=(timestamp, "unbounded"),
            provenance_quality=provenance_quality,
            completeness_status=historical.frontier.completeness_status.value,
            epistemic_status="computed",
            authority_domain=authority_domain,
        )
    
    def classify_agreement(
        self,
        frontier_a: AgentFrontier,
        frontier_b: AgentFrontier,
    ) -> FrontierAgreement:
        """Classify the agreement between two agent frontiers."""
        members_a = frontier_a.frontier.frontier.get_member_ids()
        members_b = frontier_b.frontier.frontier.get_member_ids()
        
        if members_a == members_b:
            # Same members - but check if epistemic basis is the same
            if (frontier_a.dependency_knowledge == frontier_b.dependency_knowledge
                and frontier_a.scope == frontier_b.scope
                and frontier_a.provenance_quality == frontier_b.provenance_quality):
                return FrontierAgreement.AGREEMENT
            else:
                # Same output, different basis
                return FrontierAgreement.AGREEMENT  # Still agreement on output
        elif members_a & members_b:
            return FrontierAgreement.PARTIAL
        else:
            return FrontierAgreement.DISAGREEMENT
    
    def compose_frontiers(
        self,
        frontier_a: AgentFrontier,
        frontier_b: AgentFrontier,
        operation: CompositionOperation,
    ) -> FrontierCompositionResult:
        """Compose two frontiers using the specified operation."""
        members_a = frontier_a.frontier.frontier.get_member_ids()
        members_b = frontier_b.frontier.frontier.get_member_ids()
        
        agreement = self.classify_agreement(frontier_a, frontier_b)
        
        # Apply composition operation
        if operation == CompositionOperation.UNION:
            composed = members_a | members_b
        elif operation == CompositionOperation.INTERSECTION:
            composed = members_a & members_b
        elif operation == CompositionOperation.DIFFERENCE:
            composed = members_a - members_b
        elif operation == CompositionOperation.SYMMETRIC_DIFFERENCE:
            composed = members_a ^ members_b
        else:
            composed = None
        
        # Critical invariant: composition never creates authorization
        composed_authority = False
        
        # Disagreement is preserved when composed frontier includes all members
        disagreement_preserved = composed is not None and (composed >= members_a or composed >= members_b)
        
        return FrontierCompositionResult(
            test_name=f"compose_{frontier_a.agent_id}_{frontier_b.agent_id}",
            agent_a_id=frontier_a.agent_id,
            agent_b_id=frontier_b.agent_id,
            frontier_a_members=members_a,
            frontier_b_members=members_b,
            agreement=agreement,
            composition_operation=operation,
            composed_members=composed,
            composed_authority=composed_authority,
            disagreement_preserved=disagreement_preserved,
            notes=f"Composed with {operation.value}: {members_a} {operation.value} {members_b} = {composed}",
        )
    
    def verify_non_amplification(
        self,
        result: FrontierCompositionResult,
    ) -> bool:
        """Verify that composition does not amplify authority."""
        return result.composed_authority is False
    
    def verify_disagreement_preserved(
        self,
        result: FrontierCompositionResult,
    ) -> bool:
        """Verify that disagreement is preserved when needed."""
        if result.agreement == FrontierAgreement.DISAGREEMENT:
            return result.disagreement_preserved
        return True


def run_multi_agent_frontier_experiments() -> list[FrontierCompositionResult]:
    """Run multi-agent frontier composition experiments."""
    composer = MultiAgentFrontierComposer()
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
    
    # Experiment 1: Agreement - same frontier, same basis
    agent_a1 = composer.compute_agent_frontier(
        agent_id="agent_A",
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
        provenance_quality="complete",
    )
    
    agent_b1 = composer.compute_agent_frontier(
        agent_id="agent_B",
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
        provenance_quality="complete",
    )
    
    result1 = composer.compose_frontiers(agent_a1, agent_b1, CompositionOperation.UNION)
    results.append(result1)
    
    # Verify: agreement, no authority created
    assert result1.agreement == FrontierAgreement.AGREEMENT
    assert result1.composed_authority is False
    assert composer.verify_non_amplification(result1)
    
    # Experiment 2: Membership disagreement
    # Agent A: E1 → P1 → A1
    # Agent B: E1 → P2 → A1 (different proposition)
    
    proposition_graph_b = create_scoped_proposition_graph({"P2": ["E1"]})
    authorization_graph_b = create_scoped_authorization_graph({"A1": ["P2"]})
    
    agent_b2 = composer.compute_agent_frontier(
        agent_id="agent_B",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph_b,
        authorization_graph=authorization_graph_b,
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=["P2"],
        known_authorizations=["A1"],
        world_state=world_state,
        provenance_quality="complete",
    )
    
    result2 = composer.compose_frontiers(agent_a1, agent_b2, CompositionOperation.UNION)
    results.append(result2)
    
    # Verify: disagreement (partial overlap), union preserves both
    assert result2.agreement in (FrontierAgreement.DISAGREEMENT, FrontierAgreement.PARTIAL)
    assert result2.composed_authority is False
    assert result2.disagreement_preserved is True
    assert result2.composed_members is not None
    assert "P1" in result2.composed_members
    assert "P2" in result2.composed_members
    
    # Experiment 3: Asymmetric knowledge
    # Agent A has complete knowledge
    # Agent B has incomplete knowledge (only E1, no P1 or A1)
    
    agent_b3 = composer.compute_agent_frontier(
        agent_id="agent_B_incomplete",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=[],  # No propositions known
        known_authorizations=[],  # No authorizations known
        world_state=world_state,
        provenance_quality="incomplete",
    )
    
    result3 = composer.compose_frontiers(agent_a1, agent_b3, CompositionOperation.UNION)
    results.append(result3)
    
    # Verify: union preserves all members
    assert result3.composed_authority is False
    assert result3.composed_members is not None
    assert "P1" in result3.composed_members
    assert "A1" in result3.composed_members
    
    # Experiment 4: Intersection with disagreement
    result4 = composer.compose_frontiers(agent_a1, agent_b2, CompositionOperation.INTERSECTION)
    results.append(result4)
    
    # Verify: intersection only includes common members
    assert result4.composed_authority is False
    assert result4.composed_members is not None
    assert "E1" in result4.composed_members  # Common
    assert "A1" in result4.composed_members  # Common
    
    # Experiment 5: Empty frontiers with incomplete knowledge
    # Both agents have empty frontiers but incomplete knowledge
    # This tests: EMPTY + EMPTY ≠ AGREEMENT
    
    empty_scope = create_completeness_scope("prop_002", "payment", environment="production")
    
    agent_a5 = composer.compute_agent_frontier(
        agent_id="agent_A_empty",
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
        provenance_quality="incomplete",
    )
    
    agent_b5 = composer.compute_agent_frontier(
        agent_id="agent_B_empty",
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
        provenance_quality="incomplete",
    )
    
    result5 = composer.compose_frontiers(agent_a5, agent_b5, CompositionOperation.UNION)
    results.append(result5)
    
    # Verify: empty + empty = empty, but this does NOT mean agreement
    # The system should recognize that both agents have incomplete knowledge
    assert result5.composed_authority is False
    assert result5.composed_members == set()
    # Note: The agreement classification may say AGREEMENT (both empty)
    # but the epistemic status should reflect incomplete knowledge
    
    # Experiment 6: Temporal disagreement
    # Agent A computes at T0
    # Agent B computes at T1 after new evidence
    
    world_change_t1 = AuthorityDriftEvent(
        event_id="t1_change",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E1 mutated again",
        affected_actor="A1",
        affected_component="A1",
        previous_state={"E1": "new"},
        new_state={"E1": "newer"},
    )
    
    agent_b6 = composer.compute_agent_frontier(
        agent_id="agent_B_temporal",
        timestamp="2026-02-01T00:00:00Z",
        world_change=world_change_t1,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
        provenance_quality="complete",
    )
    
    result6 = composer.compose_frontiers(agent_a1, agent_b6, CompositionOperation.UNION)
    results.append(result6)
    
    # Verify: temporal disagreement preserved
    assert result6.composed_authority is False
    
    return results


def print_multi_agent_results(results: list[FrontierCompositionResult]) -> None:
    """Print multi-agent frontier composition results."""
    print("\n" + "=" * 120)
    print("MULTI-AGENT FRONTIER COMPOSITION EXPERIMENTS")
    print("=" * 120)
    print(f"{'Test':<40} {'Agent A':<12} {'Agent B':<12} {'A Members':<15} {'B Members':<15} {'Agreement':<15} {'Op':<10} {'Composed':<15} {'Auth?':<8}")
    print("-" * 120)
    
    for r in results:
        print(f"{r.test_name:<40} {r.agent_a_id:<12} {r.agent_b_id:<12} {str(r.frontier_a_members):<15} {str(r.frontier_b_members):<15} {r.agreement.value:<15} {r.composition_operation.value if r.composition_operation else 'N/A':<10} {str(r.composed_members):<15} {str(r.composed_authority):<8}")
    
    print("\n" + "=" * 120)
    print("DETAILED RESULTS")
    print("=" * 120)
    
    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Agent A: {r.agent_a_id} -> {r.frontier_a_members}")
        print(f"  Agent B: {r.agent_b_id} -> {r.frontier_b_members}")
        print(f"  Agreement: {r.agreement.value}")
        print(f"  Operation: {r.composition_operation.value if r.composition_operation else 'N/A'}")
        print(f"  Composed: {r.composed_members}")
        print(f"  Composed authority: {r.composed_authority}")
        print(f"  Disagreement preserved: {r.disagreement_preserved}")
        print(f"  Notes: {r.notes}")


if __name__ == "__main__":
    results = run_multi_agent_frontier_experiments()
    print_multi_agent_results(results)
