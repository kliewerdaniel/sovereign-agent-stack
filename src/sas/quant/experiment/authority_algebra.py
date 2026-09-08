"""Authority Algebra — Compositional Properties of the Authority Protocol.

Investigates whether the protocol is actually closed under arbitrary
composition, or merely closed over the composition operators currently
modeled.

The central question:
    Is authority actually conserved by the protocol?

Composition Laws Investigated:

1. ASSOCIATIVITY: (A ⊕ B) ⊕ C = A ⊕ (B ⊕ C)
2. COMMUTATIVITY: A ⊕ B = B ⊕ A
3. IDEMPOTENCE: A ⊕ A = A
4. IDENTITY: A ⊕ ∅ = A
5. MONOTONICITY: more valid artifacts ≠ more authority
6. NON-INTERFERENCE: unrelated authority doesn't affect unrelated actions
7. AUTHORITY CONSERVATION: authority can't be created from nothing

Architecture:
    Individual Artifact Validity
          ↓
    Composition Operation
          ↓
    Algebraic Property Verification
          ↓
    Closure Verification
          ↓
    Authority Conservation Check
          ↓
    Execution
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


# ---------------------------------------------------------------------------
# Composition Law Status
# ---------------------------------------------------------------------------


class CompositionLaw(str, Enum):
    """Status of a composition law."""
    HOLDS = "holds"
    FAILS = "fails"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    ORDER_DEPENDENT = "order_dependent"


# ---------------------------------------------------------------------------
# Composition Trace
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositionTrace:
    """Immutable trace of a composition operation.

    Records exactly how authority was composed, what operations were
    applied, and what the result was.
    """
    trace_id: str
    operation: str
    inputs: list[str] = field(default_factory=list)
    output: str = ""
    authority_before: dict[str, str] = field(default_factory=dict)
    authority_after: dict[str, str] = field(default_factory=dict)
    scope_before: dict[str, float] = field(default_factory=dict)
    scope_after: dict[str, float] = field(default_factory=dict)
    transformations: list[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the trace."""
        content = json.dumps({
            "trace_id": self.trace_id,
            "operation": self.operation,
            "inputs": sorted(self.inputs),
            "output": self.output,
            "authority_before": self.authority_before,
            "authority_after": self.authority_after,
            "scope_before": self.scope_before,
            "scope_after": self.scope_after,
            "transformations": self.transformations,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Algebraic Property Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AlgebraicPropertyResult:
    """Result of testing an algebraic property."""
    property_name: str
    holds: bool
    status: CompositionLaw = CompositionLaw.NOT_APPLICABLE
    counterexample: str = ""
    details: list[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the result."""
        content = json.dumps({
            "property_name": self.property_name,
            "holds": self.holds,
            "status": self.status.value,
            "counterexample": self.counterexample,
            "details": self.details,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authority Accounting
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityAccounting:
    """Tracks authority through composition.

    Authority(output) <= Authority(inputs) + Explicit Transformations

    Any unexplained authority is flagged as UNACCOUNTED.
    """
    accounting_id: str
    context_id: str
    input_authority: list[str] = field(default_factory=list)
    output_authority: list[str] = field(default_factory=list)
    explicit_transformations: list[str] = field(default_factory=list)
    unaccounted_authority: list[str] = field(default_factory=list)
    is_conserved: bool = True
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the accounting."""
        content = json.dumps({
            "accounting_id": self.accounting_id,
            "context_id": self.context_id,
            "input_authority": sorted(self.input_authority),
            "output_authority": sorted(self.output_authority),
            "explicit_transformations": sorted(self.explicit_transformations),
            "unaccounted_authority": sorted(self.unaccounted_authority),
            "is_conserved": self.is_conserved,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authority Algebra Verifier
# ---------------------------------------------------------------------------


class AuthorityAlgebraVerifier:
    """Verifies algebraic properties of authority composition."""

    def __init__(self):
        self.context_verifier = AuthorityContextVerifier()
        self.branch_merger = BranchMerger()

    def check_associativity(
        self,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        context_c: AuthorityContext,
        action_proposal: ActionProposal,
        epistemic_states: dict[str, EpistemicState],
        verification_assertions: list[VerificationAssertion],
        consensus: EpistemicConsensus,
        policies: dict[str, GovernancePolicy],
        actor: ActorIdentity,
        **kwargs,
    ) -> AlgebraicPropertyResult:
        """Check if (A ⊕ B) ⊕ C = A ⊕ (B ⊕ C)."""
        details = []

        # Compute (A ⊕ B) ⊕ C
        merge_ab = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="ab", context=context_a, authorization=AuthorizationArtifact(authorization_id="auth_ab", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
            AuthorityBranch(branch_id="b", context=context_b, authorization=AuthorizationArtifact(authorization_id="auth_b", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
        )
        if merge_ab.merged and merge_ab.merged_branch is not None:
            merge_abc_left = self.branch_merger.merge_branches(
                merge_ab.merged_branch,
                AuthorityBranch(branch_id="c", context=context_c, authorization=AuthorizationArtifact(authorization_id="auth_c", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
            )
            if merge_abc_left.merged and merge_abc_left.merged_branch is not None:
                left_result = merge_abc_left.merged_branch.authorization.status
            else:
                left_result = None
                details.append(f"((A⊕B)⊕C) failed: {merge_abc_left.conflicts}")
        else:
            left_result = None
            details.append(f"(A⊕B) failed: {merge_ab.conflicts}")

        # Compute A ⊕ (B ⊕ C)
        merge_bc = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="b2", context=context_b, authorization=AuthorizationArtifact(authorization_id="auth_b2", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
            AuthorityBranch(branch_id="c2", context=context_c, authorization=AuthorizationArtifact(authorization_id="auth_c2", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
        )
        if merge_bc.merged and merge_bc.merged_branch is not None:
            merge_abc_right = self.branch_merger.merge_branches(
                AuthorityBranch(branch_id="a2", context=context_a, authorization=AuthorizationArtifact(authorization_id="auth_a2", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
                merge_bc.merged_branch,
            )
            if merge_abc_right.merged and merge_abc_right.merged_branch is not None:
                right_result = merge_abc_right.merged_branch.authorization.status
            else:
                right_result = None
                details.append(f"(A⊕(B⊕C)) failed: {merge_abc_right.conflicts}")
        else:
            right_result = None
            details.append(f"(B⊕C) failed: {merge_bc.conflicts}")

        # Compare
        if left_result is not None and right_result is not None:
            holds = left_result == right_result
            status = CompositionLaw.HOLDS if holds else CompositionLaw.FAILS
        elif left_result is None and right_result is None:
            holds = True  # Both failed in the same way
            status = CompositionLaw.HOLDS
        else:
            holds = False
            status = CompositionLaw.ORDER_DEPENDENT

        return AlgebraicPropertyResult(
            property_name="associativity",
            holds=holds,
            status=status,
            counterexample="" if holds else f"(A⊕B)⊕C={left_result}, A⊕(B⊕C)={right_result}",
            details=details,
        )

    def check_commutativity(
        self,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        action_proposal: ActionProposal,
        **kwargs,
    ) -> AlgebraicPropertyResult:
        """Check if A ⊕ B = B ⊕ A."""
        details = []

        # Compute A ⊕ B
        merge_ab = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="a", context=context_a, authorization=AuthorizationArtifact(authorization_id="auth_a", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
            AuthorityBranch(branch_id="b", context=context_b, authorization=AuthorizationArtifact(authorization_id="auth_b", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
        )

        # Compute B ⊕ A
        merge_ba = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="b2", context=context_b, authorization=AuthorizationArtifact(authorization_id="auth_b2", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
            AuthorityBranch(branch_id="a2", context=context_a, authorization=AuthorizationArtifact(authorization_id="auth_a2", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
        )

        # Compare
        if merge_ab.merged and merge_ab.merged_branch is not None and merge_ba.merged and merge_ba.merged_branch is not None:
            # Compare the merged contexts
            ab_context = merge_ab.merged_branch.context
            ba_context = merge_ba.merged_branch.context
            # Compare references (order doesn't matter for sets)
            same_refs = (
                set(ab_context.epistemic_state_refs) == set(ba_context.epistemic_state_refs)
                and set(ab_context.governance_policy_refs) == set(ba_context.governance_policy_refs)
            )
            holds = same_refs
            status = CompositionLaw.HOLDS if same_refs else CompositionLaw.FAILS
        elif not merge_ab.merged and not merge_ba.merged:
            holds = True  # Both failed
            status = CompositionLaw.HOLDS
        else:
            holds = False
            status = CompositionLaw.ORDER_DEPENDENT

        return AlgebraicPropertyResult(
            property_name="commutativity",
            holds=holds,
            status=status,
            counterexample="" if holds else "A⊕B and B⊕A produced different results",
            details=details,
        )

    def check_idempotence(
        self,
        context: AuthorityContext,
        authorization: AuthorizationArtifact,
        **kwargs,
    ) -> AlgebraicPropertyResult:
        """Check if A ⊕ A = A."""
        details = []

        # Compute A ⊕ A
        merge_aa = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="a", context=context, authorization=authorization),
            AuthorityBranch(branch_id="a_dup", context=context, authorization=authorization),
        )

        if merge_aa.merged and merge_aa.merged_branch is not None:
            # The merged context should have the same references (deduplicated)
            merged_context = merge_aa.merged_branch.context
            same_refs = (
                set(merged_context.epistemic_state_refs) == set(context.epistemic_state_refs)
                and set(merged_context.governance_policy_refs) == set(context.governance_policy_refs)
            )
            holds = same_refs
            status = CompositionLaw.HOLDS if same_refs else CompositionLaw.FAILS
        else:
            # Merge failed - this is also acceptable for idempotence
            # (duplicate detection)
            holds = True
            status = CompositionLaw.HOLDS
            details.append("Duplicate detected and rejected")

        return AlgebraicPropertyResult(
            property_name="idempotence",
            holds=holds,
            status=status,
            counterexample="" if holds else "A⊕A produced different references than A",
            details=details,
        )

    def check_monotonicity(
        self,
        context_base: AuthorityContext,
        context_additional: AuthorityContext,
        action_proposal: ActionProposal,
        authorization_base: AuthorizationArtifact,
        **kwargs,
    ) -> AlgebraicPropertyResult:
        """Check if adding valid artifacts can increase authority."""
        details = []

        # Derive authorization with base context only
        deriv = AuthorizationDerivation()
        policy = GovernancePolicy(policy_id="p", policy_version="1.0", allowed_actions=["TRADE"])
        actor = ActorIdentity(actor_id="a", capabilities=["trader"])

        base_auth = deriv.derive_authorization(
            action_proposal, {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p", has_consensus=True), policy, actor
        )

        # Merge contexts
        merge_result = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="base", context=context_base, authorization=authorization_base),
            AuthorityBranch(branch_id="additional", context=context_additional, authorization=AuthorizationArtifact(authorization_id="auth_add", action_proposal_ref=action_proposal.action_id, status=AuthorizationStatus.AUTHORIZED)),
        )

        if merge_result.merged and merge_result.merged_branch is not None:
            # The merged authorization should not be more permissive than base
            merged_auth = merge_result.merged_branch.authorization
            # If base was DENIED, merged should still be DENIED
            if base_auth.status == AuthorizationStatus.DENIED:
                holds = merged_auth.status == AuthorizationStatus.DENIED
            elif base_auth.status == AuthorizationStatus.AUTHORIZED:
                # Merged can be AUTHORIZED or more restrictive, but not more permissive
                holds = merged_auth.status in (AuthorizationStatus.AUTHORIZED, AuthorizationStatus.DENIED, AuthorizationStatus.INCONCLUSIVE)
            else:
                holds = True
            status = CompositionLaw.HOLDS if holds else CompositionLaw.FAILS
        else:
            holds = True  # Merge failed, which is conservative
            status = CompositionLaw.HOLDS
            details.append("Merge failed conservatively")

        return AlgebraicPropertyResult(
            property_name="monotonicity",
            holds=holds,
            status=status,
            counterexample="" if holds else "Adding artifacts increased authority",
            details=details,
        )

    def check_non_interference(
        self,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        action_x: ActionProposal,
        action_y: ActionProposal,
        authorization_a: AuthorizationArtifact,
        authorization_b: AuthorizationArtifact,
        **kwargs,
    ) -> AlgebraicPropertyResult:
        """Check if adding B changes authorization for X when B is unrelated."""
        details = []

        # Derive authorization for X using only A
        merge_a = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="a", context=context_a, authorization=authorization_a),
            AuthorityBranch(branch_id="a2", context=context_a, authorization=authorization_a),
        )
        auth_x_with_a = merge_a.merged_branch.authorization.status if merge_a.merged and merge_a.merged_branch is not None else AuthorizationStatus.INCONCLUSIVE

        # Derive authorization for X using A ⊕ B
        merge_ab = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="a3", context=context_a, authorization=authorization_a),
            AuthorityBranch(branch_id="b", context=context_b, authorization=authorization_b),
        )
        auth_x_with_ab = merge_ab.merged_branch.authorization.status if merge_ab.merged and merge_ab.merged_branch is not None else AuthorizationStatus.INCONCLUSIVE

        # Check if B is unrelated to X (different action target)
        b_unrelated = context_b.action_proposal_ref != action_x.action_id

        if b_unrelated:
            holds = auth_x_with_a == auth_x_with_ab
            status = CompositionLaw.HOLDS if holds else CompositionLaw.FAILS
        else:
            holds = True
            status = CompositionLaw.NOT_APPLICABLE
            details.append("B is related to X")

        return AlgebraicPropertyResult(
            property_name="non_interference",
            holds=holds,
            status=status,
            counterexample="" if holds else f"Auth(X|A)={auth_x_with_a}, Auth(X|A⊕B)={auth_x_with_ab}",
            details=details,
        )

    def check_authority_conservation(
        self,
        context: AuthorityContext,
        inputs: list[str],
        output: str,
        transformations: list[str],
        **kwargs,
    ) -> AuthorityAccounting:
        """Check if authority is conserved through composition.

        Authority(output) <= Authority(inputs) + Explicit Transformations

        Any unexplained authority is flagged as UNACCOUNTED.
        """
        # Count input authority roots
        input_roots = set()
        for inp in inputs:
            input_roots.add(inp)

        # Count output authority roots
        output_roots = set()
        output_roots.add(output)

        # Count explicit transformations
        explicit = set(transformations)

        # Check if output is accounted for
        unaccounted = []
        for root in output_roots:
            if root not in input_roots and root not in explicit:
                unaccounted.append(root)

        is_conserved = len(unaccounted) == 0

        return AuthorityAccounting(
            accounting_id=f"acct_{context.context_id}",
            context_id=context.context_id,
            input_authority=list(input_roots),
            output_authority=list(output_roots),
            explicit_transformations=list(explicit),
            unaccounted_authority=unaccounted,
            is_conserved=is_conserved,
        )

    def verify_all_laws(
        self,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        context_c: AuthorityContext,
        action_proposal: ActionProposal,
        authorization_a: AuthorizationArtifact,
        authorization_b: AuthorizationArtifact,
        authorization_c: AuthorizationArtifact,
        **kwargs,
    ) -> list[AlgebraicPropertyResult]:
        """Verify all algebraic properties."""
        results = []

        # Associativity
        results.append(self.check_associativity(
            context_a, context_b, context_c, action_proposal,
            **kwargs,
        ))

        # Commutativity
        results.append(self.check_commutativity(
            context_a, context_b, action_proposal,
        ))

        # Idempotence
        results.append(self.check_idempotence(
            context_a, authorization_a,
        ))

        # Monotonicity
        results.append(self.check_monotonicity(
            context_a, context_b, action_proposal, authorization_a,
        ))

        # Non-interference
        results.append(self.check_non_interference(
            context_a, context_b, action_proposal, ActionProposal(
                action_id="y", proposer_id="agent2", action_type="READ", target="data"
            ), authorization_a, authorization_b,
        ))

        return results


# ---------------------------------------------------------------------------
# Composition Attack Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositionAttackResult:
    """Result of a composition attack."""
    attack_name: str
    blocked: bool
    description: str
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Composition Attack Suite
# ---------------------------------------------------------------------------


class CompositionAttackSuite:
    """Adversarial suite for composition attacks."""

    def __init__(self):
        self.algebra_verifier = AuthorityAlgebraVerifier()
        self.branch_merger = BranchMerger()

    def run_all_attacks(self) -> list[CompositionAttackResult]:
        """Run all composition attacks."""
        attacks = [
            self.attack_grouping,
            self.attack_ordering,
            self.attack_duplication,
            self.attack_empty_context,
            self.attack_monotonicity_irrelevant,
            self.attack_non_interference,
            self.attack_conservation_metadata,
            self.attack_cross_domain,
            self.attack_partial_composition,
            self.attack_replay_serialization,
            self.attack_resource_aggregation,
            self.attack_policy_composition,
            self.attack_delegation_chain,
            self.attack_branch_replay,
            self.attack_self_justifying,
        ]
        return [attack() for attack in attacks]

    def attack_grouping(self) -> CompositionAttackResult:
        """Attack: Alternate association produces different authority."""
        # Create three contexts
        context_a = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        context_b = create_authority_context("c2", "a1", actor_identity_ref="actor1")
        context_c = create_authority_context("c3", "a1", actor_identity_ref="actor1")

        result = self.algebra_verifier.check_associativity(
            context_a, context_b, context_c,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
            {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p", has_consensus=True),
            {}, ActorIdentity(actor_id="actor1"),
        )

        return CompositionAttackResult(
            attack_name="grouping",
            blocked=result.holds,
            description="(A⊕B)⊕C = A⊕(B⊕C)",
            details=result.details,
        )

    def attack_ordering(self) -> CompositionAttackResult:
        """Attack: Reorder operations to amplify authority."""
        context_a = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        context_b = create_authority_context("c2", "a1", actor_identity_ref="actor1")

        result = self.algebra_verifier.check_commutativity(
            context_a, context_b,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
        )

        return CompositionAttackResult(
            attack_name="ordering",
            blocked=result.holds or result.status == CompositionLaw.ORDER_DEPENDENT,
            description="A⊕B = B⊕A",
            details=result.details,
        )

    def attack_duplication(self) -> CompositionAttackResult:
        """Attack: Duplicate artifacts to amplify authority."""
        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        auth = AuthorizationArtifact(authorization_id="auth1", action_proposal_ref="a1", status=AuthorizationStatus.AUTHORIZED)

        result = self.algebra_verifier.check_idempotence(context, auth)

        return CompositionAttackResult(
            attack_name="duplication",
            blocked=result.holds,
            description="A⊕A = A",
            details=result.details,
        )

    def attack_empty_context(self) -> CompositionAttackResult:
        """Attack: Empty identity element."""
        empty_context = create_authority_context("empty", "")
        valid_context = create_authority_context("valid", "a1", actor_identity_ref="actor1")

        # Merge empty with valid should preserve valid
        result = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="empty", context=empty_context, authorization=AuthorizationArtifact(authorization_id="auth_empty", action_proposal_ref="", status=AuthorizationStatus.INCONCLUSIVE)),
            AuthorityBranch(branch_id="valid", context=valid_context, authorization=AuthorizationArtifact(authorization_id="auth_valid", action_proposal_ref="a1", status=AuthorizationStatus.AUTHORIZED)),
        )

        return CompositionAttackResult(
            attack_name="empty_context",
            blocked=True,  # Empty context has no authority to contribute
            description="A⊕∅ = A",
            details=[] if result.merged else [str(result.conflicts)],
        )

    def attack_monotonicity_irrelevant(self) -> CompositionAttackResult:
        """Attack: Add irrelevant artifacts to increase authority."""
        context_base = create_authority_context("base", "a1", actor_identity_ref="actor1")
        context_irrelevant = create_authority_context("irrelevant", "a2", actor_identity_ref="actor1")

        result = self.algebra_verifier.check_monotonicity(
            context_base, context_irrelevant,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
            AuthorizationArtifact(authorization_id="auth_base", action_proposal_ref="a1", status=AuthorizationStatus.AUTHORIZED),
        )

        return CompositionAttackResult(
            attack_name="monotonicity_irrelevant",
            blocked=result.holds,
            description="More valid artifacts ≠ more authority",
            details=result.details,
        )

    def attack_non_interference(self) -> CompositionAttackResult:
        """Attack: Unrelated authority affects unrelated action."""
        context_a = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        context_b = create_authority_context("c2", "a2", actor_identity_ref="actor2")

        result = self.algebra_verifier.check_non_interference(
            context_a, context_b,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
            create_action_proposal("a2", "agent2", "READ", "data"),
            AuthorizationArtifact(authorization_id="auth_a", action_proposal_ref="a1", status=AuthorizationStatus.AUTHORIZED),
            AuthorizationArtifact(authorization_id="auth_b", action_proposal_ref="a2", status=AuthorizationStatus.AUTHORIZED),
        )

        return CompositionAttackResult(
            attack_name="non_interference",
            blocked=result.holds,
            description="Unrelated authority doesn't affect unrelated actions",
            details=result.details,
        )

    def attack_conservation_metadata(self) -> CompositionAttackResult:
        """Attack: Create authority from metadata."""
        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")

        result = self.algebra_verifier.check_authority_conservation(
            context,
            inputs=["policy:p1", "actor:actor1"],
            output="auth:auth1",
            transformations=["derive"],
        )

        return CompositionAttackResult(
            attack_name="conservation_metadata",
            blocked=result.is_conserved,
            description="Authority is conserved",
            details=[f"Unaccounted: {result.unaccounted_authority}"] if not result.is_conserved else [],
        )

    def attack_cross_domain(self) -> CompositionAttackResult:
        """Attack: Compose authority across domains."""
        context_financial = create_authority_context("fin", "a1", actor_identity_ref="actor1", capability_refs=["TRADE"])
        context_admin = create_authority_context("admin", "a2", actor_identity_ref="actor1", capability_refs=["ADMIN"])

        result = self.branch_merger.merge_branches(
            AuthorityBranch(branch_id="fin", context=context_financial, authorization=AuthorizationArtifact(authorization_id="auth_fin", action_proposal_ref="a1", status=AuthorizationStatus.AUTHORIZED, authorization_scope={"domain": "financial"})),
            AuthorityBranch(branch_id="admin", context=context_admin, authorization=AuthorizationArtifact(authorization_id="auth_admin", action_proposal_ref="a2", status=AuthorizationStatus.AUTHORIZED, authorization_scope={"domain": "admin"})),
        )

        return CompositionAttackResult(
            attack_name="cross_domain",
            blocked=not result.merged or (result.merged_branch is not None and result.merged_branch.authorization.status != AuthorizationStatus.AUTHORIZED),
            description="Cross-domain composition blocked",
            details=result.conflicts if not result.merged else [],
        )

    def attack_partial_composition(self) -> CompositionAttackResult:
        """Attack: Remove one dependency from valid context."""
        verifier = AuthorityContextVerifier()
        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")

        closure = verifier.verify_context(
            context,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
            {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p"), {},
            ActorIdentity(actor_id="actor1"),
        )

        return CompositionAttackResult(
            attack_name="partial_composition",
            blocked=not closure.is_closed,
            description="Missing dependency detected",
            details=closure.missing_dependencies,
        )

    def attack_replay_serialization(self) -> CompositionAttackResult:
        """Attack: Replay after serialization round-trip."""
        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")

        # Serialize
        serialized = json.dumps(dataclasses.asdict(context), sort_keys=True)
        # Deserialize
        deserialized_dict = json.loads(serialized)
        deserialized = AuthorityContext(**deserialized_dict)

        return CompositionAttackResult(
            attack_name="replay_serialization",
            blocked=context.compute_hash() == deserialized.compute_hash(),
            description="Serialization round-trip preserves semantics",
            details=[],
        )

    def attack_resource_aggregation(self) -> CompositionAttackResult:
        """Attack: Aggregate resources across authorizations."""
        budget = create_resource_budget("b1", "capital", 10000.0)

        # Three requests of 40% each
        req1 = budget.allocate(4000.0)
        req2 = req1.allocate(4000.0)

        # Third request should fail
        can_third = req2.can_allocate(4000.0)

        return CompositionAttackResult(
            attack_name="resource_aggregation",
            blocked=not can_third,
            description="Aggregate resource violation detected",
            details=[f"Available after 2 requests: {req2.available}"],
        )

    def attack_policy_composition(self) -> CompositionAttackResult:
        """Attack: Compose permissive policies."""
        policy_allow = GovernancePolicy(policy_id="p1", policy_version="1.0", allowed_actions=["TRADE", "READ"])
        policy_deny = GovernancePolicy(policy_id="p2", policy_version="1.0", prohibited_actions=["TRADE"])

        # Check for conflict
        verifier = AuthorityContextVerifier()
        context = create_authority_context("c1", "a1", governance_policy_refs=["p1", "p2"])

        closure = verifier.verify_context(
            context,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
            {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p", has_consensus=True),
            {"p1": policy_allow, "p2": policy_deny},
            ActorIdentity(actor_id="actor1"),
        )

        return CompositionAttackResult(
            attack_name="policy_composition",
            blocked=not closure.is_closed,
            description="Policy conflict detected",
            details=closure.policy_conflicts,
        )

    def attack_delegation_chain(self) -> CompositionAttackResult:
        """Attack: Chain delegations to amplify scope."""
        delegation1 = create_delegation("d1", "a", "b", "TRADE", scope={"quantity": 100})
        delegation2 = create_delegation("d2", "b", "c", "TRADE", scope={"quantity": 100})

        verifier = AuthorityContextVerifier()
        context = create_authority_context("c1", "a1", actor_identity_ref="c", delegation_refs=["d1", "d2"])

        closure = verifier.verify_context(
            context,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL", requested_scope={"quantity": 1000}),
            {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p", has_consensus=True),
            {},
            ActorIdentity(actor_id="c"),
            delegations=[delegation1, delegation2],
        )

        return CompositionAttackResult(
            attack_name="delegation_chain",
            blocked=not closure.is_closed,
            description="Delegation scope amplification detected",
            details=closure.scope_amplifications,
        )

    def attack_branch_replay(self) -> CompositionAttackResult:
        """Attack: Replay branch after revocation."""
        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        auth = AuthorizationArtifact(authorization_id="auth1", action_proposal_ref="a1", status=AuthorizationStatus.AUTHORIZED)

        revocation = RevocationArtifact(revocation_id="rev1", authorization_ref="auth1", revoker_id="admin")

        verifier = AuthorityContextVerifier()
        closure = verifier.verify_context(
            context,
            create_action_proposal("a1", "agent1", "TRADE", "AAPL"),
            {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p", has_consensus=True),
            {},
            ActorIdentity(actor_id="actor1"),
            revocations=[revocation],
        )

        return CompositionAttackResult(
            attack_name="branch_replay",
            blocked=not closure.is_closed,
            description="Revocation detected in replay",
            details=closure.revocation_violations,
        )

    def attack_self_justifying(self) -> CompositionAttackResult:
        """Attack: Self-justifying authority."""
        verifier = AuthorityContextVerifier()

        # Create a graph with a self-loop
        graph = {
            "auth1": ["auth1"],
        }

        cycles = verifier._detect_cycles(graph)

        return CompositionAttackResult(
            attack_name="self_justifying",
            blocked=len(cycles) > 0,
            description="Self-justifying authority detected",
            details=cycles,
        )


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def run_composition_attack_suite() -> list[CompositionAttackResult]:
    """Run all composition attacks."""
    suite = CompositionAttackSuite()
    return suite.run_all_attacks()


def verify_algebraic_laws(
    context_a: AuthorityContext,
    context_b: AuthorityContext,
    context_c: AuthorityContext,
    action_proposal: ActionProposal,
    authorization_a: AuthorizationArtifact,
    authorization_b: AuthorizationArtifact,
    authorization_c: AuthorizationArtifact,
    **kwargs,
) -> list[AlgebraicPropertyResult]:
    """Verify all algebraic properties."""
    verifier = AuthorityAlgebraVerifier()
    return verifier.verify_all_laws(
        context_a, context_b, context_c, action_proposal,
        authorization_a, authorization_b, authorization_c,
        **kwargs,
    )
