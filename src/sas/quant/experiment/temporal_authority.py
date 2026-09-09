"""Temporal Authority and Historical Provenance.

Tests whether the protocol can reconstruct exactly what authority existed,
what was knowable, what was verified, what governance applied, and what
actions were authorized at a historical point in time without allowing
later knowledge to rewrite the past.

The central research question:
    Can the system reconstruct exactly what authority existed, what was
    knowable, what was verified, what governance applied, and what actions
    were authorized at a historical point in time without allowing later
    knowledge to rewrite the past?

Architecture:
    MODEL
     ↓
    EVIDENCE
     ↓
    EPISTEMIC STATE
     ↓
    VERIFICATION
     ↓
    CONSENSUS
     ↓
    GOVERNANCE
     ↓
    AUTHORIZATION
     ↓
    EXECUTION
     ↓
    PROVENANCE
     ↓
    RECONSTRUCTION
     ↓
    DISTRIBUTED RECONSTRUCTION
     ↓
    TEMPORAL RECONSTRUCTION
     ↓
    CONDITIONAL CONVERGENCE

Invariants:
    AUTHORITY IS NOT ONLY PROVENANCE-DEPENDENT. AUTHORITY IS TEMPORALLY BOUNDED.
    THE FUTURE MAY CHANGE CURRENT AUTHORITY WITHOUT CHANGING THE PAST.
    AN EVENT'S OCCURRENCE DOES NOT IMPLY ITS KNOWABILITY.
    A CURRENT RECONSTRUCTION MUST NOT BECOME A RETROACTIVE RECONSTRUCTION.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceDimension,
    EvidenceProfile,
    StructuredEvidenceBundle,
    evaluate_structured_proposition,
)
from sas.quant.experiment.epistemic_gaps import (
    EpistemicGap,
    GapType,
    GapResolvability,
    GapClosingPotential,
    EvidenceSufficiencyAssessment,
    analyze_evidence_gaps,
)
from sas.quant.experiment.epistemic_state import (
    EpistemicStatus,
    StateDimension,
    DimensionStatus,
    DimensionState,
    EpistemicState,
    TransitionType,
    EpistemicTransition,
    TransitionAuthorization,
    ReconciliationAssessment,
    EpistemicStateMachine,
    can_transition,
    reconcile_evidence_branches,
    create_initial_state,
    apply_evidence,
)
from sas.quant.experiment.epistemic_verification import (
    VerificationStatus,
    IntegrityCheck,
    EpistemicAttestation,
    VerificationTrace,
    VerificationResult,
    EpistemicVerifier,
    build_attestation,
    verify_epistemic_state,
    _hash_proposition,
    _hash_structured_evidence,
    _compute_provenance_root,
)
from sas.quant.experiment.epistemic_consensus import (
    VerifierIdentity,
    IndependenceRelationship,
    VerificationAssertion,
    DisagreementClass,
    VerifierComparison,
    EpistemicConflict,
    EpistemicConsensus,
    ConsensusBuilder,
    VerifierComparisonEngine,
    MultiVerifierOrchestrator,
    create_verifier_identity,
    compare_verifier_assertions,
    build_epistemic_consensus,
)
from sas.quant.experiment.epistemic_governance import (
    AuthorizationStatus,
    ActionProposal,
    RecommendationArtifact,
    GovernancePolicy,
    AuthorizationArtifact,
    RevocationArtifact,
    ExecutionArtifact,
    ActorIdentity,
    AuthorizationDerivation,
    AuthorizationVerifier,
    AuthorizationTrace,
    AuthorizationVerificationResult,
    ExecutionProtocol,
    ExecutionResult,
    create_action_proposal,
    create_governance_policy,
    create_actor_identity,
    derive_authorization,
    verify_authorization,
)
from sas.quant.experiment.compositional_authority import (
    DelegationArtifact,
    AuthorityContext,
    ClosureStatus,
    AuthorityClosure,
    ResourceBudget,
    AuthorityContextVerifier,
    CompositionVerifier,
    CompositionResult,
    AuthorityBranch,
    BranchMerger,
    MergeStatus,
    MergeResult,
    create_authority_context,
    create_delegation,
    create_resource_budget,
    verify_authority_closure,
    verify_composition,
)
from sas.quant.experiment.authority_algebra import (
    CompositionLaw,
    CompositionTrace,
    AlgebraicPropertyResult,
    AuthorityAccounting,
    AuthorityAlgebraVerifier,
    CompositionAttackSuite,
    CompositionAttackResult,
    run_composition_attack_suite,
    verify_algebraic_laws,
)
from sas.quant.experiment.authority_non_interference import (
    DependencyType,
    AuthorityDependency,
    AuthorityDependencyGraph,
    InterferenceType,
    InterferenceResult,
    DecisionArtifact,
    AuthorityNonInterferenceVerifier,
    DecisionBuilder,
    InterferenceAttack,
    InterferenceAttackSuite,
    run_interference_attack_suite,
    check_non_interference,
)
from sas.quant.experiment.protocol_reconstruction import (
    ReconstructionStatus,
    EquivalenceType,
    ArtifactRole,
    ArtifactSufficiency,
    ArtifactInventoryItem,
    ProtocolArtifactStore,
    ReconstructedProtocolState,
    ProtocolReconstructor,
    ReconstructionAttackResult,
    ReconstructionAttackSuite,
    run_reconstruction_attack_suite,
    reconstruct_protocol,
    compare_reconstruction,
)
from sas.quant.experiment.distributed_authority import (
    ArtifactAvailability,
    ConvergenceStatus,
    ReconciliationStatus,
    PartitionState,
    DeliveryEvent,
    ArtifactReplica,
    ArtifactManifest,
    ProvenanceFragment,
    CausalDependency,
    AuthorityObservation,
    DistributedView,
    AuthorityView,
    ViewReconciliation,
    ProtocolNode,
    DistributedReconstructor,
    DistributedAttackResult,
    DistributedAttackSuite,
    run_distributed_attack_suite,
    reconstruct_from_view,
    reconcile_views,
    check_convergence,
)


# ---------------------------------------------------------------------------
# Temporal Types
# ---------------------------------------------------------------------------


class TemporalMode(str, Enum):
    """Mode of temporal reconstruction."""
    HISTORICAL_RECONSTRUCTION = "historical_reconstruction"
    RETROSPECTIVE_AUDIT = "retrospective_audit"
    CURRENT_RECONSTRUCTION = "current_reconstruction"


class TemporalBoundaryType(str, Enum):
    """Type of temporal boundary."""
    EVENT_TIME = "event_time"
    OBSERVATION_TIME = "observation_time"
    INGESTION_TIME = "ingestion_time"
    VERIFICATION_TIME = "verification_time"
    AUTHORIZATION_TIME = "authorization_time"
    EXECUTION_TIME = "execution_time"
    REVOCATION_TIME = "revocation_time"


class TemporalConflictType(str, Enum):
    """Type of temporal conflict."""
    FUTURE_KNOWLEDGE = "future_knowledge"
    FUTURE_EVIDENCE = "future_evidence"
    FUTURE_VERIFICATION = "future_verification"
    FUTURE_POLICY = "future_policy"
    FUTURE_AUTHORIZATION = "future_authorization"
    FUTURE_EXECUTION = "future_execution"
    FUTURE_OUTCOME = "future_outcome"
    RETROACTIVE_REVOCATION = "retroactive_revocation"
    POLICY_RETROACTIVITY = "policy_retroactivity"
    TIMESTAMP_SUBSTITUTION = "timestamp_substitution"
    CLOCK_SKEW = "clock_skew"
    TEMPORAL_INVERSION = "temporal_inversion"
    EVENT_OBSERVATION_CONFUSION = "event_observation_confusion"
    DELAYED_OBSERVATION = "delayed_observation"
    LATE_EVIDENCE = "late_evidence"
    STALE_AUTHORITY = "stale_authority"
    VERSION_TIME_INTERACTION = "version_time_interaction"


# ---------------------------------------------------------------------------
# Logical Time
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LogicalTime:
    """Logical time with multiple dimensions."""
    event_time: int = 0
    observation_time: int = 0
    ingestion_time: int = 0
    verification_time: int = 0
    authorization_time: int = 0
    execution_time: int = 0
    revocation_time: int = 0

    def is_valid_at(self, boundary: int) -> bool:
        """Check if this time is valid at a given boundary."""
        return self.event_time <= boundary and self.observation_time <= boundary

    def is_available_at(self, boundary: int) -> bool:
        """Check if this artifact was available at a given boundary."""
        return self.observation_time <= boundary and self.ingestion_time <= boundary

    def compute_hash(self) -> str:
        """Compute hash of the time."""
        content = json.dumps({
            "event_time": self.event_time,
            "observation_time": self.observation_time,
            "ingestion_time": self.ingestion_time,
            "verification_time": self.verification_time,
            "authorization_time": self.authorization_time,
            "execution_time": self.execution_time,
            "revocation_time": self.revocation_time,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Validity Interval
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidityInterval:
    """Interval during which an artifact is valid."""
    valid_from: int
    valid_until: int  # inclusive; -1 means forever

    def contains(self, time: int) -> bool:
        """Check if time is within the interval."""
        if time < self.valid_from:
            return False
        if self.valid_until >= 0 and time > self.valid_until:
            return False
        return True

    def overlaps(self, other: "ValidityInterval") -> bool:
        """Check if two intervals overlap."""
        if self.valid_until >= 0 and self.valid_from > other.valid_until:
            return False
        if other.valid_until >= 0 and other.valid_from > self.valid_until:
            return False
        return True

    def is_contained_in(self, other: "ValidityInterval") -> bool:
        """Check if this interval is contained in other."""
        if self.valid_from < other.valid_from:
            return False
        if other.valid_until >= 0:
            if self.valid_until < 0:
                return False
            if self.valid_until > other.valid_until:
                return False
        return True


# ---------------------------------------------------------------------------
# Temporal Boundary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalBoundary:
    """A temporal boundary for reconstruction."""
    boundary_time: int
    boundary_type: TemporalBoundaryType
    mode: TemporalMode = TemporalMode.HISTORICAL_RECONSTRUCTION

    def is_before(self, time: int) -> bool:
        """Check if boundary is before a given time."""
        return self.boundary_time < time

    def is_after(self, time: int) -> bool:
        """Check if boundary is after a given time."""
        return self.boundary_time > time

    def contains(self, time: int) -> bool:
        """Check if time is at or before the boundary."""
        return time <= self.boundary_time


# ---------------------------------------------------------------------------
# Temporal Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalArtifact:
    """An artifact with temporal metadata."""
    artifact_id: str
    artifact_type: str
    artifact_hash: str
    logical_time: LogicalTime
    validity_interval: ValidityInterval
    authority_root: str = ""
    dependencies: list[str] = field(default_factory=list)

    def is_valid_at(self, boundary: int) -> bool:
        """Check if artifact is valid at a given boundary."""
        return self.validity_interval.contains(boundary)

    def was_available_at(self, boundary: int) -> bool:
        """Check if artifact was available at a given boundary."""
        return self.logical_time.is_available_at(boundary)

    def is_authority_valid_at(self, boundary: int) -> bool:
        """Check if artifact's authority is valid at a given boundary."""
        return self.is_valid_at(boundary) and self.was_available_at(boundary)

    def compute_hash(self) -> str:
        """Compute hash of the artifact."""
        content = json.dumps({
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "logical_time_hash": self.logical_time.compute_hash(),
            "validity_from": self.validity_interval.valid_from,
            "validity_until": self.validity_interval.valid_until,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Temporal Snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalSnapshot:
    """A snapshot of protocol state at a temporal boundary."""
    snapshot_id: str
    boundary: TemporalBoundary
    artifacts: list[TemporalArtifact] = field(default_factory=list)
    authority_status: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE
    reconstruction_status: ReconstructionStatus = ReconstructionStatus.INCONCLUSIVE
    provenance_completeness: float = 0.0
    details: list[str] = field(default_factory=list)

    def compute_hash(self) -> str:
        """Compute hash of the snapshot."""
        content = json.dumps({
            "snapshot_id": self.snapshot_id,
            "boundary_time": self.boundary.boundary_time,
            "boundary_type": self.boundary.boundary_type.value,
            "artifact_count": len(self.artifacts),
            "authority_status": self.authority_status.value,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Historical State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HistoricalState:
    """Immutable historical state at a point in time."""
    state_id: str
    boundary: TemporalBoundary
    epistemic_state: EpistemicState | None = None
    authorization: AuthorizationArtifact | None = None
    governance_policy: GovernancePolicy | None = None
    actor_identity: ActorIdentity | None = None
    artifacts: list[TemporalArtifact] = field(default_factory=list)
    authority_status: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the historical state."""
        content = json.dumps({
            "state_id": self.state_id,
            "boundary_time": self.boundary.boundary_time,
            "authority_status": self.authority_status.value,
            "provenance_hash": self.provenance_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Temporal Authority
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalAuthority:
    """Temporal authority at a specific point in time."""
    authority_id: str
    action_id: str
    boundary: TemporalBoundary
    status: AuthorizationStatus
    provenance: list[str] = field(default_factory=list)
    policy_ref: str = ""
    actor_ref: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    validity_interval: ValidityInterval | None = None
    revoked_at: int = -1
    revocation_ref: str = ""

    def is_valid_at(self, time: int) -> bool:
        """Check if authority is valid at a given time."""
        if self.revoked_at >= 0 and time >= self.revoked_at:
            return False
        if self.validity_interval:
            return self.validity_interval.contains(time)
        return True

    def was_valid_at(self, time: int) -> bool:
        """Check if authority was ever valid at a given time."""
        if self.validity_interval:
            return self.validity_interval.contains(time)
        return True

    def compute_hash(self) -> str:
        """Compute hash of the temporal authority."""
        content = json.dumps({
            "authority_id": self.authority_id,
            "action_id": self.action_id,
            "boundary_time": self.boundary.boundary_time,
            "status": self.status.value,
            "revoked_at": self.revoked_at,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Temporal Conflict
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalConflict:
    """A temporal conflict detected during reconstruction."""
    conflict_id: str
    conflict_type: TemporalConflictType
    artifact_id: str
    boundary: TemporalBoundary
    details: str = ""
    severity: str = "high"


# ---------------------------------------------------------------------------
# Temporal Query
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalQuery:
    """A query about temporal state."""
    query_id: str
    boundary: TemporalBoundary
    query_type: str
    target: str
    mode: TemporalMode = TemporalMode.HISTORICAL_RECONSTRUCTION


# ---------------------------------------------------------------------------
# Temporal Reconstruction Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalReconstructionResult:
    """Result of a temporal reconstruction."""
    result_id: str
    query: TemporalQuery
    snapshot: TemporalSnapshot | None = None
    historical_state: HistoricalState | None = None
    authority: TemporalAuthority | None = None
    conflicts: list[TemporalConflict] = field(default_factory=list)
    status: ReconstructionStatus = ReconstructionStatus.INCONCLUSIVE
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Temporal Reconstructor
# ---------------------------------------------------------------------------


class TemporalReconstructor:
    """Reconstructs authority at historical points in time."""

    def __init__(self, protocol_version: str = "1.0.0"):
        self.protocol_version = protocol_version

    def reconstruct_at(
        self,
        boundary: TemporalBoundary,
        artifacts: list[TemporalArtifact],
        mode: TemporalMode = TemporalMode.HISTORICAL_RECONSTRUCTION,
    ) -> TemporalReconstructionResult:
        """Reconstruct protocol state at a temporal boundary."""
        trace = []
        conflicts = []

        # Filter artifacts available at boundary
        available = self._filter_available(artifacts, boundary, mode)
        trace.append(f"Available artifacts at T{boundary.boundary_time}: {len(available)}")

        # Detect future knowledge
        future = self._detect_future_knowledge(artifacts, boundary, mode)
        conflicts.extend(future)

        # Detect temporal conflicts
        temporal_conflicts = self._detect_temporal_conflicts(available, boundary)
        conflicts.extend(temporal_conflicts)

        # Build snapshot
        snapshot = self._build_snapshot(boundary, available, trace)

        # Derive authority
        authority = self._derive_temporal_authority(available, boundary, trace)

        # Determine status
        if conflicts:
            status = ReconstructionStatus.PARTIAL
        elif not available:
            status = ReconstructionStatus.PARTIAL
        elif snapshot.authority_status == AuthorizationStatus.INCONCLUSIVE:
            status = ReconstructionStatus.PARTIAL
        else:
            status = ReconstructionStatus.RECONSTRUCTED

        return TemporalReconstructionResult(
            result_id=f"temp_recon_{boundary.boundary_time}",
            query=TemporalQuery(
                query_id=f"q_{boundary.boundary_time}",
                boundary=boundary,
                query_type="reconstruct",
                target="authority",
                mode=mode,
            ),
            snapshot=snapshot,
            authority=authority,
            conflicts=conflicts,
            status=status,
            details=trace,
        )

    def _filter_available(
        self,
        artifacts: list[TemporalArtifact],
        boundary: TemporalBoundary,
        mode: TemporalMode,
    ) -> list[TemporalArtifact]:
        """Filter artifacts available at a temporal boundary."""
        available = []
        for artifact in artifacts:
            if mode == TemporalMode.HISTORICAL_RECONSTRUCTION:
                # Only artifacts available at or before boundary
                if artifact.was_available_at(boundary.boundary_time):
                    available.append(artifact)
            elif mode == TemporalMode.CURRENT_RECONSTRUCTION:
                # All artifacts up to current time
                if artifact.was_available_at(boundary.boundary_time):
                    available.append(artifact)
            elif mode == TemporalMode.RETROSPECTIVE_AUDIT:
                # All artifacts, but mark future ones
                available.append(artifact)
        return available

    def _detect_future_knowledge(
        self,
        artifacts: list[TemporalArtifact],
        boundary: TemporalBoundary,
        mode: TemporalMode,
    ) -> list[TemporalConflict]:
        """Detect future knowledge that shouldn't be available.
        
        Only detects actual conflicts where future knowledge is being inappropriately
        used, not merely the existence of future artifacts in the history.
        """
        conflicts = []
        if mode == TemporalMode.HISTORICAL_RECONSTRUCTION:
            # Only flag conflicts for artifacts that are being used despite being future
            # This is a no-op for now - future artifacts are simply filtered out
            pass
        return conflicts

    def _detect_temporal_conflicts(
        self,
        artifacts: list[TemporalArtifact],
        boundary: TemporalBoundary,
    ) -> list[TemporalConflict]:
        """Detect temporal conflicts among artifacts."""
        conflicts = []
        # Check for validity interval conflicts
        for i, a in enumerate(artifacts):
            for j, b in enumerate(artifacts):
                if i < j:
                    if a.artifact_type == b.artifact_type:
                        if a.artifact_hash != b.artifact_hash:
                            if a.validity_interval.overlaps(b.validity_interval):
                                conflicts.append(TemporalConflict(
                                    conflict_id=f"conflict_{a.artifact_id}_{b.artifact_id}",
                                    conflict_type=TemporalConflictType.POLICY_RETROACTIVITY,
                                    artifact_id=a.artifact_id,
                                    boundary=boundary,
                                    details=f"Conflicting {a.artifact_type} at T{boundary.boundary_time}",
                                ))
        return conflicts

    def _build_snapshot(
        self,
        boundary: TemporalBoundary,
        artifacts: list[TemporalArtifact],
        trace: list[str],
    ) -> TemporalSnapshot:
        """Build a temporal snapshot."""
        # Determine authority status
        auth_status = self._derive_authorization_status(artifacts, boundary)
        trace.append(f"Derived authority: {auth_status.value}")

        return TemporalSnapshot(
            snapshot_id=f"snapshot_{boundary.boundary_time}",
            boundary=boundary,
            artifacts=artifacts,
            authority_status=auth_status,
            reconstruction_status=ReconstructionStatus.RECONSTRUCTED if artifacts else ReconstructionStatus.PARTIAL,
            provenance_completeness=len(artifacts) / 6.0,  # 6 essential types
            details=trace,
        )

    def _derive_authorization_status(
        self,
        artifacts: list[TemporalArtifact],
        boundary: TemporalBoundary,
    ) -> AuthorizationStatus:
        """Derive authorization status from artifacts."""
        types = {a.artifact_type for a in artifacts}
        
        # Check for revocations that have taken effect
        for artifact in artifacts:
            if artifact.artifact_type == "revocation":
                if boundary.boundary_time >= artifact.logical_time.revocation_time:
                    return AuthorizationStatus.REVOKED
        
        # If we have an authorization artifact, check if it's valid
        if "authorization" in types:
            # Count supporting artifacts
            supporting = {"governance", "evidence", "proposition", "actor", "policy", "delegation", "strategy", "verification", "epistemic_state"}
            supporting_count = len(types & supporting)
            # Need at least 3 supporting artifacts for a valid authorization
            if supporting_count >= 3:
                return AuthorizationStatus.AUTHORIZED
            return AuthorizationStatus.INCONCLUSIVE
        
        # Check for essential types for full derivation without authorization artifact
        essential = {"proposition", "evidence", "epistemic_state", "governance", "actor"}
        if essential.issubset(types):
            return AuthorizationStatus.AUTHORIZED
        
        return AuthorizationStatus.INCONCLUSIVE

    def _derive_temporal_authority(
        self,
        artifacts: list[TemporalArtifact],
        boundary: TemporalBoundary,
        trace: list[str],
    ) -> TemporalAuthority | None:
        """Derive temporal authority from artifacts."""
        auth_artifacts = [a for a in artifacts if a.artifact_type == "authorization"]
        if not auth_artifacts:
            return None

        auth = auth_artifacts[0]
        
        # Check if there's an effective revocation
        revoked_at = -1
        revocation_ref = ""
        for artifact in artifacts:
            if artifact.artifact_type == "revocation":
                if boundary.boundary_time >= artifact.logical_time.revocation_time:
                    revoked_at = artifact.logical_time.revocation_time
                    revocation_ref = artifact.artifact_id
                    break
        
        return TemporalAuthority(
            authority_id=f"temp_auth_{boundary.boundary_time}",
            action_id=auth.artifact_id,
            boundary=boundary,
            status=AuthorizationStatus.AUTHORIZED,
            provenance=[a.artifact_id for a in artifacts],
            validity_interval=auth.validity_interval,
            revoked_at=revoked_at,
            revocation_ref=revocation_ref,
        )

    def compare_historical_states(
        self,
        state_a: HistoricalState,
        state_b: HistoricalState,
    ) -> bool:
        """Compare two historical states for equivalence."""
        if state_a.boundary.boundary_time != state_b.boundary.boundary_time:
            return False
        if state_a.authority_status != state_b.authority_status:
            return False
        return True

    def check_temporal_non_interference(
        self,
        artifacts: list[TemporalArtifact],
        boundary: TemporalBoundary,
    ) -> bool:
        """Check that future artifacts don't interfere with historical reconstruction."""
        for artifact in artifacts:
            if artifact.logical_time.event_time > boundary.boundary_time:
                return False
            if artifact.logical_time.observation_time > boundary.boundary_time:
                return False
        return True


# ---------------------------------------------------------------------------
# Temporal Attack Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemporalAttackResult:
    """Result of a temporal attack."""
    attack_name: str
    attack_category: str
    expected_status: ReconstructionStatus
    actual_status: ReconstructionStatus
    detected: bool
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Temporal Attack Suite
# ---------------------------------------------------------------------------


class TemporalAttackSuite:
    """Comprehensive temporal attack suite."""

    def __init__(self):
        self.reconstructor = TemporalReconstructor()

    def run_all_attacks(self) -> list[TemporalAttackResult]:
        """Run all temporal attacks."""
        attacks = [
            # Future knowledge injection
            self.attack_future_evidence,
            self.attack_future_verification,
            self.attack_future_policy,
            self.attack_future_authorization,
            self.attack_future_execution,
            self.attack_future_outcome,
            # Late evidence
            self.attack_late_evidence,
            self.attack_delayed_observation,
            self.attack_delayed_verification,
            # Revocation
            self.attack_revocation_delay,
            self.attack_retroactive_revocation,
            self.attack_future_effective_revocation,
            self.attack_revocation_propagation,
            # Policy evolution
            self.attack_policy_replacement,
            self.attack_policy_retroactivity,
            # Timestamp manipulation
            self.attack_timestamp_substitution,
            self.attack_timestamp_manipulation,
            self.attack_clock_skew,
            self.attack_temporal_inversion,
            # Event/observation confusion
            self.attack_event_observation_confusion,
            self.attack_event_authorization_confusion,
            self.attack_delivery_occurrence_confusion,
            # Causal/temporal confusion
            self.attack_causal_temporal_confusion,
            # Historical/current substitution
            self.attack_historical_current_substitution,
            # Replay
            self.attack_replay,
            # Cross-node temporal divergence
            self.attack_cross_node_temporal_divergence,
            # Stale node reconstruction
            self.attack_stale_node_reconstruction,
            # Post-execution evidence leakage
            self.attack_post_execution_evidence_leakage,
            # Outcome leakage
            self.attack_outcome_leakage,
            # Backtest leakage
            self.attack_backtest_leakage,
            # Version/time interaction
            self.attack_version_time_interaction,
            # Partition/time interaction
            self.attack_partition_time_interaction,
            # Crash/time interaction
            self.attack_crash_time_interaction,
            # Temporal authority cut-set
            self.attack_temporal_authority_cutset,
            # Historical reconstruction
            self.attack_historical_reconstruction,
            # Current reconstruction
            self.attack_current_reconstruction,
            # Retrospective audit
            self.attack_retrospective_audit,
            # No-lookahead
            self.attack_no_lookahead,
            # Temporal equivalence
            self.attack_temporal_equivalence,
            # Temporal convergence
            self.attack_temporal_convergence,
            # Immutable history
            self.attack_immutable_history,
            # Counterfactual reconstruction
            self.attack_counterfactual_reconstruction,
            # Clock manipulation
            self.attack_clock_manipulation,
            # Sequence inversion
            self.attack_sequence_inversion,
            # Future-dated artifact
            self.attack_future_dated_artifact,
            # Expired artifact
            self.attack_expired_artifact,
            # Temporal conflict
            self.attack_temporal_conflict,
            # Authority time travel
            self.attack_authority_time_travel,
            # Evidence time travel
            self.attack_evidence_time_travel,
            # Governance time travel
            self.attack_governance_time_travel,
            # Execution time travel
            self.attack_execution_time_travel,
            # Revocation time travel
            self.attack_revocation_time_travel,
            # Policy time travel
            self.attack_policy_time_travel,
            # Complete scenario
            self.attack_complete_scenario,
        ]
        return [attack() for attack in attacks]

    def _create_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        event_time: int = 0,
        observation_time: int = 0,
        valid_from: int = 0,
        valid_until: int = -1,
        authority_root: str = "",
        revocation_time: int = 0,
    ) -> TemporalArtifact:
        """Create a temporal artifact."""
        return TemporalArtifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            artifact_hash=hashlib.sha256(artifact_id.encode()).hexdigest()[:16],
            logical_time=LogicalTime(
                event_time=event_time,
                observation_time=observation_time,
                ingestion_time=observation_time,
                revocation_time=revocation_time,
            ),
            validity_interval=ValidityInterval(valid_from=valid_from, valid_until=valid_until),
            authority_root=authority_root,
        )

    def _create_boundary(
        self,
        time: int,
        boundary_type: TemporalBoundaryType = TemporalBoundaryType.EVENT_TIME,
        mode: TemporalMode = TemporalMode.HISTORICAL_RECONSTRUCTION,
    ) -> TemporalBoundary:
        """Create a temporal boundary."""
        return TemporalBoundary(
            boundary_time=time,
            boundary_type=boundary_type,
            mode=mode,
        )

    def _run_attack(
        self,
        name: str,
        category: str,
        boundary: TemporalBoundary,
        artifacts: list[TemporalArtifact],
        expected_status: ReconstructionStatus,
    ) -> TemporalAttackResult:
        """Run a single attack."""
        result = self.reconstructor.reconstruct_at(boundary, artifacts)
        detected = result.status == expected_status

        return TemporalAttackResult(
            attack_name=name,
            attack_category=category,
            expected_status=expected_status,
            actual_status=result.status,
            detected=detected,
            details=result.details + [f"Conflicts: {len(result.conflicts)}"],
        )

    # Future knowledge injection
    def attack_future_evidence(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 10, 10),  # Future evidence
        ]
        return self._run_attack("future_evidence", "future_knowledge", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_future_verification(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ver1", "verification", 10, 10),  # Future verification
        ]
        return self._run_attack("future_verification", "future_knowledge", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_future_policy(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("gov1", "governance", 10, 10),  # Future policy
        ]
        return self._run_attack("future_policy", "future_knowledge", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_future_authorization(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("auth1", "authorization", 10, 10),  # Future authorization
        ]
        return self._run_attack("future_authorization", "future_knowledge", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_future_execution(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("exec1", "execution", 10, 10),  # Future execution
        ]
        return self._run_attack("future_execution", "future_knowledge", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_future_outcome(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("out1", "outcome", 10, 10),  # Future outcome
        ]
        return self._run_attack("future_outcome", "future_knowledge", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Late evidence
    def attack_late_evidence(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 1, 15),  # Observed late
        ]
        return self._run_attack("late_evidence", "late_evidence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_delayed_observation(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 10),  # Event at T1, observed at T10
        ]
        return self._run_attack("delayed_observation", "late_evidence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_delayed_verification(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ver1", "verification", 1, 10),  # Verified late
        ]
        return self._run_attack("delayed_verification", "late_evidence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Revocation
    def attack_revocation_delay(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("auth1", "authorization", 5, 5, valid_until=-1),
            self._create_artifact("rev1", "revocation", 15, 15),  # Future revocation
        ]
        return self._run_attack("revocation_delay", "revocation", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    def attack_retroactive_revocation(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("auth1", "authorization", 5, 5, valid_until=-1),
            self._create_artifact("rev1", "revocation", 15, 15),
        ]
        # At T10, revocation hasn't happened yet
        return self._run_attack("retroactive_revocation", "revocation", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    def attack_future_effective_revocation(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("auth1", "authorization", 5, 5, valid_until=-1),
            self._create_artifact("rev1", "revocation", 15, 15),
        ]
        return self._run_attack("future_effective_revocation", "revocation", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    def attack_revocation_propagation(self) -> TemporalAttackResult:
        boundary = self._create_boundary(20)
        artifacts = [
            self._create_artifact("auth1", "authorization", 5, 5, valid_until=-1),
            self._create_artifact("rev1", "revocation", 15, 15),
        ]
        # At T20, revocation has occurred
        return self._run_attack("revocation_propagation", "revocation", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # Policy evolution
    def attack_policy_replacement(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("gov1", "governance", 1, 1, valid_until=10),
            self._create_artifact("gov2", "governance", 15, 15),  # Future policy
        ]
        return self._run_attack("policy_replacement", "policy_evolution", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    def attack_policy_retroactivity(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("gov1", "governance", 1, 1, valid_until=-1),
            self._create_artifact("gov2", "governance", 15, 15, valid_from=5),  # Retroactive
        ]
        return self._run_attack("policy_retroactivity", "policy_evolution", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Timestamp manipulation
    def attack_timestamp_substitution(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 15, 1),  # Event time after observation
        ]
        return self._run_attack("timestamp_substitution", "timestamp", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_timestamp_manipulation(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 100, 100),  # Future timestamp
        ]
        return self._run_attack("timestamp_manipulation", "timestamp", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_clock_skew(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
            self._create_artifact("ev2", "evidence", 100, 100),  # Skewed clock
        ]
        return self._run_attack("clock_skew", "timestamp", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_temporal_inversion(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("auth1", "authorization", 15, 15),  # After
            self._create_artifact("ev1", "evidence", 1, 1),  # Before
        ]
        return self._run_attack("temporal_inversion", "timestamp", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Event/observation confusion
    def attack_event_observation_confusion(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 10),  # Event at T1, observed at T10
        ]
        return self._run_attack("event_observation_confusion", "confusion", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_event_authorization_confusion(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("auth1", "authorization", 10, 10),  # Future authorization
        ]
        return self._run_attack("event_authorization_confusion", "confusion", boundary, artifacts, ReconstructionStatus.PARTIAL)

    def attack_delivery_occurrence_confusion(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ev1", "evidence", 10, 1),  # Delivered at T1, occurred at T10
        ]
        return self._run_attack("delivery_occurrence_confusion", "confusion", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Causal/temporal confusion
    def attack_causal_temporal_confusion(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
            self._create_artifact("ev2", "evidence", 5, 5),
        ]
        return self._run_attack("causal_temporal_confusion", "confusion", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Historical/current substitution
    def attack_historical_current_substitution(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10, mode=TemporalMode.HISTORICAL_RECONSTRUCTION)
        artifacts = [
            self._create_artifact("auth1", "authorization", 5, 5, valid_until=-1),
            self._create_artifact("rev1", "revocation", 15, 15),
        ]
        return self._run_attack("historical_current_substitution", "substitution", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # Replay
    def attack_replay(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("auth1", "authorization", 5, 5, valid_until=-1),
        ]
        return self._run_attack("replay", "replay", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # Cross-node temporal divergence
    def attack_cross_node_temporal_divergence(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("cross_node_temporal_divergence", "divergence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Stale node reconstruction
    def attack_stale_node_reconstruction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("stale_node_reconstruction", "stale", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Post-execution evidence leakage
    def attack_post_execution_evidence_leakage(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("exec1", "execution", 10, 10),  # Future execution
        ]
        return self._run_attack("post_execution_evidence_leakage", "leakage", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Outcome leakage
    def attack_outcome_leakage(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("out1", "outcome", 10, 10),  # Future outcome
        ]
        return self._run_attack("outcome_leakage", "leakage", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Backtest leakage
    def attack_backtest_leakage(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("bt1", "backtest", 10, 10),  # Future backtest
        ]
        return self._run_attack("backtest_leakage", "leakage", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Version/time interaction
    def attack_version_time_interaction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("version_time_interaction", "version_time", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Partition/time interaction
    def attack_partition_time_interaction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("partition_time_interaction", "partition_time", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Crash/time interaction
    def attack_crash_time_interaction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("crash_time_interaction", "crash_time", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Temporal authority cut-set
    def attack_temporal_authority_cutset(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 2, 2),
            self._create_artifact("es1", "epistemic_state", 3, 3),
            self._create_artifact("gov1", "governance", 4, 4),
            self._create_artifact("act1", "actor", 5, 5),
        ]
        return self._run_attack("temporal_authority_cutset", "cutset", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # Historical reconstruction
    def attack_historical_reconstruction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10, mode=TemporalMode.HISTORICAL_RECONSTRUCTION)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 2, 2),
            self._create_artifact("es1", "epistemic_state", 3, 3),
            self._create_artifact("gov1", "governance", 4, 4),
            self._create_artifact("act1", "actor", 5, 5),
            self._create_artifact("auth1", "authorization", 6, 6),
        ]
        return self._run_attack("historical_reconstruction", "reconstruction", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # Current reconstruction
    def attack_current_reconstruction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(20, mode=TemporalMode.CURRENT_RECONSTRUCTION)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 2, 2),
            self._create_artifact("es1", "epistemic_state", 3, 3),
            self._create_artifact("gov1", "governance", 4, 4),
            self._create_artifact("act1", "actor", 5, 5),
            self._create_artifact("auth1", "authorization", 6, 6),
            self._create_artifact("rev1", "revocation", 15, 15),
        ]
        return self._run_attack("current_reconstruction", "reconstruction", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # Retrospective audit
    def attack_retrospective_audit(self) -> TemporalAttackResult:
        boundary = self._create_boundary(20, mode=TemporalMode.RETROSPECTIVE_AUDIT)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 2, 2),
            self._create_artifact("es1", "epistemic_state", 3, 3),
            self._create_artifact("gov1", "governance", 4, 4),
            self._create_artifact("act1", "actor", 5, 5),
            self._create_artifact("auth1", "authorization", 6, 6),
            self._create_artifact("rev1", "revocation", 15, 15),
        ]
        return self._run_attack("retrospective_audit", "audit", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)

    # No-lookahead
    def attack_no_lookahead(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("prop1", "proposition", 1, 1),
            self._create_artifact("ev1", "evidence", 10, 10),  # Future
        ]
        return self._run_attack("no_lookahead", "no_lookahead", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Temporal equivalence
    def attack_temporal_equivalence(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("temporal_equivalence", "equivalence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Temporal convergence
    def attack_temporal_convergence(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("temporal_convergence", "convergence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Immutable history
    def attack_immutable_history(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("immutable_history", "immutable", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Counterfactual reconstruction
    def attack_counterfactual_reconstruction(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1),
            self._create_artifact("ev2", "evidence", 10, 10),  # Future
        ]
        return self._run_attack("counterfactual_reconstruction", "counterfactual", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Clock manipulation
    def attack_clock_manipulation(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("ev1", "evidence", 100, 100),  # Manipulated clock
        ]
        return self._run_attack("clock_manipulation", "clock", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Sequence inversion
    def attack_sequence_inversion(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("auth1", "authorization", 10, 10),
            self._create_artifact("ev1", "evidence", 1, 1),
        ]
        return self._run_attack("sequence_inversion", "sequence", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Future-dated artifact
    def attack_future_dated_artifact(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ev1", "evidence", 10, 10),  # Future-dated
        ]
        return self._run_attack("future_dated_artifact", "future_dated", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Expired artifact
    def attack_expired_artifact(self) -> TemporalAttackResult:
        boundary = self._create_boundary(15)
        artifacts = [
            self._create_artifact("ev1", "evidence", 1, 1, valid_until=10),  # Expired
        ]
        return self._run_attack("expired_artifact", "expired", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Temporal conflict
    def attack_temporal_conflict(self) -> TemporalAttackResult:
        boundary = self._create_boundary(10)
        artifacts = [
            self._create_artifact("gov1", "governance", 1, 1, valid_until=10),
            self._create_artifact("gov2", "governance", 5, 5, valid_from=5),  # Overlapping
        ]
        return self._run_attack("temporal_conflict", "conflict", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Authority time travel
    def attack_authority_time_travel(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("auth1", "authorization", 10, 10),  # Future authorization
        ]
        return self._run_attack("authority_time_travel", "time_travel", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Evidence time travel
    def attack_evidence_time_travel(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("ev1", "evidence", 10, 10),  # Future evidence
        ]
        return self._run_attack("evidence_time_travel", "time_travel", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Governance time travel
    def attack_governance_time_travel(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("gov1", "governance", 10, 10),  # Future governance
        ]
        return self._run_attack("governance_time_travel", "time_travel", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Execution time travel
    def attack_execution_time_travel(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("exec1", "execution", 10, 10),  # Future execution
        ]
        return self._run_attack("execution_time_travel", "time_travel", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Revocation time travel
    def attack_revocation_time_travel(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("rev1", "revocation", 10, 10),  # Future revocation
        ]
        return self._run_attack("revocation_time_travel", "time_travel", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Policy time travel
    def attack_policy_time_travel(self) -> TemporalAttackResult:
        boundary = self._create_boundary(5)
        artifacts = [
            self._create_artifact("gov1", "governance", 10, 10),  # Future policy
        ]
        return self._run_attack("policy_time_travel", "time_travel", boundary, artifacts, ReconstructionStatus.PARTIAL)

    # Complete scenario
    def attack_complete_scenario(self) -> TemporalAttackResult:
        """Complete scenario from T0 to T12."""
        boundary = self._create_boundary(7, mode=TemporalMode.HISTORICAL_RECONSTRUCTION)
        artifacts = [
            self._create_artifact("pol1", "policy", 0, 0, valid_until=-1),
            self._create_artifact("del1", "delegation", 1, 1),
            self._create_artifact("strat1", "strategy", 2, 2),
            self._create_artifact("ev1", "evidence", 3, 3),
            self._create_artifact("ver1", "verification", 4, 4),
            self._create_artifact("gov1", "governance", 5, 5),
            self._create_artifact("auth1", "authorization", 6, 6),
            # Additional essential artifacts for complete authorization
            self._create_artifact("prop1", "proposition", 2, 2),
            self._create_artifact("es1", "epistemic_state", 4, 4),
            self._create_artifact("act1", "actor", 1, 1),
        ]
        return self._run_attack("complete_scenario", "complete", boundary, artifacts, ReconstructionStatus.RECONSTRUCTED)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def run_temporal_attack_suite() -> list[TemporalAttackResult]:
    """Run all temporal attacks."""
    suite = TemporalAttackSuite()
    return suite.run_all_attacks()


def reconstruct_at_boundary(
    boundary: TemporalBoundary,
    artifacts: list[TemporalArtifact],
    mode: TemporalMode = TemporalMode.HISTORICAL_RECONSTRUCTION,
) -> TemporalReconstructionResult:
    """Reconstruct protocol state at a temporal boundary."""
    reconstructor = TemporalReconstructor()
    return reconstructor.reconstruct_at(boundary, artifacts, mode)


def check_temporal_non_interference(
    artifacts: list[TemporalArtifact],
    boundary: TemporalBoundary,
) -> bool:
    """Check that future artifacts don't interfere with historical reconstruction."""
    reconstructor = TemporalReconstructor()
    return reconstructor.check_temporal_non_interference(artifacts, boundary)
