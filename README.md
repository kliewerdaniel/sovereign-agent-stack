# Sovereign Agent Stack (SAS)

> *"The model becoming free doesn't mean intelligence becomes sovereign. It just relocates the rent."*
> — Daniel Kliewer, [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack)

**SAS is a local-first, compile-time AI agent framework.** It implements an 8-layer sovereignty model that scores how much of your agent infrastructure you actually own vs. rent.

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

## Quick Start

```bash
pip install sovereign-agent-stack

# Initialize config
python -m sas init --output sas.yaml

# Run sovereignty audit
python -m sas dashboard --config examples/agency-worker/sas.yaml --verbose

# Or JSON output
python -m sas dashboard --config examples/agency-worker/sas.yaml --cache ~/.sas --json
```

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
```

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

---

## Quant Research Pipeline

Self-contained professional evaluation worlds. Each QuantWorld is: data + documents + portfolio + strategies + policies + agents + tools + task + rubric + gold output.

**Portfolio Intelligence World** (`qw-portfolio-intel-001`): 10 tech stocks, $500K portfolio, 5 risk policies, 3 strategies, 15 rubric criteria — all passing.

```
QuantWorld + Task + Rubric
         │
         ▼
  QuantToolbox (22 tools: market data, computation, backtest, risk, report, provenance)
         │
         ▼
  ModelAdapter.run_loop()  ← ReAct: model calls tools → records trajectory + artifacts
         │
         ▼
  RunEvaluator.evaluate()  ← rubric criteria + sovereignty checks + provenance
         │
         ▼
  RunEvaluation: Pass@1, mean_score, sovereignty_passed
```

### Real Data Providers

| Provider | Endpoint | Cache |
|----------|----------|-------|
| YFinance | `yfinance.Ticker.history()` | `~/.sas/yf_cache/` |
| Stooq | Free CSV endpoint | `~/.sas/stooq_cache/` |
| Alpaca | Data API v2 (paper/live) | `~/.sas/alpaca_cache/` |

All providers implement `MarketDataProvider`: `get_prices(symbol, start, end)`, `validate()`, `source_info()`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLI: dashboard | init | knowledge | auth | payments | substrate | ...  │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer Registry (single source of truth for 8 sovereignty layers)        │
├─────────────────────────────────────────────────────────────────────────┤
│  Layers: model | harness | compute | identity | memory | knowledge |    │
│          auth | payments                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  Quant: engine | strategy | backtest | risk | broker | market |         │
│         provenance | reports | lifecycle | agents | knowledge            │
├─────────────────────────────────────────────────────────────────────────┤
│  Runtime: AgentRuntime | FleetCoordinator | Orchestrator                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Ecosystem: Plugin system | Community registry | ARGO skill pack         │
└─────────────────────────────────────────────────────────────────────────┘
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

Example configs: [`examples/agency-worker/`](examples/agency-worker/) (6/6 owned), [`examples/personal-assistant/`](examples/personal-assistant/), [`examples/industry-analyst/`](examples/industry-analyst/).

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

**445 tests passing.** Coverage includes: all 8 layers, quant pipeline (15/15 criteria), real data providers (YFinance/Stooq/Alpaca), plugin system, community registry, ARGO skill pack, full stack integration.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 8-phase development plan |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production deployment guide |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Operations runbook |

---

## License

MIT
