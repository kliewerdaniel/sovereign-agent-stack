"""Plugin system for the Sovereign Agent Stack.

Enables community-built layer implementations via:
- Local plugins (~/.sas/plugins/)
- Pip-installed plugins (sas_layer_* entry points)
- Built-in plugins (shipped with SAS)

Plugin priority: LOCAL > PIP > BUILTIN
Higher priority plugins override lower priority ones for the same layer.

Usage:
    from sas.plugins import register_plugin, LayerPlugin, PluginSource

    register_plugin(LayerPlugin(
        name="my-payment-adapter",
        layer_id="layer_8_payments",
        version="1.0.0",
        description="My custom payment adapter",
        source=PluginSource.LOCAL,
    ))
"""

from __future__ import annotations

import importlib
import importlib.metadata
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Protocol


class PluginSource(IntEnum):
    """Plugin source — higher value = higher priority."""
    BUILTIN = 0
    PIP = 1
    LOCAL = 2


@dataclass(frozen=True)
class LayerPlugin:
    """A plugin that provides a layer implementation."""
    name: str
    layer_id: str  # e.g., "layer_8_payments"
    version: str
    description: str = ""
    source: PluginSource = PluginSource.LOCAL
    author: str = ""
    url: str = ""
    factory: callable = None  # Optional factory to create the layer instance


class LayerProvider(Protocol):
    """Protocol that layer plugins must implement."""
    def get_layer(self, layer_id: str) -> Any: ...


@dataclass
class _PluginEntry:
    """Internal plugin registry entry."""
    plugin: LayerPlugin
    priority: PluginSource


class PluginRegistry:
    """Global plugin registry.

    Manages layer plugins with priority-based override.
    Higher priority plugins override lower priority ones.
    """

    _plugins: dict[str, _PluginEntry] = {}

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing)."""
        cls._plugins = {}

    @classmethod
    def register(cls, plugin: LayerPlugin) -> None:
        """Register a plugin, respecting priority.

        A plugin only replaces an existing one if its priority is >= current.
        """
        existing = cls._plugins.get(plugin.layer_id)
        if existing is None or plugin.source >= existing.priority:
            cls._plugins[plugin.layer_id] = _PluginEntry(
                plugin=plugin,
                priority=plugin.source,
            )

    @classmethod
    def unregister(cls, layer_id: str) -> None:
        """Unregister a plugin by layer ID."""
        cls._plugins.pop(layer_id, None)

    @classmethod
    def get(cls, layer_id: str) -> LayerPlugin | None:
        """Get the active plugin for a layer."""
        entry = cls._plugins.get(layer_id)
        return entry.plugin if entry else None

    @classmethod
    def list_all(cls, layer_id: str | None = None) -> list[LayerPlugin]:
        """List all registered plugins, optionally filtered by layer."""
        if layer_id:
            entry = cls._plugins.get(layer_id)
            return [entry.plugin] if entry else []
        return [entry.plugin for entry in cls._plugins.values()]

    @classmethod
    def discover(cls) -> list[LayerPlugin]:
        """Discover plugins from all sources.

        Searches:
        1. Built-in plugins (shipped with SAS)
        2. Pip-installed plugins (entry points)
        3. Local plugins (~/.sas/plugins/)
        """
        plugins: list[LayerPlugin] = []

        # Discover built-in plugins
        plugins.extend(_discover_builtins())

        # Discover pip-installed plugins via entry points
        plugins.extend(_discover_pip_plugins())

        # Discover local plugins
        plugins.extend(_discover_local_plugins())

        return plugins


# Module-level convenience functions
def register_plugin(plugin: LayerPlugin) -> None:
    """Register a plugin in the global registry."""
    PluginRegistry.register(plugin)


def unregister_plugin(layer_id: str) -> None:
    """Unregister a plugin by layer ID."""
    PluginRegistry.unregister(layer_id)


def get_plugin(layer_id: str) -> LayerPlugin | None:
    """Get the active plugin for a layer."""
    return PluginRegistry.get(layer_id)


def list_plugins(layer_id: str | None = None) -> list[LayerPlugin]:
    """List all registered plugins."""
    return PluginRegistry.list_all(layer_id)


def discover_plugins() -> list[LayerPlugin]:
    """Discover plugins from all sources."""
    return PluginRegistry.discover()


def _discover_builtins() -> list[LayerPlugin]:
    """Discover built-in plugins."""
    # Built-in plugins are shipped with SAS
    # For now, just return an empty list
    # In production, this would scan src/sas/layers for built-in implementations
    return []


def _discover_pip_plugins() -> list[LayerPlugin]:
    """Discover pip-installed plugins via entry points."""
    plugins: list[LayerPlugin] = []

    try:
        entry_points = importlib.metadata.entry_points()
        if hasattr(entry_points, "select"):
            sas_plugins = entry_points.select(group="sas.layers")
        else:
            sas_plugins = entry_points.get("sas.layers", [])

        for ep in sas_plugins:
            try:
                factory = ep.load()
                plugin = LayerPlugin(
                    name=ep.name,
                    layer_id=_layer_id_from_ep_name(ep.name),
                    version=_get_package_version(ep.name),
                    description=f"Pip-installed plugin: {ep.name}",
                    source=PluginSource.PIP,
                    factory=factory,
                )
                plugins.append(plugin)
            except Exception:
                # Skip broken entry points
                continue
    except Exception:
        pass

    return plugins


def _discover_local_plugins() -> list[LayerPlugin]:
    """Discover local plugins from ~/.sas/plugins/."""
    plugins: list[LayerPlugin] = []

    plugins_dir = Path.home() / ".sas" / "plugins"
    if not plugins_dir.exists():
        return plugins

    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name.startswith("_"):
            continue

        try:
            # Import the plugin module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem, str(plugin_file)
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for plugin metadata
                if hasattr(module, "SAS_PLUGIN"):
                    meta = module.SAS_PLUGIN
                    plugin = LayerPlugin(
                        name=meta.get("name", plugin_file.stem),
                        layer_id=meta.get("layer_id", ""),
                        version=meta.get("version", "0.1.0"),
                        description=meta.get("description", ""),
                        source=PluginSource.LOCAL,
                        author=meta.get("author", ""),
                        url=meta.get("url", ""),
                    )
                    plugins.append(plugin)
        except Exception:
            continue

    return plugins


def _layer_id_from_ep_name(name: str) -> str:
    """Map entry point name to layer ID."""
    mapping = {
        "sas_payments": "layer_8_payments",
        "sas_auth": "layer_7_auth",
        "sas_knowledge": "layer_6_long_term_knowledge",
        "sas_memory": "layer_5_short_term_memory",
        "sas_identity": "layer_4_identity",
        "sas_compute": "layer_3_compute",
        "sas_harness": "layer_2_harness",
        "sas_model": "layer_1_model",
    }
    return mapping.get(name, f"layer_unknown_{name}")


def _get_package_version(name: str) -> str:
    """Get the version of a pip-installed package."""
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "0.0.0"


def auto_register_discovered() -> None:
    """Auto-discover and register all plugins."""
    for plugin in discover_plugins():
        register_plugin(plugin)
