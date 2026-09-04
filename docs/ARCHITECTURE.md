# Architecture: The 7-Layer Sovereignty Model

> "The model becoming free doesn't mean intelligence becomes sovereign. It just relocates the rent."

## Overview

Every agentic AI system — regardless of use case — can be decomposed into 8 independent architectural layers. Each layer is independently swappable. The layers are ordered from most-commoditized (bottom) to most-rent-sensitive (top).

```
┌─────────────────────────────────────────────────────────────┐
│  8. PAYMENTS         │ Who can spend, how, under what limits│
├─────────────────────────────────────────────────────────────┤
│  7. AUTH             │ Who can access what, credential store│
├─────────────────────────────────────────────────────────────┤
│  6. LONG-TERM MEMORY │ Compiled knowledge, graph structure  │
├─────────────────────────────────────────────────────────────┤
│  5. SHORT-TERM MEMORY│ Session context, rolling window      │
├─────────────────────────────────────────────────────────────┤
│  4. IDENTITY         │ Addressable, reachable, trustable     │
├─────────────────────────────────────────────────────────────┤
│  3. COMPUTE SUBSTRATE│ Where the agent runs, what it can touch│
├─────────────────────────────────────────────────────────────┤
│  2. HARNESS          │ Orchestration, tool-calling, memory   │
├─────────────────────────────────────────────────────────────┤
│  1. MODEL            │ Raw next-token prediction             │
└─────────────────────────────────────────────────────────────┘
```

The thesis: **the bottom 3 layers are commodities; the top 5 are where sovereignty lives or dies.** A system that owns its top 5 layers is sovereign. A system that rents them is a managed-service product wearing open-source clothing.

---

## Layer 1: Model

**What it is:** Raw next-token prediction. The LLM.

**Current state:** Commoditized. 30+ providers (OpenAI, Claude, DeepSeek, Ollama, local GGUF). Cost per token → 0. Hermes is explicitly model-agnostic across all of them.

**Sovereignty posture:** This layer is irrelevant to sovereignty. Owning your model (self-hosting Ollama) vs. renting it (API calls) is a cost/latency tradeoff, not a sovereignty one. The intelligence is commoditized; the rent has moved up.

**Default in SAS:**
- Primary: Ollama local (Llama 3.1, Qwen 2.5, Mistral)
- Fallback: API provider (configurable via `sas.yaml`)
- Switching: Runtime, per-conversation, automatic on local-model failure

**Interface:**
```python
class ModelProvider(Protocol):
    async def complete(self, messages: list[Message], tools: list[Tool]) -> Completion: ...
    async def stream(self, messages: list[Message], tools: list[Tool]) -> AsyncIterator[Token]: ...
    @property
    def identity(self) -> ModelIdentity: ...  # name, context_window, local_or_api
```

---

## Layer 2: Harness

**What it is:** The orchestration layer around the model — tool-calling loop, memory system, skill-creation, session persistence, messaging surfaces.

**Current state:** Hermes Agent (MIT), OpenClaw (MIT), Claude Code, Codex. This is the "free" part of the stack that everyone fixates on. It is necessary but not sufficient.

**Sovereignty posture:** The harness being MIT-licensed doesn't make a deployment sovereign if it's deployed on someone else's infrastructure with someone else's memory system and someone else's auth broker. *License ≠ ownership.*

**Default in SAS:**
- ARGO-based, self-hosted (native client or Docker)
- Skill system: create, version, share, iterate
- Memory: local (not cloud-tier)
- Surfaces: Telegram, Discord, Slack, WhatsApp, CLI, web

**Interface:**
```python
class Harness(Protocol):
    async def invoke(self, session: Session, message: Message) -> Response: ...
    async def create_skill(self, experience: Experience) -> Skill: ...
    async def execute_skill(self, skill: Skill, context: Context) -> Result: ...
```

---

## Layer 3: Compute Substrate

**What it is:** The actual computer the agent runs on and can manipulate.

**Current state:** Orgo gives agents a full cloud VM (not just a browser tab). This matters because real business workflows span desktop clients, shared drives, PDF editors, legacy Windows apps — none of which a browser-only agent can touch.

**Sovereignty posture:** Cloud VM per agent = rented. Local VM/Container = owned. The sovereignty line is: does the agent's substrate live on your hardware or someone else's?

**Default in SAS:**
- Local Docker container (or local VM via Lima/UTM on macOS)
- Full desktop environment accessible to the agent via screenshots + mouse/keyboard events
- Templated: pre-configured image with SAS already installed, spins up in seconds

**Interface:**
```python
class ComputeSubstrate(Protocol):
    async def boot(self, template: str) -> Machine: ...
    async def capture(self, machine: Machine) -> Screenshot: ...
    async def click(self, machine: Machine, x: int, y: int) -> None: ...
    async def type(self, machine: Machine, text: str) -> None: ...
    async def execute(self, machine: Machine, command: str) -> Output: ...
```

---

## Layer 4: Identity

**What it is:** The agent's addressable, reachable, trustable presence on legacy communication rails (email, phone, SMS, iMessage).

**Current state:** AgentMail (API-provisioned inboxes), AgentPhone (voice/SMS/iMessage). A genuinely new infrastructure category — giving non-human actors their own identity on protocols built for human dialing human.

**Sovereignty posture:** Unavoidably rented — you cannot self-host a phone number or an email domain's MX records. But you can abstract it behind a local adapter so the dependency is swappable.

**Design principle:** Authenticity-by-disclosure. The agent uses `agentmail.to` (not `@nick.ai`). When a recipient realizes it's AI, an obviously-agent domain reads as straightforward, not deceptive.

**Default in SAS:**
- AgentMail API for email
- AgentPhone API for voice/SMS
- Local adapter pattern: swap providers without touching agent logic

**Interface:**
```python
class EmailIdentity(Protocol):
    async def provision(self, username: str, domain: str) -> Inbox: ...
    async def send(self, inbox: Inbox, message: Email) -> None: ...
    async def watch(self, inbox: Inbox) -> AsyncIterator[Email]: ...  # webhook

class PhoneIdentity(Protocol):
    async def provision(self, region: str) -> PhoneNumber: ...
    async def call(self, number: PhoneNumber, target: str) -> Call: ...
    async def sms(self, number: PhoneNumber, message: str) -> None: ...
```

---

## Layer 5: Short-Term Memory

**What it is:** Session context, rolling window, "what just happened," preference inference.

**Current state:** Honcho (AI-native memory, two-layer context injection: base layer + dialectic layer). Runtime reasoning over a rolling window.

**Sovereignty posture:** Honcho is self-hostable (AGPL-3.0), but the typical agency deploys the cloud tier. Runtime memory is re-derived every time — a fact you re-infer at token cost with possibility of drift between calls.

**Default in SAS:**
- Local RAG (ARGO-native)
- Session summaries, user representation
- Optional Honcho self-hosted (configurable)
- The runtime memory layer is acknowledged as rented-or-re-derived; the *compile-time* layer (Layer 6) is where long-term facts are settled

**Interface:**
```python
class ShortTermMemory(Protocol):
    async def recall(self, session: Session, query: str) -> list[Fact]: ...
    async def update(self, session: Session, observation: Observation) -> None: ...
    async def summarize(self, session: Session) -> Summary: ...
```

---

## Layer 6: Long-Term Knowledge (Compile-Time Graph)

**What it is:** The settled, inspectable, versionable record of what the agent knows about a client, a project, a workflow — materialized as a graph, not re-derived at query time.

**Current state:** The blog's most under-explained insight. Agencies reach for Obsidian organically (client pressure), but nobody designs for it intentionally. ARGO's RAG is retrieval-time only. This layer is the *missing* one.

**Sovereignty posture:** This is the crux of the compile-time thesis. A fact retrieved by re-running inference over a context window is **not the same artifact** as a fact compiled once into a stable, inspectable, versionable node in a graph. The former re-derives at token cost with drift. The latter is settled — checked in, diffable, auditable without an LLM in the loop.

**Default in SAS:**
- Local markdown files in a designated knowledge folder
- Obsidian-compatible format (`[[wikilinks]]`, YAML frontmatter)
- Compile step: cron-triggered graph materialization (Neo4j local, or SQLite adjacency list)
- Runtime integration: query compile-time graph first, fall back to retrieval RAG for ephemeral

**Interface:**
```python
class CompileTimeKnowledge(Protocol):
    async def compile(self, source: Path) -> KnowledgeGraph: ...
    async def query(self, graph: KnowledgeGraph, query: str) -> list[Node]: ...
    async def diff(self, graph: KnowledgeGraph, since: datetime) -> Diff: ...
    async def audit(self, graph: KnowledgeGraph) -> AuditReport: ...
```

---

## Layer 7: Auth (Local MCP Gateway)

**What it is:** The broker that manages OAuth, API keys, token refresh, permission scoping across all the tools the agent touches.

**Current state:** Composio. The least glamorous, most operationally load-bearing layer. Every credential for every tool for every client transits a third party's infrastructure.

**Sovereignty posture:** This is the layer with the least defensible moat and the highest sovereignty cost. Centralized auth brokering is convenient precisely because it's centralized, and centralization is a liability the moment the broker has an incident.

**Default in SAS:**
- Local MCP gateway (self-hosted)
- Encrypted credential vault (SQLite + libsodium envelope encryption)
- Token refresh via cron
- Same convenience, zero third-party transit

**Interface:**
```python
class AuthBroker(Protocol):
    async def register_tool(self, tool: Tool, credentials: Credentials) -> None: ...
    async def call(self, tool: Tool, request: Request, session: Session) -> Response: ...
    async def refresh(self, tool: Tool) -> None: ...
    async def audit(self) -> AuditTrail: ...
```

---

## Layer 8: Payments

**What it is:** How the agent pays for things — API calls, SaaS subscriptions, one-shot purchases, streaming micropayments.

**Current state:** Stopgap (Ramp card + computer-use fills checkout forms). Forward-looking (Stripe MPP: HTTP 402 + structured payment requirement + agent authorization).

**Sovereignty posture:** Unavoidably transits third-party financial infrastructure. But the *logic* — the decision to spend, the limits, the receipt handling — can be local.

**Default in SAS:**
- Abstracted behind a single `pay_for_resource()` tool interface
- Current implementation: computer-use + virtual card with spending limits
- Future implementation: Stripe MPP native (HTTP 402 listener → authorize → retry)
- Swapping is a config change, not a rewrite

**Interface:**
```python
class PaymentAdapter(Protocol):
    async def pay(self, requirement: PaymentRequirement) -> Receipt: ...
    async def authorize(self, limit: SpendingLimit) -> None: ...
    async def receipt(self, payment_id: str) -> Receipt: ...
```

---

## The Sovereignty Score

SAS computes a sovereignty score: **owned layers / total layers**. The target is ≥ 6/8. The two rented layers (identity, payments) are abstracted so they can be owned if the market matures.

The score is not a purity test — it's a diagnostic. A score of 5/8 with a clear plan for the other 3 is better than a score of 7/8 with no awareness of the 1 you're missing.

See [SOVEREIGNTY.md](SOVEREIGNTY.md) for the scoring methodology and how the dashboard computes it.
