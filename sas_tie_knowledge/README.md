# SAS × TIE Knowledge Layer Adapter

The `sas_tie_knowledge` package adapts the [Telemetry Intelligence Engine](https://github.com/kliewerdaniel/sovereign-agent-stack)
(TIE) — a local-first GraphRAG system for website analytics — to SAS's
Layer 6 (Long-Term Knowledge) interface.

## How it works

TIE compiles GA4 telemetry and site content into a behavioral knowledge graph
(`tie.graph.export_graph_json`). This adapter reads that compiled graph and
maps it to SAS's `KnowledgeGraph` of `Node`/`Edge` objects, so SAS's plugin
registry can pick TIE over its built-in `CompileTimeKnowledge`.

## Quick start

```python
from pathlib import Path
from sas_tie_knowledge.adapter import TIEKnowledgeAdapter

adapter = TIEKnowledgeAdapter()
graph = adapter.compile(Path("path/to/tie_graph_export.json"))
print(f"Compiled: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

# Query
results = adapter.query(graph, "sovereign")
for r in results:
    print(f"  - {r.label}")

# Audit
report = adapter.audit(graph)
print(f"Orphaned: {len(report.orphaned_nodes)}")
```

## Pointing at a different TIE instance

The adapter accepts any TIE graph export JSON (the format produced by
`tie.graph.export_graph_json`). To point at a different TIE instance:

1. Run `tie graph` in the TIE project to build the graph.
2. Use `tie.graph.export_graph_json(G)` to produce the JSON, or directly
   reference the `data/tie_graph_export.json` file.
3. Pass that path to `adapter.compile()`.

For SAS CLI usage:

```bash
# Compile a TIE graph into SAS's knowledge store
python -m sas knowledge compile /path/to/tie_graph_export.json --store ~/.sas/knowledge.db

# Query it
python -m sas knowledge query "your search" --store ~/.sas/knowledge.db

# Audit it
python -m sas knowledge audit --store ~/.sas/knowledge.db
```

## Plugin registration

The plugin at `~/.sas/plugins/tie_knowledge.py` registers TIE as the
`layer_6_long_term_knowledge` provider via `PluginSource.LOCAL`, which
outranks the built-in provider. SAS discovers it automatically:

```bash
python -m sas registry list
# → tie-knowledge (layer_6_long_term_knowledge) source=LOCAL
```

## Known schema mismatches

See [docs/ADAPTER_GAPS.md](../docs/ADAPTER_GAPS.md) for the full list. Key items:

- **Timestamps**: TIE nodes have none; the adapter synthesizes `created_at`/`updated_at` at compile time.
- **Behavioral metrics**: TIE's `views`, `avg_engagement`, etc. are preserved as-is in `node.properties`.
- **Session nodes**: TIE's `session:*` nodes are ephemeral; filter by `properties["tie_group"] == "session"` if unwanted.
- **Stale-node audit**: Not applicable (no timestamps); the adapter returns an empty `stale_nodes` list.
