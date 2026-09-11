"""Authority Boundary Model.

This module implements the formal model for authority boundary adjudication.
It distinguishes between:

- PROTOCOL AUTHORITY: authority derived through the canonical chain
- AMBIENT PROCESS PRIVILEGE: OS-level capability without protocol participation
- TRUSTED SUBSYSTEM AUTHORITY: explicit trust declaration outside protocol
- DELEGATED AUTHORITY: explicitly bounded authority transfer

Central principle:
    DISCOVERY OF AN AUTHORITY ESCAPE IS AN EPISTEMIC RESULT.
    WHETHER THAT ESCAPE IS ACCEPTABLE IS A GOVERNANCE DECISION.

New invariants:
    TRUST IS NOT AUTHORITY.
    AMBIENT PRIVILEGE IS NOT PROTOCOL AUTHORITY.
    OUTSIDE THE PROTOCOL IS NOT EQUIVALENT TO FORBIDDEN.
    AUTHORITY INTENT MUST NOT BE INFERRED FROM EXECUTION BEHAVIOR ALONE.
    DISCOVERY OF AN AUTHORITY ESCAPE DOES NOT CREATE AUTHORITY TO ENFORCE ITS REMEDIATION.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class BoundaryClassification(str, Enum):
    """Classification of an authority boundary."""
    INTENTIONAL_PROTOCOL_AUTHORITY = "intentional_protocol_authority"
    EXPLICIT_DELEGATION = "explicit_delegation"
    TRUSTED_SUBSYSTEM = "trusted_subsystem"
    LEGACY_UNGOVERNED = "legacy_ungoverned"
    UNAUTHORIZED_ESCAPE = "unauthorized_escape"
    AUTHORITY_MISMATCH = "authority_mismatch"
    RECONSTRUCTION_FAILURE = "reconstruction_failure"
    INCONCLUSIVE = "inconclusive"


class AuthorityBasis(str, Enum):
    """Basis for authority claims."""
    PROTOCOL_DERIVATION = "protocol_derivation"
    EXPLICIT_DELEGATION = "explicit_delegation"
    TRUST_DECLARATION = "trust_declaration"
    GOVERNANCE_POLICY = "governance_policy"
    AMBIENT_PRIVILEGE = "ambient_privilege"
    HISTORICAL_PRACTICE = "historical_practice"
    NONE = "none"
    UNKNOWN = "unknown"


class GovernanceDisposition(str, Enum):
    """Governance disposition of a boundary."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    CONSTRAINED = "constrained"
    PROHIBITED = "prohibited"
    PENDING_REVIEW = "pending_review"
    LEGACY_TOLERATED = "legacy_tolerated"
    INCONCLUSIVE = "inconclusive"


class ConsequenceType(str, Enum):
    """Types of consequences."""
    EXTERNAL_CONSEQUENTIAL = "external_consequential"
    AUTHORITY_MANAGEMENT = "authority_management"
    STATE_TRANSFORMING = "state_transforming"
    INFORMATIONAL = "informational"
    NON_CONSEQUENTIAL = "non_consequential"


class DeclarationType(str, Enum):
    """Types of authority declarations."""
    TRUST_DECLARATION = "trust_declaration"
    DELEGATION_DECLARATION = "delegation_declaration"
    POLICY_DECLARATION = "policy_declaration"
    BOUNDARY_DECLARATION = "boundary_declaration"
    REVOCATION_DECLARATION = "revocation_declaration"


# ---------------------------------------------------------------------------
# Authority Boundary Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityOwner:
    """An entity that owns authority over a boundary."""

    owner_id: str
    name: str
    owner_type: str  # "governance", "actor", "subsystem", "external"
    provenance_id: Optional[str] = None
    governance_scope: str = "unspecified"
    contact_reference: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "name": self.name,
            "owner_type": self.owner_type,
            "provenance_id": self.provenance_id,
            "governance_scope": self.governance_scope,
            "contact_reference": self.contact_reference,
        }


@dataclass(frozen=True)
class AuthorityIntent:
    """Declared intent for authority over a boundary."""

    intent_id: str
    boundary_id: str
    intended_owner: AuthorityOwner
    declared_mechanism: str
    consequence_types: list[str]
    resources: list[str]
    operations: list[str]
    temporal_scope: str
    constraints: list[str]
    provenance_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "intent_id": self.intent_id,
            "boundary_id": self.boundary_id,
            "intended_owner": self.intended_owner.to_dict(),
            "declared_mechanism": self.declared_mechanism,
            "consequence_types": self.consequence_types,
            "resources": self.resources,
            "operations": self.operations,
            "temporal_scope": self.temporal_scope,
            "constraints": self.constraints,
            "provenance_id": self.provenance_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class DelegationDeclaration:
    """An explicit delegation of authority."""

    declaration_id: str
    delegator_id: str
    delegate_id: str
    scope: dict[str, Any]  # actor, action, resource, domain, temporal
    constraints: list[str]
    parent_delegation_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None
    provenance_id: Optional[str] = None

    @property
    def is_active(self) -> bool:
        if self.revoked_at:
            return False
        if self.expires_at:
            now = datetime.utcnow().isoformat()
            return self.expires_at > now
        return True

    def to_dict(self) -> dict:
        return {
            "declaration_id": self.declaration_id,
            "delegator_id": self.delegator_id,
            "delegate_id": self.delegate_id,
            "scope": self.scope,
            "constraints": self.constraints,
            "parent_delegation_id": self.parent_delegation_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
            "provenance_id": self.provenance_id,
            "is_active": self.is_active,
        }


@dataclass(frozen=True)
class TrustDeclaration:
    """A declaration that a subsystem is trusted."""

    declaration_id: str
    truster_id: str
    trusted_id: str
    trust_basis: str
    scope: dict[str, Any]
    constraints: list[str]
    provenance_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None

    @property
    def is_active(self) -> bool:
        if self.revoked_at:
            return False
        if self.expires_at:
            now = datetime.utcnow().isoformat()
            return self.expires_at > now
        return True

    def to_dict(self) -> dict:
        return {
            "declaration_id": self.declaration_id,
            "truster_id": self.truster_id,
            "trusted_id": self.trusted_id,
            "trust_basis": self.trust_basis,
            "scope": self.scope,
            "constraints": self.constraints,
            "provenance_id": self.provenance_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
            "is_active": self.is_active,
        }


@dataclass(frozen=True)
class AuthorityBoundary:
    """A semantic boundary at which authority must be explicit."""

    boundary_id: str
    source_domain: str
    destination_domain: str
    actor: str
    consequence_type: ConsequenceType
    resource: str
    operation: str
    temporal_scope: str
    intended_owner: Optional[AuthorityOwner] = None
    declared_mechanism: Optional[str] = None
    delegation_source: Optional[str] = None
    trust_basis: Optional[str] = None
    governance_policy: Optional[str] = None
    provenance_requirements: list[str] = field(default_factory=list)
    reconstruction_requirements: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    revocation_mechanism: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "boundary_id": self.boundary_id,
            "source_domain": self.source_domain,
            "destination_domain": self.destination_domain,
            "actor": self.actor,
            "consequence_type": self.consequence_type.value,
            "resource": self.resource,
            "operation": self.operation,
            "temporal_scope": self.temporal_scope,
            "intended_owner": self.intended_owner.to_dict() if self.intended_owner else None,
            "declared_mechanism": self.declared_mechanism,
            "delegation_source": self.delegation_source,
            "trust_basis": self.trust_basis,
            "governance_policy": self.governance_policy,
            "provenance_requirements": self.provenance_requirements,
            "reconstruction_requirements": self.reconstruction_requirements,
            "constraints": self.constraints,
            "revocation_mechanism": self.revocation_mechanism,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class BoundaryAdjudication:
    """Result of adjudicating an authority boundary."""

    adjudication_id: str
    boundary: AuthorityBoundary
    classification: BoundaryClassification
    authority_basis: AuthorityBasis
    governance_disposition: GovernanceDisposition
    confidence: float
    runtime_evidence: list[dict[str, Any]]
    static_evidence: list[dict[str, Any]]
    reconciliation_evidence: list[dict[str, Any]]
    authority_reconstruction: Optional[dict[str, Any]]
    declarations: list[dict[str, Any]]
    findings: list[str]
    recommendations: list[str]
    unresolved_questions: list[str]
    limitations: list[str]
    provenance_chain: list[str]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "adjudication_id": self.adjudication_id,
            "boundary": self.boundary.to_dict(),
            "classification": self.classification.value,
            "authority_basis": self.authority_basis.value,
            "governance_disposition": self.governance_disposition.value,
            "confidence": self.confidence,
            "runtime_evidence": self.runtime_evidence,
            "static_evidence": self.static_evidence,
            "reconciliation_evidence": self.reconciliation_evidence,
            "authority_reconstruction": self.authority_reconstruction,
            "declarations": self.declarations,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "unresolved_questions": self.unresolved_questions,
            "limitations": self.limitations,
            "provenance_chain": self.provenance_chain,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class BoundaryFinding:
    """A finding from boundary analysis."""

    finding_id: str
    boundary_id: str
    finding_type: str
    description: str
    evidence: str
    severity: str
    provenance_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "boundary_id": self.boundary_id,
            "finding_type": self.finding_type,
            "description": self.description,
            "evidence": self.evidence,
            "severity": self.severity,
            "provenance_id": self.provenance_id,
        }


@dataclass(frozen=True)
class GovernanceRecommendation:
    """A recommendation from boundary adjudication."""

    recommendation_id: str
    adjudication_id: str
    recommendation_type: str
    description: str
    rationale: str
    required_evidence: list[str]
    constraints: list[str]
    provenance_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "adjudication_id": self.adjudication_id,
            "recommendation_type": self.recommendation_type,
            "description": self.description,
            "rationale": self.rationale,
            "required_evidence": self.required_evidence,
            "constraints": self.constraints,
            "provenance_id": self.provenance_id,
        }


# ---------------------------------------------------------------------------
# Authority Boundary Graph
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BoundaryGraphEdge:
    """An edge in the authority boundary graph."""

    edge_id: str
    source_domain: str
    destination_domain: str
    actor: str
    consequence_type: str
    authority_owner: Optional[str]
    authority_basis: str
    delegation_source: Optional[str]
    trust_basis: Optional[str]
    governance_policy: Optional[str]
    temporal_scope: str
    reconstruction_requirement: str
    governance_disposition: str
    evidence: str
    limitations: str

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source_domain": self.source_domain,
            "destination_domain": self.destination_domain,
            "actor": self.actor,
            "consequence_type": self.consequence_type,
            "authority_owner": self.authority_owner,
            "authority_basis": self.authority_basis,
            "delegation_source": self.delegation_source,
            "trust_basis": self.trust_basis,
            "governance_policy": self.governance_policy,
            "temporal_scope": self.temporal_scope,
            "reconstruction_requirement": self.reconstruction_requirement,
            "governance_disposition": self.governance_disposition,
            "evidence": self.evidence,
            "limitations": self.limitations,
        }


class AuthorityBoundaryGraph:
    """Graph of authority boundaries."""

    def __init__(self):
        self.edges: list[BoundaryGraphEdge] = []
        self.boundaries: list[AuthorityBoundary] = []
        self.adjudications: list[BoundaryAdjudication] = []

    def add_boundary(self, boundary: AuthorityBoundary):
        """Add a boundary to the graph."""
        self.boundaries.append(boundary)

    def add_adjudication(self, adjudication: BoundaryAdjudication):
        """Add an adjudication to the graph."""
        self.adjudications.append(adjudication)
        self._add_edge_from_adjudication(adjudication)

    def _add_edge_from_adjudication(self, adjudication: BoundaryAdjudication):
        """Add a graph edge from an adjudication."""
        boundary = adjudication.boundary
        edge = BoundaryGraphEdge(
            edge_id=f"bge_{boundary.boundary_id}",
            source_domain=boundary.source_domain,
            destination_domain=boundary.destination_domain,
            actor=boundary.actor,
            consequence_type=boundary.consequence_type.value,
            authority_owner=boundary.intended_owner.owner_id if boundary.intended_owner else None,
            authority_basis=adjudication.authority_basis.value,
            delegation_source=boundary.delegation_source,
            trust_basis=boundary.trust_basis,
            governance_policy=boundary.governance_policy,
            temporal_scope=boundary.temporal_scope,
            reconstruction_requirement="required" if boundary.reconstruction_requirements else "unspecified",
            governance_disposition=adjudication.governance_disposition.value,
            evidence=f"Adjudication: {adjudication.adjudication_id}",
            limitations="; ".join(adjudication.limitations) if adjudication.limitations else "none",
        )
        self.edges.append(edge)

    def get_edges_by_actor(self, actor: str) -> list[BoundaryGraphEdge]:
        """Get edges by actor."""
        return [e for e in self.edges if e.actor == actor]

    def get_edges_by_classification(self, classification: str) -> list[BoundaryGraphEdge]:
        """Get edges by governance disposition."""
        return [e for e in self.edges if e.governance_disposition == classification]

    def get_edges_by_domain(self, domain: str) -> list[BoundaryGraphEdge]:
        """Get edges by source domain."""
        return [e for e in self.edges if e.source_domain == domain]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_boundaries": len(self.boundaries),
            "total_adjudications": len(self.adjudications),
            "total_edges": len(self.edges),
            "boundaries": [b.to_dict() for b in self.boundaries],
            "adjudications": [a.to_dict() for a in self.adjudications],
            "edges": [e.to_dict() for e in self.edges],
            "summary": {
                "by_classification": self._count_by_classification(),
                "by_governance_disposition": self._count_by_disposition(),
                "by_authority_basis": self._count_by_basis(),
            },
        }

    def _count_by_classification(self) -> dict:
        counts = {}
        for a in self.adjudications:
            cls = a.classification.value
            counts[cls] = counts.get(cls, 0) + 1
        return counts

    def _count_by_disposition(self) -> dict:
        counts = {}
        for a in self.adjudications:
            disp = a.governance_disposition.value
            counts[disp] = counts.get(disp, 0) + 1
        return counts

    def _count_by_basis(self) -> dict:
        counts = {}
        for a in self.adjudications:
            basis = a.authority_basis.value
            counts[basis] = counts.get(basis, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Protocol Authority vs Ambient Authority Distinction
# ---------------------------------------------------------------------------


class AuthorityDistinguisher:
    """Distinguishes between protocol authority and ambient authority."""

    @staticmethod
    def is_protocol_authority(adjudication: BoundaryAdjudication) -> bool:
        """Check if the boundary has protocol authority."""
        return adjudication.authority_basis == AuthorityBasis.PROTOCOL_DERIVATION

    @staticmethod
    def is_ambient_privilege(adjudication: BoundaryAdjudication) -> bool:
        """Check if the boundary relies on ambient process privilege."""
        return adjudication.authority_basis == AuthorityBasis.AMBIENT_PRIVILEGE

    @staticmethod
    def is_trusted_subsystem(adjudication: BoundaryAdjudication) -> bool:
        """Check if the boundary is a trusted subsystem."""
        return adjudication.authority_basis == AuthorityBasis.TRUST_DECLARATION

    @staticmethod
    def is_delegated(adjudication: BoundaryAdjudication) -> bool:
        """Check if the boundary has explicit delegation."""
        return adjudication.authority_basis == AuthorityBasis.EXPLICIT_DELEGATION

    @staticmethod
    def has_reconstructible_provenance(adjudication: BoundaryAdjudication) -> bool:
        """Check if the adjudication has reconstructible provenance."""
        return len(adjudication.provenance_chain) > 0

    @staticmethod
    def classify_authority_type(adjudication: BoundaryAdjudication) -> str:
        """Classify the authority type of a boundary."""
        if adjudication.authority_basis == AuthorityBasis.PROTOCOL_DERIVATION:
            return "protocol_authority"
        elif adjudication.authority_basis == AuthorityBasis.EXPLICIT_DELEGATION:
            return "delegated_authority"
        elif adjudication.authority_basis == AuthorityBasis.TRUST_DECLARATION:
            return "trusted_subsystem_authority"
        elif adjudication.authority_basis == AuthorityBasis.AMBIENT_PRIVILEGE:
            return "ambient_process_privilege"
        elif adjudication.authority_basis == AuthorityBasis.HISTORICAL_PRACTICE:
            return "historical_practice"
        elif adjudication.authority_basis == AuthorityBasis.NONE:
            return "no_authority"
        else:
            return "unknown"


# ---------------------------------------------------------------------------
# Governance Separation
# ---------------------------------------------------------------------------


class GovernanceSeparation:
    """Enforces separation between findings, recommendations, and enforcement."""

    @staticmethod
    def create_finding(
        boundary: AuthorityBoundary,
        classification: BoundaryClassification,
        evidence: str,
    ) -> BoundaryFinding:
        """Create a boundary finding."""
        return BoundaryFinding(
            finding_id=f"find_{uuid.uuid4().hex[:12]}",
            boundary_id=boundary.boundary_id,
            finding_type=classification.value,
            description=f"Boundary {boundary.boundary_id} classified as {classification.value}",
            evidence=evidence,
            severity="info",
        )

    @staticmethod
    def create_recommendation(
        adjudication: BoundaryAdjudication,
        recommendation_type: str,
        description: str,
        rationale: str,
    ) -> GovernanceRecommendation:
        """Create a governance recommendation."""
        return GovernanceRecommendation(
            recommendation_id=f"rec_{uuid.uuid4().hex[:12]}",
            adjudication_id=adjudication.adjudication_id,
            recommendation_type=recommendation_type,
            description=description,
            rationale=rationale,
            required_evidence=adjudication.unresolved_questions,
            constraints=adjudication.boundary.constraints,
        )

    @staticmethod
    def validate_separation(
        finding: BoundaryFinding,
        recommendation: GovernanceRecommendation,
    ) -> dict[str, Any]:
        """Validate that finding and recommendation are properly separated."""
        issues = []

        # Finding must not contain enforcement directive
        if "block" in finding.description.lower() or "deny" in finding.description.lower():
            issues.append("Finding contains enforcement directive")

        # Recommendation must not be authoritative
        if "authorized" in recommendation.description.lower() and "not" not in recommendation.description.lower():
            issues.append("Recommendation may be interpreted as authorization")

        # Recommendation must reference finding
        if finding.boundary_id not in recommendation.description:
            issues.append("Recommendation does not reference the boundary")

        return {
            "separated": len(issues) == 0,
            "issues": issues,
        }


# ---------------------------------------------------------------------------
# Invariant Checks
# ---------------------------------------------------------------------------


class InvariantChecker:
    """Checks authority boundary invariants."""

    @staticmethod
    def check_trust_is_not_authority(adjudication: BoundaryAdjudication) -> dict[str, Any]:
        """TRUST IS NOT AUTHORITY."""
        if adjudication.authority_basis == AuthorityBasis.TRUST_DECLARATION:
            if adjudication.classification == BoundaryClassification.INTENTIONAL_PROTOCOL_AUTHORITY:
                return {
                    "invariant": "TRUST_IS_NOT_AUTHORITY",
                    "held": False,
                    "detail": "Trust declaration cannot be classified as protocol authority",
                }
        return {"invariant": "TRUST_IS_NOT_AUTHORITY", "held": True}

    @staticmethod
    def check_ambient_is_not_protocol(adjudication: BoundaryAdjudication) -> dict[str, Any]:
        """AMBIENT PRIVILEGE IS NOT PROTOCOL AUTHORITY."""
        if adjudication.authority_basis == AuthorityBasis.AMBIENT_PRIVILEGE:
            if adjudication.authority_basis == AuthorityBasis.PROTOCOL_DERIVATION:
                return {
                    "invariant": "AMBIENT_IS_NOT_PROTOCOL",
                    "held": False,
                    "detail": "Ambient privilege cannot be protocol derivation",
                }
        return {"invariant": "AMBIENT_IS_NOT_PROTOCOL", "held": True}

    @staticmethod
    def check_outside_not_forbidden(adjudication: BoundaryAdjudication) -> dict[str, Any]:
        """OUTSIDE THE PROTOCOL IS NOT EQUIVALENT TO FORBIDDEN."""
        if adjudication.authority_basis != AuthorityBasis.PROTOCOL_DERIVATION:
            if adjudication.governance_disposition == GovernanceDisposition.PROHIBITED:
                return {
                    "invariant": "OUTSIDE_NOT_FORBIDDEN",
                    "held": False,
                    "detail": "Non-protocol boundary should not be automatically prohibited",
                }
        return {"invariant": "OUTSIDE_NOT_FORBIDDEN", "held": True}

    @staticmethod
    def check_discovery_does_not_create_enforcement(adjudication: BoundaryAdjudication) -> dict[str, Any]:
        """DISCOVERY OF AN AUTHORITY ESCAPE DOES NOT CREATE AUTHORITY TO ENFORCE ITS REMEDIATION."""
        if adjudication.classification == BoundaryClassification.UNAUTHORIZED_ESCAPE:
            for rec in adjudication.recommendations:
                if "block" in rec.lower() or "deny" in rec.lower() or "prevent" in rec.lower():
                    return {
                        "invariant": "DISCOVERY_DOES_NOT_CREATE_ENFORCEMENT",
                        "held": False,
                        "detail": "Recommendation contains enforcement directive without governance authorization",
                    }
        return {"invariant": "DISCOVERY_DOES_NOT_CREATE_ENFORCEMENT", "held": True}

    @staticmethod
    def check_intent_not_inferred_from_execution(adjudication: BoundaryAdjudication) -> dict[str, Any]:
        """AUTHORITY INTENT MUST NOT BE INFERRED FROM EXECUTION BEHAVIOR ALONE."""
        if adjudication.authority_basis == AuthorityBasis.NONE and adjudication.classification not in (
            BoundaryClassification.INCONCLUSIVE,
            BoundaryClassification.LEGACY_UNGOVERNED,
        ):
            if len(adjudication.runtime_evidence) > 0 and len(adjudication.declarations) == 0:
                return {
                    "invariant": "INTENT_NOT_INFERRED_FROM_EXECUTION",
                    "held": False,
                    "detail": "Authority classification based on runtime evidence without declarations",
                }
        return {"invariant": "INTENT_NOT_INFERRED_FROM_EXECUTION", "held": True}

    @staticmethod
    def check_all(adjudication: BoundaryAdjudication) -> list[dict[str, Any]]:
        """Run all invariant checks."""
        return [
            InvariantChecker.check_trust_is_not_authority(adjudication),
            InvariantChecker.check_ambient_is_not_protocol(adjudication),
            InvariantChecker.check_outside_not_forbidden(adjudication),
            InvariantChecker.check_discovery_does_not_create_enforcement(adjudication),
            InvariantChecker.check_intent_not_inferred_from_execution(adjudication),
        ]
