# ADR-001: Use ARGO as the Base Harness (Not Hermes Directly)

*Status: Accepted*

## Context

The blog's critique centers on the $5K/month agency stack built on Hermes Agent. Hermes is MIT-licensed and self-hostable, but the typical agency deployment wraps it in rented infrastructure (Orgo, Honcho cloud, Composio, AgentMail, AgentPhone). We need a base harness that is:
- Open-source and self-hostable
- Local-first by default
- Extensible via MCP
- Cross-platform

## Decision

Use [ARGO](https://github.com/xark-argo/argo) as the base harness layer. ARGO is MIT-licensed, local-first, supports Ollama + API models, has an agent factory, local RAG, and MCP protocol support. It is the closest existing implementation of the sovereignty thesis.

## Consequences

- **Positive:** ARGO already inverts the sovereignty table — most layers default to owned. It has a multi-agent task engine, agent factory, and local RAG out of the box.
- **Positive:** MCP support means we can extend it with our compile-time knowledge graph, local auth broker, and payments abstraction without forking.
- **Neutral:** ARGO is in early development (as of 2026-09). We may need to patch or contribute upstream.
- **Neutral:** ARGO's browser control is tab-level, not full-desktop. We extend it with a local VM/Container substrate (see ADR-003).
- **Alternative considered:** Hermes Agent directly. Rejected because Hermes is a CLI/agent framework, not a full client. ARGO provides the UI, agent factory, and local RAG that Hermes lacks.

---

# ADR-002: Compile-Time Knowledge Graph as a First-Class Layer

*Status: Accepted*

## Context

The blog identifies the Honcho/Obsidian split as the most under-explained insight in the agency stack. Honcho is runtime reasoning over a rolling window (re-derived every time, drift-prone). Obsidian is compile-time structure (settled, inspectable, versionable). Agencies reach for Obsidian organically under client pressure, but nobody designs for it intentionally.

ARGO's RAG is retrieval-time only. It has no compile-time layer.

## Decision

Add a compile-time knowledge graph as a first-class layer in SAS. It is:
- Local markdown files (Obsidian-compatible: `[[wikilinks]]`, YAML frontmatter)
- Compiled periodically (or on file change) into a graph (Neo4j local, or SQLite adjacency list)
- Queried at runtime *before* retrieval RAG — settled facts first, ephemeral context second
- Diffable and auditable without an LLM in the loop

## Consequences

- **Positive:** This is the layer that most differentiates SAS from ARGO alone. It is the "long-term knowledge" layer the blog argues is missing.
- **Positive:** Markdown is human-legible. A client can read their own knowledge graph without invoking a model.
- **Positive:** Compile-time structure means facts are settled — no drift between calls, no token cost to re-derive.
- **Neutral:** Requires a compile step (cron or file watcher). Adds operational complexity.
- **Neutral:** Graph materialization (entity extraction, relationship inference) may require an LLM call. We use the local model for this.
- **Alternative considered:** Use Obsidian directly as the compile-time layer. Rejected because Obsidian is a UI, not an API. We use its file format but build our own compile/query layer on top.

---

# ADR-003: Local VM/Container Substrate (Not Orgo Cloud)

*Status: Accepted*

## Context

The blog's highest-leverage demo is watching an agent operate a full desktop (not just a browser tab). Orgo provides this as a cloud VM. The sovereignty cost: the agent's substrate lives on someone else's hardware.

## Decision

Implement the compute substrate as a local Docker container (or local VM via Lima/UTM on macOS) with a full desktop environment. The agent drives it via screenshots + mouse/keyboard events, same as Orgo's API, but local.

Pre-configured templates (Docker images) with SAS already installed spin up in seconds — the same "docker run" workflow Vasillescu describes, but on your own metal.

## Consequences

- **Positive:** The agent's substrate is owned. No cloud VM per agent. No Orgo bill.
- **Positive:** Full desktop environment — can run CRM clients, PDF editors, legacy Windows apps (via Wine or a Windows container).
- **Neutral:** Requires local resources (RAM, CPU). Not suitable for resource-constrained environments.
- **Neutral:** Docker/VM setup is more complex than `docker compose up`. We provide templates and scripts.
- **Alternative considered:** Use Orgo's API directly. Rejected on sovereignty grounds — the blog's entire thesis is that the compute substrate is one of the layers you should own.

---

# ADR-004: Self-Hosted Auth Broker (Not Composio)

*Status: Accepted*

## Context

Composio is the least defensible moat with the highest sovereignty cost: every credential for every tool for every client transits a third party's infrastructure. Centralized auth brokering is convenient because it's centralized, and centralization is a liability the moment the broker has an incident.

## Decision

Build a local MCP gateway that proxies requests to third-party tools, injecting credentials from a local encrypted vault (SQLite + libsodium envelope encryption). Token refresh via cron. Same convenience, zero third-party transit.

## Consequences

- **Positive:** Credentials never leave your infrastructure. No third-party auth broker.
- **Positive:** MCP-based — any MCP-compatible tool can be registered.
- **Positive:** Auditable — full trail of which tool was called, when, with which credential.
- **Neutral:** Requires initial setup (registering tools, provisioning credentials). We provide a CLI wizard.
- **Neutral:** Token refresh is our responsibility, not Composio's. We implement it as a cron job.
- **Alternative considered:** Use Composio directly. Rejected on sovereignty grounds — the blog flags this as the layer with the highest sovereignty cost.

---

# ADR-005: Payments Abstraction (Current Stopgap → MPP Future)

*Status: Accepted*

## Context

The payments layer is the most immature in the agency stack. The current stopgap is a Ramp card + computer-use filling checkout forms. The forward-looking solution is Stripe's Machine Payments Protocol (MPP) — HTTP 402 + structured payment requirement + agent authorization.

## Decision

Abstract the payments layer behind a single `pay_for_resource()` tool interface. Two implementations:
1. **Current (2026):** Computer-use + virtual card with spending limits
2. **Future (2027+):** MPP native (HTTP 402 listener → authorize → retry)

Swapping is a config change, not a rewrite.

## Consequences

- **Positive:** The abstraction means we don't couple to a stopgap. When MPP matures, we swap the implementation, not the interface.
- **Positive:** Spending limits and receipt handling are local logic — owned, not rented.
- **Neutral:** The current stopgap is fragile (computer-use filling forms is brittle by nature). We document this clearly.
- **Neutral:** MPP is not yet widely adopted. We build the abstraction now, implement MPP when the ecosystem matures.
- **Alternative considered:** Build MPP-native from day one. Rejected — MPP is too immature, and the stopgap works for 2026 deployments.

---

# ADR-006: Sovereignty Dashboard as a Living Artifact

*Status: Accepted*

## Context

The blog's most memorable artifact is the sovereignty accounting table: layer-by-layer, owned vs. rented. This is a static snapshot. It should be a living, scored audit.

## Decision

Implement a sovereignty dashboard that:
1. Scans the current stack configuration
2. Classifies each layer as owned/rented based on a local-vs-hosted heuristic
3. Generates a sovereignty score (owned / total)
4. Runs on a schedule (weekly) and flags drift
5. Renders as a markdown report (and optionally a web UI)

## Consequences

- **Positive:** Makes the blog's core insight operational — you can't manage what you don't measure.
- **Positive:** Drift detection — if you add a new MCP tool that transits a third-party auth broker, the dashboard flags the sovereignty score drop.
- **Positive:** Markdown report is human-legible and versionable.
- **Neutral:** The heuristic (local-vs-hosted) is imperfect. We allow manual override.
- **Alternative considered:** Static documentation only. Rejected — the blog argues the sovereignty line moves as the stack evolves. A static snapshot is a lie within weeks.
