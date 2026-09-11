# Sovereign Agent Stack (SAS)

> *"The model becoming free doesn't mean intelligence becomes sovereign. It just relocates the rent."*
> — Daniel Kliewer, [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack)

**SAS is a local-first AI agent framework** that implements an 8-layer sovereignty model. It scores how much of your agent infrastructure you actually own vs. rent, and enforces that boundary at runtime.

---

## Quick Start (3-minute demo)

```bash
# Clone and enter the repo
cd sovereign-agent-stack

# Install with dashboard dependencies
pip install -e ".[dashboard]"

# Start the dashboard
python -m sas dashboard serve

# Open http://localhost:8080
```

### What you'll see

1. **Sovereignty Score** — Load `sas.yaml` and see a real score with plain-English reasoning for each layer's owned/rented status.

2. **Quant Research Pipeline** — Click "Run" on a quant world and watch, live via SSE, as an LLM proposes a strategy, gets backtested, passes through the deterministic authorization gate, executes against the (paper) broker, and lands in a provenance graph you can inspect.

3. **Agent Chat** — Ask the agent a question and get a real model response (via local Ollama) grounded in the compiled knowledge graph.

4. **Provenance/Audit Trail** — See the chain of what happened and why the trade was or wasn't approved — concrete proof this isn't theater.

---

## What SAS actually does

**1. Sovereignty scoring.** Parse a `sas.yaml` → get a score + verdict. Know exactly which layers you own.

**2. Compile-time knowledge graph.** Markdown vault → graph → queryable. The agent's long-term knowledge is a build artifact, not a runtime dependency.

**3. Local auth broker.** Encrypted credential vault + audit trail. Tools call through the broker; credentials never leak to the model.

**4. Payments abstraction.** Virtual card today, MPP tomorrow. Spending limits enforced at the adapter level.

**5. Compute substrate.** Boot local desktop containers, auto-destroy on idle. The agent's body lives on your hardware.

**6. Identity adapters.** Email and phone behind swappable adapters. Mock for dev, production stubs for real APIs.

**7. Quant research pipeline.** Self-contained professional evaluation worlds: data → research → backtest → risk → report → provenance.

**8. Community ecosystem.** Plugin system + community registry + ARGO skill pack for harness integration.

---

## The 8-Layer Sovereignty Model

| # | Layer | Rented (typical) | Owned (SAS default) |
|---|-------|------------------|---------------------|
| 1 | **Model** | API provider | Ollama local + API fallback |
| 2 | **Harness** | OpenClaw cloud | ARGO-based, self-hosted (always owned) |
| 3 | **Compute** | Orgo cloud VM | Local Docker desktop |
| 4 | **Identity** | AgentMail/AgentPhone | APIs behind local adapter (unavoidably rented) |
| 5 | **Short-term Memory** | Honcho cloud | Local RAG + session memory |
| 6 | **Long-term Knowledge** | Obsidian (accidental) | Compile-time knowledge graph |
| 7 | **Auth** | Composio hosted broker | Local MCP gateway + encrypted vault |
| 8 | **Payments** | Ramp card | Abstracted: VirtualCard → MPP future |

**Default score: 6/8 owned** (87.5% — "Fully Sovereign"). Identity and Payments are unavoidably rented — excluded from the scoring denominator.

### Scoring Verdicts

| Score | Verdict | Meaning |
|-------|---------|---------|
| >= 87.5% | Fully Sovereign | 7-8/8 layers owned |
| >= 62.5% | Sovereign (target) | 5-6/8 layers owned |
| >= 37.5% | Partially sovereign | 3-4/8 layers owned |
| < 37.5% | Rented | 0-2/8 layers owned |

---

## CLI Reference

```bash
# Core
python -m sas init [-o OUTPUT]                          # Create template sas.yaml
python -m sas dashboard [-c CONFIG] [--json] [--verbose] # Sovereignty audit
python -m sas dashboard serve                            # Launch the live dashboard

# Knowledge
python -m sas knowledge compile <source> [--store PATH]  # Compile markdown → graph
python -m sas knowledge query <query> [--store PATH]     # Query the graph
python -m sas knowledge audit [--store PATH]             # Audit graph integrity

# Auth
python -m sas auth register <tool> --token X [--auth-type oauth] [--store PATH]
python -m sas auth list [--store PATH]
python -m sas auth get <tool> [--store PATH]
python -m sas auth unregister <tool> [--store PATH]
python -m sas auth audit [--store PATH]

# Payments
python -m sas payments pay <resource> --price X [--methods card] [--adapter virtual_card]
python -m sas payments limit --daily X --per-transaction Y [--adapter virtual_card]

# Substrate
python -m sas substrate boot [--template xfce]
python -m sas substrate list
python -m sas substrate exec <machine_id> <command>
python -m sas substrate destroy <machine_id>

# Identity
python -m sas identity provision-email <username> [--domain agentmail.to] [--mock]
python -m sas identity send-email <inbox_id> --to X --subject Y --body Z [--mock]
python -m sas identity provision-phone [--region US] [--mock]
python -m sas identity call <number_id> --to X [--mock]
python -m sas identity sms <number_id> --message X [--mock]

# Community registry
python -m sas registry publish <name> <layer_id> <version> [--desc X] [--author Y] [--url Z]
python -m sas registry unpublish <name>
python -m sas registry search <query>
python -m sas registry list
python -m sas registry get <name>
python -m sas registry by-layer <layer_id>

# ARGO skill pack
python -m sas argo info                                        # Show skill metadata
python -m sas argo invoke --params '{"action": "sovereignty_check"}'  # Invoke skill
python -m sas argo schema                                     # Show parameter schema

# Quant research
python -m sas quant status
python -m sas research --universe AAPL --horizon 1y
python -m sas quant backtest --strategy-id momentum-001 --seed 42
python -m sas quant risk --weights AAPL:0.5,MSFT:0.5
python -m sas quant provenance [node_id]
python -m sas quant auto-research --universe AAPL --universe MSFT --mode backtest-only --auto-approve
python -m sas quant auto-research --universe AAPL --mode live-paper  # requires Alpaca credentials
```

---

## Autonomous Quant Research Pipeline

The autonomous research pipeline wires: **strategy proposal (LLM) → backtest → risk evaluation → authorization gate → broker → provenance**.

```bash
# Run full pipeline with synthetic data (no credentials needed)
python -m sas quant auto-research --universe AAPL --universe MSFT --mode backtest-only --auto-approve

# Run with live paper trading (requires Alpaca credentials)
export APCA_API_KEY_ID="your-key"
export APCA_API_SECRET_KEY="your-secret"
python -m sas quant auto-research --universe AAPL --mode live-paper

# Output options
python -m sas quant auto-research --universe AAPL --output json                # JSON provenance
python -m sas quant auto-research --universe AAPL --output markdown            # Human-readable report
python -m sas quant auto-research --universe AAPL --output both --output-file report.md
```

### Architecture

```
QuantResearchOrchestrator.run()
         │
         ├── 1. Assemble QuantWorld (data + policies + agents + tools)
         ├── 2. Run LLM research loop (propose_strategy tool → strategy artifact)
         ├── 3. QuantEngine.run() → BacktestResult
         ├── 4. Create TradeIntent from strategy
         ├── 5. TradeAuthorization gate (deterministic, LLM cannot bypass)
         │      ├── RiskEngine.evaluate_trade() → RiskEvaluation
         │      ├── Session limits (max trades, max order value)
         │      └── Human approval (stdin prompt, or --auto-approve for CI)
         ├── 6. BrokerAdapter.submit_trade() → Order
         │      ├── SimulatedBroker (backtest-only mode)
         │      └── AlpacaBrokerAdapter (live-paper mode)
         └── 7. ProvenanceGraph capture (dataset → strategy → backtest → trade → order)
```

### Authorization Gate

The `TradeAuthorization` gate is a **deterministic component the LLM cannot bypass**. No order reaches the broker without passing through it.

- **Risk policy compliance**: Evaluates trades against `RiskPolicy` constraints
- **Session limits**: Max trades per session, max single-order value
- **Human-in-the-loop**: Blocks on stdin for approval (default). Use `--auto-approve` for CI/tests.

### Broker Adapters

Two implementations ship with SAS:

| Adapter | Mode | Description |
|---------|------|-------------|
| `SimulatedBroker` | `backtest-only` | Deterministic, in-memory, no external calls |
| `AlpacaBrokerAdapter` | `live-paper` | Alpaca paper trading API |

Credentials are sourced from `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` environment variables or the local auth broker vault. They are **never logged, never serialized to provenance, and never exposed in error messages**.

---

## Dashboard

The dashboard is a FastAPI + vanilla JS single-page app that demonstrates all SAS capabilities live.

```bash
# Start the server
python -m sas dashboard serve

# Open in browser
open http://localhost:8080
```

### Features

- **Sovereignty tab** — Load `sas.yaml`, see score + per-layer reasoning
- **Pipeline tab** — Run quant worlds live with SSE progress streaming
- **Worlds tab** — Browse available evaluation worlds
- **Knowledge tab** — Query the compiled knowledge graph
- **Agent tab** — Chat with a local LLM grounded in knowledge graph
- **Provenance tab** — Inspect the full audit trail of every trade decision

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Server status |
| `/api/layers` | GET | Sovereignty score + layer breakdown |
| `/api/pipeline/run` | POST | Start a pipeline run |
| `/api/pipeline/stream` | GET | SSE stream of pipeline events |
| `/api/knowledge` | GET | Query knowledge graph |
| `/api/agent/chat` | POST | Chat with the agent |

---

## Python API

### Sovereignty

```python
from sas.core.config import parse_sas_yaml
from sas.core.scoring import generate_report
from sas.layers import LayerRegistry

config = parse_sas_yaml(Path("sas.yaml"))

# Via scorer
report = generate_report(config)
print(report.score)       # 0.875
print(report.verdict)     # "Fully Sovereign"
print(report.owned_count) # 7

# Via registry
registry = LayerRegistry(config)
owned, total, score = registry.sovereignty_score()
print(f"{owned}/{total} = {score:.1%}")
```

### Knowledge Graph

```python
from sas.layers.knowledge import CompileTimeKnowledge
from pathlib import Path

ctk = CompileTimeKnowledge(store_path=":memory:")
graph = ctk.compile(Path("~/sas-knowledge"))
results = ctk.query(graph, "sovereignty")

# Audit
report = ctk.audit(graph)
print(f"{report.total_nodes} nodes, {len(report.orphaned_nodes)} orphaned")
```

### Auth Broker

```python
from sas.layers.auth import LocalAuthBroker, Credentials

broker = LocalAuthBroker(store_path="~/.sas/vault.db")
broker.register_tool("github", Credentials(
    tool_name="github", auth_type="oauth", token="ghp_...", scopes=["repo"]
))

# Make a credential-bearing call
from sas.layers.auth import Request, Response
req = Request(tool_name="github", method="GET", path="/repos", headers={})
resp = broker.call(req, my_http_client)
```

### Payments

```python
from sas.layers.payments import VirtualCardAdapter, PaymentRequirement, SpendingLimit

adapter = VirtualCardAdapter(limit=SpendingLimit(daily=100, per_transaction=50, currency="USD"))
receipt = adapter.pay(PaymentRequirement(
    resource="api", price=25.0, currency="USD", methods=["card"], cadence="one_shot", metadata={}
))
print(receipt.status)  # "completed"
```

### Identity

```python
from sas.layers.identity import MockEmailAdapter, MockPhoneAdapter

# Email
email = MockEmailAdapter()
inbox = email.provision("agent", "agentmail.to")
email.send(inbox, Email(from_="agent@agentmail.to", to="x@y.com", subject="Hi", body="Test"))
sent = email.watch(inbox)

# Phone
phone = MockPhoneAdapter()
number = phone.provision("US")
phone.sms(number, "Integration test")
```

### Quant Pipeline

```python
from sas.quant.orchestration import OrchestratorConfig, QuantResearchOrchestrator

config = OrchestratorConfig(
    universe=["AAPL", "MSFT"],
    mode="backtest-only",
    auto_approve=True,
)
orchestrator = QuantResearchOrchestrator(config)
result = orchestrator.run()

print(result.status)           # "completed"
print(result.strategy.name)    # "default-momentum"
print(result.backtest_result.sharpe_ratio)
print(result.backtest_result.total_return)
print(result.backtest_result.max_drawdown)
print(result.provenance_graph.to_dict())
```

---

## Configuration

```yaml
# sas.yaml
model:
  primary:
    provider: ollama
    name: llama3.1:8b
    location: local
  fallback:
    provider: openai
    name: gpt-4o
    location: api

compute:
  substrate: local_docker
  resources:
    cpu: 4
    memory: 8Gi
  auto_destroy: 300

memory:
  short_term:
    provider: local_rag
  long_term:
    provider: compile_time_graph
    source: ~/sas-knowledge

auth:
  broker: local_mcp_gateway
  vault: ~/.sas/vault.db
  encryption: libsodium

payments:
  adapter: virtual_card
  virtual_card:
    provider: ramp
    limit: 100

identity:
  email:
    provider: agentmail
    domain: agentmail.to
  phone:
    provider: agentphone
    region: US
```

---

## Plugin System

Three sources, priority-ordered: LOCAL > PIP > BUILTIN.

```python
from sas.plugins import LayerPlugin, PluginSource, register_plugin

register_plugin(LayerPlugin(
    name="my-payments",
    layer_id="layer_8_payments",
    version="1.0.0",
    description="Custom payment adapter",
    source=PluginSource.LOCAL,
))
```

Discovery scans built-in plugins, pip entry points (`sas.layers` group), and `~/.sas/plugins/*.py`.

---

## ARGO Skill Pack

Exposes SAS as an ARGO-compatible skill with 12 actions: `sovereignty_check`, `compile_knowledge`, `query_knowledge`, `register_credential`, `list_credentials`, `audit_credentials`, `quant_status`, `substrate_list`, `substrate_boot`, `substrate_destroy`, `payments_pay`, `payments_limit`.

```bash
python -m sas argo invoke --params '{"action": "sovereignty_check"}'
```

---

## Testing

```bash
python -m pytest tests/unit/ tests/integration/ -q \
  --ignore=tests/integration/test_mcp_server.py \
  --ignore=tests/integration/test_rust_extension.py
```

**3,175 tests passing.** Coverage includes: all 8 layers, quant pipeline, real data providers (YFinance/Stooq/Alpaca), plugin system, community registry, ARGO skill pack, full stack integration, runtime authority enforcement, capability-bound substrates, and 35 phases of authority/epistemic graph research.

---

## Architecture

### Source Layout

```
src/sas/
├── __main__.py         # CLI entry point
├── __init__.py
├── argopack.py         # ARGO skill pack
├── capability_bound_database.py  # Database enforcement
├── capability_bound_filesystem.py  # Filesystem enforcement
├── mcp_server.py       # MCP server entry
├── plugins.py          # Plugin system
├── registry.py         # Community registry
├── core/               # Sovereignty scoring, config parsing
│   ├── config.py
│   └── scoring.py
├── layers/             # 8-layer model implementations
│   ├── model_providers.py    # Ollama, OpenAI adapters
│   ├── knowledge.py          # Compile-time knowledge graph
│   ├── auth.py               # Local auth broker + vault
│   ├── payments.py           # Virtual card adapter
│   ├── identity.py           # Email/phone adapters
│   ├── substrate.py          # Compute substrate
│   ├── memory.py             # Short-term memory
│   ├── harness.py            # Harness integration
│   └── registry.py           # Layer registry + scoring
├── quant/              # Quant research pipeline
│   ├── orchestration/            # QuantResearchOrchestrator + gate + researcher
│   ├── engine/__init__.py    # Backtest engine
│   ├── risk/__init__.py      # Risk evaluation
│   ├── policy/__init__.py    # Trading policies
│   ├── strategy/__init__.py  # Strategy definitions
│   ├── reports/__init__.py   # Report generation
│   ├── market/               # Data providers (Alpaca, YFinance, Stooq)
│   ├── broker/               # Broker adapters
│   ├── provenance/           # Provenance graph
│   ├── research/             # Research loop (trial, reflection, temporal)
│   ├── statistics/           # Sharpe, PBO, CSCV, deflated Sharpe
│   ├── evaluation/           # Gate ablation, baseline, gates
│   ├── experiment/           # 40+ experiment modules (epistemic, authority, etc.)
│   ├── runtime_authority_gate.py  # Runtime enforcement
│   ├── capability_verifier.py     # Capability verification
│   ├── capability_bound_*.py      # 5 capability-bound wrappers
│   ├── consequence_executor.py    # Consequence protocol
│   ├── consequence_types.py       # Effect taxonomy
│   ├── worlds/               # Evaluation worlds + runner
│   └── cli_transport.py      # CLI transport enforcement
├── runtime/            # Agent runtime
│   ├── agent_runtime.py      # Core agent loop
│   ├── orchestrator.py       # Runtime orchestrator
│   ├── cli.py                # Runtime CLI
│   ├── capability_bound_agent.py  # Capability-bound runtime
│   └── mcp_server.py         # MCP server
├── dashboard/          # Live dashboard
│   ├── server.py             # FastAPI server
│   ├── report.py             # Report generation
│   └── static/               # Frontend (HTML/JS/CSS)
└── rust_bridge/        # Rust extension bridge
```

### Runtime Authority Enforcement

SAS enforces a strict separation between intelligence and authority:

```
MODEL OUTPUT ≠ AUTHORIZATION
CREDENTIAL ≠ AUTHORIZATION ≠ CAPABILITY
REGISTRATION ≠ AUTHORITY
PERFORMANCE ≠ AUTHORITY
```

The `RuntimeAuthorityGate` is the single enforcement point. Every consequential operation (tool invoke, trade, payment, credential access, subprocess execution, compute execution, filesystem mutation, network mutation, plugin execution) passes through it. The gate is deterministic and cannot be bypassed by the LLM.

### Capability Boundaries

| Boundary | Component | Status |
|----------|-----------|--------|
| Tool execution | `CapabilityBoundAgentRuntime` | ✅ Closed |
| Credential access | `CapabilityBoundAuthBroker` | ✅ Closed |
| Compute substrate | `CapabilityBoundSubstrate` | ✅ Closed |
| Plugin execution | `CapabilityBoundPluginExecutor` | ✅ Closed |
| CLI transport | `cli_transport.py` | ✅ Closed |
| Filesystem | `CapabilityBoundFilesystem` | ✅ Closed |
| Database | `CapabilityBoundDatabase` | ✅ Closed |
| Broker | `CapabilityBoundBroker` | ✅ Closed |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 8-phase development plan |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full architecture reference |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production deployment guide |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Operations runbook |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security model |
| [`docs/SOVEREIGNTY.md`](docs/SOVEREIGNTY.md) | Sovereignty model reference |
| [`docs/LAYERS.md`](docs/LAYERS.md) | Layer model reference |
| [`docs/PLUGINS.md`](docs/PLUGINS.md) | Plugin system reference |
| [`docs/ARGO_SKILL_PACK.md`](docs/ARGO_SKILL_PACK.md) | ARGO skill pack reference |
| [`docs/LAYER_REGISTRY.md`](docs/LAYER_REGISTRY.md) | Layer registry reference |
| [`docs/PACKAGES.md`](docs/PACKAGES.md) | Package structure |
| [`docs/ADAPTER_GAPS.md`](docs/ADAPTER_GAPS.md) | Adapter gap analysis |
| [`docs/demo-report.md`](docs/demo-report.md) | Demo walkthrough report |

---

## Research

Exploratory work on authority/epistemic graph theory lives in [`research/`](research/). It is independent of the shipping product and intentionally excluded from the demo path.

The research directory contains 35+ phases of formal work on:

- **Authority genesis** — Where does authority originate? How is the root represented?
- **Trust anchors** — Multi-domain trust without global authority
- **Authority graphs** — Construction, completeness, and reconciliation
- **Effect boundaries** — What effects can authority actually cover?
- **Temporal authority** — How does authority change over time?
- **Authority path reconstruction** — Can observed effects be traced back to their authorizing path?
- **Graph reconciliation** — Do declared authority graphs match reconstructed paths?
- **Temporal closure** — How do reconciliations survive authority changes?

Each phase includes an implementation module, adversarial test suite, and experimental report.

---

## License

MIT
