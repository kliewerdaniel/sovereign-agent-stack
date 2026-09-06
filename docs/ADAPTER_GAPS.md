# TIE → SAS Adapter Gaps

This document records genuine schema mismatches between the Telemetry
Intelligence Engine (TIE) and SAS's compile-time knowledge graph model,
and how the adapter handles each.

## 1. Timestamps (created_at / updated_at)

**SAS model:** Every `Node` has `created_at` and `updated_at` ISO timestamps.
**TIE model:** Nodes and edges have no timestamps — the graph is a compiled
snapshot of behavioral relationships, not a versioned fact store.

**Adapter behavior:** Synthesizes `created_at = updated_at = now` at compile time.
This is a **lossy mapping** — the adapter cannot distinguish a node that has
been stable for months from one that was just observed. Downstream consumers
(e.g. SAS's "stale node" audit) cannot meaningfully apply their time-based
heuristics; the adapter returns an empty `stale_nodes` list and documents why.

## 2. Behavioral metrics vs. declarative facts

**SAS model:** Node `properties` are declarative facts about a domain entity
(e.g. `client: Acme Corp`, `status: active`).

**TIE model:** Node properties are observational metrics — `views`, `avg_engagement`,
`max_scroll`, `unique_sessions`, `sources[]`. These describe *how users
interacted with* the entity, not *what the entity is*.

**Adapter behavior:** Metrics are preserved verbatim in `node.properties`
under their original keys. The adapter does not attempt to reinterpret a
pageview count as a "fact" — it is stored as data, not semantics. Queries
against these properties will match on the stringified values, which is
correct for exact lookups but does not encode that "1200 views" is a quantity.

## 3. Ephemeral session nodes

**TIE model:** Each unique `session_id` becomes a `session:*` node. For a
site with significant traffic, this can produce hundreds of nodes that
represent a single visit, not a durable entity.

**Adapter behavior:** Session nodes are included in the compiled graph.
They will appear in query results and audit reports. If this is undesirable
for a given deployment, filter them by `properties["tie_group"] == "session"`
before or after compilation.

## 4. Graph directionality

**TIE model:** Edges are directional (`from` → `to`) but stored in an
undirected `networkx.Graph`. The `export_graph_json` function emits
`from`/`to` from the edge tuple, which preserves insertion order but
not semantic direction.

**SAS model:** Edges are directional (`source` → `target`).

**Adapter behavior:** Maps `from` → `source` and `to` → `target` directly.
The semantic directionality of TIE edges (`session → page` for "viewed",
`content → topic` for "discusses") is preserved because the adapter
does not reorder them.

## 5. Compile-time vs. runtime compilation

**SAS model:** `CompileTimeKnowledge.compile(source: Path)` reads markdown
files from a directory at build time.

**TIE model:** The graph is already compiled by `tie graph` before the
adapter sees it. The adapter reads a JSON export, not raw source files.

**Adapter behavior:** The adapter's `compile()` method reads a pre-built
graph JSON. It does not invoke TIE's pipeline. This is intentional —
the adapter is a read-only consumer of TIE's output, not a re-implementation.

## Summary

| Aspect | SAS | TIE | Adapter |
|--------|-----|-----|---------|
| Timestamps | created_at, updated_at | None | Synthesized at compile time |
| Properties | Declarational facts | Observational metrics | Preserved as-is |
| Node identity | Stable domain entity | May be ephemeral session | Included, filterable |
| Edge semantics | links_to | discusses, viewed, came_from | Mapped 1:1 |
| Compile step | Reads markdown | Reads pre-built JSON | Reads pre-built JSON |
