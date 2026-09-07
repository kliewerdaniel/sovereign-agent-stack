"""Resolve the active Layer 6 knowledge backend.

Single source of truth for "which backend answers knowledge queries."
All three entry points (CLI, plain-function MCP, class-based MCP) call
this so there is exactly one place that decides.

Resolution order:
1. Call ``auto_register_discovered()`` so any plugin under ``~/.sas/plugins/``
   is registered.
2. Look up the active plugin for ``layer_6_long_term_knowledge``.
3. If a plugin with a factory is registered, return the plugin's adapter
   instance (via ``plugin.factory(store_path=...)``) and the label
   ``"plugin"``.
4. Otherwise return a ``CompileTimeKnowledge(store_path=...)`` instance and
   the label ``"builtin"``.
"""

from __future__ import annotations

from pathlib import Path

from sas.layers.knowledge import CompileTimeKnowledge, KnowledgeGraph


def resolve_knowledge_backend(store_path: str = ":memory:"):
    """Return the active Layer 6 backend and which kind it is.

    Returns ``(adapter, kind)`` where ``kind`` is ``"plugin"`` or
    ``"builtin"``. Callers can use ``kind`` to report which backend
    answered the query and to produce clearer errors on mismatch.
    """
    from sas.plugins import auto_register_discovered, get_plugin

    auto_register_discovered()
    plugin = get_plugin("layer_6_long_term_knowledge")

    if plugin is not None and plugin.factory is not None:
        return plugin.factory(store_path=store_path), "plugin"

    return CompileTimeKnowledge(store_path=store_path), "builtin"


def compile_source(adapter, source: Path) -> KnowledgeGraph:
    """Compile ``source`` using ``adapter``, with a clear error on mismatch.

    If the active backend cannot parse ``source`` (e.g. a TIE plugin
    receiving a plain markdown directory), the adapter's exception is
    caught and re-raised as a ``ValueError`` with an actionable message
    that names the plugin and tells the user how to proceed.
    """
    try:
        return adapter.compile(source)
    except Exception as e:
        name = getattr(adapter, "__class__", type(adapter)).__name__
        raise ValueError(
            f"Layer 6 backend '{name}' could not parse '{source}'. "
            f"Original error: {e}. "
            f"If this source is a plain markdown vault, remove the active "
            f"plugin (rm ~/.sas/plugins/<plugin>.py) and recompile."
        ) from e
