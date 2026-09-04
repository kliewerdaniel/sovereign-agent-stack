# Sovereign Agent Stack (SAS)

> *"The model becoming free doesn't mean intelligence becomes sovereign. It just relocates the rent."*
> — Daniel Kliewer, [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack)

**SAS is a local-first, compile-time AI agent framework** that implements the 8-layer sovereignty model. It takes the critique — that the $5K/month agency stack rents 7 of 9 layers — and inverts it: **6 of 8 layers are owned by default**, with the remaining two abstracted behind swappable adapters.

---

## Table of Contents

1. [The Sovereignty Thesis](#the-sovereignty-thesis)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [CLI Reference](#cli-reference)
6. [Python API](#python-api)
7. [MCP Server](#mcp-server)
8. [Architecture](#architecture)
9. [Rust Compile-Time Layer](#rust-compile-time-layer)
10. [Plugin System](#plugin-system)
11. [Testing](#testing)
12. [Development](#development)
13. [Documentation](#documentation)
14. [Roadmap](#roadmap)
15. [License](#license)

---

## The Sovereignty Thesis

Every agentic AI system can be decomposed into 8 independent layers. Most "agency stacks" rent 7 of them. SAS owns 6 by default.

| # | Layer | Typical Agency Stack | SAS Default | How to Own It |
|---|-------|---------------------|-------------|---------------|
| 1 | **Model** | API provider (rented) | Ollama local + API fallback | Use `ollama` as primary, `openai` as fallback |
| 2 | **Harness** | Hermes/OpenClaw (MIT, cloud-deployed) | ARGO-based, self-hosted | Included — always owned |
| 3 | **Compute Substrate** | Orgo cloud VM (rented) | Local Docker desktop | Use `local_docker` substrate |
| 4 | **Identity** | AgentMail/AgentPhone (rented) | APIs behind local adapter | Unavoidably rented — excluded from score |
| 5 | **Short-term Memory** | Honcho cloud (rented) | Local RAG + session memory | Use `local_rag` provider |
| 6 | **Long-term Knowledge** | Obsidian (accidental) | **Compile-time knowledge graph** | Use `compile_time_graph` provider |
| 7 | **Auth** | Composio hosted broker (rented) | **Local MCP gateway + encrypted vault** | Use `local_mcp_gateway` broker |
| 8 | **Payments** | Ramp card + computer-use (stopgap) | **Abstracted: VirtualCard → MPP future** | Unavoidably transits financial infra |

**Default sovereignty score: 6/8 owned** (87.5% — "Fully Sovereign") vs. 2/9 in the typical agency stack.

### Scoring Verdicts

| Score | Verdict | Meaning |
|-------|---------|---------|
| >= 87.5% | Fully Sovereign | 7-8/8 layers owned |
| >= 62.5% | Sovereign (target) | 5-6/8 layers owned |
| >= 37.5% | Partially sovereign | 3-4/8 layers owned |
| < 37.5% | Rented | 0-2/8 layers owned |

Identity and Payments are **unavoidably rented** (can't self-host phone/MX records or payment settlement) and excluded from the scoring denominator.

---

## Quick Start

```bash
# Clone
git clone https://github.com/kliewerdaniel/sovereign-agent-stack.git
cd sovereign-agent-stack

# Install (Python 3.11+ required)
pip install -e ".[dev]"

# Initialize a template config
sas init --output sas.yaml

# Run sovereignty audit
sas dashboard --verbose

# Or use a pre-configured example
sas dashboard --config examples/agency-worker/sas.yaml --verbose

# Run as MCP server (for ARGO harness integration)
sas serve --config sas.yaml

# Verify sovereignty meets threshold
sas verify --threshold 0.625
```

---

## Installation

### Requirements

- **Python**: 3.11, 3.12, or 3.14 (3.14 recommended for PyO3 extension)
- **Rust**: 1.70+ (optional, for compile-time verification layer)
- **System**: macOS, Linux, or Windows (WSL2)

### Install Methods

```bash
# From source (recommended for development)
git clone https://github.com/kliewerdaniel/sovereign-agent-stack.git
cd sovereign-agent-stack
python -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Via pip (when published)
pip install sovereign-agent-stack

# Via Homebrew (when published)
brew install sovereign-agent-stack

# Via Docker
docker pull kliewerdaniel/sas:latest
docker run -v $(pwd)/sas.yaml:/app/sas.yaml kliewerdaniel/sas:latest dashboard
```

### Build the Rust Extension (Optional)

The Rust extension provides compile-time verification of capabilities, policies, and state machines. Without it, SAS falls back to pure-Python implementations.

```bash
# Set Python for PyO3 binding
export PYO3_PYTHON=/opt/homebrew/bin/python3.14

# Build
cd rust && cargo build --release -p sas-core-py

# Copy extension to project root
cp target/release/libsas_core_py.dylib ../sas_core_py.so
# On Linux: cp target/release/libsas_core_py.so ../sas_core_py.so
```

---

## Configuration

SAS uses a single `sas.yaml` file to declare your sovereignty posture. Generate a template with `sas init`:

```yaml
# sas.yaml — Sovereign Agent Stack Configuration
# See docs/ARCHITECTURE.md for the 7-layer sovereignty model.

model:
  primary:
    provider: ollama
    name: llama3.1:8b
    location: local          # "local" or "api"
  fallback:
    provider: openai
    name: gpt-4o
    location: api
  auto_fallback: true

compute:
  substrate: local_docker    # local_docker, local_vm, orgo_cloud
  template: sas-desktop:latest
  resources:
    cpu: 4
    memory: 8Gi
  auto_destroy: 300          # seconds of inactivity before teardown

memory:
  short_term:
    provider: local_rag      # local_rag, honcho_self_hosted, honcho_cloud
    max_context_tokens: 8000
  long_term:
    provider: compile_time_graph   # compile_time_graph, retrieval_only
    source: ~/sas-knowledge
    graph_store: sqlite
    compile_cron: "0 */6 * * *"    # recompile every 6 hours
    on_watch: true                 # watch for file changes

auth:
  broker: local_mcp_gateway    # local_mcp_gateway, composio
  vault: ~/.sas/vault.db
  encryption: libsodium
  refresh_cron: "0 */1 * * *"

payments:
  adapter: virtual_card        # virtual_card, mpp_native
  virtual_card:
    provider: ramp
    limit: 100                 # daily limit in USD
  mpp:
    provider: stripe
    settlement: stablecoin

identity:
  email:
    provider: agentmail
    domain: agentmail.to
  phone:
    provider: agentphone
    region: US

# Manual sovereignty overrides (optional)
# overrides:
#   layer_5: owned    # e.g., self-hosting Honcho on your own Postgres
```

### Example Configurations

- [Agency Worker](examples/agency-worker/README.md) — 6/6 owned, fully sovereign
- [Personal Assistant](examples/personal-assistant/README.md) — 3/6 owned, balanced
- [Industry Analyst](examples/industry-analyst/README.md) — 5/6 owned, research-first

---

## CLI Reference

```bash
sas init [-o OUTPUT]              # Create template sas.yaml
sas dashboard [-c CONFIG] [--json] [--verbose]  # Sovereignty audit
sas run [-c CONFIG] [-q QUERY]    # Run agent session
sas serve [-c CONFIG]             # Start MCP server (JSON-RPC stdio)
sas fleet [-c CONFIG] [-n AGENTS] # Manage multi-agent fleet
sas tools [-c CONFIG]             # List available MCP tools
sas verify [-c CONFIG] [-t THRESHOLD]  # Verify sovereignty threshold
sas --help                        # Show all commands
sas --version                     # Show version
```

### `sas init`

Creates a template `sas.yaml` in the current directory (or `--output` path).

### `sas dashboard`

Runs the sovereignty audit. Outputs a scored layer report.

```bash
# Human-readable
sas dashboard --verbose

# JSON output (for programmatic consumption)
sas dashboard --json

# Use specific config
sas dashboard --config examples/agency-worker/sas.yaml
```

**Output:**
```
══════════════════════════════════════════════════
  SOVEREIGN AGENT STACK — DASHBOARD
══════════════════════════════════════════════════
  Score: 87.50%
  Verdict: Fully Sovereign
  Owned: 7/8
──────────────────────────────────────────────────
  ✓ Model: owned
  ✓ Harness: owned
  ✓ Compute Substrate: owned
  ✗ Identity: rented
  ✓ Short-term Memory: owned
  ✓ Long-term Knowledge: owned
  ✓ Auth: owned
  ✗ Payments: rented
══════════════════════════════════════════════════
```

### `sas run`

Runs a single agent session with sovereignty verification.

```bash
sas run --config sas.yaml --query "What is my sovereignty score?"
```

### `sas serve`

Starts the MCP server for ARGO harness integration. Communicates via stdio JSON-RPC.

```bash
sas serve --config sas.yaml
```

### `sas fleet`

Manages a multi-agent fleet.

```bash
# Spawn 5 agents
sas fleet --agents 5

# Spawn from config
sas fleet --config sas.yaml --agents 3
```

### `sas tools`

Lists all available MCP tools with their schemas.

### `sas verify`

Exits with code 1 if sovereignty is below threshold. Useful for CI/CD gates.

```bash
sas verify --threshold 0.625
# ✓ Sovereignty verified: 87.50% >= 62.50%

sas verify --threshold 0.95
# ✗ Sovereignty below threshold: 87.50% < 95.00%
# (exit code 1)
```

---

## Python API

### Agent Runtime

```python
from sas.runtime import AgentRuntime, FleetCoordinator, MCPServer
from sas.core.config import parse_sas_yaml
from sas.core.scoring import generate_report

# ── Single Agent ──────────────────────────────────────────

# From config file
runtime = AgentRuntime.from_config("sas.yaml")
runtime.initialize()

# Execute a tool
runtime.register_tool(
    "my_tool",
    "Does something useful",
    {"type": "object", "properties": {"query": {"type": "string"}}},
    ["read_filesystem"],
)
result = runtime.execute_tool("my_tool", {"query": "test"})
# {"status": "ok", "tool": "my_tool", "input": {"query": "test"}}

# Get status
status = runtime.get_status()
# {
#   "session_id": "uuid...",
#   "status": "running",
#   "state": "Idle",
#   "sovereignty_score": 0.875,
#   "sovereignty_verdict": "Fully Sovereign",
#   "registered_tools": ["my_tool"],
#   "granted_capabilities": ["read_filesystem", "read_knowledge"],
#   ...
# }

runtime.shutdown()

# ── Fleet Coordinator ─────────────────────────────────────

fleet = FleetCoordinator()

# Spawn agents
sid1 = fleet.spawn_agent("sas.yaml")
sid2 = fleet.spawn_agent()  # defaults
sid3 = fleet.spawn_agent()

# Fleet status
status = fleet.fleet_status()
# {
#   "agents": 3,
#   "average_sovereignty_score": 0.875,
#   "agents_list": [...],
#   "fleet_state": "Idle",
# }

# Terminate
fleet.terminate_agent(sid1)
fleet.shutdown_all()

# ── MCP Server ────────────────────────────────────────────

server = MCPServer.from_config("sas.yaml")

# List tools
tools = server.list_tools()
# [
#   {"name": "check_sovereignty", "description": "...", "inputSchema": {...}},
#   {"name": "query_knowledge", "description": "...", "inputSchema": {...}},
#   {"name": "pay_for_resource", "description": "...", "inputSchema": {...}},
# ]

# Call a tool programmatically
result = server.call_tool("check_sovereignty", {})
# MCPToolResult(success=True, data={"score": 0.875, ...}, error=None)

# Handle a raw MCP JSON-RPC request
response = server.handle_request({
    "method": "tools/call",
    "params": {"name": "check_sovereignty", "arguments": {}},
})

# Start serving (stdio loop)
server.serve()
```

### Core Configuration

```python
from sas.core.config import (
    parse_sas_yaml, generate_template,
    SASConfig, ModelConfig, SubstrateType, MemoryProvider,
    AuthBroker, PaymentAdapter, LongTermProvider,
)

# Parse config
config = parse_sas_yaml(Path("sas.yaml"))

# Access fields
config.model_primary.name       # "llama3.1:8b"
config.model_primary.location   # "local"
config.substrate                # SubstrateType.LOCAL_DOCKER
config.memory_short_term        # MemoryProvider.LOCAL_RAG
config.auth_broker              # AuthBroker.LOCAL_MCP_GATEWAY

# Build config programmatically
config = SASConfig(
    model_primary=ModelConfig(
        provider="ollama", name="llama3.1:8b", location="local"
    ),
    substrate=SubstrateType.LOCAL_DOCKER,
    memory_short_term=MemoryProvider.LOCAL_RAG,
    memory_long_term=LongTermProvider.COMPILE_TIME_GRAPH,
    auth_broker=AuthBroker.LOCAL_MCP_GATEWAY,
    payment_adapter=PaymentAdapter.VIRTUAL_CARD,
)

# Generate template file
generate_template(Path("sas.yaml"))
```

### Sovereignty Scoring

```python
from sas.core.scoring import generate_report, LayerID, Ownership

# Generate a report
report = generate_report(config)

report.score           # 0.875
report.verdict         # "Fully Sovereign"
report.owned_count     # 7
report.total_count     # 8
report.layers          # list[LayerScore]

# Inspect individual layers
for layer in report.layers:
    print(f"{layer.name}: {layer.scored_as.value} — {layer.reasoning}")
    print(f"  Unavoidable rental: {layer.unavoidable_rental}")

# Filter
owned = [l for l in report.layers if l.scored_as == Ownership.OWNED]
rented = [l for l in report.layers if l.scored_as == Ownership.RENTED]
unavoidable = [l for l in report.layers if l.unavoidable_rental]

# Compare with previous run
report2 = generate_report(config, previous_score=report.score)
report2.drift  # 0.0 (no change)
```

### Knowledge Graph

```python
from sas.layers.knowledge import CompileTimeKnowledge, MarkdownParser
from pathlib import Path

# Compile a directory of markdown files into a knowledge graph
ctk = CompileTimeKnowledge(store_path=":memory:")
graph = ctk.compile(Path("~/sas-knowledge"))

# Query
results = ctk.query(graph, "sovereignty")
for node in results:
    print(f"{node.label}: {node.properties.get('content', '')[:100]}")

# Diff two graph states
old_graph = ctk.compile(Path("~/sas-knowledge"))
# ... make changes ...
new_graph = ctk.compile(Path("~/sas-knowledge"))
diff = ctk.diff(old_graph, new_graph)
print(f"Added: {len(diff.added_nodes)}, Removed: {len(diff.removed_nodes)}")

# Audit
report = ctk.audit(graph)
print(f"Total: {report.total_nodes} nodes, {report.total_edges} edges")
print(f"Orphaned: {len(report.orphaned_nodes)}, Stale: {len(report.stale_nodes)}")
```

### Auth Broker

```python
from sas.layers.auth import LocalAuthBroker, Credentials

# Create with encrypted SQLite vault
broker = LocalAuthBroker(
    store_path="~/.sas/vault.db",
    encryption_key="your-secret-key",  # or auto-generated
)

# Register a tool
broker.register_tool("github", Credentials(
    tool_name="github",
    auth_type="oauth",
    token="ghp_...",
    refresh_token="ghr_...",
    scopes=["repo", "read:user"],
))

# List registered tools
tools = broker.list_tools()  # ["github"]

# Get decrypted credentials
creds = broker.get_credentials("github")
print(creds.token)  # "ghp_..."

# Audit trail
trail = broker.audit()
for entry in trail.entries:
    print(f"{entry.timestamp}: {entry.tool_name} {entry.method} {entry.path}")
```

### Payments

```python
from sas.layers.payments import (
    VirtualCardAdapter, MPPAdapter,
    PaymentRequirement, SpendingLimit,
)

# Virtual card (current stopgap)
adapter = VirtualCardAdapter(
    provider="ramp",
    limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
)

req = PaymentRequirement(
    resource="api.anthropic.com/claude-sonnet-4-20250514",
    price=3.00,
    currency="USD",
    methods=["card"],
    cadence="one_shot",
    metadata={"model": "claude-sonnet-4"},
)

receipt = adapter.pay(req)
print(f"Paid: {receipt.payment_id}, Status: {receipt.status}")
print(f"Remaining daily: ${adapter.remaining_daily:.2f}")

# MPP (future)
mpp = MPPAdapter(
    settlement="stablecoin",
    limit=SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD"),
)

req_mpp = PaymentRequirement(
    resource="compute.gpu.4xh100",
    price=50.00,
    currency="USD",
    methods=["stablecoin", "card"],
    cadence="streaming",
    metadata={"region": "us-east-1"},
)

receipt_mpp = mpp.pay(req_mpp)
```

### Capability Registry (Typestate Pattern)

```python
from sas.rust_bridge import CapabilityRegistry, ExecutionContext

# Create registry
registry = CapabilityRegistry()

# Grant capabilities
registry.grant("read_filesystem")
registry.grant("read_knowledge")
registry.grant("write_filesystem")

# Check
registry.is_granted("read_filesystem")  # True
registry.require("read_filesystem")      # OK

# Revoke
registry.revoke("write_filesystem")
registry.is_granted("write_filesystem")  # False

# All granted
caps = registry.granted_capabilities()  # {"read_filesystem", "read_knowledge"}

# ExecutionContext with typestate capability tokens
ctx = ExecutionContext()
ctx_with_read = ctx.with_read_filesystem()
# ctx_with_read.can_read_filesystem == True
# ctx.can_read_filesystem == False (original unchanged)
```

### Policy Enforcer

```python
from sas.rust_bridge import PolicyEnforcer

enforcer = PolicyEnforcer("allow")  # or "deny"

# Check operations
enforcer.check_write("/path/to/file", b"content")   # True or raises
enforcer.check_exec("git", ["status"])              # True or raises
enforcer.check_dispatch("https://api.example.com")  # True or raises
enforcer.check_payment(50.0, "USD", "recipient")    # True or raises

# In "deny" mode, all checks raise PermissionError
deny_enforcer = PolicyEnforcer("deny")
deny_enforcer.check_write("/any", b"data")  # PermissionError
```

### Agent State Machine

```python
from sas.rust_bridge import AgentStateMachine

sm = AgentStateMachine()
sm.current  # "Idle"

# Valid transitions
sm.transition("Compiling")
sm.transition("Executing")
sm.transition("Verifying")
sm.transition("Completed")
sm.transition("Idle")  # Reset

# Invalid transitions raise ValueError
sm.transition("Completed")  # ValueError: Invalid state transition: Idle -> Completed

# Check before transitioning
sm.can_transition_to("Compiling")  # True
sm.can_transition_to("Completed")  # False

# Transition history
for entry in sm.history:
    print(f"{entry['from']} -> {entry['to']} ({entry.get('reason', '')})")
```

### Sovereignty Asserter

```python
from sas.rust_bridge import SovereigntyAsserter

asserter = SovereigntyAsserter()

# Set layer ownership
asserter.with_layer("model", "owned")
asserter.with_layer("harness", "owned")
asserter.with_layer("compute", "owned")
asserter.with_layer("identity", "rented")       # unavoidable
asserter.with_layer("short_term_memory", "owned")
asserter.with_layer("long_term_knowledge", "owned")
asserter.with_layer("auth", "owned")
asserter.with_layer("payments", "rented")       # unavoidable

# Calculate score (excludes unavoidable rentals)
asserter.score           # 1.0 (6/6 scorable layers owned)
asserter.owned_count     # 6
asserter.total_count     # 6
asserter.verdict         # "Fully Sovereign"

# Assert conditions
asserter.assert_all_owned()          # True
asserter.assert_score_above(0.625)   # True
asserter.assert_score_above(0.95)    # Raises ValueError
```

---

## MCP Server

The MCP server exposes SAS tools via the [Model Context Protocol](https://modelcontextprotocol.io/) for integration with ARGO and other agent harnesses.

### Default Tools

| Tool | Description | Required Capability |
|------|-------------|-------------------|
| `check_sovereignty` | Returns current sovereignty score and layer status | `read_knowledge` |
| `query_knowledge` | Query the compile-time knowledge graph | `read_knowledge` |
| `pay_for_resource` | Pay for a resource using the virtual card | `process_payments` |

### Register Custom Tools

```python
server = MCPServer.from_config("sas.yaml")

server.register_tool(
    "search_web",
    "Search the web for information",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "description": "Max results"},
        },
        "required": ["query"],
    },
    ["dispatch_network"],  # required capabilities
)
```

### JSON-RPC Protocol

The server communicates via stdio. Each line is a JSON-RPC request:

```json
// Request: list tools
{"method": "tools/list"}

// Response
{"tools": [{"name": "check_sovereignty", ...}]}

// Request: call tool
{"method": "tools/call", "params": {"name": "check_sovereignty", "arguments": {}}}

// Response
{"content": [{"type": "text", "text": "{\"score\": 0.875, ...}"}]}

// Error
{"error": {"message": "Unknown tool: foo"}}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI (sas init/dashboard/run/serve/fleet)  │
├─────────────────────────────────────────────────────────────────┤
│   AgentRuntime │ FleetCoordinator │ MCPServer                    │
├─────────────────────────────────────────────────────────────────┤
│   rust_bridge (Rust extension ↔ Pure Python fallback)            │
├─────────────────────────────────────────────────────────────────┤
│   sas-core-rs: capability, policy, state_machine, sovereignty    │
│   sas-core-py: PyO3 bindings                                     │
│   sas-macros: #[derive(Tool)] proc-macro                         │
├─────────────────────────────────────────────────────────────────┤
│   Core Layers: config │ scoring │ knowledge │ auth │ payments    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: Tool Execution

```
┌─────────┐    ┌──────────┐    ┌────────────┐    ┌───────────┐    ┌──────────┐
│ Request │ -> │ Validate │ -> │ Capability │ -> │  Policy   │ -> │ Execute  │
│ (MCP/   │    │ Schema   │    │ Check      │    │ Enforce   │    │ Tool     │
│  CLI)   │    │          │    │            │    │           │    │          │
└─────────┘    └──────────┘    └────────────┘    └───────────┘    └──────────┘
                                                                       │
                     ┌─────────────────────────────────────────────────┘
                     v
              ┌───────────┐    ┌───────────┐
              │  Record   │ -> │  Return   │
              │  State    │    │  Result   │
              └───────────┘    └───────────┘
```

---

## Rust Compile-Time Layer

SAS includes an optional Rust workspace that provides compile-time verification of:

- **Capabilities**: Typestate pattern ensures capabilities are proven before use
- **Policy**: Policy proofs enforced at compile time
- **State Machine**: Exhaustive transition checking via `transitions!` macro
- **Sovereignty**: Compile-time sovereignty assertions

### Crates

| Crate | Purpose |
|-------|---------|
| `sas-macros` | `#[derive(Tool)]` proc-macro for automatic schema generation |
| `sas-core-rs` | Core types: `ExecutionContext`, `CapabilityRegistry`, `PolicyEnforcer`, `AgentStateMachine`, `SovereigntyAsserter` |
| `sas-core-py` | PyO3 bindings exposing all Rust types to Python |

### Build

```bash
cd rust
PYO3_PYTHON=/opt/homebrew/bin/python3.14 cargo build --release -p sas-core-py
cp target/release/libsas_core_py.dylib ../sas_core_py.so
```

### Rust Types ↔ Python Mapping

| Rust Type | Python Class | Module |
|-----------|-------------|--------|
| `ExecutionContext` | `ExecutionContext` | `sas.rust_bridge` |
| `CapabilityRegistry` | `CapabilityRegistry` | `sas.rust_bridge` |
| `PolicyEnforcer` | `PolicyEnforcer` | `sas.rust_bridge` |
| `AgentStateMachine` | `AgentStateMachine` | `sas.rust_bridge` |
| `SovereigntyAsserter` | `SovereigntyAsserter` | `sas.rust_bridge` |

When the Rust extension is unavailable, all types fall back to pure-Python implementations with identical APIs.

---

## Plugin System

SAS supports plugins for custom layer implementations. Plugins are discovered in order:

1. **LOCAL** — `./plugins/` directory (highest priority)
2. **PIP** — installed pip packages with `sas.plugins` entry point
3. **BUILTIN** — shipped with SAS (lowest priority)

### Create a Plugin

```python
# plugins/my_plugin.py
from sas.plugins import PluginRegistry

class MyCustomAuthPlugin:
    name = "my_custom_auth"
    version = "1.0.0"
    
    def register(self, registry: PluginRegistry):
        registry.register_auth_broker("custom", self)

    def get_credentials(self, tool_name: str):
        # Your implementation
        pass
```

---

## Testing

```bash
# All tests
.venv/bin/python -m pytest tests/ -v

# Unit tests only
.venv/bin/python -m pytest tests/unit/ -v

# Integration tests only
.venv/bin/python -m pytest tests/integration/ -v

# With coverage
.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing

# Benchmarks
.venv/bin/python -m pytest tests/benchmarks/ -v

# Rust tests (in rust/ directory)
cargo test --workspace
```

### Test Counts

| Category | Count |
|----------|-------|
| Unit tests | 156 |
| Integration tests | 23 |
| Benchmarks | 14 |
| Rust unit + integration | 68 |
| Rust Python extension | 25 |
| Rust Python bridge | 19 |
| **Total** | **281+** |

---

## Development

### Project Structure

```
sovereign-agent-stack/
├── src/sas/                      # Python source
│   ├── core/                     # Config, scoring
│   │   ├── config.py             # sas.yaml parser, SASConfig
│   │   └── scoring.py            # Sovereignty scoring engine
│   ├── layers/                   # Sovereignty layer implementations
│   │   ├── knowledge.py          # Compile-time knowledge graph
│   │   ├── auth.py               # Local MCP gateway
│   │   ├── payments.py           # Virtual card / MPP adapter
│   │   ├── model.py              # Model adapters
│   │   ├── memory.py             # Short-term memory
│   │   ├── identity.py           # Identity adapters
│   │   ├── harness.py            # ARGO harness integration
│   │   └── substrate.py          # Compute substrate
│   ├── runtime/                  # Agent runtime orchestration
│   │   ├── orchestrator.py       # AgentRuntime, FleetCoordinator
│   │   ├── mcp_server.py         # MCP protocol server
│   │   └── cli.py                # Click-based CLI
│   ├── rust_bridge/              # Python-Rust bindings
│   │   └── __init__.py           # Auto-detects Rust extension
│   ├── plugins.py                # Plugin registry
│   └── dashboard/                # CLI dashboard
├── rust/                         # Rust workspace
│   ├── sas-core-rs/              # Core types and verification
│   ├── sas-core-py/              # PyO3 bindings
│   └── sas-macros/               # Proc-macro derive
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── benchmarks/               # Performance benchmarks
├── docs/                         # Documentation
├── examples/                     # Example configurations
├── packaging/                    # Distribution (Homebrew, Docker, Chocolatey)
└── pyproject.toml                # Python project config
```

### Linting and Type Checking

```bash
# Lint with ruff
.venv/bin/ruff check src/

# Type check with mypy
.venv/bin/mypy src/

# Format with ruff
.venv/bin/ruff format src/
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full 7-layer sovereignty model |
| [docs/ADR.md](docs/ADR.md) | Architectural decision records |
| [docs/SOVEREIGNTY.md](docs/SOVEREIGNTY.md) | The sovereignty thesis operationalized |
| [docs/LAYERS.md](docs/LAYERS.md) | Detailed layer specifications |
| [docs/LAYER_REGISTRY.md](docs/LAYER_REGISTRY.md) | Community layer registry |
| [docs/PLUGINS.md](docs/PLUGINS.md) | Plugin development guide |
| [docs/ROADMAP](docs/ROADMAP.md) | What's built and what's next |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operations and incident response |
| [docs/SECURITY.md](docs/SECURITY.md) | Security audit and hardening |
| [docs/ARGO_SKILL_PACK.md](docs/ARGO_SKILL_PACK.md) | ARGO harness integration |
| [docs/PACKAGES.md](docs/PACKAGES.md) | Package manager distribution |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## Roadmap

### Completed (v1.0.0)

- ✅ 8-layer sovereignty model
- ✅ Compile-time knowledge graph
- ✅ Self-hosted auth broker with encrypted vault
- ✅ Payments abstraction (VirtualCard + MPP adapters)
- ✅ Compute substrate lifecycle manager
- ✅ Identity adapters (AgentMail/AgentPhone)
- ✅ Plugin system with priority-based override
- ✅ MCP server for ARGO harness integration
- ✅ Sovereignty dashboard (CLI)
- ✅ Agent runtime orchestrator with state machine
- ✅ Fleet coordinator for multi-agent management
- ✅ Rust compile-time verification layer (optional)
- ✅ 281+ tests (unit, integration, benchmark, Rust)

### Upcoming

- **Multi-user support** — Per-user sovereignty profiles
- **Knowledge graph signing** — Cryptographic verification of compiled knowledge
- **HSM for payment keys** — Hardware security module integration
- **Community layer registry** — Discover and share sovereignty layer implementations
- **ARGO skill pack** — Pre-built ARGO integration

---

## License

MIT — because the harness should be free, and the sovereignty should be yours.

---

## Acknowledgments

Sovereign Agent Stack is built on ideas from [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack) and the broader sovereign AI movement. It stands on the shoulders of:

- [Ollama](https://ollama.com/) — Local model serving
- [PyO3](https://pyo3.rs/) — Rust-Python bindings
- [Click](https://click.palletsprojects.com/) — CLI framework
- [MCP](https://modelcontextprotocol.io/) — Model Context Protocol
- [ARGO](https://github.com/nousresearch/hermes-agent) — Agent harness

---

<div align="center">

**[⬆ Back to Top](#sovereign-agent-stack-sas)**

Made with sovereignty by [Daniel Kliewer](https://danielkliewer.com)

</div>
