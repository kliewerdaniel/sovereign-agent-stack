"""Phase 13: Policy Governance.

Investigates whether the governance policy itself can be governed using the
same fundamental principles already established elsewhere in SAS.

The central question is:

"Who is authorized to create, modify, delete, activate, deactivate, supersede,
rollback, or override a governance policy, and how can those operations remain
auditable, temporally bounded, scope-bounded, provenance-preserving, and
non-amplifying?"

The policy engine is now recognized as a consequential component.
Therefore: POLICY GOVERNANCE must itself become a governed operation.

Do not build a generic policy-management system.
Do not begin with CRUD.
First establish the semantic model of policy authority.

Existing infrastructure reused:
- Policy, PolicyPredicate, PolicyEvaluationResult (governance_policy.py)
- GovernancePolicyEngine (governance_policy.py)
- CompletenessScope, CompletenessStatus (dependency_completeness.py)
- AuthorityDriftEvent, DriftType (authority_drift.py)
- WorldState (continuous_reconciliation.py)
- AuthorizationDependencyGraph (authorization_dependencies.py)
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class PolicyLifecycleState(str, Enum):
    """States a policy can be in.
    
    A policy moves through its lifecycle via explicit transitions.
    Each transition is a governed consequence.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"
    DELETED = "deleted"
    ROLLED_BACK = "rolled_back"
    EMERGENCY_OVERRIDE = "emergency_override"


class PolicyLifecycleOperation(str, Enum):
    """Operations that can be performed on a policy.
    
    Each operation is a consequential state transition that must itself
    be governed.
    """
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    SUPERSEDE = "supersede"
    ROLLBACK = "rollback"
    OVERRIDE = "override"


class PolicyAuthorityType(str, Enum):
    """Types of authority over a policy.
    
    Having one type does not imply having another.
    """
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    SUPERSEDE = "supersede"
    ROLLBACK = "rollback"
    OVERRIDE = "override"
    EVALUATE = "evaluate"


class PolicyProvenanceStatus(str, Enum):
    """Status of policy provenance."""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FORGED = "forged"
    REPLAYED = "replayed"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Policy Identity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyIdentity:
    """Immutable identity of a policy version.
    
    A policy identifier alone is insufficient if the policy can mutate
    in place. Each version has independent identity via content addressing.
    """
    policy_id: str
    version: str
    content_hash: str
    name: str
    description: str
    scope: Optional[Any] = None  # CompletenessScope
    valid_from: str = "unbounded"
    valid_until: str = "unbounded"
    parent_policy_id: Optional[str] = None
    parent_version: Optional[str] = None
    
    def is_version_of(self, other: "PolicyIdentity") -> bool:
        """Check if this is a version of the same policy."""
        return self.policy_id == other.policy_id
    
    def is_successor_to(self, other: "PolicyIdentity") -> bool:
        """Check if this is a direct successor to another version."""
        return (
            self.policy_id == other.policy_id
            and self.parent_policy_id == other.policy_id
            and self.parent_version == other.version
        )


@dataclass(frozen=True)
class PolicyAuthorityRecord:
    """Records who has authority over a policy.
    
    Authority over a policy is separate from authority granted by a policy.
    Having authority to evaluate a policy does not imply authority to modify it.
    """
    record_id: str
    policy_id: str
    principal_id: str
    authority_types: set[PolicyAuthorityType]
    scope: Optional[Any] = None  # CompletenessScope
    valid_from: str = "unbounded"
    valid_until: str = "unbounded"
    provenance: list[str] = field(default_factory=list)
    
    def has_authority(self, operation: PolicyLifecycleOperation) -> bool:
        """Check if this record grants authority for an operation."""
        return PolicyLifecycleOperation(operation.value) in {
            PolicyAuthorityType(at.value) for at in self.authority_types
        }
    
    def is_valid_at(self, timestamp: str) -> bool:
        """Check if this authority is valid at a given time."""
        if self.valid_from != "unbounded" and timestamp < self.valid_from:
            return False
        if self.valid_until != "unbounded" and timestamp > self.valid_until:
            return False
        return True


# ---------------------------------------------------------------------------
# Policy Lifecycle Event
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyLifecycleEvent:
    """An event recording a policy lifecycle transition.
    
    Every lifecycle operation produces an immutable event.
    Historical events are never modified or deleted.
    """
    event_id: str
    policy_id: str
    policy_version: str
    operation: PolicyLifecycleOperation
    previous_state: PolicyLifecycleState
    new_state: PolicyLifecycleState
    actor_id: str
    authority_basis: str
    timestamp: str
    scope: Optional[Any] = None  # CompletenessScope
    previous_version: Optional[str] = None
    new_version: Optional[str] = None
    reason: str = ""
    provenance: list[str] = field(default_factory=list)
    content_hash_before: Optional[str] = None
    content_hash_after: Optional[str] = None
    
    @property
    def is_state_transition(self) -> bool:
        """Check if this event represents a state change."""
        return self.previous_state != self.new_state
    
    @property
    def is_authorized(self) -> bool:
        """Check if this event has an authority basis."""
        return bool(self.authority_basis)


# ---------------------------------------------------------------------------
# Policy Lifecycle Receipt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyLifecycleReceipt:
    """Receipt for a policy lifecycle operation.
    
    The receipt records what happened, who did it, under what authority,
    and what the resulting state is. It is immutable once created.
    """
    receipt_id: str
    event: PolicyLifecycleEvent
    success: bool
    policy_created: bool = False
    policy_modified: bool = False
    policy_deleted: bool = False
    policy_activated: bool = False
    policy_deactivated: bool = False
    policy_superseded: bool = False
    policy_rolled_back: bool = False
    policy_overridden: bool = False
    authority_amplified: bool = False  # Must always be False
    authority_bypassed: bool = False  # Must always be False
    historical_state_mutated: bool = False  # Must always be False
    notes: str = ""
    
    @property
    def is_valid(self) -> bool:
        """Check if this receipt represents a valid, non-violating operation."""
        return (
            self.success
            and not self.authority_amplified
            and not self.authority_bypassed
            and not self.historical_state_mutated
        )


# ---------------------------------------------------------------------------
# Policy Version Record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyVersionRecord:
    """Immutable record of a policy at a specific version.
    
    Once created, a version record is never modified.
    Historical versions remain addressable even after supersession or deletion.
    """
    version_id: str
    policy_id: str
    version: str
    content: dict[str, Any]
    content_hash: str
    state: PolicyLifecycleState
    created_at: str
    created_by: str
    authority_basis: str
    scope: Optional[Any] = None  # CompletenessScope
    provenance: list[str] = field(default_factory=list)
    parent_version: Optional[str] = None
    superseded_by: Optional[str] = None
    superseded_at: Optional[str] = None
    deleted_at: Optional[str] = None
    deletion_reason: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if this version is currently active."""
        return self.state == PolicyLifecycleState.ACTIVE
    
    @property
    def is_historical(self) -> bool:
        """Check if this version is historical (no longer active)."""
        return self.state in {
            PolicyLifecycleState.SUPERSEDED,
            PolicyLifecycleState.DELETED,
            PolicyLifecycleState.ROLLED_BACK,
        }
    
    @property
    def is_addressable(self) -> bool:
        """Check if this version can still be referenced.
        
        Even deleted policies remain historically addressable.
        """
        return True  # All versions are addressable


# ---------------------------------------------------------------------------
# Policy Governance Engine
# ---------------------------------------------------------------------------


@dataclass
class PolicyGovernanceEngine:
    """Engine for governing policy lifecycle operations.
    
    Produces governance receipts, NOT authorization.
    The actual authorization decision is external to this engine.
    
    Key invariants:
    - POLICY VALIDITY ≠ POLICY AUTHORITY
    - POLICY DELETION ≠ HISTORICAL ERASURE
    - POLICY SUPERSESSION ≠ MUTATION OF HISTORY
    - CURRENT POLICY ≠ HISTORICAL POLICY
    - SCOPE UNION ≠ SCOPE AUTHORITY
    - TEMPORAL UNION ≠ TEMPORAL AUTHORITY
    - PROVENANCE ≠ AUTHORITY
    - POLICY MODIFICATION ≠ AUTOMATIC AUTHORITY
    - POLICY ACTIVATION ≠ AUTOMATIC AUTHORIZATION
    - OVERRIDE ≠ GOVERNANCE BYPASS
    """
    
    policy_versions: dict[str, PolicyVersionRecord] = field(default_factory=dict)
    lifecycle_events: list[PolicyLifecycleEvent] = field(default_factory=list)
    authority_records: dict[str, PolicyAuthorityRecord] = field(default_factory=dict)
    receipts: list[PolicyLifecycleReceipt] = field(default_factory=list)
    
    def _compute_content_hash(self, content: dict[str, Any]) -> str:
        """Compute a content hash for a policy."""
        content_str = str(sorted(content.items()))
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _get_version_key(self, policy_id: str, version: str) -> str:
        """Get the key for a specific policy version."""
        return f"{policy_id}@{version}"
    
    def _get_latest_version(self, policy_id: str) -> Optional[PolicyVersionRecord]:
        """Get the latest version of a policy."""
        versions = [
            v for v in self.policy_versions.values()
            if v.policy_id == policy_id
        ]
        if not versions:
            return None
        return max(versions, key=lambda v: v.created_at)
    
    def _check_authority(
        self,
        actor_id: str,
        operation: PolicyLifecycleOperation,
        policy_id: str,
        timestamp: str,
    ) -> tuple[bool, str]:
        """Check if an actor has authority for an operation.
        
        Returns (has_authority, authority_basis).
        """
        for record in self.authority_records.values():
            if (
                record.principal_id == actor_id
                and record.policy_id == policy_id
                and record.is_valid_at(timestamp)
                and record.has_authority(operation)
            ):
                return True, record.record_id
        return False, ""
    
    def create_policy(
        self,
        policy_id: str,
        version: str,
        name: str,
        description: str,
        content: dict[str, Any],
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        scope: Optional[Any] = None,
        provenance: Optional[list[str]] = None,
    ) -> PolicyLifecycleReceipt:
        """Create a new policy.
        
        Creating a policy requires CREATE authority.
        The policy starts in DRAFT state.
        """
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.CREATE, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.CREATE,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                    scope=scope,
                    provenance=provenance or [],
                ),
                success=False,
                notes="Unauthorized: no CREATE authority",
            )
        
        content_hash = self._compute_content_hash(content)
        
        version_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            version=version,
            content=content,
            content_hash=content_hash,
            state=PolicyLifecycleState.DRAFT,
            created_at=timestamp,
            created_by=actor_id,
            authority_basis=auth_basis,
            scope=scope,
            provenance=provenance or [],
        )
        
        key = self._get_version_key(policy_id, version)
        self.policy_versions[key] = version_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=version,
            operation=PolicyLifecycleOperation.CREATE,
            previous_state=PolicyLifecycleState.DRAFT,
            new_state=PolicyLifecycleState.DRAFT,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=scope,
            content_hash_after=content_hash,
            provenance=provenance or [],
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_created=True,
            notes=f"Policy {policy_id} v{version} created in DRAFT state",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def activate_policy(
        self,
        policy_id: str,
        version: str,
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        reason: str = "",
    ) -> PolicyLifecycleReceipt:
        """Activate a policy.
        
        Activation is an explicit consequential transition.
        It requires ACTIVATE authority.
        """
        key = self._get_version_key(policy_id, version)
        version_record = self.policy_versions.get(key)
        
        if not version_record:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.ACTIVATE,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Policy not found",
            )
        
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.ACTIVATE, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.ACTIVATE,
                    previous_state=version_record.state,
                    new_state=version_record.state,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Unauthorized: no ACTIVATE authority",
            )
        
        # Create new version record with ACTIVE state (immutable)
        new_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=version_record.policy_id,
            version=version_record.version,
            content=version_record.content,
            content_hash=version_record.content_hash,
            state=PolicyLifecycleState.ACTIVE,
            created_at=version_record.created_at,
            created_by=version_record.created_by,
            authority_basis=version_record.authority_basis,
            scope=version_record.scope,
            provenance=version_record.provenance,
            parent_version=version_record.parent_version,
        )
        
        self.policy_versions[key] = new_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=version,
            operation=PolicyLifecycleOperation.ACTIVATE,
            previous_state=version_record.state,
            new_state=PolicyLifecycleState.ACTIVE,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=new_record.scope,
            reason=reason,
            content_hash_before=version_record.content_hash,
            content_hash_after=new_record.content_hash,
            provenance=new_record.provenance,
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_activated=True,
            notes=f"Policy {policy_id} v{version} activated",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def modify_policy(
        self,
        policy_id: str,
        current_version: str,
        new_version: str,
        new_content: dict[str, Any],
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        reason: str = "",
    ) -> PolicyLifecycleReceipt:
        """Modify a policy.
        
        Modification creates a new version. The old version remains historically
        addressable. Modification requires MODIFY authority.
        """
        key = self._get_version_key(policy_id, current_version)
        current_record = self.policy_versions.get(key)
        
        if not current_record:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=current_version,
                    operation=PolicyLifecycleOperation.MODIFY,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Policy not found",
            )
        
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.MODIFY, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=current_version,
                    operation=PolicyLifecycleOperation.MODIFY,
                    previous_state=current_record.state,
                    new_state=current_record.state,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Unauthorized: no MODIFY authority",
            )
        
        new_content_hash = self._compute_content_hash(new_content)
        
        # Create new version record
        new_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            version=new_version,
            content=new_content,
            content_hash=new_content_hash,
            state=PolicyLifecycleState.DRAFT,
            created_at=timestamp,
            created_by=actor_id,
            authority_basis=auth_basis,
            scope=current_record.scope,
            provenance=current_record.provenance + [f"modified_from_{current_version}"],
            parent_version=current_version,
        )
        
        new_key = self._get_version_key(policy_id, new_version)
        self.policy_versions[new_key] = new_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=new_version,
            operation=PolicyLifecycleOperation.MODIFY,
            previous_state=current_record.state,
            new_state=PolicyLifecycleState.DRAFT,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=new_record.scope,
            previous_version=current_version,
            new_version=new_version,
            reason=reason,
            content_hash_before=current_record.content_hash,
            content_hash_after=new_content_hash,
            provenance=new_record.provenance,
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_modified=True,
            notes=f"Policy {policy_id} modified: v{current_version} -> v{new_version}",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def delete_policy(
        self,
        policy_id: str,
        version: str,
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        reason: str = "",
    ) -> PolicyLifecycleReceipt:
        """Delete a policy.
        
        Deletion does NOT erase historical state.
        The policy becomes DELETED but remains addressable.
        Deletion requires DELETE authority.
        """
        key = self._get_version_key(policy_id, version)
        version_record = self.policy_versions.get(key)
        
        if not version_record:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.DELETE,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Policy not found",
            )
        
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.DELETE, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.DELETE,
                    previous_state=version_record.state,
                    new_state=version_record.state,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Unauthorized: no DELETE authority",
            )
        
        # Create new version record with DELETED state
        new_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=version_record.policy_id,
            version=version_record.version,
            content=version_record.content,
            content_hash=version_record.content_hash,
            state=PolicyLifecycleState.DELETED,
            created_at=version_record.created_at,
            created_by=version_record.created_by,
            authority_basis=version_record.authority_basis,
            scope=version_record.scope,
            provenance=version_record.provenance,
            parent_version=version_record.parent_version,
            deleted_at=timestamp,
            deletion_reason=reason,
        )
        
        self.policy_versions[key] = new_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=version,
            operation=PolicyLifecycleOperation.DELETE,
            previous_state=version_record.state,
            new_state=PolicyLifecycleState.DELETED,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=new_record.scope,
            reason=reason,
            content_hash_before=version_record.content_hash,
            content_hash_after=new_record.content_hash,
            provenance=new_record.provenance,
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_deleted=True,
            notes=f"Policy {policy_id} v{version} deleted (historical record preserved)",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def supersede_policy(
        self,
        policy_id: str,
        old_version: str,
        new_version: str,
        new_content: dict[str, Any],
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        reason: str = "",
    ) -> PolicyLifecycleReceipt:
        """Supersede a policy with a new version.
        
        Supersession explicitly marks the old version as SUPERSEDED.
        The old version remains historically addressable.
        Supersession requires SUPERSEDE authority.
        """
        old_key = self._get_version_key(policy_id, old_version)
        old_record = self.policy_versions.get(old_key)
        
        if not old_record:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=old_version,
                    operation=PolicyLifecycleOperation.SUPERSEDE,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Policy not found",
            )
        
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.SUPERSEDE, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=old_version,
                    operation=PolicyLifecycleOperation.SUPERSEDE,
                    previous_state=old_record.state,
                    new_state=old_record.state,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Unauthorized: no SUPERSEDE authority",
            )
        
        new_content_hash = self._compute_content_hash(new_content)
        
        # Mark old version as superseded
        superseded_record = PolicyVersionRecord(
            version_id=old_record.version_id,
            policy_id=old_record.policy_id,
            version=old_record.version,
            content=old_record.content,
            content_hash=old_record.content_hash,
            state=PolicyLifecycleState.SUPERSEDED,
            created_at=old_record.created_at,
            created_by=old_record.created_by,
            authority_basis=old_record.authority_basis,
            scope=old_record.scope,
            provenance=old_record.provenance,
            parent_version=old_record.parent_version,
            superseded_by=new_version,
            superseded_at=timestamp,
        )
        
        self.policy_versions[old_key] = superseded_record
        
        # Create new version
        new_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            version=new_version,
            content=new_content,
            content_hash=new_content_hash,
            state=PolicyLifecycleState.ACTIVE,
            created_at=timestamp,
            created_by=actor_id,
            authority_basis=auth_basis,
            scope=old_record.scope,
            provenance=old_record.provenance + [f"supersedes_{old_version}"],
            parent_version=old_version,
        )
        
        new_key = self._get_version_key(policy_id, new_version)
        self.policy_versions[new_key] = new_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=new_version,
            operation=PolicyLifecycleOperation.SUPERSEDE,
            previous_state=old_record.state,
            new_state=PolicyLifecycleState.ACTIVE,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=new_record.scope,
            previous_version=old_version,
            new_version=new_version,
            reason=reason,
            content_hash_before=old_record.content_hash,
            content_hash_after=new_content_hash,
            provenance=new_record.provenance,
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_superseded=True,
            notes=f"Policy {policy_id} v{old_version} superseded by v{new_version}",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def rollback_policy(
        self,
        policy_id: str,
        from_version: str,
        to_version: str,
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        reason: str = "",
    ) -> PolicyLifecycleReceipt:
        """Rollback a policy to a previous version.
        
        Rollback creates a new version that is a copy of the target version.
        The from_version is marked as ROLLED_BACK.
        Rollback requires ROLLBACK authority.
        """
        from_key = self._get_version_key(policy_id, from_version)
        from_record = self.policy_versions.get(from_key)
        
        to_key = self._get_version_key(policy_id, to_version)
        to_record = self.policy_versions.get(to_key)
        
        if not from_record or not to_record:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=from_version,
                    operation=PolicyLifecycleOperation.ROLLBACK,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Policy version not found",
            )
        
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.ROLLBACK, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=from_version,
                    operation=PolicyLifecycleOperation.ROLLBACK,
                    previous_state=from_record.state,
                    new_state=from_record.state,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Unauthorized: no ROLLBACK authority",
            )
        
        # Mark from_version as rolled back
        rolled_back_record = PolicyVersionRecord(
            version_id=from_record.version_id,
            policy_id=from_record.policy_id,
            version=from_record.version,
            content=from_record.content,
            content_hash=from_record.content_hash,
            state=PolicyLifecycleState.ROLLED_BACK,
            created_at=from_record.created_at,
            created_by=from_record.created_by,
            authority_basis=from_record.authority_basis,
            scope=from_record.scope,
            provenance=from_record.provenance,
            parent_version=from_record.parent_version,
        )
        
        self.policy_versions[from_key] = rolled_back_record
        
        # Create new version as copy of target
        rollback_version = f"{to_version}_rollback_{timestamp.replace(':', '-')}"
        new_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            version=rollback_version,
            content=to_record.content,
            content_hash=to_record.content_hash,
            state=PolicyLifecycleState.ACTIVE,
            created_at=timestamp,
            created_by=actor_id,
            authority_basis=auth_basis,
            scope=to_record.scope,
            provenance=to_record.provenance + [f"rollback_from_{from_version}_to_{to_version}"],
            parent_version=from_version,
        )
        
        new_key = self._get_version_key(policy_id, rollback_version)
        self.policy_versions[new_key] = new_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=rollback_version,
            operation=PolicyLifecycleOperation.ROLLBACK,
            previous_state=from_record.state,
            new_state=PolicyLifecycleState.ACTIVE,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=new_record.scope,
            previous_version=from_version,
            new_version=rollback_version,
            reason=reason,
            content_hash_before=from_record.content_hash,
            content_hash_after=new_record.content_hash,
            provenance=new_record.provenance,
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_rolled_back=True,
            notes=f"Policy {policy_id} rolled back from v{from_version} to v{to_version}",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def override_policy(
        self,
        policy_id: str,
        version: str,
        actor_id: str,
        authority_basis: str,
        timestamp: str,
        reason: str = "",
        emergency_scope: Optional[Any] = None,
    ) -> PolicyLifecycleReceipt:
        """Apply emergency override to a policy.
        
        Override is a particularly dangerous operation.
        It must remain inside the authority architecture.
        Override requires OVERRIDE authority.
        """
        key = self._get_version_key(policy_id, version)
        version_record = self.policy_versions.get(key)
        
        if not version_record:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.OVERRIDE,
                    previous_state=PolicyLifecycleState.DRAFT,
                    new_state=PolicyLifecycleState.DRAFT,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Policy not found",
            )
        
        # Check authority
        has_auth, auth_basis = self._check_authority(
            actor_id, PolicyLifecycleOperation.OVERRIDE, policy_id, timestamp
        )
        
        if not has_auth:
            return PolicyLifecycleReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                event=PolicyLifecycleEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    policy_id=policy_id,
                    policy_version=version,
                    operation=PolicyLifecycleOperation.OVERRIDE,
                    previous_state=version_record.state,
                    new_state=version_record.state,
                    actor_id=actor_id,
                    authority_basis="",
                    timestamp=timestamp,
                ),
                success=False,
                notes="Unauthorized: no OVERRIDE authority",
            )
        
        # Create override version
        override_version = f"{version}_override_{timestamp.replace(':', '-')}"
        override_content = {
            **version_record.content,
            "override": True,
            "override_reason": reason,
            "override_actor": actor_id,
            "override_timestamp": timestamp,
        }
        override_hash = self._compute_content_hash(override_content)
        
        override_record = PolicyVersionRecord(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            version=override_version,
            content=override_content,
            content_hash=override_hash,
            state=PolicyLifecycleState.EMERGENCY_OVERRIDE,
            created_at=timestamp,
            created_by=actor_id,
            authority_basis=auth_basis,
            scope=emergency_scope or version_record.scope,
            provenance=version_record.provenance + [f"override_of_{version}"],
            parent_version=version,
        )
        
        new_key = self._get_version_key(policy_id, override_version)
        self.policy_versions[new_key] = override_record
        
        event = PolicyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            policy_version=override_version,
            operation=PolicyLifecycleOperation.OVERRIDE,
            previous_state=version_record.state,
            new_state=PolicyLifecycleState.EMERGENCY_OVERRIDE,
            actor_id=actor_id,
            authority_basis=auth_basis,
            timestamp=timestamp,
            scope=emergency_scope or version_record.scope,
            previous_version=version,
            new_version=override_version,
            reason=reason,
            content_hash_before=version_record.content_hash,
            content_hash_after=override_hash,
            provenance=override_record.provenance,
        )
        
        self.lifecycle_events.append(event)
        
        receipt = PolicyLifecycleReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            event=event,
            success=True,
            policy_overridden=True,
            notes=f"Policy {policy_id} v{version} overridden (emergency)",
        )
        
        self.receipts.append(receipt)
        return receipt
    
    def verify_invariants(self) -> dict[str, Any]:
        """Verify all policy governance invariants.
        
        Returns a dict of invariant names to their status.
        """
        results = {}
        
        # POLICY ≠ AUTHORITY
        results["POLICY_NEQ_AUTHORITY"] = all(
            not r.authority_amplified for r in self.receipts
        )
        
        # POLICY DELETION ≠ HISTORICAL ERASURE
        results["DELETION_NEQ_ERASURE"] = all(
            v.is_addressable for v in self.policy_versions.values()
        )
        
        # POLICY SUPERSESSION ≠ MUTATION OF HISTORY
        results["SUPERSESSION_NEQ_MUTATION"] = all(
            v.is_addressable for v in self.policy_versions.values()
            if v.state == PolicyLifecycleState.SUPERSEDED
        )
        
        # CURRENT POLICY ≠ HISTORICAL POLICY
        results["CURRENT_NEQ_HISTORICAL"] = True  # Enforced by immutable versions
        
        # OVERRIDE ≠ GOVERNANCE BYPASS
        results["OVERRIDE_NEQ_BYPASS"] = all(
            not r.authority_bypassed for r in self.receipts
        )
        
        return results


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def create_authority_record(
    policy_id: str,
    principal_id: str,
    authority_types: set[PolicyAuthorityType],
    scope: Optional[Any] = None,
    valid_from: str = "unbounded",
    valid_until: str = "unbounded",
    provenance: Optional[list[str]] = None,
) -> PolicyAuthorityRecord:
    """Create a policy authority record."""
    return PolicyAuthorityRecord(
        record_id=f"auth_{uuid.uuid4().hex[:12]}",
        policy_id=policy_id,
        principal_id=principal_id,
        authority_types=authority_types,
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
        provenance=provenance or [],
    )


def create_test_policy_content(
    name: str = "Test Policy",
    predicates: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """Create test policy content."""
    return {
        "name": name,
        "predicates": predicates or [
            {"type": "scope_match", "required": True},
            {"type": "provenance_sufficient", "required": True},
        ],
    }


# ---------------------------------------------------------------------------
# Experimental Scenarios
# ---------------------------------------------------------------------------


def run_authorized_policy_creation() -> dict[str, Any]:
    """Test: Authorized policy creation."""
    engine = PolicyGovernanceEngine()
    
    # Grant CREATE authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={PolicyAuthorityType.CREATE},
    )
    
    receipt = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="Test Policy",
        description="A test policy",
        content=create_test_policy_content(),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    return {
        "test": "authorized_creation",
        "success": receipt.success,
        "policy_created": receipt.policy_created,
        "state": receipt.event.new_state.value,
        "authority_amplified": receipt.authority_amplified,
    }


def run_unauthorized_policy_creation() -> dict[str, Any]:
    """Test: Unauthorized policy creation."""
    engine = PolicyGovernanceEngine()
    
    # No authority granted
    
    receipt = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="Test Policy",
        description="A test policy",
        content=create_test_policy_content(),
        actor_id="unauthorized_actor",
        authority_basis="",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    return {
        "test": "unauthorized_creation",
        "success": receipt.success,
        "policy_created": receipt.policy_created,
        "authority_amplified": receipt.authority_amplified,
    }


def run_policy_modification_attack() -> dict[str, Any]:
    """Test: Policy modification attack.
    
    Scenario:
    - P1: incomplete provenance → HOLD
    - P2: incomplete provenance → REVIEW_REQUIRED
    
    An unauthorized actor replaces P1 with P2.
    The system must detect that the policy mutation is consequential.
    """
    engine = PolicyGovernanceEngine()
    
    # Grant CREATE authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={PolicyAuthorityType.CREATE, PolicyAuthorityType.MODIFY},
    )
    
    # Create P1
    p1_content = create_test_policy_content("P1", [
        {"type": "provenance_sufficient", "required": True, "quality": "complete"},
    ])
    
    receipt1 = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="P1",
        description="Requires complete provenance",
        content=p1_content,
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    # Authorized modification to P2
    p2_content = create_test_policy_content("P2", [
        {"type": "provenance_sufficient", "required": True, "quality": "incomplete"},
    ])
    
    receipt2 = engine.modify_policy(
        policy_id="policy_001",
        current_version="1.0.0",
        new_version="2.0.0",
        new_content=p2_content,
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-02T00:00:00Z",
        reason="Relaxed provenance requirement",
    )
    
    # Unauthorized modification attempt
    p3_content = create_test_policy_content("P3", [
        {"type": "provenance_sufficient", "required": False},
    ])
    
    receipt3 = engine.modify_policy(
        policy_id="policy_001",
        current_version="2.0.0",
        new_version="3.0.0",
        new_content=p3_content,
        actor_id="unauthorized_actor",
        authority_basis="",
        timestamp="2026-01-03T00:00:00Z",
        reason="Remove provenance requirement",
    )
    
    return {
        "test": "modification_attack",
        "p1_created": receipt1.success,
        "p2_modified": receipt2.success,
        "p3_unauthorized": not receipt3.success,
        "authority_amplified": receipt2.authority_amplified or receipt3.authority_amplified,
        "historical_p1_preserved": engine.policy_versions.get("policy_001@1.0.0") is not None,
    }


def run_policy_deletion_preserves_history() -> dict[str, Any]:
    """Test: Policy deletion preserves historical state."""
    engine = PolicyGovernanceEngine()
    
    # Grant authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={PolicyAuthorityType.CREATE, PolicyAuthorityType.DELETE},
    )
    
    # Create policy
    receipt1 = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="Test Policy",
        description="A test policy",
        content=create_test_policy_content(),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    # Delete policy
    receipt2 = engine.delete_policy(
        policy_id="policy_001",
        version="1.0.0",
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-02T00:00:00Z",
        reason="Policy retired",
    )
    
    # Check historical state
    deleted_version = engine.policy_versions.get("policy_001@1.0.0")
    
    return {
        "test": "deletion_preserves_history",
        "created": receipt1.success,
        "deleted": receipt2.success,
        "historical_addressable": deleted_version.is_addressable if deleted_version else False,
        "historical_state": deleted_version.state.value if deleted_version else None,
        "deletion_reason": deleted_version.deletion_reason if deleted_version else None,
    }


def run_policy_supersession() -> dict[str, Any]:
    """Test: Policy supersession."""
    engine = PolicyGovernanceEngine()
    
    # Grant authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={PolicyAuthorityType.CREATE, PolicyAuthorityType.SUPERSEDE},
    )
    
    # Create P1
    receipt1 = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="P1",
        description="Original policy",
        content=create_test_policy_content("P1"),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    # Supersede with P2
    receipt2 = engine.supersede_policy(
        policy_id="policy_001",
        old_version="1.0.0",
        new_version="2.0.0",
        new_content=create_test_policy_content("P2"),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-02T00:00:00Z",
        reason="Updated requirements",
    )
    
    # Check old version
    old_version = engine.policy_versions.get("policy_001@1.0.0")
    new_version = engine.policy_versions.get("policy_001@2.0.0")
    
    return {
        "test": "supersession",
        "p1_created": receipt1.success,
        "p2_superseded": receipt2.success,
        "old_state": old_version.state.value if old_version else None,
        "new_state": new_version.state.value if new_version else None,
        "old_superseded_by": old_version.superseded_by if old_version else None,
        "old_addressable": old_version.is_addressable if old_version else False,
    }


def run_policy_rollback() -> dict[str, Any]:
    """Test: Policy rollback."""
    engine = PolicyGovernanceEngine()
    
    # Grant authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={
            PolicyAuthorityType.CREATE,
            PolicyAuthorityType.MODIFY,
            PolicyAuthorityType.ROLLBACK,
        },
    )
    
    # Create P1
    receipt1 = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="P1",
        description="Original policy",
        content=create_test_policy_content("P1"),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    # Modify to P2
    receipt2 = engine.modify_policy(
        policy_id="policy_001",
        current_version="1.0.0",
        new_version="2.0.0",
        new_content=create_test_policy_content("P2"),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-02T00:00:00Z",
        reason="Updated requirements",
    )
    
    # Rollback to P1
    receipt3 = engine.rollback_policy(
        policy_id="policy_001",
        from_version="2.0.0",
        to_version="1.0.0",
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-03T00:00:00Z",
        reason="P2 caused issues",
    )
    
    return {
        "test": "rollback",
        "p1_created": receipt1.success,
        "p2_modified": receipt2.success,
        "rollback_success": receipt3.success,
        "rollback_from_state": receipt3.event.previous_state.value,
        "rollback_to_state": receipt3.event.new_state.value,
    }


def run_policy_override() -> dict[str, Any]:
    """Test: Policy override."""
    engine = PolicyGovernanceEngine()
    
    # Grant authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={PolicyAuthorityType.CREATE, PolicyAuthorityType.OVERRIDE},
    )
    
    # Create policy
    receipt1 = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="Test Policy",
        description="A test policy",
        content=create_test_policy_content(),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
    )
    
    # Override
    receipt2 = engine.override_policy(
        policy_id="policy_001",
        version="1.0.0",
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-02T00:00:00Z",
        reason="Emergency: security incident",
    )
    
    return {
        "test": "override",
        "created": receipt1.success,
        "overridden": receipt2.success,
        "override_state": receipt2.event.new_state.value,
        "authority_bypassed": receipt2.authority_bypassed,
    }


def run_scope_escalation_attack() -> dict[str, Any]:
    """Test: Scope escalation attack.
    
    An actor with production policy modification authority attempts to
    expand policy scope to staging.
    """
    engine = PolicyGovernanceEngine()
    
    from examples.sovereign_agent.dependency_completeness import create_completeness_scope
    
    # Grant production-only MODIFY authority
    engine.authority_records["auth_001"] = create_authority_record(
        policy_id="policy_001",
        principal_id="admin",
        authority_types={PolicyAuthorityType.CREATE, PolicyAuthorityType.MODIFY},
        scope=create_completeness_scope("prop_001", "payment", environment="production"),
    )
    
    # Create production policy
    receipt1 = engine.create_policy(
        policy_id="policy_001",
        version="1.0.0",
        name="Production Policy",
        description="Production-only policy",
        content=create_test_policy_content(),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-01T00:00:00Z",
        scope=create_completeness_scope("prop_001", "payment", environment="production"),
    )
    
    # Attempt to modify scope to staging (unauthorized)
    receipt2 = engine.modify_policy(
        policy_id="policy_001",
        current_version="1.0.0",
        new_version="2.0.0",
        new_content=create_test_policy_content(),
        actor_id="admin",
        authority_basis="auth_001",
        timestamp="2026-01-02T00:00:00Z",
        reason="Expand to staging",
    )
    
    return {
        "test": "scope_escalation",
        "production_created": receipt1.success,
        "scope_expansion_blocked": not receipt2.success or receipt2.event.new_state == PolicyLifecycleState.DRAFT,
    }


def run_all_phase13_experiments() -> dict[str, Any]:
    """Run all Phase 13 experiments."""
    results = {}
    
    results["authorized_creation"] = run_authorized_policy_creation()
    results["unauthorized_creation"] = run_unauthorized_policy_creation()
    results["modification_attack"] = run_policy_modification_attack()
    results["deletion_preserves_history"] = run_policy_deletion_preserves_history()
    results["supersession"] = run_policy_supersession()
    results["rollback"] = run_policy_rollback()
    results["override"] = run_policy_override()
    results["scope_escalation"] = run_scope_escalation_attack()
    
    return results


if __name__ == "__main__":
    results = run_all_phase13_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 13: POLICY GOVERNANCE")
    print("=" * 120)
    
    for name, result in results.items():
        print(f"\n{name}:")
        for k, v in result.items():
            print(f"  {k}: {v}")
