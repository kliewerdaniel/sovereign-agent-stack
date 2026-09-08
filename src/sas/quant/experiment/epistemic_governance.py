"""Epistemic Governance and Authorization Derivation.

Implements the architectural boundary between epistemic authority and
execution authority.

The central research question:
    Can governance and authorization themselves be made independently
    derivable, provenance-backed, and resistant to authority escalation?

Architecture:
    Agent proposes
          ↓
    Evidence constrains
          ↓
    Epistemic state establishes what is known
          ↓
    Independent verification establishes what was actually established
          ↓
    Governance evaluates policy
          ↓
    Authorization is derived
          ↓
    Execution protocol verifies authorization
          ↓
    Action occurs

The agent must never be the authority root.

Invariants:
    MODEL OUTPUT ≠ EVIDENCE
    EVIDENCE ≠ EPISTEMIC STATE
    EPISTEMIC STATE ≠ VERIFICATION
    VERIFICATION ≠ CONSENSUS
    CONSENSUS ≠ GOVERNANCE
    GOVERNANCE ≠ AUTHORIZATION
    AUTHORIZATION ≠ EXECUTION
    EXECUTION ≠ EVIDENCE OF AUTHORIZATION

    No component becomes authoritative merely because it produced a
    plausible result. Authority must be derived through an explicit,
    provenance-backed transition across the appropriate boundary.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Authorization Status
# ---------------------------------------------------------------------------


class AuthorizationStatus(str, Enum):
    """Status of an authorization derivation."""
    AUTHORIZED = "authorized"
    DENIED = "denied"
    INCONCLUSIVE = "inconclusive"
    EXPIRED = "expired"
    SCOPE_MISMATCH = "scope_mismatch"
    MISSING_AUTHORITY = "missing_authority"
    POLICY_CONFLICT = "policy_conflict"
    EPISTEMIC_PREREQUISITE_UNMET = "epistemic_prerequisite_unmet"
    VERIFICATION_CONFLICT = "verification_conflict"
    PROVENANCE_INVALID = "provenance_invalid"
    REVOKED = "revoked"
    ACTOR_MISMATCH = "actor_mismatch"
    CAPABILITY_MISSING = "capability_missing"
    RESOURCE_CONSTRAINT_VIOLATION = "resource_constraint_violation"
    TEMPORAL_CONSTRAINT_VIOLATION = "temporal_constraint_violation"


# ---------------------------------------------------------------------------
# Action Proposal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionProposal:
    """Typed representation of an action request.

    An action proposal is NOT authorization. It is merely:
    > Someone is asking to perform this action.

    The proposer may be an agent. The proposer must never become
    authoritative merely by creating the proposal.
    """
    action_id: str
    proposer_id: str
    action_type: str
    target: str
    parameters: dict = field(default_factory=dict)
    required_capabilities: list[str] = field(default_factory=list)
    epistemic_dependencies: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    requested_scope: dict = field(default_factory=dict)
    requested_resources: dict = field(default_factory=dict)
    requested_time_window: tuple[str, str] = ("", "")
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the proposal."""
        content = json.dumps({
            "action_id": self.action_id,
            "proposer_id": self.proposer_id,
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
            "required_capabilities": sorted(self.required_capabilities),
            "epistemic_dependencies": sorted(self.epistemic_dependencies),
            "evidence_refs": sorted(self.evidence_refs),
            "requested_scope": self.requested_scope,
            "requested_resources": self.requested_resources,
            "requested_time_window": self.requested_time_window,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Recommendation Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecommendationArtifact:
    """A recommendation from an agent or model.

    A recommendation is NOT authorization. It is merely:
    > The agent suggests this action.

    Recommendation does not imply authorization.
    """
    recommendation_id: str
    proposer_id: str
    action_type: str
    target: str
    confidence: float = 0.0
    reasoning: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the recommendation."""
        content = json.dumps({
            "recommendation_id": self.recommendation_id,
            "proposer_id": self.proposer_id,
            "action_type": self.action_type,
            "target": self.target,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence_refs": sorted(self.evidence_refs),
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Governance Policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GovernancePolicy:
    """Immutable governance policy.

    The policy establishes the conditions under which authorization
    may be derived. It does NOT automatically grant authorization.

    Policy is immutable. Changing policy creates a new policy artifact.
    Historical policy is never mutated.
    """
    policy_id: str
    policy_version: str
    jurisdiction: str = ""
    allowed_actions: list[str] = field(default_factory=list)
    prohibited_actions: list[str] = field(default_factory=list)
    required_epistemic_dimensions: dict[str, str] = field(default_factory=dict)
    required_verification_conditions: list[str] = field(default_factory=list)
    required_identity_conditions: list[str] = field(default_factory=list)
    resource_limits: dict[str, float] = field(default_factory=dict)
    temporal_constraints: dict[str, str] = field(default_factory=dict)
    escalation_requirements: list[str] = field(default_factory=list)
    expiration: str = ""
    provenance_hash: str = ""
    semantic_version: str = "1.0.0"

    def compute_hash(self) -> str:
        """Compute hash of the policy."""
        content = json.dumps({
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "jurisdiction": self.jurisdiction,
            "allowed_actions": sorted(self.allowed_actions),
            "prohibited_actions": sorted(self.prohibited_actions),
            "required_epistemic_dimensions": self.required_epistemic_dimensions,
            "required_verification_conditions": sorted(self.required_verification_conditions),
            "required_identity_conditions": sorted(self.required_identity_conditions),
            "resource_limits": self.resource_limits,
            "temporal_constraints": self.temporal_constraints,
            "escalation_requirements": sorted(self.escalation_requirements),
            "expiration": self.expiration,
            "semantic_version": self.semantic_version,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authorization Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorizationArtifact:
    """Derived artifact representing authorization.

    Authorization must contain the derivation basis, not just a boolean.

    The executor must be able to independently verify this authorization
    from its underlying components.
    """
    authorization_id: str
    action_proposal_ref: str
    proposition_refs: list[str] = field(default_factory=list)
    epistemic_state_refs: list[str] = field(default_factory=list)
    verification_assertion_refs: list[str] = field(default_factory=list)
    consensus_conflict_refs: list[str] = field(default_factory=list)
    governance_policy_ref: str = ""
    policy_version: str = ""
    identity_ref: str = ""
    capability_refs: list[str] = field(default_factory=list)
    resource_constraints: dict[str, float] = field(default_factory=dict)
    temporal_constraints: dict[str, str] = field(default_factory=dict)
    authorization_scope: dict = field(default_factory=dict)
    derivation_trace: list[str] = field(default_factory=list)
    expiration: str = ""
    provenance_hash: str = ""
    derivation_hash: str = ""
    status: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE

    def compute_hash(self) -> str:
        """Compute hash of the authorization."""
        content = json.dumps({
            "authorization_id": self.authorization_id,
            "action_proposal_ref": self.action_proposal_ref,
            "proposition_refs": sorted(self.proposition_refs),
            "epistemic_state_refs": sorted(self.epistemic_state_refs),
            "verification_assertion_refs": sorted(self.verification_assertion_refs),
            "consensus_conflict_refs": sorted(self.consensus_conflict_refs),
            "governance_policy_ref": self.governance_policy_ref,
            "policy_version": self.policy_version,
            "identity_ref": self.identity_ref,
            "capability_refs": sorted(self.capability_refs),
            "resource_constraints": self.resource_constraints,
            "temporal_constraints": self.temporal_constraints,
            "authorization_scope": self.authorization_scope,
            "derivation_trace": self.derivation_trace,
            "expiration": self.expiration,
            "status": self.status.value,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Revocation Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RevocationArtifact:
    """Immutable revocation of an authorization.

    Revocation does NOT mutate the original authorization. It creates
    a new artifact that references the original.
    """
    revocation_id: str
    authorization_ref: str
    revoker_id: str
    reason: str = ""
    scope: dict = field(default_factory=dict)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the revocation."""
        content = json.dumps({
            "revocation_id": self.revocation_id,
            "authorization_ref": self.authorization_ref,
            "revoker_id": self.revoker_id,
            "reason": self.reason,
            "scope": self.scope,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Execution Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionArtifact:
    """Immutable record of an executed action.

    Execution does NOT retroactively establish authorization.
    Outcome ≠ authorization.
    """
    execution_id: str
    action_type: str
    target: str
    actor_id: str
    authorization_ref: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = ""
    result: str = ""
    result_details: dict = field(default_factory=dict)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the execution."""
        content = json.dumps({
            "execution_id": self.execution_id,
            "action_type": self.action_type,
            "target": self.target,
            "actor_id": self.actor_id,
            "authorization_ref": self.authorization_ref,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
            "result": self.result,
            "result_details": self.result_details,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Identity / Capability
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActorIdentity:
    """Identity of an actor with capabilities."""
    actor_id: str
    capabilities: list[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the identity."""
        content = json.dumps({
            "actor_id": self.actor_id,
            "capabilities": sorted(self.capabilities),
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authorization Derivation
# ---------------------------------------------------------------------------


class AuthorizationDerivation:
    """Derives authorization from epistemic state, policy, and constraints."""

    def derive_authorization(
        self,
        action_proposal: ActionProposal,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        current_time: str = "",
    ) -> AuthorizationArtifact:
        """Derive authorization from components."""
        derivation_trace = []
        status = AuthorizationStatus.INCONCLUSIVE

        # Step 1: Check if action is prohibited
        if action_proposal.action_type in policy.prohibited_actions:
            status = AuthorizationStatus.DENIED
            derivation_trace.append(f"Action {action_proposal.action_type} is prohibited")
            return self._create_authorization(
                action_proposal, epistemic_states, verification_assertions,
                consensus, policy, actor, status, derivation_trace,
            )

        # Step 2: Check if action is allowed
        if action_proposal.action_type not in policy.allowed_actions:
            status = AuthorizationStatus.DENIED
            derivation_trace.append(f"Action {action_proposal.action_type} is not in allowed actions")
            return self._create_authorization(
                action_proposal, epistemic_states, verification_assertions,
                consensus, policy, actor, status, derivation_trace,
            )

        derivation_trace.append(f"Action {action_proposal.action_type} is allowed")

        # Step 3: Check epistemic prerequisites
        for dim_str, required_status_str in policy.required_epistemic_dimensions.items():
            dim = StateDimension(dim_str)
            required_status = DimensionStatus(required_status_str)
            # Find matching epistemic state
            state = self._find_matching_state(action_proposal, epistemic_states, dim)
            if state is None:
                status = AuthorizationStatus.EPISTEMIC_PREREQUISITE_UNMET
                derivation_trace.append(f"Missing epistemic state for {dim_str}")
                return self._create_authorization(
                    action_proposal, epistemic_states, verification_assertions,
                    consensus, policy, actor, status, derivation_trace,
                )
            dim_state = state.dimension_states.get(dim)
            if dim_state is None or not dim_state.is_at_least_as_strong_as(
                DimensionState(dimension=dim, status=required_status)
            ):
                status = AuthorizationStatus.EPISTEMIC_PREREQUISITE_UNMET
                derivation_trace.append(
                    f"Epistemic prerequisite not met: {dim_str} requires {required_status_str}"
                )
                return self._create_authorization(
                    action_proposal, epistemic_states, verification_assertions,
                    consensus, policy, actor, status, derivation_trace,
                )
            derivation_trace.append(f"Epistemic prerequisite met: {dim_str} = {dim_state.status.value}")

        # Step 4: Check verification conditions
        if policy.required_verification_conditions:
            if not consensus.has_consensus:
                status = AuthorizationStatus.VERIFICATION_CONFLICT
                derivation_trace.append("Verification consensus required but not achieved")
                return self._create_authorization(
                    action_proposal, epistemic_states, verification_assertions,
                    consensus, policy, actor, status, derivation_trace,
                )
            derivation_trace.append("Verification consensus achieved")

        # Step 5: Check identity conditions
        for condition in policy.required_identity_conditions:
            if condition not in actor.capabilities:
                status = AuthorizationStatus.MISSING_AUTHORITY
                derivation_trace.append(f"Missing identity condition: {condition}")
                return self._create_authorization(
                    action_proposal, epistemic_states, verification_assertions,
                    consensus, policy, actor, status, derivation_trace,
                )
        derivation_trace.append("Identity conditions satisfied")

        # Step 6: Check resource constraints
        for resource, limit in policy.resource_limits.items():
            requested = action_proposal.requested_resources.get(resource, 0)
            if requested > limit:
                status = AuthorizationStatus.RESOURCE_CONSTRAINT_VIOLATION
                derivation_trace.append(
                    f"Resource constraint violated: {resource} requested={requested}, limit={limit}"
                )
                return self._create_authorization(
                    action_proposal, epistemic_states, verification_assertions,
                    consensus, policy, actor, status, derivation_trace,
                )
        derivation_trace.append("Resource constraints satisfied")

        # Step 7: Check temporal constraints
        if policy.expiration and current_time and current_time > policy.expiration:
            status = AuthorizationStatus.EXPIRED
            derivation_trace.append("Policy has expired")
            return self._create_authorization(
                action_proposal, epistemic_states, verification_assertions,
                consensus, policy, actor, status, derivation_trace,
            )
        derivation_trace.append("Temporal constraints satisfied")

        # All checks passed
        status = AuthorizationStatus.AUTHORIZED
        derivation_trace.append("All authorization conditions satisfied")

        return self._create_authorization(
            action_proposal, epistemic_states, verification_assertions,
            consensus, policy, actor, status, derivation_trace,
        )

    def _find_matching_state(
        self,
        proposal: ActionProposal,
        states: dict[str, EpistemicState],
        dim: StateDimension,
    ) -> EpistemicState | None:
        """Find an epistemic state matching the proposal's dependencies."""
        for dep_id in proposal.epistemic_dependencies:
            if dep_id in states:
                state = states[dep_id]
                if dim in state.dimension_states:
                    return state
        # If no specific dependency, check any state with the dimension
        for state in states.values():
            if dim in state.dimension_states:
                return state
        return None

    def _create_authorization(
        self,
        action_proposal: ActionProposal,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        status: AuthorizationStatus,
        derivation_trace: list[str],
    ) -> AuthorizationArtifact:
        """Create an authorization artifact."""
        auth = AuthorizationArtifact(
            authorization_id=f"auth_{action_proposal.action_id}_{policy.policy_id}",
            action_proposal_ref=action_proposal.action_id,
            proposition_refs=list(action_proposal.epistemic_dependencies),
            epistemic_state_refs=list(epistemic_states.keys()),
            verification_assertion_refs=[a.assertion_id for a in verification_assertions],
            consensus_conflict_refs=[consensus.consensus_id],
            governance_policy_ref=policy.policy_id,
            policy_version=policy.policy_version,
            identity_ref=actor.actor_id,
            capability_refs=list(actor.capabilities),
            resource_constraints=dict(policy.resource_limits),
            temporal_constraints=dict(policy.temporal_constraints),
            authorization_scope=dict(action_proposal.requested_scope),
            derivation_trace=derivation_trace,
            expiration=policy.expiration,
            status=status,
        )

        # Set hashes
        auth = AuthorizationArtifact(
            **{**dataclasses.asdict(auth),
               "provenance_hash": auth.compute_hash(),
               "derivation_hash": auth.compute_hash()}
        )

        return auth


# ---------------------------------------------------------------------------
# Authorization Verifier
# ---------------------------------------------------------------------------


class AuthorizationVerifier:
    """Independent verifier of authorization.

    The executor must NOT blindly trust an authorization artifact.
    This verifier independently reconstructs whether the action is
    actually authorized from the underlying components.
    """

    def verify_authorization(
        self,
        authorization: AuthorizationArtifact,
        action_proposal: ActionProposal,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        revocations: list[RevocationArtifact] | None = None,
        current_time: str = "",
    ) -> AuthorizationVerificationResult:
        """Independently verify authorization."""
        trace = AuthorizationTrace(
            trace_id=f"trace_{authorization.authorization_id}",
            authorization_id=authorization.authorization_id,
        )

        discrepancies = []

        # Step 1: Verify action proposal integrity
        proposal_valid = self._verify_proposal(authorization, action_proposal, trace, discrepancies)

        # Step 2: Verify epistemic state references
        states_valid = self._verify_states(authorization, epistemic_states, trace, discrepancies)

        # Step 3: Verify verification assertions
        assertions_valid = self._verify_assertions(authorization, verification_assertions, trace, discrepancies)

        # Step 4: Verify consensus
        consensus_valid = self._verify_consensus(authorization, consensus, trace, discrepancies)

        # Step 5: Verify policy
        policy_valid = self._verify_policy(authorization, policy, trace, discrepancies)

        # Step 6: Verify actor identity
        actor_valid = self._verify_actor(authorization, actor, trace, discrepancies)

        # Step 7: Verify scope
        scope_valid = self._verify_scope(authorization, action_proposal, trace, discrepancies)

        # Step 8: Verify expiration
        expiration_valid = self._verify_expiration(authorization, current_time, trace, discrepancies)

        # Step 9: Verify revocations
        revocation_valid = self._verify_revocations(authorization, revocations, trace, discrepancies)

        # Step 10: Re-derive authorization
        derivation_valid = self._verify_derivation(
            authorization, action_proposal, epistemic_states,
            verification_assertions, consensus, policy, actor,
            current_time, trace, discrepancies,
        )

        all_valid = all([
            proposal_valid,
            states_valid,
            assertions_valid,
            consensus_valid,
            policy_valid,
            actor_valid,
            scope_valid,
            expiration_valid,
            revocation_valid,
            derivation_valid,
        ])

        if all_valid:
            final_status = authorization.status
        elif not proposal_valid:
            final_status = AuthorizationStatus.PROVENANCE_INVALID
        elif not states_valid:
            final_status = AuthorizationStatus.EPISTEMIC_PREREQUISITE_UNMET
        elif not assertions_valid:
            final_status = AuthorizationStatus.VERIFICATION_CONFLICT
        elif not consensus_valid:
            final_status = AuthorizationStatus.VERIFICATION_CONFLICT
        elif not policy_valid:
            final_status = AuthorizationStatus.POLICY_CONFLICT
        elif not actor_valid:
            final_status = AuthorizationStatus.ACTOR_MISMATCH
        elif not scope_valid:
            final_status = AuthorizationStatus.SCOPE_MISMATCH
        elif not expiration_valid:
            final_status = AuthorizationStatus.EXPIRED
        elif not revocation_valid:
            final_status = AuthorizationStatus.REVOKED
        else:
            final_status = AuthorizationStatus.PROVENANCE_INVALID

        trace.proposal_valid = proposal_valid
        trace.states_valid = states_valid
        trace.assertions_valid = assertions_valid
        trace.consensus_valid = consensus_valid
        trace.policy_valid = policy_valid
        trace.actor_valid = actor_valid
        trace.scope_valid = scope_valid
        trace.expiration_valid = expiration_valid
        trace.revocation_valid = revocation_valid
        trace.derivation_valid = derivation_valid
        trace.discrepancies = discrepancies
        trace.final_status = final_status

        return AuthorizationVerificationResult(
            valid=all_valid,
            status=final_status,
            proposal_valid=proposal_valid,
            states_valid=states_valid,
            assertions_valid=assertions_valid,
            consensus_valid=consensus_valid,
            policy_valid=policy_valid,
            actor_valid=actor_valid,
            scope_valid=scope_valid,
            expiration_valid=expiration_valid,
            revocation_valid=revocation_valid,
            derivation_valid=derivation_valid,
            discrepancies=discrepancies,
            trace=trace,
        )

    def _verify_proposal(
        self,
        auth: AuthorizationArtifact,
        proposal: ActionProposal,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify action proposal integrity."""
        if auth.action_proposal_ref != proposal.action_id:
            trace.add_step("proposal", False, "Action proposal reference mismatch")
            discrepancies.append(
                f"Proposal ref mismatch: expected {proposal.action_id}, got {auth.action_proposal_ref}"
            )
            return False
        trace.add_step("proposal", True, "Action proposal verified")
        return True

    def _verify_states(
        self,
        auth: AuthorizationArtifact,
        states: dict[str, EpistemicState],
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify epistemic state references."""
        for ref in auth.epistemic_state_refs:
            if ref not in states:
                trace.add_step("states", False, f"Epistemic state {ref} not found")
                discrepancies.append(f"Epistemic state {ref} not found")
                return False
        trace.add_step("states", True, f"All {len(auth.epistemic_state_refs)} epistemic states verified")
        return True

    def _verify_assertions(
        self,
        auth: AuthorizationArtifact,
        assertions: list[VerificationAssertion],
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify verification assertions."""
        assertion_ids = {a.assertion_id for a in assertions}
        for ref in auth.verification_assertion_refs:
            if ref not in assertion_ids:
                trace.add_step("assertions", False, f"Verification assertion {ref} not found")
                discrepancies.append(f"Verification assertion {ref} not found")
                return False
        trace.add_step("assertions", True, f"All {len(auth.verification_assertion_refs)} assertions verified")
        return True

    def _verify_consensus(
        self,
        auth: AuthorizationArtifact,
        consensus: EpistemicConsensus,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify consensus reference."""
        if auth.consensus_conflict_refs and consensus.consensus_id not in auth.consensus_conflict_refs:
            trace.add_step("consensus", False, "Consensus reference mismatch")
            discrepancies.append(f"Consensus reference mismatch")
            return False
        trace.add_step("consensus", True, "Consensus verified")
        return True

    def _verify_policy(
        self,
        auth: AuthorizationArtifact,
        policy: GovernancePolicy,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify policy reference."""
        if auth.governance_policy_ref != policy.policy_id:
            trace.add_step("policy", False, "Policy reference mismatch")
            discrepancies.append(
                f"Policy ref mismatch: expected {policy.policy_id}, got {auth.governance_policy_ref}"
            )
            return False
        if auth.policy_version != policy.policy_version:
            trace.add_step("policy", False, "Policy version mismatch")
            discrepancies.append(
                f"Policy version mismatch: expected {policy.policy_version}, got {auth.policy_version}"
            )
            return False
        trace.add_step("policy", True, "Policy verified")
        return True

    def _verify_actor(
        self,
        auth: AuthorizationArtifact,
        actor: ActorIdentity,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify actor identity."""
        if auth.identity_ref != actor.actor_id:
            trace.add_step("actor", False, "Actor identity mismatch")
            discrepancies.append(
                f"Actor mismatch: expected {actor.actor_id}, got {auth.identity_ref}"
            )
            return False
        trace.add_step("actor", True, "Actor identity verified")
        return True

    def _verify_scope(
        self,
        auth: AuthorizationArtifact,
        proposal: ActionProposal,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify authorization scope matches proposal."""
        # Check that authorization scope covers the requested scope
        for key, value in proposal.requested_scope.items():
            auth_value = auth.authorization_scope.get(key)
            if auth_value is None:
                trace.add_step("scope", False, f"Scope missing key: {key}")
                discrepancies.append(f"Authorization scope missing key: {key}")
                return False
            # For numeric values, auth must be >= requested
            if isinstance(value, (int, float)) and isinstance(auth_value, (int, float)):
                if auth_value < value:
                    trace.add_step("scope", False, f"Scope insufficient for {key}")
                    discrepancies.append(f"Scope insufficient for {key}: {auth_value} < {value}")
                    return False
        trace.add_step("scope", True, "Scope verified")
        return True

    def _verify_expiration(
        self,
        auth: AuthorizationArtifact,
        current_time: str,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify authorization has not expired."""
        if auth.expiration and current_time and current_time > auth.expiration:
            trace.add_step("expiration", False, "Authorization has expired")
            discrepancies.append(f"Authorization expired at {auth.expiration}, current time {current_time}")
            return False
        trace.add_step("expiration", True, "Expiration verified")
        return True

    def _verify_revocations(
        self,
        auth: AuthorizationArtifact,
        revocations: list[RevocationArtifact] | None,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Verify authorization has not been revoked."""
        if revocations:
            for rev in revocations:
                if rev.authorization_ref == auth.authorization_id:
                    trace.add_step("revocation", False, "Authorization has been revoked")
                    discrepancies.append(f"Authorization revoked by {rev.revoker_id}")
                    return False
        trace.add_step("revocation", True, "No revocations found")
        return True

    def _verify_derivation(
        self,
        auth: AuthorizationArtifact,
        proposal: ActionProposal,
        states: dict[str, EpistemicState],
        assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        current_time: str,
        trace: AuthorizationTrace,
        discrepancies: list[str],
    ) -> bool:
        """Re-derive authorization and compare to claimed authorization."""
        deriv = AuthorizationDerivation()
        derived = deriv.derive_authorization(
            proposal, states, assertions, consensus, policy, actor, current_time,
        )

        if derived.status != auth.status:
            trace.add_step("derivation", False, "Re-derived status mismatch")
            discrepancies.append(
                f"Derivation mismatch: re-derived {derived.status.value}, claimed {auth.status.value}"
            )
            return False

        trace.add_step("derivation", True, "Derivation independently verified")
        return True


# ---------------------------------------------------------------------------
# Authorization Trace
# ---------------------------------------------------------------------------


@dataclass
class AuthorizationTrace:
    """Trace of the authorization verification process."""
    trace_id: str
    authorization_id: str

    steps: list[dict] = field(default_factory=list)

    proposal_valid: bool = False
    states_valid: bool = False
    assertions_valid: bool = False
    consensus_valid: bool = False
    policy_valid: bool = False
    actor_valid: bool = False
    scope_valid: bool = False
    expiration_valid: bool = False
    revocation_valid: bool = False
    derivation_valid: bool = False

    discrepancies: list[str] = field(default_factory=list)

    final_status: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE

    def add_step(self, check: str, passed: bool, detail: str = "") -> None:
        """Add a verification step."""
        self.steps.append({
            "check": check,
            "passed": passed,
            "detail": detail,
        })

    def explain(self) -> str:
        """Generate human-readable trace."""
        lines = [f"Authorization Trace: {self.trace_id}"]
        lines.append(f"Authorization: {self.authorization_id}")
        lines.append("")
        for step in self.steps:
            status = "✓" if step["passed"] else "✗"
            lines.append(f"  {status} {step['check']}: {step['detail']}")
        lines.append("")
        if self.discrepancies:
            lines.append("Discrepancies:")
            for d in self.discrepancies:
                lines.append(f"  ✗ {d}")
            lines.append("")
        lines.append(f"Final Status: {self.final_status.value}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Authorization Verification Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorizationVerificationResult:
    """Result of independent authorization verification."""
    valid: bool
    status: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE

    proposal_valid: bool = False
    states_valid: bool = False
    assertions_valid: bool = False
    consensus_valid: bool = False
    policy_valid: bool = False
    actor_valid: bool = False
    scope_valid: bool = False
    expiration_valid: bool = False
    revocation_valid: bool = False
    derivation_valid: bool = False

    discrepancies: list[str] = field(default_factory=list)

    trace: AuthorizationTrace | None = None

    def explain(self) -> str:
        """Generate human-readable result."""
        lines = ["Authorization Verification Result"]
        lines.append(f"Valid: {self.valid}")
        lines.append(f"Status: {self.status.value}")
        lines.append("")
        lines.append(f"Proposal Valid: {self.proposal_valid}")
        lines.append(f"States Valid: {self.states_valid}")
        lines.append(f"Assertions Valid: {self.assertions_valid}")
        lines.append(f"Consensus Valid: {self.consensus_valid}")
        lines.append(f"Policy Valid: {self.policy_valid}")
        lines.append(f"Actor Valid: {self.actor_valid}")
        lines.append(f"Scope Valid: {self.scope_valid}")
        lines.append(f"Expiration Valid: {self.expiration_valid}")
        lines.append(f"Revocation Valid: {self.revocation_valid}")
        lines.append(f"Derivation Valid: {self.derivation_valid}")
        if self.discrepancies:
            lines.append("")
            lines.append("Discrepancies:")
            for d in self.discrepancies:
                lines.append(f"  ✗ {d}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Execution Protocol
# ---------------------------------------------------------------------------


class ExecutionProtocol:
    """Protocol for executing actions with authorization verification."""

    def __init__(self):
        self.revocations: list[RevocationArtifact] = []
        self.executions: list[ExecutionArtifact] = []

    def add_revocation(self, revocation: RevocationArtifact) -> None:
        """Add a revocation."""
        self.revocations.append(revocation)

    def execute(
        self,
        action_proposal: ActionProposal,
        authorization: AuthorizationArtifact,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        current_time: str = "",
    ) -> ExecutionResult:
        """Execute an action with full verification."""
        # Step 1: Verify authorization
        verifier = AuthorizationVerifier()
        auth_result = verifier.verify_authorization(
            authorization, action_proposal, epistemic_states,
            verification_assertions, consensus, policy, actor,
            self.revocations, current_time,
        )

        if not auth_result.valid:
            return ExecutionResult(
                executed=False,
                status=auth_result.status,
                authorization_result=auth_result,
                execution_artifact=None,
            )

        if authorization.status != AuthorizationStatus.AUTHORIZED:
            return ExecutionResult(
                executed=False,
                status=authorization.status,
                authorization_result=auth_result,
                execution_artifact=None,
            )

        # Step 2: Create execution artifact
        execution = ExecutionArtifact(
            execution_id=f"exec_{action_proposal.action_id}",
            action_type=action_proposal.action_type,
            target=action_proposal.target,
            actor_id=actor.actor_id,
            authorization_ref=authorization.authorization_id,
            parameters=dict(action_proposal.parameters),
            timestamp=current_time,
            result="SUCCESS",
        )

        execution = ExecutionArtifact(
            **{**dataclasses.asdict(execution),
               "provenance_hash": execution.compute_hash()}
        )

        self.executions.append(execution)

        return ExecutionResult(
            executed=True,
            status=AuthorizationStatus.AUTHORIZED,
            authorization_result=auth_result,
            execution_artifact=execution,
        )


# ---------------------------------------------------------------------------
# Execution Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionResult:
    """Result of an execution attempt."""
    executed: bool
    status: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE
    authorization_result: AuthorizationVerificationResult | None = None
    execution_artifact: ExecutionArtifact | None = None


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_action_proposal(
    action_id: str,
    proposer_id: str,
    action_type: str,
    target: str,
    **kwargs,
) -> ActionProposal:
    """Create an action proposal."""
    return ActionProposal(
        action_id=action_id,
        proposer_id=proposer_id,
        action_type=action_type,
        target=target,
        **kwargs,
    )


def create_governance_policy(
    policy_id: str,
    policy_version: str,
    **kwargs,
) -> GovernancePolicy:
    """Create a governance policy."""
    return GovernancePolicy(
        policy_id=policy_id,
        policy_version=policy_version,
        **kwargs,
    )


def create_actor_identity(
    actor_id: str,
    capabilities: list[str] | None = None,
) -> ActorIdentity:
    """Create an actor identity."""
    return ActorIdentity(
        actor_id=actor_id,
        capabilities=capabilities or [],
    )


def derive_authorization(
    action_proposal: ActionProposal,
    epistemic_states: dict[str, EpistemicState],
    verification_assertions: list[VerificationAssertion],
    consensus: EpistemicConsensus,
    policy: GovernancePolicy,
    actor: ActorIdentity,
    current_time: str = "",
) -> AuthorizationArtifact:
    """Derive authorization from components."""
    deriv = AuthorizationDerivation()
    return deriv.derive_authorization(
        action_proposal, epistemic_states, verification_assertions,
        consensus, policy, actor, current_time,
    )


def verify_authorization(
    authorization: AuthorizationArtifact,
    action_proposal: ActionProposal,
    epistemic_states: dict[str, EpistemicState],
    verification_assertions: list[VerificationAssertion],
    consensus: EpistemicConsensus,
    policy: GovernancePolicy,
    actor: ActorIdentity,
    revocations: list[RevocationArtifact] | None = None,
    current_time: str = "",
) -> AuthorizationVerificationResult:
    """Verify authorization independently."""
    verifier = AuthorizationVerifier()
    return verifier.verify_authorization(
        authorization, action_proposal, epistemic_states,
        verification_assertions, consensus, policy, actor,
        revocations, current_time,
    )
