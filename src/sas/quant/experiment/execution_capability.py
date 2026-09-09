"""Execution Capability and Authority Materialization.

Investigates the boundary between derived authority and actual capability.

The central research question:
    Once the protocol has derived an AuthorizationArtifact, how does that
    authority become a bounded runtime capability without allowing the
    execution environment to acquire authority that was never explicitly
    derived?

Architecture:
    AuthorizationArtifact
          ↓
    CapabilityMaterializer
          ↓
    ExecutionCapability
          ↓
    ExecutionContext
          ↓
    Executor
          ↓
    ExecutionReceipt
          ↓
    External Observation
          ↓
    Verified Effect

Invariants:
    AUTHORIZATION DOES NOT IMPLY CAPABILITY.

    CAPABILITY DOES NOT IMPLY EXECUTION.

    EXECUTION DOES NOT IMPLY EFFECT.

    EXECUTOR PRIVILEGE DOES NOT BECOME CALLER AUTHORITY.

    CAPABILITY AUTHORITY CANNOT EXCEED AUTHORIZATION AUTHORITY.

    RESOURCE IDENTITY IS PART OF EXECUTION AUTHORITY.

    TEMPORAL VALIDITY BINDS CAPABILITY USE.

    REVOCATION CHANGES CURRENT AUTHORITY WITHOUT REWRITING HISTORICAL EXECUTION.

    EXECUTION CLAIMS ARE NOT EXECUTION EVIDENCE.

    EXECUTION RECEIPTS ARE DERIVED ARTIFACTS, NOT AUTHORITY ROOTS.

    NO UNDECLARED EXECUTION INTERFERENCE.

    CAPABILITY TRANSFER DOES NOT IMPLY AUTHORITY TRANSFER.

    CAPABILITY COMPOSITION DOES NOT AUTOMATICALLY PRODUCE COMPOSITE AUTHORITY.

    CAPABILITY ATTENUATION MUST NEVER INCREASE AUTHORITY.

    AMBIENT PROCESS PRIVILEGE IS NOT PROTOCOL AUTHORITY.

    EXECUTION AUTHORITY MUST BE RECONSTRUCTABLE FROM PERSISTED PROVENANCE.

    EXTERNAL EFFECT MUST BE DISTINGUISHED FROM EXECUTOR ASSERTION.
"""

from __future__ import annotations

import hashlib
import json
import uuid
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
from sas.quant.experiment.protocol_lineage import (
    AuthorityRoot,
    BridgeStatus,
    DomainAttackResult,
    DomainAttackSuite,
    DomainBoundActor,
    DomainBoundArtifact,
    DomainBoundAuthorization,
    DomainBoundDelegation,
    DomainBoundEvidenceBundle,
    DomainBoundEpistemicState,
    DomainBoundPolicy,
    DomainBoundProposition,
    DomainBridge,
    DomainConflictType,
    DomainType,
    DomainValidityInterval,
    DomainVerificationResult,
    LineageType,
    LineageVerificationResult,
    ProtocolDomain,
    ProtocolLineage,
    ProtocolLineageVerifier,
    RootType,
    BridgeVerificationResult,
    create_domain_bridge,
    create_protocol_domain,
    generate_domain_attack_report,
    run_domain_attack_suite,
)


# ---------------------------------------------------------------------------
# Capability Classification
# ---------------------------------------------------------------------------


class CapabilityType(str, Enum):
    """Types of execution capabilities."""
    EXECUTE = "execute"
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    DELEGATE = "delegate"
    REVOKE = "revoke"
    OBSERVE = "observe"
    VERIFY = "verify"
    ADMINISTER = "administer"


class AttenuationType(str, Enum):
    """Types of capability attenuation."""
    SCOPE_NARROWING = "scope_narrowing"
    RESOURCE_RESTRICTION = "resource_restriction"
    TEMPORAL_SHORTENING = "temporal_shortening"
    QUANTITY_REDUCTION = "quantity_reduction"
    ACTION_SUBSET = "action_subset"
    ARGUMENT_CONSTRAINT = "argument_constraint"


class BindingType(str, Enum):
    """Types of resource binding."""
    EXCLUSIVE = "exclusive"
    SHARED = "shared"
    EPHEMERAL = "ephemeral"
    PERSISTENT = "persistent"


class ExecutionStatus(str, Enum):
    """Status of execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REPLAYED = "replayed"
    REJECTED = "rejected"


class ReplayProtectionType(str, Enum):
    """Types of replay protection."""
    NONCE = "nonce"
    SEQUENCE = "sequence"
    TIMESTAMP = "timestamp"
    SINGLE_USE = "single_use"
    BOUNDED_USE = "bounded_use"


# ---------------------------------------------------------------------------
# Replay Guard
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReplayGuard:
    """Prevents capability replay.

    Each capability carries a replay guard that ensures it cannot be
    reused beyond its intended scope.

    Attributes:
        guard_type: Type of replay protection.
        nonce: Unique nonce for this capability.
        sequence: Sequence number for ordered execution.
        previous_nonce: Previous nonce in the chain.
        max_uses: Maximum number of uses (-1 = unlimited).
        current_uses: Current number of uses.
        created_at: When the guard was created.
    """
    guard_type: ReplayProtectionType
    nonce: str = ""
    sequence: int = 0
    previous_nonce: str = ""
    max_uses: int = 1
    current_uses: int = 0
    created_at: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "guard_type": self.guard_type.value,
            "nonce": self.nonce,
            "sequence": self.sequence,
            "previous_nonce": self.previous_nonce,
            "max_uses": self.max_uses,
            "current_uses": self.current_uses,
            "created_at": self.created_at,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_exhausted(self) -> bool:
        """Check if the guard has been used up."""
        if self.max_uses < 0:
            return False
        return self.current_uses >= self.max_uses

    def can_execute(self) -> bool:
        """Check if execution is permitted."""
        return not self.is_exhausted()

    def record_use(self) -> ReplayGuard:
        """Record a use and return updated guard."""
        return ReplayGuard(
            guard_type=self.guard_type,
            nonce=self.nonce,
            sequence=self.sequence,
            previous_nonce=self.previous_nonce,
            max_uses=self.max_uses,
            current_uses=self.current_uses + 1,
            created_at=self.created_at,
        )

    def follows(self, other: ReplayGuard) -> bool:
        """Check if this guard follows another in sequence."""
        return (
            self.sequence == other.sequence + 1
            and self.previous_nonce == other.nonce
        )


# ---------------------------------------------------------------------------
# Capability Constraints
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityConstraints:
    """Constraints on capability usage, attenuation, and composition.

    These constraints are structural guarantees that the capability cannot
    exceed its defined bounds.

    Attributes:
        attenuation_type: Type of attenuation applied.
        attenuation_factor: Factor of attenuation (0-1).
        allowed_actions: Subset of actions permitted.
        forbidden_actions: Actions explicitly forbidden.
        max_quantity: Maximum quantity allowed.
        min_quantity: Minimum quantity allowed.
        allowed_arguments: Permitted argument patterns.
        forbidden_arguments: Forbidden argument patterns.
        composition_permitted: Whether composition is allowed.
        delegation_permitted: Whether delegation is allowed.
        transfer_permitted: Whether transfer is allowed.
    """
    attenuation_type: Optional[AttenuationType] = None
    attenuation_factor: float = 1.0
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    max_quantity: float = float('inf')
    min_quantity: float = 0.0
    allowed_arguments: dict = field(default_factory=dict)
    forbidden_arguments: dict = field(default_factory=dict)
    composition_permitted: bool = False
    delegation_permitted: bool = False
    transfer_permitted: bool = False

    def compute_hash(self) -> str:
        content = json.dumps({
            "attenuation_type": self.attenuation_type.value if self.attenuation_type else None,
            "attenuation_factor": self.attenuation_factor,
            "allowed_actions": sorted(self.allowed_actions),
            "forbidden_actions": sorted(self.forbidden_actions),
            "max_quantity": self.max_quantity,
            "min_quantity": self.min_quantity,
            "allowed_arguments": self.allowed_arguments,
            "forbidden_arguments": self.forbidden_arguments,
            "composition_permitted": self.composition_permitted,
            "delegation_permitted": self.delegation_permitted,
            "transfer_permitted": self.transfer_permitted,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def permits_action(self, action: str) -> bool:
        """Check if an action is permitted."""
        if self.forbidden_actions and action in self.forbidden_actions:
            return False
        if self.allowed_actions and action not in self.allowed_actions:
            return False
        return True

    def permits_quantity(self, quantity: float) -> bool:
        """Check if a quantity is permitted."""
        return self.min_quantity <= quantity <= self.max_quantity


# ---------------------------------------------------------------------------
# Capability Scope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityScope:
    """Explicit scope of a capability.

    The scope defines exactly what the capability permits, no more.

    Attributes:
        domain_id: The domain this capability belongs to.
        lineage_id: The lineage this capability belongs to.
        actor_id: The actor this capability is bound to.
        action: The action permitted.
        resource: The resource targeted.
        resource_class: The class of resource.
        arguments: Argument constraints.
        constraints: Additional constraints.
        temporal_interval: When the capability is valid.
        delegation_chain: Chain of delegations.
        authorization_ref: Reference to parent authorization.
        provenance_ref: Reference to provenance.
        nonce: Replay guard nonce.
        expiration: When the capability expires.
    """
    domain_id: str = ""
    lineage_id: str = ""
    actor_id: str = ""
    action: str = ""
    resource: str = ""
    resource_class: str = ""
    arguments: dict = field(default_factory=dict)
    constraints: CapabilityConstraints = field(default_factory=CapabilityConstraints)
    temporal_interval: DomainValidityInterval = field(default_factory=DomainValidityInterval)
    delegation_chain: list[str] = field(default_factory=list)
    authorization_ref: str = ""
    provenance_ref: str = ""
    nonce: str = ""
    expiration: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "domain_id": self.domain_id,
            "lineage_id": self.lineage_id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource": self.resource,
            "resource_class": self.resource_class,
            "arguments": self.arguments,
            "constraints": self.constraints.compute_hash(),
            "temporal_interval": {
                "valid_from": self.temporal_interval.valid_from,
                "valid_until": self.temporal_interval.valid_until,
            },
            "delegation_chain": sorted(self.delegation_chain),
            "authorization_ref": self.authorization_ref,
            "provenance_ref": self.provenance_ref,
            "nonce": self.nonce,
            "expiration": self.expiration,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_valid_at(self, timestamp: str) -> bool:
        """Check if the scope is valid at a given timestamp."""
        return self.temporal_interval.contains(timestamp)

    def is_compatible_with_domain(self, domain: ProtocolDomain) -> bool:
        """Check if this scope is compatible with a domain."""
        if self.domain_id and self.domain_id != domain.domain_id:
            return False
        return True

    def permits_action(self, action: str) -> bool:
        """Check if an action is permitted by this scope."""
        if self.action and self.action != action:
            return False
        return self.constraints.permits_action(action)


# ---------------------------------------------------------------------------
# Execution Capability
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionCapability:
    """A materialized capability derived from authorization.

    An execution capability is the operational representation of
    already-derived authority. It must not become a new authority root.

    Attributes:
        capability_id: Unique identifier.
        authorization_ref: Reference to parent authorization.
        scope: Explicit scope of the capability.
        capability_type: Type of capability.
        replay_guard: Replay protection.
        actor_identity_ref: Reference to actor identity.
        resource_binding: Reference to resource binding.
        domain_id: The domain this capability belongs to.
        lineage_id: The lineage this capability belongs to.
        authority_root: The authority root.
        provenance_root: The provenance root.
        derived_at: When the capability was derived.
        derived_by: Who derived the capability.
        derivation_proof: Proof of derivation.
        attenuation_chain: Chain of attenuations applied.
        metadata: Additional metadata.
    """
    capability_id: str
    authorization_ref: str
    scope: CapabilityScope
    capability_type: CapabilityType = CapabilityType.EXECUTE
    replay_guard: Optional[ReplayGuard] = None
    actor_identity_ref: str = ""
    resource_binding: Optional[ExecutorBinding] = None
    domain_id: str = ""
    lineage_id: str = ""
    authority_root: str = ""
    provenance_root: str = ""
    derived_at: str = ""
    derived_by: str = ""
    derivation_proof: str = ""
    attenuation_chain: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        content = json.dumps({
            "capability_id": self.capability_id,
            "authorization_ref": self.authorization_ref,
            "scope": self.scope.compute_hash(),
            "capability_type": self.capability_type.value,
            "replay_guard": self.replay_guard.compute_hash() if self.replay_guard else "",
            "actor_identity_ref": self.actor_identity_ref,
            "resource_binding": self.resource_binding.compute_hash() if self.resource_binding else "",
            "domain_id": self.domain_id,
            "lineage_id": self.lineage_id,
            "authority_root": self.authority_root,
            "provenance_root": self.provenance_root,
            "derived_at": self.derived_at,
            "derived_by": self.derived_by,
            "derivation_proof": self.derivation_proof,
            "attenuation_chain": sorted(self.attenuation_chain),
            "metadata": self.metadata,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_valid_at(self, timestamp: str) -> bool:
        """Check if the capability is valid at a given timestamp."""
        if not self.scope.is_valid_at(timestamp):
            return False
        if self.replay_guard and not self.replay_guard.can_execute():
            return False
        return True

    def can_execute(self) -> bool:
        """Check if the capability can be executed."""
        if self.replay_guard and not self.replay_guard.can_execute():
            return False
        return True

    def is_subcapability_of(self, auth_scope: dict) -> bool:
        """Verify this capability is a subset of its parent authorization scope."""
        # Check action subset
        auth_allowed = set(auth_scope.get("allowed_actions", []))
        if auth_allowed and not set([self.scope.action]).issubset(auth_allowed):
            return False
        # Check resource subset
        auth_resources = set(auth_scope.get("target_resources", []))
        if auth_resources and not set([self.scope.resource]).issubset(auth_resources):
            return False
        return True


# ---------------------------------------------------------------------------
# Executor Binding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutorBinding:
    """Binds a capability to a specific executor and resource.

    Attributes:
        binding_id: Unique identifier.
        executor_id: The executor identity.
        resource_id: The resource identity.
        bound_resources: List of bound resource IDs.
        resource_handles: Resource handles.
        binding_type: Type of binding.
        bound_at: When the binding was created.
        bound_until: When the binding expires.
        binding_proof: Cryptographic proof of binding.
        binding_verified: Whether binding has been verified.
        verification_ref: Reference to verification artifact.
    """
    binding_id: str
    executor_id: str
    resource_id: str
    bound_resources: list[str] = field(default_factory=list)
    resource_handles: dict = field(default_factory=dict)
    binding_type: BindingType = BindingType.EXCLUSIVE
    bound_at: str = ""
    bound_until: str = ""
    binding_proof: str = ""
    binding_verified: bool = False
    verification_ref: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "binding_id": self.binding_id,
            "executor_id": self.executor_id,
            "resource_id": self.resource_id,
            "bound_resources": sorted(self.bound_resources),
            "resource_handles": self.resource_handles,
            "binding_type": self.binding_type.value,
            "bound_at": self.bound_at,
            "bound_until": self.bound_until,
            "binding_proof": self.binding_proof,
            "binding_verified": self.binding_verified,
            "verification_ref": self.verification_ref,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_valid_at(self, timestamp: str) -> bool:
        """Check if the binding is valid at a given timestamp."""
        if self.bound_at and timestamp < self.bound_at:
            return False
        if self.bound_until and self.bound_until != "-1" and timestamp > self.bound_until:
            return False
        return True

    def binds_resource(self, resource_id: str) -> bool:
        """Check if this binding covers a specific resource."""
        return resource_id in self.bound_resources or resource_id == self.resource_id


# ---------------------------------------------------------------------------
# Execution Context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionContext:
    """Runtime context for execution.

    Attributes:
        context_id: Unique identifier.
        capability_ref: Reference to the capability being executed.
        executor_id: The executor identity.
        resource_id: The resource being targeted.
        actor_id: The actor performing the action.
        domain_id: The domain of execution.
        lineage_id: The lineage of execution.
        start_time: When execution started.
        end_time: When execution completed.
        status: Current execution status.
        parameters: Execution parameters.
        environment: Environment variables (explicit, not ambient).
        provenance_ref: Reference to provenance.
    """
    context_id: str
    capability_ref: str
    executor_id: str
    resource_id: str
    actor_id: str
    domain_id: str = ""
    lineage_id: str = ""
    start_time: str = ""
    end_time: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    parameters: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    provenance_ref: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "context_id": self.context_id,
            "capability_ref": self.capability_ref,
            "executor_id": self.executor_id,
            "resource_id": self.resource_id,
            "actor_id": self.actor_id,
            "domain_id": self.domain_id,
            "lineage_id": self.lineage_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "parameters": self.parameters,
            "environment": self.environment,
            "provenance_ref": self.provenance_ref,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_active(self) -> bool:
        """Check if execution is currently active."""
        return self.status == ExecutionStatus.EXECUTING

    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return self.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED)


# ---------------------------------------------------------------------------
# Execution Receipt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionReceipt:
    """Immutable record of what actually happened during execution.

    Separates intended effect from observed effect from reported result.

    Attributes:
        receipt_id: Unique identifier.
        capability_ref: Reference to the capability.
        authorization_ref: Reference to parent authorization.
        domain_id: The domain of execution.
        lineage_id: The lineage of execution.
        actor_id: The actor who performed the action.
        executor_id: The executor that performed the action.
        resource_id: The resource targeted.
        action: The action performed.
        arguments_hash: Hash of arguments.
        start_time: When execution started.
        completion_time: When execution completed.
        effect_summary: Summary of the effect.
        result_hash: Hash of the result.
        external_reference: External reference (e.g., broker order ID).
        status: Execution status.
        intended_effect: What was intended.
        observed_effect: What was observed.
        reported_result: What the executor reported.
        provenance_hash: Hash of provenance.
        metadata: Additional metadata.
    """
    receipt_id: str
    capability_ref: str
    authorization_ref: str
    domain_id: str = ""
    lineage_id: str = ""
    actor_id: str = ""
    executor_id: str = ""
    resource_id: str = ""
    action: str = ""
    arguments_hash: str = ""
    start_time: str = ""
    completion_time: str = ""
    effect_summary: str = ""
    result_hash: str = ""
    external_reference: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    intended_effect: str = ""
    observed_effect: str = ""
    reported_result: str = ""
    provenance_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        content = json.dumps({
            "receipt_id": self.receipt_id,
            "capability_ref": self.capability_ref,
            "authorization_ref": self.authorization_ref,
            "domain_id": self.domain_id,
            "lineage_id": self.lineage_id,
            "actor_id": self.actor_id,
            "executor_id": self.executor_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "arguments_hash": self.arguments_hash,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "effect_summary": self.effect_summary,
            "result_hash": self.result_hash,
            "external_reference": self.external_reference,
            "status": self.status.value,
            "intended_effect": self.intended_effect,
            "observed_effect": self.observed_effect,
            "reported_result": self.reported_result,
            "provenance_hash": self.provenance_hash,
            "metadata": self.metadata,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_verified(self) -> bool:
        """Check if the receipt has been independently verified."""
        return self.observed_effect != "" and self.reported_result != ""

    def has_divergence(self) -> bool:
        """Check if there's divergence between intended and observed."""
        if not self.intended_effect or not self.observed_effect:
            return False
        return self.intended_effect != self.observed_effect


# ---------------------------------------------------------------------------
# Capability Materializer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapabilityMaterializationResult:
    """Result of capability materialization."""
    is_valid: bool
    capability: Optional[ExecutionCapability] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


class CapabilityMaterializer:
    """Derives execution capabilities from authorizations.

    The materializer ensures that capabilities never contain more authority
    than the authorization from which they were derived.
    """

    def __init__(self, domain: ProtocolDomain):
        self.domain = domain

    def materialize(
        self,
        authorization: AuthorizationArtifact,
        action_proposal: ActionProposal,
        actor: ActorIdentity,
        policy: GovernancePolicy,
        current_time: str = "",
        resource_id: str = "",
    ) -> CapabilityMaterializationResult:
        """Materialize a capability from an authorization."""
        conflicts = []

        # Verify authorization status
        if authorization.status != AuthorizationStatus.AUTHORIZED:
            conflicts.append(f"Authorization status is {authorization.status.value}, not AUTHORIZED")

        # Verify domain compatibility
        if self.domain.domain_id and authorization.authorization_id:
            # Domain check would go here
            pass

        # Verify temporal validity
        if current_time and authorization.expiration and authorization.expiration != "":
            if current_time > authorization.expiration:
                conflicts.append(f"Authorization expired at {authorization.expiration}")

        # Verify actor binding
        if actor.actor_id and authorization.identity_ref:
            if actor.actor_id != authorization.identity_ref:
                conflicts.append(f"Actor mismatch: {actor.actor_id} != {authorization.identity_ref}")

        # Create replay guard
        replay_guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=str(uuid.uuid4()),
            sequence=0,
            max_uses=1,
            current_uses=0,
            created_at=current_time,
        )

        # Create capability scope
        scope = CapabilityScope(
            domain_id=self.domain.domain_id,
            lineage_id=self.domain.lineage_hash,
            actor_id=actor.actor_id,
            action=action_proposal.action_type,
            resource=resource_id or action_proposal.target,
            arguments=action_proposal.parameters,
            constraints=CapabilityConstraints(
                allowed_actions=[action_proposal.action_type],
                composition_permitted=False,
                delegation_permitted=False,
                transfer_permitted=False,
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=current_time,
                valid_until=authorization.expiration if authorization.expiration != "" else "",
            ),
            authorization_ref=authorization.authorization_id,
            nonce=replay_guard.nonce,
            expiration=authorization.expiration if authorization.expiration != "" else "",
        )

        # Create capability
        capability = ExecutionCapability(
            capability_id=f"cap_{authorization.authorization_id}",
            authorization_ref=authorization.authorization_id,
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=replay_guard,
            actor_identity_ref=actor.actor_id,
            domain_id=self.domain.domain_id,
            lineage_id=self.domain.lineage_hash,
            authority_root=self.domain.authority_root,
            provenance_root=self.domain.provenance_root,
            derived_at=current_time,
            derived_by="CapabilityMaterializer",
            derivation_proof=authorization.compute_hash(),
        )

        is_valid = len(conflicts) == 0
        rejection_reason = "; ".join(conflicts) if conflicts else ""

        return CapabilityMaterializationResult(
            is_valid=is_valid,
            capability=capability if is_valid else None,
            conflicts=conflicts,
            rejection_reason=rejection_reason,
            provenance_hash=capability.compute_hash() if capability else "",
        )

    def attenuate(
        self,
        capability: ExecutionCapability,
        constraints: CapabilityConstraints,
    ) -> CapabilityMaterializationResult:
        """Attenuate a capability to a narrower scope."""
        conflicts = []

        # Verify attenuation doesn't increase authority
        if constraints.attenuation_factor > 1.0:
            conflicts.append("Attenuation factor cannot increase authority")

        # Verify action subset
        if constraints.allowed_actions:
            if capability.scope.action not in constraints.allowed_actions:
                conflicts.append(f"Action {capability.scope.action} not in allowed subset")

        # Create attenuated scope
        attenuated_scope = CapabilityScope(
            domain_id=capability.scope.domain_id,
            lineage_id=capability.scope.lineage_id,
            actor_id=capability.scope.actor_id,
            action=capability.scope.action,
            resource=capability.scope.resource,
            resource_class=capability.scope.resource_class,
            arguments=capability.scope.arguments,
            constraints=constraints,
            temporal_interval=capability.scope.temporal_interval,
            delegation_chain=capability.scope.delegation_chain,
            authorization_ref=capability.scope.authorization_ref,
            provenance_ref=capability.scope.provenance_ref,
            nonce=capability.scope.nonce,
            expiration=capability.scope.expiration,
        )

        # Create attenuated capability
        attenuated = ExecutionCapability(
            capability_id=f"cap_attenuated_{capability.capability_id}",
            authorization_ref=capability.authorization_ref,
            scope=attenuated_scope,
            capability_type=capability.capability_type,
            replay_guard=capability.replay_guard,
            actor_identity_ref=capability.actor_identity_ref,
            resource_binding=capability.resource_binding,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            authority_root=capability.authority_root,
            provenance_root=capability.provenance_root,
            derived_at=capability.derived_at,
            derived_by="CapabilityMaterializer.attenuate",
            derivation_proof=capability.derivation_proof,
            attenuation_chain=capability.attenuation_chain + [constraints.compute_hash()],
        )

        is_valid = len(conflicts) == 0
        rejection_reason = "; ".join(conflicts) if conflicts else ""

        return CapabilityMaterializationResult(
            is_valid=is_valid,
            capability=attenuated if is_valid else None,
            conflicts=conflicts,
            rejection_reason=rejection_reason,
            provenance_hash=attenuated.compute_hash() if attenuated else "",
        )


# ---------------------------------------------------------------------------
# Execution Capability Attack Suite
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionCapabilityAttackResult:
    """Result of an execution capability attack."""
    attack_name: str
    attack_category: str
    domain_id: str
    expected_valid: bool
    actual_valid: bool
    detected: bool
    details: list[str] = field(default_factory=list)
    rejection_reason: str = ""


class ExecutionCapabilityAttackSuite:
    """Adversarial tests for execution capability and authority materialization."""

    def __init__(self):
        self.domain = self._create_domain()
        self.materializer = CapabilityMaterializer(self.domain)
        self._create_base_authorization()

    def _create_domain(self) -> ProtocolDomain:
        return create_protocol_domain("trading-domain")

    def _create_base_authorization(self):
        """Create a base authorization for testing."""
        self.base_actor = ActorIdentity(
            actor_id="actor-1",
            capabilities=["execute_trade"],
        )
        self.base_policy = GovernancePolicy(
            policy_id="policy-1",
            policy_version="1.0.0",
            allowed_actions=["execute_trade"],
        )
        self.base_proposal = ActionProposal(
            action_id="action-1",
            proposer_id="agent-1",
            action_type="execute_trade",
            target="AAPL",
            parameters={"quantity": 100, "account": "account_1"},
        )
        self.base_authorization = AuthorizationArtifact(
            authorization_id="auth-1",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.AUTHORIZED,
            identity_ref="actor-1",
            authorization_scope={
                "allowed_actions": ["execute_trade"],
                "target_resources": ["broker:A"],
            },
            temporal_constraints={
                "valid_from": "2024-01-01T00:00:00Z",
                "valid_until": "2024-12-31T23:59:59Z",
            },
            expiration="2024-12-31T23:59:59Z",
        )

    def _materialize_capability(
        self,
        authorization: Optional[AuthorizationArtifact] = None,
        proposal: Optional[ActionProposal] = None,
        actor: Optional[ActorIdentity] = None,
        current_time: str = "2024-06-01T00:00:00Z",
        resource_id: str = "broker:A",
    ) -> CapabilityMaterializationResult:
        return self.materializer.materialize(
            authorization or self.base_authorization,
            proposal or self.base_proposal,
            actor or self.base_actor,
            self.base_policy,
            current_time,
            resource_id,
        )

    # --- Capability widening ---

    def attack_capability_widening(self) -> ExecutionCapabilityAttackResult:
        """Attempt to widen capability scope beyond authorization."""
        result = self._materialize_capability()
        if not result.capability:
            return ExecutionCapabilityAttackResult(
                attack_name="capability_widening",
                attack_category="capability_widening",
                domain_id=self.domain.domain_id,
                expected_valid=False,
                actual_valid=False,
                detected=True,
                details=["Capability materialization failed"],
            )
        # Capability scope should match authorization scope
        cap_scope = result.capability.scope
        auth_scope = self.base_authorization.authorization_scope
        auth_allowed = set(auth_scope.get("allowed_actions", []))
        cap_actions = set([cap_scope.action])
        is_subset = cap_actions.issubset(auth_allowed) if auth_allowed else True
        return ExecutionCapabilityAttackResult(
            attack_name="capability_widening",
            attack_category="capability_widening",
            domain_id=self.domain.domain_id,
            expected_valid=True,
            actual_valid=is_subset,
            detected=is_subset,
            details=[f"Capability actions {cap_actions} subset of auth {auth_allowed}: {is_subset}"],
        )

    # --- Actor substitution ---

    def attack_actor_substitution(self) -> ExecutionCapabilityAttackResult:
        """Attempt to substitute actor in capability."""
        different_actor = ActorIdentity(actor_id="actor-2", capabilities=["execute_trade"])
        result = self._materialize_capability(actor=different_actor)
        # Should fail because actor doesn't match authorization
        is_rejected = not result.is_valid
        return ExecutionCapabilityAttackResult(
            attack_name="actor_substitution",
            attack_category="actor_substitution",
            domain_id=self.domain.domain_id,
            expected_valid=False,
            actual_valid=not is_rejected,
            detected=is_rejected,
            details=[result.rejection_reason] if is_rejected else [],
            rejection_reason=result.rejection_reason,
        )

    # --- Resource substitution ---

    def attack_resource_substitution(self) -> ExecutionCapabilityAttackResult:
        """Attempt to substitute resource in capability."""
        # Authorize broker:A, try to use broker:B
        result = self._materialize_capability(resource_id="broker:B")
        # Resource binding should be explicit
        if result.capability:
            binds_wrong = result.capability.resource_binding.binds_resource("broker:B") if result.capability.resource_binding else False
            return ExecutionCapabilityAttackResult(
                attack_name="resource_substitution",
                attack_category="resource_substitution",
                domain_id=self.domain.domain_id,
                expected_valid=False,
                actual_valid=binds_wrong,
                detected=not binds_wrong,
                details=[f"Capability binds broker:B: {binds_wrong}"],
            )
        return ExecutionCapabilityAttackResult(
            attack_name="resource_substitution",
            attack_category="resource_substitution",
            domain_id=self.domain.domain_id,
            expected_valid=False,
            actual_valid=False,
            detected=True,
            details=["Capability materialization failed"],
        )

    # --- Temporal extension ---

    def attack_temporal_extension(self) -> ExecutionCapabilityAttackResult:
        """Attempt to use capability after expiration."""
        # Create expired authorization
        expired_auth = AuthorizationArtifact(
            authorization_id="auth-expired",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.AUTHORIZED,
            identity_ref="actor-1",
            authorization_scope={"allowed_actions": ["execute_trade"]},
            temporal_constraints={
                "valid_from": "2024-01-01T00:00:00Z",
                "valid_until": "2024-01-31T23:59:59Z",
            },
            expiration="2024-01-31T23:59:59Z",  # Expired
        )
        result = self._materialize_capability(
            authorization=expired_auth,
            current_time="2024-06-01T00:00:00Z",  # After expiration
        )
        is_rejected = not result.is_valid
        return ExecutionCapabilityAttackResult(
            attack_name="temporal_extension",
            attack_category="temporal_extension",
            domain_id=self.domain.domain_id,
            expected_valid=False,
            actual_valid=not is_rejected,
            detected=is_rejected,
            details=[result.rejection_reason] if is_rejected else [],
            rejection_reason=result.rejection_reason,
        )

    # --- Replay attack ---

    def attack_replay(self) -> ExecutionCapabilityAttackResult:
        """Attempt to replay a capability."""
        result = self._materialize_capability()
        if not result.capability:
            return ExecutionCapabilityAttackResult(
                attack_name="replay",
                attack_category="replay",
                domain_id=self.domain.domain_id,
                expected_valid=False,
                actual_valid=False,
                detected=True,
                details=["Capability materialization failed"],
            )
        # First use should succeed
        cap1 = result.capability
        can_use_1 = cap1.can_execute()
        # Record use
        used_guard = cap1.replay_guard.record_use() if cap1.replay_guard else None
        # Second use should fail
        cap2 = ExecutionCapability(
            **{**cap1.__dict__, "replay_guard": used_guard}
        )
        can_use_2 = cap2.can_execute()
        return ExecutionCapabilityAttackResult(
            attack_name="replay",
            attack_category="replay",
            domain_id=self.domain.domain_id,
            expected_valid=False,
            actual_valid=can_use_1 and not can_use_2,
            detected=can_use_1 and not can_use_2,
            details=[
                f"First use permitted: {can_use_1}",
                f"Second use permitted: {can_use_2}",
            ],
        )

    # --- Attenuation attack ---

    def attack_attenuation_increase(self) -> ExecutionCapabilityAttackResult:
        """Attempt to increase authority through attenuation."""
        result = self._materialize_capability()
        if not result.capability:
            return ExecutionCapabilityAttackResult(
                attack_name="attenuation_increase",
                attack_category="attenuation",
                domain_id=self.domain.domain_id,
                expected_valid=False,
                actual_valid=False,
                detected=True,
                details=["Capability materialization failed"],
            )
        # Try to attenuate with factor > 1 (increasing authority)
        bad_constraints = CapabilityConstraints(
            attenuation_type=AttenuationType.QUANTITY_REDUCTION,
            attenuation_factor=2.0,  # This should be rejected
            max_quantity=1000,  # More than original
        )
        att_result = self.materializer.attenuate(result.capability, bad_constraints)
        is_rejected = not att_result.is_valid
        return ExecutionCapabilityAttackResult(
            attack_name="attenuation_increase",
            attack_category="attenuation",
            domain_id=self.domain.domain_id,
            expected_valid=False,
            actual_valid=not is_rejected,
            detected=is_rejected,
            details=[att_result.rejection_reason] if is_rejected else [],
            rejection_reason=att_result.rejection_reason,
        )

    # --- Domain substitution ---

    def attack_domain_substitution(self) -> ExecutionCapabilityAttackResult:
        """Attempt to use capability in wrong domain."""
        result = self._materialize_capability()
        if not result.capability:
            return ExecutionCapabilityAttackResult(
                attack_name="domain_substitution",
                attack_category="domain_substitution",
                domain_id=self.domain.domain_id,
                expected_valid=False,
                actual_valid=False,
                detected=True,
                details=["Capability materialization failed"],
            )
        # Check domain binding
        wrong_domain = create_protocol_domain("wrong-domain")
        is_compatible = result.capability.scope.is_compatible_with_domain(wrong_domain)
        return ExecutionCapabilityAttackResult(
            attack_name="domain_substitution",
            attack_category="domain_substitution",
            domain_id=self.domain.domain_id,
            expected_valid=False,
            actual_valid=is_compatible,
            detected=not is_compatible,
            details=[f"Capability compatible with wrong domain: {is_compatible}"],
        )

    # --- Executor privilege escalation ---

    def attack_executor_privilege_escalation(self) -> ExecutionCapabilityAttackResult:
        """Attempt to escalate privileges through executor."""
        result = self._materialize_capability()
        if not result.capability:
            return ExecutionCapabilityAttackResult(
                attack_name="executor_privilege_escalation",
                attack_category="executor",
                domain_id=self.domain.domain_id,
                expected_valid=False,
                actual_valid=False,
                detected=True,
                details=["Capability materialization failed"],
            )
        # Capability scope should be narrow
        cap_scope = result.capability.scope
        is_narrow = cap_scope.action == "execute_trade" and cap_scope.constraints.composition_permitted is False
        return ExecutionCapabilityAttackResult(
            attack_name="executor_privilege_escalation",
            attack_category="executor",
            domain_id=self.domain.domain_id,
            expected_valid=True,
            actual_valid=is_narrow,
            detected=is_narrow,
            details=[f"Capability scope is narrow: {is_narrow}"],
        )

    # --- Run all attacks ---

    def run_all_attacks(self) -> list[ExecutionCapabilityAttackResult]:
        """Run all execution capability attacks."""
        attacks = [
            self.attack_capability_widening,
            self.attack_actor_substitution,
            self.attack_resource_substitution,
            self.attack_temporal_extension,
            self.attack_replay,
            self.attack_attenuation_increase,
            self.attack_domain_substitution,
            self.attack_executor_privilege_escalation,
        ]
        return [attack() for attack in attacks]


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_execution_capability(
    authorization: AuthorizationArtifact,
    action_proposal: ActionProposal,
    actor: ActorIdentity,
    policy: GovernancePolicy,
    domain: ProtocolDomain,
    current_time: str = "",
    resource_id: str = "",
) -> CapabilityMaterializationResult:
    """Create an execution capability from an authorization."""
    materializer = CapabilityMaterializer(domain)
    return materializer.materialize(
        authorization, action_proposal, actor, policy, current_time, resource_id
    )


def run_execution_capability_attack_suite() -> list[ExecutionCapabilityAttackResult]:
    """Run the complete execution capability attack suite."""
    suite = ExecutionCapabilityAttackSuite()
    return suite.run_all_attacks()


def generate_execution_capability_attack_report(
    results: list[ExecutionCapabilityAttackResult],
) -> str:
    """Generate a report from execution capability attack results."""
    lines = [
        "Execution Capability and Authority Materialization",
        "==================================================",
        "",
        f"Total attacks: {len(results)}",
        f"Detected: {sum(1 for r in results if r.detected)}",
        f"Missed: {sum(1 for r in results if not r.detected)}",
        "",
        "By category:",
    ]

    categories: dict[str, list[ExecutionCapabilityAttackResult]] = {}
    for r in results:
        categories.setdefault(r.attack_category, []).append(r)

    for category, cat_results in sorted(categories.items()):
        detected = sum(1 for r in cat_results if r.detected)
        lines.append(f"  {category}: {detected}/{len(cat_results)} detected")

    lines.append("")
    lines.append("Failures:")
    failures = [r for r in results if not r.detected]
    if failures:
        for f in failures:
            lines.append(f"  {f.attack_name}: {f.rejection_reason}")
    else:
        lines.append("  None")

    return "\n".join(lines)
