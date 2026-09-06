"""SAS Layer 6 plugin: Telemetry Intelligence Engine (TIE) knowledge adapter.

This module defines the plugin metadata and factory for registering TIE
as the long-term knowledge provider for SAS through the real plugin system.

The file ``~/.sas/plugins/tie_knowledge.py`` should contain exactly this
module's contents (or import from it). See ``scripts/install_tie_plugin.sh``
for the one-step install.

SAS discovers plugins by scanning ``~/.sas/plugins/*.py`` for a module-level
``SAS_PLUGIN`` dict. When discovered, ``create_adapter()`` is used as the
factory to instantiate the layer implementation.
"""

from __future__ import annotations

# Plugin metadata for SAS discovery
SAS_PLUGIN = {
    "name": "tie-knowledge",
    "layer_id": "layer_6_long_term_knowledge",
    "version": "0.1.0",
    "description": "TIE behavioral knowledge graph as SAS Layer 6 provider",
    "author": "Daniel Kliewer",
    "url": "https://github.com/kliewerdaniel/sovereign-agent-stack",
}


def create_adapter(store_path: str = ":memory:"):
    """Factory function that returns a TIEKnowledgeAdapter instance.

    This is the entry point SAS's plugin system calls when it discovers
    this plugin via ``PluginRegistry.discover()``.
    """
    try:
        from sas_tie_knowledge.adapter import TIEKnowledgeAdapter
        return TIEKnowledgeAdapter(store_path=store_path)
    except ImportError:
        raise RuntimeError(
            "sas_tie_knowledge package not found. "
            "Install it with: pip install -e ."
        )
