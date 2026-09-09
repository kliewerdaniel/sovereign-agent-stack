# Consequence Boundary Matrix

> **Status:** Post-Integration Audit
> **Last Updated:** 2026-09-09
> **Phase:** Runtime Authority Closure

This matrix enumerates every consequential runtime boundary and its authority properties. A boundary is "sovereign" only if it can answer all six authority questions.

---

## Matrix

| Boundary | Consequence | Authority Source | Capability | Executor | Receipt | Durable Provenance |
|----------|-------------|------------------|------------|----------|---------|-------------------|
| **Quant Orchestrator → Broker** | Order submission | `AuthorizationArtifact` from `ResearchDecision` | `ExecutionCapability` | `CapabilityBoundBroker` | `ExecutionReceipt` | `ProvenanceGraph` |
| **Agent Runtime → Tool** | Tool execution | **NONE** | **NONE** | Raw handler | **NONE** | **NONE** |
| **ARGO → CLI** | SAS command | **NONE** | **NONE** | Subprocess | **NONE** | **NONE** |
| **Plugin System** | `exec_module` | **NONE** | **NONE** | Python interpreter | **NONE** | **NONE** |
| **MCP Server** | Tool execution | `CapabilityRegistry` (string) | String capability | MCP handler | **NONE** | **NONE** |
| **CLI** | Any operation | **NONE** | **NONE** | Direct call | **NONE** | **NONE** |
| **Payment Adapter** | Financial tx | **NONE** | **NONE** | Adapter | **NONE** | **NONE** |
| **Identity Adapter** | External API | **NONE** | **NONE** | Adapter | **NONE** | **NONE** |
| **Substrate** | Container exec | **NONE** | **NONE** | Docker | **NONE** | **NONE** |
| **Auth Broker** | Credential use | **NONE** | **NONE** | HTTP client | **NONE** | **NONE** |

---

## Authority Questions

For each boundary, the six authority questions:

### 1. Quant Orchestrator → Broker ✅

| Question | Answer |
|----------|--------|
| Who can invoke? | `QuantResearchOrchestrator.run()` |
| What authorizes? | `AuthorizationArtifact` |
| Where resolved? | `_derive_authorization_from_research()` |
| Where materialized? | `_materialize_capability()` |
| Where verified? | `CapabilityBoundBroker.submit_order()` |
| What resource bound? | Specific symbol in `ExecutorBinding` |
| What executor? | `CapabilityBoundBroker` |
| Where receipt? | `ExecutionReceipt` in broker |
| Where provenance? | `ProvenanceGraph` |
| Direct invocation? | No — raw broker is name-mangled |
| Executor substitution? | No — capability bound to executor |
| Resource substitution? | No — symbol-checked |
| Replay possible? | No — single-use nonce + replay store |
| Temporal extension? | No — expiration enforced |
| Domain crossing? | No — domain-checked |
| Post-restart? | Replay protection is durable |
| Reconstructible? | Yes — from `ProvenanceGraph` |

### 2. Agent Runtime → Tool ❌

| Question | Answer |
|----------|--------|
| Who can invoke? | Any code with `AgentRuntime` reference |
| What authorizes? | **NONE** |
| Where resolved? | N/A |
| Where materialized? | N/A |
| Where verified? | N/A |
| What resource bound? | N/A |
| What executor? | Raw handler |
| Where receipt? | N/A |
| Where provenance? | N/A |
| Direct invocation? | **YES** — `tool_entry["handler"](**args)` |
| Status | **BYPASS** |

### 3. ARGO → CLI ❌

| Question | Answer |
|----------|--------|
| Who can invoke? | Any ARGO agent |
| What authorizes? | **NONE** |
| Where resolved? | N/A |
| Where materialized? | N/A |
| Where verified? | N/A |
| What resource bound? | N/A |
| What executor? | Subprocess |
| Where receipt? | N/A |
| Where provenance? | N/A |
| Direct invocation? | **YES** — `subprocess.run([sys.executable, "-m", "sas", ...])` |
| Status | **BYPASS** |

### 4. Plugin System ❌

| Question | Answer |
|----------|--------|
| Who can invoke? | Any file in `~/.sas/plugins/*.py` |
| What authorizes? | **NONE** |
| Where resolved? | N/A |
| Where materialized? | N/A |
| Where verified? | N/A |
| What resource bound? | N/A |
| What executor? | Python interpreter |
| Where receipt? | N/A |
| Where provenance? | N/A |
| Direct invocation? | **YES** — `exec_module` |
| Status | **CRITICAL BYPASS** |

---

## Classification

| Boundary | Classification |
|----------|----------------|
| Quant Orchestrator → Broker | ✅ SOVEREIGN |
| Agent Runtime → Tool | ❌ BYPASS |
| ARGO → CLI | ❌ BYPASS |
| Plugin System | ❌ CRITICAL BYPASS |
| MCP Server | ⚠️ WEAK |
| CLI | ❌ BYPASS |
| Payment Adapter | ❌ BYPASS |
| Identity Adapter | ❌ BYPASS |
| Substrate | ❌ BYPASS |
| Auth Broker | ❌ BYPASS |

---

## Closure Requirements

To make a boundary sovereign, it must:

1. **Resolve authority** from a formal `AuthorizationArtifact`
2. **Materialize capability** as an `ExecutionCapability`
3. **Verify capability** before execution (using `CapabilityVerifier`)
4. **Bind to specific resource** (symbol, account, etc.)
5. **Generate receipt** (`ExecutionReceipt`)
6. **Persist provenance** (`ProvenanceGraph`)
7. **Prevent direct invocation** of the underlying executor
8. **Enforce replay protection** (single-use nonces)
9. **Enforce temporal validity** (expiration)
10. **Enforce domain binding** (no cross-domain use)

---

## Progress

| Boundary | Current | Target |
|----------|---------|--------|
| Quant Orchestrator → Broker | ✅ 10/10 | 10/10 |
| Agent Runtime → Tool | 0/10 | 10/10 |
| ARGO → CLI | 0/10 | 10/10 |
| Plugin System | 0/10 | 10/10 |
| MCP Server | 2/10 | 10/10 |
| CLI | 0/10 | 10/10 |
| Payment Adapter | 0/10 | 10/10 |
| Identity Adapter | 0/10 | 10/10 |
| Substrate | 0/10 | 10/10 |
| Auth Broker | 0/10 | 10/10 |
