"""Phase 33: Effective Authority Graph Closure Under Authority Change.

Central research question:
    When authority changes after an observed effect has been reconciled,
    can the system preserve the historical reconciliation while correctly
    determining whether that reconciliation remains valid, becomes
    constrained, or requires revalidation under the new authority state?

The fundamental model:

    AUTHORITY STATE T1
            ↓
    EFFECT
            ↓
    RECONCILIATION R1
            ↓
    AUTHORITY CHANGE
            ↓
    AUTHORITY STATE T2
            ↓
    REVALIDATION
            ↓
    CURRENT EPISTEMIC STATE

Critical distinctions:
    HISTORICALLY_VALID ≠ CURRENTLY_VALID
    VALID_AT_EXECUTION ≠ VALID_NOW
    AUTHORITY_CHANGE ≠ RETROACTIVE_HISTORICAL_INVALIDATION
    CURRENT_INVALIDITY ≠ HISTORICAL_INVALIDITY
    FUTURE_AUTHORITY ≠ HISTORICAL_AUTHORITY
    FUTURE_REVOCATION ≠ HISTORICAL_INVALIDITY
    RECONCILIATION ≠ AUTHORIZATION
    RECONCILIATION ≠ AUTHORITY_CREATION

Existing infrastructure reused:
    - AuthorityReconciliation, CorrespondenceStatus, EpistemicStatus (authority_path_graph_reconciliation.py)
    - PolicyLifecycleEvent, PolicyLifecycleState (policy_governance.py)
    - EpistemicStateTransition, EpistemicStateMachine (epistemic_state_consequentiality.py)
    - GraphDriftResult, CompletenessState (authority_under_uncertainty.py)
    - CompletenessClaim, CompletenessStatus (continuous_effect_reconciliation.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Core enumerations
# ---------------------------------------------------------------------------


class AuthorityChangeType(str, Enum):
    """Types of authority state changes."""
    TRUST_ANCHOR_ROTATION = "trust_anchor_rotation"
    TRUST_ANCHOR_REVOCATION = "trust_anchor_revocation"
    TRUST_ANCHOR_REPLACEMENT = "trust_anchor_replacement"
    DELEGATION_REVOCATION = "delegation_revocation"
    DELEGATION_EXPIRATION = "delegation_expiration"
    DELEGATION_SCOPE_NARROWING = "delegation_scope_narrowing"
    DELEGATION_SCOPE_WIDENING = "delegation_scope_widening"
    DELEGATION_RECREATION = "delegation_recreation"
    POLICY_SUPERSESSION = "policy_supersession"
    POLICY_DELETION = "policy_deletion"
    POLICY_RECREATION = "policy_recreation"
    POLICY_AUTHORITY_CHANGE = "policy_authority_change"
    GOVERNANCE_DISPOSITION_CHANGE = "governance_disposition_change"
    CAPABILITY_REVOCATION = "capability_revocation"
    CAPABILITY_EXPIRATION = "capability_expiration"
    CAPABILITY_SCOPE_NARROWING = "capability_scope_narrowing"
    CAPABILITY_RECREATION = "capability_recreation"
    EXECUTION_GATE_CHANGE = "execution_gate_change"
    IDENTITY_BINDING_CHANGE = "identity_binding_change"
    DOMAIN_DELEGATION_CHANGE = "domain_delegation_change"
    EMERGENCY_AUTHORITY_ACTIVATION = "emergency_authority_activation"
    EMERGENCY_AUTHORITY_REVOCATION = "emergency_authority_revocation"
    RECOVERY_AUTHORITY_SUPERSESSION = "recovery_authority_supersession"
    WORKER_DELEGATION_REVOCATION = "worker_delegation_revocation"
    CROSS_DOMAIN_DELEGATION_REVOCATION = "cross_domain_delegation_revocation"
    RUNTIME_TOPOLOGY_CHANGE = "runtime_topology_change"
    GRAPH_BECOMING_INCOMPLETE = "graph_becoming_incomplete"
    GRAPH_BECOMING_COMPLETE = "graph_becoming_complete"
    UNDECLARED_AUTHORITY_APPEARANCE = "undeclared_authority_appearance"
    NO_CHANGE = "no_change"


class TemporalValidityStatus(str, Enum):
    """Temporal validity status of a reconciliation."""
    VALID_AT_EXECUTION_AND_CURRENT = "valid_at_execution_and_current"
    VALID_AT_EXECUTION_EXPIRED_NOW = "valid_at_execution_expired_now"
    VALID_AT_EXECUTION_INVALID_NOW = "valid_at_execution_invalid_now"
    HISTORICAL_ONLY = "historical_only"
    CURRENTLY_VALID = "currently_valid"
    CURRENTLY_INVALID = "currently_invalid"
    CURRENTLY_UNKNOWN = "currently_unknown"
    REVALIDATION_REQUIRED = "revalidation_required"
    SUPERSEDED = "superseded"
    HISTORICAL_PRESERVED = "historical_preserved"
    UNKNOWN = "unknown"


class RevocationType(str, Enum):
    """Types of revocation."""
    EXPLICIT = "explicit"
    EXPIRATION = "expiration"
    SCOPE_CHANGE = "scope_change"
    SUPERSession = "supersession"
    TRUST_ANCHOR_REPLACEMENT = "trust_anchor_replacement"


class AuthorityStateVersion(str, Enum):
    """Version of authority state."""
    T1 = "t1"
    T2 = "t2"
    T3 = "t3"


# ---------------------------------------------------------------------------
# Authority state transition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityStateTransition:
    """An immutable authority state transition event.

    Authority changes are represented as new events, not mutations
    of historical state. Each transition records the prior state
    reference, the new state reference, and the provenance of the change.
    """
    transition_id: str
    change_type: AuthorityChangeType
    timestamp: str
    actor: str
    source: str
    prior_state_ref: str
    new_state_ref: str
    scope: str = ""
    domain: str = ""
    reason: str = ""
    provenance: tuple[str, ...] = ()
    affected_authority_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Authority state at a point in time
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityState:
    """The state of authority at a specific point in time.

    Each state is immutable. Changes create new states.
    Historical states are never modified.
    """
    state_id: str
    version: str
    timestamp: str
    trust_anchor_id: str
    delegation_ids: tuple[str, ...] = ()
    policy_ids: tuple[str, ...] = ()
    capability_ids: tuple[str, ...] = ()
    governance_disposition: str = ""
    execution_gate_policy: str = ""
    scope: str = ""
    domain: str = ""
    is_complete: bool = True
    provenance: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_authority(self, authority_id: str) -> bool:
        """Check if a specific authority exists in this state."""
        return authority_id in self.delegation_ids or authority_id in self.policy_ids or authority_id in self.capability_ids

    def has_delegation(self, delegation_id: str) -> bool:
        """Check if a specific delegation exists in this state."""
        return delegation_id in self.delegation_ids

    def has_capability(self, capability_id: str) -> bool:
        """Check if a specific capability exists in this state."""
        return capability_id in self.capability_ids

    def has_policy(self, policy_id: str) -> bool:
        """Check if a specific policy exists in this state."""
        return policy_id in self.policy_ids


# ---------------------------------------------------------------------------
# Temporal authority reconciliation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalAuthorityReconciliation:
    """A reconciliation with temporal validity tracking.

    This wraps a reconciliation from Phase 32 with temporal semantics.
    The historical reconciliation is preserved. The current validity
    is independently determined.

    Fields:
        temporal_reconciliation_id: unique identifier
        historical_reconciliation: the original reconciliation at T1
        authority_state_t1: authority state at T1
        authority_state_t2: authority state at T2 (if changed)
        transition: the authority state transition (if any)
        historical_validity: whether the reconciliation was valid at execution
        current_validity: whether the reconciliation is currently valid
        temporal_status: overall temporal validity status
        revalidation_required: whether revalidation is needed
        current_interpretation: what the reconciliation means now
        provenance: lineage of the temporal tracking
    """
    temporal_reconciliation_id: str
    historical_reconciliation_id: str
    effect_id: str
    observation_id: str
    authority_state_t1: AuthorityState
    authority_state_t2: AuthorityState | None
    transition: AuthorityStateTransition | None
    historical_validity: bool
    current_validity: TemporalValidityStatus
    revalidation_required: bool
    current_interpretation: str
    provenance: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_historically_valid(self) -> bool:
        return self.historical_validity

    @property
    def is_currently_valid(self) -> bool:
        return self.current_validity == TemporalValidityStatus.CURRENTLY_VALID

    @property
    def is_superseded(self) -> bool:
        return self.current_validity == TemporalValidityStatus.SUPERSEDED

    @property
    def requires_revalidation(self) -> bool:
        return self.revalidation_required


# ---------------------------------------------------------------------------
# Independent oracle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OracleEvaluation:
    """Independent oracle evaluation of a temporal reconciliation.

    The oracle knows the true temporal validity but the implementation
    being tested does not.
    """
    evaluation_id: str
    world_id: str
    historical_validity_match: bool
    current_validity_match: bool
    false_historical_invalidation: bool
    false_current_authority: bool
    false_current_invalidation: bool
    notes: str = ""


# ---------------------------------------------------------------------------
# Temporal closure world
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalClosureWorld:
    """An adversarial world for temporal closure experiments.

    Contains:
        authority_state_t1: authority state at T1
        authority_state_t2: authority state at T2 (if changed)
        transition: the authority state transition (if any)
        has_transition: whether an authority change occurred
        historical_validity: whether the reconciliation was valid at execution
        expected_current_validity: the expected current validity status
        expected_revalidation_required: whether revalidation is expected
        change_type: the type of authority change
        scope: scope of the change
        domain: domain of the change
        identifier_reuse: whether identifiers are reused across states
        is_replay: whether this is a replay attack scenario
        is_future_authority: whether this tests future authority
        is_future_revocation: whether this tests future revocation
        is_scope_narrowing: whether scope was narrowed
        is_scope_widening: whether scope was widened
        is_policy_supersession: whether policy was superseded
        is_policy_deletion: whether policy was deleted
        is_trust_anchor_rotation: whether trust anchor was rotated
        is_identifier_reuse: whether identifiers are reused
        is_graph_incomplete: whether the graph becomes incomplete
        is_graph_complete: whether the graph becomes complete
        is_worker_change: whether worker delegation changed
        is_emergency: whether emergency authority is involved
        is_recovery: whether recovery authority is involved
        is_cross_domain: whether cross-domain authority is involved
    """
    world_id: str
    description: str
    authority_state_t1: AuthorityState
    authority_state_t2: AuthorityState | None
    transition: AuthorityStateTransition | None
    has_transition: bool
    historical_validity: bool
    expected_current_validity: TemporalValidityStatus
    expected_revalidation_required: bool
    change_type: AuthorityChangeType | None = None
    scope: str = ""
    domain: str = ""
    identifier_reuse: bool = False
    is_replay: bool = False
    is_future_authority: bool = False
    is_future_revocation: bool = False
    is_scope_narrowing: bool = False
    is_scope_widening: bool = False
    is_policy_supersession: bool = False
    is_policy_deletion: bool = False
    is_trust_anchor_rotation: bool = False
    is_identifier_reuse: bool = False
    is_graph_incomplete: bool = False
    is_graph_complete: bool = False
    is_worker_change: bool = False
    is_emergency: bool = False
    is_recovery: bool = False
    is_cross_domain: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Temporal closure engine
# ---------------------------------------------------------------------------


class TemporalClosureEngine:
    """Engine for testing temporal authority graph closure.

    Determines what happens to a historical reconciliation when
    authority state changes. Preserves historical truth while
    correctly determining current validity.

    CRITICAL INVARIANTS:
        HISTORICAL RECONCILIATION IS IMMUTABLE
        AUTHORITY CHANGES CREATE NEW STATES
        FUTURE AUTHORITY CANNOT AUTHORIZE PAST EFFECTS
        FUTURE REVOCATION CANNOT INVALIDATE HISTORICALLY VALID EFFECTS
        RECONCILIATION DOES NOT CREATE AUTHORITY
    """

    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.temporal_reconciliations: list[TemporalAuthorityReconciliation] = []

    def evaluate_temporal_closure(
        self,
        authority_state_t1: AuthorityState,
        authority_state_t2: AuthorityState | None,
        transition: AuthorityStateTransition | None,
        has_transition: bool,
        historical_validity: bool,
        expected_current_validity: TemporalValidityStatus,
        expected_revalidation_required: bool,
        change_type: AuthorityChangeType | None = None,
        scope: str = "",
        domain: str = "",
        identifier_reuse: bool = False,
        is_replay: bool = False,
        is_future_authority: bool = False,
        is_future_revocation: bool = False,
        is_scope_narrowing: bool = False,
        is_scope_widening: bool = False,
        is_policy_supersession: bool = False,
        is_policy_deletion: bool = False,
        is_trust_anchor_rotation: bool = False,
        is_graph_incomplete: bool = False,
        is_graph_complete: bool = False,
        is_worker_change: bool = False,
        is_emergency: bool = False,
        is_recovery: bool = False,
        is_cross_domain: bool = False,
    ) -> TemporalAuthorityReconciliation:
        """Evaluate temporal closure for a reconciliation.

        Given a historical reconciliation at T1 and optional authority
        change to T2, determine the current validity.
        """
        # Step 1: Determine current validity based on the change
        current_validity = self._determine_current_validity(
            authority_state_t1=authority_state_t1,
            authority_state_t2=authority_state_t2,
            transition=transition,
            has_transition=has_transition,
            historical_validity=historical_validity,
            change_type=change_type,
            scope=scope,
            domain=domain,
            identifier_reuse=identifier_reuse,
            is_replay=is_replay,
            is_future_authority=is_future_authority,
            is_future_revocation=is_future_revocation,
            is_scope_narrowing=is_scope_narrowing,
            is_scope_widening=is_scope_widening,
            is_policy_supersession=is_policy_supersession,
            is_policy_deletion=is_policy_deletion,
            is_trust_anchor_rotation=is_trust_anchor_rotation,
            is_graph_incomplete=is_graph_incomplete,
            is_graph_complete=is_graph_complete,
            is_worker_change=is_worker_change,
            is_emergency=is_emergency,
            is_recovery=is_recovery,
            is_cross_domain=is_cross_domain,
        )

        # Step 2: Determine if revalidation is required
        revalidation_required = self._determine_revalidation_requirement(
            has_transition=has_transition,
            current_validity=current_validity,
            change_type=change_type,
        )

        # Step 3: Generate current interpretation
        current_interpretation = self._generate_interpretation(
            historical_validity=historical_validity,
            current_validity=current_validity,
            has_transition=has_transition,
            change_type=change_type,
        )

        # Step 4: Create temporal reconciliation
        temporal_rec = TemporalAuthorityReconciliation(
            temporal_reconciliation_id=f"trec-{uuid.uuid4().hex[:12]}",
            historical_reconciliation_id=f"rec-{uuid.uuid4().hex[:12]}",
            effect_id=f"eff-{uuid.uuid4().hex[:8]}",
            observation_id=f"obs-{uuid.uuid4().hex[:8]}",
            authority_state_t1=authority_state_t1,
            authority_state_t2=authority_state_t2,
            transition=transition,
            historical_validity=historical_validity,
            current_validity=current_validity,
            revalidation_required=revalidation_required,
            current_interpretation=current_interpretation,
            provenance=f"{self.engine_id}:temporal",
            notes=self._generate_notes(
                historical_validity, current_validity, has_transition, change_type
            ),
        )

        self.temporal_reconciliations.append(temporal_rec)
        return temporal_rec

    def _determine_current_validity(
        self,
        authority_state_t1: AuthorityState,
        authority_state_t2: AuthorityState | None,
        transition: AuthorityStateTransition | None,
        has_transition: bool,
        historical_validity: bool,
        change_type: AuthorityChangeType | None,
        scope: str,
        domain: str,
        identifier_reuse: bool,
        is_replay: bool,
        is_future_authority: bool,
        is_future_revocation: bool,
        is_scope_narrowing: bool,
        is_scope_widening: bool,
        is_policy_supersession: bool,
        is_policy_deletion: bool,
        is_trust_anchor_rotation: bool,
        is_graph_incomplete: bool,
        is_graph_complete: bool,
        is_worker_change: bool,
        is_emergency: bool,
        is_recovery: bool,
        is_cross_domain: bool,
    ) -> TemporalValidityStatus:
        """Determine the current validity of a reconciliation after authority change."""
        # No transition: validity unchanged
        if not has_transition or transition is None or authority_state_t2 is None:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            else:
                return TemporalValidityStatus.CURRENTLY_INVALID

        # Handle each change type
        if change_type == AuthorityChangeType.NO_CHANGE:
            return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT if historical_validity else TemporalValidityStatus.CURRENTLY_INVALID

        # Future authority: current state has new authority that didn't exist at T1
        if is_future_authority:
            # Current validity is determined by whether authority exists NOW in state_t2
            # Check if the authority was missing at T1 but exists at T2
            if not historical_validity and authority_state_t2.is_complete:
                return TemporalValidityStatus.CURRENTLY_VALID
            return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT if historical_validity else TemporalValidityStatus.CURRENTLY_INVALID

        # Revocation cases
        if change_type in (
            AuthorityChangeType.DELEGATION_REVOCATION,
            AuthorityChangeType.CAPABILITY_REVOCATION,
            AuthorityChangeType.WORKER_DELEGATION_REVOCATION,
            AuthorityChangeType.CROSS_DOMAIN_DELEGATION_REVOCATION,
        ):
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Expiration cases
        if change_type in (
            AuthorityChangeType.DELEGATION_EXPIRATION,
            AuthorityChangeType.CAPABILITY_EXPIRATION,
        ):
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_EXPIRED_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Scope narrowing
        if change_type == AuthorityChangeType.DELEGATION_SCOPE_NARROWING:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Scope narrowing - capability
        if change_type == AuthorityChangeType.CAPABILITY_SCOPE_NARROWING:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Policy authority change
        if change_type == AuthorityChangeType.POLICY_AUTHORITY_CHANGE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Governance disposition change
        if change_type == AuthorityChangeType.GOVERNANCE_DISPOSITION_CHANGE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Identity binding change
        if change_type == AuthorityChangeType.IDENTITY_BINDING_CHANGE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Execution gate change
        if change_type == AuthorityChangeType.EXECUTION_GATE_CHANGE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Runtime topology change
        if change_type == AuthorityChangeType.RUNTIME_TOPOLOGY_CHANGE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Undeclared authority appearance (new authority appears, doesn't affect historical)
        if change_type == AuthorityChangeType.UNDECLARED_AUTHORITY_APPEARANCE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Delegation recreated (new authority exists at T2)
        if change_type == AuthorityChangeType.DELEGATION_RECREATION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_VALID

        # Policy recreated
        if change_type == AuthorityChangeType.POLICY_RECREATION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_VALID

        # Capability recreated
        if change_type == AuthorityChangeType.CAPABILITY_RECREATION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_VALID

        # Scope widening - doesn't affect historical validity
        if change_type == AuthorityChangeType.DELEGATION_SCOPE_WIDENING:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Policy supersession
        if change_type == AuthorityChangeType.POLICY_SUPERSESSION:
            if historical_validity:
                return TemporalValidityStatus.SUPERSEDED
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Policy deletion
        if change_type == AuthorityChangeType.POLICY_DELETION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Trust anchor rotation
        if change_type == AuthorityChangeType.TRUST_ANCHOR_ROTATION:
            # Rotation preserves historical validity
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Trust anchor revocation
        if change_type == AuthorityChangeType.TRUST_ANCHOR_REVOCATION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Trust anchor replacement
        if change_type == AuthorityChangeType.TRUST_ANCHOR_REPLACEMENT:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Emergency authority activation (new authority, doesn't affect historical)
        if change_type == AuthorityChangeType.EMERGENCY_AUTHORITY_ACTIVATION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Emergency authority revocation
        if change_type == AuthorityChangeType.EMERGENCY_AUTHORITY_REVOCATION:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Recovery authority supersession
        if change_type == AuthorityChangeType.RECOVERY_AUTHORITY_SUPERSESSION:
            if historical_validity:
                return TemporalValidityStatus.SUPERSEDED
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Graph incompleteness
        if change_type == AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_UNKNOWN

        # Graph becoming complete
        if change_type == AuthorityChangeType.GRAPH_BECOMING_COMPLETE:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_UNKNOWN

        # Identifier reuse - must not collapse temporal identity
        if identifier_reuse:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
            return TemporalValidityStatus.CURRENTLY_UNKNOWN

        # Replay attack
        if is_replay:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Future revocation
        if is_future_revocation:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Worker change
        if is_worker_change:
            if historical_validity:
                return TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
            return TemporalValidityStatus.CURRENTLY_INVALID

        # Default: unknown
        return TemporalValidityStatus.UNKNOWN

    def _determine_revalidation_requirement(
        self,
        has_transition: bool,
        current_validity: TemporalValidityStatus,
        change_type: AuthorityChangeType | None,
    ) -> bool:
        """Determine if revalidation is required."""
        if not has_transition:
            return False

        # Revalidation required for changes that affect current validity
        if current_validity in (
            TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            TemporalValidityStatus.VALID_AT_EXECUTION_EXPIRED_NOW,
            TemporalValidityStatus.CURRENTLY_INVALID,
            TemporalValidityStatus.CURRENTLY_UNKNOWN,
            TemporalValidityStatus.REVALIDATION_REQUIRED,
            TemporalValidityStatus.SUPERSEDED,
        ):
            return True

        return False

    def _generate_interpretation(
        self,
        historical_validity: bool,
        current_validity: TemporalValidityStatus,
        has_transition: bool,
        change_type: AuthorityChangeType | None,
    ) -> str:
        """Generate human-readable interpretation."""
        if not has_transition:
            if historical_validity:
                return "No authority change. Historical reconciliation remains valid."
            return "No authority change. Historical reconciliation was not valid."

        if change_type:
            return f"Authority change: {change_type.value}. Historical validity: {historical_validity}. Current validity: {current_validity.value}."

        return f"Authority change occurred. Historical validity: {historical_validity}. Current validity: {current_validity.value}."

    def _generate_notes(
        self,
        historical_validity: bool,
        current_validity: TemporalValidityStatus,
        has_transition: bool,
        change_type: AuthorityChangeType | None,
    ) -> str:
        """Generate notes for the temporal reconciliation."""
        parts = []
        parts.append(f"Historical validity: {historical_validity}")
        parts.append(f"Current validity: {current_validity.value}")
        if has_transition:
            parts.append(f"Transition: {change_type.value if change_type else 'unknown'}")
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Adversarial world generator
# ---------------------------------------------------------------------------


class AdversarialWorldGenerator:
    """Generates adversarial worlds for Phase 33 experiments."""

    def generate_all_worlds(self) -> list[TemporalClosureWorld]:
        """Generate all adversarial worlds."""
        worlds = [
            self._world_01_no_authority_change(),
            self._world_02_delegation_revoked(),
            self._world_03_delegation_expired(),
            self._world_04_delegation_scope_narrowed(),
            self._world_05_delegation_scope_widened(),
            self._world_06_capability_revoked(),
            self._world_07_capability_expired(),
            self._world_08_capability_scope_narrowed(),
            self._world_09_policy_superseded(),
            self._world_10_policy_deleted(),
            self._world_11_policy_authority_changed(),
            self._world_12_governance_disposition_changed(),
            self._world_13_trust_anchor_rotated(),
            self._world_14_trust_anchor_revoked(),
            self._world_15_authority_origin_changed(),
            self._world_16_identity_binding_changed(),
            self._world_17_execution_gate_changed(),
            self._world_18_runtime_topology_changed(),
            self._world_19_cross_domain_delegation_revoked(),
            self._world_20_emergency_authority_activated(),
            self._world_21_emergency_authority_revoked(),
            self._world_22_recovery_authority_superseded(),
            self._world_23_worker_delegation_revoked(),
            self._world_24_worker_delegation_changed(),
            self._world_25_authority_path_changes_before_reconciliation(),
            self._world_26_authority_path_changes_after_reconciliation(),
            self._world_27_graph_becomes_incomplete(),
            self._world_28_graph_becomes_complete(),
            self._world_29_undeclared_authority_appears(),
            self._world_30_historical_authority_valid_current_unknown(),
            self._world_31_historical_evidence_available_current_incomplete(),
            self._world_32_historical_evidence_missing(),
            self._world_33_current_authority_changed_evidence_immutable(),
            self._world_34_multiple_paths_one_revoked(),
            self._world_35_multiple_effects_different_versions(),
            self._world_36_trust_anchor_rotation_with_continuity(),
            self._world_37_trust_anchor_replacement_without_continuity(),
            self._world_38_delegation_revoked_recreated(),
            self._world_39_capability_revoked_recreated_same_id(),
            self._world_40_policy_deleted_recreated_same_id(),
            self._world_41_valid_t1_invalid_t2_valid_t3_new_derivation(),
            self._world_42_replay_after_revocation(),
            self._world_43_historical_receipt_reused_as_current(),
            self._world_44_current_cannot_authorize_past(),
            self._world_45_authority_change_no_impact(),
        ]
        return worlds

    def _make_state(
        self,
        state_id: str,
        version: str,
        timestamp: str,
        trust_anchor_id: str = "ta-001",
        delegation_ids: tuple[str, ...] = ("del-001",),
        policy_ids: tuple[str, ...] = ("pol-001",),
        capability_ids: tuple[str, ...] = ("cap-001",),
        governance_disposition: str = "authorized",
        execution_gate_policy: str = "gate-001",
        scope: str = "runtime",
        domain: str = "default",
        is_complete: bool = True,
    ) -> AuthorityState:
        return AuthorityState(
            state_id=state_id,
            version=version,
            timestamp=timestamp,
            trust_anchor_id=trust_anchor_id,
            delegation_ids=delegation_ids,
            policy_ids=policy_ids,
            capability_ids=capability_ids,
            governance_disposition=governance_disposition,
            execution_gate_policy=execution_gate_policy,
            scope=scope,
            domain=domain,
            is_complete=is_complete,
        )

    def _make_transition(
        self,
        change_type: AuthorityChangeType,
        timestamp: str,
        actor: str,
        source: str,
        prior_state_ref: str,
        new_state_ref: str,
        affected_authority_ids: tuple[str, ...] = (),
    ) -> AuthorityStateTransition:
        return AuthorityStateTransition(
            transition_id=f"trans-{uuid.uuid4().hex[:8]}",
            change_type=change_type,
            timestamp=timestamp,
            actor=actor,
            source=source,
            prior_state_ref=prior_state_ref,
            new_state_ref=new_state_ref,
            affected_authority_ids=affected_authority_ids,
        )

    # -----------------------------------------------------------------------
    # World generators
    # -----------------------------------------------------------------------

    def _world_01_no_authority_change(self) -> TemporalClosureWorld:
        """World 01: No authority change after valid reconciliation."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        return TemporalClosureWorld(
            world_id="world_01_no_authority_change",
            description="No authority change after valid reconciliation",
            authority_state_t1=state_t1,
            authority_state_t2=None,
            transition=None,
            has_transition=False,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
        )

    def _world_02_delegation_revoked(self) -> TemporalClosureWorld:
        """World 02: Delegation revoked after valid execution."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_02_delegation_revoked",
            description="Delegation revoked after valid execution",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )

    def _world_03_delegation_expired(self) -> TemporalClosureWorld:
        """World 03: Delegation expired after valid execution."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-03-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_EXPIRATION,
            "2026-03-01T00:00:00Z", "system", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_03_delegation_expired",
            description="Delegation expired after valid execution",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_EXPIRED_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_EXPIRATION,
        )

    def _world_04_delegation_scope_narrowed(self) -> TemporalClosureWorld:
        """World 04: Delegation scope narrowed after valid execution."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), scope="runtime")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",), scope="staging")
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_SCOPE_NARROWING,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_04_delegation_scope_narrowed",
            description="Delegation scope narrowed after valid execution",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_SCOPE_NARROWING,
            is_scope_narrowing=True,
        )

    def _world_05_delegation_scope_widened(self) -> TemporalClosureWorld:
        """World 05: Delegation scope widened after valid execution."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), scope="staging")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",), scope="runtime")
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_SCOPE_WIDENING,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_05_delegation_scope_widened",
            description="Delegation scope widened after valid execution",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_SCOPE_WIDENING,
            is_scope_widening=True,
        )

    def _world_06_capability_revoked(self) -> TemporalClosureWorld:
        """World 06: Capability revoked after valid execution."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", capability_ids=())
        transition = self._make_transition(
            AuthorityChangeType.CAPABILITY_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("cap-001",)
        )
        return TemporalClosureWorld(
            world_id="world_06_capability_revoked",
            description="Capability revoked after valid execution",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.CAPABILITY_REVOCATION,
        )

    def _world_07_capability_expired(self) -> TemporalClosureWorld:
        """World 07: Capability expired after valid execution."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-03-01T00:00:00Z", capability_ids=())
        transition = self._make_transition(
            AuthorityChangeType.CAPABILITY_EXPIRATION,
            "2026-03-01T00:00:00Z", "system", "test", "state-t1", "state-t2",
            ("cap-001",)
        )
        return TemporalClosureWorld(
            world_id="world_07_capability_expired",
            description="Capability expired after valid execution",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_EXPIRED_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.CAPABILITY_EXPIRATION,
        )

    def _world_08_capability_scope_narrowed(self) -> TemporalClosureWorld:
        """World 08: Capability scope narrowed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",), scope="runtime")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", capability_ids=("cap-001",), scope="staging")
        transition = self._make_transition(
            AuthorityChangeType.CAPABILITY_SCOPE_NARROWING,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("cap-001",)
        )
        return TemporalClosureWorld(
            world_id="world_08_capability_scope_narrowed",
            description="Capability scope narrowed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.CAPABILITY_SCOPE_NARROWING,
            is_scope_narrowing=True,
        )

    def _world_09_policy_superseded(self) -> TemporalClosureWorld:
        """World 09: Policy superseded."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", policy_ids=("pol-002",))
        transition = self._make_transition(
            AuthorityChangeType.POLICY_SUPERSESSION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("pol-001", "pol-002")
        )
        return TemporalClosureWorld(
            world_id="world_09_policy_superseded",
            description="Policy superseded",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.SUPERSEDED,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.POLICY_SUPERSESSION,
            is_policy_supersession=True,
        )

    def _world_10_policy_deleted(self) -> TemporalClosureWorld:
        """World 10: Policy deleted."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", policy_ids=())
        transition = self._make_transition(
            AuthorityChangeType.POLICY_DELETION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("pol-001",)
        )
        return TemporalClosureWorld(
            world_id="world_10_policy_deleted",
            description="Policy deleted",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.POLICY_DELETION,
            is_policy_deletion=True,
        )

    def _world_11_policy_authority_changed(self) -> TemporalClosureWorld:
        """World 11: Policy authority changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", policy_ids=("pol-001",))
        transition = self._make_transition(
            AuthorityChangeType.POLICY_AUTHORITY_CHANGE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("pol-001",)
        )
        return TemporalClosureWorld(
            world_id="world_11_policy_authority_changed",
            description="Policy authority changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.POLICY_AUTHORITY_CHANGE,
        )

    def _world_12_governance_disposition_changed(self) -> TemporalClosureWorld:
        """World 12: Governance disposition changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", governance_disposition="authorized")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", governance_disposition="revoked")
        transition = self._make_transition(
            AuthorityChangeType.GOVERNANCE_DISPOSITION_CHANGE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_12_governance_disposition_changed",
            description="Governance disposition changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.GOVERNANCE_DISPOSITION_CHANGE,
        )

    def _world_13_trust_anchor_rotated(self) -> TemporalClosureWorld:
        """World 13: Trust anchor rotated."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", trust_anchor_id="ta-001")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", trust_anchor_id="ta-002")
        transition = self._make_transition(
            AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("ta-001", "ta-002")
        )
        return TemporalClosureWorld(
            world_id="world_13_trust_anchor_rotated",
            description="Trust anchor rotated",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            is_trust_anchor_rotation=True,
        )

    def _world_14_trust_anchor_revoked(self) -> TemporalClosureWorld:
        """World 14: Trust anchor revoked."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", trust_anchor_id="ta-001")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", trust_anchor_id="")
        transition = self._make_transition(
            AuthorityChangeType.TRUST_ANCHOR_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("ta-001",)
        )
        return TemporalClosureWorld(
            world_id="world_14_trust_anchor_revoked",
            description="Trust anchor revoked",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.TRUST_ANCHOR_REVOCATION,
        )

    def _world_15_authority_origin_changed(self) -> TemporalClosureWorld:
        """World 15: Authority origin changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = self._make_transition(
            AuthorityChangeType.TRUST_ANCHOR_REPLACEMENT,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("ta-001",)
        )
        return TemporalClosureWorld(
            world_id="world_15_authority_origin_changed",
            description="Authority origin changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.TRUST_ANCHOR_REPLACEMENT,
        )

    def _world_16_identity_binding_changed(self) -> TemporalClosureWorld:
        """World 16: Identity binding changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = self._make_transition(
            AuthorityChangeType.IDENTITY_BINDING_CHANGE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_16_identity_binding_changed",
            description="Identity binding changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.IDENTITY_BINDING_CHANGE,
        )

    def _world_17_execution_gate_changed(self) -> TemporalClosureWorld:
        """World 17: Execution gate policy changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", execution_gate_policy="gate-001")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", execution_gate_policy="gate-002")
        transition = self._make_transition(
            AuthorityChangeType.EXECUTION_GATE_CHANGE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("gate-001", "gate-002")
        )
        return TemporalClosureWorld(
            world_id="world_17_execution_gate_changed",
            description="Execution gate policy changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.EXECUTION_GATE_CHANGE,
        )

    def _world_18_runtime_topology_changed(self) -> TemporalClosureWorld:
        """World 18: Runtime topology changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = self._make_transition(
            AuthorityChangeType.RUNTIME_TOPOLOGY_CHANGE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_18_runtime_topology_changed",
            description="Runtime topology changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.RUNTIME_TOPOLOGY_CHANGE,
        )

    def _world_19_cross_domain_delegation_revoked(self) -> TemporalClosureWorld:
        """World 19: Cross-domain delegation revoked."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), domain="domain-b")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=(), domain="domain-b")
        transition = self._make_transition(
            AuthorityChangeType.CROSS_DOMAIN_DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_19_cross_domain_delegation_revoked",
            description="Cross-domain delegation revoked",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.CROSS_DOMAIN_DELEGATION_REVOCATION,
            is_cross_domain=True,
        )

    def _world_20_emergency_authority_activated(self) -> TemporalClosureWorld:
        """World 20: Emergency authority activated."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = self._make_transition(
            AuthorityChangeType.EMERGENCY_AUTHORITY_ACTIVATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("emg-001",)
        )
        return TemporalClosureWorld(
            world_id="world_20_emergency_authority_activated",
            description="Emergency authority activated",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.EMERGENCY_AUTHORITY_ACTIVATION,
            is_emergency=True,
        )

    def _world_21_emergency_authority_revoked(self) -> TemporalClosureWorld:
        """World 21: Emergency authority revoked."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("emg-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.EMERGENCY_AUTHORITY_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("emg-001",)
        )
        return TemporalClosureWorld(
            world_id="world_21_emergency_authority_revoked",
            description="Emergency authority revoked",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.EMERGENCY_AUTHORITY_REVOCATION,
            is_emergency=True,
        )

    def _world_22_recovery_authority_superseded(self) -> TemporalClosureWorld:
        """World 22: Recovery authority superseded."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("rec-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("norm-001",))
        transition = self._make_transition(
            AuthorityChangeType.RECOVERY_AUTHORITY_SUPERSESSION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("rec-001", "norm-001")
        )
        return TemporalClosureWorld(
            world_id="world_22_recovery_authority_superseded",
            description="Recovery authority superseded",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.SUPERSEDED,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.RECOVERY_AUTHORITY_SUPERSESSION,
            is_recovery=True,
        )

    def _world_23_worker_delegation_revoked(self) -> TemporalClosureWorld:
        """World 23: Worker delegation revoked."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("wrk-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.WORKER_DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("wrk-001",)
        )
        return TemporalClosureWorld(
            world_id="world_23_worker_delegation_revoked",
            description="Worker delegation revoked",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.WORKER_DELEGATION_REVOCATION,
            is_worker_change=True,
        )

    def _world_24_worker_delegation_changed(self) -> TemporalClosureWorld:
        """World 24: Worker delegation changed."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("wrk-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("wrk-002",))
        transition = self._make_transition(
            AuthorityChangeType.WORKER_DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("wrk-001", "wrk-002")
        )
        return TemporalClosureWorld(
            world_id="world_24_worker_delegation_changed",
            description="Worker delegation changed",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.WORKER_DELEGATION_REVOCATION,
            is_worker_change=True,
        )

    def _world_25_authority_path_changes_before_reconciliation(self) -> TemporalClosureWorld:
        """World 25: Authority path changes after effect but before reconciliation."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-01-15T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-01-15T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_25_authority_path_changes_before_reconciliation",
            description="Authority path changes after effect but before reconciliation",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )

    def _world_26_authority_path_changes_after_reconciliation(self) -> TemporalClosureWorld:
        """World 26: Authority path changes after reconciliation."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_26_authority_path_changes_after_reconciliation",
            description="Authority path changes after reconciliation",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )

    def _world_27_graph_becomes_incomplete(self) -> TemporalClosureWorld:
        """World 27: Graph becomes incomplete after reconciliation."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", is_complete=True)
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", is_complete=False)
        transition = self._make_transition(
            AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_27_graph_becomes_incomplete",
            description="Graph becomes incomplete after reconciliation",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE,
            is_graph_incomplete=True,
        )

    def _world_28_graph_becomes_complete(self) -> TemporalClosureWorld:
        """World 28: Graph becomes complete."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", is_complete=False)
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", is_complete=True)
        transition = self._make_transition(
            AuthorityChangeType.GRAPH_BECOMING_COMPLETE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_28_graph_becomes_complete",
            description="Graph becomes complete",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.GRAPH_BECOMING_COMPLETE,
            is_graph_complete=True,
        )

    def _world_29_undeclared_authority_appears(self) -> TemporalClosureWorld:
        """World 29: New undeclared authority transition appears."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", is_complete=True)
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", is_complete=False)
        transition = self._make_transition(
            AuthorityChangeType.UNDECLARED_AUTHORITY_APPEARANCE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("new-auth-001",)
        )
        return TemporalClosureWorld(
            world_id="world_29_undeclared_authority_appears",
            description="New undeclared authority transition appears",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.UNDECLARED_AUTHORITY_APPEARANCE,
        )

    def _world_30_historical_authority_valid_current_unknown(self) -> TemporalClosureWorld:
        """World 30: Historical authority valid while current authority is unknown."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", is_complete=False)
        transition = self._make_transition(
            AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_30_historical_authority_valid_current_unknown",
            description="Historical authority valid while current authority is unknown",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE,
        )

    def _world_31_historical_evidence_available_current_incomplete(self) -> TemporalClosureWorld:
        """World 31: Historical evidence available but current graph incomplete."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", is_complete=False)
        transition = self._make_transition(
            AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_31_historical_evidence_available_current_incomplete",
            description="Historical evidence available but current graph incomplete",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.GRAPH_BECOMING_INCOMPLETE,
        )

    def _world_32_historical_evidence_missing(self) -> TemporalClosureWorld:
        """World 32: Historical evidence itself is missing."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = self._make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ()
        )
        return TemporalClosureWorld(
            world_id="world_32_historical_evidence_missing",
            description="Historical evidence itself is missing",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=False,
            expected_current_validity=TemporalValidityStatus.CURRENTLY_INVALID,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.NO_CHANGE,
        )

    def _world_33_current_authority_changed_evidence_immutable(self) -> TemporalClosureWorld:
        """World 33: Current authority changed but runtime evidence remains immutable."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_33_current_authority_changed_evidence_immutable",
            description="Current authority changed but runtime evidence remains immutable",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )

    def _world_34_multiple_paths_one_revoked(self) -> TemporalClosureWorld:
        """World 34: Multiple authority paths where one is revoked."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001", "del-002"))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-002",))
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_34_multiple_paths_one_revoked",
            description="Multiple authority paths where one is revoked",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )

    def _world_35_multiple_effects_different_versions(self) -> TemporalClosureWorld:
        """World 35: Multiple historical effects under different authority versions."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_35_multiple_effects_different_versions",
            description="Multiple historical effects under different authority versions",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )

    def _world_36_trust_anchor_rotation_with_continuity(self) -> TemporalClosureWorld:
        """World 36: Trust anchor rotation with explicit continuity."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", trust_anchor_id="ta-001")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", trust_anchor_id="ta-002")
        transition = self._make_transition(
            AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("ta-001", "ta-002")
        )
        return TemporalClosureWorld(
            world_id="world_36_trust_anchor_rotation_with_continuity",
            description="Trust anchor rotation with explicit continuity",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            is_trust_anchor_rotation=True,
        )

    def _world_37_trust_anchor_replacement_without_continuity(self) -> TemporalClosureWorld:
        """World 37: Trust anchor replacement without continuity."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", trust_anchor_id="ta-001")
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", trust_anchor_id="ta-002")
        transition = self._make_transition(
            AuthorityChangeType.TRUST_ANCHOR_REPLACEMENT,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("ta-001", "ta-002")
        )
        return TemporalClosureWorld(
            world_id="world_37_trust_anchor_replacement_without_continuity",
            description="Trust anchor replacement without continuity",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.TRUST_ANCHOR_REPLACEMENT,
        )

    def _world_38_delegation_revoked_recreated(self) -> TemporalClosureWorld:
        """World 38: Delegation revoked and later recreated."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-03-01T00:00:00Z", delegation_ids=("del-001",))
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-03-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_38_delegation_revoked_recreated",
            description="Delegation revoked and later recreated",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_RECREATION,
            is_identifier_reuse=True,
            identifier_reuse=True,
        )

    def _world_39_capability_revoked_recreated_same_id(self) -> TemporalClosureWorld:
        """World 39: Capability revoked and recreated with same ID."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-03-01T00:00:00Z", capability_ids=("cap-001",))
        transition = self._make_transition(
            AuthorityChangeType.CAPABILITY_RECREATION,
            "2026-03-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("cap-001",)
        )
        return TemporalClosureWorld(
            world_id="world_39_capability_revoked_recreated_same_id",
            description="Capability revoked and recreated with same ID",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.CAPABILITY_RECREATION,
            is_identifier_reuse=True,
            identifier_reuse=True,
        )

    def _world_40_policy_deleted_recreated_same_id(self) -> TemporalClosureWorld:
        """World 40: Policy deleted and recreated with same ID."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-03-01T00:00:00Z", policy_ids=("pol-001",))
        transition = self._make_transition(
            AuthorityChangeType.POLICY_RECREATION,
            "2026-03-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("pol-001",)
        )
        return TemporalClosureWorld(
            world_id="world_40_policy_deleted_recreated_same_id",
            description="Policy deleted and recreated with same ID",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.POLICY_RECREATION,
            is_identifier_reuse=True,
            identifier_reuse=True,
        )

    def _world_41_valid_t1_invalid_t2_valid_t3_new_derivation(self) -> TemporalClosureWorld:
        """World 41: Authority path valid at T1, invalid at T2, valid again at T3 through new derivation."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-03-01T00:00:00Z", delegation_ids=("del-002",))
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-03-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001", "del-002")
        )
        return TemporalClosureWorld(
            world_id="world_41_valid_t1_invalid_t2_valid_t3",
            description="Authority path valid at T1, invalid at T2, valid again at T3 through new derivation",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_RECREATION,
        )

    def _world_42_replay_after_revocation(self) -> TemporalClosureWorld:
        """World 42: Replay of historical authorization after revocation."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_42_replay_after_revocation",
            description="Replay of historical authorization after revocation",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            is_replay=True,
        )

    def _world_43_historical_receipt_reused_as_current(self) -> TemporalClosureWorld:
        """World 43: Historical execution receipt reused as evidence for new effect."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_43_historical_receipt_reused",
            description="Historical execution receipt reused as evidence for new effect",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            is_replay=True,
        )

    def _world_44_current_cannot_authorize_past(self) -> TemporalClosureWorld:
        """World 44: Current authorization cannot retroactively authorize historical effect."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=())
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",))
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-001",)
        )
        return TemporalClosureWorld(
            world_id="world_44_current_cannot_authorize_past",
            description="Current authorization cannot retroactively authorize historical effect",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=False,
            expected_current_validity=TemporalValidityStatus.CURRENTLY_VALID,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_RECREATION,
            is_future_authority=True,
        )

    def _world_45_authority_change_no_impact(self) -> TemporalClosureWorld:
        """World 45: Authority change with no impact on the particular historical path."""
        state_t1 = self._make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001", "del-002"))
        state_t2 = self._make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001", "del-003"))
        transition = self._make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z", "admin", "test", "state-t1", "state-t2",
            ("del-002", "del-003")
        )
        return TemporalClosureWorld(
            world_id="world_45_authority_change_no_impact",
            description="Authority change with no impact on the particular historical path",
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )


# ---------------------------------------------------------------------------
# Phase 33 experiment
# ---------------------------------------------------------------------------


class Phase33Experiment:
    """Runs the complete Phase 33 experiment."""

    def __init__(self) -> None:
        self.engine = TemporalClosureEngine("phase33-engine")
        self.worlds = AdversarialWorldGenerator().generate_all_worlds()
        self.results: list[dict[str, Any]] = []

    def run_all(self) -> dict[str, Any]:
        """Run all worlds and return summary."""
        for world in self.worlds:
            temporal_rec = self.engine.evaluate_temporal_closure(
                authority_state_t1=world.authority_state_t1,
                authority_state_t2=world.authority_state_t2,
                transition=world.transition,
                has_transition=world.has_transition,
                historical_validity=world.historical_validity,
                expected_current_validity=world.expected_current_validity,
                expected_revalidation_required=world.expected_revalidation_required,
                change_type=world.change_type,
                scope=world.scope,
                domain=world.domain,
                identifier_reuse=world.identifier_reuse,
                is_replay=world.is_replay,
                is_future_authority=world.is_future_authority,
                is_future_revocation=world.is_future_revocation,
                is_scope_narrowing=world.is_scope_narrowing,
                is_scope_widening=world.is_scope_widening,
                is_policy_supersession=world.is_policy_supersession,
                is_policy_deletion=world.is_policy_deletion,
                is_trust_anchor_rotation=world.is_trust_anchor_rotation,
                is_graph_incomplete=world.is_graph_incomplete,
                is_graph_complete=world.is_graph_complete,
                is_worker_change=world.is_worker_change,
                is_emergency=world.is_emergency,
                is_recovery=world.is_recovery,
                is_cross_domain=world.is_cross_domain,
            )
            self.results.append({
                "world_id": world.world_id,
                "historical_validity": temporal_rec.historical_validity,
                "current_validity": temporal_rec.current_validity.value,
                "revalidation_required": temporal_rec.revalidation_required,
                "expected_current_validity": world.expected_current_validity.value,
                "expected_revalidation_required": world.expected_revalidation_required,
                "validity_match": temporal_rec.current_validity == world.expected_current_validity,
            })
        return self.summary()

    def summary(self) -> dict[str, Any]:
        """Generate experiment summary."""
        total = len(self.results)
        validity_matches = sum(1 for r in self.results if r["validity_match"])
        historical_valid = sum(1 for r in self.results if r["historical_validity"])
        revalidation_required = sum(1 for r in self.results if r["revalidation_required"])

        return {
            "total_worlds": total,
            "total_temporal_reconciliations": len(self.engine.temporal_reconciliations),
            "validity_matches": validity_matches,
            "historical_valid_count": historical_valid,
            "revalidation_required_count": revalidation_required,
            "validity_accuracy": validity_matches / total if total > 0 else 0,
        }
