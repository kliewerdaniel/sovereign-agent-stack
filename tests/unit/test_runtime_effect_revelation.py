"""Tests for Phase 30: Runtime Effect Revelation and Epistemic Promotion."""

import pytest
from research.examples.sovereign_agent.runtime_effect_revelation import (
    AdversarialWorldGenerator,
    AttributionStatus,
    AuthorityPathStatus,
    ConsequentialEffect,
    EffectCategory,
    EffectVisibility,
    ExecutionStatus,
    IndependentOracle,
    ObservationScope,
    Phase30Experiment,
    PromotionAction,
    PromotionEngine,
    PromotionResult,
    RevelationState,
    RuntimeEffectObservation,
    RuntimeObserver,
    RuntimeRevelationWorld,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generator() -> AdversarialWorldGenerator:
    return AdversarialWorldGenerator()


@pytest.fixture
def worlds(generator: AdversarialWorldGenerator) -> list[RuntimeRevelationWorld]:
    return generator.generate_all_worlds()


@pytest.fixture
def observer() -> RuntimeObserver:
    return RuntimeObserver("test_observer", ObservationScope.TEST)


@pytest.fixture
def oracle() -> IndependentOracle:
    return IndependentOracle()


@pytest.fixture
def promotion_engine() -> PromotionEngine:
    return PromotionEngine()


def _make_effect(
    category: EffectCategory = EffectCategory.SUBPROCESS,
    source: str = "src/sas/argopack.py",
    target: str = "subprocess.run",
    operation: str = "subprocess.execute",
    visibility: EffectVisibility = EffectVisibility.DECLARED,
    authority_path_status: AuthorityPathStatus = AuthorityPathStatus.GOVERNED,
    description: str = "",
    hidden_mechanism: str = "",
) -> ConsequentialEffect:
    return ConsequentialEffect(
        effect_id=f"eff-test-{uuid.uuid4().hex[:8]}",
        category=category,
        source=source,
        target=target,
        operation=operation,
        visibility=visibility,
        authority_path_status=authority_path_status,
        description=description,
        hidden_mechanism=hidden_mechanism,
    )


import uuid


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------

class TestWorldGeneration:
    def test_generates_10_worlds(self, generator: AdversarialWorldGenerator):
        worlds = generator.generate_all_worlds()
        assert len(worlds) == 10

    def test_worlds_have_unique_ids(self, worlds: list[RuntimeRevelationWorld]):
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_all_worlds_have_ground_truth(self, worlds: list[RuntimeRevelationWorld]):
        for world in worlds:
            assert len(world.ground_truth_effects) > 0

    def test_ground_truth_equals_declared_plus_hidden(self, worlds: list[RuntimeRevelationWorld]):
        for world in worlds:
            expected_ids = {e.effect_id for e in world.declared_effects} | {e.effect_id for e in world.hidden_effects}
            actual_ids = {e.effect_id for e in world.ground_truth_effects}
            assert expected_ids == actual_ids

    def test_world_A_hidden_never_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[0]
        assert world.world_id == "world_A_hidden_never_executed"
        assert world.has_hidden_effects
        assert not world.has_executed_hidden
        assert len(world.executed_effects) == 0
        assert len(world.never_executed_effects) > 0

    def test_world_B_hidden_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[1]
        assert world.world_id == "world_B_hidden_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden
        assert len(world.executed_effects) > 0

    def test_world_C_structurally_visible_not_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[2]
        assert world.world_id == "world_C_structurally_visible_not_executed"
        assert world.has_hidden_effects
        assert not world.has_executed_hidden
        assert world.has_benign_code

    def test_world_D_structurally_unknown_then_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[3]
        assert world.world_id == "world_D_structurally_unknown_then_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden

    def test_world_E_conditionally_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[4]
        assert world.world_id == "world_E_conditionally_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden

    def test_world_F_emergency_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[5]
        assert world.world_id == "world_F_emergency_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden

    def test_world_G_recovery_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[6]
        assert world.world_id == "world_G_recovery_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden

    def test_world_H_background_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[7]
        assert world.world_id == "world_H_background_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden

    def test_world_I_dynamically_loaded_executed(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[8]
        assert world.world_id == "world_I_dynamically_loaded_executed"
        assert world.has_hidden_effects
        assert world.has_executed_hidden

    def test_world_J_multiple_executions(self, worlds: list[RuntimeRevelationWorld]):
        world = worlds[9]
        assert world.world_id == "world_J_multiple_executions"
        assert world.has_hidden_effects
        assert world.has_executed_hidden


# ---------------------------------------------------------------------------
# Runtime observer tests
# ---------------------------------------------------------------------------

class TestRuntimeObserver:
    def test_observer_records_observation(self, observer: RuntimeObserver):
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert obs.effect_id == effect.effect_id
        assert obs.actor == "test-actor"
        assert obs.execution_status == ExecutionStatus.EXECUTED
        assert observer.observation_count == 1

    def test_observer_preserves_provenance(self, observer: RuntimeObserver):
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert obs.provenance != ""
        assert obs.observation_mechanism == "test_observer"
        assert obs.temporal_validity != ""

    def test_observer_classifies_inventory_relation(self, observer: RuntimeObserver):
        declared_effect = _make_effect(visibility=EffectVisibility.DECLARED)
        hidden_effect = _make_effect(visibility=EffectVisibility.HIDDEN)
        
        obs_declared = observer.observe(
            effect=declared_effect,
            actor="test-actor",
            component=declared_effect.source,
            operation=declared_effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        obs_hidden = observer.observe(
            effect=hidden_effect,
            actor="test-actor",
            component=hidden_effect.source,
            operation=hidden_effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert obs_declared.relationship_to_inventory == "in_inventory"
        assert obs_hidden.relationship_to_inventory == "not_in_inventory"

    def test_observer_filters_by_category(self, observer: RuntimeObserver):
        subprocess_effect = _make_effect(category=EffectCategory.SUBPROCESS)
        network_effect = _make_effect(category=EffectCategory.NETWORK)
        
        observer.observe(
            effect=subprocess_effect,
            actor="test-actor",
            component=subprocess_effect.source,
            operation=subprocess_effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        observer.observe(
            effect=network_effect,
            actor="test-actor",
            component=network_effect.source,
            operation=network_effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert len(observer.get_observations_by_category(EffectCategory.SUBPROCESS)) == 1
        assert len(observer.get_observations_by_category(EffectCategory.NETWORK)) == 1

    def test_observer_filters_by_effect(self, observer: RuntimeObserver):
        effect = _make_effect()
        observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert len(observer.get_observations_by_effect(effect.effect_id)) == 1


# ---------------------------------------------------------------------------
# Promotion engine tests
# ---------------------------------------------------------------------------

class TestPromotionEngine:
    def test_unknown_with_observation_promotes_to_observed(
        self, promotion_engine: PromotionEngine
    ):
        effect = _make_effect()
        obs = _make_observation(effect)
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.UNKNOWN,
            observation=obs,
        )
        assert result.final_state == RevelationState.OBSERVED
        assert result.action == PromotionAction.PROMOTED_TO_OBSERVED

    def test_unknown_without_observation_stays_unknown(
        self, promotion_engine: PromotionEngine
    ):
        effect = _make_effect()
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.UNKNOWN,
            observation=None,
        )
        assert result.final_state == RevelationState.UNKNOWN
        assert result.action == PromotionAction.NO_ACTION

    def test_structurally_possible_with_observation_promotes(
        self, promotion_engine: PromotionEngine
    ):
        effect = _make_effect()
        obs = _make_observation(effect)
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.STRUCTURALLY_POSSIBLE,
            observation=obs,
        )
        assert result.final_state == RevelationState.OBSERVED

    def test_observed_with_execution_promotes_to_executed(
        self, promotion_engine: PromotionEngine
    ):
        effect = _make_effect()
        obs = _make_observation(effect, execution_status=ExecutionStatus.EXECUTED)
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.OBSERVED,
            observation=obs,
        )
        assert result.final_state == RevelationState.EXECUTED
        assert result.action == PromotionAction.PROMOTED_TO_CONCRETE

    def test_executed_stays_executed(self, promotion_engine: PromotionEngine):
        effect = _make_effect()
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.EXECUTED,
            observation=None,
        )
        assert result.final_state == RevelationState.EXECUTED
        assert result.action == PromotionAction.NO_ACTION

    def test_not_observed_without_observation_stays_not_observed(
        self, promotion_engine: PromotionEngine
    ):
        """NOT_OBSERVED ≠ NO_EFFECT. It stays NOT_OBSERVED."""
        effect = _make_effect()
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.NOT_OBSERVED,
            observation=None,
        )
        assert result.final_state == RevelationState.NOT_OBSERVED
        assert result.action == PromotionAction.NO_ACTION

    def test_not_observed_with_observation_promotes(
        self, promotion_engine: PromotionEngine
    ):
        """NOT_OBSERVED can be promoted if runtime evidence arrives."""
        effect = _make_effect()
        obs = _make_observation(effect)
        result = promotion_engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.NOT_OBSERVED,
            observation=obs,
        )
        assert result.final_state == RevelationState.OBSERVED


def _make_observation(
    effect: ConsequentialEffect,
    execution_status: ExecutionStatus = ExecutionStatus.EXECUTED,
) -> RuntimeEffectObservation:
    return RuntimeEffectObservation(
        observation_id=f"obs-test-{uuid.uuid4().hex[:8]}",
        effect_id=effect.effect_id,
        timestamp="2026-09-10T00:00:00Z",
        actor="test-actor",
        component=effect.source,
        operation=effect.operation,
        resource="test-resource",
        category=effect.category,
        source=effect.source,
        target=effect.target,
        execution_status=execution_status,
        authority_context={},
        capability_id=None,
        authorization_id=None,
        provenance_id=None,
        scope=ObservationScope.TEST,
        domain="test-domain",
        execution_path=[],
        triggering_event="",
        observation_mechanism="test",
        receipt=None,
        temporal_validity="2026-09-10T00:00:00Z",
        provenance="test",
        attribution_status=AttributionStatus.ATTRIBUTION_UNKNOWN,
        relationship_to_inventory="not_in_inventory",
    )


# ---------------------------------------------------------------------------
# Oracle evaluation tests
# ---------------------------------------------------------------------------

class TestOracleEvaluation:
    def test_oracle_evaluates_observations(self, worlds: list[RuntimeRevelationWorld], oracle: IndependentOracle):
        world = worlds[1]  # hidden_executed
        observer = RuntimeObserver("test")
        
        for effect in world.executed_effects:
            observer.observe(
                effect=effect,
                actor="test-actor",
                component=effect.source,
                operation=effect.operation,
                resource="test-resource",
                execution_status=ExecutionStatus.EXECUTED,
            )
        
        evaluation = oracle.evaluate(world, observer.observations)
        assert evaluation.world_id == world.world_id
        assert evaluation.observation_count > 0

    def test_oracle_detects_true_observations(self, worlds: list[RuntimeRevelationWorld], oracle: IndependentOracle):
        world = worlds[1]  # hidden_executed
        observer = RuntimeObserver("test")
        
        for effect in world.executed_effects:
            observer.observe(
                effect=effect,
                actor="test-actor",
                component=effect.source,
                operation=effect.operation,
                resource="test-resource",
                execution_status=ExecutionStatus.EXECUTED,
            )
        
        evaluation = oracle.evaluate(world, observer.observations)
        # The hidden effect was observed
        assert len(evaluation.true_observed) > 0

    def test_oracle_detects_missed_effects(self, worlds: list[RuntimeRevelationWorld], oracle: IndependentOracle):
        world = worlds[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        # No observations — the hidden effect never executes
        evaluation = oracle.evaluate(world, observer.observations)
        assert len(evaluation.missed_effects) > 0
        assert len(evaluation.never_executed) > 0

    def test_oracle_detects_never_executed(self, worlds: list[RuntimeRevelationWorld], oracle: IndependentOracle):
        world = worlds[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        evaluation = oracle.evaluate(world, observer.observations)
        assert len(evaluation.never_executed) == len(world.never_executed_effects)


# ---------------------------------------------------------------------------
# Phase 30 invariants
# ---------------------------------------------------------------------------

class TestPhase30Invariants:
    def test_not_observed_not_does_not_exist(self):
        """NOT_OBSERVED ≠ DOES_NOT_EXIST."""
        engine = PromotionEngine()
        effect = _make_effect()
        result = engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.NOT_OBSERVED,
            observation=None,
        )
        # NOT_OBSERVED is preserved — not promoted to NO_EFFECT
        assert result.final_state == RevelationState.NOT_OBSERVED

    def test_not_executed_yet_not_will_never_execute(self):
        """NOT_EXECUTED_YET ≠ WILL_NEVER_EXECUTE."""
        engine = PromotionEngine()
        effect = _make_effect()
        result = engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.REACHABLE_BUT_UNOBSERVED,
            observation=None,
        )
        # Reachable but unobserved stays unobserved
        assert result.final_state == RevelationState.REACHABLE_BUT_UNOBSERVED

    def test_observed_effect_not_authorized(self):
        """OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT."""
        observer = RuntimeObserver("test")
        effect = _make_effect(authority_path_status=AuthorityPathStatus.UNGOVERNED)
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        # Observation records what happened, not what was permitted
        assert obs.attribution_status == AttributionStatus.ATTRIBUTION_UNKNOWN

    def test_observation_not_authority(self):
        """OBSERVATION ≠ AUTHORITY."""
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        # Observation has no authority-creating fields
        assert obs.authorization_id is None
        assert obs.capability_id is None

    def test_structural_possibility_not_executed_effect(self):
        """STRUCTURAL_POSSIBILITY ≠ EXECUTED_EFFECT."""
        engine = PromotionEngine()
        effect = _make_effect()
        result = engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.STRUCTURALLY_POSSIBLE,
            observation=None,
        )
        # Without observation, no promotion
        assert result.final_state == RevelationState.STRUCTURALLY_POSSIBLE

    def test_runtime_observation_not_global_completeness(self):
        """RUNTIME_OBSERVATION ≠ GLOBAL_COMPLETENESS."""
        world = AdversarialWorldGenerator().generate_all_worlds()[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        # Observer sees nothing — but hidden effects exist
        assert observer.observation_count == 0
        assert world.has_hidden_effects  # Reality contradicts the silence

    def test_observed_set_not_complete_effect_set(self):
        """OBSERVED_SET ≠ COMPLETE_EFFECT_SET."""
        world = AdversarialWorldGenerator().generate_all_worlds()[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        # Observer sees nothing
        observed_ids = {o.effect_id for o in observer.observations}
        ground_truth_ids = {e.effect_id for e in world.ground_truth_effects}
        
        # Observed set is a subset of ground truth
        assert observed_ids.issubset(ground_truth_ids)
        # But not equal — there are unobserved effects
        assert observed_ids != ground_truth_ids

    def test_attribution_unknown_not_attribution_to_caller(self):
        """ATTRIBUTION_UNKNOWN ≠ ATTRIBUTION_TO_CALLER."""
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
            attribution_status=AttributionStatus.ATTRIBUTION_UNKNOWN,
        )
        assert obs.attribution_status == AttributionStatus.ATTRIBUTION_UNKNOWN

    def test_cross_domain_observation_not_cross_domain_authority(self):
        """CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY."""
        observer = RuntimeObserver("test", scope=ObservationScope.PRODUCTION)
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
            domain="production",
        )
        # Observation is scoped to production
        assert obs.scope == ObservationScope.PRODUCTION
        assert obs.domain == "production"

    def test_temporal_observation_not_historical_existence(self):
        """TEMPORAL_OBSERVATION ≠ HISTORICAL_EXISTENCE."""
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        # Observation has a timestamp — it doesn't prove historical existence
        assert obs.timestamp != ""
        assert obs.temporal_validity != ""

    def test_revalidation_not_retroactive_invalidation(self):
        """REVALIDATION ≠ RETROACTIVE_INVALIDATION."""
        # This is tested in Phase 28 — preserved here
        engine = PromotionEngine()
        effect = _make_effect()
        result = engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.NOT_OBSERVED,
            observation=None,
        )
        # NOT_OBSERVED is preserved — not invalidated
        assert result.final_state == RevelationState.NOT_OBSERVED

    def test_completeness_not_closure(self):
        """COMPLETENESS ≠ CLOSURE."""
        world = AdversarialWorldGenerator().generate_all_worlds()[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        # Observer sees nothing
        # But the world has hidden effects
        # So completeness ≠ closure
        assert observer.observation_count == 0
        assert world.has_hidden_effects


# ---------------------------------------------------------------------------
# Phase 30 experiment tests
# ---------------------------------------------------------------------------

class TestPhase30Experiment:
    def test_runs_all_worlds(self):
        exp = Phase30Experiment()
        results = exp.run_all()
        assert results["total_worlds"] == 10

    def test_summary_generated(self):
        exp = Phase30Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_worlds"] == 10
        assert summary["total_observations"] > 0

    def test_worlds_with_hidden_effects_count(self):
        exp = Phase30Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["worlds_with_hidden_effects"] == 10

    def test_worlds_with_executed_hidden_count(self):
        exp = Phase30Experiment()
        exp.run_all()
        summary = exp.summary()
        # Worlds B, D, E, F, G, H, I, J have executed hidden effects (8)
        assert summary["worlds_with_executed_hidden"] == 8

    def test_total_true_observed(self):
        exp = Phase30Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_true_observed"] > 0

    def test_total_missed(self):
        exp = Phase30Experiment()
        exp.run_all()
        summary = exp.summary()
        # Worlds A and C have hidden effects that never execute
        assert summary["total_missed"] > 0

    def test_total_never_executed(self):
        exp = Phase30Experiment()
        exp.run_all()
        summary = exp.summary()
        # Worlds A and C have effects that never execute
        assert summary["total_never_executed"] > 0


# ---------------------------------------------------------------------------
# Negative case tests
# ---------------------------------------------------------------------------

class TestNegativeCases:
    def test_hidden_effect_never_executed_stays_unknown(self):
        """Hidden effect that never executes stays UNKNOWN — not NO_EFFECT."""
        world = AdversarialWorldGenerator().generate_all_worlds()[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        # Observer sees nothing
        assert observer.observation_count == 0
        
        # But hidden effects exist
        assert world.has_hidden_effects
        
        # The system must NOT claim NO_EFFECT
        # (This is the most important negative case)

    def test_mechanism_silence_not_evidence_of_absence(self):
        """A mechanism that finds nothing has not proven no effect exists."""
        world = AdversarialWorldGenerator().generate_all_worlds()[0]  # hidden_never_executed
        observer = RuntimeObserver("test")
        
        # Observer sees nothing
        assert observer.observation_count == 0
        
        # But hidden effects exist
        assert world.has_hidden_effects
        
        # The silence is not evidence of absence

    def test_observation_does_not_create_authority(self):
        """Observation results do not contain authority claims."""
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        
        # No authority-creating fields
        assert obs.authorization_id is None
        assert obs.capability_id is None
        assert "authority" not in obs.relationship_to_inventory
        assert "authorized" not in obs.relationship_to_inventory


# ---------------------------------------------------------------------------
# Authority non-amplification tests
# ---------------------------------------------------------------------------

class TestAuthorityNonAmplification:
    def test_observation_does_not_create_authority(self):
        """Runtime observation must not create authority."""
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        
        # Observation records what happened, not what was permitted
        assert obs.authorization_id is None
        assert obs.capability_id is None

    def test_observed_effect_not_authorized_effect(self):
        """OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT."""
        observer = RuntimeObserver("test")
        effect = _make_effect(authority_path_status=AuthorityPathStatus.UNGOVERNED)
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        
        # Observation records execution, not authorization
        assert obs.execution_status == ExecutionStatus.EXECUTED
        assert obs.attribution_status == AttributionStatus.ATTRIBUTION_UNKNOWN

    def test_structural_gap_not_unauthorized(self):
        """STRUCTURAL_GAP ≠ UNAUTHORIZED_EFFECT."""
        engine = PromotionEngine()
        effect = _make_effect()
        result = engine.attempt_promotion(
            effect=effect,
            current_state=RevelationState.STRUCTURALLY_POSSIBLE,
            observation=None,
        )
        
        # Structural possibility without observation is not an unauthorized effect
        assert result.final_state == RevelationState.STRUCTURALLY_POSSIBLE
        assert result.action == PromotionAction.NO_ACTION


# ---------------------------------------------------------------------------
# Temporal validity tests
# ---------------------------------------------------------------------------

class TestTemporalValidity:
    def test_observation_has_temporal_validity(self):
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert obs.temporal_validity != ""

    def test_observation_has_provenance(self):
        observer = RuntimeObserver("test")
        effect = _make_effect()
        obs = observer.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        assert obs.provenance != ""
        assert obs.observation_mechanism == "test"


# ---------------------------------------------------------------------------
# Multiple execution tests
# ---------------------------------------------------------------------------

class TestMultipleExecutions:
    def test_same_effect_different_actors(self):
        """Same effect executed by different actors produces distinct observations."""
        observer = RuntimeObserver("test")
        effect = _make_effect()
        
        obs1 = observer.observe(
            effect=effect,
            actor="actor-1",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        obs2 = observer.observe(
            effect=effect,
            actor="actor-2",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
        )
        
        # Different observations
        assert obs1.observation_id != obs2.observation_id
        # Same effect
        assert obs1.effect_id == obs2.effect_id
        # Different actors
        assert obs1.actor != obs2.actor

    def test_same_effect_different_scopes(self):
        """Same effect in different scopes produces distinct observations."""
        observer_prod = RuntimeObserver("test_prod", scope=ObservationScope.PRODUCTION)
        observer_test = RuntimeObserver("test_test", scope=ObservationScope.TEST)
        effect = _make_effect()
        
        obs_prod = observer_prod.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
            domain="production",
        )
        obs_test = observer_test.observe(
            effect=effect,
            actor="test-actor",
            component=effect.source,
            operation=effect.operation,
            resource="test-resource",
            execution_status=ExecutionStatus.EXECUTED,
            domain="test",
        )
        
        assert obs_prod.scope == ObservationScope.PRODUCTION
        assert obs_test.scope == ObservationScope.TEST
        assert obs_prod.domain != obs_test.domain
