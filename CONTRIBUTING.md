# Contributing to Sovereign Agent Stack

Welcome. This is an early-stage project implementing the 7-layer sovereignty model from [The Rented Sovereign](https://www.danielkliewer.com/blog/2026-09-04-the-rented-sovereign-agent-agency-stack).

## How to Contribute

### 1. Pick a Phase

See [ROADMAP.md](docs/ROADMAP.md). Phase 1 (Core — Sovereignty Dashboard + Layer Registry) is the best place to start. Each phase is self-contained.

### 2. Read the Architecture

Before writing code, read:
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — the 7-layer model
- [LAYERS.md](docs/LAYERS.md) — detailed layer specifications
- [ADR.md](docs/ADR.md) — architectural decisions and their rationale

### 3. Open an Issue First

For non-trivial changes, open an issue describing:
- Which layer(s) you're working on
- What you plan to build
- How it affects the sovereignty score

This avoids duplicated work and keeps the architecture coherent.

### 4. Code Style

- Python 3.11+
- Type hints everywhere (this is a sovereignty-critical system — types are documentation)
- `ruff` for formatting, `mypy` for type checking
- Tests for every layer (unit + integration)

### 5. Commit Convention

```
feat(layer-6): add markdown parser for compile-time knowledge graph
fix(dashboard): correct sovereignty score when layer is manually override
docs(adr): add ADR-007 for plugin system design
test(auth-broker): add integration tests for token refresh
```

### 6. Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Write code + tests
4. Ensure `pytest` passes
5. Ensure `mypy src/` passes
6. Open a PR with a clear description of what changed and why
7. Link any related issues

### 7. What We Need Most

- **Phase 1 (Core):** Sovereignty dashboard, layer registry, `sas.yaml` parser
- **Phase 2 (Knowledge Graph):** Markdown parser, entity extraction, graph materialization
- **Phase 3 (Auth Broker):** Local MCP gateway, encrypted vault
- **Tests:** The sovereignty score logic needs thorough testing — it's the core value prop
- **Documentation:** Deployment guide, operations runbook

## Code of Conduct

Be constructive. The sovereignty thesis is a critique, not a crusade. We're building tools, not fighting wars.

## License

By contributing, you agree your contributions will be licensed under the MIT license.
