# Sovereign Agent Stack (SAS)

> *"The model becoming free doesn't mean intelligence becomes sovereign. It just relocates the rent."*
> — Daniel Kliewer, [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack)

Sovereign Agent Stack is a **local-first, compile-time AI agent framework** that implements the 7-layer sovereignty model from *The Rented Sovereign*. It takes the critique — that the $5K/month agency stack rents 7 of 9 layers — and inverts it: **6 of 8 layers are owned by default**, with the remaining two abstracted behind swappable adapters.

## The Sovereignty Thesis

Every agentic AI system can be decomposed into 8 independent layers:

| # | Layer | Typical Agency Stack | Default Here |
|---|-------|---------------------|--------------|
| 1 | Model | API provider (rented) | Ollama local + API fallback |
| 2 | Harness | Hermes/OpenClaw (MIT, but cloud-deployed) | ARGO-based, self-hosted |
| 3 | Compute Substrate | Orgo cloud VM (rented) | Local VM/Container substrate |
| 4 | Identity | AgentMail/AgentPhone (rented) | APIs behind local adapter |
| 5 | Short-term Memory | Honcho cloud (rented) | Local RAG + session memory |
| 6 | Long-term Knowledge | Obsidian (accidental) | **Compile-time knowledge graph** |
| 7 | Auth | Composio hosted broker (rented) | **Local MCP gateway + encrypted vault** |
| 8 | Payments | Ramp card + computer-use (stopgap) | **Abstracted: current → MPP future** |

**Default sovereignty score: 6/8 owned** vs. 2/9 in the typical agency stack.

## What This Repo Contains

- **7-layer sovereignty model** — formalized in `docs/ARCHITECTURE.md`
- **Compile-time knowledge graph** — the Obsidian layer, done intentionally (not accidentally)
- **Self-hosted auth broker** — Composio's convenience without Composio's centralization
- **Payments abstraction** — swap from "Ramp card + computer-use" to Stripe MPP with a config change
- **Sovereignty dashboard** — a living, scored audit of which layers you own vs. rent
- **ADR records** — every architectural decision documented with context and consequences
- **Layer specifications** — detailed interface docs for each of the 8 layers

## Quick Start

```bash
# Clone
git clone https://github.com/kliewerdaniel/sovereign-agent-stack.git
cd sovereign-agent-stack

# Install
pip install -e ".[dev]"

# Run sovereignty audit
python -m sas dashboard

# Run a sovereign agent
python -m sas run examples/agency-worker/sas.yaml
```

## Project Status

Early stages — see [ROADMAP.md](docs/ROADMAP.md) for what's built, what's next, and what's aspirational.

## License

MIT — because the harness should be free, and the sovereignty should be yours.
