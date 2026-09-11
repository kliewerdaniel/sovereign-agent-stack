"""Tests for authority boundary model and adjudication."""

import pytest

from research.examples.self_audit.authority_adjudication import (
    AdjudicationContext,
    ArgopackScenarioBuilder,
    AuthorityBoundaryAdjudicator,
)
from research.examples.self_audit.authority_boundary import (
    AuthorityBasis,
    AuthorityBoundary,
    AuthorityBoundaryGraph,
    AuthorityDistinguisher,
    AuthorityIntent,
    AuthorityOwner,
    BoundaryAdjudication,
    BoundaryClassification,
    BoundaryFinding,
    ConsequenceType,
    DelegationDeclaration,
    GovernanceDisposition,
    GovernanceRecommendation,
    GovernanceSeparation,
    InvariantChecker,
    TrustDeclaration,
)

# Rename to match the actual field name in AdjudicationContext
# static_hypotheses is the correct field name


class TestAuthorityOwner:
    """Tests for authority owner."""

    def test_owner_creation(self):
        owner = AuthorityOwner(
            owner_id="gov_001",
            name="Governance",
            owner_type="governance",
        )
        assert owner.owner_id == "gov_001"
        assert owner.name == "Governance"

    def test_owner_to_dict(self):
        owner = AuthorityOwner(
            owner_id="gov_001",
            name="Governance",
            owner_type="governance",
        )
        d = owner.to_dict()
        assert d["owner_id"] == "gov_001"
        assert d["name"] == "Governance"


class TestAuthorityBoundary:
    """Tests for authority boundary."""

    def test_boundary_creation(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        assert boundary.boundary_id == "test_boundary"
        assert boundary.actor == "test"

    def test_boundary_to_dict(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        d = boundary.to_dict()
        assert d["boundary_id"] == "test_boundary"
        assert d["actor"] == "test"


class TestDelegationDeclaration:
    """Tests for delegation declaration."""

    def test_delegation_creation(self):
        delegation = DelegationDeclaration(
            declaration_id="deleg_001",
            delegator_id="gov_001",
            delegate_id="argopack",
            scope={"actors": ["argopack"]},
            constraints=[],
        )
        assert delegation.declaration_id == "deleg_001"
        assert delegation.is_active

    def test_delegation_expired(self):
        delegation = DelegationDeclaration(
            declaration_id="deleg_001",
            delegator_id="gov_001",
            delegate_id="argopack",
            scope={"actors": ["argopack"]},
            constraints=[],
            expires_at="2020-01-01T00:00:00",
        )
        assert not delegation.is_active

    def test_delegation_revoked(self):
        delegation = DelegationDeclaration(
            declaration_id="deleg_001",
            delegator_id="gov_001",
            delegate_id="argopack",
            scope={"actors": ["argopack"]},
            constraints=[],
            revoked_at="2020-01-01T00:00:00",
        )
        assert not delegation.is_active


class TestTrustDeclaration:
    """Tests for trust declaration."""

    def test_trust_creation(self):
        trust = TrustDeclaration(
            declaration_id="trust_001",
            truster_id="gov_001",
            trusted_id="argopack",
            trust_basis="explicit",
            scope={"actors": ["argopack"]},
            constraints=[],
        )
        assert trust.declaration_id == "trust_001"
        assert trust.is_active

    def test_trust_expired(self):
        trust = TrustDeclaration(
            declaration_id="trust_001",
            truster_id="gov_001",
            trusted_id="argopack",
            trust_basis="explicit",
            scope={"actors": ["argopack"]},
            constraints=[],
            expires_at="2020-01-01T00:00:00",
        )
        assert not trust.is_active


class TestBoundaryAdjudication:
    """Tests for boundary adjudication."""

    def test_adjudication_creation(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            authority_basis=AuthorityBasis.UNKNOWN,
            governance_disposition=GovernanceDisposition.INCONCLUSIVE,
            confidence=0.5,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        assert adjudication.adjudication_id == "adj_001"
        assert adjudication.classification == BoundaryClassification.INCONCLUSIVE


class TestAuthorityBoundaryGraph:
    """Tests for authority boundary graph."""

    def test_add_boundary(self):
        graph = AuthorityBoundaryGraph()
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        graph.add_boundary(boundary)
        assert len(graph.boundaries) == 1

    def test_add_adjudication(self):
        graph = AuthorityBoundaryGraph()
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            authority_basis=AuthorityBasis.UNKNOWN,
            governance_disposition=GovernanceDisposition.INCONCLUSIVE,
            confidence=0.5,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        graph.add_adjudication(adjudication)
        assert len(graph.adjudications) == 1
        assert len(graph.edges) == 1

    def test_get_edges_by_actor(self):
        graph = AuthorityBoundaryGraph()
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            authority_basis=AuthorityBasis.UNKNOWN,
            governance_disposition=GovernanceDisposition.INCONCLUSIVE,
            confidence=0.5,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        graph.add_adjudication(adjudication)
        edges = graph.get_edges_by_actor("test")
        assert len(edges) == 1

    def test_to_dict(self):
        graph = AuthorityBoundaryGraph()
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        graph.add_boundary(boundary)  # Add this line
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            authority_basis=AuthorityBasis.UNKNOWN,
            governance_disposition=GovernanceDisposition.INCONCLUSIVE,
            confidence=0.5,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        graph.add_adjudication(adjudication)
        d = graph.to_dict()
        assert d["total_boundaries"] == 1
        assert d["total_adjudications"] == 1
        assert d["total_edges"] == 1


class TestAuthorityDistinguisher:
    """Tests for authority distinguisher."""

    def test_is_protocol_authority(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY,
            authority_basis=AuthorityBasis.PROTOCOL_DERIVATION,
            governance_disposition=GovernanceDisposition.ACCEPTED,
            confidence=0.8,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        assert AuthorityDistinguisher.is_protocol_authority(adjudication)

    def test_is_trusted_subsystem(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.TRUSTED_SUBSYSTEM,
            authority_basis=AuthorityBasis.TRUST_DECLARATION,
            governance_disposition=GovernanceDisposition.CONSTRAINED,
            confidence=0.7,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        assert AuthorityDistinguisher.is_trusted_subsystem(adjudication)

    def test_classify_authority_type(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY,
            authority_basis=AuthorityBasis.PROTOCOL_DERIVATION,
            governance_disposition=GovernanceDisposition.ACCEPTED,
            confidence=0.8,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        assert AuthorityDistinguisher.classify_authority_type(adjudication) == "protocol_authority"


class TestInvariantChecker:
    """Tests for invariant checker."""

    def test_trust_is_not_authority_holds(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.TRUSTED_SUBSYSTEM,
            authority_basis=AuthorityBasis.TRUST_DECLARATION,
            governance_disposition=GovernanceDisposition.CONSTRAINED,
            confidence=0.7,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        result = InvariantChecker.check_trust_is_not_authority(adjudication)
        assert result["held"]

    def test_trust_is_not_authority_violated(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY,
            authority_basis=AuthorityBasis.TRUST_DECLARATION,
            governance_disposition=GovernanceDisposition.ACCEPTED,
            confidence=0.8,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        result = InvariantChecker.check_trust_is_not_authority(adjudication)
        assert not result["held"]

    def test_ambient_is_not_protocol_holds(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.RECONSTRUCTION_FAILURE,
            authority_basis=AuthorityBasis.AMBIENT_PRIVILEGE,
            governance_disposition=GovernanceDisposition.PENDING_REVIEW,
            confidence=0.6,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        result = InvariantChecker.check_ambient_is_not_protocol(adjudication)
        assert result["held"]

    def test_check_all(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            authority_basis=AuthorityBasis.UNKNOWN,
            governance_disposition=GovernanceDisposition.INCONCLUSIVE,
            confidence=0.5,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        results = InvariantChecker.check_all(adjudication)
        assert len(results) == 5


class TestGovernanceSeparation:
    """Tests for governance separation."""

    def test_create_finding(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        finding = GovernanceSeparation.create_finding(
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            evidence="test evidence",
        )
        assert finding.finding_id.startswith("find_")
        assert finding.boundary_id == "test_boundary"

    def test_create_recommendation(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        adjudication = BoundaryAdjudication(
            adjudication_id="adj_001",
            boundary=boundary,
            classification=BoundaryClassification.INCONCLUSIVE,
            authority_basis=AuthorityBasis.UNKNOWN,
            governance_disposition=GovernanceDisposition.INCONCLUSIVE,
            confidence=0.5,
            runtime_evidence=[],
            static_evidence=[],
            reconciliation_evidence=[],
            authority_reconstruction=None,
            declarations=[],
            findings=[],
            recommendations=[],
            unresolved_questions=[],
            limitations=[],
            provenance_chain=[],
        )
        recommendation = GovernanceSeparation.create_recommendation(
            adjudication=adjudication,
            recommendation_type="review",
            description="Review boundary",
            rationale="Inconclusive classification",
        )
        assert recommendation.recommendation_id.startswith("rec_")

    def test_validate_separation(self):
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        finding = BoundaryFinding(
            finding_id="find_001",
            boundary_id="test_boundary",
            finding_type="test",
            description="Test finding",
            evidence="test evidence",
            severity="info",
        )
        recommendation = GovernanceRecommendation(
            recommendation_id="rec_001",
            adjudication_id="adj_001",
            recommendation_type="review",
            description="Review test_boundary",
            rationale="Test rationale",
            required_evidence=[],
            constraints=[],
        )
        result = GovernanceSeparation.validate_separation(finding, recommendation)
        assert result["separated"]


class TestAuthorityBoundaryAdjudicator:
    """Tests for the authority boundary adjudicator."""

    def test_adjudicate_no_declaration(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_a_no_declaration()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert adjudication.classification == BoundaryClassification.LEGACY_UNGOVERNED
        assert adjudication.governance_disposition == GovernanceDisposition.PENDING_REVIEW

    def test_adjudicate_trust_declaration(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_b_trust_declaration()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert adjudication.classification == BoundaryClassification.TRUSTED_SUBSYSTEM
        assert adjudication.governance_disposition == GovernanceDisposition.CONSTRAINED

    def test_adjudicate_delegation(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_c_delegation()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert adjudication.classification == BoundaryClassification.EXPLICIT_DELEGATION
        assert adjudication.governance_disposition == GovernanceDisposition.DELEGATED

    def test_adjudicate_prohibition(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_d_prohibition()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert adjudication.classification == BoundaryClassification.UNAUTHORIZED_ESCAPE
        assert adjudication.governance_disposition == GovernanceDisposition.PROHIBITED

    def test_adjudication_has_provenance_chain(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_a_no_declaration()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert len(adjudication.provenance_chain) > 0

    def test_adjudication_has_findings(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_a_no_declaration()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert len(adjudication.findings) > 0

    def test_adjudication_has_recommendations(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_a_no_declaration()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert len(adjudication.recommendations) > 0

    def test_adjudication_has_limitations(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_a_no_declaration()
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        assert len(adjudication.limitations) > 0


class TestArgopackScenarioBuilder:
    """Tests for the Argopack scenario builder."""

    def test_build_boundary(self):
        builder = ArgopackScenarioBuilder()
        boundary = builder.build_boundary()
        assert boundary.boundary_id == "argopack_subprocess"
        assert boundary.actor == "argopack"

    def test_build_runtime_evidence(self):
        builder = ArgopackScenarioBuilder()
        evidence = builder.build_runtime_evidence()
        assert len(evidence) > 0
        assert evidence[0]["event_type"] == "subprocess_create"

    def test_build_static_evidence(self):
        builder = ArgopackScenarioBuilder()
        evidence = builder.build_static_evidence()
        assert len(evidence) > 0
        assert evidence[0]["hypothesis_id"] == "hyp_0001"

    def test_build_reconciliation_evidence(self):
        builder = ArgopackScenarioBuilder()
        evidence = builder.build_reconciliation_evidence()
        assert len(evidence) > 0
        assert evidence[0]["classification"] == "authority_escape"

    def test_build_authority_reconstruction(self):
        builder = ArgopackScenarioBuilder()
        reconstruction = builder.build_authority_reconstruction()
        assert len(reconstruction) > 0
        assert reconstruction[0]["state"] == "unauthorized"

    def test_scenario_a_no_declaration(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_a_no_declaration()
        assert len(context.declarations) == 0
        assert len(context.governance_policies) == 0

    def test_scenario_b_trust_declaration(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_b_trust_declaration()
        assert len(context.declarations) == 1
        assert context.declarations[0]["declaration_type"] == "trust_declaration"

    def test_scenario_c_delegation(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_c_delegation()
        assert len(context.declarations) == 1
        assert context.declarations[0]["declaration_type"] == "delegation_declaration"

    def test_scenario_d_prohibition(self):
        builder = ArgopackScenarioBuilder()
        context = builder.build_scenario_d_prohibition()
        assert len(context.governance_policies) == 1
        assert context.governance_policies[0]["prohibits"]


class TestAdversarialCases:
    """Adversarial tests for authority boundary adjudication."""

    def test_forged_trust_declaration(self):
        """A forged trust declaration should not create authority."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        declarations = [
            {
                "declaration_id": "trust_forged",
                "declaration_type": "trust_declaration",
                "truster_id": "unauthorized_actor",
                "trusted_id": "test",
                "trust_basis": "forged",
                "scope": {},
                "constraints": [],
                "is_active": True,
                "provenance_id": None,  # No provenance
            }
        ]
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=declarations,
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should still classify as trusted_subsystem but with low confidence
        assert adjudication.confidence < 0.8

    def test_expired_delegation(self):
        """An expired delegation should not create authority."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        declarations = [
            {
                "declaration_id": "deleg_expired",
                "declaration_type": "delegation_declaration",
                "delegator_id": "gov_001",
                "delegate_id": "test",
                "scope": {"actors": ["test"]},
                "constraints": [],
                "is_active": False,  # Expired
                "expires_at": "2020-01-01T00:00:00",
            }
        ]
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=declarations,
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should not be classified as explicit_delegation
        assert adjudication.classification != BoundaryClassification.EXPLICIT_DELEGATION

    def test_revoked_delegation(self):
        """A revoked delegation should not create authority."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        declarations = [
            {
                "declaration_id": "deleg_revoked",
                "declaration_type": "delegation_declaration",
                "delegator_id": "gov_001",
                "delegate_id": "test",
                "scope": {"actors": ["test"]},
                "constraints": [],
                "is_active": False,  # Revoked
                "revoked_at": "2020-01-01T00:00:00",
            }
        ]
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=declarations,
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should not be classified as explicit_delegation
        assert adjudication.classification != BoundaryClassification.EXPLICIT_DELEGATION

    def test_delegation_exceeding_scope(self):
        """A delegation that exceeds its scope should be authority_mismatch."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        declarations = [
            {
                "declaration_id": "deleg_narrow",
                "declaration_type": "delegation_declaration",
                "delegator_id": "gov_001",
                "delegate_id": "test",
                "scope": {"actors": ["other_actor"]},  # Does not include "test"
                "constraints": [],
                "is_active": True,
            }
        ]
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=declarations,
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should be authority_mismatch
        assert adjudication.classification == BoundaryClassification.AUTHORITY_MISMATCH

    def test_wrong_authority_owner(self):
        """A boundary with wrong authority owner should be flagged."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
            intended_owner=AuthorityOwner(
                owner_id="wrong_owner",
                name="Wrong Owner",
                owner_type="actor",
            ),
        )
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=[],
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should be inconclusive or legacy_ungoverned
        assert adjudication.classification in (
            BoundaryClassification.INCONCLUSIVE,
            BoundaryClassification.LEGACY_UNGOVERNED,
        )

    def test_ambiguous_authority_intent(self):
        """Ambiguous authority intent should be inconclusive."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
        )
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[{"event_id": "evt_001", "result": "executed"}],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=[],
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should be inconclusive or legacy_ungoverned
        assert adjudication.classification in (
            BoundaryClassification.INCONCLUSIVE,
            BoundaryClassification.LEGACY_UNGOVERNED,
        )

    def test_multiple_competing_owners(self):
        """Multiple competing authority owners should be flagged."""
        boundary = AuthorityBoundary(
            boundary_id="test_boundary",
            source_domain="sas.test",
            destination_domain="os.process",
            actor="test",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            resource="test_resource",
            operation="test_operation",
            temporal_scope="unbounded",
            intended_owner=AuthorityOwner(
                owner_id="owner_1",
                name="Owner 1",
                owner_type="actor",
            ),
        )
        declarations = [
            {
                "declaration_id": "deleg_001",
                "declaration_type": "delegation_declaration",
                "delegator_id": "owner_1",
                "delegate_id": "test",
                "scope": {"actors": ["test"]},
                "constraints": [],
                "is_active": True,
            },
            {
                "declaration_id": "deleg_002",
                "declaration_type": "delegation_declaration",
                "delegator_id": "owner_2",
                "delegate_id": "test",
                "scope": {"actors": ["test"]},
                "constraints": [],
                "is_active": True,
            },
        ]
        context = AdjudicationContext(
            boundary=boundary,
            runtime_events=[],
            static_hypotheses=[],
            reconciliation_results=[],
            authority_reconstructions=[],
            declarations=declarations,
            governance_policies=[],
        )
        adjudicator = AuthorityBoundaryAdjudicator()
        adjudication = adjudicator.adjudicate(context)
        # Should have unresolved questions about competing owners
        assert len(adjudication.unresolved_questions) > 0
