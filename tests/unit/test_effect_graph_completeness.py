"""Phase 27: Consequential Effect Graph Completeness Tests.

Tests that the system can detect when a 100% closed declared inventory
does not imply global effect closure.

The critical invariant:
    100% CLOSURE OF AN INCOMPLETE EFFECT INVENTORY ≠ GLOBAL EFFECT CLOSURE
"""

from __future__ import annotations

import pytest

from research.examples.sovereign_agent.effect_graph_completeness import (
    AdversarialWorldGenerator,
    AuthorityPathStatus,
    CompletenessEngine,
    CompletenessResult,
    ConsequentialEffect,
    EffectCategory,
    EffectInventory,
    EffectVisibility,
    InventoryCompleteness,
    Phase27Experiment,
)


# ---------------------------------------------------------------------------
# Adversarial World Generator Tests
# ---------------------------------------------------------------------------


class TestAdversarialWorldGenerator:
    """Tests for the adversarial world generator."""

    def test_generates_all_worlds(self):
        """Phase 27 should generate 16 adversarial worlds."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        assert len(worlds) == 16

    def test_each_world_has_hidden_effects(self):
        """Every adversarial world must have at least one hidden effect."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        for world in worlds:
            assert world.hidden_count > 0, f"World {world.world_id} has no hidden effects"

    def test_each_world_has_ground_truth(self):
        """Ground truth must be the union of declared + hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        for world in worlds:
            assert world.ground_truth_count == world.declared_count + world.hidden_count

    def test_hidden_effects_not_in_declared(self):
        """Hidden effects must not overlap with declared effects."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        for world in worlds:
            declared_ids = {e.effect_id for e in world.declared_effects}
            hidden_ids = {e.effect_id for e in world.hidden_effects}
            assert not declared_ids & hidden_ids, f"World {world.world_id} has overlap"

    def test_worlds_cover_all_attack_categories(self):
        """Worlds should cover all 16 attack categories."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        categories = {w.attack_category for w in worlds}
        expected = {
            "direct_subprocess_bypass",
            "indirect_subprocess",
            "dynamic_import_subprocess",
            "filesystem_utility_bypass",
            "database_alternate_adapter",
            "credential_secondary_path",
            "identity_outside_adapter",
            "plugin_instantiated_effect",
            "argo_alternate_entry",
            "mcp_style_external",
            "exception_recovery_path",
            "emergency_path",
            "test_harness_effect",
            "lazy_init_side_effect",
            "background_worker",
            "callback_triggered",
        }
        assert categories == expected

    def test_subprocess_helper_world(self):
        """World 1: Direct subprocess helper should have 1 declared, 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_001_subprocess_helper")
        assert world.declared_count == 1
        assert world.hidden_count == 1
        assert world.hidden_effects[0].category == EffectCategory.SUBPROCESS
        assert world.hidden_effects[0].authority_path_status == AuthorityPathStatus.ESCAPE

    def test_indirect_subprocess_world(self):
        """World 2: Indirect subprocess should have 2 hidden effects."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_002_indirect_subprocess")
        assert world.hidden_count == 2
        categories = {e.category for e in world.hidden_effects}
        assert EffectCategory.SUBPROCESS in categories

    def test_dynamic_import_world(self):
        """World 3: Dynamic import should have hidden import + subprocess."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_003_dynamic_import")
        assert world.hidden_count == 2
        categories = {e.category for e in world.hidden_effects}
        assert EffectCategory.DYNAMIC_IMPORT in categories
        assert EffectCategory.SUBPROCESS in categories

    def test_filesystem_utility_world(self):
        """World 4: Filesystem utility should have pathlib + shutil hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_004_filesystem_utility")
        assert world.hidden_count == 2
        assert all(e.category == EffectCategory.FILESYSTEM for e in world.hidden_effects)

    def test_database_alternate_world(self):
        """World 5: Database alternate adapter should have 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_005_database_alternate")
        assert world.hidden_count == 1
        assert world.hidden_effects[0].category == EffectCategory.DATABASE

    def test_credential_secondary_world(self):
        """World 6: Credential secondary path should have 2 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_006_credential_secondary")
        assert world.hidden_count == 2
        assert all(e.category == EffectCategory.CREDENTIAL for e in world.hidden_effects)

    def test_identity_legacy_world(self):
        """World 7: Identity legacy should have 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_007_identity_legacy")
        assert world.hidden_count == 1
        assert world.hidden_effects[0].category == EffectCategory.IDENTITY

    def test_plugin_instantiated_world(self):
        """World 8: Plugin instantiated should have 2 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_008_plugin_instantiated")
        assert world.hidden_count == 2

    def test_argo_alternate_world(self):
        """World 9: ARGO alternate entry should have 1 hidden subprocess."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_009_argo_alternate")
        assert world.hidden_count == 1
        assert world.hidden_effects[0].category == EffectCategory.SUBPROCESS

    def test_mcp_external_world(self):
        """World 10: MCP external should have 2 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_010_mcp_external")
        assert world.hidden_count == 2

    def test_exception_recovery_world(self):
        """World 11: Exception recovery should have 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_011_exception_recovery")
        assert world.hidden_count == 1

    def test_emergency_path_world(self):
        """World 12: Emergency path should have 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_012_emergency_path")
        assert world.hidden_count == 1

    def test_test_harness_world(self):
        """World 13: Test harness should have 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_013_test_harness")
        assert world.hidden_count == 1

    def test_lazy_init_world(self):
        """World 14: Lazy init should have 1 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_014_lazy_init")
        assert world.hidden_count == 1

    def test_background_worker_world(self):
        """World 15: Background worker should have 2 hidden."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_015_background_worker")
        assert world.hidden_count == 2

    def test_callback_triggered_world(self):
        """World 16: Callback triggered should have 2 hidden (broker + payment)."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        world = next(w for w in worlds if w.world_id == "world_016_callback_triggered")
        assert world.hidden_count == 2


# ---------------------------------------------------------------------------
# Completeness Engine Tests
# ---------------------------------------------------------------------------


class TestCompletenessEngine:
    """Tests for the completeness engine."""

    def _make_effect(
        self,
        effect_id: str,
        category: EffectCategory,
        visibility: EffectVisibility,
        authority_status: AuthorityPathStatus,
    ) -> ConsequentialEffect:
        return ConsequentialEffect(
            effect_id=effect_id,
            category=category,
            source="test.py",
            target="test_target",
            operation="test_op",
            visibility=visibility,
            authority_path_status=authority_status,
            description="test effect",
            hidden_mechanism="test",
        )

    def _make_inventory(
        self,
        effects: list[ConsequentialEffect],
        claimed_closure: float = 1.0,
    ) -> EffectInventory:
        return EffectInventory(
            inventory_id="test-inv",
            effects=tuple(effects),
            claimed_closure_rate=claimed_closure,
            scope="test",
            observation_method="test",
            generated_by="test",
        )

    def test_complete_within_scope_no_hidden(self):
        """When no hidden effects exist, inventory is complete within scope."""
        engine = CompletenessEngine()
        effect = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        inv = self._make_inventory([effect])

        # Create a minimal world with no hidden effects
        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(effect,),
            hidden_effects=(),
            ground_truth_effects=(effect,),
            attack_category="none",
            expected_completeness=InventoryCompleteness.COMPLETE_WITHIN_SCOPE,
        )

        result = engine.evaluate(world, inv, inv, inv)
        assert result.completeness_classification == InventoryCompleteness.COMPLETE_WITHIN_SCOPE
        assert result.closure_claim_valid

    def test_false_closure_detected(self):
        """When hidden effects exist but none detected, it's false closure."""
        engine = CompletenessEngine()
        declared = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        hidden = self._make_effect("e2", EffectCategory.SUBPROCESS, EffectVisibility.HIDDEN, AuthorityPathStatus.ESCAPE)

        declared_inv = self._make_inventory([declared])
        ground_truth_inv = self._make_inventory([declared, hidden])

        # Observed inventory only has declared (misses hidden)
        observed_inv = self._make_inventory([declared])

        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(declared,),
            hidden_effects=(hidden,),
            ground_truth_effects=(declared, hidden),
            attack_category="test",
            expected_completeness=InventoryCompleteness.FALSE_CLOSURE,
        )

        result = engine.evaluate(world, declared_inv, observed_inv, ground_truth_inv)
        assert result.false_closure
        assert not result.closure_claim_valid
        assert result.completeness_classification == InventoryCompleteness.FALSE_CLOSURE
        assert len(result.detected_hidden) == 0
        assert len(result.missed_hidden) == 1

    def test_incomplete_when_some_detected(self):
        """When some but not all hidden effects detected, inventory is incomplete."""
        engine = CompletenessEngine()
        declared = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        hidden1 = self._make_effect("e2", EffectCategory.SUBPROCESS, EffectVisibility.HIDDEN, AuthorityPathStatus.ESCAPE)
        hidden2 = self._make_effect("e3", EffectCategory.FILESYSTEM, EffectVisibility.HIDDEN, AuthorityPathStatus.UNGOVERNED)

        declared_inv = self._make_inventory([declared])
        # Observed finds hidden1 but misses hidden2
        observed_inv = self._make_inventory([declared, hidden1])
        ground_truth_inv = self._make_inventory([declared, hidden1, hidden2])

        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(declared,),
            hidden_effects=(hidden1, hidden2),
            ground_truth_effects=(declared, hidden1, hidden2),
            attack_category="test",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

        result = engine.evaluate(world, declared_inv, observed_inv, ground_truth_inv)
        assert result.completeness_classification == InventoryCompleteness.INCOMPLETE
        assert len(result.detected_hidden) == 1
        assert len(result.missed_hidden) == 1
        assert not result.closure_claim_valid

    def test_detection_rate_perfect(self):
        """Detection rate is 1.0 when all hidden effects are found."""
        engine = CompletenessEngine()
        declared = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        hidden = self._make_effect("e2", EffectCategory.SUBPROCESS, EffectVisibility.HIDDEN, AuthorityPathStatus.ESCAPE)

        declared_inv = self._make_inventory([declared])
        observed_inv = self._make_inventory([declared, hidden])
        ground_truth_inv = self._make_inventory([declared, hidden])

        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(declared,),
            hidden_effects=(hidden,),
            ground_truth_effects=(declared, hidden),
            attack_category="test",
            expected_completeness=InventoryCompleteness.COMPLETE_WITHIN_SCOPE,
        )

        result = engine.evaluate(world, declared_inv, observed_inv, ground_truth_inv)
        assert result.detection_rate == 1.0
        assert result.closure_claim_valid

    def test_detection_rate_zero(self):
        """Detection rate is 0.0 when no hidden effects are found."""
        engine = CompletenessEngine()
        declared = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        hidden = self._make_effect("e2", EffectCategory.SUBPROCESS, EffectVisibility.HIDDEN, AuthorityPathStatus.ESCAPE)

        declared_inv = self._make_inventory([declared])
        observed_inv = self._make_inventory([declared])
        ground_truth_inv = self._make_inventory([declared, hidden])

        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(declared,),
            hidden_effects=(hidden,),
            ground_truth_effects=(declared, hidden),
            attack_category="test",
            expected_completeness=InventoryCompleteness.FALSE_CLOSURE,
        )

        result = engine.evaluate(world, declared_inv, observed_inv, ground_truth_inv)
        assert result.detection_rate == 0.0
        assert result.false_closure

    def test_false_positives_detected(self):
        """False positives are effects observed but not in ground truth."""
        engine = CompletenessEngine()
        declared = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        false_positive = self._make_effect("e_fp", EffectCategory.NETWORK, EffectVisibility.OBSERVED, AuthorityPathStatus.GOVERNED)

        declared_inv = self._make_inventory([declared])
        # Observed has a false positive
        observed_inv = self._make_inventory([declared, false_positive])
        ground_truth_inv = self._make_inventory([declared])

        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(declared,),
            hidden_effects=(),
            ground_truth_effects=(declared,),
            attack_category="test",
            expected_completeness=InventoryCompleteness.COMPLETE_WITHIN_SCOPE,
        )

        result = engine.evaluate(world, declared_inv, observed_inv, ground_truth_inv)
        assert len(result.false_positives) == 1
        assert result.false_positives[0].effect_id == "e_fp"


# ---------------------------------------------------------------------------
# Phase 27 Experiment Tests
# ---------------------------------------------------------------------------


class TestPhase27Experiment:
    """Tests for the full Phase 27 experiment."""

    def test_runs_all_worlds(self):
        """Phase 27 should run all 16 adversarial worlds."""
        exp = Phase27Experiment()
        results = exp.run_all()
        assert len(results) == 16

    def test_all_results_have_worlds(self):
        """Every result should reference its world."""
        exp = Phase27Experiment()
        results = exp.run_all()
        for r in results:
            assert r.world is not None
            assert r.world.world_id

    def test_all_worlds_have_hidden_effects(self):
        """All worlds should have at least one hidden effect."""
        exp = Phase27Experiment()
        results = exp.run_all()
        for r in results:
            assert r.world.hidden_count > 0

    def test_false_closure_detected_in_all_worlds(self):
        """Since all worlds have hidden effects, all should show false closure
        when the declared inventory claims 100% closure but misses hidden effects."""
        exp = Phase27Experiment()
        results = exp.run_all()
        for r in results:
            # The declared inventory claims 100% closure
            assert r.declared_inventory.claimed_closure_rate == 1.0
            # But hidden effects exist
            assert len(r.world.hidden_effects) > 0
            # And the observed inventory (which includes hidden) shows the discrepancy
            assert r.observed_inventory.size > r.declared_inventory.size

    def test_summary_generated(self):
        """Summary should be generated with correct counts."""
        exp = Phase27Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_worlds"] == 16
        assert "false_closures" in summary
        assert "average_detection_rate" in summary

    def test_observed_inventory_larger_than_declared(self):
        """Observed inventory should always be >= declared inventory."""
        exp = Phase27Experiment()
        results = exp.run_all()
        for r in results:
            assert r.observed_inventory.size >= r.declared_inventory.size

    def test_ground_truth_matches_union(self):
        """Ground truth should equal declared + hidden."""
        exp = Phase27Experiment()
        results = exp.run_all()
        for r in results:
            assert r.ground_truth.size == r.declared_inventory.size + r.world.hidden_count


# ---------------------------------------------------------------------------
# Invariant Tests
# ---------------------------------------------------------------------------


class TestPhase27Invariants:
    """Tests for the critical Phase 27 invariants."""

    def test_incomplete_inventory_closure_claim_invalid(self):
        """100% closure of an incomplete inventory is NOT global closure.

        The declared inventory can have 100% actual closure (all its own
        effects are governed) while missing hidden effects that exist in
        the ground truth. This is the false closure problem.
        """
        exp = Phase27Experiment()
        results = exp.run_all()
        for r in results:
            if r.world.hidden_count > 0:
                # The declared inventory claims 100% closure
                assert r.declared_inventory.claimed_closure_rate == 1.0
                # The declared inventory's own effects are all governed
                # (its actual_closure_rate == 1.0 by construction)
                # BUT: the ground truth has additional effects
                assert r.ground_truth.size > r.declared_inventory.size
                # Therefore: the declared inventory is incomplete.
                # Its 100% closure does NOT imply global closure.
                # The system must refuse to interpret this as global closure.
                assert r.declared_inventory.size < r.ground_truth.size
                # The number of hidden effects that exist outside the inventory
                assert len(r.world.hidden_effects) > 0

    def test_hidden_effects_are_ungoverned_or_escape(self):
        """Hidden effects should be ungoverned or escapes."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        for world in worlds:
            for effect in world.hidden_effects:
                assert effect.authority_path_status in (
                    AuthorityPathStatus.UNGOVERNED,
                    AuthorityPathStatus.ESCAPE,
                ), f"Hidden effect {effect.effect_id} in {world.world_id} is {effect.authority_path_status}"

    def test_declared_effects_are_governed(self):
        """Declared effects should be governed."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        for world in worlds:
            for effect in world.declared_effects:
                assert effect.authority_path_status == AuthorityPathStatus.GOVERNED

    def test_false_closure_definition(self):
        """False closure = claimed 100% + hidden exist + none detected."""
        engine = CompletenessEngine()
        declared = self._make_effect("e1", EffectCategory.SUBPROCESS, EffectVisibility.DECLARED, AuthorityPathStatus.GOVERNED)
        hidden = self._make_effect("e2", EffectCategory.SUBPROCESS, EffectVisibility.HIDDEN, AuthorityPathStatus.ESCAPE)

        declared_inv = EffectInventory(
            inventory_id="test",
            effects=(declared,),
            claimed_closure_rate=1.0,
            scope="test",
            observation_method="test",
            generated_by="test",
        )
        # Observed misses the hidden effect
        observed_inv = EffectInventory(
            inventory_id="test",
            effects=(declared,),
            claimed_closure_rate=1.0,
            scope="test",
            observation_method="test",
            generated_by="test",
        )
        ground_truth_inv = EffectInventory(
            inventory_id="test",
            effects=(declared, hidden),
            claimed_closure_rate=1.0,
            scope="test",
            observation_method="test",
            generated_by="test",
        )

        from research.examples.sovereign_agent.effect_graph_completeness import AdversarialWorld
        world = AdversarialWorld(
            world_id="test",
            description="test",
            declared_effects=(declared,),
            hidden_effects=(hidden,),
            ground_truth_effects=(declared, hidden),
            attack_category="test",
            expected_completeness=InventoryCompleteness.FALSE_CLOSURE,
        )

        result = engine.evaluate(world, declared_inv, observed_inv, ground_truth_inv)
        assert result.false_closure
        assert not result.closure_claim_valid

    def _make_effect(self, effect_id, category, visibility, authority_status):
        return ConsequentialEffect(
            effect_id=effect_id,
            category=category,
            source="test.py",
            target="test_target",
            operation="test_op",
            visibility=visibility,
            authority_path_status=authority_status,
            description="test",
            hidden_mechanism="test",
        )


# ---------------------------------------------------------------------------
# Effect Category Coverage Tests
# ---------------------------------------------------------------------------


class TestEffectCategoryCoverage:
    """Tests that all effect categories are covered by hidden effects."""

    def test_all_categories_have_hidden_effects(self):
        """Every effect category should appear as a hidden effect in some world."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        hidden_categories = set()
        for world in worlds:
            for effect in world.hidden_effects:
                hidden_categories.add(effect.category)
        # All categories should be represented
        all_categories = set(EffectCategory)
        assert hidden_categories == all_categories

    def test_subprocess_hidden_in_multiple_worlds(self):
        """Subprocess should be hidden in multiple worlds."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        subprocess_worlds = [
            w for w in worlds
            if any(e.category == EffectCategory.SUBPROCESS for e in w.hidden_effects)
        ]
        assert len(subprocess_worlds) >= 3

    def test_filesystem_hidden_in_multiple_worlds(self):
        """Filesystem should be hidden in multiple worlds."""
        gen = AdversarialWorldGenerator()
        worlds = gen.generate_all_worlds()
        filesystem_worlds = [
            w for w in worlds
            if any(e.category == EffectCategory.FILESYSTEM for e in w.hidden_effects)
        ]
        assert len(filesystem_worlds) >= 2
