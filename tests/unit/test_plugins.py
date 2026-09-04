"""Tests for the plugin system."""

from __future__ import annotations

import pytest

from sas.plugins import (
    LayerPlugin,
    PluginRegistry,
    PluginSource,
    discover_plugins,
    get_plugin,
    list_plugins,
    register_plugin,
    unregister_plugin,
)


class TestPluginRegistry:
    """Tests for the plugin registry."""

    def setup_method(self) -> None:
        """Reset registry before each test."""
        PluginRegistry.reset()

    def teardown_method(self) -> None:
        """Reset registry after each test."""
        PluginRegistry.reset()

    def test_register_plugin(self) -> None:
        """Registering a plugin makes it available."""
        plugin = LayerPlugin(
            name="test-payment-adapter",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Test payment adapter",
            source=PluginSource.LOCAL,
        )
        register_plugin(plugin)

        assert get_plugin("layer_8_payments") == plugin

    def test_unregister_plugin(self) -> None:
        """Unregistering a plugin removes it."""
        plugin = LayerPlugin(
            name="test-payment-adapter",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Test payment adapter",
            source=PluginSource.LOCAL,
        )
        register_plugin(plugin)
        unregister_plugin("layer_8_payments")

        assert get_plugin("layer_8_payments") is None

    def test_list_plugins(self) -> None:
        """List all registered plugins."""
        p1 = LayerPlugin(
            name="adapter-a",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Payment adapter",
            source=PluginSource.LOCAL,
        )
        p2 = LayerPlugin(
            name="adapter-b",
            layer_id="layer_7_auth",
            version="0.1.0",
            description="Auth adapter",
            source=PluginSource.LOCAL,
        )
        register_plugin(p1)
        register_plugin(p2)

        plugins = list_plugins()
        assert len(plugins) == 2

    def test_list_plugins_by_layer(self) -> None:
        """Filter plugins by layer."""
        p1 = LayerPlugin(
            name="payment-adapter",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Payment adapter",
            source=PluginSource.LOCAL,
        )
        p2 = LayerPlugin(
            name="auth-adapter",
            layer_id="layer_7_auth",
            version="0.1.0",
            description="Auth adapter",
            source=PluginSource.LOCAL,
        )
        register_plugin(p1)
        register_plugin(p2)

        payment_plugins = list_plugins(layer_id="layer_8_payments")
        assert len(payment_plugins) == 1
        assert payment_plugins[0].name == "payment-adapter"

    def test_override_builtin_with_pip(self) -> None:
        """PIP-installed plugins override built-in plugins."""
        builtin = LayerPlugin(
            name="builtin-payments",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Built-in payment adapter",
            source=PluginSource.BUILTIN,
        )
        pip_plugin = LayerPlugin(
            name="better-payments",
            layer_id="layer_8_payments",
            version="0.2.0",
            description="Better payment adapter",
            source=PluginSource.PIP,
        )

        register_plugin(builtin)
        register_plugin(pip_plugin)

        # PIP plugin should override builtin
        active = get_plugin("layer_8_payments")
        assert active is not None
        assert active.name == "better-payments"

    def test_builtin_does_not_override_pip(self) -> None:
        """Built-in plugins do not override already-registered PIP plugins."""
        pip_plugin = LayerPlugin(
            name="better-payments",
            layer_id="layer_8_payments",
            version="0.2.0",
            description="Better payment adapter",
            source=PluginSource.PIP,
        )
        builtin = LayerPlugin(
            name="builtin-payments",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Built-in payment adapter",
            source=PluginSource.BUILTIN,
        )

        register_plugin(pip_plugin)
        register_plugin(builtin)

        active = get_plugin("layer_8_payments")
        assert active is not None
        assert active.name == "better-payments"

    def test_local_overrides_all(self) -> None:
        """Local plugins override both PIP and built-in."""
        builtin = LayerPlugin(
            name="builtin-payments",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Built-in payment adapter",
            source=PluginSource.BUILTIN,
        )
        pip_plugin = LayerPlugin(
            name="pip-payments",
            layer_id="layer_8_payments",
            version="0.2.0",
            description="PIP payment adapter",
            source=PluginSource.PIP,
        )
        local = LayerPlugin(
            name="local-payments",
            layer_id="layer_8_payments",
            version="0.3.0",
            description="Local payment adapter",
            source=PluginSource.LOCAL,
        )

        register_plugin(builtin)
        register_plugin(pip_plugin)
        register_plugin(local)

        active = get_plugin("layer_8_payments")
        assert active is not None
        assert active.name == "local-payments"

    def test_duplicate_name_different_layers(self) -> None:
        """Same plugin name can register for different layers."""
        p1 = LayerPlugin(
            name="universal-adapter",
            layer_id="layer_7_auth",
            version="0.1.0",
            description="Auth adapter",
            source=PluginSource.LOCAL,
        )
        p2 = LayerPlugin(
            name="universal-adapter",
            layer_id="layer_8_payments",
            version="0.1.0",
            description="Payment adapter",
            source=PluginSource.LOCAL,
        )

        register_plugin(p1)
        register_plugin(p2)

        assert get_plugin("layer_7_auth") == p1
        assert get_plugin("layer_8_payments") == p2


class TestDiscoverPlugins:
    """Tests for plugin discovery."""

    def test_discover_builtins(self) -> None:
        """Discover built-in plugins."""
        plugins = discover_plugins()
        # At least the built-in layers should be discoverable
        assert isinstance(plugins, list)


class TestLayerPlugin:
    """Tests for the LayerPlugin dataclass."""

    def test_plugin_attributes(self) -> None:
        """Plugin has expected attributes."""
        plugin = LayerPlugin(
            name="test-adapter",
            layer_id="layer_8_payments",
            version="1.0.0",
            description="Test adapter",
            source=PluginSource.PIP,
        )
        assert plugin.name == "test-adapter"
        assert plugin.layer_id == "layer_8_payments"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Test adapter"
        assert plugin.source == PluginSource.PIP

    def test_plugin_source_priority(self) -> None:
        """PluginSource has correct priority ordering."""
        assert PluginSource.LOCAL > PluginSource.PIP > PluginSource.BUILTIN
