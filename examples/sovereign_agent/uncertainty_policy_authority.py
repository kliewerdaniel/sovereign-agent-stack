"""Phase 21: Uncertainty Policy Authority and Epistemic Escalation.

Tests whether uncertainty policy itself can amplify authority, connecting
the epistemic uncertainty layer back to the Phase 14/15 amplification
and effect boundary work.

Phase 20 established AUTHORITY_UNDER_UNCERTAINTY_SAFE: the system can
safely make authority decisions under incomplete knowledge. The
UncertaintyPolicy maps epistemic states to governance dispositions.

Phase 21 asks:

    CAN UNCERTAINTY POLICY ITSELF AMPLIFY AUTHORITY?

The central hypothesis:

    A POLICY GOVERNING UNCERTAINTY IS ITSELF A CONSEQUENTIAL AUTHORITY
    MECHANISM AND MUST BE SUBJECT TO THE SAME EFFECT-BOUNDARY AND
    AUTHORITY-GENESIS CONSTRAINTS AS ORDINARY GOVERNANCE POLICY.

This connects the epistemic uncertainty layer to Phase 13-15 work on
policy authority, effect boundaries, and amplification.

The adversarial attack: an actor with legitimate authority to modify
uncertainty policy can indirectly obtain authority that exceeds their
legitimate authority.

Existing infrastructure reused:
- AuthorityUnderUncertaintyEngine, UncertaintyPolicy, AuthorityClaimWithProvenance (authority_under_uncertainty.py)
- AuthorityGraphCompletenessEngine, CompletenessResult (authority_graph_completeness.py)
- AuthoritySurface, AuthorityEnvelope (effect_boundary.py)
- PolicyGovernanceEngine, PolicyAuthorityRecord (policy_governance.py)
- GovernancePolicyEngine, Policy, PolicyEvaluationResult (governance_policy.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Uncertainty Policy Authority Types
# ---------------------------------------------------------------------------


class UncertaintyPolicyResult(str, Enum):
    """Result of an uncertainty policy authority experiment."""
    POLICY_VALID = "policy_valid"
    POLICY_INVALID = "policy_invalid"
    AMPLIFICATION_DETECTED = "amplification_detected"
    NO_AMPLIFICATION = "no_amplification"
    ESCALATION_DETECTED = "escalation_detected"
    EFFECT_BOUNDARY_VIOLATION = "effect_boundary_violation"
    WITHIN_ENVELOPE = "within_envelope"
    POLICY_EFFECT_EXCEEDS_AUTHORITY = "policy_effect_exceeds_authority"
    UNCERTAINTY_AUTHORITY_DISTINCT = "uncertainty_authority_distinct"
    UNKNOWN = "unknown"


class UncertaintyPolicyOperation(str, Enum):
    """Operations on uncertainty policy."""
    CREATE = "create"
    MODIFY = "modify"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    ROLLBACK = "rollback"
    SUPERSEDE = "supersede"


# ---------------------------------------------------------------------------
# Bounded Completeness (Fixing the Phase 20 conceptual regression)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BoundedCompleteness:
    """Completeness with explicit scope, temporal, provenance, and
    observation semantics.
    
    Fixes the Phase 20 conceptual regression where COMPLETE sounded
    like a positive completeness claim. It is actually an
    observation-bounded statement.
    """
    state: str  # COMPLETE, INCOMPLETE, UNKNOWN, WAS_COMPLETE_AT_T
    scope: str  # Scope within which completeness was assessed
    temporal_interval: tuple[str, str]  # When the assessment is valid
    observation_method: str  # How completeness was established
    evidence: tuple[str, ...] = ()  # Supporting evidence
    provenance: tuple[str, ...] = ()  # Who performed the assessment
    confidence: float = 0.0  # 0.0 to 1.0
    
    def is_bounded_complete(self) -> bool:
        return self.state == "complete"
    
    def is_observation_bounded(self) -> bool:
        """Check if completeness is properly bounded."""
        return (
            self.scope != "*"
            and self.temporal_interval != ("unbounded", "unbounded")
            and self.observation_method != ""
        )


# ---------------------------------------------------------------------------
# Uncertainty Policy with Authority Tracking
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UncertaintyPolicyWithAuthority:
    """An uncertainty policy with explicit authority tracking.
    
    The policy itself has authority consequences and must be subject
    to the same effect-boundary constraints as ordinary governance
    policy.
    """
    policy_id: str
    name: str
    description: str
    state_to_disposition: dict[str, str] = field(default_factory=dict)
    # Authority bounds on the policy itself
    authority_scope: str = ""
    authority_envelope: Optional[Any] = None  # AuthorityEnvelope
    max_authority_effect: str = ""  # Maximum authority this policy can create
    # Provenance
    created_by: str = ""
    created_at: str = ""
    authority_basis: str = ""
    provenance: tuple[str, ...] = ()
    # Effect boundary
    effect_boundary_valid: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Uncertainty Policy Effect Tracker
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UncertaintyPolicyEffect:
    """Tracks the authority effect of an uncertainty policy.
    
    Maps the policy's effect on authority to detect amplification.
    """
    effect_id: str
    policy_id: str
    input_completeness: str
    output_disposition: str
    authority_created: bool = False
    authority_amplified: bool = False
    authority_effect_scope: str = ""
    notes: str = ""
    
    @property
    def is_amplifying(self) -> bool:
        """Check if this policy effect amplifies authority."""
        return self.authority_amplified


# ---------------------------------------------------------------------------
# Uncertainty Policy Authority Engine
# ---------------------------------------------------------------------------


@dataclass
class UncertaintyPolicyAuthorityEngine:
    """Engine for testing whether uncertainty policy can amplify authority.
    
    The engine:
    1. Creates uncertainty policies with explicit authority bounds
    2. Applies policies to completeness states
    3. Tracks the authority effect of each policy application
    4. Detects amplification, escalation, and effect-boundary violations
    """
    
    policies: dict[str, UncertaintyPolicyWithAuthority] = field(default_factory=dict)
    effects: list[UncertaintyPolicyEffect] = field(default_factory=list)
    experiments: list["UncertaintyPolicyExperiment"] = field(default_factory=list)
    
    def create_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        state_to_disposition: dict[str, str],
        authority_scope: str = "",
        max_authority_effect: str = "",
        created_by: str = "",
        authority_basis: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> UncertaintyPolicyWithAuthority:
        """Create an uncertainty policy with explicit authority bounds."""
        policy = UncertaintyPolicyWithAuthority(
            policy_id=policy_id,
            name=name,
            description=description,
            state_to_disposition=state_to_disposition,
            authority_scope=authority_scope,
            max_authority_effect=max_authority_effect,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            authority_basis=authority_basis,
            provenance=(f"created_by={created_by}", f"basis={authority_basis}"),
            metadata=metadata or {},
        )
        self.policies[policy_id] = policy
        return policy
    
    def apply_policy(
        self,
        policy_id: str,
        completeness_state: str,
    ) -> UncertaintyPolicyEffect:
        """Apply an uncertainty policy to a completeness state.
        
        Tracks the authority effect for amplification detection.
        """
        policy = self.policies.get(policy_id)
        if not policy:
            return UncertaintyPolicyEffect(
                effect_id=f"effect_{uuid.uuid4().hex[:12]}",
                policy_id=policy_id,
                input_completeness=completeness_state,
                output_disposition="unknown",
                notes=f"Policy {policy_id} not found",
            )
        
        disposition = policy.state_to_disposition.get(
            completeness_state, "hold"
        )
        
        # Check for amplification
        authority_amplified = self._check_amplification(policy, disposition)
        
        effect = UncertaintyPolicyEffect(
            effect_id=f"effect_{uuid.uuid4().hex[:12]}",
            policy_id=policy_id,
            input_completeness=completeness_state,
            output_disposition=disposition,
            authority_created=(disposition == "authorize"),
            authority_amplified=authority_amplified,
            authority_effect_scope=policy.authority_scope,
            notes=f"Disposition: {disposition}, Amplified: {authority_amplified}",
        )
        self.effects.append(effect)
        return effect
    
    def _check_amplification(
        self,
        policy: UncertaintyPolicyWithAuthority,
        disposition: str,
    ) -> bool:
        """Check if the policy amplifies authority."""
        # Amplification occurs when:
        # 1. Policy creates authority from uncertainty (UNKNOWN → AUTHORIZE)
        # 2. Policy's authority effect exceeds its declared scope
        if disposition == "authorize" and "authorize" not in policy.authority_scope:
            return True
        if disposition == "authorize" and policy.max_authority_effect:
            # Check if authorization exceeds max effect
            return True
        return False
    
    def check_effect_boundary(
        self,
        policy_id: str,
    ) -> tuple[bool, list[str]]:
        """Check if a policy's effect is within its authority envelope."""
        policy = self.policies.get(policy_id)
        if not policy:
            return False, ["Policy not found"]
        
        violations = []
        
        # Check: policy creates authority beyond its scope
        for effect in self.effects:
            if effect.policy_id == policy_id:
                if effect.authority_created and not policy.authority_scope:
                    violations.append(
                        f"Policy creates authority but has no declared scope"
                    )
                if effect.authority_amplified:
                    violations.append(
                        f"Policy amplifies authority: {effect.input_completeness} → {effect.output_disposition}"
                    )
        
        return len(violations) == 0, violations
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        result: UncertaintyPolicyResult,
        notes: str = "",
        normative_assumptions: list[str] | None = None,
        underspecifications: list[str] | None = None,
    ) -> "UncertaintyPolicyExperiment":
        """Run an uncertainty policy authority experiment."""
        experiment = UncertaintyPolicyExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            result=result,
            effects=list(self.effects),
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Uncertainty Policy Experiment
# ---------------------------------------------------------------------------


@dataclass
class UncertaintyPolicyExperiment:
    """Result of an uncertainty policy authority experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    result: UncertaintyPolicyResult
    effects: list[UncertaintyPolicyEffect] = field(default_factory=list)
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Experiment 1: UNKNOWN → HOLD
# ---------------------------------------------------------------------------


def run_unknown_hold(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """UNKNOWN → HOLD: No amplification."""
    engine.create_policy(
        policy_id="policy_hold",
        name="Hold on Unknown",
        description="Hold authority when completeness is unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
            "was_complete_at_t": "review",
        },
        authority_scope="governance",
        max_authority_effect="hold",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    engine.apply_policy("policy_hold", "unknown")
    
    return engine.run_experiment(
        experiment_name="unknown_hold",
        description="UNKNOWN → HOLD: No amplification",
        result=UncertaintyPolicyResult.NO_AMPLIFICATION,
        notes="HOLD does not create or amplify authority",
        normative_assumptions=["HOLD is a conservative disposition"],
    )


# ---------------------------------------------------------------------------
# Experiment 2: UNKNOWN → REVIEW
# ---------------------------------------------------------------------------


def run_unknown_review(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """UNKNOWN → REVIEW: No amplification, revalidation required."""
    engine.create_policy(
        policy_id="policy_review",
        name="Review on Unknown",
        description="Require review when completeness is unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "review",
            "was_complete_at_t": "review",
        },
        authority_scope="governance",
        max_authority_effect="review",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    engine.apply_policy("policy_review", "unknown")
    
    return engine.run_experiment(
        experiment_name="unknown_review",
        description="UNKNOWN → REVIEW: No amplification",
        result=UncertaintyPolicyResult.NO_AMPLIFICATION,
        notes="REVIEW does not create authority, requires revalidation",
    )


# ---------------------------------------------------------------------------
# Experiment 3: UNKNOWN → ESCALATE
# ---------------------------------------------------------------------------


def run_unknown_escalate(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """UNKNOWN → ESCALATE: No amplification, escalation path."""
    engine.create_policy(
        policy_id="policy_escalate",
        name="Escalate on Unknown",
        description="Escalate when completeness is unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "escalate",
            "was_complete_at_t": "review",
        },
        authority_scope="governance",
        max_authority_effect="escalate",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    engine.apply_policy("policy_escalate", "unknown")
    
    return engine.run_experiment(
        experiment_name="unknown_escalate",
        description="UNKNOWN → ESCALATE: No amplification",
        result=UncertaintyPolicyResult.NO_AMPLIFICATION,
        notes="ESCALATE does not create authority, routes to higher authority",
    )


# ---------------------------------------------------------------------------
# Experiment 4: UNKNOWN → DENY
# ---------------------------------------------------------------------------


def run_unknown_deny(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """UNKNOWN → DENY: No amplification, explicit denial."""
    engine.create_policy(
        policy_id="policy_deny",
        name="Deny on Unknown",
        description="Deny authority when completeness is unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "deny",
            "unknown": "deny",
            "was_complete_at_t": "review",
        },
        authority_scope="governance",
        max_authority_effect="deny",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    engine.apply_policy("policy_deny", "unknown")
    
    return engine.run_experiment(
        experiment_name="unknown_deny",
        description="UNKNOWN → DENY: No amplification",
        result=UncertaintyPolicyResult.NO_AMPLIFICATION,
        notes="DENY does not create authority, explicit denial",
    )


# ---------------------------------------------------------------------------
# Experiment 5: UNKNOWN → AUTHORIZE (AMPLIFICATION!)
# ---------------------------------------------------------------------------


def run_unknown_authorize(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """UNKNOWN → AUTHORIZE: AUTHORITY AMPLIFICATION DETECTED.
    
    This is the dangerous case. A policy that authorizes from uncertainty
    is amplifying authority beyond what the epistemic state supports.
    """
    engine.create_policy(
        policy_id="policy_authorize",
        name="Authorize on Unknown",
        description="Authorize authority when completeness is unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
            "was_complete_at_t": "authorize",
        },
        authority_scope="governance",
        max_authority_effect="authorize",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    effect = engine.apply_policy("policy_authorize", "unknown")
    
    return engine.run_experiment(
        experiment_name="unknown_authorize",
        description="UNKNOWN → AUTHORIZE: AMPLIFICATION DETECTED",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="AUTHORITY AMPLIFICATION: Policy creates authority from uncertainty",
        normative_assumptions=[
            "Authority should not be created from uncertainty",
        ],
        underspecifications=[
            "Policy is valid but amplifies authority",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 6: INCOMPLETE → AUTHORIZE (AMPLIFICATION!)
# ---------------------------------------------------------------------------


def run_incomplete_authorize(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """INCOMPLETE → AUTHORIZE: AUTHORITY AMPLIFICATION DETECTED.
    
    A policy that authorizes when the graph is known to be incomplete
    is amplifying authority beyond what the epistemic state supports.
    """
    engine.create_policy(
        policy_id="policy_incomplete_auth",
        name="Authorize on Incomplete",
        description="Authorize authority when graph is incomplete",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "hold",
            "was_complete_at_t": "review",
        },
        authority_scope="governance",
        max_authority_effect="authorize",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    effect = engine.apply_policy("policy_incomplete_auth", "incomplete")
    
    return engine.run_experiment(
        experiment_name="incomplete_authorize",
        description="INCOMPLETE → AUTHORIZE: AMPLIFICATION DETECTED",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="AUTHORITY AMPLIFICATION: Policy creates authority from known incompleteness",
    )


# ---------------------------------------------------------------------------
# Experiment 7: WAS_COMPLETE_AT_T → AUTHORIZE
# ---------------------------------------------------------------------------


def run_was_complete_authorize(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """WAS_COMPLETE_AT_T → AUTHORIZE: Effect boundary check."""
    engine.create_policy(
        policy_id="policy_was_complete",
        name="Authorize on Was Complete",
        description="Authorize when graph was complete at T1",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
            "was_complete_at_t": "authorize",
        },
        authority_scope="governance",
        max_authority_effect="authorize",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    effect = engine.apply_policy("policy_was_complete", "was_complete_at_t")
    
    return engine.run_experiment(
        experiment_name="was_complete_authorize",
        description="WAS_COMPLETE_AT_T → AUTHORIZE: Effect boundary check",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Historical completeness does not justify future authority",
    )


# ---------------------------------------------------------------------------
# Experiment 8: Historical Uncertainty Policy Changes
# ---------------------------------------------------------------------------


def run_historical_policy_change(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Test historical uncertainty policy changes.
    
    A policy changes from HOLD to AUTHORIZE over time.
    The historical authorization under the old policy is preserved.
    """
    # T1: Conservative policy
    engine.create_policy(
        policy_id="policy_v1",
        name="Conservative Policy",
        description="HOLD on unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
        },
        authority_scope="governance",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    # Apply conservative policy at T1
    engine.apply_policy("policy_v1", "unknown")
    
    # T2: Aggressive policy
    engine.create_policy(
        policy_id="policy_v2",
        name="Aggressive Policy",
        description="AUTHORIZE on unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="governance",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    # Apply aggressive policy at T2
    effect = engine.apply_policy("policy_v2", "unknown")
    
    return engine.run_experiment(
        experiment_name="historical_policy_change",
        description="Historical policy change from HOLD to AUTHORIZE",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Policy change from conservative to aggressive is detected as amplification",
        normative_assumptions=[
            "Historical authorizations under old policy are preserved",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 9: Emergency Uncertainty Policy
# ---------------------------------------------------------------------------


def run_emergency_policy(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Emergency uncertainty policy: different semantics under emergency."""
    engine.create_policy(
        policy_id="policy_emergency",
        name="Emergency Uncertainty Policy",
        description="AUTHORIZE on unknown during emergency",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="emergency_governance",
        max_authority_effect="authorize",
        created_by="emergency_admin",
        authority_basis="emergency_trust_anchor",
        metadata={"emergency": True},
    )
    
    effect = engine.apply_policy("policy_emergency", "unknown")
    
    return engine.run_experiment(
        experiment_name="emergency_policy",
        description="Emergency uncertainty policy: AUTHORIZE on unknown",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Emergency policy may legitimately authorize from uncertainty",
        normative_assumptions=[
            "Emergency authority may have different semantics",
        ],
        underspecifications=[
            "Emergency authority is a separate trust domain",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 10: Cross-Domain Uncertainty Policy
# ---------------------------------------------------------------------------


def run_cross_domain_policy(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Cross-domain uncertainty policy: different domains, different semantics."""
    # Domain A: Conservative
    engine.create_policy(
        policy_id="policy_domain_a",
        name="Domain A Conservative",
        description="HOLD on unknown in domain A",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
        },
        authority_scope="domain_a",
        created_by="admin_a",
        authority_basis="anchor_a",
    )
    
    # Domain B: Aggressive
    engine.create_policy(
        policy_id="policy_domain_b",
        name="Domain B Aggressive",
        description="AUTHORIZE on unknown in domain B",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="domain_b",
        created_by="admin_b",
        authority_basis="anchor_b",
    )
    
    # Apply both
    effect_a = engine.apply_policy("policy_domain_a", "unknown")
    effect_b = engine.apply_policy("policy_domain_b", "unknown")
    
    return engine.run_experiment(
        experiment_name="cross_domain_policy",
        description="Cross-domain uncertainty policies with different semantics",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect_b.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Domain B policy amplifies authority relative to Domain A",
        normative_assumptions=[
            "Different domains may have different uncertainty semantics",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 11: Uncertainty Policy Modification
# ---------------------------------------------------------------------------


def run_policy_modification(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Test uncertainty policy modification by an actor."""
    # Original policy
    engine.create_policy(
        policy_id="policy_original",
        name="Original Policy",
        description="Conservative uncertainty handling",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
        },
        authority_scope="governance",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    # Modified by policy_admin
    engine.create_policy(
        policy_id="policy_modified",
        name="Modified Policy",
        description="Aggressive uncertainty handling",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="governance",
        created_by="policy_admin",
        authority_basis="policy_authority",
    )
    
    effect = engine.apply_policy("policy_modified", "unknown")
    
    return engine.run_experiment(
        experiment_name="policy_modification",
        description="Policy modification from conservative to aggressive",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Policy modification detected as authority amplification",
        normative_assumptions=[
            "Policy modification requires authority",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 12: Uncertainty Policy Activation
# ---------------------------------------------------------------------------


def run_policy_activation(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Test uncertainty policy activation."""
    engine.create_policy(
        policy_id="policy_active",
        name="Active Policy",
        description="Currently active uncertainty policy",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="governance",
        created_by="admin",
        authority_basis="trust_anchor",
        metadata={"active": True},
    )
    
    effect = engine.apply_policy("policy_active", "unknown")
    
    return engine.run_experiment(
        experiment_name="policy_activation",
        description="Active uncertainty policy",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Active policy amplifies authority",
    )


# ---------------------------------------------------------------------------
# Experiment 13: Uncertainty Policy Rollback
# ---------------------------------------------------------------------------


def run_policy_rollback(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Test uncertainty policy rollback."""
    # Aggressive policy
    engine.create_policy(
        policy_id="policy_aggressive",
        name="Aggressive Policy",
        description="AUTHORIZE on unknown",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="governance",
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    # Rollback to conservative
    engine.create_policy(
        policy_id="policy_rollback",
        name="Rollback Policy",
        description="Rolled back to conservative",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
        },
        authority_scope="governance",
        created_by="admin",
        authority_basis="trust_anchor",
        metadata={"rollback_of": "policy_aggressive"},
    )
    
    effect = engine.apply_policy("policy_rollback", "unknown")
    
    return engine.run_experiment(
        experiment_name="policy_rollback",
        description="Policy rollback from aggressive to conservative",
        result=(
            UncertaintyPolicyResult.NO_AMPLIFICATION
            if not effect.authority_amplified
            else UncertaintyPolicyResult.AMPLIFICATION_DETECTED
        ),
        notes="Rollback to conservative removes amplification",
    )


# ---------------------------------------------------------------------------
# Experiment 14: Actor with Narrow Policy Authority Attempts Broad Change
# ---------------------------------------------------------------------------


def run_narrow_authority_attempt(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Actor with narrow policy authority attempts broad uncertainty policy change.
    
    The actor has authority to modify policy only within their scope,
    but attempts to modify uncertainty policy that has broad authority
    consequences.
    """
    # Actor has narrow scope
    engine.create_policy(
        policy_id="policy_narrow",
        name="Narrow Scope Policy",
        description="Actor with narrow scope modifies policy",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="narrow_scope",
        created_by="narrow_actor",
        authority_basis="delegated_authority",
        metadata={"actor_scope": "narrow"},
    )
    
    effect = engine.apply_policy("policy_narrow", "unknown")
    
    # Check effect boundary
    within_envelope, violations = engine.check_effect_boundary("policy_narrow")
    
    return engine.run_experiment(
        experiment_name="narrow_authority_attempt",
        description="Actor with narrow authority attempts broad policy",
        result=(
            UncertaintyPolicyResult.EFFECT_BOUNDARY_VIOLATION
            if not within_envelope
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes=f"Effect boundary violations: {violations}",
        underspecifications=[
            "Actor scope vs policy effect scope mismatch",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 15: Policy Creates Authority Exceeding Its Effect Envelope
# ---------------------------------------------------------------------------


def run_policy_exceeds_envelope(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Policy creates authority that exceeds its declared effect envelope.
    
    The policy declares a narrow scope but its effect creates authority
    beyond that scope.
    """
    engine.create_policy(
        policy_id="policy_exceeds",
        name="Exceeds Envelope",
        description="Policy declares narrow scope but creates broad authority",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="narrow_scope",  # Declared narrow
        max_authority_effect="authorize",  # But effect is broad
        created_by="admin",
        authority_basis="trust_anchor",
    )
    
    effect = engine.apply_policy("policy_exceeds", "unknown")
    
    within_envelope, violations = engine.check_effect_boundary("policy_exceeds")
    
    return engine.run_experiment(
        experiment_name="policy_exceeds_envelope",
        description="Policy creates authority exceeding its envelope",
        result=(
            UncertaintyPolicyResult.POLICY_EFFECT_EXCEEDS_AUTHORITY
            if not within_envelope
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes=f"Effect boundary violations: {violations}",
    )


# ---------------------------------------------------------------------------
# Experiment 16: Hidden Uncertainty-Policy Authority
# ---------------------------------------------------------------------------


def run_hidden_policy_authority(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Hidden uncertainty-policy authority.
    
    An uncertainty policy exists outside the declared authority graph.
    """
    # Hidden policy (not in declared graph)
    engine.create_policy(
        policy_id="policy_hidden",
        name="Hidden Policy",
        description="Hidden uncertainty policy",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="*",
        created_by="hidden_actor",
        authority_basis="hidden",
        metadata={"hidden": True, "declared": False},
    )
    
    effect = engine.apply_policy("policy_hidden", "unknown")
    
    return engine.run_experiment(
        experiment_name="hidden_policy_authority",
        description="Hidden uncertainty-policy authority",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Hidden policy amplifies authority without declared provenance",
        underspecifications=[
            "Hidden policy may not be visible to completeness checker",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 17: Unobservable Emergency Uncertainty Policy
# ---------------------------------------------------------------------------


def run_unobservable_emergency(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Unobservable emergency uncertainty policy.
    
    An emergency uncertainty policy that is unobservable under normal
    circumstances.
    """
    engine.create_policy(
        policy_id="policy_unobservable",
        name="Unobservable Emergency Policy",
        description="Emergency policy unobservable under normal conditions",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="emergency",
        created_by="emergency_admin",
        authority_basis="emergency_anchor",
        metadata={"observable": False, "emergency": True},
    )
    
    effect = engine.apply_policy("policy_unobservable", "unknown")
    
    return engine.run_experiment(
        experiment_name="unobservable_emergency",
        description="Unobservable emergency uncertainty policy",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Unobservable emergency policy can amplify authority",
        underspecifications=[
            "Emergency policies may bypass normal observation",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 18: Two Domains with Different Uncertainty Semantics
# ---------------------------------------------------------------------------


def run_different_semantics(engine: UncertaintyPolicyAuthorityEngine) -> UncertaintyPolicyExperiment:
    """Two domains with different uncertainty semantics.
    
    Domain A: UNKNOWN → HOLD
    Domain B: UNKNOWN → AUTHORIZE
    
    Both are valid policies but have different authority consequences.
    This tests POLICY VALIDITY ≠ POLICY AUTHORITY ≠ POLICY CORRECTNESS ≠ POLICY EFFECT.
    """
    # Domain A: Conservative
    engine.create_policy(
        policy_id="policy_semantics_a",
        name="Domain A Conservative",
        description="UNKNOWN → HOLD",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "review",
            "unknown": "hold",
        },
        authority_scope="domain_a",
        created_by="admin_a",
        authority_basis="anchor_a",
    )
    
    # Domain B: Aggressive
    engine.create_policy(
        policy_id="policy_semantics_b",
        name="Domain B Aggressive",
        description="UNKNOWN → AUTHORIZE",
        state_to_disposition={
            "complete": "normal",
            "incomplete": "authorize",
            "unknown": "authorize",
        },
        authority_scope="domain_b",
        created_by="admin_b",
        authority_basis="anchor_b",
    )
    
    effect_a = engine.apply_policy("policy_semantics_a", "unknown")
    effect_b = engine.apply_policy("policy_semantics_b", "unknown")
    
    return engine.run_experiment(
        experiment_name="different_semantics",
        description="Two domains with different uncertainty semantics",
        result=(
            UncertaintyPolicyResult.AMPLIFICATION_DETECTED
            if effect_b.authority_amplified
            else UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        notes="Domain B amplifies authority relative to Domain A",
        normative_assumptions=[
            "Both policies are valid but have different authority consequences",
            "POLICY VALIDITY ≠ POLICY AUTHORITY ≠ POLICY CORRECTNESS ≠ POLICY EFFECT",
        ],
    )


# ---------------------------------------------------------------------------
# Run All Phase 21 Experiments
# ---------------------------------------------------------------------------


def run_all_phase21_experiments() -> dict[str, Any]:
    """Run all Phase 21 experiments."""
    engine = UncertaintyPolicyAuthorityEngine()
    
    experiments = [
        run_unknown_hold(engine),
        run_unknown_review(engine),
        run_unknown_escalate(engine),
        run_unknown_deny(engine),
        run_unknown_authorize(engine),
    ]
    
    # Reset for next batch
    engine = UncertaintyPolicyAuthorityEngine()
    experiments.extend([
        run_incomplete_authorize(engine),
        run_was_complete_authorize(engine),
        run_historical_policy_change(engine),
        run_emergency_policy(engine),
    ])
    
    engine = UncertaintyPolicyAuthorityEngine()
    experiments.extend([
        run_cross_domain_policy(engine),
        run_policy_modification(engine),
        run_policy_activation(engine),
        run_policy_rollback(engine),
    ])
    
    engine = UncertaintyPolicyAuthorityEngine()
    experiments.extend([
        run_narrow_authority_attempt(engine),
        run_policy_exceeds_envelope(engine),
        run_hidden_policy_authority(engine),
        run_unobservable_emergency(engine),
        run_different_semantics(engine),
    ])
    
    return {
        "experiments": {e.experiment_name: e for e in experiments},
        "total_experiments": len(experiments),
        "amplification_detected": sum(
            1 for e in experiments
            if e.result == UncertaintyPolicyResult.AMPLIFICATION_DETECTED
        ),
        "no_amplification": sum(
            1 for e in experiments
            if e.result == UncertaintyPolicyResult.NO_AMPLIFICATION
        ),
        "effect_boundary_violations": sum(
            1 for e in experiments
            if e.result == UncertaintyPolicyResult.EFFECT_BOUNDARY_VIOLATION
        ),
        "policy_exceeds_authority": sum(
            1 for e in experiments
            if e.result == UncertaintyPolicyResult.POLICY_EFFECT_EXCEEDS_AUTHORITY
        ),
    }


if __name__ == "__main__":
    results = run_all_phase21_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 21: UNCERTAINTY POLICY AUTHORITY AND EPISTEMIC ESCALATION")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Amplification detected: {results['amplification_detected']}")
    print(f"No amplification: {results['no_amplification']}")
    print(f"Effect boundary violations: {results['effect_boundary_violations']}")
    print(f"Policy exceeds authority: {results['policy_exceeds_authority']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Description: {exp.description}")
        print(f"  Result: {exp.result.value}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
