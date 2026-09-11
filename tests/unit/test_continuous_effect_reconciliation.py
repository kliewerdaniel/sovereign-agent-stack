"""Tests for Phase 28: Continuous Effect Reconciliation."""

import pytest
from research.examples.sovereign_agent.continuous_effect_reconciliation import (
    AuthorityPathStatus,
    ChangeType,
    CompletenessClaim,
    CompletenessStatus,
    ConsequentialEffect,
    ContinuousEffectReconciler,
    EffectCategory,
    EffectInventory,
    EffectVisibility,
    InventoryDelta,
    Phase28Experiment,
    ReconciliationAction,
    SystemChange,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def reconciler() -> ContinuousEffectReconciler:
    return ContinuousEffectReconciler()


def _make_effect(
    category: EffectCategory = EffectCategory.SUBPROCESS,
    source: str = "src/sas/argopack.py",
    target: str = "subprocess.run",
    operation: str = "subprocess.execute",
    visibility: EffectVisibility = EffectVisibility.DECLARED,
    authority_path_status: AuthorityPathStatus = AuthorityPathStatus.GOVERNED,
    description: str = "",
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
    )


def _make_inventory(
    effects: tuple[ConsequentialEffect, ...] = (),
    commit_ref: str = "test",
    scope: str = "runtime",
) -> EffectInventory:
    return EffectInventory(
        inventory_id=f"inv-test-{uuid.uuid4().hex[:8]}",
        effects=effects,
        claimed_closure_rate=1.0,
        scope=scope,
        observation_method="test",
        generated_by="test",
        commit_ref=commit_ref,
    )


def _make_change(
    change_type: ChangeType = ChangeType.SOURCE_MODIFIED,
    source: str = "test.py",
    description: str = "test change",
    commit_ref: str = "test",
    introduces_effects: bool = False,
    removes_effects: bool = False,
    categories_affected: set[EffectCategory] | None = None,
) -> SystemChange:
    return SystemChange(
        change_id=f"change-test-{uuid.uuid4().hex[:8]}",
        change_type=change_type,
        source=source,
        description=description,
        commit_ref=commit_ref,
        timestamp="2026-09-10T00:00:00Z",
        introduces_effects=introduces_effects,
        removes_effects=removes_effects,
        categories_affected=categories_affected or set(),
    )


import uuid


# ---------------------------------------------------------------------------
# Baseline registration tests
# ---------------------------------------------------------------------------

class TestBaselineRegistration:
    def test_register_baseline_creates_current_claim(self, reconciler: ContinuousEffectReconciler):
        effects = (_make_effect(),)
        inventory = _make_inventory(effects, commit_ref="C1")
        claim = reconciler.register_baseline(inventory, "C1", "2026-09-10T00:00:00Z")
        assert claim.is_current
        assert claim.status == CompletenessStatus.COMPLETE_WITHIN_SCOPE
        assert reconciler.current_claim == claim

    def test_baseline_claim_has_correct_scope(self, reconciler: ContinuousEffectReconciler):
        effects = (_make_effect(),)
        inventory = _make_inventory(effects, commit_ref="C1", scope="runtime")
        claim = reconciler.register_baseline(inventory, "C1", "2026-09-10T00:00:00Z")
        assert claim.scope == "runtime"

    def test_baseline_claim_preserves_inventory(self, reconciler: ContinuousEffectReconciler):
        effects = (_make_effect(), _make_effect(category=EffectCategory.FILESYSTEM))
        inventory = _make_inventory(effects, commit_ref="C1")
        claim = reconciler.register_baseline(inventory, "C1", "2026-09-10T00:00:00Z")
        assert claim.inventory.size == 2


# ---------------------------------------------------------------------------
# Delta computation tests
# ---------------------------------------------------------------------------

class TestDeltaComputation:
    def test_no_changes(self, reconciler: ContinuousEffectReconciler):
        effects = (_make_effect(),)
        baseline = _make_inventory(effects, commit_ref="C1")
        current = _make_inventory(effects, commit_ref="C1")
        delta = reconciler.compute_delta(baseline, current)
        assert not delta.has_changes
        assert len(delta.added) == 0
        assert len(delta.removed) == 0

    def test_added_effects(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect()
        e2 = _make_effect(category=EffectCategory.FILESYSTEM)
        baseline = _make_inventory((e1,), commit_ref="C1")
        current = _make_inventory((e1, e2), commit_ref="C2")
        delta = reconciler.compute_delta(baseline, current)
        assert delta.has_changes
        assert len(delta.added) == 1
        assert delta.added[0].category == EffectCategory.FILESYSTEM

    def test_removed_effects(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect()
        e2 = _make_effect(category=EffectCategory.FILESYSTEM)
        baseline = _make_inventory((e1, e2), commit_ref="C1")
        current = _make_inventory((e1,), commit_ref="C2")
        delta = reconciler.compute_delta(baseline, current)
        assert delta.has_changes
        assert len(delta.removed) == 1
        assert delta.removed[0].category == EffectCategory.FILESYSTEM


# ---------------------------------------------------------------------------
# Reconciliation: no-change scenario
# ---------------------------------------------------------------------------

class TestNoChangeScenario:
    def test_no_change_returns_no_action(self, reconciler: ContinuousEffectReconciler):
        effects = (_make_effect(),)
        inventory = _make_inventory(effects, commit_ref="C1")
        reconciler.register_baseline(inventory, "C1", "2026-09-10T00:00:00Z")
        change = _make_change(introduces_effects=False, removes_effects=False)
        result = reconciler.reconcile_change(change, inventory)
        assert result.action == ReconciliationAction.NO_ACTION
        assert result.scope_impact == "unchanged"
        assert result.temporal_impact == "no_invalidation"

    def test_no_change_preserves_claim(self, reconciler: ContinuousEffectReconciler):
        effects = (_make_effect(),)
        inventory = _make_inventory(effects, commit_ref="C1")
        baseline_claim = reconciler.register_baseline(inventory, "C1", "2026-09-10T00:00:00Z")
        change = _make_change()
        result = reconciler.reconcile_change(change, inventory)
        assert result.prior_claim == baseline_claim
        assert reconciler.current_claim == baseline_claim


# ---------------------------------------------------------------------------
# Reconciliation: new category discovery
# ---------------------------------------------------------------------------

class TestNewCategoryDiscovery:
    def test_new_category_invalidates_completeness(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.action == ReconciliationAction.COMPLETENESS_INVALIDATED
        assert result.scope_impact == "new_category"

    def test_new_category_creates_new_claim(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.new_claim is not None
        assert result.new_claim.status == CompletenessStatus.INCOMPLETE

    def test_new_category_preserves_historical_claim(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        result = reconciler.reconcile_change(change, current_inv)
        # Historical claim is NOT retroactively invalidated
        assert result.historical_claim_preserved
        assert result.temporal_impact == "revalidation_required"


# ---------------------------------------------------------------------------
# Reconciliation: existing category extension
# ---------------------------------------------------------------------------

class TestExistingCategoryExtension:
    def test_new_effect_in_existing_category_extends_inventory(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.SUBPROCESS, source="src/sas/cli/helper.py")
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_MODIFIED,
            introduces_effects=True,
            categories_affected={EffectCategory.SUBPROCESS},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.action == ReconciliationAction.INVENTORY_EXTENDED
        assert result.scope_impact == "extended"

    def test_extended_inventory_requires_revalidation(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.SUBPROCESS, source="src/sas/cli/helper.py")
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_MODIFIED,
            introduces_effects=True,
            categories_affected={EffectCategory.SUBPROCESS},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.requires_revalidation


# ---------------------------------------------------------------------------
# Reconciliation: effect removal
# ---------------------------------------------------------------------------

class TestEffectRemoval:
    def test_effect_removal_narrows_scope(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        e2 = _make_effect(category=EffectCategory.FILESYSTEM)
        baseline_inv = _make_inventory((e1, e2), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        current_inv = _make_inventory((e1,), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_REMOVED,
            removes_effects=True,
            categories_affected={EffectCategory.FILESYSTEM},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.action == ReconciliationAction.SCOPE_NARROWED
        assert result.scope_impact == "narrowed"

    def test_effect_removal_does_not_require_revalidation(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        e2 = _make_effect(category=EffectCategory.FILESYSTEM)
        baseline_inv = _make_inventory((e1, e2), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        current_inv = _make_inventory((e1,), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_REMOVED,
            removes_effects=True,
            categories_affected={EffectCategory.FILESYSTEM},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert not result.requires_revalidation
        assert result.temporal_impact == "no_invalidation"


# ---------------------------------------------------------------------------
# Temporal validity chain
# ---------------------------------------------------------------------------

class TestTemporalValidityChain:
    def test_claim_chain_grows_with_changes(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        # First change
        e2 = _make_effect(category=EffectCategory.PAYMENT)
        inv_2 = _make_inventory((e1, e2), commit_ref="C2")
        change_1 = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        reconciler.reconcile_change(change_1, inv_2)

        # Second change
        e3 = _make_effect(category=EffectCategory.PLUGIN)
        inv_3 = _make_inventory((e1, e2, e3), commit_ref="C3")
        change_2 = _make_change(
            change_type=ChangeType.PLUGIN_REGISTERED,
            introduces_effects=True,
            categories_affected={EffectCategory.PLUGIN},
        )
        reconciler.reconcile_change(change_2, inv_3)

        claims = reconciler.claim_history
        assert len(claims) == 3  # baseline + 2 new

    def test_only_latest_claim_is_current(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        inv_2 = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        reconciler.reconcile_change(change, inv_2)

        current_claims = [c for c in reconciler.claim_history if c.is_current]
        assert len(current_claims) == 1

    def test_historical_claims_are_expired_not_invalidated(self, reconciler: ContinuousEffectReconciler):
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        inv_2 = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        reconciler.reconcile_change(change, inv_2)

        expired = [c for c in reconciler.claim_history if c.is_expired]
        assert len(expired) >= 1
        # Expired claims were valid for their time
        for c in expired:
            assert c.status in (
                CompletenessStatus.COMPLETE_WITHIN_SCOPE,
                CompletenessStatus.UNKNOWN,
            )


# ---------------------------------------------------------------------------
# Phase 28 invariants
# ---------------------------------------------------------------------------

class TestPhase28Invariants:
    def test_inventory_change_invalidates_only_within_changed_scope(self):
        """INVENTORY_CHANGE_INVALIDATES_COMPLETENESS_CLAIM_ONLY_WITHIN_CHANGED_SCOPE."""
        reconciler = ContinuousEffectReconciler()
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        # Add new category
        e2 = _make_effect(category=EffectCategory.PAYMENT)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        result = reconciler.reconcile_change(change, current_inv)

        # Completeness is invalidated for the new category
        assert result.action == ReconciliationAction.COMPLETENESS_INVALIDATED
        # But the historical claim is preserved
        assert result.historical_claim_preserved

    def test_revalidation_requirement_not_retroactive_invalidation(self):
        """REVALIDATION_REQUIREMENT ≠ RETROACTIVE_INVALIDATION."""
        reconciler = ContinuousEffectReconciler()
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        result = reconciler.reconcile_change(change, current_inv)

        # Revalidation is required
        assert result.requires_revalidation
        # But the prior claim is NOT retroactively invalidated
        assert result.temporal_impact != "retroactive_invalidation"
        assert result.historical_claim_preserved

    def test_completeness_claim_is_temporally_bounded(self):
        """COMPLETENESS_CLAIM_IS_TEMPORALLY_BOUNDED."""
        reconciler = ContinuousEffectReconciler()
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        claim = reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        # Claim is valid from registration
        assert claim.valid_from == "2026-09-10T00:00:00Z"
        # Claim is current (no expiry)
        assert claim.is_current

        # After a change, claim is expired
        e2 = _make_effect(category=EffectCategory.PAYMENT)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT},
        )
        reconciler.reconcile_change(change, current_inv)

        # The original claim should now be expired
        updated_claims = [c for c in reconciler.claim_history if c.claim_id == claim.claim_id]
        assert len(updated_claims) == 1
        assert updated_claims[0].is_expired

    def test_effect_discovery_triggers_revalidation(self):
        """EFFECT_DISCOVERY_TRIGGERS_REVALIDATION_WITHOUT_INVALIDATING_HISTORY."""
        reconciler = ContinuousEffectReconciler()
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        # Discover new effect
        e2 = _make_effect(category=EffectCategory.NETWORK)
        current_inv = _make_inventory((e1, e2), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.NETWORK},
        )
        result = reconciler.reconcile_change(change, current_inv)

        # Revalidation is triggered
        assert result.requires_revalidation
        # History is preserved
        assert result.historical_claim_preserved


# ---------------------------------------------------------------------------
# Phase 28 experiment tests
# ---------------------------------------------------------------------------

class TestPhase28Experiment:
    def test_runs_all_scenarios(self):
        exp = Phase28Experiment()
        results = exp.run_all()
        assert len(results) >= 5

    def test_baseline_registration(self):
        exp = Phase28Experiment()
        exp._run_baseline_registration()
        assert exp.reconciler.current_claim is not None
        assert exp.reconciler.current_claim.is_current

    def test_no_change_scenario(self):
        exp = Phase28Experiment()
        exp._run_baseline_registration()
        exp._run_no_change_scenario()
        results = [r for r in exp._results if r.action == ReconciliationAction.NO_ACTION]
        assert len(results) >= 1

    def test_new_category_scenario(self):
        exp = Phase28Experiment()
        exp._run_baseline_registration()
        exp._run_new_category_discovery()
        results = [r for r in exp._results if r.action == ReconciliationAction.COMPLETENESS_INVALIDATED]
        assert len(results) >= 1

    def test_temporal_validity_chain(self):
        exp = Phase28Experiment()
        exp.run_all()
        claims = exp.reconciler.claim_history
        # Should have multiple claims
        assert len(claims) >= 2
        # Only one current
        current = [c for c in claims if c.is_current]
        assert len(current) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_reconciliation_without_baseline(self):
        """Reconciliation without baseline registration."""
        reconciler = ContinuousEffectReconciler()
        effects = (_make_effect(),)
        inventory = _make_inventory(effects, commit_ref="C1")
        change = _make_change()
        result = reconciler.reconcile_change(change, inventory)
        assert result.action == ReconciliationAction.REVALIDATION_REQUIRED

    def test_multiple_categories_added_simultaneously(self):
        """Multiple new categories in one change."""
        reconciler = ContinuousEffectReconciler()
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        baseline_inv = _make_inventory((e1,), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        e2 = _make_effect(category=EffectCategory.PAYMENT)
        e3 = _make_effect(category=EffectCategory.PLUGIN)
        current_inv = _make_inventory((e1, e2, e3), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_ADDED,
            introduces_effects=True,
            categories_affected={EffectCategory.PAYMENT, EffectCategory.PLUGIN},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.action == ReconciliationAction.COMPLETENESS_INVALIDATED
        assert result.scope_impact == "new_category"

    def test_effect_removal_does_not_affect_other_categories(self):
        """Removing effects in one category doesn't affect other categories."""
        reconciler = ContinuousEffectReconciler()
        e1 = _make_effect(category=EffectCategory.SUBPROCESS)
        e2 = _make_effect(category=EffectCategory.FILESYSTEM)
        baseline_inv = _make_inventory((e1, e2), commit_ref="C1")
        reconciler.register_baseline(baseline_inv, "C1", "2026-09-10T00:00:00Z")

        # Remove filesystem effect
        current_inv = _make_inventory((e1,), commit_ref="C2")
        change = _make_change(
            change_type=ChangeType.SOURCE_REMOVED,
            removes_effects=True,
            categories_affected={EffectCategory.FILESYSTEM},
        )
        result = reconciler.reconcile_change(change, current_inv)
        assert result.action == ReconciliationAction.SCOPE_NARROWED
        # Subprocess category is unaffected
        assert result.scope_impact == "narrowed"
