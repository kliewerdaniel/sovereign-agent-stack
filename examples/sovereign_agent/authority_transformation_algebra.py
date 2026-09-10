"""Phase 22: Authority Transformation Algebra.

Generalizes the amplification phenomenon discovered in Phase 14, 15, and 21
into a unified theory of authority transformation.

Phase 14 discovered: policy modification can amplify downstream authority.
Phase 15 discovered: policy transformations have effect boundaries.
Phase 21 discovered: uncertainty policy can amplify authority through
                    the interpretation of epistemic states.

All three are instances of the same phenomenon:

    A PRINCIPAL MAY POSSESS LEGITIMATE AUTHORITY TO MODIFY A MECHANISM
    WITHOUT POSSESSING AUTHORITY OVER EVERY AUTHORITY EFFECT THAT THE
    MECHANISM CAN PRODUCE.

Phase 22 asks: CAN WE BUILD A GENERAL THEORY OF AUTHORITY TRANSFORMATION
THAT UNIFIES THESE CASES?

The central abstraction:

    INPUT AUTHORITY
          ↓
    TRANSFORMATION
          ↓
    EFFECT AUTHORITY

The key invariant:

    A LEGITIMATE AUTHORITY TO PERFORM A TRANSFORMATION DOES NOT IMPLY
    LEGITIMATE AUTHORITY OVER EVERY EFFECT PRODUCED BY THAT TRANSFORMATION.

Existing infrastructure reused:
- AuthoritySurface, AuthorityEnvelope, CapabilityClass (effect_boundary.py)
- AuthorityToken, TransitionStep (closed_authority_loop.py)
- UncertaintyPolicyWithAuthority, UncertaintyPolicyEffect (uncertainty_policy_authority.py)
- PolicyAuthorityRecord, PolicyLifecycleEvent (policy_governance.py)
- AuthorityClaimWithProvenance (authority_under_uncertainty.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Transformation Classification
# ---------------------------------------------------------------------------


class TransformationClass(str, Enum):
    """Classification of authority transformations.
    
    Do NOT force these into a scalar ordering. Authority surfaces can be
    incomparable (as established in Phase 15).
    """
    CONSERVATIVE = "conservative"      # Effect ⊆ Input (authority conserved)
    AMPLIFYING = "amplifying"          # Effect ⊃ Input (authority increased)
    INCOMPARABLE = "incomparable"      # Effect and Input incomparable
    UNCHANGED = "unchanged"            # Effect = Input (identity)
    UNKNOWN = "unknown"                # Cannot determine


# ---------------------------------------------------------------------------
# Authority Transformation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityTransformation:
    """A general authority transformation.
    
    Captures the relationship between input authority, the transformation
    applied, and the effect authority. This is the central abstraction
    that unifies policy modification, uncertainty policy, governance
    changes, delegation, emergency authority, recovery, and capability
    assignment.
    """
    transformation_id: str
    input_authority: dict[str, Any]  # Input authority surface
    effect_authority: dict[str, Any]  # Effect authority surface
    transformation_type: str  # What kind of transformation
    actor: str  # Who performed the transformation
    authority_basis: str  # What authority authorized this transformation
    scope: str = ""
    temporal_bounds: tuple[str, str] = ("unbounded", "unbounded")
    capability_bounds: str = ""
    provenance: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def classification(self) -> TransformationClass:
        """Classify this transformation."""
        return classify_transformation(self)
    
    @property
    def is_amplifying(self) -> bool:
        """Check if this transformation amplifies authority."""
        return self.classification == TransformationClass.AMPLIFYING
    
    @property
    def is_conservative(self) -> bool:
        """Check if this transformation is conservative."""
        return self.classification == TransformationClass.CONSERVATIVE
    
    @property
    def is_incomparable(self) -> bool:
        """Check if this transformation is incomparable."""
        return self.classification == TransformationClass.INCOMPARABLE


# ---------------------------------------------------------------------------
# Transformation Envelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformationEnvelope:
    """The permitted effect envelope for a transformation.
    
    A transformation is legitimate only if its effect falls within
    the envelope granted to its principal.
    """
    envelope_id: str
    principal: str
    granted_authority: dict[str, Any]
    permitted_effects: list[dict[str, Any]]
    max_scope: str
    max_temporal_bounds: tuple[str, str]
    max_capability_class: str
    provenance: tuple[str, ...] = ()
    
    def contains(self, effect: dict[str, Any]) -> bool:
        """Check if an effect is within this envelope."""
        # Check scope
        effect_scope = effect.get("scope", "")
        if effect_scope != self.max_scope and self.max_scope != "*":
            return False
        
        # Check temporal bounds
        effect_temporal = effect.get("temporal_bounds", ("unbounded", "unbounded"))
        if self.max_temporal_bounds[0] != "unbounded":
            if effect_temporal[0] == "unbounded":
                return False
            if effect_temporal[0] < self.max_temporal_bounds[0]:
                return False
        if self.max_temporal_bounds[1] != "unbounded":
            if effect_temporal[1] == "unbounded":
                return False
            if effect_temporal[1] > self.max_temporal_bounds[1]:
                return False
        
        # Check capability class
        effect_capability = effect.get("capability_class", "")
        if effect_capability and self.max_capability_class:
            # Amplifying if effect capability > max capability
            capability_order = [
                "read_only", "observe", "analyze", "simulate", "recommend",
                "governance_disposition", "authorize", "modify_policy",
                "create_policy", "activate_policy", "override_policy",
                "execute_action", "execute_payment", "execute_subprocess",
                "execute_network", "mutate_identity", "mutate_credential",
                "mutate_configuration", "produce_authority", "produce_execution"
            ]
            try:
                effect_idx = capability_order.index(effect_capability)
                max_idx = capability_order.index(self.max_capability_class)
                if effect_idx > max_idx:
                    return False
            except ValueError:
                pass
        
        return True


# ---------------------------------------------------------------------------
# Transformation Classifier
# ---------------------------------------------------------------------------


def classify_transformation(transformation: AuthorityTransformation) -> TransformationClass:
    """Classify an authority transformation.
    
    Compares input authority to effect authority to determine if the
    transformation is conservative, amplifying, incomparable, or unchanged.
    """
    input_auth = transformation.input_authority
    effect_auth = transformation.effect_authority
    
    # Check for identity
    if input_auth == effect_auth:
        return TransformationClass.UNCHANGED
    
    # Compare scope
    input_scope = input_auth.get("scope", "")
    effect_scope = effect_auth.get("scope", "")
    
    # Compare capability class
    input_capability = input_auth.get("capability_class", "")
    effect_capability = effect_auth.get("capability_class", "")
    
    # Compare temporal bounds
    input_temporal = input_auth.get("temporal_bounds", ("unbounded", "unbounded"))
    effect_temporal = effect_auth.get("temporal_bounds", ("unbounded", "unbounded"))
    
    # Check for amplification
    is_amplifying = False
    is_conservative = True
    
    # Scope amplification
    if input_scope != effect_scope:
        if input_scope == "*" and effect_scope != "*":
            pass  # Narrowing scope is conservative
        elif input_scope != "*" and effect_scope == "*":
            is_amplifying = True
            is_conservative = False
        else:
            # Different scopes - incomparable
            return TransformationClass.INCOMPARABLE
    
    # Capability amplification
    capability_order = [
        "hold", "review", "escalate", "deny",
        "read_only", "observe", "analyze", "simulate", "recommend",
        "governance_disposition", "authorize", "modify_policy",
        "create_policy", "activate_policy", "override_policy",
        "execute_action", "execute_payment", "execute_subprocess",
        "execute_network", "execute", "mutate_identity", "mutate_credential",
        "mutate_configuration", "produce_authority", "produce_execution"
    ]
    
    try:
        input_idx = capability_order.index(input_capability) if input_capability else 0
        effect_idx = capability_order.index(effect_capability) if effect_capability else 0
        if effect_idx > input_idx:
            is_amplifying = True
            is_conservative = False
        elif effect_idx < input_idx:
            pass  # Narrowing capability is conservative
    except ValueError:
        pass
    
    # Condition amplification (removing conditions = fewer constraints = amplifying)
    input_conditions = input_auth.get("conditions", frozenset())
    effect_conditions = effect_auth.get("conditions", frozenset())
    if input_conditions != effect_conditions:
        if len(effect_conditions) < len(input_conditions):
            is_amplifying = True
            is_conservative = False
        elif len(effect_conditions) > len(input_conditions):
            pass  # Adding conditions is conservative
    
    # Temporal amplification
    if input_temporal[0] != "unbounded":
        if effect_temporal[0] == "unbounded" or effect_temporal[0] < input_temporal[0]:
            is_amplifying = True
            is_conservative = False
    if input_temporal[1] != "unbounded":
        if effect_temporal[1] == "unbounded" or effect_temporal[1] > input_temporal[1]:
            is_amplifying = True
            is_conservative = False
    
    if is_amplifying:
        return TransformationClass.AMPLIFYING
    if is_conservative:
        return TransformationClass.CONSERVATIVE
    return TransformationClass.UNKNOWN


# ---------------------------------------------------------------------------
# Transformation Algebra Engine
# ---------------------------------------------------------------------------


@dataclass
class TransformationAlgebraEngine:
    """Engine for testing authority transformation algebra.
    
    Creates transformations, classifies them, checks envelopes,
    and detects amplification.
    """
    
    transformations: list[AuthorityTransformation] = field(default_factory=list)
    envelopes: dict[str, TransformationEnvelope] = field(default_factory=dict)
    experiments: list["TransformationExperiment"] = field(default_factory=list)
    
    def create_transformation(
        self,
        input_authority: dict[str, Any],
        effect_authority: dict[str, Any],
        transformation_type: str,
        actor: str,
        authority_basis: str,
        scope: str = "",
        capability_bounds: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuthorityTransformation:
        """Create and classify an authority transformation."""
        transformation = AuthorityTransformation(
            transformation_id=f"transform_{uuid.uuid4().hex[:12]}",
            input_authority=input_authority,
            effect_authority=effect_authority,
            transformation_type=transformation_type,
            actor=actor,
            authority_basis=authority_basis,
            scope=scope,
            capability_bounds=capability_bounds,
            metadata=metadata or {},
        )
        self.transformations.append(transformation)
        return transformation
    
    def create_envelope(
        self,
        principal: str,
        granted_authority: dict[str, Any],
        max_scope: str,
        max_temporal_bounds: tuple[str, str],
        max_capability_class: str,
    ) -> TransformationEnvelope:
        """Create a transformation envelope."""
        envelope = TransformationEnvelope(
            envelope_id=f"envelope_{uuid.uuid4().hex[:12]}",
            principal=principal,
            granted_authority=granted_authority,
            permitted_effects=[],
            max_scope=max_scope,
            max_temporal_bounds=max_temporal_bounds,
            max_capability_class=max_capability_class,
        )
        self.envelopes[principal] = envelope
        return envelope
    
    def check_transformation(
        self,
        transformation: AuthorityTransformation,
    ) -> tuple[TransformationClass, bool, list[str]]:
        """Check a transformation against its envelope.
        
        Returns: (classification, within_envelope, violations)
        """
        classification = transformation.classification
        
        # Check envelope
        envelope = self.envelopes.get(transformation.actor)
        if not envelope:
            return classification, True, []
        
        within = envelope.contains(transformation.effect_authority)
        violations = []
        
        if not within:
            violations.append(
                f"Effect exceeds envelope for {transformation.actor}: "
                f"scope={transformation.effect_authority.get('scope')}, "
                f"max_scope={envelope.max_scope}"
            )
        
        return classification, within, violations
    
    def compose_transformations(
        self,
        t1: AuthorityTransformation,
        t2: AuthorityTransformation,
    ) -> AuthorityTransformation:
        """Compose two transformations: t1 followed by t2."""
        return AuthorityTransformation(
            transformation_id=f"composed_{uuid.uuid4().hex[:12]}",
            input_authority=t1.input_authority,
            effect_authority=t2.effect_authority,
            transformation_type=f"composed({t1.transformation_type}, {t2.transformation_type})",
            actor=t1.actor,
            authority_basis=t1.authority_basis,
            metadata={"composed_from": [t1.transformation_id, t2.transformation_id]},
        )
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        transformation: AuthorityTransformation,
        classification: TransformationClass,
        within_envelope: bool,
        violations: list[str],
        notes: str = "",
        normative_assumptions: list[str] | None = None,
        underspecifications: list[str] | None = None,
    ) -> "TransformationExperiment":
        """Run a transformation algebra experiment."""
        experiment = TransformationExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            transformation=transformation,
            classification=classification,
            within_envelope=within_envelope,
            violations=violations,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Transformation Experiment
# ---------------------------------------------------------------------------


@dataclass
class TransformationExperiment:
    """Result of a transformation algebra experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    transformation: AuthorityTransformation
    classification: TransformationClass
    within_envelope: bool
    violations: list[str]
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Experiment 1: Identity Transformation (A → A)
# ---------------------------------------------------------------------------


def run_identity_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → A: Identity transformation is conservative."""
    input_auth = {"scope": "production", "capability_class": "execute_action"}
    effect_auth = {"scope": "production", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="identity",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="identity",
        description="A → A: Identity transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Identity transformation is conservative",
    )


# ---------------------------------------------------------------------------
# Experiment 2: Narrowing Transformation (A → narrower(A))
# ---------------------------------------------------------------------------


def run_narrowing_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → narrower(A): Narrowing is conservative."""
    input_auth = {"scope": "*", "capability_class": "execute_action"}
    effect_auth = {"scope": "production", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="narrowing",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="narrowing",
        description="A → narrower(A): Narrowing transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Narrowing scope is conservative",
    )


# ---------------------------------------------------------------------------
# Experiment 3: Broadening Transformation (A → broader(A)) — AMPLIFYING
# ---------------------------------------------------------------------------


def run_broadening_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → broader(A): Broadening is AMPLIFYING."""
    input_auth = {"scope": "production", "capability_class": "execute_action"}
    effect_auth = {"scope": "*", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="broadening",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="broadening",
        description="A → broader(A): AMPLIFYING transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Broadening scope is AMPLIFYING",
    )


# ---------------------------------------------------------------------------
# Experiment 4: Scope Change (A → different_scope(A)) — INCOMPARABLE
# ---------------------------------------------------------------------------


def run_scope_change_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → different_scope(A): Scope change is INCOMPARABLE."""
    input_auth = {"scope": "production", "capability_class": "execute_action"}
    effect_auth = {"scope": "staging", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="scope_change",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="scope_change",
        description="A → different_scope(A): INCOMPARABLE transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Different scopes are incomparable",
    )


# ---------------------------------------------------------------------------
# Experiment 5: Temporal Shift (A → different_time(A)) — AMPLIFYING
# ---------------------------------------------------------------------------


def run_temporal_shift_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → different_time(A): Temporal shift is AMPLIFYING."""
    input_auth = {
        "scope": "production",
        "capability_class": "execute_action",
        "temporal_bounds": ("2026-01-01", "2026-01-31"),
    }
    effect_auth = {
        "scope": "production",
        "capability_class": "execute_action",
        "temporal_bounds": ("2026-01-01", "2026-12-31"),
    }
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="temporal_shift",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="temporal_shift",
        description="A → different_time(A): AMPLIFYING transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Extending temporal bounds is AMPLIFYING",
    )


# ---------------------------------------------------------------------------
# Experiment 6: Capability Change (A → different_capability(A)) — AMPLIFYING
# ---------------------------------------------------------------------------


def run_capability_change_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → different_capability(A): Capability escalation is AMPLIFYING."""
    input_auth = {"scope": "production", "capability_class": "analyze"}
    effect_auth = {"scope": "production", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="capability_escalation",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="capability_change",
        description="A → different_capability(A): AMPLIFYING transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Capability escalation is AMPLIFYING",
    )


# ---------------------------------------------------------------------------
# Experiment 7: Condition Change (A → different_conditions(A))
# ---------------------------------------------------------------------------


def run_condition_change_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → different_conditions(A): Condition change."""
    input_auth = {
        "scope": "production",
        "capability_class": "execute_action",
        "conditions": frozenset(["business_hours"]),
    }
    effect_auth = {
        "scope": "production",
        "capability_class": "execute_action",
        "conditions": frozenset(),
    }
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="condition_removal",
        actor="admin",
        authority_basis="trust_anchor",
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="condition_change",
        description="A → different_conditions(A): Condition removal",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Removing conditions is AMPLIFYING (fewer constraints)",
    )


# ---------------------------------------------------------------------------
# Experiment 8: Delegation (A → delegated(A))
# ---------------------------------------------------------------------------


def run_delegation_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → delegated(A): Delegation should be conservative."""
    input_auth = {"scope": "production", "capability_class": "execute_action"}
    effect_auth = {"scope": "production", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="delegation",
        actor="admin",
        authority_basis="trust_anchor",
        metadata={"delegatee": "subordinate"},
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="delegation",
        description="A → delegated(A): Delegation transformation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Delegation should be conservative (no amplification)",
    )


# ---------------------------------------------------------------------------
# Experiment 9: Composition (A → composed(A+B)) — AMPLIFYING
# ---------------------------------------------------------------------------


def run_composition_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → composed(A+B): Composition can be AMPLIFYING."""
    input_auth = {"scope": "production", "capability_class": "analyze"}
    effect_auth = {"scope": "production", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="composition",
        actor="admin",
        authority_basis="trust_anchor",
        metadata={"composed_capabilities": ["analyze", "execute"]},
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="composition",
        description="A → composed(A+B): AMPLIFYING composition",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Composition can amplify authority",
    )


# ---------------------------------------------------------------------------
# Experiment 10: Interpretation (A → interpreted(A)) — AMPLIFYING
# ---------------------------------------------------------------------------


def run_interpretation_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → interpreted(A): Interpretation can be AMPLIFYING.
    
    This is the Phase 21 case: uncertainty policy interprets UNKNOWN
    as AUTHORIZE, effectively amplifying authority.
    """
    input_auth = {"scope": "production", "capability_class": "hold"}
    effect_auth = {"scope": "production", "capability_class": "authorize"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="interpretation",
        actor="admin",
        authority_basis="trust_anchor",
        metadata={"interpretation": "UNKNOWN → AUTHORIZE"},
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="interpretation",
        description="A → interpreted(A): AMPLIFYING interpretation",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Interpretation can amplify authority (Phase 21 case)",
    )


# ---------------------------------------------------------------------------
# Experiment 11: Uncertainty Policy (A → uncertainty_policy(A)) — AMPLIFYING
# ---------------------------------------------------------------------------


def run_uncertainty_policy_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → uncertainty_policy(A): Uncertainty policy can be AMPLIFYING."""
    input_auth = {"scope": "production", "capability_class": "review"}
    effect_auth = {"scope": "production", "capability_class": "authorize"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="uncertainty_policy",
        actor="admin",
        authority_basis="trust_anchor",
        metadata={"policy": "UNKNOWN → AUTHORIZE"},
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="uncertainty_policy",
        description="A → uncertainty_policy(A): AMPLIFYING uncertainty policy",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Uncertainty policy can amplify authority (Phase 21)",
    )


# ---------------------------------------------------------------------------
# Experiment 12: Emergency (A → emergency(A))
# ---------------------------------------------------------------------------


def run_emergency_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → emergency(A): Emergency authority may be AMPLIFYING."""
    input_auth = {"scope": "production", "capability_class": "execute_action"}
    effect_auth = {"scope": "*", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="emergency",
        actor="emergency_admin",
        authority_basis="emergency_anchor",
        metadata={"emergency": True},
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="emergency",
        description="A → emergency(A): Emergency authority",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Emergency authority may legitimately amplify",
        underspecifications=["Emergency authority is a separate trust domain"],
    )


# ---------------------------------------------------------------------------
# Experiment 13: Recovery (A → recovery(A))
# ---------------------------------------------------------------------------


def run_recovery_transformation(engine: TransformationAlgebraEngine) -> TransformationExperiment:
    """A → recovery(A): Recovery authority may be AMPLIFYING."""
    input_auth = {"scope": "production", "capability_class": "execute_action"}
    effect_auth = {"scope": "*", "capability_class": "execute_action"}
    
    transformation = engine.create_transformation(
        input_authority=input_auth,
        effect_authority=effect_auth,
        transformation_type="recovery",
        actor="recovery_admin",
        authority_basis="recovery_anchor",
        metadata={"recovery": True},
    )
    
    classification, within, violations = engine.check_transformation(transformation)
    
    return engine.run_experiment(
        experiment_name="recovery",
        description="A → recovery(A): Recovery authority",
        transformation=transformation,
        classification=classification,
        within_envelope=within,
        violations=violations,
        notes="Recovery authority may legitimately amplify",
        underspecifications=["Recovery authority is a separate trust domain"],
    )


# ---------------------------------------------------------------------------
# Run All Phase 22 Experiments
# ---------------------------------------------------------------------------


def run_all_phase22_experiments() -> dict[str, Any]:
    """Run all Phase 22 experiments."""
    engine = TransformationAlgebraEngine()
    
    # Create envelope for admin
    engine.create_envelope(
        principal="admin",
        granted_authority={"scope": "production", "capability_class": "execute_action"},
        max_scope="production",
        max_temporal_bounds=("2026-01-01", "2026-12-31"),
        max_capability_class="execute_action",
    )
    
    experiments = [
        run_identity_transformation(engine),
        run_narrowing_transformation(engine),
        run_broadening_transformation(engine),
        run_scope_change_transformation(engine),
        run_temporal_shift_transformation(engine),
        run_capability_change_transformation(engine),
        run_condition_change_transformation(engine),
        run_delegation_transformation(engine),
        run_composition_transformation(engine),
        run_interpretation_transformation(engine),
        run_uncertainty_policy_transformation(engine),
        run_emergency_transformation(engine),
        run_recovery_transformation(engine),
    ]
    
    return {
        "experiments": {e.experiment_name: e for e in experiments},
        "total_experiments": len(experiments),
        "conservative_count": sum(
            1 for e in experiments if e.classification == TransformationClass.CONSERVATIVE
        ),
        "amplifying_count": sum(
            1 for e in experiments if e.classification == TransformationClass.AMPLIFYING
        ),
        "incomparable_count": sum(
            1 for e in experiments if e.classification == TransformationClass.INCOMPARABLE
        ),
        "unchanged_count": sum(
            1 for e in experiments if e.classification == TransformationClass.UNCHANGED
        ),
        "within_envelope_count": sum(
            1 for e in experiments if e.within_envelope
        ),
        "violation_count": sum(
            1 for e in experiments if e.violations
        ),
    }


if __name__ == "__main__":
    results = run_all_phase22_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 22: AUTHORITY TRANSFORMATION ALGEBRA")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Conservative: {results['conservative_count']}")
    print(f"Amplifying: {results['amplifying_count']}")
    print(f"Incomparable: {results['incomparable_count']}")
    print(f"Unchanged: {results['unchanged_count']}")
    print(f"Within envelope: {results['within_envelope_count']}")
    print(f"Violations: {results['violation_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Description: {exp.description}")
        print(f"  Classification: {exp.classification.value}")
        print(f"  Within envelope: {exp.within_envelope}")
        if exp.violations:
            print(f"  Violations: {exp.violations}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
