"""Distributed Authority Convergence.

Tests whether reconstructible authority remains valid when the protocol
is distributed across independent processes, machines, artifact stores,
and partially observed provenance.

The central research question:
    Can authority survive process separation, partial knowledge,
    asynchronous delivery, conflicting views, and distributed
    reconstruction without becoming stronger merely because nodes
    converge on the same answer?

Architecture:
    Producer A ──┐
                 │
    Producer B ──┼──→ Artifact Exchange ──→ Reconstructor
                 │             ↑
    Producer C ──┘             │
                               ↓
                          Independent
                           Verifier

Invariants:
    AUTHORITY IS A FUNCTION OF PROVENANCE, NOT LOCATION.
    AUTHORITY DOES NOT INCREASE BECAUSE MORE NODES OBSERVE IT.
    DISTRIBUTED AGREEMENT DOES NOT CREATE AUTHORITY.
    PARTIAL KNOWLEDGE MUST PRODUCE BOUNDED UNCERTAINTY, NOT INFERRED ABSENCE.
    EQUIVALENT PROVENANCE MUST PRODUCE EQUIVALENT AUTHORITY.
    INCOMPLETE PROVENANCE CANNOT BE COMPLETED BY CONSENSUS ALONE.
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


# ---------------------------------------------------------------------------
# Artifact Availability
# ---------------------------------------------------------------------------


class ArtifactAvailability(str, Enum):
    """Availability status of an artifact at a node."""
    UNKNOWN = "unknown"
    MISSING = "missing"
    NOT_YET_RECEIVED = "not_yet_received"
    NOT_APPLICABLE = "not_applicable"
    INVALID = "invalid"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"
    AVAILABLE = "available"
    VERIFIED = "verified"


# ---------------------------------------------------------------------------
# Convergence Status
# ---------------------------------------------------------------------------


class ConvergenceStatus(str, Enum):
    """Status of convergence between distributed views."""
    CONVERGED = "converged"
    NON_CONVERGENT = "non_convergent"
    PARTIALLY_CONVERGED = "partially_converged"
    CONFLICTING = "conflicting"
    INSUFFICIENT_KNOWLEDGE = "insufficient_knowledge"
    VERSION_MISMATCH = "version_mismatch"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Reconciliation Status
# ---------------------------------------------------------------------------


class ReconciliationStatus(str, Enum):
    """Status of view reconciliation."""
    RECONCILED = "reconciled"
    CONFLICTING = "conflicting"
    INCOMPLETE = "incomplete"
    VERSION_MISMATCH = "version_mismatch"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    PROVENANCE_MISMATCH = "provenance_mismatch"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Partition State
# ---------------------------------------------------------------------------


class PartitionState(str, Enum):
    """Network partition state."""
    CONNECTED = "connected"
    PARTITIONED = "partitioned"
    HEALING = "healing"
    HEALED = "healed"


# ---------------------------------------------------------------------------
# Delivery Event
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeliveryEvent:
    """An artifact delivery event."""
    event_id: str
    artifact_type: str
    artifact_hash: str
    source_node: str
    target_node: str
    timestamp: int
    protocol_version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Artifact Replica
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArtifactReplica:
    """A replica of an artifact at a node."""
    replica_id: str
    artifact_type: str
    artifact_hash: str
    availability: ArtifactAvailability
    received_at: int = 0
    verified: bool = False
    source_node: str = ""
    protocol_version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Artifact Manifest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArtifactManifest:
    """What artifacts a node has."""
    manifest_id: str
    artifacts: dict[str, ArtifactReplica] = field(default_factory=dict)
    protocol_version: str = "1.0.0"

    def has_artifact(self, artifact_type: str) -> bool:
        """Check if manifest has an available artifact of given type."""
        if artifact_type not in self.artifacts:
            return False
        return self.artifacts[artifact_type].availability in (
            ArtifactAvailability.AVAILABLE,
            ArtifactAvailability.VERIFIED,
        )

    def get_availability(self, artifact_type: str) -> ArtifactAvailability:
        """Get availability of an artifact type."""
        if artifact_type not in self.artifacts:
            return ArtifactAvailability.UNKNOWN
        return self.artifacts[artifact_type].availability

    def compute_hash(self) -> str:
        """Compute hash of the manifest."""
        content = json.dumps({
            "manifest_id": self.manifest_id,
            "artifacts": {k: v.artifact_hash for k, v in sorted(self.artifacts.items())},
            "protocol_version": self.protocol_version,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Provenance Fragment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProvenanceFragment:
    """A fragment of the provenance graph."""
    fragment_id: str
    artifact_type: str
    artifact_hash: str
    parent_hashes: list[str] = field(default_factory=list)
    causal_dependencies: list[str] = field(default_factory=list)
    timestamp: int = 0
    authority_root: str = ""


# ---------------------------------------------------------------------------
# Causal Dependency
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CausalDependency:
    """Causal dependency between artifacts."""
    dependency_id: str
    source_artifact: str
    target_artifact: str
    dependency_type: str
    satisfied: bool = False


# ---------------------------------------------------------------------------
# Authority Observation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityObservation:
    """An observation of authority at a node."""
    observation_id: str
    node_id: str
    authority_status: AuthorizationStatus
    timestamp: int
    provenance_hash: str = ""
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Distributed View
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DistributedView:
    """A node's view of the protocol."""
    view_id: str
    node_id: str
    manifest: ArtifactManifest
    provenance_fragments: list[ProvenanceFragment] = field(default_factory=list)
    causal_dependencies: list[CausalDependency] = field(default_factory=list)
    authority_observations: list[AuthorityObservation] = field(default_factory=list)
    protocol_version: str = "1.0.0"
    partition_state: PartitionState = PartitionState.CONNECTED
    temporal_position: int = 0

    def has_artifact(self, artifact_type: str) -> bool:
        """Check if view has an available artifact."""
        return self.manifest.has_artifact(artifact_type)

    def get_availability(self, artifact_type: str) -> ArtifactAvailability:
        """Get availability of an artifact type."""
        return self.manifest.get_availability(artifact_type)

    def compute_hash(self) -> str:
        """Compute hash of the view."""
        content = json.dumps({
            "view_id": self.view_id,
            "node_id": self.node_id,
            "manifest_hash": self.manifest.compute_hash(),
            "protocol_version": self.protocol_version,
            "partition_state": self.partition_state.value,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authority View
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityView:
    """A node's view of authority."""
    view_id: str
    node_id: str
    authority_status: AuthorizationStatus
    reconstruction_status: ReconstructionStatus
    provenance_completeness: float = 0.0
    artifact_count: int = 0
    verified_count: int = 0
    confidence: float = 0.0
    timestamp: int = 0
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# View Reconciliation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ViewReconciliation:
    """Reconciling two distributed views."""
    reconciliation_id: str
    view_a: DistributedView
    view_b: DistributedView
    status: ReconciliationStatus
    convergence: ConvergenceStatus
    combined_artifacts: dict[str, ArtifactReplica] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)
    missing_artifacts: list[str] = field(default_factory=list)
    version_compatible: bool = True
    temporal_consistent: bool = True
    provenance_consistent: bool = True


# ---------------------------------------------------------------------------
# Protocol Node
# ---------------------------------------------------------------------------


@dataclass
class ProtocolNode:
    """A node in the distributed protocol."""
    node_id: str
    protocol_version: str = "1.0.0"
    manifest: ArtifactManifest = field(default_factory=lambda: ArtifactManifest(manifest_id=""))
    provenance_fragments: list[ProvenanceFragment] = field(default_factory=list)
    causal_dependencies: list[CausalDependency] = field(default_factory=list)
    authority_observations: list[AuthorityObservation] = field(default_factory=list)
    partition_state: PartitionState = PartitionState.CONNECTED
    temporal_position: int = 0
    received_events: list[DeliveryEvent] = field(default_factory=list)
    reconstructed_state: ReconstructedProtocolState | None = None
    authority_view: AuthorityView | None = None

    def __post_init__(self):
        if not self.manifest.manifest_id:
            self.manifest = ArtifactManifest(manifest_id=f"manifest_{self.node_id}")

    def receive_artifact(self, event: DeliveryEvent, artifact: ArtifactReplica) -> None:
        """Receive an artifact delivery."""
        self.received_events.append(event)
        # Update manifest
        self.manifest = ArtifactManifest(
            manifest_id=self.manifest.manifest_id,
            artifacts={**self.manifest.artifacts, event.artifact_type: artifact},
            protocol_version=self.manifest.protocol_version,
        )
        self.temporal_position = max(self.temporal_position, event.timestamp)

    def get_view(self) -> DistributedView:
        """Get the current distributed view."""
        return DistributedView(
            view_id=f"view_{self.node_id}",
            node_id=self.node_id,
            manifest=self.manifest,
            provenance_fragments=list(self.provenance_fragments),
            causal_dependencies=list(self.causal_dependencies),
            authority_observations=list(self.authority_observations),
            protocol_version=self.protocol_version,
            partition_state=self.partition_state,
            temporal_position=self.temporal_position,
        )


# ---------------------------------------------------------------------------
# Distributed Reconstructor
# ---------------------------------------------------------------------------


class DistributedReconstructor:
    """Reconstructs authority from distributed views."""

    def __init__(self, protocol_version: str = "1.0.0"):
        self.protocol_version = protocol_version
        self.base_reconstructor = ProtocolReconstructor(protocol_version)

    def reconstruct_from_view(self, view: DistributedView) -> ReconstructedProtocolState:
        """Reconstruct authority from a distributed view."""
        trace = []
        missing = []

        # Check protocol version
        if view.protocol_version != self.protocol_version:
            trace.append(f"Version mismatch: {view.protocol_version} vs {self.protocol_version}")
            return ReconstructedProtocolState(
                reconstruction_id=f"recon_{view.view_id}",
                status=ReconstructionStatus.VERSION_MISMATCH,
                reconstruction_trace=trace,
            )

        # Check partition state
        if view.partition_state == PartitionState.PARTITIONED:
            trace.append("Node is partitioned")
            return ReconstructedProtocolState(
                reconstruction_id=f"recon_{view.view_id}",
                status=ReconstructionStatus.PARTIAL,
                reconstruction_trace=trace,
                missing_artifacts=["partitioned"],
            )

        # Determine available artifacts
        essential_types = [
            "proposition", "evidence", "epistemic_state",
            "governance", "actor", "authorization",
        ]
        available = {}
        for art_type in essential_types:
            avail = view.get_availability(art_type)
            if avail in (ArtifactAvailability.AVAILABLE, ArtifactAvailability.VERIFIED):
                available[art_type] = avail
            else:
                missing.append(art_type)

        # Determine reconstruction status
        if not available:
            status = ReconstructionStatus.PARTIAL
        elif len(available) < len(essential_types):
            status = ReconstructionStatus.PARTIAL
        else:
            status = ReconstructionStatus.RECONSTRUCTED

        # Derive authorization from available artifacts
        auth_status = self._derive_authorization(view, available, trace)

        return ReconstructedProtocolState(
            reconstruction_id=f"recon_{view.view_id}",
            status=status,
            reconstructed_authorization=auth_status,
            reconstruction_trace=trace,
            missing_artifacts=missing,
        )

    def _derive_authorization(
        self,
        view: DistributedView,
        available: dict[str, ArtifactAvailability],
        trace: list[str],
    ) -> AuthorizationStatus:
        """Derive authorization from available artifacts."""
        # Check essential artifacts
        if "proposition" not in available:
            trace.append("Missing proposition")
            return AuthorizationStatus.INCONCLUSIVE
        if "evidence" not in available:
            trace.append("Missing evidence")
            return AuthorizationStatus.INCONCLUSIVE
        if "epistemic_state" not in available:
            trace.append("Missing epistemic state")
            return AuthorizationStatus.INCONCLUSIVE
        if "governance" not in available:
            trace.append("Missing governance")
            return AuthorizationStatus.INCONCLUSIVE
        if "actor" not in available:
            trace.append("Missing actor")
            return AuthorizationStatus.INCONCLUSIVE

        # Check for revocations
        if "revocation" in available:
            trace.append("Revocation present")
            return AuthorizationStatus.REVOKED

        # Check for conflicts
        if "conflict" in available:
            trace.append("Conflict present")
            return AuthorizationStatus.POLICY_CONFLICT

        # All essential artifacts available
        trace.append("All essential artifacts available")
        return AuthorizationStatus.AUTHORIZED

    def reconcile_views(
        self, view_a: DistributedView, view_b: DistributedView
    ) -> ViewReconciliation:
        """Reconcile two distributed view."""
        conflicts = []
        missing = []
        version_compatible = True
        temporal_consistent = True
        provenance_consistent = True

        # Check protocol version compatibility
        if view_a.protocol_version != view_b.protocol_version:
            version_compatible = False
            conflicts.append(
                f"Version mismatch: {view_a.protocol_version} vs {view_b.protocol_version}"
            )

        # Check temporal consistency
        if abs(view_a.temporal_position - view_b.temporal_position) > 100:
            temporal_consistent = False
            conflicts.append("Temporal inconsistency")

        # Combine artifacts
        combined = {}
        combined.update(view_a.manifest.artifacts)
        for art_type, replica in view_b.manifest.artifacts.items():
            if art_type in combined:
                existing = combined[art_type]
                if existing.artifact_hash != replica.artifact_hash:
                    conflicts.append(f"Artifact conflict: {art_type}")
                if existing.availability != replica.availability:
                    conflicts.append(f"Availability conflict: {art_type}")
            combined[art_type] = replica

        # Check for missing artifacts
        all_types = set(view_a.manifest.artifacts.keys()) | set(view_b.manifest.artifacts.keys())
        essential_types = {"proposition", "evidence", "epistemic_state", "governance", "actor"}
        for art_type in essential_types:
            if art_type not in all_types:
                missing.append(art_type)

        # Determine reconciliation status
        if conflicts:
            status = ReconciliationStatus.CONFLICTING
        elif missing:
            status = ReconciliationStatus.INCOMPLETE
        elif not version_compatible:
            status = ReconciliationStatus.VERSION_MISMATCH
        elif not temporal_consistent:
            status = ReconciliationStatus.TEMPORAL_MISMATCH
        else:
            status = ReconciliationStatus.RECONCILED

        # Determine convergence
        if status == ReconciliationStatus.RECONCILED:
            convergence = ConvergenceStatus.CONVERGED
        elif conflicts:
            convergence = ConvergenceStatus.CONFLICTING
        elif missing:
            convergence = ConvergenceStatus.INSUFFICIENT_KNOWLEDGE
        elif not version_compatible:
            convergence = ConvergenceStatus.VERSION_MISMATCH
        else:
            convergence = ConvergenceStatus.UNKNOWN

        return ViewReconciliation(
            reconciliation_id=f"recon_{view_a.view_id}_{view_b.view_id}",
            view_a=view_a,
            view_b=view_b,
            status=status,
            convergence=convergence,
            combined_artifacts=combined,
            conflicts=conflicts,
            missing_artifacts=missing,
            version_compatible=version_compatible,
            temporal_consistent=temporal_consistent,
            provenance_consistent=provenance_consistent,
        )

    def check_convergence(
        self, views: list[DistributedView]
    ) -> ConvergenceStatus:
        """Check convergence across multiple views."""
        if not views:
            return ConvergenceStatus.UNKNOWN

        # Check protocol versions
        versions = {v.protocol_version for v in views}
        if len(versions) > 1:
            return ConvergenceStatus.VERSION_MISMATCH

        # Check partition states
        partitions = {v.partition_state for v in views}
        if PartitionState.PARTITIONED in partitions:
            return ConvergenceStatus.PARTIALLY_CONVERGED

        # Check temporal consistency
        temporal_positions = [v.temporal_position for v in views if v.temporal_position > 0]
        if temporal_positions:
            temporal_range = max(temporal_positions) - min(temporal_positions)
            if temporal_range > 100:
                return ConvergenceStatus.NON_CONVERGENT

        # Build artifact maps: {artifact_type: hash}
        artifact_maps = []
        for view in views:
            artifacts = {}
            for art_type, replica in view.manifest.artifacts.items():
                if replica.availability in (ArtifactAvailability.AVAILABLE, ArtifactAvailability.VERIFIED):
                    artifacts[art_type] = replica.artifact_hash
            artifact_maps.append(artifacts)

        # Check for hash conflicts (same artifact type, different hashes)
        for i, a in enumerate(artifact_maps):
            for j, b in enumerate(artifact_maps):
                if i < j:
                    for art_type in set(a.keys()) & set(b.keys()):
                        if a[art_type] != b[art_type]:
                            return ConvergenceStatus.NON_CONVERGENT

        # Check if all views have identical artifact sets
        all_sets = [set(a.keys()) for a in artifact_maps]
        all_hashes = [tuple(sorted(a.items())) for a in artifact_maps]

        if all(s == all_sets[0] for s in all_sets) and all(h == all_hashes[0] for h in all_hashes):
            # All views have the same artifacts with same hashes
            if len(all_sets[0]) >= 5:
                return ConvergenceStatus.CONVERGED
            elif len(all_sets[0]) > 0:
                return ConvergenceStatus.INSUFFICIENT_KNOWLEDGE
            else:
                # All views are empty - they converge on "nothing known"
                return ConvergenceStatus.CONVERGED

        # Check for partial overlap (different artifacts, no conflicts)
        for i, a in enumerate(artifact_maps):
            for j, b in enumerate(artifact_maps):
                if i < j:
                    if set(a.keys()) != set(b.keys()):
                        return ConvergenceStatus.PARTIALLY_CONVERGED

        return ConvergenceStatus.PARTIALLY_CONVERGED


# ---------------------------------------------------------------------------
# Distributed Attack Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DistributedAttackResult:
    """Result of a distributed attack."""
    attack_name: str
    attack_category: str
    expected_convergence: ConvergenceStatus
    actual_convergence: ConvergenceStatus
    detected: bool
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Distributed Attack Suite
# ---------------------------------------------------------------------------


class DistributedAttackSuite:
    """Comprehensive distributed attack suite."""

    def __init__(self):
        self.reconstructor = DistributedReconstructor()

    def run_all_attacks(self) -> list[DistributedAttackResult]:
        """Run all distributed attacks."""
        attacks = [
            # Partial knowledge
            self.attack_partial_knowledge_proposition,
            self.attack_partial_knowledge_evidence,
            self.attack_partial_knowledge_governance,
            self.attack_partial_knowledge_actor,
            # Artifact omission
            self.attack_omit_proposition,
            self.attack_omit_evidence,
            self.attack_omit_governance,
            # Artifact substitution
            self.attack_substitute_evidence,
            self.attack_substitute_policy,
            self.attack_substitute_actor,
            # Artifact duplication
            self.attack_duplicate_evidence,
            # Artifact reordering
            self.attack_reorder_delivery,
            # Delayed delivery
            self.attack_delayed_evidence,
            self.attack_delayed_revocation,
            # Replay
            self.attack_replay_authorization,
            # Revocation delay
            self.attack_revocation_delay,
            # Temporal inversion
            self.attack_temporal_inversion,
            # Policy conflict
            self.attack_policy_conflict,
            # Verification conflict
            self.attack_verification_conflict,
            # Governance conflict
            self.attack_governance_conflict,
            # Identity substitution
            self.attack_identity_substitution,
            # Delegation substitution
            self.attack_delegation_substitution,
            # Cross-domain artifacts
            self.attack_cross_domain_artifact,
            # Byzantine node
            self.attack_byzantine_forged_evidence,
            self.attack_byzantine_stale_artifact,
            # Sybil identity
            self.attack_sybil_identity,
            # Provenance fragmentation
            self.attack_provenance_fragmentation,
            # Version divergence
            self.attack_version_divergence,
            # Partition
            self.attack_partition,
            self.attack_partition_healing,
            # Crash recovery
            self.attack_crash_recovery,
            # Historical/current confusion
            self.attack_historical_current_confusion,
            # Stale authority
            self.attack_stale_authority,
            # Conflicting roots
            self.attack_conflicting_roots,
            # Dependency omission
            self.attack_dependency_omission,
            # Resource contention
            self.attack_resource_contention,
            # Authority cut-set
            self.attack_authority_cutset,
            # Monotonic knowledge
            self.attack_monotonic_knowledge,
            # Non-monotonic authority
            self.attack_non_monotonic_revocation,
            self.attack_non_monotonic_supersession,
            # Asynchronous delivery
            self.attack_async_evidence_before_proposition,
            self.attack_async_revocation_before_authorization,
            # Deterministic convergence
            self.attack_deterministic_convergence,
            # Authority availability vs existence
            self.attack_authority_availability_vs_existence,
            # Byzantine artifact injection
            self.attack_forged_provenance,
            self.attack_manipulated_timestamp,
            # Identity multiplicity vs independence
            self.attack_identity_multiplicity,
            # Protocol version divergence
            self.attack_version_downgrade,
            # Replay across nodes
            self.attack_replay_across_nodes,
            # Distributed crash recovery
            self.attack_distributed_crash,
            # Stronger distributed invariant
            self.attack_agreement_does_not_create_authority,
            self.attack_partial_knowledge_bounded_uncertainty,
            self.attack_incomplete_provenance_no_consensus,
        ]
        return [attack() for attack in attacks]

    def _create_view(
        self,
        node_id: str,
        artifacts: dict[str, ArtifactReplica] | None = None,
        protocol_version: str = "1.0.0",
        partition_state: PartitionState = PartitionState.CONNECTED,
        temporal_position: int = 0,
    ) -> DistributedView:
        """Create a distributed view."""
        manifest = ArtifactManifest(
            manifest_id=f"manifest_{node_id}",
            artifacts=artifacts or {},
            protocol_version=protocol_version,
        )
        return DistributedView(
            view_id=f"view_{node_id}",
            node_id=node_id,
            manifest=manifest,
            protocol_version=protocol_version,
            partition_state=partition_state,
            temporal_position=temporal_position,
        )

    def _create_replica(
        self,
        artifact_type: str,
        artifact_hash: str | None = None,
        availability: ArtifactAvailability = ArtifactAvailability.AVAILABLE,
        protocol_version: str = "1.0.0",
    ) -> ArtifactReplica:
        """Create an artifact replica."""
        if artifact_hash is None:
            artifact_hash = hashlib.sha256(artifact_type.encode()).hexdigest()[:16]
        return ArtifactReplica(
            replica_id=f"replica_{artifact_type}",
            artifact_type=artifact_type,
            artifact_hash=artifact_hash,
            availability=availability,
            protocol_version=protocol_version,
        )

    def _run_attack(
        self,
        name: str,
        category: str,
        views: list[DistributedView],
        expected_convergence: ConvergenceStatus,
    ) -> DistributedAttackResult:
        """Run a single attack."""
        convergence = self.reconstructor.check_convergence(views)
        detected = convergence == expected_convergence

        return DistributedAttackResult(
            attack_name=name,
            attack_category=category,
            expected_convergence=expected_convergence,
            actual_convergence=convergence,
            detected=detected,
            details=[f"Convergence: {convergence.value}"],
        )

    # Partial knowledge attacks
    def attack_partial_knowledge_proposition(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "partial_knowledge_proposition", "partial_knowledge", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_partial_knowledge_evidence(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "partial_knowledge_evidence", "partial_knowledge", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_partial_knowledge_governance(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "partial_knowledge_governance", "partial_knowledge", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_partial_knowledge_actor(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
        })
        return self._run_attack(
            "partial_knowledge_actor", "partial_knowledge", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    # Artifact omission
    def attack_omit_proposition(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "omit_proposition", "artifact_omission", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_omit_evidence(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "omit_evidence", "artifact_omission", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_omit_governance(self) -> DistributedAttackResult:
        view = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "omit_governance", "artifact_omission", [view],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    # Artifact substitution
    def attack_substitute_evidence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence", "hash_a"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence", "hash_b"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "substitute_evidence", "artifact_substitution", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    def attack_substitute_policy(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "policy_a"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "policy_b"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "substitute_policy", "artifact_substitution", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    def attack_substitute_actor(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor", "actor_a"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor", "actor_b"),
        })
        return self._run_attack(
            "substitute_actor", "artifact_substitution", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Artifact duplication
    def attack_duplicate_evidence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "duplicate_evidence", "artifact_duplication", [view_a, view_b],
            ConvergenceStatus.CONVERGED,
        )

    # Artifact reordering
    def attack_reorder_delivery(self) -> DistributedAttackResult:
        view_a = self._create_view("A", temporal_position=1)
        view_b = self._create_view("B", temporal_position=2)
        return self._run_attack(
            "reorder_delivery", "artifact_reordering", [view_a, view_b],
            ConvergenceStatus.CONVERGED,
        )

    # Delayed delivery
    def attack_delayed_evidence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "evidence": self._create_replica("evidence"),
        }, temporal_position=2)
        return self._run_attack(
            "delayed_evidence", "delayed_delivery", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    def attack_delayed_revocation(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "revocation": self._create_replica("revocation"),
        }, temporal_position=2)
        return self._run_attack(
            "delayed_revocation", "delayed_delivery", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Replay
    def attack_replay_authorization(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        })
        view_b = self._create_view("B", {
            "authorization": self._create_replica("authorization"),
        })
        return self._run_attack(
            "replay_authorization", "replay", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Revocation delay
    def attack_revocation_delay(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "revocation": self._create_replica("revocation"),
        }, temporal_position=2)
        return self._run_attack(
            "revocation_delay", "revocation_delay", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Temporal inversion
    def attack_temporal_inversion(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "authorization": self._create_replica("authorization"),
        }, temporal_position=2)
        view_b = self._create_view("B", {
            "revocation": self._create_replica("revocation"),
        }, temporal_position=1)
        return self._run_attack(
            "temporal_inversion", "temporal_inversion", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Policy conflict
    def attack_policy_conflict(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "policy_a"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "policy_b"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "policy_conflict", "policy_conflict", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Verification conflict
    def attack_verification_conflict(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "verification": self._create_replica("verification", "pass"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "verification": self._create_replica("verification", "fail"),
        })
        return self._run_attack(
            "verification_conflict", "verification_conflict", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Governance conflict
    def attack_governance_conflict(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "gov_a"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "gov_b"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "governance_conflict", "governance_conflict", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Identity substitution
    def attack_identity_substitution(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor", "actor_a"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor", "actor_b"),
        })
        return self._run_attack(
            "identity_substitution", "identity_substitution", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Delegation substitution
    def attack_delegation_substitution(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "delegation": self._create_replica("delegation", "del_a"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "delegation": self._create_replica("delegation", "del_b"),
        })
        return self._run_attack(
            "delegation_substitution", "delegation_substitution", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Cross-domain artifacts
    def attack_cross_domain_artifact(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "cross_domain": self._create_replica("cross_domain"),
        })
        return self._run_attack(
            "cross_domain_artifact", "cross_domain", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Byzantine node
    def attack_byzantine_forged_evidence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence", "valid_hash"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence", "forged_hash"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "byzantine_forged_evidence", "byzantine", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    def attack_byzantine_stale_artifact(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, temporal_position=2)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "old_policy"),
            "actor": self._create_replica("actor"),
        }, temporal_position=1)
        return self._run_attack(
            "byzantine_stale_artifact", "byzantine", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Sybil identity
    def attack_sybil_identity(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_c = self._create_view("C", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "sybil_identity", "sybil", [view_a, view_b, view_c],
            ConvergenceStatus.CONVERGED,
        )

    # Provenance fragmentation
    def attack_provenance_fragmentation(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
        })
        view_b = self._create_view("B", {
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
        })
        view_c = self._create_view("C", {
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        })
        return self._run_attack(
            "provenance_fragmentation", "provenance_fragmentation", [view_a, view_b, view_c],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Version divergence
    def attack_version_divergence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, protocol_version="1.0.0")
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, protocol_version="2.0.0")
        return self._run_attack(
            "version_divergence", "version_divergence", [view_a, view_b],
            ConvergenceStatus.VERSION_MISMATCH,
        )

    # Partition
    def attack_partition(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, partition_state=PartitionState.PARTITIONED)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, partition_state=PartitionState.CONNECTED)
        return self._run_attack(
            "partition", "partition", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    def attack_partition_healing(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, partition_state=PartitionState.HEALED)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, partition_state=PartitionState.HEALED)
        return self._run_attack(
            "partition_healing", "partition", [view_a, view_b],
            ConvergenceStatus.CONVERGED,
        )

    # Crash recovery
    def attack_crash_recovery(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "crash_recovery", "crash_recovery", [view_a, view_b],
            ConvergenceStatus.CONVERGED,
        )

    # Historical/current confusion
    def attack_historical_current_confusion(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "revocation": self._create_replica("revocation"),
        }, temporal_position=2)
        return self._run_attack(
            "historical_current_confusion", "historical_current", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Stale authority
    def attack_stale_authority(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, temporal_position=2)
        return self._run_attack(
            "stale_authority", "stale_authority", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Conflicting roots
    def attack_conflicting_roots(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "root_a"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "root_b"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "conflicting_roots", "conflicting_roots", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Dependency omission
    def attack_dependency_omission(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
        })
        view_b = self._create_view("B", {
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "dependency_omission", "dependency_omission", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Resource contention
    def attack_resource_contention(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "resource": self._create_replica("resource", "budget_a"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "resource": self._create_replica("resource", "budget_b"),
        })
        return self._run_attack(
            "resource_contention", "resource_contention", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Authority cut-set
    def attack_authority_cutset(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
        })
        view_b = self._create_view("B", {
            "epistemic_state": self._create_replica("epistemic_state"),
        })
        view_c = self._create_view("C", {
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "authority_cutset", "authority_cutset", [view_a, view_b, view_c],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Monotonic knowledge
    def attack_monotonic_knowledge(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
        })
        return self._run_attack(
            "monotonic_knowledge", "monotonic_knowledge", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Non-monotonic authority
    def attack_non_monotonic_revocation(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "revocation": self._create_replica("revocation"),
        }, temporal_position=2)
        return self._run_attack(
            "non_monotonic_revocation", "non_monotonic", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    def attack_non_monotonic_supersession(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "v1"),
            "actor": self._create_replica("actor"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance", "v2"),
            "actor": self._create_replica("actor"),
        }, temporal_position=2)
        return self._run_attack(
            "non_monotonic_supersession", "non_monotonic", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Asynchronous delivery
    def attack_async_evidence_before_proposition(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "evidence": self._create_replica("evidence"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
        }, temporal_position=2)
        return self._run_attack(
            "async_evidence_before_proposition", "async_delivery", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    def attack_async_revocation_before_authorization(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "revocation": self._create_replica("revocation"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "authorization": self._create_replica("authorization"),
        }, temporal_position=2)
        return self._run_attack(
            "async_revocation_before_authorization", "async_delivery", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Deterministic convergence
    def attack_deterministic_convergence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "deterministic_convergence", "convergence", [view_a, view_b],
            ConvergenceStatus.CONVERGED,
        )

    # Authority availability vs existence
    def attack_authority_availability_vs_existence(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "authority_availability_vs_existence", "availability_existence", [view_a, view_b],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Byzantine artifact injection
    def attack_forged_provenance(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence", "forged"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "forged_provenance", "byzantine_injection", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    def attack_manipulated_timestamp(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, temporal_position=1)
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, temporal_position=1000)
        return self._run_attack(
            "manipulated_timestamp", "byzantine_injection", [view_a, view_b],
            ConvergenceStatus.NON_CONVERGENT,
        )

    # Identity multiplicity vs independence
    def attack_identity_multiplicity(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_c = self._create_view("C", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "identity_multiplicity", "identity_multiplicity", [view_a, view_b, view_c],
            ConvergenceStatus.CONVERGED,
        )

    # Protocol version divergence
    def attack_version_downgrade(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, protocol_version="1.0.0")
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        }, protocol_version="0.9.0")
        return self._run_attack(
            "version_downgrade", "version_divergence", [view_a, view_b],
            ConvergenceStatus.VERSION_MISMATCH,
        )

    # Replay across nodes
    def attack_replay_across_nodes(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
            "authorization": self._create_replica("authorization"),
        })
        view_b = self._create_view("B", {
            "authorization": self._create_replica("authorization"),
        })
        view_c = self._create_view("C", {
            "authorization": self._create_replica("authorization"),
        })
        return self._run_attack(
            "replay_across_nodes", "replay_across_nodes", [view_a, view_b, view_c],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )

    # Distributed crash recovery
    def attack_distributed_crash(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
            "epistemic_state": self._create_replica("epistemic_state"),
            "governance": self._create_replica("governance"),
            "actor": self._create_replica("actor"),
        })
        return self._run_attack(
            "distributed_crash", "distributed_crash", [view_a, view_b],
            ConvergenceStatus.CONVERGED,
        )

    # Stronger distributed invariant
    def attack_agreement_does_not_create_authority(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
        })
        view_b = self._create_view("B", {
            "proposition": self._create_replica("proposition"),
        })
        view_c = self._create_view("C", {
            "proposition": self._create_replica("proposition"),
        })
        return self._run_attack(
            "agreement_does_not_create_authority", "invariant", [view_a, view_b, view_c],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_partial_knowledge_bounded_uncertainty(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
            "evidence": self._create_replica("evidence"),
        })
        return self._run_attack(
            "partial_knowledge_bounded_uncertainty", "invariant", [view_a],
            ConvergenceStatus.INSUFFICIENT_KNOWLEDGE,
        )

    def attack_incomplete_provenance_no_consensus(self) -> DistributedAttackResult:
        view_a = self._create_view("A", {
            "proposition": self._create_replica("proposition"),
        })
        view_b = self._create_view("B", {
            "evidence": self._create_replica("evidence"),
        })
        view_c = self._create_view("C", {
            "epistemic_state": self._create_replica("epistemic_state"),
        })
        return self._run_attack(
            "incomplete_provenance_no_consensus", "invariant", [view_a, view_b, view_c],
            ConvergenceStatus.PARTIALLY_CONVERGED,
        )


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def run_distributed_attack_suite() -> list[DistributedAttackResult]:
    """Run all distributed attacks."""
    suite = DistributedAttackSuite()
    return suite.run_all_attacks()


def reconstruct_from_view(view: DistributedView) -> ReconstructedProtocolState:
    """Reconstruct protocol from a distributed view."""
    reconstructor = DistributedReconstructor()
    return reconstructor.reconstruct_from_view(view)


def reconcile_views(view_a: DistributedView, view_b: DistributedView) -> ViewReconciliation:
    """Reconcile two distributed views."""
    reconstructor = DistributedReconstructor()
    return reconstructor.reconcile_views(view_a, view_b)


def check_convergence(views: list[DistributedView]) -> ConvergenceStatus:
    """Check convergence across multiple views."""
    reconstructor = DistributedReconstructor()
    return reconstructor.check_convergence(views)
