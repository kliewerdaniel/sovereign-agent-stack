"""Phase 9: Frontier Composition Semantics.

Investigates whether frontier composition preserves the semantic information
required for governance to make legitimate decisions.

The central hypothesis: A frontier is not merely a set of artifact IDs.
It is a temporally and epistemically bounded claim about semantic impact.

Set operations (union, intersection) produce a membership projection that
may destroy precisely the information governance needs:
- Which agent identified each artifact
- Under what scope and temporal bounds
- With what evidence and provenance
- Under what completeness conditions

This module does NOT introduce a new abstraction until experiments
demonstrate the existing model cannot represent the required distinctions.

Existing infrastructure reused:
- HistoricalFrontier, KnowledgeBoundary, TemporalFrontierEngine
- ScopedFrontier, ScopedFrontierMember
- ScopeProvenanceEngine, ScopedArtifact
- AuthorityFrontierIntegrator
- DisagreementRecord, AgentDisagreementEngine
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.self_audit.continuous_reconciliation import WorldState
from research.examples.sovereign_agent.agent_disagreement import (
    AgentDisagreementEngine,
    DisagreementType,
)
from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependencyGraph,
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    create_completeness_scope,
)
from research.examples.sovereign_agent.scoped_impact_propagation import (
    ScopedFrontier,
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)
from research.examples.sovereign_agent.scope_provenance_experiment import (
    ScopeAuthority,
    ScopeSource,
    ScopedArtifact,
)
from research.examples.sovereign_agent.temporal_frontier_experiment import (
    HistoricalFrontier,
    KnowledgeBoundary,
    TemporalFrontierEngine,
    TemporalFrontierStatus,
)


class SemanticDisagreementType(str, Enum):
    """Types of disagreement that can occur between agent frontiers."""
    WORLD_DISAGREEMENT = "world_disagreement"
    EPISTEMIC_DISAGREEMENT = "epistemic_disagreement"
    SCOPE_DISAGREEMENT = "scope_disagreement"
    TEMPORAL_DISAGREEMENT = "temporal_disagreement"
    COMPUTATIONAL_DISAGREEMENT = "computational_disagreement"
    EVIDENCE_DISAGREEMENT = "evidence_disagreement"
    PROVENANCE_DISAGREEMENT = "provenance_disagreement"
    COMPLETENESS_DISAGREEMENT = "completeness_disagreement"
    ALGORITHMIC_DISAGREEMENT = "algorithmic_disagagement"
    UNKNOWN = "unknown"


class CompositionOperation(str, Enum):
    """Operations for composing frontiers."""
    UNION = "union"
    INTERSECTION = "intersection"
    PROVENANCE_PRESERVING_UNION = "provenance_preserving_union"
    PROVENANCE_PRESERVING_INTERSECTION = "provenance_preserving_intersection"


@dataclass(frozen=True)
class RichFrontierMember:
    """A single frontier member with full semantic context.
    
    This represents the claim "artifact X is in the frontier" with all
    the epistemic context needed to evaluate that claim.
    """
    artifact_id: str
    artifact_type: str
    agent_id: str
    evidence_basis: list[str]
    scope: CompletenessScope
    temporal_bounds: tuple[str, str]
    provenance: list[str]
    provenance_quality: str
    completeness_status: str
    epistemic_status: str


@dataclass(frozen=True)
class RichFrontier:
    """A frontier with full semantic context.
    
    This is the epistemically rich representation that a set projection
    ({E1,P1,A1}) throws away.
    """
    frontier_id: str
    agent_id: str
    timestamp: str
    members: list[RichFrontierMember]
    knowledge_boundary: KnowledgeBoundary
    scope: CompletenessScope
    temporal_bounds: tuple[str, str]
    provenance_quality: str
    completeness_status: str
    epistemic_status: str
    authority_domain: str
    world_state_hash: str
    
    def get_member_ids(self) -> set[str]:
        """Get the set projection of this frontier.
        
        This is the lossy representation used for set operations.
        """
        return {m.artifact_id for m in self.members}
    
    def get_member(self, artifact_id: str) -> Optional[RichFrontierMember]:
        """Get a specific member by ID."""
        for m in self.members:
            if m.artifact_id == artifact_id:
                return m
        return None
    
    def get_members_by_evidence(self, evidence_id: str) -> list[RichFrontierMember]:
        """Get all members that depend on a specific evidence."""
        return [m for m in self.members if evidence_id in m.evidence_basis]


@dataclass(frozen=True)
class MemberProvenance:
    """Provenance for a single member in a composed frontier."""
    artifact_id: str
    agents: list[str]
    evidence_basis: list[str]
    scopes: list[CompletenessScope]
    temporal_bounds: list[tuple[str, str]]
    provenance_chains: list[list[str]]
    provenance_qualities: list[str]
    completeness_statuses: list[str]
    epistemic_statuses: list[str]


@dataclass(frozen=True)
class ProvenancePreservingComposition:
    """A composition that preserves the origin of each membership."""
    composition_id: str
    operation: CompositionOperation
    agent_a_id: str
    agent_b_id: str
    composed_members: set[str]
    member_provenance: dict[str, MemberProvenance]
    information_lost: bool
    information_loss_details: list[str]
    semantic_disagreements: list[SemanticDisagreementType]
    
    def get_member_agents(self, artifact_id: str) -> list[str]:
        """Get the agents that identified a specific artifact."""
        if artifact_id in self.member_provenance:
            return self.member_provenance[artifact_id].agents
        return []
    
    def get_member_evidence(self, artifact_id: str) -> list[str]:
        """Get the evidence basis for a specific artifact."""
        if artifact_id in self.member_provenance:
            return self.member_provenance[artifact_id].evidence_basis
        return []


@dataclass(frozen=True)
class CompositionComparisonResult:
    """Comparison of set composition vs provenance-preserving composition."""
    test_name: str
    agent_a_id: str
    agent_b_id: str
    set_composition_members: set[str]
    provenance_composition_members: set[str]
    information_lost: bool
    information_loss_details: list[str]
    semantic_disagreements: list[SemanticDisagreementType]
    notes: str = ""


@dataclass
class FrontierCompositionSemanticsEngine:
    """Engine for investigating frontier composition semantics.
    
    Tests whether set operations preserve the semantic information
    required for governance decisions.
    """
    
    temporal_engine: TemporalFrontierEngine = field(default_factory=TemporalFrontierEngine)
    disagreement_engine: AgentDisagreementEngine = field(default_factory=AgentDisagreementEngine)
    
    def compute_rich_frontier(
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
        evidence_basis: list[str] | None = None,
    ) -> RichFrontier:
        """Compute a rich frontier with full semantic context."""
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
        
        # Build rich members
        rich_members = []
        for member in historical.frontier.members:
            rich_members.append(RichFrontierMember(
                artifact_id=member.artifact_id,
                artifact_type=member.artifact_type,
                agent_id=agent_id,
                evidence_basis=evidence_basis or list(known_dependencies),
                scope=member.scope,
                temporal_bounds=(timestamp, "unbounded"),
                provenance=historical.frontier.provenance_chain,
                provenance_quality=provenance_quality,
                completeness_status=historical.frontier.completeness_status.value,
                epistemic_status="computed",
            ))
        
        return RichFrontier(
            frontier_id=historical.frontier_id,
            agent_id=agent_id,
            timestamp=timestamp,
            members=rich_members,
            knowledge_boundary=historical.knowledge_boundary,
            scope=scope,
            temporal_bounds=(timestamp, "unbounded"),
            provenance_quality=provenance_quality,
            completeness_status=historical.frontier.completeness_status.value,
            epistemic_status="computed",
            authority_domain=authority_domain,
            world_state_hash=str(hash(str(world_state.static_topology))),
        )
    
    def compose_provenance_preserving(
        self,
        frontier_a: RichFrontier,
        frontier_b: RichFrontier,
        operation: CompositionOperation,
    ) -> ProvenancePreservingComposition:
        """Compose two frontiers preserving provenance information."""
        members_a = frontier_a.get_member_ids()
        members_b = frontier_b.get_member_ids()
        
        # Compute set composition
        if operation in (CompositionOperation.UNION, CompositionOperation.PROVENANCE_PRESERVING_UNION):
            composed = members_a | members_b
        elif operation in (CompositionOperation.INTERSECTION, CompositionOperation.PROVENANCE_PRESERVING_INTERSECTION):
            composed = members_a & members_b
        else:
            composed = set()
        
        # Build member provenance
        member_provenance = {}
        for artifact_id in composed:
            agents = []
            evidence_basis = []
            scopes = []
            temporal_bounds = []
            provenance_chains = []
            provenance_qualities = []
            completeness_statuses = []
            epistemic_statuses = []
            
            mem_a = frontier_a.get_member(artifact_id)
            mem_b = frontier_b.get_member(artifact_id)
            
            if mem_a:
                agents.append(mem_a.agent_id)
                evidence_basis.extend(mem_a.evidence_basis)
                scopes.append(mem_a.scope)
                temporal_bounds.append(mem_a.temporal_bounds)
                provenance_chains.append(mem_a.provenance)
                provenance_qualities.append(mem_a.provenance_quality)
                completeness_statuses.append(mem_a.completeness_status)
                epistemic_statuses.append(mem_a.epistemic_status)
            
            if mem_b:
                agents.append(mem_b.agent_id)
                evidence_basis.extend(mem_b.evidence_basis)
                scopes.append(mem_b.scope)
                temporal_bounds.append(mem_b.temporal_bounds)
                provenance_chains.append(mem_b.provenance)
                provenance_qualities.append(mem_b.provenance_quality)
                completeness_statuses.append(mem_b.completeness_status)
                epistemic_statuses.append(mem_b.epistemic_status)
            
            member_provenance[artifact_id] = MemberProvenance(
                artifact_id=artifact_id,
                agents=agents,
                evidence_basis=list(set(evidence_basis)),
                scopes=scopes,
                temporal_bounds=temporal_bounds,
                provenance_chains=provenance_chains,
                provenance_qualities=provenance_qualities,
                completeness_statuses=completeness_statuses,
                epistemic_statuses=epistemic_statuses,
            )
        
        # Detect information loss
        information_lost = False
        information_loss_details = []
        semantic_disagreements = []
        
        # Check for scope disagreement
        if frontier_a.scope != frontier_b.scope:
            information_lost = True
            information_loss_details.append(
                f"Scope disagreement: {frontier_a.scope.environment} vs {frontier_b.scope.environment}"
            )
            semantic_disagreements.append(SemanticDisagreementType.SCOPE_DISAGREEMENT)
        
        # Check for temporal disagreement
        if frontier_a.temporal_bounds[0] != frontier_b.temporal_bounds[0]:
            information_lost = True
            information_loss_details.append(
                f"Temporal disagreement: {frontier_a.temporal_bounds[0]} vs {frontier_b.temporal_bounds[0]}"
            )
            semantic_disagreements.append(SemanticDisagreementType.TEMPORAL_DISAGREEMENT)
        
        # Check for provenance quality disagreement
        if frontier_a.provenance_quality != frontier_b.provenance_quality:
            information_lost = True
            information_loss_details.append(
                f"Provenance quality disagreement: {frontier_a.provenance_quality} vs {frontier_b.provenance_quality}"
            )
            semantic_disagreements.append(SemanticDisagreementType.PROVENANCE_DISAGREEMENT)
        
        # Check for completeness disagreement
        if frontier_a.completeness_status != frontier_b.completeness_status:
            information_lost = True
            information_loss_details.append(
                f"Completeness disagreement: {frontier_a.completeness_status} vs {frontier_b.completeness_status}"
            )
            semantic_disagreements.append(SemanticDisagreementType.COMPLETENESS_DISAGREEMENT)
        
        # Check for membership disagreement
        if members_a != members_b:
            semantic_disagreements.append(SemanticDisagreementType.EPISTEMIC_DISAGREEMENT)
        
        # Check for evidence disagreement (same frontier, different evidence)
        if members_a == members_b:
            evidence_a = set()
            evidence_b = set()
            for m in frontier_a.members:
                evidence_a.update(m.evidence_basis)
            for m in frontier_b.members:
                evidence_b.update(m.evidence_basis)
            if evidence_a != evidence_b:
                information_lost = True
                information_loss_details.append(
                    f"Evidence disagreement: {evidence_a} vs {evidence_b}"
                )
                semantic_disagreements.append(SemanticDisagreementType.EVIDENCE_DISAGREEMENT)
        
        return ProvenancePreservingComposition(
            composition_id=f"comp_{uuid.uuid4().hex[:12]}",
            operation=operation,
            agent_a_id=frontier_a.agent_id,
            agent_b_id=frontier_b.agent_id,
            composed_members=composed,
            member_provenance=member_provenance,
            information_lost=information_lost,
            information_loss_details=information_loss_details,
            semantic_disagreements=semantic_disagreements,
        )
    
    def compare_compositions(
        self,
        frontier_a: RichFrontier,
        frontier_b: RichFrontier,
    ) -> CompositionComparisonResult:
        """Compare set composition vs provenance-preserving composition."""
        set_union = frontier_a.get_member_ids() | frontier_b.get_member_ids()
        set_intersection = frontier_a.get_member_ids() & frontier_b.get_member_ids()
        
        prov_union = self.compose_provenance_preserving(
            frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
        )
        
        return CompositionComparisonResult(
            test_name=f"compare_{frontier_a.agent_id}_{frontier_b.agent_id}",
            agent_a_id=frontier_a.agent_id,
            agent_b_id=frontier_b.agent_id,
            set_composition_members=set_union,
            provenance_composition_members=prov_union.composed_members,
            information_lost=prov_union.information_lost,
            information_loss_details=prov_union.information_loss_details,
            semantic_disagreements=prov_union.semantic_disagreements,
            notes=f"Set union has {len(set_union)} members, provenance-preserving has {len(prov_union.composed_members)} members",
        )


def run_identical_frontier_different_evidence() -> CompositionComparisonResult:
    """Experiment 1: Identical frontier, different evidence."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, evidence=EA
    frontier_a = engine.compute_rich_frontier(
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
        evidence_basis=["EA"],
    )
    
    # Agent B: frontier={E1,P1,A1}, evidence=EB (materially different)
    frontier_b = engine.compute_rich_frontier(
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
        evidence_basis=["EB"],
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_identical_frontier_different_completeness() -> CompositionComparisonResult:
    """Experiment 2: Identical frontier, different completeness."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, complete dependency knowledge
    frontier_a = engine.compute_rich_frontier(
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
    
    # Agent B: frontier={E1,P1,A1}, incomplete dependency knowledge
    frontier_b = engine.compute_rich_frontier(
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
        provenance_quality="incomplete",
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_identical_frontier_different_scope() -> CompositionComparisonResult:
    """Experiment 3: Identical frontier, different scope."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, scope=production
    frontier_a = engine.compute_rich_frontier(
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
    )
    
    # Agent B: frontier={E1,P1,A1}, scope=staging
    frontier_b = engine.compute_rich_frontier(
        agent_id="agent_B",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope_b,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_identical_frontier_different_temporal() -> CompositionComparisonResult:
    """Experiment 4: Identical frontier, different temporal validity."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, temporal=[T0,T1]
    frontier_a = engine.compute_rich_frontier(
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
    )
    
    # Agent B: frontier={E1,P1,A1}, temporal=[T1,T2]
    frontier_b = engine.compute_rich_frontier(
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
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_identical_frontier_different_provenance() -> CompositionComparisonResult:
    """Experiment 5: Identical frontier, different provenance quality."""
    engine = FrontierCompositionSemanticsEngine()
    
    scope = create_completeness_scope("prop_001", "payment", environment="production")
    
    dep_graph_a = build_authorization_dependency_graph(
        authorization_id="auth_001",
        evidence_ids=["E1"],
        proposition_id="P1",
        epistemic_state_id="S1",
        experiment_id="exp_001",
        recommendation_id="rec_001",
        governance_policy_id="gov_001",
        resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01",
        provenance=["src_001", "src_002", "src_003"],  # Complete provenance
    )
    
    dep_graph_b = build_authorization_dependency_graph(
        authorization_id="auth_001",
        evidence_ids=["E1"],
        proposition_id="P1",
        epistemic_state_id="S1",
        experiment_id="exp_001",
        recommendation_id="rec_001",
        governance_policy_id="gov_001",
        resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01",
        provenance=["src_001"],  # Incomplete provenance
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
    
    # Agent A: frontier={E1,P1,A1}, complete provenance
    frontier_a = engine.compute_rich_frontier(
        agent_id="agent_A",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph_a,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
        provenance_quality="complete",
    )
    
    # Agent B: frontier={E1,P1,A1}, incomplete provenance
    frontier_b = engine.compute_rich_frontier(
        agent_id="agent_B",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph_b,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
        provenance_quality="incomplete",
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_different_frontier_same_world_evidence() -> CompositionComparisonResult:
    """Experiment 6: Different frontier, same world evidence.
    
    Tests whether different outputs imply different worlds.
    """
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}
    frontier_a = engine.compute_rich_frontier(
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
    )
    
    # Agent B: frontier={E1,P2,A1} (different proposition, same evidence)
    proposition_graph_b = create_scoped_proposition_graph({"P2": ["E1"]})
    authorization_graph_b = create_scoped_authorization_graph({"A1": ["P2"]})
    
    frontier_b = engine.compute_rich_frontier(
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
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_different_frontier_granularity() -> CompositionComparisonResult:
    """Experiment 7: Different frontier, different propagation granularity."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}
    frontier_a = engine.compute_rich_frontier(
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
    )
    
    # Agent B: frontier={E1,P1} (different granularity - no authorization)
    frontier_b = engine.compute_rich_frontier(
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
        known_authorizations=[],  # No authorizations
        world_state=world_state,
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_provenance_preserving_union() -> ProvenancePreservingComposition:
    """Experiment 8: Provenance-preserving union."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, evidence=EA
    frontier_a = engine.compute_rich_frontier(
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
        evidence_basis=["EA"],
    )
    
    # Agent B: frontier={E1,P2,A1}, evidence=EB
    proposition_graph_b = create_scoped_proposition_graph({"P2": ["E1"]})
    authorization_graph_b = create_scoped_authorization_graph({"A1": ["P2"]})
    
    frontier_b = engine.compute_rich_frontier(
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
        evidence_basis=["EB"],
    )
    
    return engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
    )


def run_provenance_preserving_intersection() -> ProvenancePreservingComposition:
    """Experiment 9: Provenance-preserving intersection."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, evidence=EA
    frontier_a = engine.compute_rich_frontier(
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
        evidence_basis=["EA"],
    )
    
    # Agent B: frontier={E1,P2,A1}, evidence=EB
    proposition_graph_b = create_scoped_proposition_graph({"P2": ["E1"]})
    authorization_graph_b = create_scoped_authorization_graph({"A1": ["P2"]})
    
    frontier_b = engine.compute_rich_frontier(
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
        evidence_basis=["EB"],
    )
    
    return engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_INTERSECTION
    )


def run_evidence_correlation() -> CompositionComparisonResult:
    """Experiment 10: Evidence correlation - same evidence vs independent evidence."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, evidence=E1
    frontier_a = engine.compute_rich_frontier(
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
        evidence_basis=["E1"],
    )
    
    # Agent B: frontier={E1,P1,A1}, evidence=E1 (SAME evidence - not independent)
    frontier_b = engine.compute_rich_frontier(
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
        evidence_basis=["E1"],  # Same evidence, not independent
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_adversarial_empty_frontier() -> CompositionComparisonResult:
    """Experiment 11: Adversarial - empty frontier."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}
    frontier_a = engine.compute_rich_frontier(
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
    )
    
    # Agent B: empty frontier (adversarial)
    frontier_b = engine.compute_rich_frontier(
        agent_id="agent_B_adversarial",
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
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph={},
        authorization_graph={},
        scope=scope,
        known_dependencies=[],
        known_propositions=[],
        known_authorizations=[],
        world_state=world_state,
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_adversarial_scope_widened() -> CompositionComparisonResult:
    """Experiment 12: Adversarial - scope widened."""
    engine = FrontierCompositionSemanticsEngine()
    
    scope_production = create_completeness_scope("prop_001", "payment", environment="production")
    scope_wide = create_completeness_scope("prop_001", "payment", environment="*")  # Wildcard scope
    
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
    
    # Agent A: frontier={E1,P1,A1}, scope=production
    frontier_a = engine.compute_rich_frontier(
        agent_id="agent_A",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope_production,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
    )
    
    # Agent B: frontier={E1,P1,A1}, scope=* (widened - adversarial)
    frontier_b = engine.compute_rich_frontier(
        agent_id="agent_B_scope_widened",
        timestamp="2026-01-01T00:00:00Z",
        world_change=world_change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope_wide,
        known_dependencies=["E1"],
        known_propositions=["P1"],
        known_authorizations=["A1"],
        world_state=world_state,
    )
    
    return engine.compare_compositions(frontier_a, frontier_b)


def run_malicious_agreement() -> ProvenancePreservingComposition:
    """Experiment 13: Malicious agreement - N identical incorrect frontiers."""
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}
    frontier_a = engine.compute_rich_frontier(
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
    )
    
    # Agent B: frontier={E1,P1,A1} (identical - potentially malicious agreement)
    frontier_b = engine.compute_rich_frontier(
        agent_id="agent_B_malicious",
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
    
    return engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
    )


def run_composition_information_loss() -> dict[str, Any]:
    """Experiment 14: Composition information-loss measurement.
    
    The central experiment. Measures what semantic information survives
    set composition.
    """
    engine = FrontierCompositionSemanticsEngine()
    
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
    
    # Agent A: frontier={E1,P1,A1}, evidence=EA, scope=production, temporal=T0
    frontier_a = engine.compute_rich_frontier(
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
        evidence_basis=["EA"],
        provenance_quality="complete",
    )
    
    # Agent B: frontier={E1,P2,A1}, evidence=EB, scope=staging, temporal=T1
    scope_b = create_completeness_scope("prop_001", "payment", environment="staging")
    proposition_graph_b = create_scoped_proposition_graph({"P2": ["E1"]})
    authorization_graph_b = create_scoped_authorization_graph({"A1": ["P2"]})
    
    frontier_b = engine.compute_rich_frontier(
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
        proposition_graph=proposition_graph_b,
        authorization_graph=authorization_graph_b,
        scope=scope_b,
        known_dependencies=["E1"],
        known_propositions=["P2"],
        known_authorizations=["A1"],
        world_state=WorldState(timestamp="2026-02-01T00:00:00Z"),
        evidence_basis=["EB"],
        provenance_quality="partial",
    )
    
    # Measure information loss
    set_union = frontier_a.get_member_ids() | frontier_b.get_member_ids()
    prov_union = engine.compose_provenance_preserving(
        frontier_a, frontier_b, CompositionOperation.PROVENANCE_PRESERVING_UNION
    )
    
    # Information in RichFrontier that is NOT in set representation
    rich_info = {
        "agent_count": len(set(m.agent_id for m in frontier_a.members + frontier_b.members)),
        "evidence_bases": len(set(
            m.evidence_basis[0] for m in frontier_a.members + frontier_b.members if m.evidence_basis
        )),
        "scopes": len(set(m.scope.environment for m in frontier_a.members + frontier_b.members)),
        "temporal_bounds": len(set(m.temporal_bounds[0] for m in frontier_a.members + frontier_b.members)),
        "provenance_qualities": len(set(
            m.provenance_quality for m in frontier_a.members + frontier_b.members
        )),
        "completeness_statuses": len(set(
            m.completeness_status for m in frontier_a.members + frontier_b.members
        )),
    }
    
    # Information in set representation
    set_info = {
        "member_count": len(set_union),
    }
    
    # Information in provenance-preserving representation
    prov_info = {
        "member_count": len(prov_union.composed_members),
        "members_with_multiple_agents": sum(
            1 for mp in prov_union.member_provenance.values() if len(mp.agents) > 1
        ),
        "members_with_multiple_evidence": sum(
            1 for mp in prov_union.member_provenance.values() if len(mp.evidence_basis) > 1
        ),
        "semantic_disagreements": len(prov_union.semantic_disagreements),
    }
    
    return {
        "rich_information": rich_info,
        "set_information": set_info,
        "provenance_information": prov_info,
        "information_lost": prov_union.information_lost,
        "information_loss_details": prov_union.information_loss_details,
        "semantic_disagreements": [s.value for s in prov_union.semantic_disagreements],
    }


def run_all_semantics_experiments() -> dict[str, Any]:
    """Run all frontier composition semantics experiments."""
    results = {}
    
    results["identical_frontier_different_evidence"] = run_identical_frontier_different_evidence()
    results["identical_frontier_different_completeness"] = run_identical_frontier_different_completeness()
    results["identical_frontier_different_scope"] = run_identical_frontier_different_scope()
    results["identical_frontier_different_temporal"] = run_identical_frontier_different_temporal()
    results["identical_frontier_different_provenance"] = run_identical_frontier_different_provenance()
    results["different_frontier_same_world_evidence"] = run_different_frontier_same_world_evidence()
    results["different_frontier_granularity"] = run_different_frontier_granularity()
    results["provenance_preserving_union"] = run_provenance_preserving_union()
    results["provenance_preserving_intersection"] = run_provenance_preserving_intersection()
    results["evidence_correlation"] = run_evidence_correlation()
    results["adversarial_empty_frontier"] = run_adversarial_empty_frontier()
    results["adversarial_scope_widened"] = run_adversarial_scope_widened()
    results["malicious_agreement"] = run_malicious_agreement()
    results["composition_information_loss"] = run_composition_information_loss()
    
    return results


def print_semantics_results(results: dict[str, Any]) -> None:
    """Print frontier composition semantics results."""
    print("\n" + "=" * 120)
    print("FRONTIER COMPOSITION SEMANTICS EXPERIMENTS")
    print("=" * 120)
    
    for name, result in results.items():
        print(f"\n{name}:")
        if isinstance(result, CompositionComparisonResult):
            print(f"  Agent A: {result.agent_a_id}")
            print(f"  Agent B: {result.agent_b_id}")
            print(f"  Set composition: {result.set_composition_members}")
            print(f"  Provenance composition: {result.provenance_composition_members}")
            print(f"  Information lost: {result.information_lost}")
            if result.information_loss_details:
                print(f"  Loss details: {result.information_loss_details}")
            if result.semantic_disagreements:
                print(f"  Semantic disagreements: {[s.value for s in result.semantic_disagreements]}")
        elif isinstance(result, ProvenancePreservingComposition):
            print(f"  Operation: {result.operation.value}")
            print(f"  Composed members: {result.composed_members}")
            print(f"  Information lost: {result.information_lost}")
            if result.information_loss_details:
                print(f"  Loss details: {result.information_loss_details}")
            if result.semantic_disagreements:
                print(f"  Semantic disagreements: {[s.value for s in result.semantic_disagreements]}")
            print(f"  Member provenance:")
            for artifact_id, mp in result.member_provenance.items():
                print(f"    {artifact_id}: agents={mp.agents}, evidence={mp.evidence_basis}")
        elif isinstance(result, dict):
            for k, v in result.items():
                print(f"  {k}: {v}")


if __name__ == "__main__":
    results = run_all_semantics_experiments()
    print_semantics_results(results)
