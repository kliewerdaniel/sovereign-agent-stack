"""Phase 25 tests: Consequential Effect Closure.

Tests verify that the effect inventory correctly identifies and classifies
all externally consequential operations in the codebase.
"""

import pytest
from examples.sovereign_agent.consequential_effect_closure import (
    ConsequentialEffectClosureEngine,
    EffectGovernance,
    EffectInventory,
    EffectInventoryBuilder,
    EffectSeverity,
    EffectType,
    run_all_phase25_experiments,
)


class TestEffectInventory:
    """Test effect inventory."""

    def test_build_inventory(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        assert len(inventory.entries) > 0

    def test_get_by_type(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        subprocess_effects = inventory.get_by_type(EffectType.SUBPROCESS)
        assert len(subprocess_effects) > 0

    def test_get_by_governance(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        governed = inventory.get_by_governance(EffectGovernance.GOVERNED)
        assert len(governed) > 0

    def test_get_open_effects(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        open_effects = inventory.get_open_effects()
        assert len(open_effects) > 0

    def test_get_closed_effects(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        closed_effects = inventory.get_closed_effects()
        assert len(closed_effects) > 0

    def test_get_summary(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        summary = inventory.get_summary()
        assert summary["total"] > 0
        assert summary["governed"] > 0
        assert summary["unguarded"] > 0


class TestSubprocessEffects:
    """Test subprocess effects."""

    def test_subprocess_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.SUBPROCESS)
        assert len(effects) >= 2

    def test_subprocess_severity(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.SUBPROCESS)
        assert any(e.severity == EffectSeverity.CRITICAL for e in effects)

    def test_subprocess_governance(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.SUBPROCESS)
        assert any(e.governance_status == EffectGovernance.UNGUARDED for e in effects)


class TestHttpEffects:
    """Test HTTP effects."""

    def test_http_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.HTTP)
        assert len(effects) > 0

    def test_http_governed(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.HTTP)
        assert any(e.governance_status == EffectGovernance.GOVERNED for e in effects)


class TestFilesystemEffects:
    """Test filesystem effects."""

    def test_filesystem_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.FILESYSTEM)
        assert len(effects) > 0

    def test_filesystem_partially_governed(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.FILESYSTEM)
        assert any(e.governance_status == EffectGovernance.PARTIALLY_GOVERNED for e in effects)


class TestDatabaseEffects:
    """Test database effects."""

    def test_database_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.DATABASE)
        assert len(effects) > 0


class TestBrokerEffects:
    """Test broker effects."""

    def test_broker_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.BROKER)
        assert len(effects) > 0

    def test_broker_governed(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.BROKER)
        assert any(e.governance_status == EffectGovernance.GOVERNED for e in effects)


class TestPaymentEffects:
    """Test payment effects."""

    def test_payment_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.PAYMENT)
        assert len(effects) > 0

    def test_payment_governed(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.PAYMENT)
        assert any(e.governance_status == EffectGovernance.GOVERNED for e in effects)


class TestIdentityEffects:
    """Test identity effects."""

    def test_identity_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.IDENTITY)
        assert len(effects) > 0

    def test_identity_unguarded(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.IDENTITY)
        assert any(e.governance_status == EffectGovernance.UNGUARDED for e in effects)


class TestCredentialEffects:
    """Test credential effects."""

    def test_credential_effects_exist(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.CREDENTIAL)
        assert len(effects) > 0

    def test_credential_governed(self):
        builder = EffectInventoryBuilder()
        inventory = builder.build_inventory()
        effects = inventory.get_by_type(EffectType.CREDENTIAL)
        assert any(e.governance_status == EffectGovernance.GOVERNED for e in effects)


class TestAllPhase25Experiments:
    """Test all Phase 25 experiments."""

    def test_all_experiments_run(self):
        results = run_all_phase25_experiments()
        assert len(results["experiments"]) == 8

    def test_summary(self):
        results = run_all_phase25_experiments()
        assert results["summary"]["total"] > 0

    def test_closure_rate(self):
        results = run_all_phase25_experiments()
        assert 0 <= results["closure_rate"] <= 1

    def test_open_effects_identified(self):
        results = run_all_phase25_experiments()
        assert len(results["open_effects"]) > 0

    def test_closed_effects_identified(self):
        results = run_all_phase25_experiments()
        assert len(results["closed_effects"]) > 0

    def test_subprocess_open(self):
        results = run_all_phase25_experiments()
        assert results["experiments"]["subprocess"]["open"] > 0

    def test_broker_closed(self):
        results = run_all_phase25_experiments()
        assert results["experiments"]["broker"]["closed"] > 0

    def test_payment_closed(self):
        results = run_all_phase25_experiments()
        assert results["experiments"]["payment"]["closed"] > 0

    def test_credential_closed(self):
        results = run_all_phase25_experiments()
        assert results["experiments"]["credential"]["closed"] > 0


class TestConsequentialEffectClosureEngine:
    """Test consequential effect closure engine."""

    def test_build_inventory(self):
        engine = ConsequentialEffectClosureEngine()
        inventory = engine.build_inventory()
        assert len(inventory.entries) > 0

    def test_check_closure(self):
        engine = ConsequentialEffectClosureEngine()
        engine.build_inventory()
        result = engine.check_closure()
        assert "summary" in result
        assert "open_effects" in result
        assert "closed_effects" in result
        assert "closure_rate" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
