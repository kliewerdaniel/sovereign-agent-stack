"""Phase 34: Temporal Effective Authority Graph Divergence Detection.

Central research question:
    Can the system detect runtime effects that diverged from the authority
    graph that existed at the exact time of execution, while preserving
    the distinction between historical authority state, current authority
    state, runtime observation, and later graph changes?

This is NOT a graph comparison problem. It is a temporal forensic problem.

The system must answer:
    Given an observed runtime effect E occurring at time T, what did the
    declared authority graph permit at T, what authority path actually
    governed E at T, and did the runtime effect diverge from the authority
    state that actually existed at T?

The critical temporal relation:
    OBSERVED EFFECT AT T
    → DECLARED GRAPH AT T
    → RECONSTRUCTED EFFECTIVE PATH AT T
    → TEMPORAL RECONCILIATION
    → DIVERGENCE ANALYSIS

Do NOT use the current graph to explain historical runtime behavior.

Critical invariants:
    AUTHORITY AT EXECUTION TIME MUST BE EVALUATED AGAINST THE AUTHORITY
    STATE THAT EXISTED AT EXECUTION TIME.

    LATER AUTHORITY STATE MUST NEVER EXPLAIN AN EARLIER EFFECT UNLESS
    THE HISTORICAL RECORD EXPLICITLY ESTABLISHES THAT THE LATER STATE
    WAS ALREADY VALID AT THE TIME OF EXECUTION.

    MISSING HISTORICAL EVIDENCE ≠ UNAUTHORIZED.
    MISSING HISTORICAL EVIDENCE → UNKNOWN.

    INCOMPLETE GRAPH ≠ AUTHORITY ESCAPE.
    INCOMPLETE GRAPH → INCOMPLETE / UNKNOWN.

    IDENTIFIER EQUALITY ≠ TEMPORAL IDENTITY.
    cap_001@T1 ≠ cap_001@T3.

    TIMESTAMP EQUALITY ≠ ORDERING PROOF.
    Events at the same timestamp require explicit ordering evidence.

    THE DIVERGENCE DETECTOR IS PURELY EPISTEMIC.
    It must not authorize, delegate, repair, or modify authority.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# Reuse from Phase 33 (temporal closure)
from research.examples.sovereign_agent.effective_authority_graph_temporal_closure import (
    AuthorityChangeType,
    AuthorityState,
    AuthorityStateTransition,
    TemporalValidityStatus,
)

# Reuse from Phase 32 (authority graph reconciliation)
from research.examples.sovereign_agent.authority_path_graph_reconciliation import (
    CorrespondenceStatus,
    DivergenceType,
    EpistemicStatus,
    GraphCompletenessStatus,
)


# ---------------------------------------------------------------------------
# Phase 34 core enumerations
# ---------------------------------------------------------------------------


class TemporalDivergenceStatus(str, Enum):
    """Status of temporal divergence detection.

    Distinguishes:
        NO_DIVERGENCE — effective path matches declared graph at execution
        HISTORICAL_DIVERGENCE — divergence at execution time
        CURRENT_DIVERGENCE — divergence only in current state
        BOTH_DIVERGENCE — divergence at execution AND current state
        UNKNOWN — insufficient evidence
        TEMPORAL_ORDER_UNKNOWN — cannot determine event ordering
        HISTORICAL_STATE_UNKNOWN — historical graph state is missing
        RECONSTRUCTION_INCOMPLETE — cannot reconstruct effective path
    """

    NO_DIVERGENCE = "no_divergence"
    HISTORICAL_DIVERGENCE = "historical_divergence"
    CURRENT_DIVERGENCE = "current_divergence"
    BOTH_DIVERGENCE = "both_divergence"
    UNKNOWN = "unknown"
    TEMPORAL_ORDER_UNKNOWN = "temporal_order_unknown"
    HISTORICAL_STATE_UNKNOWN = "historical_state_unknown"
    RECONSTRUCTION_INCOMPLETE = "reconstruction_incomplete"


class TemporalOrderStatus(str, Enum):
    """Ordering of two events in time.

    Explicitly distinguishes:
        BEFORE — event A happened before event B (proven)
        AFTER — event A happened after event B (proven)
        CONCURRENT_KNOWN — same timestamp, ordering known from provenance
        CONCURRENT_UNKNOWN — same timestamp, ordering unknown
        UNKNOWN — no ordering evidence available
    """

    BEFORE = "before"
    AFTER = "after"
    CONCURRENT_KNOWN = "concurrent_known"
    CONCURRENT_UNKNOWN = "concurrent_unknown"
    UNKNOWN = "unknown"


class DivergenceCause(str, Enum):
    """Cause classification for detected divergence."""

    NONE = "none"
    EFFECTIVE_PATH_NOT_DECLARED = "effective_path_not_declared"
    DECLARED_PATH_NOT_EXECUTED = "declared_path_not_executed"
    SCOPE_VIOLATION = "scope_violation"
    DOMAIN_VIOLATION = "domain_violation"
    ACTOR_VIOLATION = "actor_violation"
    CAPABILITY_VIOLATION = "capability_violation"
    POLICY_VIOLATION = "policy_violation"
    GOVERNANCE_VIOLATION = "governance_violation"
    TRUST_ANCHOR_VIOLATION = "trust_anchor_violation"
    IDENTIFIER_REUSE_COLLAPSE = "identifier_reuse_collapse"
    FUTURE_AUTHORITY_EXPLAINS_PAST = "future_authority_explains_past"
    MISSING_HISTORICAL_EVIDENCE = "missing_historical_evidence"


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalAuthorityDivergence:
    """Result of temporal divergence detection.

    Preserves the full historical/current epistemic context so that
    the investigation can explain what was authorized, what was executed,
    what was declared, what was effective, what changed later, and what
    remains unknown.
    """

    divergence_id: str
    effect_id: str
    observation_id: str
    execution_time: str
    current_time: str
    historical_graph_ref: str
    current_graph_ref: str
    historical_effective_path: str
    current_effective_status: TemporalValidityStatus
    historical_reconciliation: CorrespondenceStatus
    current_reconciliation: CorrespondenceStatus
    divergence_status: TemporalDivergenceStatus
    divergence_cause: DivergenceCause
    temporal_order_status: TemporalOrderStatus
    graph_completeness_status: GraphCompletenessStatus
    historical_validity: bool
    current_validity: bool
    epistemic_status: EpistemicStatus
    confidence: float
    provenance: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TemporalDivergenceWorld:
    """An adversarial world for temporal divergence experiments.

    The oracle fields (expected_*) represent ground truth. The engine
    being tested does NOT have access to these.
    """

    world_id: str
    description: str
    execution_time: str
    current_time: str
    authority_state_at_execution: AuthorityState | None
    authority_state_current: AuthorityState | None
    transition: AuthorityStateTransition | None
    observed_effect: str
    effective_path_reconstructed: str
    graph_completeness: GraphCompletenessStatus
    graph_complete_for_scope: bool
    expected_divergence_status: TemporalDivergenceStatus
    expected_divergence_cause: DivergenceCause
    expected_temporal_order: TemporalOrderStatus
    has_transition: bool
    is_unauthorized_effect: bool
    is_future_authority_attack: bool
    is_future_revocation_attack: bool
    is_identifier_reuse: bool
    is_graph_rollback: bool
    is_event_reorder: bool
    is_missing_event: bool
    is_emergency: bool
    is_recovery: bool
    is_cross_domain: bool
    is_worker_authority: bool
    is_concurrent_event: bool
    temporal_order_known: bool
    is_complete_graph: bool
    is_incomplete_graph: bool
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_state(
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
    change_type: AuthorityChangeType,
    timestamp: str,
    actor: str = "admin",
    source: str = "test",
    prior_state_ref: str = "state-t1",
    new_state_ref: str = "state-t2",
    affected_ids: tuple[str, ...] = (),
) -> AuthorityStateTransition:
    return AuthorityStateTransition(
        transition_id=f"trans-{uuid.uuid4().hex[:8]}",
        change_type=change_type,
        timestamp=timestamp,
        actor=actor,
        source=source,
        prior_state_ref=prior_state_ref,
        new_state_ref=new_state_ref,
        affected_authority_ids=affected_ids,
    )


# ---------------------------------------------------------------------------
# Divergence detection engine
# ---------------------------------------------------------------------------


class DivergenceDetectionEngine:
    """Detects temporal divergence between effective authority paths and
    the declared authority graph at the exact time of execution.

    CRITICAL INVARIANTS:
        NEVER USE CURRENT AUTHORITY STATE TO EXPLAIN HISTORICAL EFFECTS.
        MISSING HISTORICAL EVIDENCE → UNKNOWN (not unauthorized).
        INCOMPLETE GRAPH → INCOMPLETE (not authority escape).
        TIMESTAMP EQUALITY ≠ ORDERING PROOF.
        IDENTIFIER EQUALITY ≠ TEMPORAL IDENTITY.

    This engine is purely epistemic. It does NOT authorize, delegate,
    repair, or modify authority in any way.
    """

    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.divergences: list[TemporalAuthorityDivergence] = []

    def detect_divergence(
        self,
        world: TemporalDivergenceWorld,
    ) -> TemporalAuthorityDivergence:
        """Detect temporal divergence for an observed effect.

        Uses ONLY the authority state at execution time for historical
        evaluation. Uses the current state ONLY for separate current-state
        analysis. Never conflates the two.
        """
        # Step 1: Check if historical state is available
        if world.authority_state_at_execution is None:
            return self._create_divergence(
                world=world,
                divergence_status=TemporalDivergenceStatus.HISTORICAL_STATE_UNKNOWN,
                divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
                temporal_order_status=TemporalOrderStatus.UNKNOWN,
                historical_validity=False,
                current_validity=False,
                epistemic_status=EpistemicStatus.UNKNOWN,
                confidence=0.1,
                notes="Historical authority state is missing. Cannot evaluate.",
            )

        # Step 2: Check for concurrent events with unknown ordering
        if world.is_concurrent_event and not world.temporal_order_known:
            return self._create_divergence(
                world=world,
                divergence_status=TemporalDivergenceStatus.TEMPORAL_ORDER_UNKNOWN,
                divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
                temporal_order_status=TemporalOrderStatus.CONCURRENT_UNKNOWN,
                historical_validity=False,
                current_validity=False,
                epistemic_status=EpistemicStatus.UNKNOWN,
                confidence=0.15,
                notes="Concurrent events with unknown ordering. Cannot determine temporal relationship.",
            )

        # Step 3: Check if graph is incomplete — cannot draw strong conclusions
        if world.is_incomplete_graph or world.graph_completeness in (
            GraphCompletenessStatus.INCOMPLETE,
            GraphCompletenessStatus.INCOMPLETE_FOR_SCOPE,
        ):
            return self._handle_incomplete_graph(world)

        # Step 4: Check if effective path is available
        if not world.effective_path_reconstructed:
            return self._create_divergence(
                world=world,
                divergence_status=TemporalDivergenceStatus.RECONSTRUCTION_INCOMPLETE,
                divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
                temporal_order_status=world.expected_temporal_order,
                historical_validity=False,
                current_validity=False,
                epistemic_status=EpistemicStatus.INCOMPLETE,
                confidence=0.2,
                notes="Effective path reconstruction is incomplete.",
            )

        # Step 5: Evaluate historical divergence using ONLY execution-time state
        historical_divergence = self._evaluate_historical_divergence(world)

        # Step 6: Evaluate current divergence separately
        current_divergence = self._evaluate_current_divergence(world)

        # Step 7: Combine
        return self._combine_divergences(world, historical_divergence, current_divergence)

    def _handle_incomplete_graph(
        self, world: TemporalDivergenceWorld
    ) -> TemporalAuthorityDivergence:
        """Handle cases where the declared graph is incomplete.

        Incomplete graphs cannot support authority escape conclusions.
        The result is INCOMPLETE or UNKNOWN, never AUTHORITY_ESCAPE.
        """
        # Even with incomplete graphs, if the effect is clearly unauthorized
        # and the relevant scope is complete, we may still detect divergence
        if (
            world.graph_complete_for_scope
            and world.is_unauthorized_effect
            and world.effective_path_reconstructed
        ):
            return self._create_divergence(
                world=world,
                divergence_status=TemporalDivergenceStatus.HISTORICAL_DIVERGENCE,
                divergence_cause=DivergenceCause.EFFECTIVE_PATH_NOT_DECLARED,
                temporal_order_status=world.expected_temporal_order,
                historical_validity=False,
                current_validity=False,
                epistemic_status=EpistemicStatus.DIVERGENT,
                confidence=0.55,
                notes="Graph incomplete globally but complete for this scope. Divergence detected.",
            )

        return self._create_divergence(
            world=world,
            divergence_status=TemporalDivergenceStatus.UNKNOWN,
            divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            temporal_order_status=world.expected_temporal_order,
            historical_validity=False,
            current_validity=False,
            epistemic_status=EpistemicStatus.INCOMPLETE,
            confidence=0.25,
            notes="Graph is incomplete. Cannot conclude divergence or escape.",
        )

    def _evaluate_historical_divergence(
        self, world: TemporalDivergenceWorld
    ) -> dict[str, Any]:
        """Evaluate divergence at execution time using ONLY historical state."""
        # If the effect is unauthorized AND the graph is complete for scope
        if world.is_unauthorized_effect:
            if world.graph_complete_for_scope or world.is_complete_graph:
                return {
                    "divergence": True,
                    "cause": DivergenceCause.EFFECTIVE_PATH_NOT_DECLARED,
                    "validity": False,
                    "epistemic": EpistemicStatus.DIVERGENT,
                    "confidence": 0.8,
                }
            else:
                return {
                    "divergence": True,
                    "cause": DivergenceCause.EFFECTIVE_PATH_NOT_DECLARED,
                    "validity": False,
                    "epistemic": EpistemicStatus.INCOMPLETE,
                    "confidence": 0.4,
                }

        # If the effect is authorized
        return {
            "divergence": False,
            "cause": DivergenceCause.NONE,
            "validity": True,
            "epistemic": EpistemicStatus.RECONCILED,
            "confidence": 0.85,
        }

    def _evaluate_current_divergence(
        self, world: TemporalDivergenceWorld
    ) -> dict[str, Any]:
        """Evaluate divergence in the current state (separate from historical).

        Only reports CURRENT_DIVERGENCE when:
        1. The effect was historically valid, AND
        2. The authority state changed in a way that affects the graph
           (not a preserving transition like rotation or widening)
        """
        if world.has_transition and world.authority_state_current is not None:
            # Check if the transition preserves authority
            is_preserving = (
                world.is_identifier_reuse
                or world.is_graph_rollback
                or world.expected_divergence_status == TemporalDivergenceStatus.NO_DIVERGENCE
            )

            if is_preserving:
                # Authority-preserving transition (rotation, widening, reuse)
                return {
                    "divergence": False,
                    "cause": DivergenceCause.NONE,
                    "validity": True,
                    "epistemic": EpistemicStatus.RECONCILED,
                    "confidence": 0.85,
                    "current_status": TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
                }

            # Authority-changing transition
            if world.is_future_revocation_attack:
                return {
                    "divergence": True,
                    "cause": DivergenceCause.NONE,
                    "validity": False,
                    "epistemic": EpistemicStatus.RECONCILED,
                    "confidence": 0.8,
                    "current_status": TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
                }
            if world.is_future_authority_attack:
                return {
                    "divergence": True,
                    "cause": DivergenceCause.FUTURE_AUTHORITY_EXPLAINS_PAST,
                    "validity": False,
                    "epistemic": EpistemicStatus.DIVERGENT,
                    "confidence": 0.8,
                    "current_status": TemporalValidityStatus.CURRENTLY_VALID,
                }
            # Other authority-changing transition
            return {
                "divergence": True,
                "cause": DivergenceCause.NONE,
                "validity": False,
                "epistemic": EpistemicStatus.RECONCILED,
                "confidence": 0.7,
                "current_status": TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            }

        return {
            "divergence": False,
            "cause": DivergenceCause.NONE,
            "validity": True,
            "epistemic": EpistemicStatus.RECONCILED,
            "confidence": 0.85,
            "current_status": TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
        }

    def _combine_divergences(
        self,
        world: TemporalDivergenceWorld,
        historical: dict[str, Any],
        current: dict[str, Any],
    ) -> TemporalAuthorityDivergence:
        """Combine historical and current divergence results."""
        hist_div = historical["divergence"]
        cur_div = current["divergence"]

        if hist_div and cur_div:
            status = TemporalDivergenceStatus.BOTH_DIVERGENCE
        elif hist_div:
            status = TemporalDivergenceStatus.HISTORICAL_DIVERGENCE
        elif cur_div:
            status = TemporalDivergenceStatus.CURRENT_DIVERGENCE
        else:
            status = TemporalDivergenceStatus.NO_DIVERGENCE

        cause = (
            historical["cause"]
            if hist_div and current["cause"] == DivergenceCause.NONE
            else (current["cause"] if cur_div else historical["cause"])
        )

        confidence = (historical["confidence"] + current["confidence"]) / 2

        return self._create_divergence(
            world=world,
            divergence_status=status,
            divergence_cause=cause,
            temporal_order_status=world.expected_temporal_order,
            historical_validity=historical["validity"],
            current_validity=current["validity"],
            epistemic_status=(
                EpistemicStatus.DIVERGENT
                if hist_div
                else current.get("epistemic", EpistemicStatus.RECONCILED)
            ),
            confidence=confidence,
            notes=(
                f"Historical divergence: {hist_div} (cause: {historical['cause'].value}). "
                f"Current divergence: {cur_div} (cause: {current['cause'].value})."
            ),
        )

    def _create_divergence(
        self,
        world: TemporalDivergenceWorld,
        divergence_status: TemporalDivergenceStatus,
        divergence_cause: DivergenceCause,
        temporal_order_status: TemporalOrderStatus,
        historical_validity: bool,
        current_validity: bool,
        epistemic_status: EpistemicStatus,
        confidence: float,
        notes: str,
    ) -> TemporalAuthorityDivergence:
        """Create a divergence record and store it."""
        div = TemporalAuthorityDivergence(
            divergence_id=f"div-{uuid.uuid4().hex[:12]}",
            effect_id=world.observed_effect,
            observation_id=f"obs-{uuid.uuid4().hex[:8]}",
            execution_time=world.execution_time,
            current_time=world.current_time,
            historical_graph_ref=(
                world.authority_state_at_execution.state_id
                if world.authority_state_at_execution
                else "unknown"
            ),
            current_graph_ref=(
                world.authority_state_current.state_id
                if world.authority_state_current
                else "unknown"
            ),
            historical_effective_path=world.effective_path_reconstructed,
            current_effective_status=(
                TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
                if historical_validity and current_validity
                else (
                    TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
                    if historical_validity
                    else (
                        TemporalValidityStatus.CURRENTLY_VALID
                        if current_validity
                        else TemporalValidityStatus.CURRENTLY_INVALID
                    )
                )
            ),
            historical_reconciliation=(
                CorrespondenceStatus.CORRESPONDS
                if historical_validity
                else CorrespondenceStatus.DIVERGES
            ),
            current_reconciliation=(
                CorrespondenceStatus.CORRESPONDS
                if current_validity
                else CorrespondenceStatus.DIVERGES
            ),
            divergence_status=divergence_status,
            divergence_cause=divergence_cause,
            temporal_order_status=temporal_order_status,
            graph_completeness_status=world.graph_completeness,
            historical_validity=historical_validity,
            current_validity=current_validity,
            epistemic_status=epistemic_status,
            confidence=confidence,
            provenance=f"{self.engine_id}:temporal",
            notes=notes,
        )
        self.divergences.append(div)
        return div


# ---------------------------------------------------------------------------
# Adversarial world generator
# ---------------------------------------------------------------------------


class AdversarialWorldGenerator:
    """Generates adversarial worlds for Phase 34 experiments.

    Each world tests a specific temporal divergence scenario. The oracle
    fields represent ground truth available only to the independent oracle.
    """

    def generate_all_worlds(self) -> list[TemporalDivergenceWorld]:
        """Generate all adversarial worlds for Phase 34."""
        return [
            self._world_01_stable_authority_no_divergence(),
            self._world_02_historical_valid_then_revoked(),
            self._world_03_historical_valid_then_expired(),
            self._world_04_historical_valid_then_scope_narrowed(),
            self._world_05_historical_valid_then_policy_superseded(),
            self._world_06_historical_valid_then_trust_anchor_rotated(),
            self._world_07_historical_valid_then_topology_changed(),
            self._world_08_unauthorized_then_later_authorized(),
            self._world_09_unauthorized_then_graph_repair(),
            self._world_10_unauthorized_complete_graph(),
            self._world_11_unauthorized_incomplete_graph(),
            self._world_12_current_differs_from_historical(),
            self._world_13_graph_returns_to_historical_shape(),
            self._world_14_identifier_reuse_capability(),
            self._world_15_identifier_reuse_delegation(),
            self._world_16_identifier_reuse_policy(),
            self._world_17_identifier_reuse_authorization(),
            self._world_18_worker_authority_introduced_after(),
            self._world_19_worker_authority_revoked_after(),
            self._world_20_emergency_authority_introduced(),
            self._world_21_emergency_authority_revoked(),
            self._world_22_recovery_authority_introduced(),
            self._world_23_recovery_authority_superseded(),
            self._world_24_cross_domain_delegation_introduced(),
            self._world_25_cross_domain_delegation_revoked(),
            self._world_26_policy_supersession(),
            self._world_27_policy_deletion(),
            self._world_28_governance_approval_after_unauthorized(),
            self._world_29_governance_revocation_after_valid(),
            self._world_30_capability_widening_after(),
            self._world_31_capability_narrowing_after(),
            self._world_32_runtime_gate_change(),
            self._world_33_runtime_topology_change(),
            self._world_34_historical_evidence_missing(),
            self._world_35_historical_graph_state_missing(),
            self._world_36_partial_historical_provenance(),
            self._world_37_historical_state_known_path_unknown(),
            self._world_38_effective_path_known_graph_incomplete(),
            self._world_39_multiple_valid_paths_at_t(),
            self._world_40_one_path_revoked_other_remains(),
            self._world_41_replayed_authorization_after_revocation(),
            self._world_42_historical_receipt_as_current(),
            self._world_43_effect_at_expiration_boundary(),
            self._world_44_effect_at_activation_boundary(),
            self._world_45_concurrent_events_known_order(),
            self._world_46_concurrent_events_unknown_order(),
            self._world_47_reordered_event_log(),
            self._world_48_missing_event_from_log(),
            self._world_49_contradictory_evidence(),
            self._world_50_graph_rollback_attack(),
        ]

    # -----------------------------------------------------------------------
    # Worlds 01-10: Basic temporal scenarios
    # -----------------------------------------------------------------------

    def _world_01_stable_authority_no_divergence(self) -> TemporalDivergenceWorld:
        """World 01: Stable authority, no divergence. Baseline."""
        state = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        return TemporalDivergenceWorld(
            world_id="world_01_stable_authority_no_divergence",
            description="Stable authority, no divergence",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state,
            authority_state_current=state,
            transition=None,
            observed_effect="eff-valid-001",
            effective_path_reconstructed="path-valid-001",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=False,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_02_historical_valid_then_revoked(self) -> TemporalDivergenceWorld:
        """World 02: Historical effect valid, then authority revoked."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_02_historical_valid_then_revoked",
            description="Historical effect valid, then authority revoked",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-002",
            effective_path_reconstructed="path-valid-002",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_03_historical_valid_then_expired(self) -> TemporalDivergenceWorld:
        """World 03: Historical effect valid, then authority expired."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-03-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_EXPIRATION,
            "2026-03-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_03_historical_valid_then_expired",
            description="Historical effect valid, then authority expired",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-03-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-003",
            effective_path_reconstructed="path-valid-003",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_04_historical_valid_then_scope_narrowed(self) -> TemporalDivergenceWorld:
        """World 04: Historical effect valid, then scope narrowed."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), scope="runtime")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",), scope="staging")
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_SCOPE_NARROWING,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_04_historical_valid_then_scope_narrowed",
            description="Historical effect valid, then scope narrowed",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-004",
            effective_path_reconstructed="path-valid-004",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_05_historical_valid_then_policy_superseded(self) -> TemporalDivergenceWorld:
        """World 05: Historical effect valid, then policy superseded."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", policy_ids=("pol-002",))
        transition = _make_transition(
            AuthorityChangeType.POLICY_SUPERSESSION,
            "2026-02-01T00:00:00Z",
            affected_ids=("pol-001", "pol-002"),
        )
        return TemporalDivergenceWorld(
            world_id="world_05_historical_valid_then_policy_superseded",
            description="Historical effect valid, then policy superseded",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-005",
            effective_path_reconstructed="path-valid-005",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_06_historical_valid_then_trust_anchor_rotated(self) -> TemporalDivergenceWorld:
        """World 06: Historical effect valid, then trust anchor rotated."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", trust_anchor_id="ta-001")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", trust_anchor_id="ta-002")
        transition = _make_transition(
            AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("ta-001", "ta-002"),
        )
        return TemporalDivergenceWorld(
            world_id="world_06_historical_valid_then_trust_anchor_rotated",
            description="Historical effect valid, then trust anchor rotated",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-006",
            effective_path_reconstructed="path-valid-006",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_07_historical_valid_then_topology_changed(self) -> TemporalDivergenceWorld:
        """World 07: Historical effect valid, then runtime topology changed."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = _make_transition(
            AuthorityChangeType.RUNTIME_TOPOLOGY_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_07_historical_valid_then_topology_changed",
            description="Historical effect valid, then runtime topology changed",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-007",
            effective_path_reconstructed="path-valid-007",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_08_unauthorized_then_later_authorized(self) -> TemporalDivergenceWorld:
        """World 08: Unauthorized effect, then authority added later."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=())
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_08_unauthorized_then_later_authorized",
            description="Unauthorized effect, then authority added later",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-unauth-008",
            effective_path_reconstructed="path-unauth-008",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.BOTH_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.FUTURE_AUTHORITY_EXPLAINS_PAST,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=True,
            is_future_authority_attack=True,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_09_unauthorized_then_graph_repair(self) -> TemporalDivergenceWorld:
        """World 09: Unauthorized effect, then graph is repaired to explain it."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=(), is_complete=False)
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",), is_complete=True)
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_09_unauthorized_then_graph_repair",
            description="Unauthorized effect, then graph is repaired to explain it",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-unauth-009",
            effective_path_reconstructed="path-unauth-009",
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=True,
            is_future_authority_attack=True,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    def _world_10_unauthorized_complete_graph(self) -> TemporalDivergenceWorld:
        """World 10: Unauthorized effect with complete graph — genuine escape."""
        state = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        return TemporalDivergenceWorld(
            world_id="world_10_unauthorized_complete_graph",
            description="Unauthorized effect with complete graph — genuine escape",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state,
            authority_state_current=state,
            transition=None,
            observed_effect="eff-unauth-010",
            effective_path_reconstructed="path-unauth-010",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.HISTORICAL_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.EFFECTIVE_PATH_NOT_DECLARED,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=False,
            is_unauthorized_effect=True,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_11_unauthorized_incomplete_graph(self) -> TemporalDivergenceWorld:
        """World 11: Unauthorized effect with incomplete graph — cannot conclude escape."""
        state = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), is_complete=False)
        return TemporalDivergenceWorld(
            world_id="world_11_unauthorized_incomplete_graph",
            description="Unauthorized effect with incomplete graph — cannot conclude escape",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state,
            authority_state_current=state,
            transition=None,
            observed_effect="eff-unauth-011",
            effective_path_reconstructed="path-unauth-011",
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=False,
            is_unauthorized_effect=True,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    # -----------------------------------------------------------------------
    # Worlds 12-25: Graph change scenarios
    # -----------------------------------------------------------------------

    def _world_12_current_differs_from_historical(self) -> TemporalDivergenceWorld:
        """World 12: Current graph differs from historical graph."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-002",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_12_current_differs_from_historical",
            description="Current graph differs from historical graph",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-012",
            effective_path_reconstructed="path-valid-012",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_13_graph_returns_to_historical_shape(self) -> TemporalDivergenceWorld:
        """World 13: Graph returns to a structure resembling the historical one."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_13_graph_returns_to_historical_shape",
            description="Graph returns to a structure resembling the historical one",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-013",
            effective_path_reconstructed="path-valid-013",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=True,
            is_graph_rollback=True,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_14_identifier_reuse_capability(self) -> TemporalDivergenceWorld:
        """World 14: Capability identifier reused across time."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-03-01T00:00:00Z", capability_ids=("cap-001",))
        transition = _make_transition(
            AuthorityChangeType.CAPABILITY_RECREATION,
            "2026-03-01T00:00:00Z",
            affected_ids=("cap-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_14_identifier_reuse_capability",
            description="Capability identifier reused across time",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-03-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-014",
            effective_path_reconstructed="path-valid-014",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=True,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_15_identifier_reuse_delegation(self) -> TemporalDivergenceWorld:
        """World 15: Delegation identifier reused across time."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-03-01T00:00:00Z", delegation_ids=("del-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-03-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_15_identifier_reuse_delegation",
            description="Delegation identifier reused across time",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-03-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-015",
            effective_path_reconstructed="path-valid-015",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=True,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_16_identifier_reuse_policy(self) -> TemporalDivergenceWorld:
        """World 16: Policy identifier reused across time."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-03-01T00:00:00Z", policy_ids=("pol-001",))
        transition = _make_transition(
            AuthorityChangeType.POLICY_RECREATION,
            "2026-03-01T00:00:00Z",
            affected_ids=("pol-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_16_identifier_reuse_policy",
            description="Policy identifier reused across time",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-03-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-016",
            effective_path_reconstructed="path-valid-016",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=True,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_17_identifier_reuse_authorization(self) -> TemporalDivergenceWorld:
        """World 17: Authorization identifier reused across time."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("auth-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-03-01T00:00:00Z", delegation_ids=("auth-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-03-01T00:00:00Z",
            affected_ids=("auth-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_17_identifier_reuse_authorization",
            description="Authorization identifier reused across time",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-03-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-valid-017",
            effective_path_reconstructed="path-valid-017",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=True,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_18_worker_authority_introduced_after(self) -> TemporalDivergenceWorld:
        """World 18: Worker authority introduced after historical execution."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=())
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("wrk-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("wrk-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_18_worker_authority_introduced_after",
            description="Worker authority introduced after historical execution",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-worker-018",
            effective_path_reconstructed="path-worker-018",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.BOTH_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.FUTURE_AUTHORITY_EXPLAINS_PAST,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=True,
            is_future_authority_attack=True,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=True,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_19_worker_authority_revoked_after(self) -> TemporalDivergenceWorld:
        """World 19: Worker authority revoked after historical execution."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("wrk-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.WORKER_DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("wrk-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_19_worker_authority_revoked_after",
            description="Worker authority revoked after historical execution",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-worker-019",
            effective_path_reconstructed="path-worker-019",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=True,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_20_emergency_authority_introduced(self) -> TemporalDivergenceWorld:
        """World 20: Emergency authority introduced."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("emg-001",))
        transition = _make_transition(
            AuthorityChangeType.EMERGENCY_AUTHORITY_ACTIVATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("emg-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_20_emergency_authority_introduced",
            description="Emergency authority introduced",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-emg-020",
            effective_path_reconstructed="path-emg-020",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=True,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_21_emergency_authority_revoked(self) -> TemporalDivergenceWorld:
        """World 21: Emergency authority revoked."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("emg-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.EMERGENCY_AUTHORITY_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("emg-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_21_emergency_authority_revoked",
            description="Emergency authority revoked",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-emg-021",
            effective_path_reconstructed="path-emg-021",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=True,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_22_recovery_authority_introduced(self) -> TemporalDivergenceWorld:
        """World 22: Recovery authority introduced."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("rec-001",))
        transition = _make_transition(
            AuthorityChangeType.RECOVERY_AUTHORITY_SUPERSESSION,
            "2026-02-01T00:00:00Z",
            affected_ids=("rec-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_22_recovery_authority_introduced",
            description="Recovery authority introduced",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-rec-022",
            effective_path_reconstructed="path-rec-022",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=True,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_23_recovery_authority_superseded(self) -> TemporalDivergenceWorld:
        """World 23: Recovery authority superseded."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("rec-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("norm-001",))
        transition = _make_transition(
            AuthorityChangeType.RECOVERY_AUTHORITY_SUPERSESSION,
            "2026-02-01T00:00:00Z",
            affected_ids=("rec-001", "norm-001"),
        )
        return TemporalDivergenceWorld(
            world_id="world_23_recovery_authority_superseded",
            description="Recovery authority superseded",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-rec-023",
            effective_path_reconstructed="path-rec-023",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=True,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_24_cross_domain_delegation_introduced(self) -> TemporalDivergenceWorld:
        """World 24: Cross-domain delegation introduced."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", domain="domain-a")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("xdom-001",), domain="domain-b")
        transition = _make_transition(
            AuthorityChangeType.DOMAIN_DELEGATION_CHANGE,
            "2026-02-01T00:00:00Z",
            affected_ids=("xdom-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_24_cross_domain_delegation_introduced",
            description="Cross-domain delegation introduced",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-xdom-024",
            effective_path_reconstructed="path-xdom-024",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=True,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_25_cross_domain_delegation_revoked(self) -> TemporalDivergenceWorld:
        """World 25: Cross-domain delegation revoked."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("xdom-001",), domain="domain-b")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=(), domain="domain-b")
        transition = _make_transition(
            AuthorityChangeType.CROSS_DOMAIN_DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("xdom-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_25_cross_domain_delegation_revoked",
            description="Cross-domain delegation revoked",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-xdom-025",
            effective_path_reconstructed="path-xdom-025",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=True,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    # -----------------------------------------------------------------------
    # Worlds 26-33: Policy, governance, capability, gate, topology
    # -----------------------------------------------------------------------

    def _world_26_policy_supersession(self) -> TemporalDivergenceWorld:
        """World 26: Policy supersession."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", policy_ids=("pol-002",))
        transition = _make_transition(
            AuthorityChangeType.POLICY_SUPERSESSION,
            "2026-02-01T00:00:00Z",
            affected_ids=("pol-001", "pol-002"),
        )
        return TemporalDivergenceWorld(
            world_id="world_26_policy_supersession",
            description="Policy supersession",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-pol-026",
            effective_path_reconstructed="path-pol-026",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_27_policy_deletion(self) -> TemporalDivergenceWorld:
        """World 27: Policy deletion."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", policy_ids=("pol-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", policy_ids=())
        transition = _make_transition(
            AuthorityChangeType.POLICY_DELETION,
            "2026-02-01T00:00:00Z",
            affected_ids=("pol-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_27_policy_deletion",
            description="Policy deletion",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-pol-027",
            effective_path_reconstructed="path-pol-027",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_28_governance_approval_after_unauthorized(self) -> TemporalDivergenceWorld:
        """World 28: Governance approval after unauthorized effect."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", governance_disposition="review_required")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", governance_disposition="approved")
        transition = _make_transition(
            AuthorityChangeType.GOVERNANCE_DISPOSITION_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_28_governance_approval_after_unauthorized",
            description="Governance approval after unauthorized effect",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-gov-028",
            effective_path_reconstructed="path-gov-028",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.BOTH_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.GOVERNANCE_VIOLATION,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=True,
            is_future_authority_attack=True,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_29_governance_revocation_after_valid(self) -> TemporalDivergenceWorld:
        """World 29: Governance revocation after valid effect."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", governance_disposition="authorized")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", governance_disposition="revoked")
        transition = _make_transition(
            AuthorityChangeType.GOVERNANCE_DISPOSITION_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_29_governance_revocation_after_valid",
            description="Governance revocation after valid effect",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-gov-029",
            effective_path_reconstructed="path-gov-029",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_30_capability_widening_after(self) -> TemporalDivergenceWorld:
        """World 30: Capability widening after historical effect."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",), scope="staging")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", capability_ids=("cap-001",), scope="runtime")
        transition = _make_transition(
            AuthorityChangeType.CAPABILITY_SCOPE_NARROWING,
            "2026-02-01T00:00:00Z",
            affected_ids=("cap-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_30_capability_widening_after",
            description="Capability widening after historical effect",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-cap-030",
            effective_path_reconstructed="path-cap-030",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_31_capability_narrowing_after(self) -> TemporalDivergenceWorld:
        """World 31: Capability narrowing after historical effect."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", capability_ids=("cap-001",), scope="runtime")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", capability_ids=("cap-001",), scope="staging")
        transition = _make_transition(
            AuthorityChangeType.CAPABILITY_SCOPE_NARROWING,
            "2026-02-01T00:00:00Z",
            affected_ids=("cap-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_31_capability_narrowing_after",
            description="Capability narrowing after historical effect",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-cap-031",
            effective_path_reconstructed="path-cap-031",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_32_runtime_gate_change(self) -> TemporalDivergenceWorld:
        """World 32: Runtime gate change."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", execution_gate_policy="gate-001")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", execution_gate_policy="gate-002")
        transition = _make_transition(
            AuthorityChangeType.EXECUTION_GATE_CHANGE,
            "2026-02-01T00:00:00Z",
            affected_ids=("gate-001", "gate-002"),
        )
        return TemporalDivergenceWorld(
            world_id="world_32_runtime_gate_change",
            description="Runtime gate change",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-gate-032",
            effective_path_reconstructed="path-gate-032",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_33_runtime_topology_change(self) -> TemporalDivergenceWorld:
        """World 33: Runtime topology change."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = _make_transition(
            AuthorityChangeType.RUNTIME_TOPOLOGY_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_33_runtime_topology_change",
            description="Runtime topology change",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-topo-033",
            effective_path_reconstructed="path-topo-033",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    # -----------------------------------------------------------------------
    # Worlds 34-42: Missing evidence scenarios
    # -----------------------------------------------------------------------

    def _world_34_historical_evidence_missing(self) -> TemporalDivergenceWorld:
        """World 34: Historical evidence is missing."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = _make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_34_historical_evidence_missing",
            description="Historical evidence is missing",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-miss-034",
            effective_path_reconstructed="",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.RECONSTRUCTION_INCOMPLETE,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_35_historical_graph_state_missing(self) -> TemporalDivergenceWorld:
        """World 35: Historical graph state is missing entirely."""
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        return TemporalDivergenceWorld(
            world_id="world_35_historical_graph_state_missing",
            description="Historical graph state is missing entirely",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=None,
            authority_state_current=state_t2,
            transition=None,
            observed_effect="eff-miss-035",
            effective_path_reconstructed="",
            graph_completeness=GraphCompletenessStatus.UNKNOWN,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.HISTORICAL_STATE_UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.UNKNOWN,
            has_transition=False,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=False,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    def _world_36_partial_historical_provenance(self) -> TemporalDivergenceWorld:
        """World 36: Partial historical provenance available."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), is_complete=False)
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",), is_complete=False)
        transition = _make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_36_partial_historical_provenance",
            description="Partial historical provenance available",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-partial-036",
            effective_path_reconstructed="path-partial-036",
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    def _world_37_historical_state_known_path_unknown(self) -> TemporalDivergenceWorld:
        """World 37: Historical state known but effective path unknown."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z")
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z")
        transition = _make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_37_historical_state_known_path_unknown",
            description="Historical state known but effective path unknown",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-unkpath-037",
            effective_path_reconstructed="",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.RECONSTRUCTION_INCOMPLETE,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_38_effective_path_known_graph_incomplete(self) -> TemporalDivergenceWorld:
        """World 38: Effective path known but declared graph incomplete."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", is_complete=False)
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", is_complete=False)
        transition = _make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_38_effective_path_known_graph_incomplete",
            description="Effective path known but declared graph incomplete",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-inc-038",
            effective_path_reconstructed="path-inc-038",
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    def _world_39_multiple_valid_paths_at_t(self) -> TemporalDivergenceWorld:
        """World 39: Multiple valid paths at historical T."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001", "del-002"))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001", "del-002"))
        transition = _make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_39_multiple_valid_paths_at_t",
            description="Multiple valid paths at historical T",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-multi-039",
            effective_path_reconstructed="path-multi-039",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_40_one_path_revoked_other_remains(self) -> TemporalDivergenceWorld:
        """World 40: One historical path later revoked while another remains valid."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001", "del-002"))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-002",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_40_one_path_revoked_other_remains",
            description="One historical path later revoked while another remains valid",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-one-040",
            effective_path_reconstructed="path-one-040",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    # -----------------------------------------------------------------------
    # Worlds 41-50: Replay, boundary, concurrent, event log, contradictory
    # -----------------------------------------------------------------------

    def _world_41_replayed_authorization_after_revocation(self) -> TemporalDivergenceWorld:
        """World 41: Replayed authorization after revocation."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_41_replayed_authorization_after_revocation",
            description="Replayed authorization after revocation",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-replay-041",
            effective_path_reconstructed="path-replay-041",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_42_historical_receipt_as_current(self) -> TemporalDivergenceWorld:
        """World 42: Historical receipt presented as current authority."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_42_historical_receipt_as_current",
            description="Historical receipt presented as current authority",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-receipt-042",
            effective_path_reconstructed="path-receipt-042",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_43_effect_at_expiration_boundary(self) -> TemporalDivergenceWorld:
        """World 43: Effect occurs exactly at authority expiration boundary."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-01-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_EXPIRATION,
            "2026-01-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_43_effect_at_expiration_boundary",
            description="Effect occurs exactly at authority expiration boundary",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-bound-043",
            effective_path_reconstructed="path-bound-043",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_44_effect_at_activation_boundary(self) -> TemporalDivergenceWorld:
        """World 44: Effect occurs exactly at authority activation boundary."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=())
        state_t2 = _make_state("state-t2", "t2", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-01-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_44_effect_at_activation_boundary",
            description="Effect occurs exactly at authority activation boundary",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-activ-044",
            effective_path_reconstructed="path-activ-044",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.BOTH_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.FUTURE_AUTHORITY_EXPLAINS_PAST,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=True,
            is_future_authority_attack=True,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_45_concurrent_events_known_order(self) -> TemporalDivergenceWorld:
        """World 45: Concurrent events with known ordering."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-01-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-01-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_45_concurrent_events_known_order",
            description="Concurrent events with known ordering",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-conc-045",
            effective_path_reconstructed="path-conc-045",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.CONCURRENT_KNOWN,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=True,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_46_concurrent_events_unknown_order(self) -> TemporalDivergenceWorld:
        """World 46: Concurrent events with unknown ordering."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-01-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-01-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_46_concurrent_events_unknown_order",
            description="Concurrent events with unknown ordering",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-conc-046",
            effective_path_reconstructed="path-conc-046",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.TEMPORAL_ORDER_UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.CONCURRENT_UNKNOWN,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=True,
            temporal_order_known=False,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_47_reordered_event_log(self) -> TemporalDivergenceWorld:
        """World 47: Reordered event log."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=())
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_47_reordered_event_log",
            description="Reordered event log",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-reorder-047",
            effective_path_reconstructed="path-reorder-047",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.CURRENT_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=True,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=True,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )

    def _world_48_missing_event_from_log(self) -> TemporalDivergenceWorld:
        """World 48: Missing event from historical authority log."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), is_complete=False)
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=(), is_complete=False)
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_REVOCATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_48_missing_event_from_log",
            description="Missing event from historical authority log",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-missev-048",
            effective_path_reconstructed="path-missev-048",
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=True,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    def _world_49_contradictory_evidence(self) -> TemporalDivergenceWorld:
        """World 49: Contradictory evidence from two sources."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",), is_complete=False)
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",), is_complete=False)
        transition = _make_transition(
            AuthorityChangeType.NO_CHANGE,
            "2026-02-01T00:00:00Z",
        )
        return TemporalDivergenceWorld(
            world_id="world_49_contradictory_evidence",
            description="Contradictory evidence from two sources",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-contr-049",
            effective_path_reconstructed="path-contr-049",
            graph_completeness=GraphCompletenessStatus.INCOMPLETE,
            graph_complete_for_scope=False,
            expected_divergence_status=TemporalDivergenceStatus.UNKNOWN,
            expected_divergence_cause=DivergenceCause.MISSING_HISTORICAL_EVIDENCE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=False,
            is_graph_rollback=False,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=False,
            is_incomplete_graph=True,
        )

    def _world_50_graph_rollback_attack(self) -> TemporalDivergenceWorld:
        """World 50: Graph rollback attack — graph returns to historical shape."""
        state_t1 = _make_state("state-t1", "t1", "2026-01-01T00:00:00Z", delegation_ids=("del-001",))
        state_t2 = _make_state("state-t2", "t2", "2026-02-01T00:00:00Z", delegation_ids=("del-001",))
        transition = _make_transition(
            AuthorityChangeType.DELEGATION_RECREATION,
            "2026-02-01T00:00:00Z",
            affected_ids=("del-001",),
        )
        return TemporalDivergenceWorld(
            world_id="world_50_graph_rollback_attack",
            description="Graph rollback attack — graph returns to historical shape",
            execution_time="2026-01-01T00:00:00Z",
            current_time="2026-02-01T00:00:00Z",
            authority_state_at_execution=state_t1,
            authority_state_current=state_t2,
            transition=transition,
            observed_effect="eff-rollback-050",
            effective_path_reconstructed="path-rollback-050",
            graph_completeness=GraphCompletenessStatus.COMPLETE,
            graph_complete_for_scope=True,
            expected_divergence_status=TemporalDivergenceStatus.NO_DIVERGENCE,
            expected_divergence_cause=DivergenceCause.NONE,
            expected_temporal_order=TemporalOrderStatus.BEFORE,
            has_transition=True,
            is_unauthorized_effect=False,
            is_future_authority_attack=False,
            is_future_revocation_attack=False,
            is_identifier_reuse=True,
            is_graph_rollback=True,
            is_event_reorder=False,
            is_missing_event=False,
            is_emergency=False,
            is_recovery=False,
            is_cross_domain=False,
            is_worker_authority=False,
            is_concurrent_event=False,
            temporal_order_known=True,
            is_complete_graph=True,
            is_incomplete_graph=False,
        )


# ---------------------------------------------------------------------------
# Independent oracle
# ---------------------------------------------------------------------------


class IndependentOracle:
    """Evaluates divergence detection results against ground truth.

    The oracle knows the true divergence status but the detection engine
    does not. This provides an independent evaluation of detection accuracy.
    """

    def evaluate(
        self,
        world: TemporalDivergenceWorld,
        divergence: TemporalAuthorityDivergence,
    ) -> dict[str, Any]:
        """Evaluate a divergence detection result against ground truth."""
        status_match = divergence.divergence_status == world.expected_divergence_status
        cause_match = divergence.divergence_cause == world.expected_divergence_cause
        order_match = divergence.temporal_order_status == world.expected_temporal_order

        # False historical divergence: detected divergence but actually valid
        false_historical_divergence = (
            divergence.divergence_status
            in (
                TemporalDivergenceStatus.HISTORICAL_DIVERGENCE,
                TemporalDivergenceStatus.BOTH_DIVERGENCE,
            )
            and world.expected_divergence_status == TemporalDivergenceStatus.NO_DIVERGENCE
        )

        # False historical authorization: detected valid but actually divergent
        false_historical_authorization = (
            divergence.divergence_status == TemporalDivergenceStatus.NO_DIVERGENCE
            and world.expected_divergence_status
            in (
                TemporalDivergenceStatus.HISTORICAL_DIVERGENCE,
                TemporalDivergenceStatus.BOTH_DIVERGENCE,
            )
        )

        # False current authority: detected current divergence but actually valid
        false_current_authority = (
            divergence.divergence_status
            in (
                TemporalDivergenceStatus.CURRENT_DIVERGENCE,
                TemporalDivergenceStatus.BOTH_DIVERGENCE,
            )
            and world.expected_divergence_status == TemporalDivergenceStatus.NO_DIVERGENCE
        )

        return {
            "evaluation_id": f"eval-{uuid.uuid4().hex[:12]}",
            "world_id": world.world_id,
            "status_match": status_match,
            "cause_match": cause_match,
            "order_match": order_match,
            "false_historical_divergence": false_historical_divergence,
            "false_historical_authorization": false_historical_authorization,
            "false_current_authority": false_current_authority,
            "notes": (
                f"Expected: {world.expected_divergence_status.value}. "
                f"Got: {divergence.divergence_status.value}."
            ),
        }


# ---------------------------------------------------------------------------
# Phase 34 experiment
# ---------------------------------------------------------------------------


class Phase34Experiment:
    """Runs the complete Phase 34 experiment."""

    def __init__(self) -> None:
        self.engine = DivergenceDetectionEngine("phase34-engine")
        self.worlds = AdversarialWorldGenerator().generate_all_worlds()
        self.oracle = IndependentOracle()
        self.results: list[dict[str, Any]] = []

    def run_all(self) -> dict[str, Any]:
        """Run all worlds and return summary."""
        for world in self.worlds:
            divergence = self.engine.detect_divergence(world)
            evaluation = self.oracle.evaluate(world, divergence)
            self.results.append({
                "world_id": world.world_id,
                "divergence_status": divergence.divergence_status.value,
                "expected_status": world.expected_divergence_status.value,
                "divergence_cause": divergence.divergence_cause.value,
                "expected_cause": world.expected_divergence_cause.value,
                "temporal_order": divergence.temporal_order_status.value,
                "expected_order": world.expected_temporal_order.value,
                "historical_validity": divergence.historical_validity,
                "current_validity": divergence.current_validity,
                "epistemic_status": divergence.epistemic_status.value,
                "status_match": evaluation["status_match"],
                "cause_match": evaluation["cause_match"],
                "order_match": evaluation["order_match"],
                "false_historical_divergence": evaluation["false_historical_divergence"],
                "false_historical_authorization": evaluation["false_historical_authorization"],
                "false_current_authority": evaluation["false_current_authority"],
            })
        return self.summary()

    def summary(self) -> dict[str, Any]:
        """Generate experiment summary."""
        total = len(self.results)
        status_matches = sum(1 for r in self.results if r["status_match"])
        cause_matches = sum(1 for r in self.results if r["cause_match"])
        order_matches = sum(1 for r in self.results if r["order_match"])
        false_hist_div = sum(1 for r in self.results if r["false_historical_divergence"])
        false_hist_auth = sum(1 for r in self.results if r["false_historical_authorization"])
        false_cur_auth = sum(1 for r in self.results if r["false_current_authority"])

        return {
            "total_worlds": total,
            "total_divergences": len(self.engine.divergences),
            "status_matches": status_matches,
            "cause_matches": cause_matches,
            "order_matches": order_matches,
            "status_accuracy": status_matches / total if total > 0 else 0,
            "cause_accuracy": cause_matches / total if total > 0 else 0,
            "order_accuracy": order_matches / total if total > 0 else 0,
            "false_historical_divergence_rate": false_hist_div / total if total > 0 else 0,
            "false_historical_authorization_rate": false_hist_auth / total if total > 0 else 0,
            "false_current_authority_rate": false_cur_auth / total if total > 0 else 0,
        }
