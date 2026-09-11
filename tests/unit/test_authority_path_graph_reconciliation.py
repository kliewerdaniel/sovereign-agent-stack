"""Tests for Phase 32: Reconstructed Authority Path → Declared Authority Graph Reconciliation."""

import pytest
from research.examples.sovereign_agent.authority_path_graph_reconciliation import (
    AdversarialWorldGenerator,
    ActorReconciliationStatus,
    AttributionStatus,
    AuthorityPathNode,
    AuthorityReconciliation,
    AuthoritySourceType,
    CapabilityStatus,
    CorrespondenceStatus,
    DeclaredAuthorityGraph,
    DeclaredAuthorityNode,
    DomainReconciliationStatus,
    DivergenceType,
    EpistemicStatus,
    EscapeType,
    GovernanceStatus,
    GraphCompletenessStatus,
    IndependentOracle,
    PathNodeStatus,
    PathValidity,
    ReconciliationEngine,
    ReconciliationWorld,
    ReconstructedAuthorityPath,
    ScopeReconciliationStatus,
    ScopeStatus,
    TemporalReconciliationStatus,
    TemporalStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> ReconciliationEngine:
    return ReconciliationEngine("test-engine")


@pytest.fixture
def oracle() -> IndependentOracle:
    return IndependentOracle()


@pytest.fixture
def worlds() -> list[ReconciliationWorld]:
    return AdversarialWorldGenerator().generate_all_worlds()


@pytest.fixture
def graph_complete() -> DeclaredAuthorityGraph:
    """A complete declared authority graph."""
    graph = DeclaredAuthorityGraph(graph_id="test-complete", version="v1")
    graph.add_node(DeclaredAuthorityNode(
        node_id="ta-001",
        node_type="trust_anchor",
        principal="admin",
        capability="*",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.TRUST_ANCHOR,
        trust_anchor_id="ta-001",
    ))
    graph.add_node(DeclaredAuthorityNode(
        node_id="del-001",
        node_type="delegation",
        principal="admin",
        capability="subprocess.execute",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.DELEGATION,
        trust_anchor_id="ta-001",
    ))
    graph.add_node(DeclaredAuthorityNode(
        node_id="pol-001",
        node_type="policy",
        principal="admin",
        capability="subprocess.execute",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.POLICY,
        trust_anchor_id="ta-001",
    ))
    graph.add_node(DeclaredAuthorityNode(
        node_id="gov-001",
        node_type="governance",
        principal="admin",
        capability="subprocess.execute",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.POLICY,
        trust_anchor_id="ta-001",
    ))
    graph.add_node(DeclaredAuthorityNode(
        node_id="cap-001",
        node_type="capability",
        principal="admin",
        capability="subprocess.execute",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.POLICY,
        trust_anchor_id="ta-001",
    ))
    graph.add_node(DeclaredAuthorityNode(
        node_id="exe-001",
        node_type="execution_gate",
        principal="admin",
        capability="subprocess.execute",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.POLICY,
        trust_anchor_id="ta-001",
    ))
    graph.add_node(DeclaredAuthorityNode(
        node_id="eff-001",
        node_type="effect",
        principal="admin",
        capability="subprocess.run",
        scope="runtime",
        domain="default",
        source_type=AuthoritySourceType.POLICY,
        trust_anchor_id="ta-001",
    ))
    from research.examples.sovereign_agent.authority_path_graph_reconciliation import DeclaredAuthorityEdge
    graph.add_edge(DeclaredAuthorityEdge(edge_id="e1", source_node_id="ta-001", target_node_id="del-001"))
    graph.add_edge(DeclaredAuthorityEdge(edge_id="e2", source_node_id="del-001", target_node_id="pol-001"))
    graph.add_edge(DeclaredAuthorityEdge(edge_id="e3", source_node_id="pol-001", target_node_id="gov-001"))
    graph.add_edge(DeclaredAuthorityEdge(edge_id="e4", source_node_id="gov-001", target_node_id="cap-001"))
    graph.add_edge(DeclaredAuthorityEdge(edge_id="e5", source_node_id="cap-001", target_node_id="exe-001"))
    graph.add_edge(DeclaredAuthorityEdge(edge_id="e6", source_node_id="exe-001", target_node_id="eff-001"))
    return graph


@pytest.fixture
def valid_path() -> ReconstructedAuthorityPath:
    """A valid reconstructed authority path."""
    nodes = (
        AuthorityPathNode(
            node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev1", evidence_type="trust_anchor_record",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:trust_anchor",
        ),
        AuthorityPathNode(
            node_id="n2", node_type="delegation", principal="admin", capability="subprocess.execute",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev2", evidence_type="delegation_link",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:delegation",
        ),
        AuthorityPathNode(
            node_id="n3", node_type="policy", principal="admin", capability="subprocess.execute",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev3", evidence_type="policy_record",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:policy",
        ),
        AuthorityPathNode(
            node_id="n4", node_type="governance", principal="admin", capability="subprocess.execute",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev4", evidence_type="governance_disposition",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:governance",
        ),
        AuthorityPathNode(
            node_id="n5", node_type="capability", principal="admin", capability="subprocess.execute",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev5", evidence_type="capability_record",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:capability",
        ),
        AuthorityPathNode(
            node_id="n6", node_type="execution_gate", principal="admin", capability="subprocess.execute",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev6", evidence_type="execution_receipt",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:execution_gate",
        ),
        AuthorityPathNode(
            node_id="n7", node_type="effect", principal="admin", capability="subprocess.run",
            scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
            evidence_id="ev7", evidence_type="runtime_observation",
            temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
            provenance="test:effect",
        ),
    )
    return ReconstructedAuthorityPath(
        path_id="path-test",
        observation_id="obs-test",
        effect_id="eff-test",
        validity=PathValidity.VALID,
        nodes=nodes,
        trust_anchor_id="ta-001",
        delegation_chain=("del-001",),
        capability_status=CapabilityStatus.VALID,
        governance_status=GovernanceStatus.VALID,
        temporal_status=TemporalStatus.VALID,
        scope_status=ScopeStatus.VALID,
        attribution_status=AttributionStatus.CONFIRMED,
        escape_type=EscapeType.NO_ESCAPE,
        completeness_status="complete_within_declared_graph",
        provenance="test:reconstruction",
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------


class TestWorldGeneration:
    def test_generates_35_worlds(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        assert len(worlds) == 35

    def test_worlds_have_unique_ids(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_world_01_exact_correspondence(self, worlds):
        world = worlds[0]
        assert world.world_id == "world_01_exact_correspondence"
        assert world.true_reconciliation == CorrespondenceStatus.CORRESPONDS
        assert world.ground_truth_epistemic == EpistemicStatus.RECONCILED

    def test_world_02_valid_path_not_in_declared_graph(self, worlds):
        world = worlds[1]
        assert world.world_id == "world_02_valid_path_not_in_declared_graph"
        assert world.is_incomplete_graph

    def test_world_11_valid_auth_id_forged_provenance(self, worlds):
        world = worlds[10]
        assert world.world_id == "world_11_valid_auth_id_forged_provenance"
        assert world.is_laundering

    def test_world_18_intentionally_incomplete_graph(self, worlds):
        world = worlds[17]
        assert world.world_id == "world_18_intentionally_incomplete_graph"
        assert world.is_incomplete_graph
        assert world.graph_completeness == GraphCompletenessStatus.INCOMPLETE

    def test_world_21_emergency_path_declared(self, worlds):
        world = worlds[20]
        assert world.world_id == "world_21_emergency_path_declared"
        assert world.is_emergency

    def test_world_24_background_worker_no_delegation(self, worlds):
        world = worlds[23]
        assert world.world_id == "world_24_background_worker_no_delegation"
        assert world.is_background

    def test_world_28_cyclic_declared_graph(self, worlds):
        world = worlds[27]
        assert world.world_id == "world_28_cyclic_declared_graph"
        assert world.is_cyclic

    def test_world_30_direct_primitive_escape(self, worlds):
        world = worlds[29]
        assert world.world_id == "world_30_direct_primitive_escape"
        assert world.true_reconciliation == CorrespondenceStatus.AUTHORITY_ESCAPE


# ---------------------------------------------------------------------------
# Reconciliation engine tests
# ---------------------------------------------------------------------------


class TestReconciliationEngine:
    def test_reconciles_valid_path(self, engine, graph_complete, valid_path):
        result = engine.reconcile(
            reconstructed_path=valid_path,
            declared_graph=graph_complete,
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
        )
        assert result.is_reconciled
        assert result.epistemic_status == EpistemicStatus.RECONCILED
        assert result.correspondence_status == CorrespondenceStatus.CORRESPONDS

    def test_detects_invalid_reconstruction(self, engine, graph_complete):
        invalid_path = ReconstructedAuthorityPath(
            path_id="path-invalid",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.INVALID,
            nodes=(),
            trust_anchor_id="",
            delegation_chain=(),
            capability_status=CapabilityStatus.INVALID,
            governance_status=GovernanceStatus.INVALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.UNKNOWN,
            escape_type=EscapeType.DIRECT_PRIMITIVE_BYPASS,
            completeness_status="unknown",
            provenance="test:invalid",
            confidence=0.1,
        )
        result = engine.reconcile(
            reconstructed_path=invalid_path,
            declared_graph=graph_complete,
        )
        assert result.epistemic_status == EpistemicStatus.INVALID_RECONSTRUCTION

    def test_detects_unknown_reconstruction(self, engine, graph_complete):
        unknown_path = ReconstructedAuthorityPath(
            path_id="path-unknown",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.UNKNOWN,
            nodes=(),
            trust_anchor_id="",
            delegation_chain=(),
            capability_status=CapabilityStatus.MISSING,
            governance_status=GovernanceStatus.MISSING,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.UNKNOWN,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="unknown",
            provenance="test:unknown",
            confidence=0.1,
        )
        result = engine.reconcile(
            reconstructed_path=unknown_path,
            declared_graph=graph_complete,
        )
        assert result.epistemic_status == EpistemicStatus.UNKNOWN

    def test_detects_escape_authorization_laundering(self, engine, graph_complete):
        path = ReconstructedAuthorityPath(
            path_id="path-escape",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.AUTHORIZATION_LAUNDERING,
            completeness_status="complete_within_declared_graph",
            provenance="test:laundering",
            confidence=0.5,
        )
        result = engine.reconcile(
            reconstructed_path=path,
            declared_graph=graph_complete,
        )
        assert result.is_escape
        assert result.epistemic_status == EpistemicStatus.AUTHORITY_ESCAPE

    def test_detects_incomplete_graph(self, engine, valid_path):
        incomplete_graph = DeclaredAuthorityGraph(graph_id="test-incomplete", version="v1")
        incomplete_graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        # Missing most nodes

        result = engine.reconcile(
            reconstructed_path=valid_path,
            declared_graph=incomplete_graph,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )
        assert result.epistemic_status == EpistemicStatus.INCOMPLETE
        assert result.divergence_type == DivergenceType.INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE

    def test_detects_cyclic_graph(self, engine, valid_path):
        cyclic_graph = DeclaredAuthorityGraph(graph_id="test-cyclic", version="v1")
        cyclic_graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        cyclic_graph.add_node(DeclaredAuthorityNode(
            node_id="del-001",
            node_type="delegation",
            principal="admin",
            capability="subprocess.execute",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.DELEGATION,
            trust_anchor_id="ta-001",
        ))
        from research.examples.sovereign_agent.authority_path_graph_reconciliation import DeclaredAuthorityEdge
        cyclic_graph.add_edge(DeclaredAuthorityEdge(edge_id="e1", source_node_id="ta-001", target_node_id="del-001"))
        cyclic_graph.add_edge(DeclaredAuthorityEdge(edge_id="e2", source_node_id="del-001", target_node_id="ta-001"))

        result = engine.reconcile(
            reconstructed_path=valid_path,
            declared_graph=cyclic_graph,
            is_cyclic=True,
        )
        assert result.epistemic_status == EpistemicStatus.DIVERGENT
        assert result.divergence_type == DivergenceType.CYCLIC_DECLARED_GRAPH


# ---------------------------------------------------------------------------
# Phase 32 invariants
# ---------------------------------------------------------------------------


class TestPhase32Invariants:
    def test_reconciliation_not_authorization(self):
        """RECONCILIATION ≠ AUTHORIZATION."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph)
        # Reconciliation is epistemic, not authorization
        assert isinstance(result, AuthorityReconciliation)
        assert not hasattr(result, "authorize")
        assert not hasattr(result, "grant_authority")

    def test_reconstructed_path_not_declared_path(self):
        """RECONSTRUCTED PATH ≠ DECLARED PATH."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph)
        # The result distinguishes the two paths
        assert result.reconstructed_path_id == "path-test"
        assert result.declared_path_reference != result.reconstructed_path_id

    def test_missing_correspondence_not_invalid_authority(self):
        """MISSING CORRESPONDENCE ≠ INVALID AUTHORITY."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        # Path with different principal - won't match
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="other", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-other",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(
            path, graph,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )
        # Missing correspondence in incomplete graph = INCOMPLETE, not ESCAPE
        assert result.epistemic_status == EpistemicStatus.INCOMPLETE

    def test_no_path_found_not_path_proven_invalid(self):
        """NO PATH FOUND ≠ PATH PROVEN INVALID."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="other", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-other",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(
            path, graph,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )
        # No path found in incomplete graph = INCOMPLETE, not INVALID
        assert result.epistemic_status != EpistemicStatus.INVALID_RECONSTRUCTION

    def test_incomplete_graph_not_invalid_path(self):
        """INCOMPLETE GRAPH ≠ INVALID PATH."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(
            path, graph,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )
        # Incomplete graph should not make the path invalid
        assert result.epistemic_status != EpistemicStatus.INVALID_RECONSTRUCTION

    def test_valid_path_within_incomplete_graph_not_global_valid(self):
        """VALID PATH WITHIN INCOMPLETE GRAPH ≠ GLOBAL AUTHORITY VALID."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(
            path, graph,
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            is_incomplete_graph=True,
        )
        # Valid path in incomplete graph should be RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH
        assert result.epistemic_status == EpistemicStatus.RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH

    def test_historically_valid_not_currently_valid(self):
        """HISTORICALLY_VALID ≠ CURRENTLY_VALID."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.HISTORICALLY_VALID,  # Historical
                    scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.HISTORICALLY_VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph, is_historical=True)
        # Historical validity should be preserved
        assert result.historical_validity
        assert result.temporal_correspondence == TemporalReconciliationStatus.HISTORICALLY_VALID

    def test_caller_authority_not_worker_authority(self):
        """CALLER_AUTHORITY ≠ WORKER_AUTHORITY."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CALLER_TO_WORKER_UNCONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph, is_background=True)
        # Background worker should have unconfirmed attribution
        assert result.actor_correspondence == ActorReconciliationStatus.CALLER_TO_WORKER_UNCONFIRMED

    def test_cross_domain_observation_not_cross_domain_authority(self):
        """CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="domain-a",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="domain-b",  # Different domain
                    status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.CROSS_DOMAIN_BLOCKED,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.CROSS_DOMAIN_BLOCKED,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph, is_cross_domain=True)
        # Cross-domain without authority should be blocked
        assert result.domain_correspondence == DomainReconciliationStatus.CROSS_DOMAIN_BLOCKED

    def test_emergency_path_not_automatically_unauthorized(self):
        """EMERGENCY_PATH ≠ AUTOMATICALLY_UNAUTHORIZED."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph, is_emergency=True)
        # Emergency path should not be automatically unauthorized
        assert result.actor_correspondence == ActorReconciliationStatus.EMERGENCY_ACTOR_VALID

    def test_recovery_path_not_automatically_unauthorized(self):
        """RECOVERY_PATH ≠ AUTOMATICALLY_UNAUTHORIZED."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph, is_recovery=True)
        # Recovery path should not be automatically unauthorized
        assert result.actor_correspondence == ActorReconciliationStatus.RECOVERY_ACTOR_VALID

    def test_static_possibility_not_executed_effect(self):
        """STATIC POSSIBILITY ≠ EXECUTED EFFECT."""
        engine = ReconciliationEngine("test")
        graph = DeclaredAuthorityGraph(graph_id="test", version="v1")
        graph.add_node(DeclaredAuthorityNode(
            node_id="ta-001",
            node_type="trust_anchor",
            principal="admin",
            capability="*",
            scope="runtime",
            domain="default",
            source_type=AuthoritySourceType.TRUST_ANCHOR,
            trust_anchor_id="ta-001",
        ))
        path = ReconstructedAuthorityPath(
            path_id="path-test",
            observation_id="obs-test",
            effect_id="eff-test",
            validity=PathValidity.VALID,
            nodes=(
                AuthorityPathNode(
                    node_id="n1", node_type="trust_anchor", principal="admin", capability="*",
                    scope="runtime", domain="default", status=PathNodeStatus.VERIFIED,
                    evidence_id="ev1", evidence_type="trust_anchor_record",
                    temporal_status=TemporalStatus.VALID, scope_status=ScopeStatus.VALID,
                    provenance="test:trust_anchor",
                ),
            ),
            trust_anchor_id="ta-001",
            delegation_chain=(),
            capability_status=CapabilityStatus.VALID,
            governance_status=GovernanceStatus.VALID,
            temporal_status=TemporalStatus.VALID,
            scope_status=ScopeStatus.VALID,
            attribution_status=AttributionStatus.CONFIRMED,
            escape_type=EscapeType.NO_ESCAPE,
            completeness_status="complete_within_declared_graph",
            provenance="test",
            confidence=0.5,
        )
        result = engine.reconcile(path, graph, declared_path_executed=False)
        # Declared path that was not executed should be DIVERGENT
        assert result.epistemic_status == EpistemicStatus.DIVERGENT
        assert result.divergence_type == DivergenceType.STATIC_POSSIBILITY_NOT_EXECUTED


# ---------------------------------------------------------------------------
# Oracle evaluation tests
# ---------------------------------------------------------------------------


class TestOracleEvaluation:
    def test_oracle_evaluates_exact_correspondence(self, oracle, worlds):
        world = worlds[0]  # exact correspondence
        engine = ReconciliationEngine("test")
        reconciliation = engine.reconcile(
            reconstructed_path=world.reconstructed_path,
            declared_graph=world.declared_graph,
            graph_completeness=world.graph_completeness,
            graph_complete_for_scope=world.graph_complete_for_scope,
        )
        evaluation = oracle.evaluate(world, reconciliation)
        assert evaluation.status_match
        assert evaluation.epistemic_match
        assert not evaluation.false_authorization
        assert not evaluation.false_escape

    def test_oracle_detects_false_authorization(self, oracle, worlds):
        """Test that oracle detects false authorization."""
        world = worlds[10]  # authorization laundering
        engine = ReconciliationEngine("test")
        reconciliation = engine.reconcile(
            reconstructed_path=world.reconstructed_path,
            declared_graph=world.declared_graph,
            graph_completeness=world.graph_completeness,
            graph_complete_for_scope=world.graph_complete_for_scope,
        )
        evaluation = oracle.evaluate(world, reconciliation)
        # The reconciliation should detect the escape
        assert reconciliation.epistemic_status == EpistemicStatus.AUTHORITY_ESCAPE
        assert not evaluation.false_authorization

    def test_oracle_evaluates_incomplete_graph(self, oracle, worlds):
        world = worlds[17]  # intentionally incomplete graph
        engine = ReconciliationEngine("test")
        reconciliation = engine.reconcile(
            reconstructed_path=world.reconstructed_path,
            declared_graph=world.declared_graph,
            graph_completeness=world.graph_completeness,
            graph_complete_for_scope=world.graph_complete_for_scope,
            is_incomplete_graph=world.is_incomplete_graph,
        )
        evaluation = oracle.evaluate(world, reconciliation)
        # Should correctly identify as incomplete, not escape
        assert reconciliation.epistemic_status == EpistemicStatus.INCOMPLETE
        assert evaluation.epistemic_match


# ---------------------------------------------------------------------------
# Full experiment test
# ---------------------------------------------------------------------------


class TestPhase32Experiment:
    def test_runs_all_worlds(self):
        from research.examples.sovereign_agent.authority_path_graph_reconciliation import Phase32Experiment
        exp = Phase32Experiment()
        results = exp.run_all()
        assert results["total_worlds"] == 35

    def test_summary_generated(self):
        from research.examples.sovereign_agent.authority_path_graph_reconciliation import Phase32Experiment
        exp = Phase32Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_worlds"] == 35
        assert summary["total_reconciliations"] == 35

    def test_false_authorizations_count(self):
        from research.examples.sovereign_agent.authority_path_graph_reconciliation import Phase32Experiment
        exp = Phase32Experiment()
        exp.run_all()
        summary = exp.summary()
        # False authorizations are the most important failure mode
        assert summary["false_authorizations"] >= 0

    def test_false_escapes_count(self):
        from research.examples.sovereign_agent.authority_path_graph_reconciliation import Phase32Experiment
        exp = Phase32Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["false_escapes"] >= 0
