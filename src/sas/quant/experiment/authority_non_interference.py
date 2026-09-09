"""Authority Non-Interference and Dependency-Scoped Composition.

Investigates why non-interference was PARTIAL and establishes
dependency-scoped authority composition.

The core invariant:

    B ⟂ X ⇒ Decision(X, A) = Decision(X, A ⊕ B)

where ⟂ is explicit authority non-interference.

Architecture:
    Authority Decision
          ↓
    Dependency Graph Construction
          ↓
    Interference Analysis
          ↓
    Decision Stability Verification
          ↓
    Dependency-Scoped Execution
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


# ---------------------------------------------------------------------------
# Dependency Types
# ---------------------------------------------------------------------------


class DependencyType(str, Enum):
    """Types of authority dependency."""
    DIRECT = "direct"             # Explicitly declared dependency
    INDIRECT = "indirect"         # Transitive dependency
    RESOURCE = "resource"         # Shared resource dependency
    TEMPORAL = "temporal"         # Shared temporal constraint
    POLICY = "policy"             # Policy interaction
    ACTOR = "actor"               # Actor identity dependency
    DELEGATION = "delegation"     # Delegation chain dependency
    EPISTEMIC = "epistemic"       # Epistemic state dependency
    VERIFICATION = "verification" # Verification dependency
    CONSENSUS = "consensus"       # Consensus dependency
    REVOCATION = "revocation"     # Revocation propagation
    PROVENANCE = "provenance"     # Provenance dependency
    NONE = "none"                 # No dependency
    UNKNOWN = "unknown"           # Cannot determine


# ---------------------------------------------------------------------------
# Authority Dependency
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDependency:
    """Explicit dependency edge in the authority graph."""
    source: str
    target: str
    dependency_type: DependencyType
    description: str = ""
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the dependency."""
        content = json.dumps({
            "source": self.source,
            "target": self.target,
            "dependency_type": self.dependency_type.value,
            "description": self.description,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Authority Dependency Graph
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityDependencyGraph:
    """Graph of authority dependencies."""
    graph_id: str
    dependencies: list[AuthorityDependency] = field(default_factory=list)
    roots: list[str] = field(default_factory=list)
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the graph."""
        content = json.dumps({
            "graph_id": self.graph_id,
            "dependencies": [d.compute_hash() for d in self.dependencies],
            "roots": sorted(self.roots),
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def has_dependency(self, source: str, target: str) -> bool:
        """Check if there's a dependency from source to target."""
        return any(
            d.source == source and d.target == target
            for d in self.dependencies
        )

    def get_dependencies(self, target: str) -> list[AuthorityDependency]:
        """Get all dependencies targeting a specific node."""
        return [d for d in self.dependencies if d.target == target]

    def get_dependents(self, source: str) -> list[AuthorityDependency]:
        """Get all dependents of a specific node."""
        return [d for d in self.dependencies if d.source == source]

    def is_independent(self, source: str, target: str) -> bool:
        """Check if source is independent of target."""
        return not self.has_dependency(source, target)

    def get_closure(self, node: str) -> set[str]:
        """Get the dependency closure for a node."""
        closure = set()
        to_process = [node]
        while to_process:
            current = to_process.pop()
            if current not in closure:
                closure.add(current)
                deps = self.get_dependents(current)
                to_process.extend([d.target for d in deps])
        return closure


# ---------------------------------------------------------------------------
# Interference Type
# ---------------------------------------------------------------------------


class InterferenceType(str, Enum):
    """Types of authority interference."""
    EXPECTED = "expected"                           # Legitimate dependency
    EXPLICITLY_DECLARED = "explicitly_declared"     # Declared dependency
    RESOURCE_CONTENTION = "resource_contention"     # Shared resource
    TEMPORAL_CONTENTION = "temporal_contention"     # Shared temporal window
    POLICY_CONFLICT = "policy_conflict"             # Policy interaction
    REVOCATION_PROPAGATION = "revocation_propagation" # Revocation chain
    UNAUTHORIZED_INTERFERENCE = "unauthorized_interference" # Security failure
    UNDECLARED_DEPENDENCY = "undeclared_dependency" # Missing dependency edge
    UNKNOWN = "unknown"                             # Cannot determine


# ---------------------------------------------------------------------------
# Interference Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InterferenceResult:
    """Result of an interference test."""
    action: str
    baseline_context: str
    extended_context: str
    baseline_decision: str
    extended_decision: str
    interference_detected: bool
    interference_type: InterferenceType = InterferenceType.UNKNOWN
    explanation: str = ""
    dependency_path: list[str] = field(default_factory=list)

    @property
    def is_authorized(self) -> bool:
        """Check if the interference is authorized."""
        return self.interference_type in (
            InterferenceType.EXPECTED,
            InterferenceType.EXPLICITLY_DECLARED,
            InterferenceType.RESOURCE_CONTENTION,
            InterferenceType.TEMPORAL_CONTENTION,
            InterferenceType.POLICY_CONFLICT,
            InterferenceType.REVOCATION_PROPAGATION,
        )


# ---------------------------------------------------------------------------
# Decision Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionArtifact:
    """Structured authorization decision."""
    decision_id: str
    action: str
    subject: str
    actor: str
    resources: dict[str, float] = field(default_factory=dict)
    policy_refs: list[str] = field(default_factory=list)
    temporal_context: dict[str, str] = field(default_factory=dict)
    required_epistemic: dict[str, str] = field(default_factory=dict)
    required_verification: list[str] = field(default_factory=list)
    authority_roots: list[str] = field(default_factory=list)
    dependency_closure: list[str] = field(default_factory=list)
    scope: dict[str, float] = field(default_factory=dict)
    disposition: AuthorizationStatus = AuthorizationStatus.INCONCLUSIVE
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of the decision."""
        content = json.dumps({
            "decision_id": self.decision_id,
            "action": self.action,
            "subject": self.subject,
            "actor": self.actor,
            "resources": self.resources,
            "policy_refs": sorted(self.policy_refs),
            "temporal_context": self.temporal_context,
            "required_epistemic": self.required_epistemic,
            "required_verification": sorted(self.required_verification),
            "authority_roots": sorted(self.authority_roots),
            "dependency_closure": sorted(self.dependency_closure),
            "scope": self.scope,
            "disposition": self.disposition.value,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_semantically_equivalent(self, other: "DecisionArtifact") -> bool:
        """Check semantic equivalence (ignoring IDs)."""
        return (
            self.action == other.action
            and self.subject == other.subject
            and self.actor == other.actor
            and self.disposition == other.disposition
            and set(self.authority_roots) == set(other.authority_roots)
            and set(self.policy_refs) == set(other.policy_refs)
        )


# ---------------------------------------------------------------------------
# Authority Non-Interference Verifier
# ---------------------------------------------------------------------------


class AuthorityNonInterferenceVerifier:
    """Verifies authority non-interference properties."""

    def __init__(self):
        self.context_verifier = AuthorityContextVerifier()

    def build_dependency_graph(
        self,
        action: ActionProposal,
        context: AuthorityContext,
        epistemic_states: dict[str, EpistemicState],
        policies: dict[str, GovernancePolicy],
        actor: ActorIdentity,
        delegations: list[DelegationArtifact] | None = None,
        resource_budgets: dict[str, ResourceBudget] | None = None,
        revocations: list[RevocationArtifact] | None = None,
    ) -> AuthorityDependencyGraph:
        """Build the authority dependency graph."""
        dependencies = []
        roots = []

        # Actor dependencies
        for policy_ref in context.governance_policy_refs:
            if policy_ref in policies:
                policy = policies[policy_ref]
                dependencies.append(AuthorityDependency(
                    source=f"actor:{actor.actor_id}",
                    target=f"policy:{policy_ref}",
                    dependency_type=DependencyType.DIRECT,
                    description="Actor bound to policy",
                ))
                roots.append(f"actor:{actor.actor_id}")

        # Policy dependencies
        for policy_ref in context.governance_policy_refs:
            if policy_ref in policies:
                roots.append(f"policy:{policy_ref}")

        # Delegation dependencies
        if delegations:
            for delegation in delegations:
                dependencies.append(AuthorityDependency(
                    source=f"delegation:{delegation.delegation_id}",
                    target=f"actor:{delegation.delegator_id}",
                    dependency_type=DependencyType.DELEGATION,
                    description=f"Delegation chain: {delegation.delegator_id} -> {delegation.delegate_id}",
                ))
                roots.append(f"actor:{delegation.delegator_id}")

        # Epistemic dependencies
        for state_ref in context.epistemic_state_refs:
            if state_ref in epistemic_states:
                dependencies.append(AuthorityDependency(
                    source=f"auth:{action.action_id}",
                    target=f"state:{state_ref}",
                    dependency_type=DependencyType.EPISTEMIC,
                    description="Authorization depends on epistemic state",
                ))

        # Resource dependencies
        if resource_budgets:
            for budget_ref in context.resource_constraint_refs:
                if budget_ref in resource_budgets:
                    dependencies.append(AuthorityDependency(
                        source=f"auth:{action.action_id}",
                        target=f"budget:{budget_ref}",
                        dependency_type=DependencyType.RESOURCE,
                        description="Authorization consumes resources",
                    ))

        # Revocation dependencies
        if revocations:
            for revocation in revocations:
                dependencies.append(AuthorityDependency(
                    source=f"revocation:{revocation.revocation_id}",
                    target=f"auth:{revocation.authorization_ref}",
                    dependency_type=DependencyType.REVOCATION,
                    description="Revocation propagates to authorization",
                ))

        return AuthorityDependencyGraph(
            graph_id=f"graph_{action.action_id}",
            dependencies=dependencies,
            roots=roots,
        )

    def check_interference(
        self,
        action: ActionProposal,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        decision_a: DecisionArtifact,
        decision_ab: DecisionArtifact,
        graph_a: AuthorityDependencyGraph,
        graph_ab: AuthorityDependencyGraph,
    ) -> InterferenceResult:
        """Check if adding B interferes with authorization for X."""
        # Check if decisions differ
        decisions_differ = not decision_a.is_semantically_equivalent(decision_ab)

        if not decisions_differ:
            return InterferenceResult(
                action=action.action_id,
                baseline_context=context_a.context_id,
                extended_context=context_b.context_id,
                baseline_decision=decision_a.disposition.value,
                extended_decision=decision_ab.disposition.value,
                interference_detected=False,
                interference_type=InterferenceType.EXPECTED,
                explanation="Decisions are semantically equivalent",
            )

        # Determine interference type
        interference_type = self._classify_interference(
            action, context_a, context_b, decision_a, decision_ab, graph_a, graph_ab
        )

        # Find dependency path
        dependency_path = self._find_dependency_path(graph_ab, action.action_id)

        return InterferenceResult(
            action=action.action_id,
            baseline_context=context_a.context_id,
            extended_context=context_b.context_id,
            baseline_decision=decision_a.disposition.value,
            extended_decision=decision_ab.disposition.value,
            interference_detected=True,
            interference_type=interference_type,
            explanation=self._explain_interference(interference_type),
            dependency_path=dependency_path,
        )

    def _classify_interference(
        self,
        action: ActionProposal,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        decision_a: DecisionArtifact,
        decision_ab: DecisionArtifact,
        graph_a: AuthorityDependencyGraph,
        graph_ab: AuthorityDependencyGraph,
    ) -> InterferenceType:
        """Classify the type of interference."""
        # Check for resource contention
        if self._has_resource_contention(context_a, context_b):
            return InterferenceType.RESOURCE_CONTENTION

        # Check for temporal contention
        if self._has_temporal_contention(context_a, context_b):
            return InterferenceType.TEMPORAL_CONTENTION

        # Check for policy conflict
        if self._has_policy_conflict(context_a, context_b):
            return InterferenceType.POLICY_CONFLICT

        # Check for revocation propagation
        if self._has_revocation_propagation(context_a, context_b):
            return InterferenceType.REVOCATION_PROPAGATION

        # Check for explicit dependency
        if self._has_explicit_dependency(action, context_b, graph_ab):
            return InterferenceType.EXPLICITLY_DECLARED

        # Check for undeclared dependency
        if self._has_undeclared_dependency(action, context_a, context_b, graph_a, graph_ab):
            return InterferenceType.UNDECLARED_DEPENDENCY

        return InterferenceType.UNAUTHORIZED_INTERFERENCE

    def _has_resource_contention(
        self, context_a: AuthorityContext, context_b: AuthorityContext
    ) -> bool:
        """Check if contexts share resource constraints."""
        return bool(
            set(context_a.resource_constraint_refs)
            & set(context_b.resource_constraint_refs)
        )

    def _has_temporal_contention(
        self, context_a: AuthorityContext, context_b: AuthorityContext
    ) -> bool:
        """Check if contexts share temporal constraints."""
        return bool(
            set(context_a.temporal_constraints.keys())
            & set(context_b.temporal_constraints.keys())
        )

    def _has_policy_conflict(
        self, context_a: AuthorityContext, context_b: AuthorityContext
    ) -> bool:
        """Check if contexts have potentially conflicting policies."""
        return bool(
            set(context_a.governance_policy_refs)
            & set(context_b.governance_policy_refs)
        )

    def _has_revocation_propagation(
        self, context_a: AuthorityContext, context_b: AuthorityContext
    ) -> bool:
        """Check if revocations in B affect A."""
        return bool(
            set(context_a.provenance_refs)
            & set(context_b.revocation_refs)
        )

    def _has_explicit_dependency(
        self,
        action: ActionProposal,
        context_b: AuthorityContext,
        graph: AuthorityDependencyGraph,
    ) -> bool:
        """Check if B has an explicit dependency on action."""
        return graph.has_dependency(
            f"auth:{action.action_id}",
            f"context:{context_b.context_id}",
        )

    def _has_undeclared_dependency(
        self,
        action: ActionProposal,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        graph_a: AuthorityDependencyGraph,
        graph_ab: AuthorityDependencyGraph,
    ) -> bool:
        """Check if there's an undeclared dependency."""
        # Check if graph_b has new dependencies that graph_a doesn't
        deps_a = {(d.source, d.target) for d in graph_a.dependencies}
        deps_b = {(d.source, d.target) for d in graph_ab.dependencies}
        new_deps = deps_b - deps_a
        return len(new_deps) > 0

    def _find_dependency_path(
        self, graph: AuthorityDependencyGraph, target: str
    ) -> list[str]:
        """Find the dependency path to target."""
        paths = []
        for dep in graph.dependencies:
            if dep.target == target:
                paths.append(f"{dep.source} -> {dep.target}")
        return paths

    def _explain_interference(self, interference_type: InterferenceType) -> str:
        """Generate human-readable explanation."""
        explanations = {
            InterferenceType.EXPECTED: "Legitimate dependency",
            InterferenceType.EXPLICITLY_DECLARED: "Explicitly declared dependency",
            InterferenceType.RESOURCE_CONTENTION: "Shared resource contention",
            InterferenceType.TEMPORAL_CONTENTION: "Shared temporal constraint",
            InterferenceType.POLICY_CONFLICT: "Policy conflict",
            InterferenceType.REVOCATION_PROPAGATION: "Revocation propagation",
            InterferenceType.UNAUTHORIZED_INTERFERENCE: "UNAUTHORIZED: Authority leak detected",
            InterferenceType.UNDECLARED_DEPENDENCY: "Undeclared dependency found",
            InterferenceType.UNKNOWN: "Cannot determine interference type",
        }
        return explanations.get(interference_type, "Unknown")


# ---------------------------------------------------------------------------
# Decision Builder
# ---------------------------------------------------------------------------


class DecisionBuilder:
    """Builds structured decision artifacts."""

    def build_decision(
        self,
        action: ActionProposal,
        context: AuthorityContext,
        authorization: AuthorizationArtifact,
        actor: ActorIdentity,
        graph: AuthorityDependencyGraph,
        resource_budgets: dict[str, ResourceBudget] | None = None,
    ) -> DecisionArtifact:
        """Build a decision artifact."""
        # Compute dependency closure
        closure = graph.get_closure(f"auth:{action.action_id}")

        # Compute scope from authorization
        scope = dict(authorization.authorization_scope)

        # Compute resources from budgets
        resources = {}
        if resource_budgets:
            for budget in resource_budgets.values():
                resources[budget.resource_type] = budget.available

        return DecisionArtifact(
            decision_id=f"decision_{action.action_id}_{context.context_id}",
            action=action.action_id,
            subject=action.target,
            actor=actor.actor_id,
            resources=resources,
            policy_refs=list(context.governance_policy_refs),
            temporal_context=dict(context.temporal_constraints),
            required_epistemic={},
            required_verification=list(context.verification_assertion_refs),
            authority_roots=list(graph.roots),
            dependency_closure=list(closure),
            scope=scope,
            disposition=authorization.status,
        )


# ---------------------------------------------------------------------------
# Interference Attack
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InterferenceAttack:
    """Definition of an interference attack."""
    attack_id: str
    category: str
    description: str
    context_extensions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Interference Attack Suite
# ---------------------------------------------------------------------------


class InterferenceAttackSuite:
    """Comprehensive interference attack suite."""

    def __init__(self):
        self.non_interference_verifier = AuthorityNonInterferenceVerifier()
        self.decision_builder = DecisionBuilder()

    def run_all_attacks(self) -> list[InterferenceResult]:
        """Run all interference attacks."""
        attacks = [
            self.attack_unrelated_actor,
            self.attack_unrelated_policy,
            self.attack_unrelated_delegation,
            self.attack_unrelated_resource,
            self.attack_unrelated_proposition,
            self.attack_unrelated_evidence,
            self.attack_unrelated_epistemic_state,
            self.attack_unrelated_verification,
            self.attack_unrelated_consensus,
            self.attack_unrelated_temporal,
            self.attack_unrelated_revocation,
            self.attack_unrelated_execution,
            self.attack_unrelated_provenance,
            self.attack_unrelated_cache,
            self.attack_unrelated_serialization,
            self.attack_unrelated_recovery,
            self.attack_unrelated_retry,
            self.attack_unrelated_branch,
            self.attack_unrelated_error,
            self.attack_unrelated_capability,
            self.attack_shared_actor,
            self.attack_shared_policy,
            self.attack_shared_delegation,
            self.attack_shared_resource,
            self.attack_shared_proposition,
            self.attack_shared_evidence,
            self.attack_shared_epistemic,
            self.attack_shared_verifier,
            self.attack_shared_consensus,
            self.attack_shared_temporal,
            self.attack_unrelated_plus_revoked,
            self.attack_unrelated_plus_expired,
            self.attack_unrelated_plus_stronger_capability,
            self.attack_unrelated_plus_larger_budget,
            self.attack_unrelated_plus_stronger_epistemic,
            self.attack_unrelated_plus_majority_consensus,
            self.attack_unrelated_plus_governance_approval,
            self.attack_unrelated_plus_execution_success,
            self.attack_unrelated_plus_serialized,
            self.attack_unrelated_plus_recovered,
            self.attack_nested_delegation,
            self.attack_cross_actor_delegation,
            self.attack_shared_policy_separate_actors,
            self.attack_shared_budget_separate_actions,
            self.attack_shared_temporal_separate_actions,
            self.attack_revocation_propagation,
            self.attack_branch_merge,
            self.attack_branch_replay,
            self.attack_partial_failure,
            self.attack_concurrent_authorization,
        ]
        return [attack() for attack in attacks]

    def _create_base_context(self) -> tuple:
        """Create base context for attacks."""
        action = create_action_proposal("action_x", "agent_x", "TRADE", "AAPL")
        context = create_authority_context(
            "ctx_a", "action_x",
            actor_identity_ref="actor_a",
            governance_policy_refs=["policy_x"],
            epistemic_state_refs=["state_x"],
            verification_assertion_refs=["verif_x"],
            resource_constraint_refs=["budget_x"],
        )
        policy = create_governance_policy("policy_x", "1.0", allowed_actions=["TRADE"])
        actor = create_actor_identity("actor_a", capabilities=["trader"])
        budget = create_resource_budget("budget_x", "capital", 10000.0)
        return action, context, policy, actor, budget

    def _create_unrelated_context(self) -> tuple:
        """Create unrelated context for attacks."""
        unrelated_action = create_action_proposal("action_y", "agent_y", "READ", "data")
        unrelated_context = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_b",
            governance_policy_refs=["policy_y"],
            epistemic_state_refs=["state_y"],
            verification_assertion_refs=["verif_y"],
            resource_constraint_refs=["budget_y"],
        )
        unrelated_policy = create_governance_policy("policy_y", "1.0", allowed_actions=["READ"])
        unrelated_actor = create_actor_identity("actor_b", capabilities=["reader"])
        unrelated_budget = create_resource_budget("budget_y", "storage", 1000.0)
        return unrelated_action, unrelated_context, unrelated_policy, unrelated_actor, unrelated_budget

    def _run_interference_test(
        self,
        attack_name: str,
        action: ActionProposal,
        context_a: AuthorityContext,
        context_b: AuthorityContext,
        policy: GovernancePolicy,
        actor: ActorIdentity,
        budget: ResourceBudget,
        extensions: list[str] | None = None,
    ) -> InterferenceResult:
        """Run a single interference test."""
        # Build dependency graph for context A
        graph_a = self.non_interference_verifier.build_dependency_graph(
            action, context_a, {}, {"policy_x": policy}, actor,
            resource_budgets={"budget_x": budget},
        )

        # Derive authorization for context A
        deriv = AuthorizationDerivation()
        auth_a = deriv.derive_authorization(
            action, {}, [], EpistemicConsensus(consensus_id="c", proposition_id="p", has_consensus=True),
            policy, actor,
        )

        # Build decision for context A
        decision_a = self.decision_builder.build_decision(
            action, context_a, auth_a, actor, graph_a,
            resource_budgets={"budget_x": budget},
        )

        # Merge contexts
        merger = BranchMerger()
        merge_result = merger.merge_branches(
            AuthorityBranch(branch_id="a", context=context_a, authorization=auth_a),
            AuthorityBranch(branch_id="b", context=context_b, authorization=AuthorizationArtifact(authorization_id="auth_b", action_proposal_ref=action.action_id, status=AuthorizationStatus.AUTHORIZED)),
        )

        if merge_result.merged and merge_result.merged_branch is not None:
            merged_context = merge_result.merged_branch.context
            merged_auth = merge_result.merged_branch.authorization

            # Build dependency graph for merged context
            graph_ab = self.non_interference_verifier.build_dependency_graph(
                action, merged_context, {}, {"policy_x": policy}, actor,
                resource_budgets={"budget_x": budget},
            )

            # Build decision for merged context
            decision_ab = self.decision_builder.build_decision(
                action, merged_context, merged_auth, actor, graph_ab,
                resource_budgets={"budget_x": budget},
            )

            # Check interference
            return self.non_interference_verifier.check_interference(
                action, context_a, context_b, decision_a, decision_ab, graph_a, graph_ab
            )
        else:
            # Merge failed - no interference possible
            return InterferenceResult(
                action=action.action_id,
                baseline_context=context_a.context_id,
                extended_context=context_b.context_id,
                baseline_decision=auth_a.status.value,
                extended_decision="MERGE_FAILED",
                interference_detected=False,
                interference_type=InterferenceType.EXPECTED,
                explanation="Contexts are independent (merge failed due to actor mismatch)",
            )

    def attack_unrelated_actor(self) -> InterferenceResult:
        """Test: Unrelated actor doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_actor", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_policy(self) -> InterferenceResult:
        """Test: Unrelated policy doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_policy", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_delegation(self) -> InterferenceResult:
        """Test: Unrelated delegation doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_delegation", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_resource(self) -> InterferenceResult:
        """Test: Unrelated resource doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_resource", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_proposition(self) -> InterferenceResult:
        """Test: Unrelated proposition doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_proposition", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_evidence(self) -> InterferenceResult:
        """Test: Unrelated evidence doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_evidence", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_epistemic_state(self) -> InterferenceResult:
        """Test: Unrelated epistemic state doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_epistemic_state", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_verification(self) -> InterferenceResult:
        """Test: Unrelated verification doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_verification", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_consensus(self) -> InterferenceResult:
        """Test: Unrelated consensus doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_consensus", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_temporal(self) -> InterferenceResult:
        """Test: Unrelated temporal window doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_temporal", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_revocation(self) -> InterferenceResult:
        """Test: Unrelated revocation doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_revocation", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_execution(self) -> InterferenceResult:
        """Test: Unrelated execution doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_execution", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_provenance(self) -> InterferenceResult:
        """Test: Unrelated provenance doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_provenance", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_cache(self) -> InterferenceResult:
        """Test: Unrelated cache doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_cache", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_serialization(self) -> InterferenceResult:
        """Test: Unrelated serialization doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_serialization", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_recovery(self) -> InterferenceResult:
        """Test: Unrelated recovery state doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_recovery", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_retry(self) -> InterferenceResult:
        """Test: Unrelated retry state doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_retry", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_branch(self) -> InterferenceResult:
        """Test: Unrelated branch doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_branch", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_error(self) -> InterferenceResult:
        """Test: Unrelated error state doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_error", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_capability(self) -> InterferenceResult:
        """Test: Unrelated capability doesn't affect authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_capability", action, context_a, context_b, policy, actor, budget)

    def attack_shared_actor(self) -> InterferenceResult:
        """Test: Shared actor affects authorization (legitimate dependency)."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",  # Same actor
            governance_policy_refs=["policy_y"],
        )
        return self._run_interference_test("shared_actor", action, context_a, context_b, policy, actor, budget)

    def attack_shared_policy(self) -> InterferenceResult:
        """Test: Shared policy affects authorization (legitimate dependency)."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            governance_policy_refs=["policy_x"],  # Same policy
        )
        return self._run_interference_test("shared_policy", action, context_a, context_b, policy, actor, budget)

    def attack_shared_delegation(self) -> InterferenceResult:
        """Test: Shared delegation affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            delegation_refs=["delegation_x"],
        )
        context_a = create_authority_context(
            "ctx_a", "action_x",
            actor_identity_ref="actor_a",
            governance_policy_refs=["policy_x"],
            delegation_refs=["delegation_x"],
        )
        return self._run_interference_test("shared_delegation", action, context_a, context_b, policy, actor, budget)

    def attack_shared_resource(self) -> InterferenceResult:
        """Test: Shared resource affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            resource_constraint_refs=["budget_x"],  # Same budget
        )
        return self._run_interference_test("shared_resource", action, context_a, context_b, policy, actor, budget)

    def attack_shared_proposition(self) -> InterferenceResult:
        """Test: Shared proposition affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            epistemic_state_refs=["state_x"],  # Same state
        )
        return self._run_interference_test("shared_proposition", action, context_a, context_b, policy, actor, budget)

    def attack_shared_evidence(self) -> InterferenceResult:
        """Test: Shared evidence affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            epistemic_state_refs=["state_x"],
        )
        return self._run_interference_test("shared_evidence", action, context_a, context_b, policy, actor, budget)

    def attack_shared_epistemic(self) -> InterferenceResult:
        """Test: Shared epistemic prerequisite affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            epistemic_state_refs=["state_x"],
        )
        return self._run_interference_test("shared_epistemic", action, context_a, context_b, policy, actor, budget)

    def attack_shared_verifier(self) -> InterferenceResult:
        """Test: Shared verifier affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            verification_assertion_refs=["verif_x"],
        )
        return self._run_interference_test("shared_verifier", action, context_a, context_b, policy, actor, budget)

    def attack_shared_consensus(self) -> InterferenceResult:
        """Test: Shared consensus prerequisite affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            consensus_refs=["consensus_x"],
        )
        context_a = create_authority_context(
            "ctx_a", "action_x",
            actor_identity_ref="actor_a",
            governance_policy_refs=["policy_x"],
            consensus_refs=["consensus_x"],
        )
        return self._run_interference_test("shared_consensus", action, context_a, context_b, policy, actor, budget)

    def attack_shared_temporal(self) -> InterferenceResult:
        """Test: Shared temporal constraint affects authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            temporal_constraints={"session": "2024-01-01"},
        )
        context_a = create_authority_context(
            "ctx_a", "action_x",
            actor_identity_ref="actor_a",
            governance_policy_refs=["policy_x"],
            temporal_constraints={"session": "2024-01-01"},
        )
        return self._run_interference_test("shared_temporal", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_revoked(self) -> InterferenceResult:
        """Test: Unrelated artifact + revoked."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_revoked", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_expired(self) -> InterferenceResult:
        """Test: Unrelated artifact + expired."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_expired", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_stronger_capability(self) -> InterferenceResult:
        """Test: Unrelated artifact + stronger capability."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_stronger_capability", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_larger_budget(self) -> InterferenceResult:
        """Test: Unrelated artifact + larger budget."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_larger_budget", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_stronger_epistemic(self) -> InterferenceResult:
        """Test: Unrelated artifact + stronger epistemic state."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_stronger_epistemic", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_majority_consensus(self) -> InterferenceResult:
        """Test: Unrelated artifact + majority consensus."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_majority_consensus", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_governance_approval(self) -> InterferenceResult:
        """Test: Unrelated artifact + governance approval."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_governance_approval", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_execution_success(self) -> InterferenceResult:
        """Test: Unrelated artifact + execution success."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_execution_success", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_serialized(self) -> InterferenceResult:
        """Test: Unrelated artifact + serialized state."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_serialized", action, context_a, context_b, policy, actor, budget)

    def attack_unrelated_plus_recovered(self) -> InterferenceResult:
        """Test: Unrelated artifact + recovered state."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("unrelated_plus_recovered", action, context_a, context_b, policy, actor, budget)

    def attack_nested_delegation(self) -> InterferenceResult:
        """Test: Nested delegation chains."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_b",
            delegation_refs=["delegation_b"],
        )
        return self._run_interference_test("nested_delegation", action, context_a, context_b, policy, actor, budget)

    def attack_cross_actor_delegation(self) -> InterferenceResult:
        """Test: Cross-actor delegation."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_b",
        )
        return self._run_interference_test("cross_actor_delegation", action, context_a, context_b, policy, actor, budget)

    def attack_shared_policy_separate_actors(self) -> InterferenceResult:
        """Test: Shared policy with separate actors."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_b",
            governance_policy_refs=["policy_x"],  # Same policy
        )
        return self._run_interference_test("shared_policy_separate_actors", action, context_a, context_b, policy, actor, budget)

    def attack_shared_budget_separate_actions(self) -> InterferenceResult:
        """Test: Shared budget with separate actions."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            resource_constraint_refs=["budget_x"],  # Same budget
        )
        return self._run_interference_test("shared_budget_separate_actions", action, context_a, context_b, policy, actor, budget)

    def attack_shared_temporal_separate_actions(self) -> InterferenceResult:
        """Test: Shared temporal session with separate actions."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_a",
            temporal_constraints={"session": "2024-01-01"},
        )
        context_a = create_authority_context(
            "ctx_a", "action_x",
            actor_identity_ref="actor_a",
            governance_policy_refs=["policy_x"],
            temporal_constraints={"session": "2024-01-01"},
        )
        return self._run_interference_test("shared_temporal_separate_actions", action, context_a, context_b, policy, actor, budget)

    def attack_revocation_propagation(self) -> InterferenceResult:
        """Test: Revocation propagation through delegation."""
        action, context_a, policy, actor, budget = self._create_base_context()
        context_b = create_authority_context(
            "ctx_b", "action_y",
            actor_identity_ref="actor_b",
            revocation_refs=["revocation_x"],
        )
        return self._run_interference_test("revocation_propagation", action, context_a, context_b, policy, actor, budget)

    def attack_branch_merge(self) -> InterferenceResult:
        """Test: Branch merge."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("branch_merge", action, context_a, context_b, policy, actor, budget)

    def attack_branch_replay(self) -> InterferenceResult:
        """Test: Branch replay."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("branch_replay", action, context_a, context_b, policy, actor, budget)

    def attack_partial_failure(self) -> InterferenceResult:
        """Test: Partial failure."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("partial_failure", action, context_a, context_b, policy, actor, budget)

    def attack_concurrent_authorization(self) -> InterferenceResult:
        """Test: Concurrent authorization."""
        action, context_a, policy, actor, budget = self._create_base_context()
        _, context_b, _, _, _ = self._create_unrelated_context()
        return self._run_interference_test("concurrent_authorization", action, context_a, context_b, policy, actor, budget)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def run_interference_attack_suite() -> list[InterferenceResult]:
    """Run all interference attacks."""
    suite = InterferenceAttackSuite()
    return suite.run_all_attacks()


def check_non_interference(
    action: ActionProposal,
    context_a: AuthorityContext,
    context_b: AuthorityContext,
    policy: GovernancePolicy,
    actor: ActorIdentity,
    budget: ResourceBudget,
) -> InterferenceResult:
    """Check non-interference for a specific action and contexts."""
    suite = InterferenceAttackSuite()
    return suite._run_interference_test(
        "custom", action, context_a, context_b, policy, actor, budget
    )
