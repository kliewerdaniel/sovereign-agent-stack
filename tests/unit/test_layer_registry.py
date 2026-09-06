# ── Layer Registry Unit Tests ──────────────────────────────────────────────────

import pytest

from sas.core.config import (
    AuthBroker,
    LongTermProvider,
    MemoryProvider,
    ModelConfig,
    SASConfig,
    SubstrateType,
)
from sas.layers import LayerRegistry
from sas.layers.registry import LayerID


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sovereign_config(tmp_path) -> SASConfig:
    """A fully-owned config (local model, local docker, local RAG, etc.)."""
    cfg = SASConfig()
    cfg.model_primary = ModelConfig(
        provider="ollama", name="llama3.1:8b", location="local"
    )
    cfg.substrate = SubstrateType.LOCAL_DOCKER
    cfg.memory_short_term = MemoryProvider.LOCAL_RAG
    cfg.memory_long_term = LongTermProvider.COMPILE_TIME_GRAPH
    cfg.auth_broker = AuthBroker.LOCAL_MCP_GATEWAY
    return cfg


@pytest.fixture
def rented_config(tmp_path) -> SASConfig:
    """A fully-rented config (API model, orgo cloud, composio, etc.)."""
    cfg = SASConfig()
    cfg.model_primary = ModelConfig(
        provider="openai", name="gpt-4o", location="api"
    )
    cfg.substrate = SubstrateType.ORGO_CLOUD
    cfg.memory_short_term = MemoryProvider.HONCHO_CLOUD
    cfg.memory_long_term = LongTermProvider.RETRIEVAL_ONLY
    cfg.auth_broker = AuthBroker.COMPOSIO
    return cfg


@pytest.fixture
def registry(sovereign_config) -> LayerRegistry:
    return LayerRegistry(sovereign_config)


# ── Construction ───────────────────────────────────────────────────────────────

class TestLayerRegistryConstruction:
    def test_default_config_none(self):
        r = LayerRegistry()
        assert r.config is None
        assert r.list_layers() == [
            LayerID.MODEL,
            LayerID.HARNESS,
            LayerID.COMPUTE,
            LayerID.IDENTITY,
            LayerID.SHORT_TERM_MEMORY,
            LayerID.LONG_TERM_KNOWLEDGE,
            LayerID.AUTH,
            LayerID.PAYMENTS,
        ]

    def test_config_set_on_init(self, sovereign_config):
        r = LayerRegistry(sovereign_config)
        assert r.config is sovereign_config

    def test_config_setter(self, registry, rented_config):
        registry.config = rented_config
        assert registry.config is rented_config


# ── Layer List ─────────────────────────────────────────────────────────────────

class TestLayerList:
    def test_all_eight_layers(self, registry):
        ids = registry.list_layers()
        assert len(ids) == 8
        assert set(ids) == set(LayerID)

    def test_scored_excludes_unavoidable(self, registry):
        scored = registry.list_layers(scored=True)
        ids = [lid.value for lid in scored]
        assert "layer_4_identity" not in ids
        assert "layer_8_payments" not in ids
        assert len(scored) == 6

    def test_scored_includes_six(self, registry):
        scored = registry.list_layers(scored=True)
        assert len(scored) == 6


# ── Layer Lookup ───────────────────────────────────────────────────────────────

class TestLayerLookup:
    def test_enum_passed_through(self, registry):
        lid = registry.get_layer(LayerID.MODEL)
        assert lid is LayerID.MODEL

    def test_full_value(self, registry):
        lid = registry.get_layer("layer_1_model")
        assert lid is LayerID.MODEL

    def test_short_layer_prefix(self, registry):
        lid = registry.get_layer("layer_5")
        assert lid is LayerID.SHORT_TERM_MEMORY

    def test_numeric_suffix(self, registry):
        lid = registry.get_layer("3")
        assert lid is LayerID.COMPUTE

    def test_all_layers_by_numeric(self, registry):
        expected = {
            "1": LayerID.MODEL,
            "2": LayerID.HARNESS,
            "3": LayerID.COMPUTE,
            "4": LayerID.IDENTITY,
            "5": LayerID.SHORT_TERM_MEMORY,
            "6": LayerID.LONG_TERM_KNOWLEDGE,
            "7": LayerID.AUTH,
            "8": LayerID.PAYMENTS,
        }
        for num, lid in expected.items():
            assert registry.get_layer(num) is lid

    def test_unknown_layer_raises(self, registry):
        with pytest.raises(KeyError, match="Unknown layer"):
            registry.get_layer("bogus")
        with pytest.raises(KeyError, match="Unknown layer"):
            registry.get_layer("9")
        with pytest.raises(KeyError, match="Unknown layer"):
            registry.get_layer("layer_99_foo")


# ── Ownership Queries ──────────────────────────────────────────────────────────

class TestOwnershipQueries:
    def test_all_owned_with_sovereign_config(self, registry):
        for lid in LayerID:
            if lid in (LayerID.IDENTITY, LayerID.PAYMENTS):
                assert registry.is_owned(lid) is False  # unavoidable rentals
            else:
                assert registry.is_owned(lid) is True

    def test_model_owned_by_short_key(self, registry):
        assert registry.is_owned("layer_1") is True
        assert registry.is_owned("1") is True

    def test_identity_not_owned(self, registry):
        assert registry.is_owned(LayerID.IDENTITY) is False
        assert registry.is_owned("layer_4") is False

    def test_payments_not_owned(self, registry):
        assert registry.is_owned(LayerID.PAYMENTS) is False
        assert registry.is_owned("8") is False

    def test_rented_config_all_rented(self, rented_config):
        r = LayerRegistry(rented_config)
        for lid in (LayerID.MODEL, LayerID.COMPUTE,
                    LayerID.SHORT_TERM_MEMORY, LayerID.LONG_TERM_KNOWLEDGE,
                    LayerID.AUTH):
            assert r.is_owned(lid) is False
        # harness is always owned (hardcoded in scorer)
        assert r.is_owned(LayerID.HARNESS) is True

    def test_is_owned_without_config_returns_false(self):
        r = LayerRegistry()  # no config
        assert r.is_owned(LayerID.MODEL) is False


# ── Unavoidable Rental Detection ───────────────────────────────────────────────

class TestUnavoidableRental:
    def test_identity_unavoidable(self, registry):
        assert registry.is_unavoidable_rental(LayerID.IDENTITY) is True
        assert registry.is_unavoidable_rental("layer_4") is True
        assert registry.is_unavoidable_rental("4") is True

    def test_payments_unavoidable(self, registry):
        assert registry.is_unavoidable_rental(LayerID.PAYMENTS) is True
        assert registry.is_unavoidable_rental("layer_8") is True
        assert registry.is_unavoidable_rental("8") is True

    def test_model_not_unavoidable(self, registry):
        assert registry.is_unavoidable_rental(LayerID.MODEL) is False

    def test_all_unavoidable(self, registry):
        unavoidable = [lid for lid in LayerID if registry.is_unavoidable_rental(lid)]
        assert set(unavoidable) == {LayerID.IDENTITY, LayerID.PAYMENTS}


# ── Sovereignty Score ──────────────────────────────────────────────────────────

class TestSovereigntyScore:
    def test_sovereign_config_scores_full(self, registry):
        owned, total, score = registry.sovereignty_score()
        assert owned == 6
        assert total == 6
        assert score == 1.0

    def test_rented_config_scores_low(self, rented_config):
        r = LayerRegistry(rented_config)
        owned, total, score = r.sovereignty_score()
        # harness owned, rest rented; 6 scorable layers, 1 owned
        assert owned == 1
        assert total == 6
        assert score == pytest.approx(1 / 6)

    def test_no_config_returns_zero(self):
        r = LayerRegistry()
        assert r.sovereignty_score() == (0, 0, 0.0)

    def test_score_via_short_key(self, registry):
        owned, total, score = registry.sovereignty_score()
        assert owned == 6
        assert total == 6


# ── Sync with scorer ───────────────────────────────────────────────────────────

class TestSyncWithScorer:
    """Ensure the registry's score matches sas.core.scoring.score_config."""

    def test_registry_layers_match_score_config_layers(self, sovereign_config):
        from sas.core.scoring import score_config

        r = LayerRegistry(sovereign_config)
        registry_ids = {lid.value for lid in r.list_layers()}
        all_scored_ids = {l.layer_id.value for l in score_config(sovereign_config)}

        assert registry_ids == {
            "layer_1_model",
            "layer_2_harness",
            "layer_3_compute",
            "layer_4_identity",
            "layer_5_short_term_memory",
            "layer_6_long_term_knowledge",
            "layer_7_auth",
            "layer_8_payments",
        }
        # Registry's full layer list includes all 8; scorer also returns all 8
        assert registry_ids == all_scored_ids

        # Registry's scored list (6) excludes identity + payments —
        # but scorer returns all 8 regardless (ownership decides scorable)
        scored_from_registry = {lid.value for lid in r.list_layers(scored=True)}
        assert "layer_4_identity" not in scored_from_registry
        assert "layer_8_payments" not in scored_from_registry
        assert len(scored_from_registry) == 6

    def test_registry_score_matches_direct_score(self, sovereign_config):
        from sas.core.scoring import compute_score, score_config

        r = LayerRegistry(sovereign_config)
        owned_r, total_r, score_r = r.sovereignty_score()

        layers = score_config(sovereign_config)
        owned_s, total_s, score_s = compute_score(layers)

        assert owned_r == owned_s
        assert total_r == total_s
        assert score_r == score_s




# ── Edge Cases ─────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_none_config_sovereignty_score(self):
        r = LayerRegistry(config=None)
        assert r.sovereignty_score() == (0, 0, 0.0)

    def test_is_owned_with_explicit_none_config_uses_instance(self, registry):
        # registry has a sovereign config; passing None falls back to it
        assert registry.is_owned(LayerID.MODEL, config=None) is True

    def test_is_owned_with_no_config_returns_false(self):
        r = LayerRegistry()  # no config
        assert r.is_owned(LayerID.MODEL, config=None) is False

    def test_get_layer_accepts_enum(self, registry):
        assert registry.get_layer(LayerID.AUTH) is LayerID.AUTH

    def test_list_layers_returns_new_list(self, registry):
        a = registry.list_layers()
        b = registry.list_layers()
        assert a is not b
        a.append(LayerID.MODEL)  # mutability check
        assert len(b) == 8
