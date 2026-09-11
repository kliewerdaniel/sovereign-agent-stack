"""Phase 30: Runtime Effect Revelation and Epistemic Promotion.

Central question:
    Can runtime observation convert a structurally possible or unknown effect
    into a concrete, provenance-bearing effect observation without incorrectly
    treating non-observation as evidence of absence?

The epistemic ladder:
    UNKNOWN → STRUCTURAL POSSIBILITY → RUNTIME OBSERVATION → CONCRETE EFFECT → RECONCILIATION → COMPLETENESS

With NO upward shortcut from "we didn't see it" to "it doesn't exist."

Critical distinctions:
    NOT_OBSERVED ≠ DOES_NOT_EXIST
    NOT_EXECUTED_YET ≠ WILL_NEVER_EXECUTE
    OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT
    OBSERVATION ≠ AUTHORITY
    EXECUTION_RECEIPT ≠ AUTHORITY
    STRUCTURAL_POSSIBILITY ≠ EXECUTED_EFFECT
    RUNTIME_OBSERVATION ≠ GLOBAL_COMPLETENESS
    OBSERVED_SET ≠ COMPLETE_EFFECT_SET
    ATTRIBUTION_UNKNOWN ≠ ATTRIBUTION_TO_CALLER
    CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY
    TEMPORAL_OBSERVATION ≠ HISTORICAL_EXISTENCE
    REVALIDATION ≠ RETROACTIVE_INVALIDATION
    COMPLETENESS ≠ CLOSURE
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Core enumerations
# ---------------------------------------------------------------------------


class EffectCategory(str, Enum):
    """Categories of consequential effects."""
    SUBPROCESS = "subprocess"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    BROKER = "broker"
    PAYMENT = "payment"
    IDENTITY = "identity"
    CREDENTIAL = "credential"
    PLUGIN = "plugin"
    DYNAMIC_IMPORT = "dynamic_import"


class EffectVisibility(str, Enum):
    """How an effect relates to the declared inventory."""
    DECLARED = "declared"
    OBSERVED = "observed"
    AVAILABLE = "available"
    EXECUTED = "executed"
    HIDDEN = "hidden"
    UNOBSERVED = "unobserved"


class AuthorityPathStatus(str, Enum):
    """Status of an effect's authority path."""
    GOVERNED = "governed"
    UNGOVERNED = "ungoverned"
    ESCAPE = "escape"
    UNKNOWN = "unknown"


class RevelationState(str, Enum):
    """Epistemic state of an effect in the runtime revelation model.

    The ladder:
        UNKNOWN → STRUCTURALLY_POSSIBLE → POSSIBLY_REACHABLE →
        REACHABLE_BUT_UNOBSERVED → OBSERVED → EXECUTED → NOT_OBSERVED

    Critical: NOT_OBSERVED is NOT the same as NO_EFFECT.
    """
    UNKNOWN = "unknown"
    STRUCTURALLY_POSSIBLE = "structurally_possible"
    POSSIBLY_REACHABLE = "possibly_reachable"
    REACHABLE_BUT_UNOBSERVED = "reachable_but_unobserved"
    OBSERVED = "observed"
    EXECUTED = "executed"
    NOT_OBSERVED = "not_observed"


class ExecutionStatus(str, Enum):
    """Whether an effect has been executed."""
    NEVER_EXECUTED = "never_executed"
    EXECUTING = "executing"
    EXECUTED = "executed"
    EXECUTED_MULTIPLE = "executed_multiple"


class AttributionStatus(str, Enum):
    """Status of authority attribution for an observed effect."""
    ATTRIBUTED = "attributed"
    ATTRIBUTION_UNKNOWN = "attribution_unknown"
    ATTRIBUTION_PARTIAL = "attribution_partial"
    CROSS_DOMAIN_BLOCKED = "cross_domain_blocked"


class ObservationScope(str, Enum):
    """Scope of an observation."""
    PRODUCTION = "production"
    STAGING = "staging"
    TEST = "test"
    DEVELOPMENT = "development"


class PromotionAction(str, Enum):
    """Action taken by the promotion engine."""
    NO_ACTION = "no_action"
    PROMOTED_TO_OBSERVED = "promoted_to_observed"
    PROMOTED_TO_CONCRETE = "promoted_to_concrete"
    INVENTORY_EXTENDED = "inventory_extended"
    COMPLETENESS_REASSESSMENT = "completeness_reassessment"
    ESCAPE_DETECTED = "escape_detected"
    REVALIDATION_REQUIRED = "revalidation_required"


# ---------------------------------------------------------------------------
# Effect representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsequentialEffect:
    """A single consequential effect."""
    effect_id: str
    category: EffectCategory
    source: str
    target: str
    operation: str
    visibility: EffectVisibility
    authority_path_status: AuthorityPathStatus
    description: str = ""
    hidden_mechanism: str = ""
    scope: str = "runtime"
    temporal_boundary: str = ""
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Runtime effect observation — the core epistemic object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeEffectObservation:
    """A concrete observation of an effect executing at runtime.

    This is evidence that an effect occurred. It is NOT:
    - authorization for the effect
    - proof that the effect was permitted
    - proof that the effect was necessary
    - authority for future executions

    It IS:
    - evidence that the effect occurred at a specific time
    - evidence of the execution context (actor, scope, domain)
    - evidence that can be reconciled with the inventory
    - evidence that can trigger revalidation

    Fields preserve the full epistemic context:
        observation_id: unique identifier
        effect_id: which effect was observed
        timestamp: when the observation was made
        actor: who/what triggered the effect
        component: which component executed
        operation: what operation was performed
        resource: what resource was affected
        category: effect category
        source: source path
        target: target primitive
        execution_status: whether execution completed
        authority_context: authority context at time of execution
        capability_id: capability used (if any)
        authorization_id: authorization reference (if any)
        provenance_id: provenance record (if any)
        scope: observation scope (production/staging/test)
        domain: domain of execution
        execution_path: call path if available
        triggering_event: what triggered the execution
        observation_mechanism: how the observation was made
        receipt: execution receipt if available
        temporal_validity: when this observation is valid
        provenance: lineage of the observation
        attribution_status: whether authority was attributed
        relationship_to_inventory: how this relates to the inventory
        metadata: additional metadata
    """
    observation_id: str
    effect_id: str
    timestamp: str
    actor: str
    component: str
    operation: str
    resource: str
    category: EffectCategory
    source: str
    target: str
    execution_status: ExecutionStatus
    authority_context: dict[str, Any]
    capability_id: str | None
    authorization_id: str | None
    provenance_id: str | None
    scope: ObservationScope
    domain: str
    execution_path: list[str]
    triggering_event: str
    observation_mechanism: str
    receipt: str | None
    temporal_validity: str
    provenance: str
    attribution_status: AttributionStatus
    relationship_to_inventory: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Runtime revelation world
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeRevelationWorld:
    """An adversarial world for runtime effect revelation experiments.

    Contains:
        declared_effects — what the inventory says exists
        hidden_effects — effects that exist but are NOT in inventory
        executed_effects — effects that actually execute during the experiment
        ground_truth — union of declared + hidden
        has_hidden_effects — whether hidden effects exist
        has_executed_hidden — whether hidden effects actually execute
        execution_triggers — what triggers execution of each effect
    """
    world_id: str
    description: str
    declared_effects: tuple[ConsequentialEffect, ...]
    hidden_effects: tuple[ConsequentialEffect, ...]
    executed_effects: tuple[ConsequentialEffect, ...]
    ground_truth_effects: tuple[ConsequentialEffect, ...]
    attack_category: str
    has_structural_anomaly: bool = False
    structural_anomaly_description: str = ""
    benign_code: tuple[ConsequentialEffect, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def hidden_count(self) -> int:
        return len(self.hidden_effects)

    @property
    def has_hidden_effects(self) -> bool:
        return len(self.hidden_effects) > 0

    @property
    def has_executed_hidden(self) -> bool:
        return len(self.executed_effects) > 0

    @property
    def has_benign_code(self) -> bool:
        return len(self.benign_code) > 0

    @property
    def never_executed_effects(self) -> tuple[ConsequentialEffect, ...]:
        """Effects that exist but never execute."""
        executed_ids = {e.effect_id for e in self.executed_effects}
        return tuple(
            e for e in self.ground_truth_effects
            if e.effect_id not in executed_ids
        )


# ---------------------------------------------------------------------------
# Promotion result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromotionResult:
    """Result of attempting to promote an effect through the epistemic ladder."""
    result_id: str
    world_id: str
    effect_id: str
    initial_state: RevelationState
    final_state: RevelationState
    action: PromotionAction
    observation: RuntimeEffectObservation | None
    timestamp: str
    provenance: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Oracle evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OracleEvaluation:
    """Independent oracle evaluation of a runtime observation.

    The oracle knows the ground truth but the runtime observer does not.
    """
    evaluation_id: str
    world_id: str
    observation_count: int
    true_observed: tuple[str, ...]      # effect_ids correctly observed
    false_observed: tuple[str, ...]     # effect_ids observed but not in ground truth
    missed_effects: tuple[str, ...]     # ground-truth effects never observed
    never_executed: tuple[str, ...]     # effects that exist but never execute
    attribution_correct: tuple[str, ...] # observations with correct attribution
    attribution_unknown: tuple[str, ...] # observations with unknown attribution
    escape_detected: tuple[str, ...]    # unauthorized executions detected
    notes: str = ""


# ---------------------------------------------------------------------------
# Runtime observer
# ---------------------------------------------------------------------------


class RuntimeObserver:
    """Observes runtime execution and produces evidence of effects.

    CRITICAL INVARIANTS:
        OBSERVATION ≠ AUTHORITY
        OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT
        EXECUTION_RECEIPT ≠ AUTHORITY
        NOT_OBSERVED ≠ DOES_NOT_EXIST
        ATTRIBUTION_UNKNOWN ≠ ATTRIBUTION_TO_CALLER

    The observer records what happened. The authority system determines
    what was permitted.
    """

    def __init__(self, observer_id: str, scope: ObservationScope = ObservationScope.PRODUCTION):
        self.observer_id = observer_id
        self.scope = scope
        self.observations: list[RuntimeEffectObservation] = []

    def observe(
        self,
        effect: ConsequentialEffect,
        actor: str,
        component: str,
        operation: str,
        resource: str,
        execution_status: ExecutionStatus,
        authority_context: dict[str, Any] | None = None,
        capability_id: str | None = None,
        authorization_id: str | None = None,
        provenance_id: str | None = None,
        domain: str = "default",
        execution_path: list[str] | None = None,
        triggering_event: str = "",
        receipt: str | None = None,
        attribution_status: AttributionStatus = AttributionStatus.ATTRIBUTION_UNKNOWN,
    ) -> RuntimeEffectObservation:
        """Record an observation of an effect executing."""
        observation = RuntimeEffectObservation(
            observation_id=f"obs-{uuid.uuid4().hex[:12]}",
            effect_id=effect.effect_id,
            timestamp=datetime.now(UTC).isoformat(),
            actor=actor,
            component=component,
            operation=operation,
            resource=resource,
            category=effect.category,
            source=effect.source,
            target=effect.target,
            execution_status=execution_status,
            authority_context=authority_context or {},
            capability_id=capability_id,
            authorization_id=authorization_id,
            provenance_id=provenance_id,
            scope=self.scope,
            domain=domain,
            execution_path=execution_path or [],
            triggering_event=triggering_event,
            observation_mechanism=self.observer_id,
            receipt=receipt,
            temporal_validity=datetime.now(UTC).isoformat(),
            provenance=f"{self.observer_id}:{effect.effect_id}",
            attribution_status=attribution_status,
            relationship_to_inventory=self._classify_inventory_relation(effect),
        )
        self.observations.append(observation)
        return observation

    def _classify_inventory_relation(self, effect: ConsequentialEffect) -> str:
        """Classify how an effect relates to the inventory."""
        if effect.visibility == EffectVisibility.DECLARED:
            return "in_inventory"
        elif effect.visibility == EffectVisibility.HIDDEN:
            return "not_in_inventory"
        elif effect.visibility == EffectVisibility.OBSERVED:
            return "observed_not_declared"
        else:
            return "unknown"

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    def get_observations_by_category(self, category: EffectCategory) -> list[RuntimeEffectObservation]:
        return [o for o in self.observations if o.category == category]

    def get_observations_by_effect(self, effect_id: str) -> list[RuntimeEffectObservation]:
        return [o for o in self.observations if o.effect_id == effect_id]


# ---------------------------------------------------------------------------
# Independent oracle
# ---------------------------------------------------------------------------


class IndependentOracle:
    """Evaluates runtime observations against ground truth.

    The oracle knows:
        - effect exists
        - effect executes
        - expected category
        - expected source

    The runtime observer may only know what the runtime actually exposes.
    """

    def evaluate(
        self,
        world: RuntimeRevelationWorld,
        observations: list[RuntimeEffectObservation],
    ) -> OracleEvaluation:
        """Evaluate observations against ground truth."""
        observed_effect_ids = {o.effect_id for o in observations}
        ground_truth_ids = {e.effect_id for e in world.ground_truth_effects}
        executed_ids = {e.effect_id for e in world.executed_effects}

        # True observed: correctly observed effects that exist
        true_observed = tuple(
            eid for eid in observed_effect_ids
            if eid in ground_truth_ids
        )

        # False observed: observed but not in ground truth
        false_observed = tuple(
            eid for eid in observed_effect_ids
            if eid not in ground_truth_ids
        )

        # Missed: ground-truth effects that were never observed
        # (either because they never executed or because the observer missed them)
        missed = tuple(
            eid for eid in ground_truth_ids
            if eid not in observed_effect_ids
        )

        # Never executed: effects that exist but never ran
        never_executed = tuple(
            eid for eid in ground_truth_ids
            if eid not in executed_ids
        )

        # Attribution analysis
        attribution_correct = tuple(
            o.effect_id for o in observations
            if o.attribution_status == AttributionStatus.ATTRIBUTED
        )
        attribution_unknown = tuple(
            o.effect_id for o in observations
            if o.attribution_status == AttributionStatus.ATTRIBUTION_UNKNOWN
        )

        # Escape detection: observed effects with no authority
        escape_detected = tuple(
            o.effect_id for o in observations
            if o.attribution_status == AttributionStatus.ATTRIBUTION_UNKNOWN
            and o.relationship_to_inventory == "not_in_inventory"
        )

        return OracleEvaluation(
            evaluation_id=f"eval-{uuid.uuid4().hex[:12]}",
            world_id=world.world_id,
            observation_count=len(observations),
            true_observed=true_observed,
            false_observed=false_observed,
            missed_effects=missed,
            never_executed=never_executed,
            attribution_correct=attribution_correct,
            attribution_unknown=attribution_unknown,
            escape_detected=escape_detected,
        )


# ---------------------------------------------------------------------------
# Promotion engine
# ---------------------------------------------------------------------------


class PromotionEngine:
    """Manages epistemic promotion of effects through the revelation ladder.

    The ladder:
        UNKNOWN → STRUCTURALLY_POSSIBLE → POSSIBLY_REACHABLE →
        REACHABLE_BUT_UNOBSERVED → OBSERVED → EXECUTED → NOT_OBSERVED

    Rules:
        1. Promotion requires runtime evidence.
        2. NOT_OBSERVED never promotes to NO_EFFECT.
        3. OBSERVATION never creates AUTHORITY.
        4. Each transition must be earned.
    """

    def attempt_promotion(
        self,
        effect: ConsequentialEffect,
        current_state: RevelationState,
        observation: RuntimeEffectObservation | None = None,
    ) -> PromotionResult:
        """Attempt to promote an effect to a higher epistemic state."""
        if current_state == RevelationState.UNKNOWN:
            if observation is not None:
                return self._promote_to_observed(effect, observation)
            return self._no_promotion(effect, current_state, "No observation provided")

        elif current_state == RevelationState.STRUCTURALLY_POSSIBLE:
            if observation is not None:
                return self._promote_to_observed(effect, observation)
            return self._no_promotion(effect, current_state, "Structural possibility without execution")

        elif current_state == RevelationState.POSSIBLY_REACHABLE:
            if observation is not None:
                return self._promote_to_observed(effect, observation)
            return self._no_promotion(effect, current_state, "Possibly reachable but not observed")

        elif current_state == RevelationState.REACHABLE_BUT_UNOBSERVED:
            if observation is not None:
                return self._promote_to_observed(effect, observation)
            return self._no_promotion(effect, current_state, "Reachable but not observed")

        elif current_state == RevelationState.OBSERVED:
            if observation is not None and observation.execution_status == ExecutionStatus.EXECUTED:
                return self._promote_to_executed(effect, observation)
            return self._no_promotion(effect, current_state, "Already observed, no new execution")

        elif current_state == RevelationState.EXECUTED:
            return self._no_promotion(effect, current_state, "Already at highest state")

        elif current_state == RevelationState.NOT_OBSERVED:
            # NOT_OBSERVED never promotes to NO_EFFECT
            # It stays NOT_OBSERVED unless runtime evidence arrives
            if observation is not None:
                return self._promote_to_observed(effect, observation)
            return self._no_promotion(effect, current_state, "NOT_OBSERVED preserved (≠ NO_EFFECT)")

        return self._no_promotion(effect, current_state, "Unknown state")

    def _promote_to_observed(
        self, effect: ConsequentialEffect, observation: RuntimeEffectObservation
    ) -> PromotionResult:
        return PromotionResult(
            result_id=f"promo-{uuid.uuid4().hex[:12]}",
            world_id="",
            effect_id=effect.effect_id,
            initial_state=RevelationState.UNKNOWN,
            final_state=RevelationState.OBSERVED,
            action=PromotionAction.PROMOTED_TO_OBSERVED,
            observation=observation,
            timestamp=datetime.now(UTC).isoformat(),
            provenance=f"promotion_engine:{effect.effect_id}",
        )

    def _promote_to_executed(
        self, effect: ConsequentialEffect, observation: RuntimeEffectObservation
    ) -> PromotionResult:
        return PromotionResult(
            result_id=f"promo-{uuid.uuid4().hex[:12]}",
            world_id="",
            effect_id=effect.effect_id,
            initial_state=RevelationState.OBSERVED,
            final_state=RevelationState.EXECUTED,
            action=PromotionAction.PROMOTED_TO_CONCRETE,
            observation=observation,
            timestamp=datetime.now(UTC).isoformat(),
            provenance=f"promotion_engine:{effect.effect_id}",
        )

    def _no_promotion(
        self, effect: ConsequentialEffect, current_state: RevelationState, reason: str
    ) -> PromotionResult:
        return PromotionResult(
            result_id=f"promo-{uuid.uuid4().hex[:12]}",
            world_id="",
            effect_id=effect.effect_id,
            initial_state=current_state,
            final_state=current_state,
            action=PromotionAction.NO_ACTION,
            observation=None,
            timestamp=datetime.now(UTC).isoformat(),
            provenance=f"promotion_engine:{effect.effect_id}",
            notes=reason,
        )


# ---------------------------------------------------------------------------
# Adversarial world generator
# ---------------------------------------------------------------------------


class AdversarialWorldGenerator:
    """Generates runtime revelation worlds."""

    def __init__(self):
        self._worlds: list[RuntimeRevelationWorld] = []

    def generate_all_worlds(self) -> list[RuntimeRevelationWorld]:
        """Generate all 10 runtime revelation worlds (A-J)."""
        self._worlds = [
            self._world_a_hidden_never_executed(),
            self._world_b_hidden_executed(),
            self._world_c_structurally_visible_not_executed(),
            self._world_d_structurally_unknown_then_executed(),
            self._world_e_conditionally_executed(),
            self._world_f_emergency_executed(),
            self._world_g_recovery_executed(),
            self._world_h_background_executed(),
            self._world_i_dynamically_loaded_executed(),
            self._world_j_multiple_executions(),
        ]
        return self._worlds

    def _make_effect(
        self,
        category: EffectCategory,
        source: str,
        target: str,
        operation: str,
        visibility: EffectVisibility = EffectVisibility.DECLARED,
        authority_path_status: AuthorityPathStatus = AuthorityPathStatus.GOVERNED,
        description: str = "",
        hidden_mechanism: str = "",
    ) -> ConsequentialEffect:
        return ConsequentialEffect(
            effect_id=f"eff-{uuid.uuid4().hex[:12]}",
            category=category,
            source=source,
            target=target,
            operation=operation,
            visibility=visibility,
            authority_path_status=authority_path_status,
            description=description,
            hidden_mechanism=hidden_mechanism,
        )

    def _world_a_hidden_never_executed(self) -> RuntimeRevelationWorld:
        """A. HIDDEN_AND_NEVER_EXECUTED — effect exists but path never triggered."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/legacy.py",
                              "subprocess.Popen", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Hidden subprocess in legacy module",
                              hidden_mechanism="dead_code"),
        )
        return RuntimeRevelationWorld(
            world_id="world_A_hidden_never_executed",
            description="Hidden effect exists but execution path is never triggered",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=(),  # Nothing executes
            ground_truth_effects=declared + hidden,
            attack_category="hidden_never_executed",
            has_structural_anomaly=True,
            structural_anomaly_description="Hidden effect in dead code path",
        )

    def _world_b_hidden_executed(self) -> RuntimeRevelationWorld:
        """B. HIDDEN_AND_EXECUTED — effect exists outside inventory and executes."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/cli/helper.py",
                              "subprocess.Popen", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Hidden subprocess in CLI helper",
                              hidden_mechanism="indirect_helper"),
        )
        return RuntimeRevelationWorld(
            world_id="world_B_hidden_executed",
            description="Hidden effect exists outside inventory and is executed",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="hidden_executed",
        )

    def _world_c_structurally_visible_not_executed(self) -> RuntimeRevelationWorld:
        """C. STRUCTURALLY_VISIBLE_BUT_NOT_EXECUTED — static analysis finds it, runtime never reaches."""
        declared = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/registry.py",
                              "open", "file.write"),
        )
        hidden = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/deprecated/utils.py",
                              "shutil.copy", "file.copy",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Deprecated utility — dead code",
                              hidden_mechanism="dead_code"),
        )
        return RuntimeRevelationWorld(
            world_id="world_C_structurally_visible_not_executed",
            description="Static analysis can identify the effect but runtime never reaches it",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=(),  # Nothing executes
            ground_truth_effects=declared + hidden,
            attack_category="structurally_visible_not_executed",
            has_structural_anomaly=True,
            structural_anomaly_description="Dead code appears consequential but never executes",
            benign_code=hidden,
        )

    def _world_d_structurally_unknown_then_executed(self) -> RuntimeRevelationWorld:
        """D. STRUCTURALLY_UNKNOWN_THEN_EXECUTED — no prior discovery, runtime reveals it."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.DYNAMIC_IMPORT, "src/sas/plugins/loader.py",
                              "importlib.import_module", "dynamic_load",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Dynamically loaded plugin spawns subprocess",
                              hidden_mechanism="dynamic_plugin"),
        )
        return RuntimeRevelationWorld(
            world_id="world_D_structurally_unknown_then_executed",
            description="No prior discovery mechanism identifies the effect, but runtime execution reveals it",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="structurally_unknown_then_executed",
        )

    def _world_e_conditionally_executed(self) -> RuntimeRevelationWorld:
        """E. CONDITIONALLY_EXECUTED — effect executes only under specific condition."""
        declared = (
            self._make_effect(EffectCategory.DATABASE, "src/sas_tie_knowledge/adapter.py",
                              "aiosqlite", "db.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.NETWORK, "src/sas/quant/cache.py",
                              "requests.get", "http.request",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Cache miss triggers network fetch",
                              hidden_mechanism="cache_miss"),
        )
        return RuntimeRevelationWorld(
            world_id="world_E_conditionally_executed",
            description="Effect executes only under a specific condition (cache miss)",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="conditionally_executed",
        )

    def _world_f_emergency_executed(self) -> RuntimeRevelationWorld:
        """F. EMERGENCY_EXECUTED — effect executes only through emergency path."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/emergency.py",
                              "os.system", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Emergency kill switch bypasses governance",
                              hidden_mechanism="emergency_path"),
        )
        return RuntimeRevelationWorld(
            world_id="world_F_emergency_executed",
            description="Effect executes only through an emergency path",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="emergency_executed",
        )

    def _world_g_recovery_executed(self) -> RuntimeRevelationWorld:
        """G. RECOVERY_EXECUTED — effect executes only through exception/recovery."""
        declared = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/registry.py",
                              "open", "file.write"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/recovery.py",
                              "subprocess.Popen", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Recovery path spawns subprocess",
                              hidden_mechanism="exception_recovery"),
        )
        return RuntimeRevelationWorld(
            world_id="world_G_recovery_executed",
            description="Effect executes only through exception/recovery handling",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="recovery_executed",
        )

    def _world_h_background_executed(self) -> RuntimeRevelationWorld:
        """H. BACKGROUND_EXECUTED — effect executes asynchronously."""
        declared = (
            self._make_effect(EffectCategory.DATABASE, "src/sas_tie_knowledge/adapter.py",
                              "aiosqlite", "db.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/quant/background.py",
                              "open", "file.write",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Background worker writes files",
                              hidden_mechanism="background_worker"),
        )
        return RuntimeRevelationWorld(
            world_id="world_H_background_executed",
            description="Effect executes asynchronously outside the initiating call path",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="background_executed",
        )

    def _world_i_dynamically_loaded_executed(self) -> RuntimeRevelationWorld:
        """I. DYNAMICALLY_LOADED_AND_EXECUTED — plugin loaded dynamically then performs effect."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.PLUGIN, "src/sas/plugins/dynamic.py",
                              "importlib.import_module", "dynamic_load",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Dynamically loaded plugin performs network call",
                              hidden_mechanism="dynamic_plugin"),
        )
        return RuntimeRevelationWorld(
            world_id="world_I_dynamically_loaded_executed",
            description="Plugin/module is loaded dynamically and then performs an effect",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="dynamically_loaded_executed",
        )

    def _world_j_multiple_executions(self) -> RuntimeRevelationWorld:
        """J. MULTIPLE_EXECUTIONS — same effect executes multiple times with different authority."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/multi.py",
                              "subprocess.Popen", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Same subprocess called by multiple actors",
                              hidden_mechanism="multiple_actors"),
        )
        return RuntimeRevelationWorld(
            world_id="world_J_multiple_executions",
            description="Same effect executes multiple times under different authority/scope/time conditions",
            declared_effects=declared,
            hidden_effects=hidden,
            executed_effects=hidden,  # The hidden effect executes
            ground_truth_effects=declared + hidden,
            attack_category="multiple_executions",
        )


# ---------------------------------------------------------------------------
# Phase 30 experiment
# ---------------------------------------------------------------------------


class Phase30Experiment:
    """Runs the full Phase 30 experiment suite."""

    def __init__(self):
        self.worlds = AdversarialWorldGenerator().generate_all_worlds()
        self.observer = RuntimeObserver("phase30_observer")
        self.oracle = IndependentOracle()
        self.promotion_engine = PromotionEngine()
        self.results: list[PromotionResult] = []
        self.evaluations: list[OracleEvaluation] = []

    def run_all(self) -> dict[str, Any]:
        """Run all worlds and return summary."""
        for world in self.worlds:
            self._run_world(world)
        return self.summary()

    def _run_world(self, world: RuntimeRevelationWorld) -> None:
        """Run a single world through the runtime observer."""
        # Observe executed effects
        for effect in world.executed_effects:
            observation = self.observer.observe(
                effect=effect,
                actor=f"actor-{world.world_id}",
                component=effect.source,
                operation=effect.operation,
                resource="test-resource",
                execution_status=ExecutionStatus.EXECUTED,
                authority_context={"world": world.world_id},
                domain="test-domain",
                execution_path=[effect.source, effect.target],
                triggering_event=f"trigger-{world.world_id}",
                attribution_status=AttributionStatus.ATTRIBUTION_UNKNOWN,
            )
            self.results.append(self.promotion_engine.attempt_promotion(
                effect=effect,
                current_state=RevelationState.UNKNOWN,
                observation=observation,
            ))

        # Evaluate with oracle
        world_observations = [
            o for o in self.observer.observations
            if o.effect_id in {e.effect_id for e in world.ground_truth_effects}
        ]
        self.evaluations.append(self.oracle.evaluate(world, world_observations))

    def summary(self) -> dict[str, Any]:
        """Generate experiment summary."""
        return {
            "total_worlds": len(self.worlds),
            "total_observations": self.observer.observation_count,
            "total_promotions": len(self.results),
            "worlds_with_hidden_effects": sum(1 for w in self.worlds if w.has_hidden_effects),
            "worlds_with_executed_hidden": sum(1 for w in self.worlds if w.has_executed_hidden),
            "total_true_observed": sum(len(e.true_observed) for e in self.evaluations),
            "total_missed": sum(len(e.missed_effects) for e in self.evaluations),
            "total_never_executed": sum(len(e.never_executed) for e in self.evaluations),
            "total_escape_detected": sum(len(e.escape_detected) for e in self.evaluations),
        }
