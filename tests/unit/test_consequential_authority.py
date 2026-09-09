"""Tests for Consequential Authority Graph."""

import pytest

from examples.self_audit.consequential_authority import (
    AuthorityCondition,
    AuthorityCutSet,
    AuthorityDisposition,
    AuthorityPath,
    ConditionalAuthority,
    ConsequenceType,
    ConsequentialAuthority,
    ConsequentialAuthorityGraph,
    ConsequentialAuthorityInvariants,
    EdgeType,
    EpistemicState,
    GraphEdge,
    GraphNode,
    PathEdge,
    ReachabilityType,
)


class TestGraphNode:
    """Tests for graph node."""

    def test_node_creation(self):
        node = GraphNode(
            node_id="test_node",
            node_type="component",
            name="Test Node",
        )
        assert node.node_id == "test_node"
        assert node.node_type == "component"

    def test_node_to_dict(self):
        node = GraphNode(
            node_id="test_node",
            node_type="component",
            name="Test Node",
        )
        d = node.to_dict()
        assert d["node_id"] == "test_node"
        assert d["node_type"] == "component"


class TestGraphEdge:
    """Tests for graph edge."""

    def test_edge_creation(self):
        edge = GraphEdge(
            edge_id="test_edge",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        assert edge.edge_id == "test_edge"
        assert edge.source == "A"
        assert edge.target == "B"
        assert edge.edge_type == EdgeType.DEPENDENCY

    def test_edge_to_dict(self):
        edge = GraphEdge(
            edge_id="test_edge",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        d = edge.to_dict()
        assert d["edge_id"] == "test_edge"
        assert d["source"] == "A"
        assert d["target"] == "B"
        assert d["edge_type"] == "dependency"


class TestConsequentialAuthorityGraph:
    """Tests for the consequential authority graph."""

    def test_add_node(self):
        graph = ConsequentialAuthorityGraph()
        node = GraphNode(node_id="test", node_type="component", name="Test")
        graph.add_node(node)
        assert len(graph.nodes) == 1

    def test_add_edge(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="test",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        graph.add_edge(edge)
        assert len(graph.edges) == 1

    def test_get_edges_by_type(self):
        graph = ConsequentialAuthorityGraph()
        edge1 = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        edge2 = GraphEdge(
            edge_id="e2",
            source="B",
            target="C",
            edge_type=EdgeType.CONSEQUENCE,
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        dep_edges = graph.get_edges_by_type(EdgeType.DEPENDENCY)
        assert len(dep_edges) == 1
        assert dep_edges[0].edge_id == "e1"

    def test_get_edges_by_source(self):
        graph = ConsequentialAuthorityGraph()
        edge1 = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        edge2 = GraphEdge(
            edge_id="e2",
            source="A",
            target="C",
            edge_type=EdgeType.CONSEQUENCE,
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        a_edges = graph.get_edges_by_source("A")
        assert len(a_edges) == 2

    def test_get_edges_by_target(self):
        graph = ConsequentialAuthorityGraph()
        edge1 = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        edge2 = GraphEdge(
            edge_id="e2",
            source="C",
            target="B",
            edge_type=EdgeType.CONSEQUENCE,
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        b_edges = graph.get_edges_by_target("B")
        assert len(b_edges) == 2

    def test_get_consequence_edges(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CONSEQUENCE,
        )
        graph.add_edge(edge)
        cons_edges = graph.get_consequence_edges()
        assert len(cons_edges) == 1

    def test_get_authority_edges(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.AUTHORITY,
        )
        graph.add_edge(edge)
        auth_edges = graph.get_authority_edges()
        assert len(auth_edges) == 1

    def test_get_delegation_edges(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DELEGATION,
        )
        graph.add_edge(edge)
        del_edges = graph.get_delegation_edges()
        assert len(del_edges) == 1

    def test_get_credential_edges(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CREDENTIAL,
        )
        graph.add_edge(edge)
        cred_edges = graph.get_credential_edges()
        assert len(cred_edges) == 1

    def test_get_boundary_edges(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.BOUNDARY,
        )
        graph.add_edge(edge)
        bound_edges = graph.get_boundary_edges()
        assert len(bound_edges) == 1

    def test_to_dict(self):
        graph = ConsequentialAuthorityGraph()
        node = GraphNode(node_id="test", node_type="component", name="Test")
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        graph.add_node(node)
        graph.add_edge(edge)
        d = graph.to_dict()
        assert d["metadata"]["total_nodes"] == 1
        assert d["metadata"]["total_edges"] == 1
        assert "summary" in d


class TestConsequentialAuthority:
    """Tests for consequential authority."""

    def test_authority_creation(self):
        auth = ConsequentialAuthority(
            authority_id="auth_001",
            actor="checkout",
            component="payment_gateway",
            operation="charge",
            resource="customer_card",
            consequence_type=ConsequenceType.PAYMENT,
        )
        assert auth.authority_id == "auth_001"
        assert auth.actor == "checkout"
        assert auth.consequence_type == ConsequenceType.PAYMENT

    def test_authority_to_dict(self):
        auth = ConsequentialAuthority(
            authority_id="auth_001",
            actor="checkout",
            component="payment_gateway",
            operation="charge",
            resource="customer_card",
            consequence_type=ConsequenceType.PAYMENT,
        )
        d = auth.to_dict()
        assert d["authority_id"] == "auth_001"
        assert d["actor"] == "checkout"
        assert d["consequence_type"] == "payment"


class TestAuthorityPath:
    """Tests for authority path."""

    def test_path_creation(self):
        edge = PathEdge(
            edge_id="pe_001",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        path = AuthorityPath(
            path_id="path_001",
            edges=[edge],
            source="A",
            target="B",
            consequence_type=ConsequenceType.PAYMENT,
            authority_disposition=AuthorityDisposition.AUTHORIZED,
        )
        assert path.path_id == "path_001"
        assert len(path.edges) == 1
        assert path.authority_disposition == AuthorityDisposition.AUTHORIZED

    def test_path_to_dict(self):
        edge = PathEdge(
            edge_id="pe_001",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        path = AuthorityPath(
            path_id="path_001",
            edges=[edge],
            source="A",
            target="B",
            consequence_type=ConsequenceType.PAYMENT,
            authority_disposition=AuthorityDisposition.AUTHORIZED,
        )
        d = path.to_dict()
        assert d["path_id"] == "path_001"
        assert len(d["edges"]) == 1
        assert d["authority_disposition"] == "authorized"


class TestAuthorityCutSet:
    """Tests for authority cut set."""

    def test_cut_set_creation(self):
        cut_set = AuthorityCutSet(
            cut_set_id="cut_001",
            target_consequence="payment",
            boundaries=["payment_gateway", "credential_store"],
            cut_type="capability",
            authority_basis="protocol_derivation",
        )
        assert cut_set.cut_set_id == "cut_001"
        assert cut_set.target_consequence == "payment"
        assert len(cut_set.boundaries) == 2

    def test_cut_set_to_dict(self):
        cut_set = AuthorityCutSet(
            cut_set_id="cut_001",
            target_consequence="payment",
            boundaries=["payment_gateway", "credential_store"],
            cut_type="capability",
            authority_basis="protocol_derivation",
        )
        d = cut_set.to_dict()
        assert d["cut_set_id"] == "cut_001"
        assert d["target_consequence"] == "payment"
        assert len(d["boundaries"]) == 2


class TestConditionalAuthority:
    """Tests for conditional authority."""

    def test_conditional_authority_creation(self):
        condition = AuthorityCondition(
            condition_id="cond_001",
            condition_type="feature_flag",
            description="new_fraud_service enabled",
            value=True,
        )
        auth = ConditionalAuthority(
            authority_id="auth_001",
            authority_type="delegation",
            conditions=[condition],
            authority_basis="explicit_delegation",
        )
        assert auth.authority_id == "auth_001"
        assert len(auth.conditions) == 1
        assert not auth.is_unconditional

    def test_unconditional_authority(self):
        auth = ConditionalAuthority(
            authority_id="auth_001",
            authority_type="protocol",
            conditions=[],
            authority_basis="protocol_derivation",
        )
        assert auth.is_unconditional

    def test_conditional_authority_to_dict(self):
        condition = AuthorityCondition(
            condition_id="cond_001",
            condition_type="feature_flag",
            description="new_fraud_service enabled",
            value=True,
        )
        auth = ConditionalAuthority(
            authority_id="auth_001",
            authority_type="delegation",
            conditions=[condition],
            authority_basis="explicit_delegation",
        )
        d = auth.to_dict()
        assert d["authority_id"] == "auth_001"
        assert len(d["conditions"]) == 1
        assert not d["is_unconditional"]


class TestConsequentialAuthorityInvariants:
    """Tests for invariant checks."""

    def test_dependency_not_authority_holds(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_dependency_not_authority(graph)
        assert result["held"]

    def test_dependency_not_authority_violated(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.DEPENDENCY,
            authority_basis="protocol_derivation",
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_dependency_not_authority(graph)
        assert not result["held"]

    def test_reachability_not_authority_holds(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CALL,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_reachability_not_authority(graph)
        assert result["held"]

    def test_reachability_not_authority_violated(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CALL,
            authority_basis="protocol_derivation",
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_reachability_not_authority(graph)
        assert not result["held"]

    def test_consequence_not_authorization_holds(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CONSEQUENCE,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_consequence_not_authorization(graph)
        assert result["held"]

    def test_consequence_not_authorization_violated(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CONSEQUENCE,
            authorization_id="auth_001",
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_consequence_not_authorization(graph)
        assert not result["held"]

    def test_credential_not_authorization_holds(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CREDENTIAL,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_credential_not_authorization(graph)
        assert result["held"]

    def test_credential_not_authorization_violated(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CREDENTIAL,
            authority_basis="protocol_derivation",
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_credential_not_authorization(graph)
        assert not result["held"]

    def test_runtime_not_governance_holds(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CALL,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_runtime_not_governance(graph)
        assert result["held"]

    def test_runtime_not_governance_violated(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.CALL,
            governance_policy_id="policy_001",
            epistemic_state=EpistemicState.OBSERVED,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_runtime_not_governance(graph)
        assert not result["held"]

    def test_trust_not_authority_holds(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.TRUST,
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_trust_not_authority(graph)
        assert result["held"]

    def test_trust_not_authority_violated(self):
        graph = ConsequentialAuthorityGraph()
        edge = GraphEdge(
            edge_id="e1",
            source="A",
            target="B",
            edge_type=EdgeType.TRUST,
            authority_basis="protocol_derivation",
        )
        graph.add_edge(edge)
        result = ConsequentialAuthorityInvariants.check_trust_not_authority(graph)
        assert not result["held"]

    def test_consequential_reachable_not_authoritative_holds(self):
        graph = ConsequentialAuthorityGraph()
        path = AuthorityPath(
            path_id="p1",
            edges=[],
            source="A",
            target="B",
            consequence_type=ConsequenceType.PAYMENT,
            authority_disposition=AuthorityDisposition.AUTHORIZED,
        )
        graph.add_path(path)
        result = ConsequentialAuthorityInvariants.check_consequential_reachable_not_authoritative(graph)
        assert result["held"]

    def test_consequential_reachable_not_authoritative_violated(self):
        graph = ConsequentialAuthorityGraph()
        path = AuthorityPath(
            path_id="p1",
            edges=[],
            source="A",
            target="B",
            consequence_type=ConsequenceType.PAYMENT,
            authority_disposition=AuthorityDisposition.UNKNOWN,
        )
        graph.add_path(path)
        result = ConsequentialAuthorityInvariants.check_consequential_reachable_not_authoritative(graph)
        assert not result["held"]

    def test_check_all(self):
        graph = ConsequentialAuthorityGraph()
        results = ConsequentialAuthorityInvariants.check_all(graph)
        assert len(results) == 7


class TestPaymentFixture:
    """Tests for the payment fixture."""

    def test_load_production_config(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            load_environment_config,
        )
        config = load_environment_config("production")
        assert config.production is True
        assert config.debug is False
        assert config.api_endpoint == "https://api.payment-provider.com/v1"

    def test_load_staging_config(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            load_environment_config,
        )
        config = load_environment_config("staging")
        assert config.production is False
        assert config.debug is True

    def test_load_development_config(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            load_environment_config,
        )
        config = load_environment_config("development")
        assert config.production is False
        assert config.debug is True

    def test_feature_flags_differ_by_environment(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            load_environment_config,
        )
        prod = load_environment_config("production")
        staging = load_environment_config("staging")
        dev = load_environment_config("development")
        # Legacy processor is disabled in prod but enabled in staging/dev
        assert prod.feature_flags["legacy_processor"] is False
        assert staging.feature_flags["legacy_processor"] is True
        assert dev.feature_flags["legacy_processor"] is True
        # New fraud service is enabled in prod/staging but not dev
        assert prod.feature_flags["new_fraud_service"] is True
        assert staging.feature_flags["new_fraud_service"] is True
        assert dev.feature_flags["new_fraud_service"] is False

    def test_checkout_service_creation(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            CheckoutService,
            load_environment_config,
        )
        config = load_environment_config("production")
        checkout = CheckoutService(config)
        assert checkout is not None

    def test_payment_gateway_creation(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            PaymentGateway,
            load_environment_config,
        )
        config = load_environment_config("production")
        gateway = PaymentGateway(config)
        assert gateway is not None

    def test_fraud_service_creation(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            FraudService,
            load_environment_config,
        )
        config = load_environment_config("production")
        fraud = FraudService(config)
        assert fraud is not None

    def test_admin_service_creation(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            AdminService,
            load_environment_config,
        )
        config = load_environment_config("production")
        admin = AdminService(config)
        assert admin is not None

    def test_background_worker_creation(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            BackgroundWorker,
            load_environment_config,
        )
        config = load_environment_config("production")
        worker = BackgroundWorker(config)
        assert worker is not None

    def test_fixture_builder(self):
        from examples.payment_dependency_auditor.authority_fixture.fixture import (
            PaymentFixtureBuilder,
        )
        builder = PaymentFixtureBuilder("production")
        services = builder.get_all_services()
        assert "checkout" in services
        assert "payment_gateway" in services
        assert "fraud_service" in services
        assert "admin" in services
        assert "legacy_processor" in services
        assert "worker" in services


class TestAuthorityTopologyIntegrator:
    """Tests for the authority topology integrator."""

    def test_integrate_dependencies(self):
        from examples.payment_dependency_auditor.authority_fixture.integration import (
            AuthorityTopologyIntegrator,
            DependencyObservation,
        )
        integrator = AuthorityTopologyIntegrator()
        deps = [
            DependencyObservation(
                source="checkout",
                target="payment_gateway",
                dependency_type="call",
                epistemic_state="observed",
            ),
        ]
        integrator.integrate_dependencies(deps)
        graph = integrator.get_graph()
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_integrate_runtime(self):
        from examples.payment_dependency_auditor.authority_fixture.integration import (
            AuthorityTopologyIntegrator,
            RuntimeObservation,
        )
        integrator = AuthorityTopologyIntegrator()
        obs = [
            RuntimeObservation(
                actor="checkout",
                operation="charge",
                resource="payment_gateway",
                result="success",
            ),
        ]
        integrator.integrate_runtime(obs)
        graph = integrator.get_graph()
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_integrate_authority(self):
        from examples.payment_dependency_auditor.authority_fixture.integration import (
            AuthorityDeclaration,
            AuthorityTopologyIntegrator,
        )
        integrator = AuthorityTopologyIntegrator()
        decls = [
            AuthorityDeclaration(
                declaration_id="auth_001",
                declaration_type="delegation",
                actor="checkout",
                operation="charge",
                scope={"resource": "payment_gateway"},
                basis="explicit_delegation",
            ),
        ]
        integrator.integrate_authority(decls)
        graph = integrator.get_graph()
        assert len(graph.edges) == 1
        assert graph.edges[0].edge_type == EdgeType.AUTHORITY

    def test_full_integration(self):
        from examples.payment_dependency_auditor.authority_fixture.integration import (
            AuthorityDeclaration,
            AuthorityTopologyIntegrator,
            DependencyObservation,
            RuntimeObservation,
        )
        integrator = AuthorityTopologyIntegrator()

        deps = [
            DependencyObservation(
                source="checkout",
                target="payment_gateway",
                dependency_type="call",
                epistemic_state="observed",
            ),
            DependencyObservation(
                source="payment_gateway",
                target="fraud_service",
                dependency_type="call",
                epistemic_state="observed",
            ),
        ]
        integrator.integrate_dependencies(deps)

        obs = [
            RuntimeObservation(
                actor="checkout",
                operation="charge",
                resource="payment_gateway",
                result="success",
            ),
        ]
        integrator.integrate_runtime(obs)

        decls = [
            AuthorityDeclaration(
                declaration_id="auth_001",
                declaration_type="delegation",
                actor="checkout",
                operation="charge",
                scope={"resource": "payment_gateway"},
                basis="explicit_delegation",
            ),
        ]
        integrator.integrate_authority(decls)

        graph = integrator.get_graph()
        assert len(graph.nodes) == 3  # checkout, payment_gateway, fraud_service
        assert len(graph.edges) == 4  # 2 dependency + 1 runtime + 1 authority
