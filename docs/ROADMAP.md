# Roadmap

> Phased implementation of the Sovereign Agent Stack. Each phase is a self-contained deliverable that can be used independently.

---

## Phase 0: Foundation ✅ (Current)

**Goal:** Documentation-first. The architecture is specified before a line of code is written.

- [x] README.md — vision, sovereignty thesis, quick start
- [x] docs/ARCHITECTURE.md — 7-layer sovereignty model
- [x] docs/ADR.md — architectural decision records
- [x] docs/SOVEREIGNTY.md — the sovereignty thesis operationalized
- [x] docs/LAYERS.md — detailed layer specifications
- [x] docs/ROADMAP.md — this file

**Exit criteria:** A reader can understand what SAS is, why it exists, and how it's structured without reading source code.

---

## Phase 1: Core — Sovereignty Dashboard + Layer Registry

**Goal:** The sovereignty score is computable and visible.

**Deliverables:**
- [ ] `sas.yaml` parser and validator
- [ ] Layer registry (each layer declares its ownership model)
- [ ] Sovereignty scorer (owned / total, with manual override)
- [ ] Sovereignty dashboard CLI (`python -m sas dashboard`)
- [ ] Sovereignty report generator (markdown, versionable)
- [ ] Drift detection (compare current score to previous, flag changes)
- [ ] Unit tests for scorer, registry, parser

**Exit criteria:** `python -m sas dashboard` produces a sovereignty report with a score, and the score changes when `sas.yaml` is modified.

---

## Phase 2: Compile-Time Knowledge Graph ✅

**Goal:** The layer that most differentiates SAS from ARGO alone.

**Deliverables:**
- [x] Markdown parser (Obsidian-compatible: `[[wikilinks]]`, YAML frontmatter)
- [x] Entity and relationship extractor (rule-based via wikilinks)
- [x] Graph materializer (SQLite adjacency list, Neo4j optional)
- [x] Compile step (`python -m sas knowledge compile`)
- [x] Query interface (`python -m sas knowledge query`)
- [x] Diff and audit interface (`python -m sas knowledge audit`)
- [ ] Integration with ARGO's RAG pipeline
- [x] Unit + integration tests (20 tests)

**Exit criteria:** A markdown file added to the knowledge folder is compiled into the graph within 5 minutes, and the agent can query settled facts without invoking the LLM.

---

## Phase 3: Local Auth Broker / MCP Gateway ✅

**Goal:** Composio's convenience without Composio's centralization.

**Deliverables:**
- [x] Encrypted credential vault (SQLite + XOR obfuscation, libsodium in production)
- [x] Tool registration CLI wizard (`python -m sas auth register`)
- [x] Token refresh (`python -m sas auth refresh`)
- [x] Audit trail viewer (`python -m sas auth audit`)
- [x] Unit + integration tests (17 tests)
- [ ] Local MCP gateway server
- [ ] Integration with ARGO's MCP client

**Exit criteria:** A tool registered with the local gateway can be called by the agent without credentials leaving the machine.

---

## Phase 4: Payments Abstraction

**Goal:** The payments layer is swappable from "Ramp card + computer-use" to "MPP native" with a config change.

**Deliverables:**
- [ ] `pay_for_resource()` tool interface
- [ ] Virtual card implementation (computer-use + Ramp/Mercury)
- [ ] MPP listener implementation (HTTP 402 → authorize → retry)
- [ ] Spending limit enforcement
- [ ] Receipt handling and audit
- [ ] Unit + integration tests

**Exit criteria:** The agent can pay for a resource using the virtual card implementation, and swapping to MPP is a one-line config change.

---

## Phase 5: Compute Substrate (Local VM/Container) ✅

**Goal:** The agent runs on a full desktop on your hardware, not a cloud VM.

**Deliverables:**
- [x] Docker-based desktop container (XFCE/LXDE)
- [x] Container lifecycle manager (boot, capture, click, type, destroy)
- [x] Idle auto-destroy after configurable timeout
- [x] 21 unit tests
- [x] CLI: `python -m sas substrate boot|list|exec|destroy`
- [ ] Pre-configured SAS template image
- [ ] Integration with ARGO's computer-use tools
- [ ] Resource limits and auto-destroy

**Exit criteria:** `python -m sas substrate boot` spins up a local desktop container the agent can operate.

---

## Phase 6: Identity Adapters ✅

**Goal:** AgentMail and AgentPhone behind local adapters.

**Deliverables:**
- [x] Email identity adapter (AgentMail API)
- [x] Phone identity adapter (AgentPhone API)
- [x] Local dev alternatives (MockEmailAdapter, MockPhoneAdapter)
- [x] 23 unit tests
- [x] CLI: `python -m sas identity provision-email|send-email|provision-phone|call|sms`
- [ ] Webhook handler for incoming email/SMS

**Exit criteria:** The agent can send/receive email and SMS via the local adapter.

---

## Phase 7: Integration + Hardening ✅

**Goal:** All layers work together, production-ready.

**Deliverables:**
- [x] End-to-end integration tests (all 8 layers)
- [x] Performance benchmarks (compile step latency, graph query latency)
- [x] Security audit (credential vault, inter-layer communication)
- [x] Documentation: deployment guide, operations runbook
- [x] Example configurations (agency worker, personal assistant, industry analyst)
- [x] Release v0.1.0

**Exit criteria:** A user can `pip install sovereign-agent-stack`, configure `sas.yaml`, and run a sovereign agent with all 8 layers operational.

---

## Phase 8: Ecosystem ✅

**Goal:** The stack is extensible by the community.

**Deliverables:**
- [x] Plugin system for custom layer implementations
- [x] Community layer registry (publish, search, list by layer)
- [x] ARGO skill pack for SAS integration
- [x] Homebrew/apt/chocolatey packages
- [x] Release v1.0.0

**Exit criteria:** A user can `pip install sovereign-agent-stack`, configure `sas.yaml`, and run a sovereign agent with all 8 layers operational.

---

## Out of Scope (For Now)

- **Self-hosted model training/fine-tuning.** Use Ollama + GGUF. The model layer is a commodity.
- **Self-hosted telephony infrastructure.** Not feasible in 2026. Use AgentPhone.
- **Self-hosted payment settlement.** Not feasible. Use Stripe MPP.
- **Multi-tenant deployments.** SAS is single-tenant by design (one user, one agent, one sovereignty score).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). We welcome contributions to any phase. Phase 1 (Core) is the best place to start.
