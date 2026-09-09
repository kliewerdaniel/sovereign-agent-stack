"""Authority Drift & Continuous Reconciliation.

Models temporal authority drift, staleness, debt, and continuous reconciliation.

Central thesis:
    AUTHORITY IS NOT STATIC CONFIGURATION. AUTHORITY IS A TEMPORALLY BOUNDED
    CLAIM ABOUT A CONSEQUENTIAL SYSTEM.

A previously valid authority state must not automatically remain valid after
the underlying system, delegation, policy, credential, topology, runtime
behavior, or governance changes.

New invariants:
    CURRENT AUTHORITY DOES NOT RETROACTIVELY ALTER HISTORICAL AUTHORITY.
    FUTURE AUTHORITY DOES NOT JUSTIFY PAST CONSEQUENCES.
    DRIFT DETECTION DOES NOT CREATE REVOCATION AUTHORITY.
    STALENESS DOES NOT IMPLY INVALIDITY WITHOUT A GOVERNANCE RULE.
    LATEST OBSERVATION DOES NOT IMPLY EPISTEMIC SUPERIORITY.
    TEMPORAL ORDER DOES NOT IMPLY AUTHORITY.
    AUTHORITY VALIDITY IS TEMPORALLY BOUNDED.
    INCOMPLETE TEMPORAL PROVENANCE PRODUCES BOUNDED UNCERTAINTY.
    RECONCILIATION DOES NOT CREATE AUTHORITY.
    AUTHORITY DEBT DOES NOT CREATE ENFORCEMENT AUTHORITY.
    HISTORICAL ARTIFACTS ARE IMMUTABLE.
    CURRENT GOVERNANCE AND HISTORICAL GOVERNANCE ARE DISTINCT EPISTEMIC OBJECTS.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class DriftType(str, Enum):
    """Types of authority drift."""
    NO_DRIFT = "no_drift"
    DOCUMENTATION_DRIFT = "documentation_drift"
    IMPLEMENTATION_DRIFT = "implementation_drift"
    RUNTIME_DRIFT = "runtime_drift"
    AUTHORITY_DRIFT = "authority_drift"
    GOVERNANCE_DRIFT = "governance_drift"
    PROVENANCE_DRIFT = "provenance_drift"
    MULTI_DIMENSIONAL_DRIFT = "multi_dimensional_drift"
    INCONCLUSIVE_DRIFT = "inconclusive_drift"


class DriftClassification(str, Enum):
    """Classification of drift."""
    NONE = "none"
    BENIGN = "benign"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"
    INCONCLUSIVE = "inconclusive"


class ReconciliationState(str, Enum):
    """State of reconciliation."""
    RECONCILED = "reconciled"
    DRIFT_DETECTED = "drift_detected"
    INCONCLUSIVE = "inconclusive"
    CONFLICT = "conflict"
    PENDING_REVIEW = "pending_review"


class EpistemicState(str, Enum):
    """Epistemic state of a claim."""
    OBSERVED = "observed"
    INFERRED = "inferred"
    SUPPORTED = "supported"
    INCONCLUSIVE = "inconclusive"
    REJECTED = "rejected"


class ConsequenceType(str, Enum):
    """Types of consequences."""
    PAYMENT = "payment"
    REFUND = "refund"
    SETTLEMENT = "settlement"
    NOTIFICATION = "notification"
    LEDGER_MUTATION = "ledger_mutation"
    CREDENTIAL_ACCESS = "credential_access"
    IDENTITY_MUTATION = "identity_mutation"
    DATA_EXFILTRATION = "data_exfiltration"
    SERVICE_DEGRADATION = "service_degradation"
    CONFIGURATION_MUTATION = "configuration_mutation"
    EXTERNAL_EFFECT = "external_effect"
    INTERNAL_EFFECT = "internal_effect"


class EdgeType(str, Enum):
    """Types of edges."""
    CALL = "call"
    DEPENDENCY = "dependency"
    CONSEQUENCE = "consequence"
    AUTHORITY = "authority"
    DELEGATION = "delegation"
    TRUST = "trust"
    GOVERNANCE = "governance"
    CAPABILITY = "capability"
    PROVENANCE = "provenance"
    TEMPORAL = "temporal"
    ENVIRONMENT = "environment"
    CREDENTIAL = "credential"
    BOUNDARY = "boundary"


# ---------------------------------------------------------------------------
# Authority Snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthoritySnapshot:
    """An immutable snapshot of authority at a specific point in time."""

    snapshot_id: str
    timestamp: str
    actor: str
    component: str
    operation: str
    resource: str
    consequence_type: ConsequenceType
    authority_owner: Optional[str] = None
    authority_basis: Optional[str] = None
    authorization_id: Optional[str] = None
    capability_id: Optional[str] = None
    delegation_id: Optional[str] = None
    policy_id: Optional[str] = None
    domain: Optional[str] = None
    lineage: list[str] = field(default_factory=list)
    temporal_scope: str = "unbounded"
    runtime_path: list[str] = field(default_factory=list)
    static_hypothesis_id: Optional[str] = None
    evidence: list[str] = field(default_factory=list)
    provenance_id: Optional[str] = None
    limitations: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "component": self.component,
            "operation": self.operation,
            "resource": self.resource,
            "consequence_type": self.consequence_type.value,
            "authority_owner": self.authority_owner,
            "authority_basis": self.authority_basis,
            "authorization_id": self.authorization_id,
            "capability_id": self.capability_id,
            "delegation_id": self.delegation_id,
            "policy_id": self.policy_id,
            "domain": self.domain,
            "lineage": self.lineage,
            "temporal_scope": self.temporal_scope,
            "runtime_path": self.runtime_path,
            "static_hypothesis_id": self.static_hypothesis_id,
            "evidence": self.evidence,
            "provenance_id": self.provenance_id,
            "limitations": self.limitations,
            "conditions": self.conditions,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Authority Delta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDelta:
    """Records a change in authority between two snapshots."""

    delta_id: str
    previous_snapshot: AuthoritySnapshot
    current_snapshot: AuthoritySnapshot
    drift_type: DriftType
    drift_classification: DriftClassification
    changed_fields: list[str]
    previous_authority: Optional[str] = None
    current_authority: Optional[str] = None
    previous_governance: Optional[str] = None
    current_governance: Optional[str] = None
    runtime_evidence: list[str] = field(default_factory=list)
    static_evidence: list[str] = field(default_factory=list)
    epistemic_evidence: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "previous_snapshot": self.previous_snapshot.to_dict(),
            "current_snapshot": self.current_snapshot.to_dict(),
            "drift_type": self.drift_type.value,
            "drift_classification": self.drift_classification.value,
            "changed_fields": self.changed_fields,
            "previous_authority": self.previous_authority,
            "current_authority": self.current_authority,
            "previous_governance": self.previous_governance,
            "current_governance": self.current_governance,
            "runtime_evidence": self.runtime_evidence,
            "static_evidence": self.static_evidence,
            "epistemic_evidence": self.epistemic_evidence,
            "provenance_chain": self.provenance_chain,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Authority Drift
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDrift:
    """A finding of authority drift."""

    drift_id: str
    drift_type: DriftType
    drift_classification: DriftClassification
    description: str
    affected_actor: str
    affected_component: str
    affected_consequence: str
    affected_resource: str
    previous_authority: Optional[str] = None
    current_authority: Optional[str] = None
    previous_governance: Optional[str] = None
    current_governance: Optional[str] = None
    temporal_boundary: Optional[str] = None
    runtime_evidence: list[str] = field(default_factory=list)
    static_evidence: list[str] = field(default_factory=list)
    epistemic_evidence: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "drift_id": self.drift_id,
            "drift_type": self.drift_type.value,
            "drift_classification": self.drift_classification.value,
            "description": self.description,
            "affected_actor": self.affected_actor,
            "affected_component": self.affected_component,
            "affected_consequence": self.affected_consequence,
            "affected_resource": self.affected_resource,
            "previous_authority": self.previous_authority,
            "current_authority": self.current_authority,
            "previous_governance": self.previous_governance,
            "current_governance": self.current_governance,
            "temporal_boundary": self.temporal_boundary,
            "runtime_evidence": self.runtime_evidence,
            "static_evidence": self.static_evidence,
            "epistemic_evidence": self.epistemic_evidence,
            "provenance_chain": self.provenance_chain,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Authority Staleness
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityValidityInterval:
    """Temporal bounds of authority validity."""

    interval_id: str
    authority_id: str
    valid_from: str
    valid_until: Optional[str] = None  # None means still valid
    authority_owner: str = ""
    authority_basis: str = ""
    conditions: list[str] = field(default_factory=list)

    @property
    def is_valid_at(self) -> bool:
        """Check if authority is currently valid."""
        now = datetime.utcnow().isoformat()
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "interval_id": self.interval_id,
            "authority_id": self.authority_id,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "authority_owner": self.authority_owner,
            "authority_basis": self.authority_basis,
            "conditions": self.conditions,
            "is_valid_at": self.is_valid_at,
        }


@dataclass(frozen=True)
class AuthorityStalenessFinding:
    """A finding that authority has become stale."""

    finding_id: str
    authority_id: str
    staleness_type: str
    description: str
    previous_state: str
    current_state: str
    temporal_boundary: str
    affected_consequence: str
    evidence: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "authority_id": self.authority_id,
            "staleness_type": self.staleness_type,
            "description": self.description,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "temporal_boundary": self.temporal_boundary,
            "affected_consequence": self.affected_consequence,
            "evidence": self.evidence,
            "provenance_chain": self.provenance_chain,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Authority Debt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDebtItem:
    """A single item of authority debt."""

    debt_id: str
    debt_type: str  # documentation_runtime_divergence, runtime_governance_divergence, etc.
    description: str
    evidence: list[str]
    scope: str
    temporal_interval: str
    affected_consequence: str
    epistemic_status: EpistemicState
    resolution_requirements: list[str]
    provenance_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "debt_id": self.debt_id,
            "debt_type": self.debt_type,
            "description": self.description,
            "evidence": self.evidence,
            "scope": self.scope,
            "temporal_interval": self.temporal_interval,
            "affected_consequence": self.affected_consequence,
            "epistemic_status": self.epistemic_status.value,
            "resolution_requirements": self.resolution_requirements,
            "provenance_id": self.provenance_id,
        }


@dataclass(frozen=True)
class AuthorityDebt:
    """Structured set of unresolved authority discrepancies."""

    debt_report_id: str
    documentation_runtime_divergence: list[AuthorityDebtItem] = field(default_factory=list)
    runtime_governance_divergence: list[AuthorityDebtItem] = field(default_factory=list)
    governance_provenance_gap: list[AuthorityDebtItem] = field(default_factory=list)
    stale_delegation: list[AuthorityDebtItem] = field(default_factory=list)
    unbounded_consequence: list[AuthorityDebtItem] = field(default_factory=list)
    unresolved_owner: list[AuthorityDebtItem] = field(default_factory=list)
    missing_reconstruction: list[AuthorityDebtItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total_debt_items(self) -> int:
        return (
            len(self.documentation_runtime_divergence)
            + len(self.runtime_governance_divergence)
            + len(self.governance_provenance_gap)
            + len(self.stale_delegation)
            + len(self.unbounded_consequence)
            + len(self.unresolved_owner)
            + len(self.missing_reconstruction)
        )

    def to_dict(self) -> dict:
        return {
            "debt_report_id": self.debt_report_id,
            "documentation_runtime_divergence": [d.to_dict() for d in self.documentation_runtime_divergence],
            "runtime_governance_divergence": [d.to_dict() for d in self.runtime_governance_divergence],
            "governance_provenance_gap": [d.to_dict() for d in self.governance_provenance_gap],
            "stale_delegation": [d.to_dict() for d in self.stale_delegation],
            "unbounded_consequence": [d.to_dict() for d in self.unbounded_consequence],
            "unresolved_owner": [d.to_dict() for d in self.unresolved_owner],
            "missing_reconstruction": [d.to_dict() for d in self.missing_reconstruction],
            "total_debt_items": self.total_debt_items,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Drift Finding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DriftFinding:
    """A finding from drift detection."""

    finding_id: str
    drift_type: DriftType
    drift_classification: DriftClassification
    description: str
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    temporal_boundary: str
    affected_actor: str
    affected_component: str
    affected_consequence: str
    affected_resource: str
    evidence: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "drift_type": self.drift_type.value,
            "drift_classification": self.drift_classification.value,
            "description": self.description,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "temporal_boundary": self.temporal_boundary,
            "affected_actor": self.affected_actor,
            "affected_component": self.affected_component,
            "affected_consequence": self.affected_consequence,
            "affected_resource": self.affected_resource,
            "evidence": self.evidence,
            "provenance_chain": self.provenance_chain,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Reconciliation State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconciliationStatus:
    """Status of continuous reconciliation."""

    status_id: str
    timestamp: str
    reconciliation_state: ReconciliationState
    current_authority_state: dict[str, Any]
    historical_authority_state: dict[str, Any]
    authority_delta: Optional[AuthorityDelta] = None
    drift_findings: list[DriftFinding] = field(default_factory=list)
    authority_debt: Optional[AuthorityDebt] = None
    stale_authority: list[AuthorityStalenessFinding] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    provenance_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status_id": self.status_id,
            "timestamp": self.timestamp,
            "reconciliation_state": self.reconciliation_state.value,
            "current_authority_state": self.current_authority_state,
            "historical_authority_state": self.historical_authority_state,
            "authority_delta": self.authority_delta.to_dict() if self.authority_delta else None,
            "drift_findings": [f.to_dict() for f in self.drift_findings],
            "authority_debt": self.authority_debt.to_dict() if self.authority_debt else None,
            "stale_authority": [s.to_dict() for s in self.stale_authority],
            "unresolved_questions": self.unresolved_questions,
            "limitations": self.limitations,
            "provenance_chain": self.provenance_chain,
        }


# ---------------------------------------------------------------------------
# Topology Delta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TopologyDelta:
    """Records a change in topology."""

    delta_id: str
    previous_timestamp: str
    current_timestamp: str
    added_edges: list[dict[str, Any]] = field(default_factory=list)
    removed_edges: list[dict[str, Any]] = field(default_factory=list)
    modified_edges: list[dict[str, Any]] = field(default_factory=list)
    added_nodes: list[dict[str, Any]] = field(default_factory=list)
    removed_nodes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "previous_timestamp": self.previous_timestamp,
            "current_timestamp": self.current_timestamp,
            "added_edges": self.added_edges,
            "removed_edges": self.removed_edges,
            "modified_edges": self.modified_edges,
            "added_nodes": self.added_nodes,
            "removed_nodes": self.removed_nodes,
        }


# ---------------------------------------------------------------------------
# Governance Delta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GovernanceDelta:
    """Records a change in governance."""

    delta_id: str
    previous_timestamp: str
    current_timestamp: str
    added_policies: list[dict[str, Any]] = field(default_factory=list)
    removed_policies: list[dict[str, Any]] = field(default_factory=list)
    modified_policies: list[dict[str, Any]] = field(default_factory=list)
    added_delegations: list[dict[str, Any]] = field(default_factory=list)
    removed_delegations: list[dict[str, Any]] = field(default_factory=list)
    modified_delegations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "previous_timestamp": self.previous_timestamp,
            "current_timestamp": self.current_timestamp,
            "added_policies": self.added_policies,
            "removed_policies": self.removed_policies,
            "modified_policies": self.modified_policies,
            "added_delegations": self.added_delegations,
            "removed_delegations": self.removed_delegations,
            "modified_delegations": self.modified_delegations,
        }


# ---------------------------------------------------------------------------
# Runtime Delta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeDelta:
    """Records a change in runtime behavior."""

    delta_id: str
    previous_timestamp: str
    current_timestamp: str
    added_paths: list[dict[str, Any]] = field(default_factory=list)
    removed_paths: list[dict[str, Any]] = field(default_factory=list)
    modified_paths: list[dict[str, Any]] = field(default_factory=list)
    new_actors: list[str] = field(default_factory=list)
    removed_actors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "previous_timestamp": self.previous_timestamp,
            "current_timestamp": self.current_timestamp,
            "added_paths": self.added_paths,
            "removed_paths": self.removed_paths,
            "modified_paths": self.modified_paths,
            "new_actors": self.new_actors,
            "removed_actors": self.removed_actors,
        }


# ---------------------------------------------------------------------------
# Provenance Delta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProvenanceDelta:
    """Records a change in provenance."""

    delta_id: str
    previous_timestamp: str
    current_timestamp: str
    added_records: list[dict[str, Any]] = field(default_factory=list)
    removed_records: list[dict[str, Any]] = field(default_factory=list)
    modified_records: list[dict[str, Any]] = field(default_factory=list)
    missing_records: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "delta_id": self.delta_id,
            "previous_timestamp": self.previous_timestamp,
            "current_timestamp": self.current_timestamp,
            "added_records": self.added_records,
            "removed_records": self.removed_records,
            "modified_records": self.modified_records,
            "missing_records": self.missing_records,
        }


# ---------------------------------------------------------------------------
# Authority Drift Event
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDriftEvent:
    """A controlled mutation event."""

    event_id: str
    timestamp: str
    event_type: str  # provider_replacement, credential_rotation, feature_flag_activation, etc.
    description: str
    affected_actor: str
    affected_component: str
    previous_state: dict[str, Any]
    new_state: dict[str, Any]
    evidence: list[str] = field(default_factory=list)
    provenance_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "description": self.description,
            "affected_actor": self.affected_actor,
            "affected_component": self.affected_component,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "evidence": self.evidence,
            "provenance_id": self.provenance_id,
        }
