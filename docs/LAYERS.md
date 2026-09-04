# Layer Specifications

Detailed interface and implementation specifications for each of the 8 layers.

---

## Layer 1: Model

### Purpose
Raw next-token prediction. The most commoditized layer — irrelevant to sovereignty but critical to capability.

### Interface
```python
from dataclasses import dataclass
from enum import Enum

class ModelLocation(Enum):
    LOCAL = "local"      # Ollama, llama.cpp
    API = "api"          # OpenAI, Claude, DeepSeek

@dataclass
class ModelIdentity:
    name: str
    context_window: int
    location: ModelLocation
    provider: str        # "ollama", "openai", "anthropic"

class ModelProvider(Protocol):
    async def complete(self, messages: list[Message], tools: list[Tool]) -> Completion: ...
    async def stream(self, messages: list[Message], tools: list[Tool]) -> AsyncIterator[Token]: ...
    @property
    def identity(self) -> ModelIdentity: ...
```

### Configuration (sas.yaml)
```yaml
model:
  primary:
    provider: ollama
    name: llama3.1:8b
    location: local
  fallback:
    provider: openai
    name: gpt-4o
    location: api
  auto_fallback: true    # Fall back to API on local failure
```

### Sovereignty Notes
- Owning (self-hosting) vs. renting (API) is a **cost/latency tradeoff**, not a sovereignty one.
- The intelligence is commoditized. The rent has moved up to layers 3-8.
- Score as **owned** if local model exists (even if API fallback is configured).
- Score as **rented** if API-only with no local option.

---

## Layer 2: Harness

### Purpose
Orchestration around the model: tool-calling loop, memory, skills, session persistence, messaging surfaces.

### Interface
```python
class Harness(Protocol):
    async def invoke(self, session: Session, message: Message) -> Response: ...
    async def create_skill(self, experience: Experience) -> Skill: ...
    async def execute_skill(self, skill: Skill, context: Context) -> Result: ...
    async def register_tool(self, tool: Tool, adapter: ToolAdapter) -> None: ...
```

### Implementation
- **Base:** ARGO (MIT-licensed, self-hosted)
- **Agent Factory:** Visual scenario creation, model binding, tool integration
- **Skill System:** Create from experience, version, share, iterate
- **Surfaces:** Telegram, Discord, Slack, WhatsApp, CLI, web

### Sovereignty Notes
- License ≠ ownership. MIT-licensed but cloud-deployed is still rented.
- Score as **owned** if self-hosted on your hardware.
- Score as **rented** if using a SaaS harness tier.

---

## Layer 3: Compute Substrate

### Purpose
The actual computer the agent runs on and can manipulate. Full desktop, not just a browser tab.

### Interface
```python
class ComputeSubstrate(Protocol):
    async def boot(self, template: str) -> Machine: ...
    async def capture(self, machine: Machine) -> Screenshot: ...
    async def click(self, machine: Machine, x: int, y: int) -> None: ...
    async def type(self, machine: Machine, text: str) -> None: ...
    async def execute(self, machine: Machine, command: str) -> Output: ...
    async def destroy(self, machine: Machine) -> None: ...
```

### Implementation
- **Local Docker container** with full desktop environment (XFCE/LXDE)
- **Orchestrator:** SAS spawns containers on demand, destroys when idle
- **Templates:** Pre-configured images with SAS + common tools pre-installed
- **Input surface:** Screenshots + mouse/keyboard events (same as Orgo's API)

### Configuration
```yaml
compute:
  substrate: local_docker    # local_docker, local_vm, orgo_cloud
  template: sas-desktop:latest
  resources:
    cpu: 4
    memory: 8Gi
  auto_destroy: 300          # seconds of inactivity before destroy
```

### Sovereignty Notes
- Cloud VM per agent (Orgo) = rented. Local container = owned.
- Score as **owned** if substrate runs on your hardware.
- Score as **rented** if using Orgo or similar cloud VM.

---

## Layer 4: Identity

### Purpose
The agent's addressable, reachable, trustable presence on legacy communication rails.

### Interface
```python
class EmailIdentity(Protocol):
    async def provision(self, username: str, domain: str) -> Inbox: ...
    async def send(self, inbox: Inbox, message: Email) -> None: ...
    async def watch(self, inbox: Inbox) -> AsyncIterator[Email]: ...

class PhoneIdentity(Protocol):
    async def provision(self, region: str) -> PhoneNumber: ...
    async def call(self, number: PhoneNumber, target: str) -> Call: ...
    async def sms(self, number: PhoneNumber, message: str) -> None: ...
```

### Implementation
- **Email:** AgentMail API (or self-hosted Mailpit for dev)
- **Phone:** AgentPhone API for voice/SMS/iMessage
- **Trust design:** Use `agentmail.to` domain, not spoofed `@nick.ai`
- **Adapter pattern:** Local interface, swappable providers

### Configuration
```yaml
identity:
  email:
    provider: agentmail      # agentmail, mailpit, self_hosted
    domain: agentmail.to
  phone:
    provider: agentphone     # agentphone, none
    region: US
```

### Sovereignty Notes
- **Unavoidably rented** — you cannot self-host a phone number or MX records.
- Abstract behind local adapter so provider is swappable.
- Not counted against sovereignty score.

---

## Layer 5: Short-Term Memory

### Purpose
Session context, rolling window, "what just happened," preference inference.

### Interface
```python
class ShortTermMemory(Protocol):
    async def recall(self, session: Session, query: str) -> list[Fact]: ...
    async def update(self, session: Session, observation: Observation) -> None: ...
    async def summarize(self, session: Session) -> Summary: ...
```

### Implementation
- **Primary:** ARGO's local RAG (files, folders, websites, dynamic sync)
- **Session summaries:** Auto-generated, human-legible
- **Optional:** Self-hosted Honcho (AGPL-3.0) for two-layer context injection

### Configuration
```yaml
memory:
  short_term:
    provider: local_rag      # local_rag, honcho_self_hosted, honcho_cloud
    max_context_tokens: 8000
    summary_refresh: 10      # messages between summary refreshes
```

### Sovereignty Notes
- Runtime memory is re-derived every time — a fact you re-infer at token cost.
- Score as **owned** if local RAG or self-hosted Honcho.
- Score as **rented** if Honcho cloud tier.

---

## Layer 6: Long-Term Knowledge (Compile-Time Graph)

### Purpose
The settled, inspectable, versionable record of what the agent knows — materialized as a graph, not re-derived at query time.

### Interface
```python
class CompileTimeKnowledge(Protocol):
    async def compile(self, source: Path) -> KnowledgeGraph: ...
    async def query(self, graph: KnowledgeGraph, query: str) -> list[Node]: ...
    async def diff(self, graph: KnowledgeGraph, since: datetime) -> Diff: ...
    async def audit(self, graph: KnowledgeGraph) -> AuditReport: ...
```

### Implementation
- **Storage:** Local markdown files in designated knowledge folder
- **Format:** Obsidian-compatible (`[[wikilinks]]`, YAML frontmatter, folder structure)
- **Compile step:** Cron-triggered graph materialization
  - Parse markdown files
  - Extract entities and relationships (local LLM or rule-based)
  - Materialize graph (Neo4j local, or SQLite adjacency list)
  - Generate sovereignty report
- **Runtime integration:** Query compile-time graph first, fall back to retrieval RAG

### Configuration
```yaml
memory:
  long_term:
    provider: compile_time_graph   # compile_time_graph, retrieval_only
    source: ~/sas-knowledge
    graph_store: sqlite            # sqlite, neo4j
    compile_cron: "0 */6 * * *"    # every 6 hours
    on_watch: true                 # compile on file change
```

### Sovereignty Notes
- **This is the layer SAS contributes that ARGO alone does not have.**
- A fact compiled once into a stable graph node is an asset.
- A fact re-derived at query time is a liability.
- Score as **owned** if compile-time graph exists.
- Score as **rented** if retrieval-only with no compile step.

---

## Layer 7: Auth (Local MCP Gateway)

### Purpose
Manages OAuth, API keys, token refresh, permission scoping across all tools the agent touches.

### Interface
```python
class AuthBroker(Protocol):
    async def register_tool(self, tool: Tool, credentials: Credentials) -> None: ...
    async def call(self, tool: Tool, request: Request, session: Session) -> Response: ...
    async def refresh(self, tool: Tool) -> None: ...
    async def audit(self) -> AuditTrail: ...
```

### Implementation
- **Local MCP gateway** (self-hosted)
- **Credential store:** SQLite + libsodium envelope encryption
- **Token refresh:** Cron-triggered
- **Audit trail:** Full log of which tool was called, when, with which credential

### Configuration
```yaml
auth:
  broker: local_mcp_gateway    # local_mcp_gateway, composio
  vault: ~/.sas/vault.db
  encryption: libsodium
  refresh_cron: "0 */1 * * *"  # hourly
```

### Sovereignty Notes
- Composio = rented. Local gateway = owned.
- Centralized auth brokering is convenient because it's centralized, and centralization is a liability.
- Score as **owned** if local MCP gateway.
- Score as **rented** if Composio hosted broker.

---

## Layer 8: Payments

### Purpose
How the agent pays for things — API calls, SaaS subscriptions, one-shot purchases, streaming micropayments.

### Interface
```python
class PaymentAdapter(Protocol):
    async def pay(self, requirement: PaymentRequirement) -> Receipt: ...
    async def authorize(self, limit: SpendingLimit) -> None: ...
    async def receipt(self, payment_id: str) -> Receipt: ...
```

### Implementation
- **Abstracted behind `pay_for_resource()` tool interface**
- **Current (2026):** Computer-use + virtual card (Ramp/Mercury) with spending limits
- **Future (2027+):** Stripe MPP native (HTTP 402 listener → authorize → retry)
- **Swapping:** Config change, not rewrite

### Configuration
```yaml
payments:
  adapter: virtual_card        # virtual_card, mpp_native
  virtual_card:
    provider: ramp
    limit: 100                 # USD per day
  mpp:
    provider: stripe
    settlement: stablecoin      # stablecoin, card, lightning
```

### Sovereignty Notes
- **Unavoidably transits third-party financial infrastructure.**
- The *logic* (decision to spend, limits, receipt handling) is local.
- Abstracted so swapping implementations is a config change.
- Not counted against sovereignty score.

---

## Cross-Cutting Concerns

### Configuration
All layers are configured via a single `sas.yaml` file. The sovereignty dashboard reads this file to classify each layer.

### Observability
Each layer emits structured events (JSON) to a local event bus. The dashboard subscribes to these events to detect drift.

### Testing
Each layer has a mock implementation for testing. Integration tests verify layer isolation (swapping one layer doesn't break others).

### Security
- Credentials never leave the local vault
- All inter-layer communication is over localhost (Unix sockets or loopback TCP)
- No telemetry leaves the machine without explicit opt-in
