"""Phase 15: Effect Boundary.

Investigates what authority must be established for a policy transformation
to legitimately create or alter downstream authority.

The central question:

WHO HAS AUTHORITY TO CREATE AUTHORITY?

Phase 14 established DOWNSTREAM_AUTHORITY_AMPLIFICATION:
an actor with legitimate MODIFY_POLICY authority can construct policies
whose downstream authority exceeds the actor's legitimate authority.

Phase 15 does NOT immediately implement a fix.
It first determines whether the architecture requires a distinct concept
of POLICY EFFECT AUTHORITY, or whether the amplification reveals a more
fundamental delegation gap.

Existing infrastructure reused:
- PolicyGovernanceEngine, PolicyAuthorityRecord, PolicyLifecycleEvent (policy_governance.py)
- GovernancePolicyEngine, PolicyEvaluationResult (governance_policy.py)
- EpistemicallyConditionedGovernanceEngine (epistemic_governance.py)
- AuthorityFrontierIntegrator, GovernanceAction (authority_frontier_integration.py)
- RichFrontier, ProvenancePreservingComposition (frontier_composition_semantics.py)
- CompletenessScope, CompletenessStatus (dependency_completeness.py)
- AuthorityDriftEvent, DriftType, AuthoritySnapshot (authority_drift.py)
- ConsequentialAuthority, ConditionalAuthority (consequential_authority.py)
- WorldState (continuous_reconciliation.py)
- ClosedAuthorityLoopEngine, AuthorityToken, TransitionStep (closed_authority_loop.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Authority Surface — Multi-Dimensional Authority Representation
# ---------------------------------------------------------------------------


class CapabilityClass(str, Enum):
    """Ordered capability classes.
    
    The ordering is NOT assumed — it is experimentally investigated.
    This enum documents the capability classes observed in the architecture.
    """
    READ_ONLY = "read_only"
    OBSERVE = "observe"
    ANALYZE = "analyze"
    SIMULATE = "simulate"
    RECOMMEND = "recommend"
    GOVERNANCE_DISPOSITION = "governance_disposition"
    AUTHORIZE = "authorize"
    MODIFY_POLICY = "modify_policy"
    CREATE_POLICY = "create_policy"
    ACTIVATE_POLICY = "activate_policy"
    OVERRIDE_POLICY = "override_policy"
    EXECUTE_ACTION = "execute_action"
    EXECUTE_PAYMENT = "execute_payment"
    EXECUTE_SUBPROCESS = "execute_subprocess"
    EXECUTE_NETWORK = "execute_network"
    MUTATE_IDENTITY = "mutate_identity"
    MUTATE_CREDENTIAL = "mutate_credential"
    MUTATE_CONFIGURATION = "mutate_configuration"
    PRODUCE_AUTHORITY = "produce_authority"
    PRODUCE_EXECUTION = "produce_execution"


@dataclass(frozen=True)
class AuthoritySurface:
    """A multi-dimensional representation of authority.
    
    Current architecture treats authority as a flat label.
    Phase 15 investigates whether authority must be treated as a
    surface across multiple dimensions.
    
    Dimensions:
    - principal: who holds the authority
    - operation: what operation is permitted
    - resource: what resource is affected
    - scope: domain/environment scope
    - temporal_interval: when the authority is valid
    - conditions: under what conditions the authority applies
    - provenance: the authority chain that established this
    - policy_lineage: which policy versions produced this
    - capability_class: what class of capability this permits
    """
    principal: str
    operation: str
    resource: str
    scope: str
    temporal_interval: tuple[str, str] = ("unbounded", "unbounded")
    conditions: frozenset[str] = field(default_factory=frozenset)
    provenance: tuple[str, ...] = ()
    policy_lineage: tuple[str, ...] = ()
    capability_class: str = ""
    
    def permits(self, other: "AuthoritySurface") -> bool:
        """Check if this authority surface permits another surface.
        
        This is the core comparison: does this authority cover the
        other authority across all dimensions?
        
        NOTE: This is a hypothesis, not an established invariant.
        The experiments test whether this comparison is meaningful.
        """
        # Principal must match
        if self.principal != other.principal:
            return False
        
        # Operation must cover
        if self.operation != other.operation and self.operation != "*":
            return False
        
        # Resource must cover
        if self.resource != other.resource and self.resource != "*":
            return False
        
        # Scope must cover
        if self.scope != other.scope and self.scope != "*":
            return False
        
        # Temporal interval must contain
        if self.temporal_interval[0] != "unbounded":
            if other.temporal_interval[0] == "unbounded":
                return False
            if other.temporal_interval[0] < self.temporal_interval[0]:
                return False
        if self.temporal_interval[1] != "unbounded":
            if other.temporal_interval[1] == "unbounded":
                return False
            if other.temporal_interval[1] > self.temporal_interval[1]:
                return False
        
        # Conditions must be a superset (more conditions = more restrictive)
        if not self.conditions >= other.conditions:
            return False
        
        return True
    
    def is_broader_than(self, other: "AuthoritySurface") -> bool:
        """Check if this surface is strictly broader than another."""
        if not self.covers(other):
            return False
        # Strictly broader if any dimension is strictly broader
        if self.scope != other.scope and self.scope == "*":
            return True
        if self.resource != other.resource and self.resource == "*":
            return True
        if self.temporal_interval != other.temporal_interval:
            if self.temporal_interval[0] == "unbounded" and other.temporal_interval[0] != "unbounded":
                return True
            if self.temporal_interval[1] == "unbounded" and other.temporal_interval[1] != "unbounded":
                return True
        if self.conditions < other.conditions:  # Fewer conditions = broader
            return True
        return False
    
    def covers(self, other: "AuthoritySurface") -> bool:
        """Alias for permits."""
        return self.permits(other)


@dataclass(frozen=True)
class AuthorityEnvelope:
    """The set of downstream effects a principal is legitimately permitted
    to cause through a specific authority grant.
    
    An envelope is NOT authority. It is a bound on the effects that
    an authority grant can produce.
    """
    envelope_id: str
    principal: str
    granted_authority: AuthoritySurface
    permitted_effects: list[AuthoritySurface]
    max_scope: str
    max_temporal_interval: tuple[str, str]
    max_capability_class: str
    min_conditions: frozenset[str] = field(default_factory=frozenset)
    
    def contains_effect(self, effect: AuthoritySurface) -> bool:
        """Check if an effect is within this envelope."""
        # Effect principal must match envelope principal
        if effect.principal != self.principal:
            return False
        
        # Effect scope must be within max scope
        if effect.scope != self.max_scope and self.max_scope != "*":
            return False
        
        # Effect temporal interval must be within max interval
        if self.max_temporal_interval[0] != "unbounded":
            if effect.temporal_interval[0] == "unbounded":
                return False
            if effect.temporal_interval[0] < self.max_temporal_interval[0]:
                return False
        if self.max_temporal_interval[1] != "unbounded":
            if effect.temporal_interval[1] == "unbounded":
                return False
            if effect.temporal_interval[1] > self.max_temporal_interval[1]:
                return False
        
        # Effect conditions must include at least the minimum
        if not effect.conditions >= self.min_conditions:
            return False
        
        return True


# ---------------------------------------------------------------------------
# Policy Effect Authority
# ---------------------------------------------------------------------------


class PolicyEffectAuthorityType(str, Enum):
    """Types of authority over policy effects.
    
    Having authority to modify a policy does NOT automatically grant
    authority to produce every downstream effect of that policy.
    """
    MODIFY_POLICY = "modify_policy"
    CREATE_POLICY = "create_policy"
    ACTIVATE_POLICY = "activate_policy"
    OVERRIDE_POLICY = "override_policy"
    PRODUCE_GOVERNANCE_DISPOSITION = "produce_governance_disposition"
    PRODUCE_AUTHORITY = "produce_authority"
    PRODUCE_CAPABILITY = "produce_capability"
    PRODUCE_EXECUTION = "produce_execution"


@dataclass(frozen=True)
class PolicyEffectAuthority:
    """Authority to produce specific downstream effects through policy.
    
    This is a HYPOTHETICAL type investigated by Phase 15.
    It may or may not be necessary depending on experimental results.
    """
    authority_id: str
    principal_id: str
    policy_id: str
    effect_types: frozenset[PolicyEffectAuthorityType]
    max_scope: str
    max_temporal_interval: tuple[str, str]
    max_capability_class: str
    conditions: frozenset[str] = field(default_factory=frozenset)
    provenance: tuple[str, ...] = ()
    
    def can_produce_effect(self, effect_type: PolicyEffectAuthorityType) -> bool:
        """Check if this authority can produce a specific effect type."""
        return effect_type in self.effect_types


# ---------------------------------------------------------------------------
# Authority Transformation
# ---------------------------------------------------------------------------


class AuthorityTransformationType(str, Enum):
    """Types of authority transformations."""
    IDENTITY = "identity"  # A → A
    NARROWING = "narrowing"  # A → narrower(A)
    BROADENING = "broadening"  # A → broader(A)
    SCOPE_CHANGE = "scope_change"  # A → different_scope(A)
    TEMPORAL_SHIFT = "temporal_shift"  # A → later(A) or earlier(A)
    CONDITION_CHANGE = "condition_change"  # A → different conditions
    CAPABILITY_TRANSITION = "capability_transition"  # A → different_capability(A)
    NEW_CAPABILITY = "new_capability"  # A → new capability class
    COMPOSITION = "composition"  # A + B → composed


@dataclass(frozen=True)
class AuthorityTransformation:
    """Records a transformation from one authority surface to another."""
    transformation_id: str
    transformation_type: AuthorityTransformationType
    input_surface: AuthoritySurface
    output_surface: AuthoritySurface
    actor: str
    authority_basis: str
    timestamp: str
    policy_id: Optional[str] = None
    provenance: tuple[str, ...] = ()
    
    @property
    def is_conservative(self) -> bool:
        """Check if the transformation is conservative (not amplifying)."""
        return self.input_surface.covers(self.output_surface)
    
    @property
    def is_amplifying(self) -> bool:
        """Check if the transformation is amplifying."""
        return not self.is_conservative


# ---------------------------------------------------------------------------
# Semantic Transition Map
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SemanticTransition:
    """A single transition in the authority semantic map."""
    transition_id: str
    from_concept: str
    to_concept: str
    transformation: str
    authority_required: str
    authority_created: bool
    authority_transformed: bool
    authority_delegated: bool
    authority_materialized: bool
    authority_inherited: bool
    authority_expanded: bool
    authority_restricted: bool
    notes: str = ""


# ---------------------------------------------------------------------------
# Phase 15 Experiment Engine
# ---------------------------------------------------------------------------


class EffectBoundaryResult(str, Enum):
    """Result of an effect boundary experiment."""
    WITHIN_ENVELOPE = "within_envelope"
    EXCEEDS_ENVELOPE = "exceeds_envelope"
    EXPLICITLY_AUTHORIZED = "explicitly_authorized"
    AMPLIFICATION_DETECTED = "amplification_detected"
    DELEGATION_GAP = "delegation_gap"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EffectBoundaryExperiment:
    """Result of an effect boundary experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    result: EffectBoundaryResult
    input_authority: AuthoritySurface
    output_effect: AuthoritySurface
    envelope: Optional[AuthorityEnvelope]
    transformation: AuthorityTransformation
    authority_amplified: bool
    explicitly_authorized: bool
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


@dataclass
class EffectBoundaryEngine:
    """Engine for testing effect boundary requirements."""
    
    experiments: list[EffectBoundaryExperiment] = field(default_factory=list)
    transformations: list[AuthorityTransformation] = field(default_factory=list)
    semantic_transitions: list[SemanticTransition] = field(default_factory=list)
    
    def create_authority_surface(
        self,
        principal: str,
        operation: str,
        resource: str,
        scope: str,
        temporal_interval: tuple[str, str] = ("unbounded", "unbounded"),
        conditions: Optional[frozenset[str]] = None,
        capability_class: str = "",
        provenance: tuple[str, ...] = (),
        policy_lineage: tuple[str, ...] = (),
    ) -> AuthoritySurface:
        """Create a new authority surface."""
        return AuthoritySurface(
            principal=principal,
            operation=operation,
            resource=resource,
            scope=scope,
            temporal_interval=temporal_interval,
            conditions=conditions or frozenset(),
            capability_class=capability_class,
            provenance=provenance,
            policy_lineage=policy_lineage,
        )
    
    def create_envelope(
        self,
        principal: str,
        granted_authority: AuthoritySurface,
        max_scope: str = "production",
        max_temporal_interval: tuple[str, str] = ("unbounded", "unbounded"),
        max_capability_class: str = "",
        min_conditions: Optional[frozenset[str]] = None,
    ) -> AuthorityEnvelope:
        """Create an authority envelope."""
        return AuthorityEnvelope(
            envelope_id=f"env_{uuid.uuid4().hex[:12]}",
            principal=principal,
            granted_authority=granted_authority,
            permitted_effects=[],
            max_scope=max_scope,
            max_temporal_interval=max_temporal_interval,
            max_capability_class=max_capability_class,
            min_conditions=min_conditions or frozenset(),
        )
    
    def record_transformation(
        self,
        transformation_type: AuthorityTransformationType,
        input_surface: AuthoritySurface,
        output_surface: AuthoritySurface,
        actor: str,
        authority_basis: str,
        timestamp: str,
        policy_id: Optional[str] = None,
    ) -> AuthorityTransformation:
        """Record an authority transformation."""
        transformation = AuthorityTransformation(
            transformation_id=f"tx_{uuid.uuid4().hex[:12]}",
            transformation_type=transformation_type,
            input_surface=input_surface,
            output_surface=output_surface,
            actor=actor,
            authority_basis=authority_basis,
            timestamp=timestamp,
            policy_id=policy_id,
        )
        self.transformations.append(transformation)
        return transformation
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        input_authority: AuthoritySurface,
        output_effect: AuthoritySurface,
        envelope: Optional[AuthorityEnvelope] = None,
        transformation: Optional[AuthorityTransformation] = None,
        notes: str = "",
        normative_assumptions: Optional[list[str]] = None,
        underspecifications: Optional[list[str]] = None,
    ) -> EffectBoundaryExperiment:
        """Run an effect boundary experiment."""
        if transformation is None:
            transformation = self.record_transformation(
                transformation_type=AuthorityTransformationType.IDENTITY,
                input_surface=input_authority,
                output_surface=output_effect,
                actor=input_authority.principal,
                authority_basis="experiment",
                timestamp="2026-01-15T00:00:00Z",
            )
        
        authority_amplified = transformation.is_amplifying
        
        if envelope is not None:
            if envelope.contains_effect(output_effect):
                if authority_amplified:
                    result = EffectBoundaryResult.EXCEEDS_ENVELOPE
                else:
                    result = EffectBoundaryResult.WITHIN_ENVELOPE
            else:
                if authority_amplified:
                    result = EffectBoundaryResult.AMPLIFICATION_DETECTED
                else:
                    result = EffectBoundaryResult.DELEGATION_GAP
        else:
            if authority_amplified:
                result = EffectBoundaryResult.AMPLIFICATION_DETECTED
            else:
                result = EffectBoundaryResult.WITHIN_ENVELOPE
        
        experiment = EffectBoundaryExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            result=result,
            input_authority=input_authority,
            output_effect=output_effect,
            envelope=envelope,
            transformation=transformation,
            authority_amplified=authority_amplified,
            explicitly_authorized=False,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Experiment Implementations
# ---------------------------------------------------------------------------


def run_narrow_policy_change(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 1: Policy modification within existing envelope."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="fraud_review_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="fraud_review_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.IDENTITY,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="narrow_policy_change",
        description="Policy modification that stays within existing authority envelope",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether narrow policy changes remain within envelope",
    )


def run_broad_policy_change(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 2: Policy modification that exceeds existing envelope."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="fraud_review_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_payment",  # Different capability class
        resource="fraud_review_policy",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="broad_policy_change",
        description="Policy modification that exceeds existing envelope",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether broad policy changes exceed envelope",
    )


def run_scope_expansion(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 3: Scope expansion through policy modification."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="staging",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",  # Scope escalation
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="staging",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.SCOPE_CHANGE,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="scope_expansion",
        description="Policy modification that expands scope from staging to production",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether scope expansion is detected",
    )


def run_temporal_expansion(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 4: Temporal expansion through policy modification."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        temporal_interval=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),  # Extended
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.TEMPORAL_SHIFT,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="temporal_expansion",
        description="Policy modification that extends temporal validity",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether temporal expansion is detected",
    )


def run_condition_removal(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 5: Condition removal through policy modification."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        conditions=frozenset({"provenance_required", "dual_approval_required"}),
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        conditions=frozenset(),  # Conditions removed
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
        min_conditions=frozenset({"provenance_required", "dual_approval_required"}),
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CONDITION_CHANGE,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="condition_removal",
        description="Policy modification that removes governance conditions",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether condition removal is detected as authority expansion",
    )


def run_new_authorization_path(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 6: New authorization path creation."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="create_policy",
        resource="new_policy",
        scope="production",
        capability_class=CapabilityClass.CREATE_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_new_capability",
        resource="new_resource",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_ACTION,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.CREATE_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.NEW_CAPABILITY,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="create_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="new_authorization_path",
        description="Creating a new policy that enables a new authorization path",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether creating new paths requires authority over the resulting capability",
    )


def run_capability_class_expansion(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 7: Capability class expansion."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="review_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="authorize",
        resource="review_policy",
        scope="production",
        capability_class=CapabilityClass.AUTHORIZE,  # Higher capability
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="capability_class_expansion",
        description="Policy modification that enables higher capability class",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether capability class transitions are detected",
    )


def run_policy_composition(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 8: Policy composition creating new authority."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="composed_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_action",
        resource="composed_resource",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_ACTION,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.COMPOSITION,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="policy_composition",
        description="Two individually authorized policies composed",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether composition creates unauthorized authority",
    )


def run_delegated_meta_authority(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 9: Delegated meta-authority test.
    
    Actor has POLICY_MODIFY_AUTHORITY but no PAYMENT_EXECUTION_AUTHORITY.
    Then granted explicit POLICY_EFFECT_AUTHORITY for payment execution.
    """
    # Actor has policy modify authority
    policy_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    # Actor does NOT have payment execution authority
    # But is granted explicit policy effect authority
    effect_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="produce_authority",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.PRODUCE_AUTHORITY,
        conditions=frozenset({"explicit_effect_authority_granted"}),
    )
    
    # The downstream effect
    output_effect = engine.create_authority_surface(
        principal="governance_admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    # Envelope with explicit effect authority
    envelope = engine.create_envelope(
        principal="governance_admin",
        granted_authority=effect_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.PRODUCE_AUTHORITY,
        min_conditions=frozenset({"explicit_effect_authority_granted"}),
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=effect_auth,
        output_surface=output_effect,
        actor="governance_admin",
        authority_basis="explicit_effect_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="delegated_meta_authority",
        description="Actor with explicit policy effect authority modifies payment policy",
        input_authority=effect_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether explicit effect authority legitimately permits downstream authority",
        normative_assumptions=[
            "Explicit effect authority can be delegated independently of operational authority",
        ],
    )


def run_explicit_effect_authority_boundary(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 10: Policy modification outside effect authority envelope."""
    # Actor has policy modify authority
    policy_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    # Actor has effect authority for payment only
    effect_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="produce_authority",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.PRODUCE_AUTHORITY,
        conditions=frozenset({"explicit_effect_authority_granted"}),
    )
    
    # Attempts to modify identity policy (outside envelope)
    output_effect = engine.create_authority_surface(
        principal="governance_admin",
        operation="mutate_identity",
        resource="identity_policy",
        scope="production",
        capability_class=CapabilityClass.MUTATE_IDENTITY,
    )
    
    # Envelope only covers payment policy
    envelope = engine.create_envelope(
        principal="governance_admin",
        granted_authority=effect_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.PRODUCE_AUTHORITY,
        min_conditions=frozenset({"explicit_effect_authority_granted"}),
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=effect_auth,
        output_surface=output_effect,
        actor="governance_admin",
        authority_basis="explicit_effect_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="explicit_effect_authority_boundary",
        description="Actor attempts to modify policy outside effect authority envelope",
        input_authority=effect_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether effect authority envelope prevents out-of-scope policy modification",
    )


def run_authority_creation_as_governed_operation(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 11: Authority creation as a governed operation."""
    input_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="create_authority",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.AUTHORIZE,
    )
    
    output_effect = engine.create_authority_surface(
        principal="governance_admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="governance_admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.AUTHORIZE,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.NEW_CAPABILITY,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="governance_admin",
        authority_basis="authorize_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="authority_creation_as_governed_operation",
        description="Authority creation as a consequential operation requiring authority",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether CREATE_AUTHORITY requires its own authority basis",
    )


def run_authority_transformation_algebra(engine: EffectBoundaryEngine) -> list[EffectBoundaryExperiment]:
    """Experiment 12: Authority transformation algebra.
    
    Test which transformations preserve authority and which require new authority.
    """
    experiments = []
    
    base_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        temporal_interval=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        conditions=frozenset({"provenance_required"}),
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformations = [
        (AuthorityTransformationType.IDENTITY, "A → A", base_auth),
        (AuthorityTransformationType.NARROWING, "A → narrower(A)", None),  # Would need narrower version
        (AuthorityTransformationType.BROADENING, "A → broader(A)", None),  # Would need broader version
        (AuthorityTransformationType.SCOPE_CHANGE, "A → different_scope(A)", None),
        (AuthorityTransformationType.TEMPORAL_SHIFT, "A → later(A)", None),
        (AuthorityTransformationType.CONDITION_CHANGE, "A → different_conditions(A)", None),
        (AuthorityTransformationType.CAPABILITY_TRANSITION, "A → different_capability(A)", None),
        (AuthorityTransformationType.NEW_CAPABILITY, "A → new_capability(A)", None),
    ]
    
    for tx_type, desc, output in transformations:
        if output is None:
            continue
        
        transformation = engine.record_transformation(
            transformation_type=tx_type,
            input_surface=base_auth,
            output_surface=output,
            actor="admin",
            authority_basis="test",
            timestamp="2026-01-15T00:00:00Z",
        )
        
        exp = engine.run_experiment(
            experiment_name=f"transformation_{tx_type.value}",
            description=f"Authority transformation: {desc}",
            input_authority=base_auth,
            output_effect=output,
            transformation=transformation,
            notes=f"Tests whether {desc} preserves authority",
        )
        experiments.append(exp)
    
    return experiments


def run_scope_temporal_authority(engine: EffectBoundaryEngine) -> list[EffectBoundaryExperiment]:
    """Experiment 13: Scope and temporal authority dimensions."""
    experiments = []
    
    base_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        temporal_interval=("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"),
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    # Scope escalation tests
    scope_tests = [
        ("production", "staging", "PRODUCTION → STAGING"),
        ("staging", "production", "STAGING → PRODUCTION"),
        ("production", "production", "PRODUCTION → PRODUCTION"),
    ]
    
    for from_scope, to_scope, desc in scope_tests:
        input_surf = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope=from_scope,
            capability_class=CapabilityClass.MODIFY_POLICY,
        )
        output_surf = engine.create_authority_surface(
            principal="admin",
            operation="execute_payment",
            resource="payment_policy",
            scope=to_scope,
            capability_class=CapabilityClass.EXECUTE_PAYMENT,
        )
        
        transformation = engine.record_transformation(
            transformation_type=AuthorityTransformationType.SCOPE_CHANGE,
            input_surface=input_surf,
            output_surface=output_surf,
            actor="admin",
            authority_basis="test",
            timestamp="2026-01-15T00:00:00Z",
        )
        
        exp = engine.run_experiment(
            experiment_name=f"scope_{from_scope}_to_{to_scope}",
            description=f"Scope change: {desc}",
            input_authority=input_surf,
            output_effect=output_surf,
            transformation=transformation,
            notes=f"Tests scope authority: {desc}",
        )
        experiments.append(exp)
    
    return experiments


def run_capability_class_transitions(engine: EffectBoundaryEngine) -> list[EffectBoundaryExperiment]:
    """Experiment 14: Capability class transitions."""
    experiments = []
    
    base_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transitions = [
        (CapabilityClass.READ_ONLY, CapabilityClass.OBSERVE, "READ → OBSERVE"),
        (CapabilityClass.OBSERVE, CapabilityClass.ANALYZE, "OBSERVE → ANALYZE"),
        (CapabilityClass.ANALYZE, CapabilityClass.SIMULATE, "ANALYZE → SIMULATE"),
        (CapabilityClass.SIMULATE, CapabilityClass.EXECUTE_ACTION, "SIMULATE → EXECUTE"),
        (CapabilityClass.RECOMMEND, CapabilityClass.AUTHORIZE, "RECOMMEND → AUTHORIZE"),
        (CapabilityClass.AUTHORIZE, CapabilityClass.EXECUTE_ACTION, "AUTHORIZE → EXECUTE"),
        (CapabilityClass.MODIFY_POLICY, CapabilityClass.EXECUTE_PAYMENT, "MODIFY_POLICY → EXECUTE_PAYMENT"),
    ]
    
    for from_cap, to_cap, desc in transitions:
        input_surf = engine.create_authority_surface(
            principal="admin",
            operation="modify_policy",
            resource="payment_policy",
            scope="production",
            capability_class=from_cap,
        )
        output_surf = engine.create_authority_surface(
            principal="admin",
            operation="execute_payment",
            resource="payment_policy",
            scope="production",
            capability_class=to_cap,
        )
        
        transformation = engine.record_transformation(
            transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
            input_surface=input_surf,
            output_surface=output_surf,
            actor="admin",
            authority_basis="test",
            timestamp="2026-01-15T00:00:00Z",
        )
        
        exp = engine.run_experiment(
            experiment_name=f"capability_{from_cap.value}_to_{to_cap.value}",
            description=f"Capability transition: {desc}",
            input_authority=input_surf,
            output_effect=output_surf,
            transformation=transformation,
            notes=f"Tests capability class transition: {desc}",
        )
        experiments.append(exp)
    
    return experiments


def run_policy_effect_provenance(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 15: Policy effect provenance."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
        provenance=("admin_grant", "policy_created", "policy_activated"),
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
        provenance=("admin_grant", "policy_created", "policy_activated", "policy_modified", "governance_eval", "authority_materialized"),
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="policy_effect_provenance",
        description="Policy effect provenance chain reconstruction",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether provenance can reconstruct the full policy effect chain",
        normative_assumptions=[
            "Provenance must explain the effect without being mistaken for authority",
        ],
    )


def run_revocation_and_effect_authority(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 16: Revocation and effect authority."""
    input_auth = engine.create_authority_surface(
        principal="issuer",
        operation="create_policy",
        resource="payment_policy",
        scope="production",
        temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        capability_class=CapabilityClass.CREATE_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="issuer",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        temporal_interval=("2026-07-01T00:00:00Z", "2026-12-31T23:59:59Z"),  # After issuer authority expired
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="issuer",
        granted_authority=input_auth,
        max_scope="production",
        max_temporal_interval=("2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
        max_capability_class=CapabilityClass.CREATE_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.TEMPORAL_SHIFT,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="issuer",
        authority_basis="create_policy_authority",
        timestamp="2026-07-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="revocation_and_effect_authority",
        description="Policy effect after issuer authority revoked",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether revocation of issuer authority affects policy effect authority",
        underspecifications=[
            "Current implementation does not track revocation effects on policy authority",
        ],
    )


def run_authority_amplification_with_explicit_meta_authority(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 17: Authority amplification with explicit meta-authority.
    
    This is the central adversarial experiment.
    """
    # Actor has policy modify authority
    policy_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    # Actor is granted explicit policy effect authority
    effect_auth = engine.create_authority_surface(
        principal="governance_admin",
        operation="produce_authority",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.PRODUCE_AUTHORITY,
        conditions=frozenset({"explicit_effect_authority_granted"}),
    )
    
    # Actor modifies policy to enable payment execution
    output_effect = engine.create_authority_surface(
        principal="governance_admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    # Envelope covers the effect authority
    envelope = engine.create_envelope(
        principal="governance_admin",
        granted_authority=effect_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.PRODUCE_AUTHORITY,
        min_conditions=frozenset({"explicit_effect_authority_granted"}),
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=effect_auth,
        output_surface=output_effect,
        actor="governance_admin",
        authority_basis="explicit_effect_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="authority_amplification_with_explicit_meta_authority",
        description="Actor with explicit meta-authority modifies policy to enable downstream authority",
        input_authority=effect_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests whether explicit meta-authority distinguishes authorized effect from amplification",
        normative_assumptions=[
            "Explicit effect authority can legitimately create downstream authority",
        ],
    )


def run_authority_cut_sets(engine: EffectBoundaryEngine) -> EffectBoundaryExperiment:
    """Experiment 18: Authority cut sets."""
    input_auth = engine.create_authority_surface(
        principal="admin",
        operation="modify_policy",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    output_effect = engine.create_authority_surface(
        principal="admin",
        operation="execute_payment",
        resource="payment_policy",
        scope="production",
        capability_class=CapabilityClass.EXECUTE_PAYMENT,
    )
    
    envelope = engine.create_envelope(
        principal="admin",
        granted_authority=input_auth,
        max_scope="production",
        max_capability_class=CapabilityClass.MODIFY_POLICY,
    )
    
    transformation = engine.record_transformation(
        transformation_type=AuthorityTransformationType.CAPABILITY_TRANSITION,
        input_surface=input_auth,
        output_surface=output_effect,
        actor="admin",
        authority_basis="modify_policy_authority",
        timestamp="2026-01-15T00:00:00Z",
    )
    
    return engine.run_experiment(
        experiment_name="authority_cut_sets",
        description="Minimum cut set analysis for authority amplification",
        input_authority=input_auth,
        output_effect=output_effect,
        envelope=envelope,
        transformation=transformation,
        notes="Tests which nodes in the authority chain constitute amplification surfaces",
    )


# ---------------------------------------------------------------------------
# Run All Phase 15 Experiments
# ---------------------------------------------------------------------------


def run_all_phase15_experiments() -> dict[str, Any]:
    """Run all Phase 15 experiments."""
    engine = EffectBoundaryEngine()
    
    experiments = {}
    
    # Single experiments
    experiments["narrow_policy_change"] = run_narrow_policy_change(engine)
    experiments["broad_policy_change"] = run_broad_policy_change(engine)
    experiments["scope_expansion"] = run_scope_expansion(engine)
    experiments["temporal_expansion"] = run_temporal_expansion(engine)
    experiments["condition_removal"] = run_condition_removal(engine)
    experiments["new_authorization_path"] = run_new_authorization_path(engine)
    experiments["capability_class_expansion"] = run_capability_class_expansion(engine)
    experiments["policy_composition"] = run_policy_composition(engine)
    experiments["delegated_meta_authority"] = run_delegated_meta_authority(engine)
    experiments["explicit_effect_authority_boundary"] = run_explicit_effect_authority_boundary(engine)
    experiments["authority_creation_as_governed_operation"] = run_authority_creation_as_governed_operation(engine)
    experiments["policy_effect_provenance"] = run_policy_effect_provenance(engine)
    experiments["revocation_and_effect_authority"] = run_revocation_and_effect_authority(engine)
    experiments["authority_amplification_with_explicit_meta_authority"] = run_authority_amplification_with_explicit_meta_authority(engine)
    experiments["authority_cut_sets"] = run_authority_cut_sets(engine)
    
    # Multi-experiment runs
    transformation_experiments = run_authority_transformation_algebra(engine)
    for i, exp in enumerate(transformation_experiments):
        experiments[f"transformation_{i}"] = exp
    
    scope_temporal_experiments = run_scope_temporal_authority(engine)
    for i, exp in enumerate(scope_temporal_experiments):
        experiments[f"scope_temporal_{i}"] = exp
    
    capability_experiments = run_capability_class_transitions(engine)
    for i, exp in enumerate(capability_experiments):
        experiments[f"capability_{i}"] = exp
    
    return {
        "experiments": experiments,
        "total_experiments": len(experiments),
        "within_envelope_count": sum(1 for e in experiments.values() if e.result == EffectBoundaryResult.WITHIN_ENVELOPE),
        "exceeds_envelope_count": sum(1 for e in experiments.values() if e.result == EffectBoundaryResult.EXCEEDS_ENVELOPE),
        "amplification_count": sum(1 for e in experiments.values() if e.result == EffectBoundaryResult.AMPLIFICATION_DETECTED),
        "delegation_gap_count": sum(1 for e in experiments.values() if e.result == EffectBoundaryResult.DELEGATION_GAP),
    }


if __name__ == "__main__":
    results = run_all_phase15_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 15: EFFECT BOUNDARY")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Within envelope: {results['within_envelope_count']}")
    print(f"Exceeds envelope: {results['exceeds_envelope_count']}")
    print(f"Amplification detected: {results['amplification_count']}")
    print(f"Delegation gap: {results['delegation_gap_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Result: {exp.result.value}")
        print(f"  Authority amplified: {exp.authority_amplified}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
