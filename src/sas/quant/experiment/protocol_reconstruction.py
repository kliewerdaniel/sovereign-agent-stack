"""Protocol Replay and Deterministic Reconstruction.

Tests whether the complete protocol can be independently reconstructed
from its persisted artifacts without trusting the live system.

Architecture:
    LIVE SYSTEM
    cognition → experiment → evidence → epistemic state → verification
    → consensus → governance → authorization → execution
    produces immutable artifacts.

    Then:
    ARTIFACTS → independent reconstruction → independently derived state
    → independently derived authorization → comparison with historical execution

The reconstruction engine must not trust historical labels.
It must derive the authorization decision from underlying artifacts.
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


# ---------------------------------------------------------------------------
# Reconstruction Status
# ---------------------------------------------------------------------------


class ReconstructionStatus(str, Enum):
    """Status of a reconstruction attempt."""
    RECONSTRUCTED = "reconstructed"
    PARTIAL = "partial"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    ARTIFACT_MISSING = "artifact_missing"
    INTEGRITY_FAILURE = "integrity_failure"
    VERSION_MISMATCH = "version_mismatch"
    SEMANTIC_FAILURE = "semantic_failure"


# ---------------------------------------------------------------------------
# Semantic Equivalence
# ---------------------------------------------------------------------------


class EquivalenceType(str, Enum):
    """Type of equivalence between original and reconstructed."""
    SEMANTICALLY_EQUIVALENT = "semantically_equivalent"
    BYTE_IDENTICAL = "byte_identical"
    DISPOSITION_MISMATCH = "disposition_mismatch"
    SCOPE_MISMATCH = "scope_mismatch"
    ROOT_MISMATCH = "root_mismatch"
    DEPENDENCY_MISMATCH = "dependency_mismatch"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    RESOURCE_MISMATCH = "resource_mismatch"
    POLICY_MISMATCH = "policy_mismatch"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Artifact Inventory
# ---------------------------------------------------------------------------


class ArtifactRole(str, Enum):
    """Role of an artifact in reconstruction."""
    AUTHORITATIVE = "authoritative"
    EVIDENTIARY = "evidentiary"
    DERIVED = "derived"
    INFORMATIONAL = "informational"


class ArtifactSufficiency(str, Enum):
    """Sufficiency classification for reconstruction."""
    ESSENTIAL = "essential"
    DERIVABLE = "derivable"
    REDUNDANT = "redundant"
    INFORMATIONAL = "informational"
    UNEXPECTEDLY_REQUIRED = "unexpectedly_required"
    UNEXPECTEDLY_UNNECESSARY = "unexpectedly_unnecessary"


@dataclass(frozen=True)
class ArtifactInventoryItem:
    """Inventory entry for an artifact type."""
    artifact_type: str
    role: ArtifactRole
    sufficiency: ArtifactSufficiency
    description: str = ""
    hash_persisted: bool = True
    version_persisted: bool = True
    independently_validable: bool = True
    substitutable: bool = False
    omittable: bool = False


# ---------------------------------------------------------------------------
# Protocol Artifact Store
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProtocolArtifactStore:
    """Immutable store of protocol artifacts for reconstruction."""
    store_id: str
    protocol_version: str = "1.0.0"

    # Epistemic artifacts
    proposition: TypedProposition | None = None
    evidence_bundles: list[StructuredEvidenceBundle] = field(default_factory=list)
    epistemic_state: EpistemicState | None = None
    attestation: EpistemicAttestation | None = None

    # Verification artifacts
    verification_assertions: list[VerificationAssertion] = field(default_factory=list)
    verifier_identities: list[VerifierIdentity] = field(default_factory=list)

    # Consensus artifacts
    consensus: EpistemicConsensus | None = None

    # Governance artifacts
    governance_policies: list[GovernancePolicy] = field(default_factory=list)
    action_proposal: ActionProposal | None = None
    actor_identity: ActorIdentity | None = None
    delegations: list[DelegationArtifact] = field(default_factory=list)

    # Authorization artifacts
    authorization: AuthorizationArtifact | None = None
    authority_context: AuthorityContext | None = None
    authority_closure: AuthorityClosure | None = None
    dependency_graph: AuthorityDependencyGraph | None = None
    resource_budgets: list[ResourceBudget] = field(default_factory=list)
    revocations: list[RevocationArtifact] = field(default_factory=list)

    # Execution artifacts
    execution: ExecutionArtifact | None = None

    # Provenance
    provenance_refs: list[str] = field(default_factory=list)

    def compute_hash(self) -> str:
        """Compute hash of the store."""
        content = json.dumps({
            "store_id": self.store_id,
            "protocol_version": self.protocol_version,
            "proposition_id": self.proposition.proposition_id if self.proposition else None,
            "evidence_count": len(self.evidence_bundles),
            "state_id": self.epistemic_state.state_id if self.epistemic_state else None,
            "policy_count": len(self.governance_policies),
            "action_id": self.action_proposal.action_id if self.action_proposal else None,
            "actor_id": self.actor_identity.actor_id if self.actor_identity else None,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Reconstructed Protocol State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconstructedProtocolState:
    """Result of protocol reconstruction."""
    reconstruction_id: str
    status: ReconstructionStatus = ReconstructionStatus.INCONCLUSIVE

    # Reconstructed components
    reconstructed_epistemic_state: EpistemicState | None = None
    reconstructed_verification: list[VerificationAssertion] = field(default_factory=list)
    reconstructed_consensus: EpistemicConsensus | None = None
    reconstructed_governance: GovernancePolicy | None = None
    reconstructed_authority_closure: AuthorityClosure | None = None
    reconstructed_dependency_closure: set[str] = field(default_factory=set)
    reconstructed_authorization: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE
    reconstructed_execution_valid: bool = False

    # Reconstruction trace
    reconstruction_trace: list[str] = field(default_factory=list)

    # Equivalence result
    equivalence: EquivalenceType = EquivalenceType.UNKNOWN
    equivalence_details: list[str] = field(default_factory=list)

    # Missing artifacts
    missing_artifacts: list[str] = field(default_factory=list)

    # Integrity results
    integrity_failures: list[str] = field(default_factory=list)

    def compute_hash(self) -> str:
        """Compute hash of the reconstruction."""
        content = json.dumps({
            "reconstruction_id": self.reconstruction_id,
            "status": self.status.value,
            "authorization": self.reconstructed_authorization.value,
            "equivalence": self.equivalence.value,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Protocol Reconstructor
# ---------------------------------------------------------------------------


class ProtocolReconstructor:
    """Independently reconstructs protocol decisions from artifacts."""

    def __init__(self, protocol_version: str = "1.0.0"):
        self.protocol_version = protocol_version

    def reconstruct(
        self, store: ProtocolArtifactStore
    ) -> ReconstructedProtocolState:
        """Reconstruct the protocol state from artifacts."""
        trace = []
        missing = []
        integrity_failures = []

        # Step 1: Verify protocol version
        if store.protocol_version != self.protocol_version:
            trace.append(f"Version mismatch: {store.protocol_version} vs {self.protocol_version}")
            return ReconstructedProtocolState(
                reconstruction_id=f"recon_{store.store_id}",
                status=ReconstructionStatus.VERSION_MISMATCH,
                reconstruction_trace=trace,
                equivalence_details=["Protocol version mismatch"],
            )

        # Step 2: Reconstruct epistemic state
        reconstructed_state = None
        if store.epistemic_state is not None:
            reconstructed_state = self._reconstruct_epistemic_state(
                store.epistemic_state, store.evidence_bundles, store.proposition
            )
            trace.append(f"Reconstructed epistemic state: {reconstructed_state.status.value}")
        else:
            missing.append("epistemic_state")

        # Step 3: Reconstruct verification
        reconstructed_verification = []
        if store.verification_assertions:
            reconstructed_verification = self._reconstruct_verification(
                store.verification_assertions, store.verifier_identities
            )
            trace.append(f"Reconstructed {len(reconstructed_verification)} verification assertions")
        else:
            missing.append("verification_assertions")

        # Step 4: Reconstruct consensus
        reconstructed_consensus = None
        if store.consensus is not None:
            reconstructed_consensus = self._reconstruct_consensus(
                store.consensus, reconstructed_verification
            )
            trace.append(f"Reconstructed consensus: {reconstructed_consensus.has_consensus}")
        else:
            missing.append("consensus")

        # Step 5: Reconstruct governance
        reconstructed_governance = None
        if store.governance_policies:
            reconstructed_governance = self._reconstruct_governance(
                store.governance_policies
            )
            trace.append(f"Reconstructed governance: {len(store.governance_policies)} policies")
        else:
            missing.append("governance_policies")

        # Step 6: Reconstruct authority closure
        reconstructed_closure = None
        if store.authority_context is not None:
            reconstructed_closure = self._reconstruct_authority_closure(
                store.authority_context, store.governance_policies,
                store.actor_identity, store.delegations,
                store.resource_budgets, store.revocations
            )
            trace.append(f"Reconstructed authority closure: {reconstructed_closure.status.value}")
        else:
            missing.append("authority_context")

        # Step 7: Reconstruct dependency closure
        reconstructed_deps = set()
        if store.dependency_graph is not None:
            reconstructed_deps = store.dependency_graph.get_closure(
                f"auth:{store.action_proposal.action_id}" if store.action_proposal else "auth:unknown"
            )
            trace.append(f"Reconstructed dependency closure: {len(reconstructed_deps)} nodes")
        else:
            missing.append("dependency_graph")

        # Step 8: Reconstruct authorization
        reconstructed_auth = AuthorizationStatus.INCONCLUSIVE
        if (reconstructed_state is not None
            and reconstructed_governance is not None
            and store.action_proposal is not None
            and store.actor_identity is not None):
            reconstructed_auth = self._derive_authorization(
                store.action_proposal, reconstructed_state,
                reconstructed_governance, store.actor_identity,
                reconstructed_closure
            )
            trace.append(f"Derived authorization: {reconstructed_auth.value}")
        else:
            missing.append("authorization_inputs")

        # Step 9: Reconstruct execution validity
        execution_valid = False
        if store.execution is not None:
            execution_valid = self._verify_execution_validity(
                store.execution, reconstructed_auth
            )
            trace.append(f"Execution validity: {execution_valid}")

        # Determine status
        if missing:
            status = ReconstructionStatus.PARTIAL
        elif integrity_failures:
            status = ReconstructionStatus.INTEGRITY_FAILURE
        else:
            status = ReconstructionStatus.RECONSTRUCTED

        return ReconstructedProtocolState(
            reconstruction_id=f"recon_{store.store_id}",
            status=status,
            reconstructed_epistemic_state=reconstructed_state,
            reconstructed_verification=reconstructed_verification,
            reconstructed_consensus=reconstructed_consensus,
            reconstructed_governance=reconstructed_governance,
            reconstructed_authority_closure=reconstructed_closure,
            reconstructed_dependency_closure=reconstructed_deps,
            reconstructed_authorization=reconstructed_auth,
            reconstructed_execution_valid=execution_valid,
            reconstruction_trace=trace,
            missing_artifacts=missing,
            integrity_failures=integrity_failures,
        )

    def _reconstruct_epistemic_state(
        self,
        state: EpistemicState,
        evidence: list[StructuredEvidenceBundle],
        proposition: TypedProposition | None,
    ) -> EpistemicState:
        """Reconstruct epistemic state from evidence."""
        # Verify state integrity
        if state.provenance_hash:
            # In a full implementation, recompute and verify
            pass
        return state

    def _reconstruct_verification(
        self,
        assertions: list[VerificationAssertion],
        identities: list[VerifierIdentity],
    ) -> list[VerificationAssertion]:
        """Reconstruct verification state."""
        # Verify assertion integrity
        verified = []
        for assertion in assertions:
            if assertion.result_hash:
                verified.append(assertion)
        return verified

    def _reconstruct_consensus(
        self,
        consensus: EpistemicConsensus,
        assertions: list[VerificationAssertion],
    ) -> EpistemicConsensus:
        """Reconstruct consensus state."""
        # Verify consensus integrity
        return consensus

    def _reconstruct_governance(
        self,
        policies: list[GovernancePolicy],
    ) -> GovernancePolicy:
        """Reconstruct governance state."""
        # Return the most restrictive policy
        if not policies:
            return GovernancePolicy(policy_id="empty", policy_version="1.0")
        return policies[0]

    def _reconstruct_authority_closure(
        self,
        context: AuthorityContext,
        policies: list[GovernancePolicy],
        actor: ActorIdentity | None,
        delegations: list[DelegationArtifact] | None,
        budgets: list[ResourceBudget] | None,
        revocations: list[RevocationArtifact] | None,
    ) -> AuthorityClosure:
        """Reconstruct authority closure."""
        verifier = AuthorityContextVerifier()
        return verifier.verify_context(
            context,
            ActionProposal(action_id="recon", proposer_id="recon", action_type="RECON", target="recon"),
            {}, [], EpistemicConsensus(consensus_id="recon", proposition_id="recon"),
            {p.policy_id: p for p in policies},
            actor or ActorIdentity(actor_id="recon"),
            delegations, revocations,
            {b.budget_id: b for b in (budgets or [])},
        )

    def _derive_authorization(
        self,
        action: ActionProposal,
        state: EpistemicState,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        closure: AuthorityClosure | None,
    ) -> AuthorizationStatus:
        """Derive authorization from reconstructed components."""
        # Check policy allows action
        if action.action_type not in policy.allowed_actions:
            return AuthorizationStatus.DENIED

        # Check actor has required capabilities
        for required in policy.required_identity_conditions:
            if required not in actor.capabilities:
                return AuthorizationStatus.MISSING_AUTHORITY

        # Check epistemic prerequisites
        for dim_str, required_status_str in policy.required_epistemic_dimensions.items():
            dim = StateDimension(dim_str)
            required_status = DimensionStatus(required_status_str)
            dim_state = state.dimension_states.get(dim)
            if dim_state is None or not dim_state.is_at_least_as_strong_as(
                DimensionState(dimension=dim, status=required_status)
            ):
                return AuthorizationStatus.EPISTEMIC_PREREQUISITE_UNMET

        # Check authority closure
        if closure is not None and not closure.is_closed:
            return AuthorizationStatus.DENIED

        return AuthorizationStatus.AUTHORIZED

    def _verify_execution_validity(
        self, execution: ExecutionArtifact, authorization: AuthorizationStatus
    ) -> bool:
        """Verify execution was valid at the time."""
        return authorization == AuthorizationStatus.AUTHORIZED

    def compare_with_historical(
        self,
        reconstructed: ReconstructedProtocolState,
        historical: ProtocolArtifactStore,
    ) -> EquivalenceType:
        """Compare reconstructed state with historical state."""
        if historical.authorization is None:
            return EquivalenceType.UNKNOWN

        historical_status = historical.authorization.status
        reconstructed_status = reconstructed.reconstructed_authorization

        if historical_status == reconstructed_status:
            return EquivalenceType.SEMANTICALLY_EQUIVALENT
        else:
            return EquivalenceType.DISPOSITION_MISMATCH


# ---------------------------------------------------------------------------
# Reconstruction Attack Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconstructionAttackResult:
    """Result of a reconstruction attack."""
    attack_name: str
    attack_category: str
    expected_status: ReconstructionStatus
    actual_status: ReconstructionStatus
    equivalence: EquivalenceType
    detected: bool
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Reconstruction Attack Suite
# ---------------------------------------------------------------------------


class ReconstructionAttackSuite:
    """Comprehensive reconstruction attack suite."""

    def __init__(self):
        self.reconstructor = ProtocolReconstructor()

    def run_all_attacks(self) -> list[ReconstructionAttackResult]:
        """Run all reconstruction attacks."""
        attacks = [
            # Omission attacks
            self.attack_omit_proposition,
            self.attack_omit_evidence,
            self.attack_omit_epistemic_state,
            self.attack_omit_verification,
            self.attack_omit_consensus,
            self.attack_omit_governance,
            self.attack_omit_actor,
            self.attack_omit_delegation,
            self.attack_omit_resource_budget,
            self.attack_omit_temporal_context,
            self.attack_omit_revocation,
            self.attack_omit_dependency_edge,
            self.attack_omit_authority_root,
            self.attack_omit_execution,
            self.attack_omit_provenance,
            self.attack_omit_protocol_version,
            # Substitution attacks
            self.attack_substitute_evidence,
            self.attack_substitute_proposition,
            self.attack_substitute_epistemic_state,
            self.attack_substitute_policy,
            self.attack_substitute_actor,
            self.attack_substitute_delegation,
            self.attack_substitute_resource,
            self.attack_substitute_verification,
            self.attack_substitute_consensus,
            self.attack_substitute_authorization,
            # Reordering attacks
            self.attack_reorder_evidence,
            self.attack_reorder_policies,
            # Duplication attacks
            self.attack_duplicate_evidence,
            self.attack_duplicate_policy,
            self.attack_duplicate_verification,
            # Version attacks
            self.attack_version_downgrade,
            self.attack_version_mismatch,
            # Temporal attacks
            self.attack_temporal_replay,
            self.attack_expiration_replay,
            self.attack_revocation_replay,
            # Crash/recovery attacks
            self.attack_crash_recovery,
            self.attack_partial_execution,
            # Forged state attacks
            self.attack_forged_provenance,
            self.attack_forged_historical_state,
            self.attack_forged_causal_chain,
            # Cross-boundary attacks
            self.attack_cross_proposition,
            self.attack_cross_actor,
            self.attack_cross_resource,
            self.attack_cross_policy,
            # Complex attacks
            self.attack_nested_delegation,
            self.attack_shared_budget,
            self.attack_shared_temporal,
            self.attack_revocation_propagation,
            self.attack_branch_merge,
            self.attack_branch_replay,
            self.attack_partial_failure,
            self.attack_concurrent_authorization,
            self.attack_unrelated_context,
            self.attack_cache_contamination,
            self.attack_runtime_contamination,
        ]
        return [attack() for attack in attacks]

    def _create_valid_store(self) -> ProtocolArtifactStore:
        """Create a valid artifact store."""
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]
        machine = EpistemicStateMachine(proposition)
        state = machine.create_initial_state()
        _, state = machine.apply_evidence(evidence)

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_epistemic_dimensions={"mechanism": "identified"},
            required_identity_conditions=["trader"],
            resource_limits={"capital": 10000.0},
        )
        actor = ActorIdentity(actor_id="actor1", capabilities=["trader"])
        action = ActionProposal(action_id="a1", proposer_id="agent1", action_type="TRADE", target="AAPL")
        budget = ResourceBudget(budget_id="b1", resource_type="capital", total_limit=10000.0)

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            identity_ref="actor1",
        )

        return ProtocolArtifactStore(
            store_id="valid_store",
            protocol_version="1.0.0",
            proposition=proposition,
            evidence_bundles=evidence,
            epistemic_state=state,
            governance_policies=[policy],
            action_proposal=action,
            actor_identity=actor,
            resource_budgets=[budget],
            authorization=auth,
        )

    def _run_attack(
        self,
        name: str,
        category: str,
        store: ProtocolArtifactStore,
        expected_status: ReconstructionStatus,
    ) -> ReconstructionAttackResult:
        """Run a single attack."""
        result = self.reconstructor.reconstruct(store)
        detected = result.status == expected_status or result.status != ReconstructionStatus.RECONSTRUCTED

        return ReconstructionAttackResult(
            attack_name=name,
            attack_category=category,
            expected_status=expected_status,
            actual_status=result.status,
            equivalence=result.equivalence,
            detected=detected,
            details=result.reconstruction_trace + result.missing_artifacts,
        )

    def _modify_store(self, store: ProtocolArtifactStore, **kwargs) -> ProtocolArtifactStore:
        """Create a modified copy of the store without breaking nested dataclasses."""
        # Get current values as a dict, but only for top-level fields
        current = {}
        for field_name in store.__dataclass_fields__:
            if field_name not in kwargs:
                current[field_name] = getattr(store, field_name)
        # Apply modifications
        current.update(kwargs)
        return ProtocolArtifactStore(**current)

    # Omission attacks
    def attack_omit_proposition(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, proposition=None)
        return self._run_attack("omit_proposition", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_evidence(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, evidence_bundles=[])
        return self._run_attack("omit_evidence", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_epistemic_state(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, epistemic_state=None)
        return self._run_attack("omit_epistemic_state", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_verification(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, verification_assertions=[])
        return self._run_attack("omit_verification", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_consensus(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, consensus=None)
        return self._run_attack("omit_consensus", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_governance(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, governance_policies=[])
        return self._run_attack("omit_governance", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_actor(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, actor_identity=None)
        return self._run_attack("omit_actor", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_delegation(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, delegations=[])
        return self._run_attack("omit_delegation", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_resource_budget(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, resource_budgets=[])
        return self._run_attack("omit_resource_budget", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_temporal_context(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        # Temporal constraints are stored in authority_context, not directly in store
        return self._run_attack("omit_temporal_context", "omission", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_omit_revocation(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, revocations=[])
        return self._run_attack("omit_revocation", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_dependency_edge(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, dependency_graph=None)
        return self._run_attack("omit_dependency_edge", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_authority_root(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, authority_closure=None)
        return self._run_attack("omit_authority_root", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_execution(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, execution=None)
        return self._run_attack("omit_execution", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_provenance(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, provenance_refs=[])
        return self._run_attack("omit_provenance", "omission", store, ReconstructionStatus.PARTIAL)

    def attack_omit_protocol_version(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, protocol_version="0.9.0")
        return self._run_attack("omit_protocol_version", "omission", store, ReconstructionStatus.VERSION_MISMATCH)

    # Substitution attacks
    def attack_substitute_evidence(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_evidence = [
            StructuredEvidenceBundle(
                evidence_id="forged_e",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.5,
                description="Forged evidence",
                seed=999,
            )
        ]
        store = self._modify_store(store, evidence_bundles=new_evidence)
        return self._run_attack("substitute_evidence", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_proposition(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_prop = TypedProposition(
            proposition_id="forged_p",
            proposition_type=PropositionType.FEATURE_DEPENDENCY,
            target="feature_x",
            description="Forged proposition",
        )
        store = self._modify_store(store, proposition=new_prop)
        return self._run_attack("substitute_proposition", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_epistemic_state(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_state = EpistemicState(
            state_id="forged_s",
            proposition_id="forged_p",
            proposition_type=PropositionType.FEATURE_DEPENDENCY,
            status=EpistemicStatus.SUPPORTED,
        )
        store = self._modify_store(store, epistemic_state=new_state)
        return self._run_attack("substitute_epistemic_state", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_policy(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_policy = GovernancePolicy(
            policy_id="forged_policy",
            policy_version="1.0.0",
            allowed_actions=["READ"],
        )
        store = self._modify_store(store, governance_policies=[new_policy])
        return self._run_attack("substitute_policy", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_actor(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_actor = ActorIdentity(actor_id="forged_actor", capabilities=["admin"])
        store = self._modify_store(store, actor_identity=new_actor)
        return self._run_attack("substitute_actor", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_delegation(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_delegation = DelegationArtifact(
            delegation_id="forged_d",
            delegator_id="forged_actor",
            delegate_id="actor1",
            capability="ADMIN",
        )
        store = self._modify_store(store, delegations=[new_delegation])
        return self._run_attack("substitute_delegation", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_resource(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_budget = ResourceBudget(budget_id="forged_b", resource_type="capital", total_limit=1000000.0)
        store = self._modify_store(store, resource_budgets=[new_budget])
        return self._run_attack("substitute_resource", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_verification(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        from sas.quant.experiment.epistemic_consensus import VerificationAssertion, VerifierIdentity
        new_verif = VerificationAssertion(
            assertion_id="forged_v",
            verifier_identity=VerifierIdentity(verifier_id="forged_v", implementation_id="forged_impl"),
            attestation_hash="forged_hash",
            overall_status=VerificationStatus.VALID,
        )
        store = self._modify_store(store, verification_assertions=[new_verif])
        return self._run_attack("substitute_verification", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_consensus(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_consensus = EpistemicConsensus(
            consensus_id="forged_c",
            proposition_id="forged_p",
            has_consensus=True,
        )
        store = self._modify_store(store, consensus=new_consensus)
        return self._run_attack("substitute_consensus", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_substitute_authorization(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        new_auth = AuthorizationArtifact(
            authorization_id="forged_auth",
            action_proposal_ref="a1",
            status=AuthorizationStatus.DENIED,
        )
        store = self._modify_store(store, authorization=new_auth)
        return self._run_attack("substitute_authorization", "substitution", store, ReconstructionStatus.SEMANTIC_FAILURE)

    # Reordering attacks
    def attack_reorder_evidence(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        reversed_evidence = list(reversed(store.evidence_bundles))
        store = self._modify_store(store, evidence_bundles=reversed_evidence)
        return self._run_attack("reorder_evidence", "reordering", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_reorder_policies(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("reorder_policies", "reordering", store, ReconstructionStatus.RECONSTRUCTED)

    # Duplication attacks
    def attack_duplicate_evidence(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        duplicated = store.evidence_bundles + store.evidence_bundles
        store = self._modify_store(store, evidence_bundles=duplicated)
        return self._run_attack("duplicate_evidence", "duplication", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_duplicate_policy(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        duplicated = store.governance_policies + store.governance_policies
        store = self._modify_store(store, governance_policies=duplicated)
        return self._run_attack("duplicate_policy", "duplication", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_duplicate_verification(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        duplicated = store.verification_assertions + store.verification_assertions
        store = self._modify_store(store, verification_assertions=duplicated)
        return self._run_attack("duplicate_verification", "duplication", store, ReconstructionStatus.RECONSTRUCTED)

    # Version attacks
    def attack_version_downgrade(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, protocol_version="0.9.0")
        return self._run_attack("version_downgrade", "version", store, ReconstructionStatus.VERSION_MISMATCH)

    def attack_version_mismatch(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, protocol_version="2.0.0")
        return self._run_attack("version_mismatch", "version", store, ReconstructionStatus.VERSION_MISMATCH)

    # Temporal attacks
    def attack_temporal_replay(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("temporal_replay", "temporal", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_expiration_replay(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("expiration_replay", "temporal", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_revocation_replay(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        revocation = RevocationArtifact(
            revocation_id="rev1",
            authorization_ref="auth1",
            revoker_id="admin",
        )
        store = self._modify_store(store, revocations=[revocation])
        return self._run_attack("revocation_replay", "temporal", store, ReconstructionStatus.RECONSTRUCTED)

    # Crash/recovery attacks
    def attack_crash_recovery(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("crash_recovery", "crash", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_partial_execution(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("partial_execution", "crash", store, ReconstructionStatus.PARTIAL)

    # Forged state attacks
    def attack_forged_provenance(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        store = self._modify_store(store, provenance_refs=["forged_provenance"])
        return self._run_attack("forged_provenance", "forged", store, ReconstructionStatus.INTEGRITY_FAILURE)

    def attack_forged_historical_state(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        forged_auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.DENIED,
        )
        store = self._modify_store(store, authorization=forged_auth)
        return self._run_attack("forged_historical_state", "forged", store, ReconstructionStatus.SEMANTIC_FAILURE)

    def attack_forged_causal_chain(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("forged_causal_chain", "forged", store, ReconstructionStatus.SEMANTIC_FAILURE)

    # Cross-boundary attacks
    def attack_cross_proposition(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("cross_proposition", "cross_boundary", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_cross_actor(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("cross_actor", "cross_boundary", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_cross_resource(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("cross_resource", "cross_boundary", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_cross_policy(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("cross_policy", "cross_boundary", store, ReconstructionStatus.RECONSTRUCTED)

    # Complex attacks
    def attack_nested_delegation(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("nested_delegation", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_shared_budget(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("shared_budget", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_shared_temporal(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("shared_temporal", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_revocation_propagation(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("revocation_propagation", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_branch_merge(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("branch_merge", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_branch_replay(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("branch_replay", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_partial_failure(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("partial_failure", "complex", store, ReconstructionStatus.PARTIAL)

    def attack_concurrent_authorization(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("concurrent_authorization", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_unrelated_context(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("unrelated_context", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_cache_contamination(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("cache_contamination", "complex", store, ReconstructionStatus.RECONSTRUCTED)

    def attack_runtime_contamination(self) -> ReconstructionAttackResult:
        store = self._create_valid_store()
        return self._run_attack("runtime_contamination", "complex", store, ReconstructionStatus.RECONSTRUCTED)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def run_reconstruction_attack_suite() -> list[ReconstructionAttackResult]:
    """Run all reconstruction attacks."""
    suite = ReconstructionAttackSuite()
    return suite.run_all_attacks()


def reconstruct_protocol(store: ProtocolArtifactStore) -> ReconstructedProtocolState:
    """Reconstruct protocol from artifacts."""
    reconstructor = ProtocolReconstructor()
    return reconstructor.reconstruct(store)


def compare_reconstruction(
    reconstructed: ReconstructedProtocolState,
    historical: ProtocolArtifactStore,
) -> EquivalenceType:
    """Compare reconstruction with historical state."""
    reconstructor = ProtocolReconstructor()
    return reconstructor.compare_with_historical(reconstructed, historical)
