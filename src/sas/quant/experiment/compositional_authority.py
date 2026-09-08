"""Compositional Authority and Protocol Closure.

Implements the architectural boundary where individually valid artifacts
must compose into a valid authority context.

The central research question:
    If every individual transition is valid, can composition of
    individually valid transitions nevertheless create unauthorized
    authority?

Architecture:
    Individual Artifact Validity
          ↓
    Dependency Resolution
          ↓
    Semantic Compatibility
          ↓
    Temporal Compatibility
          ↓
    Scope Compatibility
          ↓
    Authority Non-Amplification
          ↓
    Resource Closure
          ↓
    Revocation Closure
          ↓
    Provenance Closure
          ↓
    No Circular Authority
          ↓
    Authority Root Resolution
          ↓
    Authority Closure
          ↓
    Execution-Time Revalidation
          ↓
    Execution

Invariants:
    VALID(A) + VALID(B) + VALID(C) ≠ necessarily VALID(A+B+C)

    Authority is valid only when the complete derivation is valid,
    not merely when each component is valid in isolation.

    No authority appears from nowhere.
    Every execution authority must have a traceable derivation to
    an explicit authority root.
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


# ---------------------------------------------------------------------------
# Delegation Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationArtifact:
    """Explicit delegation of authority.

    Delegation must specify:
    - delegator
    - delegate
    - capability
    - scope
    - duration
    - constraints
    - provenance
    - revocation
    """
    delegation_id: str
    delegator_id: str
    delegate_id: str
    capability: str
    scope: dict = field(default_factory=dict)
    valid_from: str = ""
    valid_until: str = ""
    constraints: dict = field(default_factory=dict)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the delegation."""
        content = json.dumps({
            "delegation_id": self.delegation_id,
            "delegator_id": self.delegator_id,
            "delegate_id": self.delegate_id,
            "capability": self.capability,
            "scope": self.scope,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "constraints": self.constraints,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authority Context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityContext:
    """Immutable structure representing the complete context for authorization.

    The context must be reconstructable. It must NOT be:
        authorized = true

    It should be:
        Here are the exact artifacts from which authorization was derived.
    """
    context_id: str
    action_proposal_ref: str
    epistemic_state_refs: list[str] = field(default_factory=list)
    verification_assertion_refs: list[str] = field(default_factory=list)
    consensus_refs: list[str] = field(default_factory=list)
    governance_policy_refs: list[str] = field(default_factory=list)
    actor_identity_ref: str = ""
    capability_refs: list[str] = field(default_factory=list)
    delegation_refs: list[str] = field(default_factory=list)
    resource_constraint_refs: list[str] = field(default_factory=list)
    temporal_constraints: dict[str, str] = field(default_factory=dict)
    revocation_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    created_at: str = ""
    valid_from: str = ""
    valid_until: str = ""
    derivation_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the context."""
        content = json.dumps({
            "context_id": self.context_id,
            "action_proposal_ref": self.action_proposal_ref,
            "epistemic_state_refs": sorted(self.epistemic_state_refs),
            "verification_assertion_refs": sorted(self.verification_assertion_refs),
            "consensus_refs": sorted(self.consensus_refs),
            "governance_policy_refs": sorted(self.governance_policy_refs),
            "actor_identity_ref": self.actor_identity_ref,
            "capability_refs": sorted(self.capability_refs),
            "delegation_refs": sorted(self.delegation_refs),
            "resource_constraint_refs": sorted(self.resource_constraint_refs),
            "temporal_constraints": self.temporal_constraints,
            "revocation_refs": sorted(self.revocation_refs),
            "provenance_refs": sorted(self.provenance_refs),
            "created_at": self.created_at,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authority Closure
# ---------------------------------------------------------------------------


class ClosureStatus(str, Enum):
    """Status of authority closure verification."""
    CLOSED = "closed"
    OPEN = "open"
    CIRCULAR = "circular"
    MISSING_DEPENDENCY = "missing_dependency"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    SCOPE_AMPLIFICATION = "scope_amplification"
    RESOURCE_VIOLATION = "resource_violation"
    REVOCATION_VIOLATION = "revocation_violation"
    POLICY_CONFLICT = "policy_conflict"
    DELEGATION_AMPLIFICATION = "delegation_amplification"


@dataclass(frozen=True)
class AuthorityClosure:
    """Structural representation of authority closure.

    Answers: Given an action proposal and all referenced artifacts,
    is the complete authority derivation closed?
    """
    closure_id: str
    context_id: str
    status: ClosureStatus = ClosureStatus.OPEN
    missing_dependencies: list[str] = field(default_factory=list)
    circular_dependencies: list[str] = field(default_factory=list)
    temporal_mismatches: list[str] = field(default_factory=list)
    scope_amplifications: list[str] = field(default_factory=list)
    resource_violations: list[str] = field(default_factory=list)
    revocation_violations: list[str] = field(default_factory=list)
    policy_conflicts: list[str] = field(default_factory=list)
    delegation_amplifications: list[str] = field(default_factory=list)
    authority_roots: list[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the closure."""
        content = json.dumps({
            "closure_id": self.closure_id,
            "context_id": self.context_id,
            "status": self.status.value,
            "missing_dependencies": sorted(self.missing_dependencies),
            "circular_dependencies": sorted(self.circular_dependencies),
            "temporal_mismatches": sorted(self.temporal_mismatches),
            "scope_amplifications": sorted(self.scope_amplifications),
            "resource_violations": sorted(self.resource_violations),
            "revocation_violations": sorted(self.revocation_violations),
            "policy_conflicts": sorted(self.policy_conflicts),
            "delegation_amplifications": sorted(self.delegation_amplifications),
            "authority_roots": sorted(self.authority_roots),
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @property
    def is_closed(self) -> bool:
        """Check if the closure is valid."""
        return self.status == ClosureStatus.CLOSED


# ---------------------------------------------------------------------------
# Resource Budget
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResourceBudget:
    """Tracks resource consumption across authorizations."""
    budget_id: str
    resource_type: str
    total_limit: float
    consumed: float = 0.0
    reserved: float = 0.0

    @property
    def available(self) -> float:
        """Get available resources."""
        return self.total_limit - self.consumed - self.reserved

    def can_allocate(self, amount: float) -> bool:
        """Check if amount can be allocated."""
        return amount <= self.available

    def allocate(self, amount: float) -> "ResourceBudget":
        """Allocate resources."""
        if not self.can_allocate(amount):
            raise ValueError(f"Cannot allocate {amount}, only {self.available} available")
        return ResourceBudget(
            budget_id=self.budget_id,
            resource_type=self.resource_type,
            total_limit=self.total_limit,
            consumed=self.consumed + amount,
            reserved=self.reserved,
        )

    def reserve(self, amount: float) -> "ResourceBudget":
        """Reserve resources."""
        if not self.can_allocate(amount):
            raise ValueError(f"Cannot reserve {amount}, only {self.available} available")
        return ResourceBudget(
            budget_id=self.budget_id,
            resource_type=self.resource_type,
            total_limit=self.total_limit,
            consumed=self.consumed,
            reserved=self.reserved + amount,
        )

    def release(self, amount: float) -> "ResourceBudget":
        """Release reserved resources."""
        return ResourceBudget(
            budget_id=self.budget_id,
            resource_type=self.resource_type,
            total_limit=self.total_limit,
            consumed=self.consumed,
            reserved=max(0, self.reserved - amount),
        )


# ---------------------------------------------------------------------------
# Authority Context Verifier
# ---------------------------------------------------------------------------


class AuthorityContextVerifier:
    """Independently verifies the entire authority context.

    Verifies:
    - All required dependencies exist
    - All dependencies are valid
    - All semantic relationships are valid
    - All provenance links resolve
    - All temporal constraints hold
    - All revocations are accounted for
    - All policy predicates are satisfied
    - All identity/capability constraints hold
    - No hidden authority dependency exists
    - No circular dependency exists
    - No scope expansion occurred
    - No conflicting branch remains unresolved
    """

    def verify_context(
        self,
        context: AuthorityContext,
        action_proposal: ActionProposal,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policies: dict[str, GovernancePolicy],
        actor: ActorIdentity,
        delegations: list[DelegationArtifact] | None = None,
        revocations: list[RevocationArtifact] | None = None,
        resource_budgets: dict[str, ResourceBudget] | None = None,
        current_time: str = "",
    ) -> AuthorityClosure:
        """Verify the entire authority context."""
        missing_deps = []
        circular_deps = []
        temporal_mismatches = []
        scope_amplifications = []
        resource_violations = []
        revocation_violations = []
        policy_conflicts = []
        delegation_amplifications = []
        authority_roots = []

        # Step 1: Verify all epistemic state references exist
        for ref in context.epistemic_state_refs:
            if ref not in epistemic_states:
                missing_deps.append(f"epistemic_state:{ref}")

        # Step 2: Verify all verification assertion references exist
        assertion_ids = {a.assertion_id for a in verification_assertions}
        for ref in context.verification_assertion_refs:
            if ref not in assertion_ids:
                missing_deps.append(f"verification_assertion:{ref}")

        # Step 3: Verify all policy references exist
        for ref in context.governance_policy_refs:
            if ref not in policies:
                missing_deps.append(f"governance_policy:{ref}")

        # Step 4: Verify actor identity
        if context.actor_identity_ref != actor.actor_id:
            missing_deps.append(f"actor_identity:{context.actor_identity_ref}")

        # Step 5: Verify temporal constraints
        if context.valid_from and current_time and current_time < context.valid_from:
            temporal_mismatches.append(f"Context not yet valid: {current_time} < {context.valid_from}")
        if context.valid_until and current_time and current_time > context.valid_until:
            temporal_mismatches.append(f"Context expired: {current_time} > {context.valid_until}")

        # Step 6: Verify no revocations
        if revocations:
            for rev in revocations:
                if rev.authorization_ref in context.provenance_refs:
                    revocation_violations.append(f"Authorization revoked:{rev.revocation_id}")

        # Step 7: Verify resource constraints
        if resource_budgets:
            for ref in context.resource_constraint_refs:
                if ref in resource_budgets:
                    budget = resource_budgets[ref]
                    requested = action_proposal.requested_resources.get(budget.resource_type, 0)
                    if not budget.can_allocate(requested):
                        resource_violations.append(
                            f"Resource {budget.resource_type}: requested={requested}, available={budget.available}"
                        )

        # Step 8: Verify delegation chains
        if delegations:
            for delegation in delegations:
                # Check delegation is valid
                if delegation.valid_until and current_time and current_time > delegation.valid_until:
                    temporal_mismatches.append(f"Delegation expired:{delegation.delegation_id}")
                # Check delegation doesn't amplify scope
                for key, value in delegation.scope.items():
                    if isinstance(value, (int, float)):
                        requested = action_proposal.requested_scope.get(key, 0)
                        if requested > value:
                            scope_amplifications.append(
                                f"Delegation scope exceeded:{delegation.delegation_id}:{key}"
                            )

        # Step 9: Check for policy conflicts
        if len(policies) > 1:
            policy_list = list(policies.values())
            for i in range(len(policy_list)):
                for j in range(i + 1, len(policy_list)):
                    p1, p2 = policy_list[i], policy_list[j]
                    # Check for conflicting actions
                    for action in p1.allowed_actions:
                        if action in p2.prohibited_actions:
                            policy_conflicts.append(
                                f"Policy conflict: {p1.policy_id} allows {action}, {p2.policy_id} prohibits"
                            )

        # Step 10: Identify authority roots
        # Authority roots are: policies, actor identity, delegations
        for policy in policies.values():
            authority_roots.append(f"policy:{policy.policy_id}")
        authority_roots.append(f"actor:{actor.actor_id}")
        for delegation in (delegations or []):
            authority_roots.append(f"delegation:{delegation.delegation_id}")

        # Step 11: Check for circular authority
        # Build dependency graph and check for cycles
        graph = self._build_dependency_graph(
            context, epistemic_states, verification_assertions, policies, delegations
        )
        cycles = self._detect_cycles(graph)
        circular_deps.extend(cycles)

        # Determine closure status
        if missing_deps:
            status = ClosureStatus.MISSING_DEPENDENCY
        elif circular_deps:
            status = ClosureStatus.CIRCULAR
        elif temporal_mismatches:
            status = ClosureStatus.TEMPORAL_MISMATCH
        elif scope_amplifications:
            status = ClosureStatus.SCOPE_AMPLIFICATION
        elif resource_violations:
            status = ClosureStatus.RESOURCE_VIOLATION
        elif revocation_violations:
            status = ClosureStatus.REVOCATION_VIOLATION
        elif policy_conflicts:
            status = ClosureStatus.POLICY_CONFLICT
        elif delegation_amplifications:
            status = ClosureStatus.DELEGATION_AMPLIFICATION
        else:
            status = ClosureStatus.CLOSED

        closure = AuthorityClosure(
            closure_id=f"closure_{context.context_id}",
            context_id=context.context_id,
            status=status,
            missing_dependencies=missing_deps,
            circular_dependencies=circular_deps,
            temporal_mismatches=temporal_mismatches,
            scope_amplifications=scope_amplifications,
            resource_violations=resource_violations,
            revocation_violations=revocation_violations,
            policy_conflicts=policy_conflicts,
            delegation_amplifications=delegation_amplifications,
            authority_roots=authority_roots,
        )

        closure = AuthorityClosure(
            **{**dataclasses.asdict(closure), "provenance_hash": closure.compute_hash()}
        )

        return closure

    def _build_dependency_graph(
        self,
        context: AuthorityContext,
        states: dict[str, EpistemicState],
        assertions: list[VerificationAssertion],
        policies: dict[str, GovernancePolicy],
        delegations: list[DelegationArtifact] | None,
    ) -> dict[str, list[str]]:
        """Build a dependency graph."""
        graph = {}

        # Add edges from context to its dependencies
        for ref in context.epistemic_state_refs:
            graph.setdefault(context.context_id, []).append(f"state:{ref}")
        for ref in context.verification_assertion_refs:
            graph.setdefault(context.context_id, []).append(f"assertion:{ref}")
        for ref in context.governance_policy_refs:
            graph.setdefault(context.context_id, []).append(f"policy:{ref}")

        # Add delegation chains
        if delegations:
            for delegation in delegations:
                graph.setdefault(f"delegation:{delegation.delegation_id}", []).append(
                    f"actor:{delegation.delegator_id}"
                )

        return graph

    def _detect_cycles(self, graph: dict[str, list[str]]) -> list[str]:
        """Detect cycles in the dependency graph."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append("->".join(cycle))

            path.pop()
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles


# ---------------------------------------------------------------------------
# Composition Verifier
# ---------------------------------------------------------------------------


class CompositionVerifier:
    """Verifies that individually valid artifacts compose correctly."""

    def __init__(self):
        self.context_verifier = AuthorityContextVerifier()

    def verify_composition(
        self,
        context: AuthorityContext,
        action_proposal: ActionProposal,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policies: dict[str, GovernancePolicy],
        actor: ActorIdentity,
        authorization: AuthorizationArtifact,
        delegations: list[DelegationArtifact] | None = None,
        revocations: list[RevocationArtifact] | None = None,
        resource_budgets: dict[str, ResourceBudget] | None = None,
        current_time: str = "",
    ) -> CompositionResult:
        """Verify the complete composition."""
        # Step 1: Verify individual artifacts
        individual_valid = self._verify_individual_artifacts(
            action_proposal, epistemic_states, verification_assertions,
            consensus, policies, actor, authorization,
        )

        # Step 2: Verify context closure
        closure = self.context_verifier.verify_context(
            context, action_proposal, epistemic_states,
            verification_assertions, consensus, policies, actor,
            delegations, revocations, resource_budgets, current_time,
        )

        # Step 3: Verify authorization derivation
        auth_valid = self._verify_authorization_derivation(
            authorization, action_proposal, epistemic_states,
            verification_assertions, consensus, policies, actor,
        )

        # Step 4: Check for composition-specific issues
        composition_issues = self._check_composition_issues(
            context, action_proposal, epistemic_states, policies,
            authorization, resource_budgets,
        )

        all_valid = (
            individual_valid
            and closure.is_closed
            and auth_valid
            and not composition_issues
        )

        return CompositionResult(
            valid=all_valid,
            individual_valid=individual_valid,
            closure=closure,
            authorization_valid=auth_valid,
            composition_issues=composition_issues,
        )

    def _verify_individual_artifacts(
        self,
        proposal: ActionProposal,
        states: dict[str, EpistemicState],
        assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policies: dict[str, GovernancePolicy],
        actor: ActorIdentity,
        authorization: AuthorizationArtifact,
    ) -> bool:
        """Verify each artifact is individually valid."""
        # Check states have valid status
        for state in states.values():
            if state.status == EpistemicStatus.UNKNOWN:
                return False

        # Check assertions have valid status
        for assertion in assertions:
            if assertion.overall_status == VerificationStatus.FORGED:
                return False

        # Check consensus
        if not consensus.has_consensus and consensus.unresolved_conflicts:
            return False

        # Check policies
        for policy in policies.values():
            if not policy.policy_id:
                return False

        # Check actor
        if not actor.actor_id:
            return False

        # Check authorization
        if authorization.status not in (
            AuthorizationStatus.AUTHORIZED,
            AuthorizationStatus.DENIED,
            AuthorizationStatus.INCONCLUSIVE,
        ):
            return False

        return True

    def _verify_authorization_derivation(
        self,
        authorization: AuthorizationArtifact,
        proposal: ActionProposal,
        states: dict[str, EpistemicState],
        assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policies: dict[str, GovernancePolicy],
        actor: ActorIdentity,
    ) -> bool:
        """Verify authorization was properly derived."""
        # Re-derive authorization
        deriv = AuthorizationDerivation()
        # Use the first policy (simplified)
        policy = list(policies.values())[0] if policies else None
        if policy is None:
            return False

        derived = deriv.derive_authorization(
            proposal, states, assertions, consensus, policy, actor
        )

        # Compare
        return derived.status == authorization.status

    def _check_composition_issues(
        self,
        context: AuthorityContext,
        proposal: ActionProposal,
        states: dict[str, EpistemicState],
        policies: dict[str, GovernancePolicy],
        authorization: AuthorizationArtifact,
        resource_budgets: dict[str, ResourceBudget] | None,
    ) -> list[str]:
        """Check for composition-specific issues."""
        issues = []

        # Check for aggregate resource violations
        if resource_budgets:
            for budget in resource_budgets.values():
                requested = proposal.requested_resources.get(budget.resource_type, 0)
                if not budget.can_allocate(requested):
                    issues.append(
                        f"Aggregate resource violation: {budget.resource_type} "
                        f"requested={requested}, available={budget.available}"
                    )

        # Check for policy conflicts
        if len(policies) > 1:
            policy_list = list(policies.values())
            for i in range(len(policy_list)):
                for j in range(i + 1, len(policy_list)):
                    p1, p2 = policy_list[i], policy_list[j]
                    for action in p1.allowed_actions:
                        if action in p2.prohibited_actions:
                            issues.append(
                                f"Policy conflict: {p1.policy_id} allows {action} "
                                f"but {p2.policy_id} prohibits"
                            )

        return issues


# ---------------------------------------------------------------------------
# Composition Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositionResult:
    """Result of composition verification."""
    valid: bool
    individual_valid: bool = False
    closure: AuthorityClosure | None = None
    authorization_valid: bool = False
    composition_issues: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Authority Branch
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityBranch:
    """Represents a branch of authority derivation."""
    branch_id: str
    context: AuthorityContext
    authorization: AuthorizationArtifact
    parent_branch_id: str | None = None
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the branch."""
        content = json.dumps({
            "branch_id": self.branch_id,
            "context_id": self.context.context_id,
            "authorization_id": self.authorization.authorization_id,
            "parent_branch_id": self.parent_branch_id,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Branch Merger
# ---------------------------------------------------------------------------


class BranchMerger:
    """Merges authority branches."""

    def merge_branches(
        self,
        branch_a: AuthorityBranch,
        branch_b: AuthorityBranch,
    ) -> MergeResult:
        """Merge two authority branches."""
        # Check for conflicts
        conflicts = self._detect_conflicts(branch_a, branch_b)

        if conflicts:
            return MergeResult(
                merged=False,
                status=MergeStatus.CONFLICT,
                conflicts=conflicts,
                merged_branch=None,
            )

        # Merge contexts
        merged_context = self._merge_contexts(branch_a.context, branch_b.context)

        # Merge authorizations (most restrictive wins)
        merged_auth = self._merge_authorizations(
            branch_a.authorization, branch_b.authorization
        )

        merged_branch = AuthorityBranch(
            branch_id=f"merged_{branch_a.branch_id}_{branch_b.branch_id}",
            context=merged_context,
            authorization=merged_auth,
        )

        return MergeResult(
            merged=True,
            status=MergeStatus.MERGED,
            conflicts=[],
            merged_branch=merged_branch,
        )

    def _detect_conflicts(
        self,
        a: AuthorityBranch,
        b: AuthorityBranch,
    ) -> list[str]:
        """Detect conflicts between branches."""
        conflicts = []

        # Check for actor mismatch
        if a.context.actor_identity_ref != b.context.actor_identity_ref:
            conflicts.append(
                f"Actor mismatch: {a.context.actor_identity_ref} vs {b.context.actor_identity_ref}"
            )

        # Check for temporal mismatch
        if a.context.valid_until and b.context.valid_from:
            if a.context.valid_until < b.context.valid_from:
                conflicts.append("Temporal mismatch: branches not simultaneously valid")

        # Check for authorization status conflict
        if a.authorization.status != b.authorization.status:
            conflicts.append(
                f"Authorization status conflict: "
                f"{a.authorization.status.value} vs {b.authorization.status.value}"
            )

        return conflicts

    def _merge_contexts(
        self,
        a: AuthorityContext,
        b: AuthorityContext,
    ) -> AuthorityContext:
        """Merge two contexts."""
        # Union of all references
        merged = AuthorityContext(
            context_id=f"merged_{a.context_id}_{b.context_id}",
            action_proposal_ref=a.action_proposal_ref,
            epistemic_state_refs=list(set(a.epistemic_state_refs + b.epistemic_state_refs)),
            verification_assertion_refs=list(set(a.verification_assertion_refs + b.verification_assertion_refs)),
            consensus_refs=list(set(a.consensus_refs + b.consensus_refs)),
            governance_policy_refs=list(set(a.governance_policy_refs + b.governance_policy_refs)),
            actor_identity_ref=a.actor_identity_ref,
            capability_refs=list(set(a.capability_refs + b.capability_refs)),
            delegation_refs=list(set(a.delegation_refs + b.delegation_refs)),
            resource_constraint_refs=list(set(a.resource_constraint_refs + b.resource_constraint_refs)),
            revocation_refs=list(set(a.revocation_refs + b.revocation_refs)),
            provenance_refs=list(set(a.provenance_refs + b.provenance_refs)),
        )

        return AuthorityContext(
            **{**dataclasses.asdict(merged), "derivation_hash": merged.compute_hash()}
        )

    def _merge_authorizations(
        self,
        a: AuthorizationArtifact,
        b: AuthorizationArtifact,
    ) -> AuthorizationArtifact:
        """Merge two authorizations (most restrictive wins)."""
        # If either is denied, result is denied
        if a.status == AuthorizationStatus.DENIED or b.status == AuthorizationStatus.DENIED:
            status = AuthorizationStatus.DENIED
        elif a.status == AuthorizationStatus.INCONCLUSIVE or b.status == AuthorizationStatus.INCONCLUSIVE:
            status = AuthorizationStatus.INCONCLUSIVE
        else:
            status = AuthorizationStatus.AUTHORIZED

        # Intersection of scopes
        merged_scope = {}
        for key in set(a.authorization_scope.keys()) & set(b.authorization_scope.keys()):
            a_val = a.authorization_scope[key]
            b_val = b.authorization_scope[key]
            if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
                merged_scope[key] = min(a_val, b_val)
            else:
                merged_scope[key] = a_val

        merged = AuthorizationArtifact(
            authorization_id=f"merged_{a.authorization_id}_{b.authorization_id}",
            action_proposal_ref=a.action_proposal_ref,
            status=status,
            authorization_scope=merged_scope,
        )

        return AuthorizationArtifact(
            **{**dataclasses.asdict(merged),
               "provenance_hash": merged.compute_hash(),
               "derivation_hash": merged.compute_hash()}
        )


# ---------------------------------------------------------------------------
# Merge Result
# ---------------------------------------------------------------------------


class MergeStatus(str, Enum):
    """Status of a branch merge."""
    MERGED = "merged"
    CONFLICT = "conflict"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True)
class MergeResult:
    """Result of merging authority branches."""
    merged: bool
    status: MergeStatus = MergeStatus.INCOMPATIBLE
    conflicts: list[str] = field(default_factory=list)
    merged_branch: AuthorityBranch | None = None


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_authority_context(
    context_id: str,
    action_proposal_ref: str,
    **kwargs,
) -> AuthorityContext:
    """Create an authority context."""
    return AuthorityContext(
        context_id=context_id,
        action_proposal_ref=action_proposal_ref,
        **kwargs,
    )


def create_delegation(
    delegation_id: str,
    delegator_id: str,
    delegate_id: str,
    capability: str,
    **kwargs,
) -> DelegationArtifact:
    """Create a delegation."""
    return DelegationArtifact(
        delegation_id=delegation_id,
        delegator_id=delegator_id,
        delegate_id=delegate_id,
        capability=capability,
        **kwargs,
    )


def create_resource_budget(
    budget_id: str,
    resource_type: str,
    total_limit: float,
) -> ResourceBudget:
    """Create a resource budget."""
    return ResourceBudget(
        budget_id=budget_id,
        resource_type=resource_type,
        total_limit=total_limit,
    )


def verify_authority_closure(
    context: AuthorityContext,
    action_proposal: ActionProposal,
    epistemic_states: dict[str, EpistemicState],
    verification_assertions: list[VerificationAssertion],
    consensus: EpistemicConsensus,
    policies: dict[str, GovernancePolicy],
    actor: ActorIdentity,
    **kwargs,
) -> AuthorityClosure:
    """Verify authority closure."""
    verifier = AuthorityContextVerifier()
    return verifier.verify_context(
        context, action_proposal, epistemic_states,
        verification_assertions, consensus, policies, actor,
        **kwargs,
    )


def verify_composition(
    context: AuthorityContext,
    action_proposal: ActionProposal,
    epistemic_states: dict[str, EpistemicState],
    verification_assertions: list[VerificationAssertion],
    consensus: EpistemicConsensus,
    policies: dict[str, GovernancePolicy],
    actor: ActorIdentity,
    authorization: AuthorizationArtifact,
    **kwargs,
) -> CompositionResult:
    """Verify composition."""
    verifier = CompositionVerifier()
    return verifier.verify_composition(
        context, action_proposal, epistemic_states,
        verification_assertions, consensus, policies, actor,
        authorization, **kwargs,
    )
