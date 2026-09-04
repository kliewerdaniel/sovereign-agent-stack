# Sovereign Agent Stack (SAS) v0.1.0

> *"The model becoming free doesn't mean intelligence becomes sovereign. It just relocates the rent."*
> — Daniel Kliewer, [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack)

Sovereign Agent Stack is a **local-first, compile-time AI agent framework** that implements the 7-layer sovereignty model from *The Rented Sovereign*. It takes the critique — that the $5K/month agency stack rents 7 of 9 layers — and inverts it: **6 of 8 layers are owned by default**, with the remaining two abstracted behind swappable adapters.

## The Sovereignty Thesis

Every agentic AI system can be decomposed into 8 independent layers:

| # | Layer | Typical Agency Stack | Default Here |
|---|-------|---------------------|--------------|
| 1 | Model | API provider (rented) | Ollama local + API fallback |
| 2 | Harness | Hermes/OpenClaw (MIT, but cloud-deployed) | ARGO-based, self-hosted |
| 3 | Compute Substrate | Orgo cloud VM (rented) | Local Docker desktop |
| 4 | Identity | AgentMail/AgentPhone (rented) | APIs behind local adapter |
| 5 | Short-term Memory | Honcho cloud (rented) | Local RAG + session memory |
| 6 | Long-term Knowledge | Obsidian (accidental) | **Compile-time knowledge graph** |
| 7 | Auth | Composio hosted broker (rented) | **Local MCP gateway + encrypted vault** |
| 8 | Payments | Ramp card + computer-use (stopgap) | **Abstracted: current → MPP future** |

**Default sovereignty score: 6/8 owned** vs. 2/9 in the typical agency stack.

## What's in v0.1.0

- **7-layer sovereignty model** — formalized in `docs/ARCHITECTURE.md`
- **Compile-time knowledge graph** — the Obsidian layer, done intentionally (not accidentally)
- **Self-hosted auth broker** — Composio's convenience without Composio's centralization
- **Payments abstraction** — swap from "Ramp card + computer-use" to Stripe MPP with a config change
- **Compute substrate** — local Docker container lifecycle manager
- **Identity adapters** — AgentMail + AgentPhone with mock dev alternatives
- **Sovereignty dashboard** — a living, scored audit of which layers you own vs. rent
- **96 unit tests + 23 integration tests + 14 benchmarks**
- **3 example configurations** — agency worker, personal assistant, industry analyst

## Quick Start

```bash
# Clone
git clone https://github.com/kliewerdaniel/sovereign-agent-stack.git
cd sovereign-agent-stack

# Install
pip install -e ".[dev]"

# Initialize a template config
python -m sas init --output sas.yaml

# Run sovereignty audit
python -m sas dashboard --config sas.yaml --verbose

# Or use a pre-configured example
python -m sas dashboard --config examples/agency-worker/sas.yaml --verbose
```

## Example Configurations

- [Agency Worker](examples/agency-worker/README.md) — 6/6 owned, fully sovereign
- [Personal Assistant](examples/personal-assistant/README.md) — 3/6 owned, balanced
- [Industry Analyst](examples/industry-analyst/README.md) — 5/6 owned, research-first

## CLI Usage

```bash
# Initialize a template sas.yaml
python -m sas init --output sas.yaml

# Run sovereignty dashboard (markdown)
python -m sas dashboard --config sas.yaml --verbose

# Run sovereignty dashboard (JSON)
python -m sas dashboard --config sas.yaml --json
```

## Scoring

The sovereignty score measures how many layers you **own** (local, compile-time, inspectable) vs. **rent** (hosted, runtime, re-derived).

| Score | Verdict | Meaning |
|-------|---------|---------|
| >= 87.5% | Fully Sovereign | 7-8/8 layers owned |
| >= 62.5% | Sovereign (target) | 5-6/8 layers owned |
| >= 37.5% | Partially sovereign | 3-4/8 layers owned |
| < 37.5% | Rented | 0-2/8 layers owned |

Identity and Payments are **unavoidably rented** (can't self-host phone/MX records or payment settlement) and excluded from the denominator.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full 7-layer model.

```
┌─────────────────────────────────────────┐
│  Model (Ollama local + API fallback)    │
├─────────────────────────────────────────┤
│  Harness (ARGO-based, self-hosted)      │
├─────────────────────────────────────────┤
│  Compute (Local Docker desktop)         │
├─────────────────────────────────────────┤
│  Identity (AgentMail/Phone adapters)    │
├─────────────────────────────────────────┤
│  Memory (Local RAG + session context)   │
├─────────────────────────────────────────┤
│  Knowledge (Compile-time graph)         │
├─────────────────────────────────────────┤
│  Auth (Local MCP gateway + vault)       │
├─────────────────────────────────────────┤
│  Payments (Virtual card / MPP adapter)  │
└─────────────────────────────────────────┘
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/integration/ -v

# Run benchmarks
python -m pytest tests/benchmarks/ -v
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — 7-layer sovereignty model
- [ADR](docs/ADR.md) — Architectural decision records
- [Sovereignty](docs/SOVEREIGNTY.md) — The sovereignty thesis operationalized
- [Layers](docs/LAYERS.md) — Detailed layer specifications
- [Roadmap](docs/ROADMAP.md) — What's built and what's next
- [Deployment](docs/DEPLOYMENT.md) — Production deployment guide
- [Runbook](docs/RUNBOOK.md) — Operations and incident response
- [Security](docs/SECURITY.md) — Security audit and hardening roadmap

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full roadmap. Upcoming:

- **Phase 8: Ecosystem** — Plugin system, community layer registry, ARGO skill pack
- **v1.0.0** — Multi-user support, knowledge graph signing, HSM for payment keys

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). We welcome contributions to any phase.

## License

MIT — because the harness should be free, and the sovereignty should be yours.
