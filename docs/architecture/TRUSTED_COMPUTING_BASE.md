# Trusted Computing Base

> **Status:** Initial Analysis
> **Last Updated:** 2026-09-09
> **Phase:** Consequence Boundary Unification

This document identifies the minimum components that must be trusted for authority enforcement in the Sovereign Agent Stack.

---

## TCB Categories

### Authority TCB

Components whose compromise can create unauthorized authority.

| Component | Location | Compromise Impact |
|-----------|----------|-------------------|
| `CapabilityVerifier` | `capability_verifier.py` | Can forge capability verification results |
| `RuntimeAuthorityGate` | `runtime_authority_gate.py` | Can register arbitrary authorizations |
| `AuthorizationArtifact` constructor | `epistemic_governance.py` | Can create forged authorizations |
| `CapabilityMaterializer` | `execution_capability.py` | Can materialize capabilities without valid authorization |
| Governance derivation | `epistemic_governance.py` | Can derive authorization without proper evidence |

### Execution TCB

Components whose compromise can directly create effects despite protocol denial.

| Component | Location | Compromise Impact |
|-----------|----------|-------------------|
| `CapabilityBoundBroker.__broker` | `capability_bound_broker.py` | Can submit orders directly |
| `CapabilityBoundTool.__handler` | `capability_bound_tool.py` | Can invoke tools directly |
| `LocalAuthBroker.__encryptor` | `auth.py` | Can decrypt credentials |
| `LocalAuthBroker._get_conn()` | `auth.py` | Can read credential store |
| `SimulatedBroker.submit_trade()` | `broker/__init__.py` | Can process trades without capability |
| `AlpacaBrokerAdapter.submit_trade()` | `broker/alpaca.py` | Can submit live orders |

### Evidence TCB

Components whose compromise can falsify provenance.

| Component | Location | Compromise Impact |
|-----------|----------|-------------------|
| `ProvenanceGraph` | `provenance/__init__.py` | Can forge provenance records |
| `ExecutionReceipt` constructor | `execution_capability.py` | Can forge execution receipts |
| `ReplayProtectionStore` | `capability_verifier.py` | Can clear replay history |

### Transport

Components that merely carry authority-bearing requests. Compromise does not directly create authority or effects.

| Component | Location | Impact |
|-----------|----------|--------|
| `argopack.py invoke()` | `argopack.py` | Can route requests but not authorize |
| CLI commands | `__main__.py` | Can invoke commands but not authorize |
| MCP server | `mcp_server.py` | Can route requests but not authorize |

---

## TCB Reduction Analysis

### Before Authority Integration

The TCB included:
- Every broker adapter (direct access)
- Every tool handler (direct access)
- Auth broker (credential access)
- Payment adapter (financial access)
- Identity adapter (external API access)
- Substrate (container execution)
- Plugin system (arbitrary code)

### After Authority Integration

The TCB is reduced to:
- `CapabilityVerifier` (verification logic)
- `RuntimeAuthorityGate` (authorization resolution)
- Governance derivation (authorization creation)
- `ReplayProtectionStore` (nonce tracking)
- Name-mangled private attributes in wrappers

The raw executors are no longer in the TCB because they're inaccessible without capability.

---

## Remaining TCB Concerns

### 1. Plugin System

Plugins execute arbitrary Python code. Even if plugin operations are wrapped in capability checks, the plugin code itself has process privileges.

**Mitigation:** Document that plugins are in-process and trusted. For untrusted plugins, process/container isolation is needed.

### 2. Auth Broker

The auth broker holds credentials. Even if credential use is wrapped in capability checks, the encryption key is in memory.

**Mitigation:** The auth broker should only release credentials inside an authorized execution context.

### 3. CLI

The CLI can invoke any command. Even if commands are wrapped in capability checks, the CLI process has user privileges.

**Mitigation:** The CLI should be authority-aware for consequential commands.

### 4. ARGO

ARGO invokes the CLI via subprocess. The subprocess has the same privileges as the parent.

**Mitigation:** ARGO should route through the same authority gate.

---

## TCB Invariant

> **THE TCB MUST BE MINIMAL AND EXPLICIT.**

Every component in the TCB must be:
1. **Identified** — documented in this file
2. **Necessary** — required for authority enforcement
3. **Verified** — tested for correctness
4. **Isolated** — not accessible to untrusted code

---

## Process Restart and Durability

The current TCB is primarily in-memory. For process restart survival:

| Component | Current | Target |
|-----------|---------|--------|
| `ReplayProtectionStore` | In-memory + durable state | Durable store |
| `ProvenanceGraph` | In-memory | Durable store |
| `AuthorizationArtifact` | Registered in gate | Durable store |
| `ExecutionReceipt` | In-memory | Durable store |

The authority state must survive process restart to prevent replay attacks.
