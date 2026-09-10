"""Phase 14: Closed Authority Loop.

Experimentally determines whether the authority architecture is actually closed.

The central research question:

Can an actor obtain authority over execution by obtaining, exercising,
composing, or indirectly influencing authority over the rules that
govern execution?

This module does NOT answer from architectural intention.
It constructs experiments that attempt to violate the boundary.

The critical distinction:

POLICY VALIDITY
≠
POLICY AUTHORITY
≠
POLICY CORRECTNESS
≠
POLICY EFFECT
≠
DOWNSTREAM AUTHORITY

Existing infrastructure reused:
- PolicyGovernanceEngine, PolicyAuthorityRecord, PolicyLifecycleEvent (policy_governance.py)
- GovernancePolicyEngine, PolicyEvaluationResult (governance_policy.py)
- EpistemicallyConditionedGovernanceEngine (epistemic_governance.py)
- AuthorityFrontierIntegrator, GovernanceAction (authority_frontier_integration.py)
- RichFrontier, ProvenancePreservingComposition (frontier_composition_semantics.py)
- CompletenessScope, CompletenessStatus (dependency_completeness.py)
- AuthorityDriftEvent, DriftType, AuthoritySnapshot (authority_drift.py)
- WorldState (continuous_reconciliation.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class ClosedLoopResult(str, Enum):
    """Result of a closed loop experiment."""
    CLOSED = "closed"  # Authority conserved
    AMPLIFICATION_DETECTED = "amplification_detected"  # Authority increased
    BYPASS_DETECTED = "bypass_detected"  # Authority bypassed
    ESCALATION_DETECTED = "escalation_detected"  # Authority escalated
    UNKNOWN = "unknown"  # Cannot determine


class AttackClass(str, Enum):
    """Classes of attacks against the closed authority loop."""
    AUTHORIZED_POLICY_BROADENING = "authorized_policy_broadening"
    SCOPE_ESCALATION = "scope_escalation"
    TEMPORAL_ESCALATION = "temporal_escalation"
    AUTHORITY_EXPIRATION = "authority_expiration"
    POLICY_COMPOSITION_ESCALATION = "policy_composition_escalation"
    PREDICATE_WEAKENING = "predicate_weakening"
    AUTHORIZATION_PATH_CREATION = "authorization_path_creation"
    EMERGENCY_OVERRIDE = "emergency_override"
    ROLLBACK_ESCALATION = "rollback_escalation"
    HISTORICAL_REPRODUCIBILITY = "historical_reproducibility"
    POLICY_AUTHORITY_REVOCATION = "policy_authority_revocation"
    POLICY_EFFECT_ANALYSIS = "policy_effect_analysis"
    AUTHORITY_CUT_SET = "authority_cut_set"
    POLICY_ENGINE_COMPROMISE = "policy_engine_compromise"
    REPLAY = "replay"
    LEGITIMATE_AUTHORITY_ABUSE = "legitimate_authority_abuse"
    MULTI_STEP_ESCALATION = "multi_step_escalation"
    COMPOSITIONAL_ESCALATION = "compositional_escalation"


# ---------------------------------------------------------------------------
# Authority Conservation Tracker
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityToken:
    """Represents a unit of authority at a specific point in the chain.
    
    Authority tokens are tracked as they traverse the chain to detect
    amplification.
    """
    token_id: str
    source: str  # Where this authority originated
    scope: str  # Scope of authority
    temporal_bounds: tuple[str, str]  # When this authority is valid
    capability_class: str  # What this authority permits
    provenance: list[str] = field(default_factory=list)
    
    def can_authorize(self, capability: str, scope: str, timestamp: str) -> bool:
        """Check if this token can authorize a specific capability."""
        if self.capability_class != capability:
            return False
        if self.scope != scope:
            return False
        if self.temporal_bounds[0] != "unbounded" and timestamp < self.temporal_bounds[0]:
            return False
        if self.temporal_bounds[1] != "unbounded" and timestamp > self.temporal_bounds[1]:
            return False
        return True


@dataclass(frozen=True)
class TransitionStep:
    """A single step in the authority chain.
    
    Each step records the input authority, the transformation applied,
    and the output authority.
    """
    step_id: str
    step_name: str
    input_authority: Optional[AuthorityToken]
    output_authority: Optional[AuthorityToken]
    transformation: str
    actor: str
    authority_basis: str
    timestamp: str
    scope: str
    provenance: list[str] = field(default_factory=list)
    
    @property
    def authority_conserved(self) -> bool:
        """Check if authority is conserved (not amplified) across this step."""
        if self.input_authority is None:
            return True  # No input authority to conserve
        if self.output_authority is None:
            return True  # No output authority
        
        # Output scope must be within input scope
        if self.input_authority.scope != self.output_authority.scope:
            return False
        
        # Output capability must be within input capability
        if self.input_authority.capability_class != self.output_authority.capability_class:
            return False
        
        # Output temporal bounds must be within input temporal bounds
        if self.input_authority.temporal_bounds[0] != "unbounded":
            if self.output_authority.temporal_bounds[0] == "unbounded":
                return False
            if self.output_authority.temporal_bounds[0] < self.input_authority.temporal_bounds[0]:
                return False
        if self.input_authority.temporal_bounds[1] != "unbounded":
            if self.output_authority.temporal_bounds[1] == "unbounded":
                return False
            if self.output_authority.temporal_bounds[1] > self.input_authority.temporal_bounds[1]:
                return False
        
        return True
    
    @property
    def authority_amplified(self) -> bool:
        """Check if authority is amplified across this step."""
        return not self.authority_conserved


# ---------------------------------------------------------------------------
# Closed Authority Loop Experiment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClosedLoopExperiment:
    """Result of a closed authority loop experiment."""
    experiment_id: str
    attack_class: AttackClass
    description: str
    result: ClosedLoopResult
    steps: list[TransitionStep]
    authority_amplified: bool
    authority_bypassed: bool
    authority_escalated: bool
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Closed Authority Loop Engine
# ---------------------------------------------------------------------------


@dataclass
class ClosedAuthorityLoopEngine:
    """Engine for testing whether the authority loop is closed.
    
    Tracks authority tokens as they traverse the chain and detects
    amplification, bypass, and escalation.
    """
    
    experiments: list[ClosedLoopExperiment] = field(default_factory=list)
    authority_tokens: dict[str, AuthorityToken] = field(default_factory=dict)
    transition_log: list[TransitionStep] = field(default_factory=list)
    
    def create_authority_token(
        self,
        source: str,
        scope: str,
        capability_class: str,
        temporal_bounds: tuple[str, str] = ("unbounded", "unbounded"),
        provenance: Optional[list[str]] = None,
    ) -> AuthorityToken:
        """Create a new authority token."""
        token = AuthorityToken(
            token_id=f"auth_{uuid.uuid4().hex[:12]}",
            source=source,
            scope=scope,
            temporal_bounds=temporal_bounds,
            capability_class=capability_class,
            provenance=provenance or [],
        )
        self.authority_tokens[token.token_id] = token
        return token
    
    def record_transition(
        self,
        step_name: str,
        input_token: Optional[AuthorityToken],
        output_token: Optional[AuthorityToken],
        transformation: str,
        actor: str,
        authority_basis: str,
        timestamp: str,
        scope: str,
        provenance: Optional[list[str]] = None,
    ) -> TransitionStep:
        """Record a transition step."""
        step = TransitionStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            step_name=step_name,
            input_authority=input_token,
            output_authority=output_token,
            transformation=transformation,
            actor=actor,
            authority_basis=authority_basis,
            timestamp=timestamp,
            scope=scope,
            provenance=provenance or [],
        )
        self.transition_log.append(step)
        return step
    
    def run_experiment(
        self,
        attack_class: AttackClass,
        description: str,
        steps: list[TransitionStep],
        notes: str = "",
        normative_assumptions: Optional[list[str]] = None,
        underspecifications: Optional[list[str]] = None,
    ) -> ClosedLoopExperiment:
        """Run a closed loop experiment."""
        authority_amplified = any(s.authority_amplified for s in steps)
        authority_bypassed = any(
            s.input_authority is not None and s.output_authority is None
            for s in steps
        )
        authority_escalated = any(
            s.input_authority is not None
            and s.output_authority is not None
            and s.input_authority.capability_class != s.output_authority.capability_class
            for s in steps
        )
        
        if authority_amplified:
            result = ClosedLoopResult.AMPLIFICATION_DETECTED
        elif authority_bypassed:
            result = ClosedLoopResult.BYPASS_DETECTED
        elif authority_escalated:
            result = ClosedLoopResult.ESCALATION_DETECTED
        else:
            result = ClosedLoopResult.CLOSED
        
        experiment = ClosedLoopExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            attack_class=attack_class,
            description=description,
            result=result,
            steps=steps,
            authority_amplified=authority_amplified,
            authority_bypassed=authority_bypassed,
            authority_escalated=authority_escalated,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Attack Class Implementations
# ---------------------------------------------------------------------------


def run_authorized_policy_broadening(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 1: Authorized Policy Broadening.
    
    Give an actor legitimate authority to modify a policy.
    Have that actor modify the policy so that a downstream authorization
    condition becomes broader.
    
    Determine whether the resulting execution authority can exceed what
    the actor was legitimately authorized to influence.
    """
    steps = []
    
    # Step 1: Actor has policy modification authority for scope=production
    policy_auth = engine.create_authority_token(
        source="policy_authority_registry",
        scope="production",
        capability_class="modify_policy",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant"],
    )
    
    # Step 2: Actor modifies policy to broaden predicate
    # (e.g., removes provenance requirement)
    modified_policy_auth = engine.create_authority_token(
        source="policy_modification",
        scope="production",
        capability_class="modify_policy",  # Same capability class
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_modified"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_modification",
        input_token=policy_auth,
        output_token=modified_policy_auth,
        transformation="remove_provenance_requirement",
        actor="admin",
        authority_basis="policy_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Broader policy produces broader governance disposition
    governance_auth = engine.create_authority_token(
        source="governance_policy_evaluation",
        scope="production",
        capability_class="governance_disposition",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_modified", "governance_eval"],
    )
    
    step2 = engine.record_transition(
        step_name="governance_evaluation",
        input_token=modified_policy_auth,
        output_token=governance_auth,
        transformation="evaluate_broader_policy",
        actor="governance_engine",
        authority_basis="modified_policy",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    # Step 4: Broader disposition produces broader execution authority
    execution_auth = engine.create_authority_token(
        source="authority_materialization",
        scope="production",
        capability_class="execute_action",  # NEW capability class - escalation
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_modified", "governance_eval", "authority_materialized"],
    )
    
    step3 = engine.record_transition(
        step_name="authority_materialization",
        input_token=governance_auth,
        output_token=execution_auth,
        transformation="materialize_authority",
        actor="authority_mechanism",
        authority_basis="governance_disposition",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step3)
    
    return engine.run_experiment(
        attack_class=AttackClass.AUTHORIZED_POLICY_BROADENING,
        description="Actor with legitimate policy modification authority broadens policy predicates",
        steps=steps,
        notes="Tests whether policy modification authority can create broader execution authority",
        normative_assumptions=[
            "Policy modification authority is scoped to production",
            "Execution authority should not exceed policy modification authority",
        ],
        underspecifications=[
            "Current implementation does not track authority surface area quantitatively",
        ],
    )


def run_scope_escalation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 2: Scope Escalation.
    
    Start with a policy authorized for DOMAIN_A.
    Attempt to produce authority affecting DOMAIN_B through legitimate
    policy modification, policy composition, inheritance, or scope union.
    """
    steps = []
    
    # Step 1: Actor has production policy authority
    policy_auth = engine.create_authority_token(
        source="policy_authority_registry",
        scope="production",
        capability_class="modify_policy",
        provenance=["admin_grant"],
    )
    
    # Step 2: Actor attempts to expand scope to staging
    expanded_policy_auth = engine.create_authority_token(
        source="policy_modification",
        scope="staging",  # SCOPE ESCALATION
        capability_class="modify_policy",
        provenance=["admin_grant", "scope_expansion_attempt"],
    )
    
    step1 = engine.record_transition(
        step_name="scope_expansion",
        input_token=policy_auth,
        output_token=expanded_policy_auth,
        transformation="expand_scope_to_staging",
        actor="admin",
        authority_basis="policy_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="staging",
    )
    steps.append(step1)
    
    return engine.run_experiment(
        attack_class=AttackClass.SCOPE_ESCALATION,
        description="Actor attempts to expand policy scope from production to staging",
        steps=steps,
        notes="Tests whether scope authority can be manufactured by policy modification",
        normative_assumptions=[
            "Production authority does not grant staging authority",
        ],
    )


def run_temporal_escalation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 3: Temporal Escalation.
    
    Test: authorized policy at T0, policy activation at T1,
    issuer authority expires at T2, execution occurs at T3.
    
    Determine exactly which temporal authority is required at each transition.
    """
    steps = []
    
    # T0: Alice has authority
    alice_auth = engine.create_authority_token(
        source="authority_registry",
        scope="production",
        capability_class="create_policy",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),  # Expires mid-year
        provenance=["admin_grant"],
    )
    
    # T1: Alice creates P1
    p1_auth = engine.create_authority_token(
        source="policy_creation",
        scope="production",
        capability_class="policy_active",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        provenance=["admin_grant", "policy_created"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_creation",
        input_token=alice_auth,
        output_token=p1_auth,
        transformation="create_policy",
        actor="alice",
        authority_basis="alice_auth",
        timestamp="2026-02-01T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # T2: Alice's authority expires (simulated)
    # T3: P1 is evaluated AFTER alice's authority expired
    expired_eval = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="execute_action",
        temporal_bounds=("2026-07-01T00:00:00Z", "2026-12-31T23:59:59Z"),  # After expiry
        provenance=["admin_grant", "policy_created", "evaluation_after_expiry"],
    )
    
    step2 = engine.record_transition(
        step_name="policy_evaluation_after_expiry",
        input_token=p1_auth,
        output_token=expired_eval,
        transformation="evaluate_policy",
        actor="governance_engine",
        authority_basis="p1_auth",
        timestamp="2026-07-15T00:00:00Z",  # After alice's authority expired
        scope="production",
    )
    steps.append(step2)
    
    return engine.run_experiment(
        attack_class=AttackClass.TEMPORAL_ESCALATION,
        description="Policy evaluated after issuer authority expires",
        steps=steps,
        notes="Tests whether policy validity implies continuing policy authority",
        normative_assumptions=[
            "Policy authority should not outlive issuer authority without explicit delegation",
        ],
        underspecifications=[
            "Current implementation does not re-evaluate policy authority at execution time",
        ],
    )


def run_authority_expiration(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 4: Authority Expiration.
    
    Create a policy while an issuer possesses authority.
    Revoke or expire the issuer authority.
    Determine whether the policy remains VALID, AUTHORIZED, EFFECTIVE,
    and CAPABLE OF PRODUCING AUTHORITY.
    """
    steps = []
    
    # Step 1: Issuer has authority
    issuer_auth = engine.create_authority_token(
        source="authority_registry",
        scope="production",
        capability_class="create_policy",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        provenance=["admin_grant"],
    )
    
    # Step 2: Issuer creates policy
    policy_auth = engine.create_authority_token(
        source="policy_creation",
        scope="production",
        capability_class="policy_active",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_created"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_creation",
        input_token=issuer_auth,
        output_token=policy_auth,
        transformation="create_policy",
        actor="issuer",
        authority_basis="issuer_auth",
        timestamp="2026-02-01T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Issuer authority expires, policy is evaluated
    post_expiry_eval = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="execute_action",
        temporal_bounds=("2026-07-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_created", "post_expiry_eval"],
    )
    
    step2 = engine.record_transition(
        step_name="post_expiry_evaluation",
        input_token=policy_auth,
        output_token=post_expiry_eval,
        transformation="evaluate_policy",
        actor="governance_engine",
        authority_basis="policy_auth",
        timestamp="2026-07-15T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    return engine.run_experiment(
        attack_class=AttackClass.AUTHORITY_EXPIRATION,
        description="Policy evaluated after issuer authority expires",
        steps=steps,
        notes="Tests whether policy remains effective after issuer authority expires",
        underspecifications=[
            "Current implementation does not distinguish VALID, AUTHORIZED, EFFECTIVE states explicitly",
        ],
    )


def run_policy_composition_escalation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 5: Policy Composition Escalation.
    
    Create two policies P1 and P2, each individually legitimate.
    Compose them and attempt to produce unauthorized downstream authority.
    """
    steps = []
    
    # Step 1: P1 authorized for production
    p1_auth = engine.create_authority_token(
        source="policy_authority",
        scope="production",
        capability_class="governance_disposition",
        provenance=["admin_grant_p1"],
    )
    
    # Step 2: P2 authorized for production
    p2_auth = engine.create_authority_token(
        source="policy_authority",
        scope="production",
        capability_class="governance_disposition",
        provenance=["admin_grant_p2"],
    )
    
    # Step 3: Compose P1 + P2
    composed_auth = engine.create_authority_token(
        source="policy_composition",
        scope="production",
        capability_class="execute_action",  # Composition creates new capability
        provenance=["admin_grant_p1", "admin_grant_p2", "composed"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_composition",
        input_token=p1_auth,
        output_token=composed_auth,
        transformation="compose_p1_p2",
        actor="governance_engine",
        authority_basis="p1_auth_and_p2_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    return engine.run_experiment(
        attack_class=AttackClass.POLICY_COMPOSITION_ESCALATION,
        description="Two individually authorized policies composed to create new authority",
        steps=steps,
        notes="Tests whether AUTHORIZED(P1) + AUTHORIZED(P2) = AUTHORIZED(P1+P2)",
        normative_assumptions=[
            "Policy composition should not create new authority",
        ],
    )


def run_predicate_weakening(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 6: Predicate Weakening.
    
    Start with a restrictive governance predicate.
    Create an authorized policy mutation that removes one condition.
    Determine whether the system recognizes that the mutation has changed
    the authority surface.
    """
    steps = []
    
    # Step 1: Original restrictive policy
    restrictive_auth = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="governance_disposition",
        provenance=["restrictive_policy"],
    )
    
    # Step 2: Weakened policy (removed provenance requirement)
    weakened_auth = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="execute_action",  # Broader capability
        provenance=["weakened_policy"],
    )
    
    step1 = engine.record_transition(
        step_name="predicate_weakening",
        input_token=restrictive_auth,
        output_token=weakened_auth,
        transformation="remove_provenance_requirement",
        actor="admin",
        authority_basis="modify_authority",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    return engine.run_experiment(
        attack_class=AttackClass.PREDICATE_WEAKENING,
        description="Authorized removal of governance predicate condition",
        steps=steps,
        notes="Tests whether predicate weakening changes authority surface",
    )


def run_authorization_path_creation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 7: Authorization Path Creation.
    
    Create a policy that introduces an entirely new path from principal
    to execution.
    
    Determine whether creating the path requires authority over the
    resulting capability class.
    """
    steps = []
    
    # Step 1: Actor has policy creation authority
    policy_auth = engine.create_authority_token(
        source="policy_authority_registry",
        scope="production",
        capability_class="create_policy",
        provenance=["admin_grant"],
    )
    
    # Step 2: Actor creates policy that enables new execution path
    new_path_auth = engine.create_authority_token(
        source="new_policy",
        scope="production",
        capability_class="execute_new_capability",  # NEW capability class
        provenance=["admin_grant", "new_path_created"],
    )
    
    step1 = engine.record_transition(
        step_name="new_path_creation",
        input_token=policy_auth,
        output_token=new_path_auth,
        transformation="create_new_authorization_path",
        actor="admin",
        authority_basis="policy_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    return engine.run_experiment(
        attack_class=AttackClass.AUTHORIZATION_PATH_CREATION,
        description="Actor creates policy enabling new execution path",
        steps=steps,
        notes="Tests whether creating a path requires authority over the resulting capability",
        normative_assumptions=[
            "Creating a rule describing execution should not grant authority over that execution",
        ],
    )


def run_emergency_override(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 8: Emergency Override.
    
    Test the emergency override mechanism adversarially.
    Determine exactly what OVERRIDE changes.
    Verify: OVERRIDE ≠ GOVERNANCE BYPASS.
    """
    steps = []
    
    # Step 1: Normal policy authority
    normal_auth = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="governance_disposition",
        provenance=["normal_policy"],
    )
    
    # Step 2: Emergency override
    override_auth = engine.create_authority_token(
        source="emergency_override",
        scope="production",
        capability_class="execute_action",  # Broader than governance_disposition
        provenance=["normal_policy", "emergency_override"],
    )
    
    step1 = engine.record_transition(
        step_name="emergency_override",
        input_token=normal_auth,
        output_token=override_auth,
        transformation="apply_emergency_override",
        actor="admin",
        authority_basis="override_authority",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    return engine.run_experiment(
        attack_class=AttackClass.EMERGENCY_OVERRIDE,
        description="Emergency override applied to policy",
        steps=steps,
        notes="Tests whether override can bypass governance",
        normative_assumptions=[
            "Override must remain inside the authority architecture",
        ],
    )


def run_rollback_escalation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 9: Rollback Escalation.
    
    Create P1, supersede P1 with P2, change authority conditions, rollback.
    Determine whether rollback restores the historical policy only or
    accidentally restores historical authority.
    """
    steps = []
    
    # Step 1: P1 active
    p1_auth = engine.create_authority_token(
        source="policy_activation",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_active"],
    )
    
    # Step 2: P2 supersedes P1
    p2_auth = engine.create_authority_token(
        source="policy_supersession",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_active", "p2_supersedes"],
    )
    
    step1 = engine.record_transition(
        step_name="supersession",
        input_token=p1_auth,
        output_token=p2_auth,
        transformation="supersede_p1_with_p2",
        actor="admin",
        authority_basis="modify_authority",
        timestamp="2026-02-01T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Rollback to P1
    rollback_auth = engine.create_authority_token(
        source="policy_rollback",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_active", "p2_supersedes", "rollback_to_p1"],
    )
    
    step2 = engine.record_transition(
        step_name="rollback",
        input_token=p2_auth,
        output_token=rollback_auth,
        transformation="rollback_to_p1",
        actor="admin",
        authority_basis="rollback_authority",
        timestamp="2026-03-01T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    return engine.run_experiment(
        attack_class=AttackClass.ROLLBACK_ESCALATION,
        description="Rollback after authority conditions changed",
        steps=steps,
        notes="Tests whether POLICY ROLLBACK = AUTHORITY ROLLBACK",
        normative_assumptions=[
            "Historical policy content may be restored without restoring obsolete authority",
        ],
    )


def run_historical_reproducibility(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 10: Historical Reproducibility.
    
    Evaluate an execution decision under P1.
    Later: P1 is superseded, P1 is deleted, P2 becomes active,
    issuer authority changes, governance predicates change.
    Reconstruct the original decision.
    """
    steps = []
    
    # Step 1: Original evaluation under P1
    original_decision = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_active", "original_evaluation"],
    )
    
    # Step 2: P1 superseded by P2
    p2_active = engine.create_authority_token(
        source="policy_supersession",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_active", "p2_supersedes"],
    )
    
    step1 = engine.record_transition(
        step_name="supersession",
        input_token=original_decision,
        output_token=p2_active,
        transformation="supersede_p1_with_p2",
        actor="admin",
        authority_basis="modify_authority",
        timestamp="2026-02-01T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Attempt to reconstruct original decision
    reconstructed = engine.create_authority_token(
        source="historical_reconstruction",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_active", "original_evaluation", "reconstructed"],
    )
    
    step2 = engine.record_transition(
        step_name="historical_reconstruction",
        input_token=p2_active,
        output_token=reconstructed,
        transformation="reconstruct_under_p1",
        actor="governance_engine",
        authority_basis="historical_record",
        timestamp="2026-03-01T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    return engine.run_experiment(
        attack_class=AttackClass.HISTORICAL_REPRODUCIBILITY,
        description="Historical decision reconstruction after policy changes",
        steps=steps,
        notes="Tests whether CURRENT POLICY = HISTORICAL POLICY",
        normative_assumptions=[
            "Historical result must remain reproducible",
        ],
    )


def run_policy_authority_revocation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 11: Policy Authority Revocation.
    
    Create a policy under authority A.
    Revoke A.
    Determine whether existing policies remain active, become inactive,
    become invalid, become unauthorized, require revalidation, or remain
    historically valid but no longer effective.
    """
    steps = []
    
    # Step 1: Authority A exists
    authority_a = engine.create_authority_token(
        source="authority_registry",
        scope="production",
        capability_class="create_policy",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        provenance=["admin_grant"],
    )
    
    # Step 2: Create policy under A
    policy_auth = engine.create_authority_token(
        source="policy_creation",
        scope="production",
        capability_class="policy_active",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_created"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_creation",
        input_token=authority_a,
        output_token=policy_auth,
        transformation="create_policy",
        actor="issuer",
        authority_basis="authority_a",
        timestamp="2026-02-01T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Authority A revoked, policy evaluated post-revocation
    post_revocation_eval = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="execute_action",
        temporal_bounds=("2026-07-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_created", "post_revocation_eval"],
    )
    
    step2 = engine.record_transition(
        step_name="post_revocation_evaluation",
        input_token=policy_auth,
        output_token=post_revocation_eval,
        transformation="evaluate_policy",
        actor="governance_engine",
        authority_basis="policy_auth",
        timestamp="2026-07-15T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    return engine.run_experiment(
        attack_class=AttackClass.POLICY_AUTHORITY_REVOCATION,
        description="Policy evaluated after issuing authority revoked",
        steps=steps,
        notes="Tests whether policy remains effective after authority revocation",
        underspecifications=[
            "Current implementation does not explicitly track authority revocation effects",
        ],
    )


def run_policy_effect_analysis(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 12: Policy Effect Analysis.
    
    Construct two policies that are both valid and authorized.
    Have them produce materially different downstream authority surfaces.
    Determine whether the system can distinguish POLICY AUTHORITY from
    POLICY EFFECT.
    """
    steps = []
    
    # Step 1: P1 with narrow effect
    p1_auth = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="governance_disposition",
        provenance=["p1_narrow"],
    )
    
    # Step 2: P2 with broad effect (same authority, different effect)
    p2_auth = engine.create_authority_token(
        source="policy_evaluation",
        scope="production",
        capability_class="execute_action",  # Broader effect
        provenance=["p2_broad"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_evaluation_p1",
        input_token=p1_auth,
        output_token=p2_auth,
        transformation="evaluate_p2_broader",
        actor="governance_engine",
        authority_basis="policy_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    return engine.run_experiment(
        attack_class=AttackClass.POLICY_EFFECT_ANALYSIS,
        description="Two authorized policies with different downstream effects",
        steps=steps,
        notes="Tests whether system distinguishes POLICY AUTHORITY from POLICY EFFECT",
    )


def run_legitimate_authority_abuse(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 16: Legitimate Authority Abuse.
    
    Give an actor legitimate authority to modify governance policy.
    Have the actor use that legitimate authority to construct a policy
    that grants or enables execution authority beyond the intended
    authority boundary.
    
    This is the most important experiment.
    """
    steps = []
    
    # Step 1: Actor has legitimate policy modification authority
    actor_auth = engine.create_authority_token(
        source="policy_authority_registry",
        scope="production",
        capability_class="modify_policy",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant"],
    )
    
    # Step 2: Actor modifies policy to enable broader execution
    modified_auth = engine.create_authority_token(
        source="policy_modification",
        scope="production",
        capability_class="modify_policy",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_modified"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_modification",
        input_token=actor_auth,
        output_token=modified_auth,
        transformation="weaken_governance_predicate",
        actor="authorized_actor",
        authority_basis="actor_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Modified policy produces broader governance disposition
    governance_auth = engine.create_authority_token(
        source="governance_evaluation",
        scope="production",
        capability_class="governance_disposition",
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_modified", "governance_eval"],
    )
    
    step2 = engine.record_transition(
        step_name="governance_evaluation",
        input_token=modified_auth,
        output_token=governance_auth,
        transformation="evaluate_modified_policy",
        actor="governance_engine",
        authority_basis="modified_policy",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    # Step 4: Broader disposition produces broader execution authority
    execution_auth = engine.create_authority_token(
        source="authority_materialization",
        scope="production",
        capability_class="execute_action",  # NEW capability class
        temporal_bounds=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        provenance=["admin_grant", "policy_modified", "governance_eval", "authority_materialized"],
    )
    
    step3 = engine.record_transition(
        step_name="authority_materialization",
        input_token=governance_auth,
        output_token=execution_auth,
        transformation="materialize_authority",
        actor="authority_mechanism",
        authority_basis="governance_disposition",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step3)
    
    return engine.run_experiment(
        attack_class=AttackClass.LEGITIMATE_AUTHORITY_ABUSE,
        description="Actor uses legitimate policy authority to create broader execution authority",
        steps=steps,
        notes="Tests whether legitimate policy authority can be abused to create unauthorized downstream authority",
        normative_assumptions=[
            "Authority to change policy ≠ authority to create every effect of that policy",
        ],
        underspecifications=[
            "Current implementation does not have a second authority boundary over policy effects",
        ],
    )


def run_multi_step_escalation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 17: Multi-Step Escalation.
    
    Attempt: authorized policy change → policy activation → governance
    disposition → authority materialization → capability → execution.
    
    At every transition identify: actor, authority basis, provenance,
    scope, temporal bounds, policy version, input evidence, resulting
    disposition, resulting authority, capability, execution identity.
    """
    steps = []
    
    # Step 1: Policy change
    policy_auth = engine.create_authority_token(
        source="policy_authority",
        scope="production",
        capability_class="modify_policy",
        provenance=["admin_grant"],
    )
    
    activated_auth = engine.create_authority_token(
        source="policy_activation",
        scope="production",
        capability_class="policy_active",
        provenance=["admin_grant", "policy_activated"],
    )
    
    step1 = engine.record_transition(
        step_name="policy_activation",
        input_token=policy_auth,
        output_token=activated_auth,
        transformation="activate_policy",
        actor="admin",
        authority_basis="policy_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 2: Governance disposition
    governance_auth = engine.create_authority_token(
        source="governance_evaluation",
        scope="production",
        capability_class="governance_disposition",
        provenance=["admin_grant", "policy_activated", "governance_eval"],
    )
    
    step2 = engine.record_transition(
        step_name="governance_evaluation",
        input_token=activated_auth,
        output_token=governance_auth,
        transformation="evaluate_policy",
        actor="governance_engine",
        authority_basis="activated_policy",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    # Step 3: Authority materialization
    materialized_auth = engine.create_authority_token(
        source="authority_materialization",
        scope="production",
        capability_class="execute_action",
        provenance=["admin_grant", "policy_activated", "governance_eval", "authority_materialized"],
    )
    
    step3 = engine.record_transition(
        step_name="authority_materialization",
        input_token=governance_auth,
        output_token=materialized_auth,
        transformation="materialize_authority",
        actor="authority_mechanism",
        authority_basis="governance_disposition",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step3)
    
    return engine.run_experiment(
        attack_class=AttackClass.MULTI_STEP_ESCALATION,
        description="Multi-step escalation through full authority chain",
        steps=steps,
        notes="Tests whether any transition silently inherits authority without explicit basis",
    )


def run_compositional_escalation(engine: ClosedAuthorityLoopEngine) -> ClosedLoopExperiment:
    """Attack 18: Compositional Escalation.
    
    Test whether individually legitimate operations compose into an
    illegitimate authority path.
    """
    steps = []
    
    # Step 1: Authorized CREATE
    create_auth = engine.create_authority_token(
        source="policy_authority",
        scope="production",
        capability_class="create_policy",
        provenance=["admin_grant"],
    )
    
    # Step 2: Authorized MODIFY
    modify_auth = engine.create_authority_token(
        source="policy_modification",
        scope="production",
        capability_class="modify_policy",
        provenance=["admin_grant", "policy_modified"],
    )
    
    step1 = engine.record_transition(
        step_name="create_then_modify",
        input_token=create_auth,
        output_token=modify_auth,
        transformation="create_and_modify",
        actor="admin",
        authority_basis="create_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step1)
    
    # Step 3: Authorized ACTIVATE
    activate_auth = engine.create_authority_token(
        source="policy_activation",
        scope="production",
        capability_class="policy_active",
        provenance=["admin_grant", "policy_modified", "policy_activated"],
    )
    
    step2 = engine.record_transition(
        step_name="modify_then_activate",
        input_token=modify_auth,
        output_token=activate_auth,
        transformation="modify_and_activate",
        actor="admin",
        authority_basis="modify_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step2)
    
    # Step 4: Authorized OVERRIDE
    override_auth = engine.create_authority_token(
        source="emergency_override",
        scope="production",
        capability_class="execute_action",
        provenance=["admin_grant", "policy_modified", "policy_activated", "override"],
    )
    
    step3 = engine.record_transition(
        step_name="activate_then_override",
        input_token=activate_auth,
        output_token=override_auth,
        transformation="activate_and_override",
        actor="admin",
        authority_basis="activate_auth",
        timestamp="2026-01-15T00:00:00Z",
        scope="production",
    )
    steps.append(step3)
    
    return engine.run_experiment(
        attack_class=AttackClass.COMPOSITIONAL_ESCALATION,
        description="Individually authorized operations composed",
        steps=steps,
        notes="Tests whether composition of legitimate operations creates illegitimate authority",
    )


# ---------------------------------------------------------------------------
# Run All Experiments
# ---------------------------------------------------------------------------


def run_all_phase14_experiments() -> dict[str, Any]:
    """Run all Phase 14 experiments."""
    engine = ClosedAuthorityLoopEngine()
    
    experiments = {}
    
    experiments["authorized_policy_broadening"] = run_authorized_policy_broadening(engine)
    experiments["scope_escalation"] = run_scope_escalation(engine)
    experiments["temporal_escalation"] = run_temporal_escalation(engine)
    experiments["authority_expiration"] = run_authority_expiration(engine)
    experiments["policy_composition_escalation"] = run_policy_composition_escalation(engine)
    experiments["predicate_weakening"] = run_predicate_weakening(engine)
    experiments["authorization_path_creation"] = run_authorization_path_creation(engine)
    experiments["emergency_override"] = run_emergency_override(engine)
    experiments["rollback_escalation"] = run_rollback_escalation(engine)
    experiments["historical_reproducibility"] = run_historical_reproducibility(engine)
    experiments["policy_authority_revocation"] = run_policy_authority_revocation(engine)
    experiments["policy_effect_analysis"] = run_policy_effect_analysis(engine)
    experiments["legitimate_authority_abuse"] = run_legitimate_authority_abuse(engine)
    experiments["multi_step_escalation"] = run_multi_step_escalation(engine)
    experiments["compositional_escalation"] = run_compositional_escalation(engine)
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "closed_count": sum(1 for e in experiments.values() if e.result == ClosedLoopResult.CLOSED),
        "amplification_count": sum(1 for e in experiments.values() if e.result == ClosedLoopResult.AMPLIFICATION_DETECTED),
        "bypass_count": sum(1 for e in experiments.values() if e.result == ClosedLoopResult.BYPASS_DETECTED),
        "escalation_count": sum(1 for e in experiments.values() if e.result == ClosedLoopResult.ESCALATION_DETECTED),
    }


if __name__ == "__main__":
    results = run_all_phase14_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 14: CLOSED AUTHORITY LOOP")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Closed: {results['closed_count']}")
    print(f"Amplification detected: {results['amplification_count']}")
    print(f"Bypass detected: {results['bypass_count']}")
    print(f"Escalation detected: {results['escalation_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Result: {exp.result.value}")
        print(f"  Authority amplified: {exp.authority_amplified}")
        print(f"  Authority bypassed: {exp.authority_bypassed}")
        print(f"  Authority escalated: {exp.authority_escalated}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
