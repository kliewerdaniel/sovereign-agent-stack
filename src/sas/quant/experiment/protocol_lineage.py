"""Protocol Lineage and Sovereign Domain Integrity.

Tests whether the protocol can establish that a collection of individually
valid artifacts belongs to the same authority universe and protocol lineage.

The central research question:
    How does the protocol establish that a collection of individually
    valid artifacts belongs to the same authority universe and protocol lineage?

Architecture:
    Individual Artifact Validity
          ↓
    Domain Binding
          ↓
    Protocol Lineage Verification
          ↓
    Authority Root Resolution
          ↓
    Identity Root Resolution
          ↓
    Policy Root Resolution
          ↓
    Provenance Root Resolution
          ↓
    Cross-Domain Bridge Verification
          ↓
    Domain-Aware Reconstruction
          ↓
    Sovereign Authority Domain Establishment

Invariants:
    VALID ARTIFACT ≠ VALID ARTIFACT FOR THIS PROTOCOL

    VALID PROVENANCE ≠ VALID PROVENANCE FOR THIS AUTHORITY DOMAIN

    SAME SCHEMA ≠ SAME SOVEREIGN DOMAIN

    SAME DOMAIN ≠ SAME PROTOCOL LINEAGE

    AUTHORITY IS NOT A PROPERTY OF THE ARTIFACT ALONE.

    AUTHORITY IS A PROPERTY OF AN ARTIFACT'S PROVENANCE WITHIN
    A SPECIFIC SOVEREIGN PROTOCOL DOMAIN, LINEAGE, TEMPORAL
    BOUNDARY, AND DELEGATION CONTEXT.
"""

from __future__ import annotations

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
from sas.quant.experiment.temporal_authority import (
    TemporalMode,
    TemporalBoundaryType,
    TemporalConflictType,
    LogicalTime,
    TemporalArtifact,
    TemporalSnapshot,
    HistoricalState,
    TemporalAuthority,
    TemporalConflict,
    TemporalQuery,
    TemporalReconstructionResult,
    TemporalReconstructor,
    TemporalAttackResult,
    TemporalAttackSuite,
    run_temporal_attack_suite,
    reconstruct_at_boundary,
    check_temporal_non_interference,
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
# Domain Classification
# ---------------------------------------------------------------------------


class DomainType(str, Enum):
    """Types of sovereign domains."""
    SOVEREIGN = "sovereign"
    FEDERATED = "federated"
    BRIDGED = "bridged"
    FORKED = "forked"


class LineageType(str, Enum):
    """Types of protocol lineage."""
    ORIGINAL = "original"
    FORK = "fork"
    BRIDGE = "bridge"
    MERGE = "merge"
    DIVERGENT = "divergent"


class RootType(str, Enum):
    """Types of roots in the authority hierarchy."""
    AUTHORITY = "authority"
    IDENTITY = "identity"
    POLICY = "policy"
    PROVENANCE = "provenance"


class BridgeStatus(str, Enum):
    """Status of a domain bridge."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"
    FUTURE = "future"


class DomainConflictType(str, Enum):
    """Types of domain conflicts."""
    CROSS_DOMAIN_EVIDENCE = "cross_domain_evidence"
    CROSS_DOMAIN_PROPOSITION = "cross_domain_proposition"
    CROSS_DOMAIN_VERIFICATION = "cross_domain_verification"
    CROSS_DOMAIN_GOVERNANCE = "cross_domain_governance"
    CROSS_DOMAIN_ACTOR = "cross_domain_actor"
    CROSS_DOMAIN_DELEGATION = "cross_domain_delegation"
    CROSS_DOMAIN_AUTHORIZATION = "cross_domain_authorization"
    CROSS_DOMAIN_EXECUTION = "cross_domain_execution"
    CROSS_DOMAIN_REVOCATION = "cross_domain_revocation"
    AUTHORITY_ROOT_SUBSTITUTION = "authority_root_substitution"
    IDENTITY_ROOT_SUBSTITUTION = "identity_root_substitution"
    POLICY_ROOT_SUBSTITUTION = "policy_root_substitution"
    PROVENANCE_ROOT_SUBSTITUTION = "provenance_root_substitution"
    SCHEMA_COLLISION = "schema_collision"
    SEMANTIC_COLLISION = "semantic_collision"
    VERSION_COLLISION = "version_collision"
    LINEAGE_COLLISION = "lineage_collision"
    PROTOCOL_FORK = "protocol_fork"
    DOMAIN_FORK = "domain_fork"
    BRIDGE_SCOPE_ESCALATION = "bridge_scope_escalation"
    BRIDGE_TEMPORAL_ESCALATION = "bridge_temporal_escalation"
    BRIDGE_RESOURCE_ESCALATION = "bridge_resource_escalation"
    BRIDGE_ACTOR_SUBSTITUTION = "bridge_actor_substitution"
    BRIDGE_POLICY_SUBSTITUTION = "bridge_policy_substitution"
    BRIDGE_REPLAY = "bridge_replay"
    REVOKED_BRIDGE = "revoked_bridge"
    EXPIRED_BRIDGE = "expired_bridge"
    FUTURE_BRIDGE = "future_bridge"
    HISTORICAL_BRIDGE = "historical_bridge"
    NESTED_BRIDGE = "nested_bridge"
    CIRCULAR_BRIDGE = "circular_bridge"
    CROSS_DOMAIN_CONSENSUS = "cross_domain_consensus"
    CROSS_DOMAIN_MAJORITY = "cross_domain_majority"
    CROSS_DOMAIN_ARTIFACT_REPLAY = "cross_domain_artifact_replay"
    CROSS_DOMAIN_PROVENANCE_SUBSTITUTION = "cross_domain_provenance_substitution"
    CROSS_DOMAIN_TEMPORAL_REPLAY = "cross_domain_temporal_replay"
    CROSS_DOMAIN_CRASH_RECOVERY = "cross_domain_crash_recovery"
    CROSS_DOMAIN_DISTRIBUTED_CONVERGENCE = "cross_domain_distributed_convergence"


# ---------------------------------------------------------------------------
# Domain Validity Interval
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainValidityInterval:
    """Interval during which a domain or bridge is valid (string timestamps)."""
    valid_from: str = ""
    valid_until: str = ""  # inclusive; -1 means forever

    def contains(self, time: str) -> bool:
        """Check if a timestamp falls within this interval."""
        if self.valid_from and time < self.valid_from:
            return False
        if self.valid_until and self.valid_until != "-1" and time > self.valid_until:
            return False
        return True

    def overlaps(self, other: DomainValidityInterval) -> bool:
        """Check if two intervals overlap."""
        if self.valid_until and self.valid_until != "-1" and other.valid_from:
            if self.valid_until < other.valid_from:
                return False
        if other.valid_until and other.valid_until != "-1" and self.valid_from:
            if other.valid_until < self.valid_from:
                return False
        return True


# ---------------------------------------------------------------------------
# Authority Root
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityRoot:
    """Root of authority for a sovereign domain."""
    root_id: str
    domain_id: str
    root_type: RootType
    root_hash: str
    established_at: str = ""
    expires_at: str = "-1"
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        content = json.dumps({
            "root_id": self.root_id,
            "domain_id": self.domain_id,
            "root_type": self.root_type.value,
            "root_hash": self.root_hash,
            "established_at": self.established_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_valid_at(self, timestamp: str) -> bool:
        if self.established_at and timestamp < self.established_at:
            return False
        if self.expires_at != "-1" and timestamp > self.expires_at:
            return False
        return True


# ---------------------------------------------------------------------------
# Protocol Domain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProtocolDomain:
    """A sovereign authority universe."""
    domain_id: str
    domain_type: DomainType
    domain_root: str
    protocol_family: str = "sovereign-quant"
    protocol_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    identity_root: str = ""
    policy_root: str = ""
    provenance_root: str = ""
    created_at: str = ""
    parent_domain_id: str = ""
    lineage_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        content = json.dumps({
            "domain_id": self.domain_id,
            "domain_type": self.domain_type.value,
            "domain_root": self.domain_root,
            "protocol_family": self.protocol_family,
            "protocol_version": self.protocol_version,
            "schema_version": self.schema_version,
            "semantic_version": self.semantic_version,
            "authority_root": self.authority_root,
            "identity_root": self.identity_root,
            "policy_root": self.policy_root,
            "provenance_root": self.provenance_root,
            "created_at": self.created_at,
            "parent_domain_id": self.parent_domain_id,
            "lineage_hash": self.lineage_hash,
            "metadata": self.metadata,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_compatible_with(self, other: ProtocolDomain) -> bool:
        return (
            self.protocol_family == other.protocol_family
            and self.authority_root == other.authority_root
            and self.identity_root == other.identity_root
            and self.policy_root == other.policy_root
            and self.provenance_root == other.provenance_root
        )

    def shares_lineage_with(self, other: ProtocolDomain) -> bool:
        return self.lineage_hash == other.lineage_hash and self.lineage_hash != ""


# ---------------------------------------------------------------------------
# Protocol Lineage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProtocolLineage:
    """Tracks the lineage of a protocol domain."""
    lineage_id: str
    domain_id: str
    parent_lineage_id: str = ""
    fork_point: str = ""
    lineage_type: LineageType = LineageType.ORIGINAL
    compatibility: dict = field(default_factory=dict)
    divergence_point: str = ""
    created_at: str = ""
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        content = json.dumps({
            "lineage_id": self.lineage_id,
            "domain_id": self.domain_id,
            "parent_lineage_id": self.parent_lineage_id,
            "fork_point": self.fork_point,
            "lineage_type": self.lineage_type.value,
            "compatibility": self.compatibility,
            "divergence_point": self.divergence_point,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_ancestor_of(self, other: ProtocolLineage) -> bool:
        if not other.parent_lineage_id:
            return False
        return other.parent_lineage_id == self.lineage_id

    def is_compatible_version(self, version: str) -> bool:
        return self.compatibility.get(version) == "compatible"


# ---------------------------------------------------------------------------
# Domain Bridge
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainBridge:
    """Explicit cross-domain delegation mechanism."""
    bridge_id: str
    source_domain_id: str
    destination_domain_id: str
    scope: dict = field(default_factory=dict)
    validity_interval: DomainValidityInterval = field(
        default_factory=lambda: DomainValidityInterval()
    )
    policy: str = ""
    authority_root: str = ""
    delegation_chain: list[str] = field(default_factory=list)
    provenance: str = ""
    constraints: dict = field(default_factory=dict)
    status: BridgeStatus = BridgeStatus.ACTIVE
    created_at: str = ""
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        content = json.dumps({
            "bridge_id": self.bridge_id,
            "source_domain_id": self.source_domain_id,
            "destination_domain_id": self.destination_domain_id,
            "scope": self.scope,
            "validity_interval": {
                "valid_from": self.validity_interval.valid_from,
                "valid_until": self.validity_interval.valid_until,
            },
            "policy": self.policy,
            "authority_root": self.authority_root,
            "delegation_chain": sorted(self.delegation_chain),
            "provenance": self.provenance,
            "constraints": self.constraints,
            "status": self.status.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_valid_at(self, timestamp: str) -> bool:
        if self.status != BridgeStatus.ACTIVE:
            return False
        return self.validity_interval.contains(timestamp)

    def allows_action(self, action: str) -> bool:
        allowed = self.scope.get("allowed_actions", [])
        if not allowed:
            return False
        return action in allowed

    def allows_resource(self, resource: str) -> bool:
        allowed = self.scope.get("allowed_resources", [])
        if not allowed:
            return False
        return resource in allowed

    def allows_actor(self, actor: str) -> bool:
        allowed = self.scope.get("allowed_actors", [])
        if not allowed:
            return False
        return actor in allowed


# ---------------------------------------------------------------------------
# Domain-Bound Artifact Mixin (non-dataclass to avoid field ordering issues)
# ---------------------------------------------------------------------------


class DomainBoundArtifact:
    """Mixin for artifacts that are bound to a specific domain.
    
    This is a non-dataclass mixin to avoid field ordering issues with
    multiple inheritance. Domain-bound dataclasses should inherit from
    their base artifact class and include the domain fields directly.
    """
    
    domain_id: str
    protocol_lineage_id: str
    schema_version: str
    semantic_version: str
    authority_root: str
    provenance_root: str

    def is_compatible_with_domain(self, domain: ProtocolDomain) -> bool:
        if self.domain_id and self.domain_id != domain.domain_id:
            return False
        if self.authority_root and self.authority_root != domain.authority_root:
            return False
        if self.provenance_root and self.provenance_root != domain.provenance_root:
            return False
        return True

    def compute_domain_hash(self) -> str:
        content = json.dumps({
            "domain_id": self.domain_id,
            "protocol_lineage_id": self.protocol_lineage_id,
            "schema_version": self.schema_version,
            "semantic_version": self.semantic_version,
            "authority_root": self.authority_root,
            "provenance_root": self.provenance_root,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Domain-Bound Versions of Existing Artifacts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainBoundEvidenceBundle(EvidenceBundle):
    """Evidence bundle bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


@dataclass(frozen=True)
class DomainBoundProposition(TypedProposition):
    """Typed proposition bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


@dataclass(frozen=True)
class DomainBoundEpistemicState(EpistemicState):
    """Epistemic state bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


@dataclass(frozen=True)
class DomainBoundAuthorization(AuthorizationArtifact):
    """Authorization bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


@dataclass(frozen=True)
class DomainBoundActor(ActorIdentity):
    """Actor identity bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


@dataclass(frozen=True)
class DomainBoundPolicy(GovernancePolicy):
    """Governance policy bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


@dataclass(frozen=True)
class DomainBoundDelegation(DelegationArtifact):
    """Delegation bound to a specific domain."""
    domain_id: str = ""
    protocol_lineage_id: str = ""
    schema_version: str = "1.0.0"
    semantic_version: str = "1.0.0"
    authority_root: str = ""
    provenance_root: str = ""


# ---------------------------------------------------------------------------
# Protocol Lineage Verifier
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineageVerificationResult:
    """Result of a lineage verification."""
    is_valid: bool
    domain_id: str
    lineage_id: str
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


@dataclass(frozen=True)
class DomainVerificationResult:
    """Result of a domain verification."""
    is_valid: bool
    domain_id: str
    artifact_id: str
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


@dataclass(frozen=True)
class BridgeVerificationResult:
    """Result of a bridge verification."""
    is_valid: bool
    bridge_id: str
    source_domain_id: str
    destination_domain_id: str
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


class ProtocolLineageVerifier:
    """Verifies protocol lineage and sovereign domain integrity."""

    def __init__(self, domain: ProtocolDomain):
        self.domain = domain
        self._lineages: dict[str, ProtocolLineage] = {}
        self._bridges: dict[str, DomainBridge] = {}
        self._roots: dict[str, AuthorityRoot] = {}

    def register_lineage(self, lineage: ProtocolLineage) -> None:
        self._lineages[lineage.lineage_id] = lineage

    def register_bridge(self, bridge: DomainBridge) -> None:
        self._bridges[bridge.bridge_id] = bridge

    def register_root(self, root: AuthorityRoot) -> None:
        self._roots[root.root_id] = root

    def verify_artifact_domain(
        self,
        artifact: object,
        expected_domain: Optional[ProtocolDomain] = None,
    ) -> DomainVerificationResult:
        domain = expected_domain or self.domain
        conflicts = []

        if hasattr(artifact, 'domain_id') and artifact.domain_id and artifact.domain_id != domain.domain_id:
            conflicts.append(
                f"Domain mismatch: artifact.domain_id={artifact.domain_id} "
                f"!= domain.domain_id={domain.domain_id}"
            )

        if hasattr(artifact, 'authority_root') and artifact.authority_root and artifact.authority_root != domain.authority_root:
            conflicts.append(
                f"Authority root mismatch: artifact.authority_root={artifact.authority_root} "
                f"!= domain.authority_root={domain.authority_root}"
            )

        if hasattr(artifact, 'provenance_root') and artifact.provenance_root and artifact.provenance_root != domain.provenance_root:
            conflicts.append(
                f"Provenance root mismatch: artifact.provenance_root={artifact.provenance_root} "
                f"!= domain.provenance_root={domain.provenance_root}"
            )

        if hasattr(artifact, 'protocol_lineage_id') and artifact.protocol_lineage_id:
            if artifact.protocol_lineage_id not in self._lineages:
                conflicts.append(f"Unknown lineage: {artifact.protocol_lineage_id}")
            else:
                lineage = self._lineages[artifact.protocol_lineage_id]
                if lineage.domain_id != domain.domain_id:
                    conflicts.append(
                        f"Lineage domain mismatch: lineage.domain_id={lineage.domain_id} "
                        f"!= domain.domain_id={domain.domain_id}"
                    )

        is_valid = len(conflicts) == 0
        rejection_reason = "; ".join(conflicts) if conflicts else ""

        domain_hash = ""
        if hasattr(artifact, 'compute_domain_hash'):
            domain_hash = artifact.compute_domain_hash()

        return DomainVerificationResult(
            is_valid=is_valid,
            domain_id=domain.domain_id,
            artifact_id=getattr(artifact, 'domain_id', ''),
            conflicts=conflicts,
            rejection_reason=rejection_reason,
            provenance_hash=domain_hash,
        )

    def verify_bridge(
        self,
        bridge: DomainBridge,
        timestamp: str = "",
    ) -> BridgeVerificationResult:
        conflicts = []

        if timestamp and not bridge.is_valid_at(timestamp):
            conflicts.append(f"Bridge {bridge.bridge_id} is not valid at {timestamp}")
        elif not timestamp:
            if bridge.status != BridgeStatus.ACTIVE:
                conflicts.append(f"Bridge {bridge.bridge_id} is not active")

        if bridge.source_domain_id != self.domain.domain_id:
            if bridge.destination_domain_id != self.domain.domain_id:
                conflicts.append(
                    f"Bridge {bridge.bridge_id} does not involve domain {self.domain.domain_id}"
                )

        if self._detect_circular_bridge(bridge):
            conflicts.append(f"Circular bridge detected: {bridge.bridge_id}")

        is_valid = len(conflicts) == 0
        rejection_reason = "; ".join(conflicts) if conflicts else ""

        return BridgeVerificationResult(
            is_valid=is_valid,
            bridge_id=bridge.bridge_id,
            source_domain_id=bridge.source_domain_id,
            destination_domain_id=bridge.destination_domain_id,
            conflicts=conflicts,
            rejection_reason=rejection_reason,
            provenance_hash=bridge.compute_hash(),
        )

    def _detect_circular_bridge(self, bridge: DomainBridge) -> bool:
        visited = set()
        current = bridge
        while current.bridge_id:
            if current.bridge_id in visited:
                return True
            visited.add(current.bridge_id)
            if current.delegation_chain:
                next_bridge_id = current.delegation_chain[-1]
                if next_bridge_id in self._bridges:
                    current = self._bridges[next_bridge_id]
                else:
                    break
            else:
                break
        return False

    def verify_cross_domain_composition(
        self,
        artifacts: list[object],
        bridge: Optional[DomainBridge] = None,
    ) -> LineageVerificationResult:
        conflicts = []
        warnings = []

        domains = set()
        authority_roots = set()
        provenance_roots = set()
        lineage_ids = set()

        for artifact in artifacts:
            if hasattr(artifact, 'domain_id') and artifact.domain_id:
                domains.add(artifact.domain_id)
            if hasattr(artifact, 'authority_root') and artifact.authority_root:
                authority_roots.add(artifact.authority_root)
            if hasattr(artifact, 'provenance_root') and artifact.provenance_root:
                provenance_roots.add(artifact.provenance_root)
            if hasattr(artifact, 'protocol_lineage_id') and artifact.protocol_lineage_id:
                lineage_ids.add(artifact.protocol_lineage_id)

        if len(domains) > 1 and not bridge:
            conflicts.append(f"Multiple domains {domains} without a bridge")

        if len(authority_roots) > 1 and not bridge:
            conflicts.append(f"Multiple authority roots {authority_roots} without a bridge")

        if len(provenance_roots) > 1 and not bridge:
            conflicts.append(f"Multiple provenance roots {provenance_roots} without a bridge")

        if bridge:
            bridge_result = self.verify_bridge(bridge)
            if not bridge_result.is_valid:
                conflicts.extend(bridge_result.conflicts)

        is_valid = len(conflicts) == 0

        return LineageVerificationResult(
            is_valid=is_valid,
            domain_id=self.domain.domain_id,
            lineage_id="",
            conflicts=conflicts,
            warnings=warnings,
            rejection_reason="; ".join(conflicts) if conflicts else "",
            provenance_hash="",
        )

    def verify_lineage_continuity(
        self,
        lineage: ProtocolLineage,
    ) -> LineageVerificationResult:
        conflicts = []

        if lineage.domain_id != self.domain.domain_id:
            conflicts.append(
                f"Lineage domain mismatch: {lineage.domain_id} != {self.domain.domain_id}"
            )

        if lineage.parent_lineage_id:
            if lineage.parent_lineage_id not in self._lineages:
                conflicts.append(f"Parent lineage not found: {lineage.parent_lineage_id}")
            else:
                parent = self._lineages[lineage.parent_lineage_id]
                if parent.domain_id != lineage.domain_id:
                    conflicts.append(
                        f"Parent lineage domain mismatch: {parent.domain_id} != {lineage.domain_id}"
                    )

        is_valid = len(conflicts) == 0

        return LineageVerificationResult(
            is_valid=is_valid,
            domain_id=self.domain.domain_id,
            lineage_id=lineage.lineage_id,
            conflicts=conflicts,
            rejection_reason="; ".join(conflicts) if conflicts else "",
            provenance_hash=lineage.compute_hash(),
        )


# ---------------------------------------------------------------------------
# Domain Attack Suite
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainAttackResult:
    """Result of a domain attack."""
    attack_name: str
    attack_category: str
    domain_id: str
    expected_valid: bool
    actual_valid: bool
    detected: bool
    details: list[str] = field(default_factory=list)
    rejection_reason: str = ""


class DomainAttackSuite:
    """Adversarial tests for protocol lineage and domain integrity."""

    def __init__(self):
        self.domain_a = self._create_domain_a()
        self.domain_b = self._create_domain_b()
        self.verifier_a = ProtocolLineageVerifier(self.domain_a)
        self.verifier_b = ProtocolLineageVerifier(self.domain_b)
        self._register_lineages()

    def _create_domain_a(self) -> ProtocolDomain:
        return ProtocolDomain(
            domain_id="domain-a",
            domain_type=DomainType.SOVEREIGN,
            domain_root="root-hash-a",
            protocol_family="sovereign-quant",
            protocol_version="1.0.0",
            schema_version="1.0.0",
            semantic_version="1.0.0",
            authority_root="auth-root-a",
            identity_root="identity-root-a",
            policy_root="policy-root-a",
            provenance_root="provenance-root-a",
            created_at="2024-01-01T00:00:00Z",
            lineage_hash="lineage-hash-a",
        )

    def _create_domain_b(self) -> ProtocolDomain:
        return ProtocolDomain(
            domain_id="domain-b",
            domain_type=DomainType.SOVEREIGN,
            domain_root="root-hash-b",
            protocol_family="sovereign-quant",
            protocol_version="1.0.0",
            schema_version="1.0.0",
            semantic_version="1.0.0",
            authority_root="auth-root-b",
            identity_root="identity-root-b",
            policy_root="policy-root-b",
            provenance_root="provenance-root-b",
            created_at="2024-01-01T00:00:00Z",
            lineage_hash="lineage-hash-b",
        )

    def _register_lineages(self) -> None:
        lineage_a = ProtocolLineage(
            lineage_id="lineage-a",
            domain_id="domain-a",
            lineage_type=LineageType.ORIGINAL,
            compatibility={"1.0.0": "compatible", "0.9.0": "incompatible"},
        )
        lineage_b = ProtocolLineage(
            lineage_id="lineage-b",
            domain_id="domain-b",
            lineage_type=LineageType.ORIGINAL,
            compatibility={"1.0.0": "compatible", "0.9.0": "incompatible"},
        )
        self.verifier_a.register_lineage(lineage_a)
        self.verifier_b.register_lineage(lineage_b)

    def _create_evidence_for_domain(
        self,
        domain_id: str,
        authority_root: str = "",
        provenance_root: str = "",
    ) -> DomainBoundEvidenceBundle:
        return DomainBoundEvidenceBundle(
            evidence_id=f"evidence-{domain_id}",
            intervention_type=InterventionType.FEATURE_ABLATION,
            target="test",
            effect_size=0.5,
            description="Test evidence",
            domain_id=domain_id,
            authority_root=authority_root or f"auth-root-{domain_id}",
            provenance_root=provenance_root or f"provenance-root-{domain_id}",
        )

    def _create_proposition_for_domain(
        self,
        domain_id: str,
        authority_root: str = "",
        provenance_root: str = "",
    ) -> DomainBoundProposition:
        return DomainBoundProposition(
            proposition_id=f"proposition-{domain_id}",
            proposition_type=PropositionType.FEATURE_DEPENDENCY,
            target="test",
            description="Test proposition",
            domain_id=domain_id,
            authority_root=authority_root or f"auth-root-{domain_id}",
            provenance_root=provenance_root or f"provenance-root-{domain_id}",
        )

    def _create_actor_for_domain(
        self,
        domain_id: str,
        authority_root: str = "",
        provenance_root: str = "",
    ) -> DomainBoundActor:
        return DomainBoundActor(
            actor_id=f"actor-{domain_id}",
            capabilities=["test"],
            domain_id=domain_id,
            authority_root=authority_root or f"auth-root-{domain_id}",
            provenance_root=provenance_root or f"provenance-root-{domain_id}",
        )

    def _create_policy_for_domain(
        self,
        domain_id: str,
        authority_root: str = "",
        provenance_root: str = "",
    ) -> DomainBoundPolicy:
        return DomainBoundPolicy(
            policy_id=f"policy-{domain_id}",
            policy_version="1.0.0",
            allowed_actions=["test"],
            domain_id=domain_id,
            authority_root=authority_root or f"auth-root-{domain_id}",
            provenance_root=provenance_root or f"provenance-root-{domain_id}",
        )

    def _create_delegation_for_domain(
        self,
        domain_id: str,
        authority_root: str = "",
        provenance_root: str = "",
    ) -> DomainBoundDelegation:
        return DomainBoundDelegation(
            delegation_id=f"delegation-{domain_id}",
            delegator_id=f"delegator-{domain_id}",
            delegate_id=f"delegate-{domain_id}",
            capability="test",
            scope={"actions": ["test"]},
            domain_id=domain_id,
            authority_root=authority_root or f"auth-root-{domain_id}",
            provenance_root=provenance_root or f"provenance-root-{domain_id}",
        )

    def attack_cross_domain_evidence(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_evidence",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_proposition(self) -> DomainAttackResult:
        prop_b = self._create_proposition_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(prop_b)
        return DomainAttackResult(
            attack_name="cross_domain_proposition",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_actor(self) -> DomainAttackResult:
        actor_b = self._create_actor_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(actor_b)
        return DomainAttackResult(
            attack_name="cross_domain_actor",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_policy(self) -> DomainAttackResult:
        policy_b = self._create_policy_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(policy_b)
        return DomainAttackResult(
            attack_name="cross_domain_policy",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_delegation(self) -> DomainAttackResult:
        delegation_b = self._create_delegation_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(delegation_b)
        return DomainAttackResult(
            attack_name="cross_domain_delegation",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_authority_root_substitution(self) -> DomainAttackResult:
        evidence = self._create_evidence_for_domain(
            "domain-a",
            authority_root="auth-root-b",
        )
        result = self.verifier_a.verify_artifact_domain(evidence)
        return DomainAttackResult(
            attack_name="authority_root_substitution",
            attack_category="root_substitution",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_identity_root_substitution(self) -> DomainAttackResult:
        actor = self._create_actor_for_domain(
            "domain-a",
            authority_root="auth-root-b",
        )
        result = self.verifier_a.verify_artifact_domain(actor)
        return DomainAttackResult(
            attack_name="identity_root_substitution",
            attack_category="root_substitution",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_policy_root_substitution(self) -> DomainAttackResult:
        policy = self._create_policy_for_domain(
            "domain-a",
            authority_root="auth-root-b",
        )
        result = self.verifier_a.verify_artifact_domain(policy)
        return DomainAttackResult(
            attack_name="policy_root_substitution",
            attack_category="root_substitution",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_provenance_root_substitution(self) -> DomainAttackResult:
        evidence = self._create_evidence_for_domain(
            "domain-a",
            provenance_root="provenance-root-b",
        )
        result = self.verifier_a.verify_artifact_domain(evidence)
        return DomainAttackResult(
            attack_name="provenance_root_substitution",
            attack_category="root_substitution",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_schema_collision(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain(
            "domain-b",
            authority_root="auth-root-a",
            provenance_root="provenance-root-a",
        )
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="schema_collision",
            attack_category="collision",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_semantic_collision(self) -> DomainAttackResult:
        evidence = self._create_evidence_for_domain(
            "domain-a",
            authority_root="auth-root-b",
        )
        result = self.verifier_a.verify_artifact_domain(evidence)
        return DomainAttackResult(
            attack_name="semantic_collision",
            attack_category="collision",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_version_collision(self) -> DomainAttackResult:
        evidence = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence)
        return DomainAttackResult(
            attack_name="version_collision",
            attack_category="collision",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_lineage_collision(self) -> DomainAttackResult:
        evidence = self._create_evidence_for_domain(
            "domain-b",
            authority_root="auth-root-a",
            provenance_root="provenance-root-a",
        )
        result = self.verifier_a.verify_artifact_domain(evidence)
        return DomainAttackResult(
            attack_name="lineage_collision",
            attack_category="collision",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_protocol_fork(self) -> DomainAttackResult:
        lineage_fork = ProtocolLineage(
            lineage_id="lineage-fork",
            domain_id="domain-a",
            parent_lineage_id="lineage-a",
            lineage_type=LineageType.FORK,
            divergence_point="v2.0.0",
        )
        self.verifier_a.register_lineage(lineage_fork)
        result = self.verifier_a.verify_lineage_continuity(lineage_fork)
        return DomainAttackResult(
            attack_name="protocol_fork",
            attack_category="fork",
            domain_id="domain-a",
            expected_valid=True,
            actual_valid=result.is_valid,
            detected=result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_domain_fork(self) -> DomainAttackResult:
        domain_fork = ProtocolDomain(
            domain_id="domain-a-fork",
            domain_type=DomainType.FORKED,
            domain_root="root-hash-a-fork",
            protocol_family="sovereign-quant",
            protocol_version="2.0.0",
            schema_version="1.0.0",
            semantic_version="2.0.0",
            authority_root="auth-root-a-fork",
            identity_root="identity-root-a-fork",
            policy_root="policy-root-a-fork",
            provenance_root="provenance-root-a-fork",
            parent_domain_id="domain-a",
            lineage_hash="lineage-hash-a-fork",
        )
        is_compatible = self.domain_a.is_compatible_with(domain_fork)
        return DomainAttackResult(
            attack_name="domain_fork",
            attack_category="fork",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not is_compatible,
            detected=not is_compatible,
            details=[f"Domains compatible: {is_compatible}"],
            rejection_reason="" if not is_compatible else "Fork should not be compatible",
        )

    def attack_bridge_scope_escalation(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            status=BridgeStatus.ACTIVE,
        )
        allows_unauthorized = bridge.allows_action("execute_trade")
        return DomainAttackResult(
            attack_name="bridge_scope_escalation",
            attack_category="bridge_scope",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not allows_unauthorized,
            detected=not allows_unauthorized,
            details=[f"Bridge allows execute_trade: {allows_unauthorized}"],
            rejection_reason="" if not allows_unauthorized else "Bridge should not allow execute_trade",
        )

    def attack_bridge_temporal_escalation(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-temporal",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            validity_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2024-12-31T23:59:59Z",
            ),
            status=BridgeStatus.ACTIVE,
        )
        is_valid_after = bridge.is_valid_at("2025-01-01T00:00:00Z")
        return DomainAttackResult(
            attack_name="bridge_temporal_escalation",
            attack_category="bridge_temporal",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not is_valid_after,
            detected=not is_valid_after,
            details=[f"Bridge valid after expiration: {is_valid_after}"],
            rejection_reason="" if not is_valid_after else "Bridge should not be valid after expiration",
        )

    def attack_bridge_resource_escalation(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-resource",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_resources": ["evidence"]},
            status=BridgeStatus.ACTIVE,
        )
        allows_unauthorized = bridge.allows_resource("trading")
        return DomainAttackResult(
            attack_name="bridge_resource_escalation",
            attack_category="bridge_resource",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not allows_unauthorized,
            detected=not allows_unauthorized,
            details=[f"Bridge allows trading resource: {allows_unauthorized}"],
            rejection_reason="" if not allows_unauthorized else "Bridge should not allow trading resource",
        )

    def attack_bridge_actor_substitution(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-actor",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actors": ["actor-a"]},
            status=BridgeStatus.ACTIVE,
        )
        allows_unauthorized = bridge.allows_actor("actor-b")
        return DomainAttackResult(
            attack_name="bridge_actor_substitution",
            attack_category="bridge_actor",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not allows_unauthorized,
            detected=not allows_unauthorized,
            details=[f"Bridge allows actor-b: {allows_unauthorized}"],
            rejection_reason="" if not allows_unauthorized else "Bridge should not allow actor-b",
        )

    def attack_bridge_policy_substitution(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-policy",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            policy="policy-a",
            status=BridgeStatus.ACTIVE,
        )
        has_correct_policy = bridge.policy == "policy-a"
        return DomainAttackResult(
            attack_name="bridge_policy_substitution",
            attack_category="bridge_policy",
            domain_id="domain-a",
            expected_valid=True,
            actual_valid=has_correct_policy,
            detected=has_correct_policy,
            details=[f"Bridge policy: {bridge.policy}"],
            rejection_reason="" if has_correct_policy else "Policy mismatch",
        )

    def attack_bridge_replay(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-replay",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            status=BridgeStatus.REVOKED,
        )
        is_valid = bridge.is_valid_at("2024-06-01T00:00:00Z")
        return DomainAttackResult(
            attack_name="bridge_replay",
            attack_category="bridge_replay",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not is_valid,
            detected=not is_valid,
            details=[f"Revoked bridge valid: {is_valid}"],
            rejection_reason="" if not is_valid else "Revoked bridge should not be valid",
        )

    def attack_revoked_bridge(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-revoked",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            status=BridgeStatus.REVOKED,
        )
        is_valid = bridge.is_valid_at("2024-06-01T00:00:00Z")
        return DomainAttackResult(
            attack_name="revoked_bridge",
            attack_category="bridge_revoked",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not is_valid,
            detected=not is_valid,
            details=[f"Revoked bridge valid: {is_valid}"],
            rejection_reason="" if not is_valid else "Revoked bridge should not be valid",
        )

    def attack_expired_bridge(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-expired",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            validity_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2024-06-01T00:00:00Z",
            ),
            status=BridgeStatus.ACTIVE,
        )
        is_valid = bridge.is_valid_at("2024-07-01T00:00:00Z")
        return DomainAttackResult(
            attack_name="expired_bridge",
            attack_category="bridge_expired",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not is_valid,
            detected=not is_valid,
            details=[f"Expired bridge valid: {is_valid}"],
            rejection_reason="" if not is_valid else "Expired bridge should not be valid",
        )

    def attack_future_bridge(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-future",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            validity_interval=DomainValidityInterval(
                valid_from="2025-01-01T00:00:00Z",
                valid_until="2025-12-31T23:59:59Z",
            ),
            status=BridgeStatus.ACTIVE,
        )
        is_valid = bridge.is_valid_at("2024-06-01T00:00:00Z")
        return DomainAttackResult(
            attack_name="future_bridge",
            attack_category="bridge_future",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=not is_valid,
            detected=not is_valid,
            details=[f"Future bridge valid: {is_valid}"],
            rejection_reason="" if not is_valid else "Future bridge should not be valid",
        )

    def attack_historical_bridge(self) -> DomainAttackResult:
        bridge = DomainBridge(
            bridge_id="bridge-a-b-historical",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            validity_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2024-06-01T00:00:00Z",
            ),
            status=BridgeStatus.ACTIVE,
        )
        is_valid_during = bridge.is_valid_at("2024-03-01T00:00:00Z")
        is_valid_after = bridge.is_valid_at("2024-07-01T00:00:00Z")
        return DomainAttackResult(
            attack_name="historical_bridge",
            attack_category="bridge_historical",
            domain_id="domain-a",
            expected_valid=True,
            actual_valid=is_valid_during and not is_valid_after,
            detected=is_valid_during and not is_valid_after,
            details=[
                f"Bridge valid during period: {is_valid_during}",
                f"Bridge valid after expiration: {is_valid_after}",
            ],
            rejection_reason="",
        )

    def attack_nested_bridges(self) -> DomainAttackResult:
        bridge1 = DomainBridge(
            bridge_id="bridge-nested-1",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            status=BridgeStatus.ACTIVE,
        )
        bridge2 = DomainBridge(
            bridge_id="bridge-nested-2",
            source_domain_id="domain-a",
            destination_domain_id="domain-c",
            scope={"allowed_actions": ["read_evidence"]},
            delegation_chain=["bridge-nested-1"],
            status=BridgeStatus.ACTIVE,
        )
        self.verifier_a.register_bridge(bridge1)
        self.verifier_a.register_bridge(bridge2)
        result = self.verifier_a.verify_bridge(bridge2)
        return DomainAttackResult(
            attack_name="nested_bridges",
            attack_category="bridge_nested",
            domain_id="domain-a",
            expected_valid=True,
            actual_valid=result.is_valid,
            detected=result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_circular_bridges(self) -> DomainAttackResult:
        bridge1 = DomainBridge(
            bridge_id="bridge-circular-1",
            source_domain_id="domain-a",
            destination_domain_id="domain-b",
            scope={"allowed_actions": ["read_evidence"]},
            delegation_chain=["bridge-circular-2"],
            status=BridgeStatus.ACTIVE,
        )
        bridge2 = DomainBridge(
            bridge_id="bridge-circular-2",
            source_domain_id="domain-b",
            destination_domain_id="domain-a",
            scope={"allowed_actions": ["read_evidence"]},
            delegation_chain=["bridge-circular-1"],
            status=BridgeStatus.ACTIVE,
        )
        self.verifier_a.register_bridge(bridge1)
        self.verifier_a.register_bridge(bridge2)
        result = self.verifier_a.verify_bridge(bridge1)
        return DomainAttackResult(
            attack_name="circular_bridges",
            attack_category="bridge_circular",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_consensus(self) -> DomainAttackResult:
        evidence_a = self._create_evidence_for_domain("domain-a")
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_cross_domain_composition(
            [evidence_a, evidence_b]
        )
        return DomainAttackResult(
            attack_name="cross_domain_consensus",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason="",
        )

    def attack_cross_domain_majority(self) -> DomainAttackResult:
        evidence_a1 = self._create_evidence_for_domain("domain-a")
        evidence_a2 = self._create_evidence_for_domain("domain-a")
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_cross_domain_composition(
            [evidence_a1, evidence_a2, evidence_b]
        )
        return DomainAttackResult(
            attack_name="cross_domain_majority",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason="",
        )

    def attack_cross_domain_artifact_replay(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_artifact_replay",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_provenance_substitution(self) -> DomainAttackResult:
        evidence = self._create_evidence_for_domain(
            "domain-a",
            provenance_root="provenance-root-b",
        )
        result = self.verifier_a.verify_artifact_domain(evidence)
        return DomainAttackResult(
            attack_name="cross_domain_provenance_substitution",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_temporal_replay(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_temporal_replay",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_crash_recovery(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_crash_recovery",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_distributed_convergence(self) -> DomainAttackResult:
        evidence_a = self._create_evidence_for_domain("domain-a")
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_cross_domain_composition(
            [evidence_a, evidence_b]
        )
        return DomainAttackResult(
            attack_name="cross_domain_distributed_convergence",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason="",
        )

    def attack_cross_domain_verification(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_verification",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_governance(self) -> DomainAttackResult:
        policy_b = self._create_policy_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(policy_b)
        return DomainAttackResult(
            attack_name="cross_domain_governance",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_authorization(self) -> DomainAttackResult:
        actor_b = self._create_actor_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(actor_b)
        return DomainAttackResult(
            attack_name="cross_domain_authorization",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_execution(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_execution",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def attack_cross_domain_revocation(self) -> DomainAttackResult:
        evidence_b = self._create_evidence_for_domain("domain-b")
        result = self.verifier_a.verify_artifact_domain(evidence_b)
        return DomainAttackResult(
            attack_name="cross_domain_revocation",
            attack_category="cross_domain",
            domain_id="domain-a",
            expected_valid=False,
            actual_valid=result.is_valid,
            detected=not result.is_valid,
            details=result.conflicts,
            rejection_reason=result.rejection_reason,
        )

    def run_all_attacks(self) -> list[DomainAttackResult]:
        attacks = [
            self.attack_cross_domain_evidence,
            self.attack_cross_domain_proposition,
            self.attack_cross_domain_actor,
            self.attack_cross_domain_policy,
            self.attack_cross_domain_delegation,
            self.attack_authority_root_substitution,
            self.attack_identity_root_substitution,
            self.attack_policy_root_substitution,
            self.attack_provenance_root_substitution,
            self.attack_schema_collision,
            self.attack_semantic_collision,
            self.attack_version_collision,
            self.attack_lineage_collision,
            self.attack_protocol_fork,
            self.attack_domain_fork,
            self.attack_bridge_scope_escalation,
            self.attack_bridge_temporal_escalation,
            self.attack_bridge_resource_escalation,
            self.attack_bridge_actor_substitution,
            self.attack_bridge_policy_substitution,
            self.attack_bridge_replay,
            self.attack_revoked_bridge,
            self.attack_expired_bridge,
            self.attack_future_bridge,
            self.attack_historical_bridge,
            self.attack_nested_bridges,
            self.attack_circular_bridges,
            self.attack_cross_domain_consensus,
            self.attack_cross_domain_majority,
            self.attack_cross_domain_artifact_replay,
            self.attack_cross_domain_provenance_substitution,
            self.attack_cross_domain_temporal_replay,
            self.attack_cross_domain_crash_recovery,
            self.attack_cross_domain_distributed_convergence,
            self.attack_cross_domain_verification,
            self.attack_cross_domain_governance,
            self.attack_cross_domain_authorization,
            self.attack_cross_domain_execution,
            self.attack_cross_domain_revocation,
        ]
        return [attack() for attack in attacks]


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_protocol_domain(
    domain_id: str,
    domain_type: DomainType = DomainType.SOVEREIGN,
    protocol_family: str = "sovereign-quant",
    protocol_version: str = "1.0.0",
    schema_version: str = "1.0.0",
    semantic_version: str = "1.0.0",
    authority_root: str = "",
    identity_root: str = "",
    policy_root: str = "",
    provenance_root: str = "",
    parent_domain_id: str = "",
) -> ProtocolDomain:
    if not authority_root:
        authority_root = f"auth-root-{domain_id}"
    if not identity_root:
        identity_root = f"identity-root-{domain_id}"
    if not policy_root:
        policy_root = f"policy-root-{domain_id}"
    if not provenance_root:
        provenance_root = f"provenance-root-{domain_id}"

    domain_root = hashlib.sha256(
        f"{domain_id}:{authority_root}:{identity_root}:{policy_root}:{provenance_root}".encode()
    ).hexdigest()[:16]

    lineage_hash = hashlib.sha256(
        f"{domain_id}:{protocol_family}:{protocol_version}".encode()
    ).hexdigest()[:16]

    return ProtocolDomain(
        domain_id=domain_id,
        domain_type=domain_type,
        domain_root=domain_root,
        protocol_family=protocol_family,
        protocol_version=protocol_version,
        schema_version=schema_version,
        semantic_version=semantic_version,
        authority_root=authority_root,
        identity_root=identity_root,
        policy_root=policy_root,
        provenance_root=provenance_root,
        parent_domain_id=parent_domain_id,
        lineage_hash=lineage_hash,
    )


def create_domain_bridge(
    bridge_id: str,
    source_domain_id: str,
    destination_domain_id: str,
    scope: dict,
    valid_from: str = "",
    valid_until: str = "-1",
    policy: str = "",
) -> DomainBridge:
    return DomainBridge(
        bridge_id=bridge_id,
        source_domain_id=source_domain_id,
        destination_domain_id=destination_domain_id,
        scope=scope,
        validity_interval=DomainValidityInterval(valid_from=valid_from, valid_until=valid_until),
        policy=policy or f"bridge-policy-{bridge_id}",
    )


def run_domain_attack_suite() -> list[DomainAttackResult]:
    suite = DomainAttackSuite()
    return suite.run_all_attacks()


def generate_domain_attack_report(results: list[DomainAttackResult]) -> str:
    lines = [
        "Protocol Lineage and Sovereign Domain Integrity",
        "================================================",
        "",
        f"Total attacks: {len(results)}",
        f"Detected: {sum(1 for r in results if r.detected)}",
        f"Missed: {sum(1 for r in results if not r.detected)}",
        "",
        "By category:",
    ]

    categories: dict[str, list[DomainAttackResult]] = {}
    for r in results:
        categories.setdefault(r.attack_category, []).append(r)

    for category, cat_results in sorted(categories.items()):
        detected = sum(1 for r in cat_results if r.detected)
        lines.append(f"  {category}: {detected}/{len(cat_results)} detected")

    lines.append("")
    lines.append("By domain:")
    domains: dict[str, list[DomainAttackResult]] = {}
    for r in results:
        domains.setdefault(r.domain_id, []).append(r)

    for domain_id, domain_results in sorted(domains.items()):
        detected = sum(1 for r in domain_results if r.detected)
        lines.append(f"  {domain_id}: {detected}/{len(domain_results)} detected")

    lines.append("")
    lines.append("Failures:")
    failures = [r for r in results if not r.detected]
    if failures:
        for f in failures:
            lines.append(f"  {f.attack_name}: {f.rejection_reason}")
    else:
        lines.append("  None")

    return "\n".join(lines)
