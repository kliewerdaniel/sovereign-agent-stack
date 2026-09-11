# Authority Escape Graph V2 — Reconstructed from Implementation

> **Status:** Phase 1 Audit Complete
> **Last Updated:** 2026-09-09
> **Phase:** Consequence Protocol Closure II

This graph was reconstructed from actual code paths, not documentation. Every entry point is traced from actual implementation.

---

## Consequential Primitive Inventory

### 1. Quant Trading
- **Entry:** `QuantResearchOrchestrator.run()` → `CapabilityBoundBroker.submit_order()` → `SimulatedBroker.submit_trade()`
- **Status:** ✅ AUTHORITY-CLOSED
- **Verification:** `CapabilityVerifier` + `ExecutionCapability` + `AuthorizationArtifact`

### 2. Agent Tool Execution
- **Entry:** `CapabilityBoundAgentRuntime.run()` → `CapabilityBoundTool.invoke()` → handler
- **Status:** ✅ AUTHORITY-CLOSED
- **Verification:** `CapabilityVerifier` + `ExecutionCapability`

### 3. Credential Access
- **Entry:** `CapabilityBoundAuthBroker.use_credentials()` → `LocalAuthBroker.call()`
- **Status:** ✅ AUTHORITY-CLOSED
- **Verification:** `CapabilityVerifier` + `ExecutionCapability`

### 4. Compute Substrate
- **Entry:** `CapabilityBoundSubstrate.execute()` → `LocalDockerSubstrate.execute()`
- **Status:** ✅ AUTHORITY-CLOSED
- **Verification:** `CapabilityVerifier` + `ExecutionCapability`

### 5. Plugin System
- **Entry:** `PluginRegistry.discover()` → `_discover_local_plugins()` → `exec_module()`
- **Status:** ❌ AUTHORITY ESCAPE
- **Risk:** Arbitrary Python execution with full process privileges
- **Attack surface:** `~/.sas/plugins/*.py`, pip entry points

### 6. MCP Server
- **Entry:** `MCPServer.call_tool()` → `_execute_tool()` → tool handler
- **Status:** ❌ AUTHORITY ESCAPE
- **Risk:** String-based capability check (`CapabilityRegistry.is_granted()`)
- **Attack surface:** MCP protocol, tool handlers

### 7. CLI
- **Entry:** `python -m sas <command>` → direct function calls
- **Status:** ❌ AUTHORITY ESCAPE
- **Risk:** Direct invocation of consequential operations
- **Attack surface:** `__main__.py` commands

### 8. ARGO
- **Entry:** `argopack.py invoke()` → `subprocess.run([sys.executable, "-m", "sas", ...])`
- **Status:** ❌ AUTHORITY ESCAPE
- **Risk:** Subprocess bypass of authority
- **Attack surface:** ARGO actions

### 9. Payments
- **Entry:** `VirtualCardAdapter.pay()` / `MPPAdapter.pay()`
- **Status:** ❌ AUTHORITY ESCAPE
- **Risk:** Direct financial transactions
- **Attack surface:** Payment adapters

### 10. Identity
- **Entry:** `AgentMailAdapter.send()` / `AgentPhoneAdapter.send()` / etc.
- **Status:** ❌ AUTHORITY ESCAPE
- **Risk:** External API calls, identity mutation
- **Attack surface:** Identity adapters

### 11. Auth Broker (raw)
- **Entry:** `LocalAuthBroker.get_credentials()` → credential material
- **Status:** ❌ AUTHORITY ESCAPE (raw), ✅ (via CapabilityBoundAuthBroker)
- **Risk:** Direct credential access
- **Attack surface:** Auth broker protocol

---

## Authority Node Classification

| Node | Classification | Status |
|------|----------------|--------|
| `AuthorizationArtifact` | AUTHORITY_ROOT | ✅ Canonical |
| `ExecutionCapability` | CAPABILITY_MATERIALIZATION | ✅ Canonical |
| `CapabilityVerifier` | AUTHORITY_VERIFICATION | ✅ Canonical |
| `CapabilityBoundBroker` | CONSEQUENCE_BOUNDARY | ✅ Closed |
| `CapabilityBoundTool` | CONSEQUENCE_BOUNDARY | ✅ Closed |
| `CapabilityBoundAuthBroker` | CONSEQUENCE_BOUNDARY | ✅ Closed |
| `CapabilityBoundSubstrate` | CONSEQUENCE_BOUNDARY | ✅ Closed |
| `CapabilityBoundAgentRuntime` | CONSEQUENCE_BOUNDARY | ✅ Closed |
| `PluginRegistry` | AUTHORITY_MANAGEMENT | ❌ ESCAPE |
| `MCPServer` | TRANSPORT | ❌ ESCAPE |
| `argopack.py` | TRANSPORT | ❌ ESCAPE |
| CLI commands | TRANSPORT | ❌ ESCAPE |
| `VirtualCardAdapter` | RAW_PRIMITIVE | ❌ ESCAPE |
| `AgentMailAdapter` | RAW_PRIMITIVE | ❌ ESCAPE |

---

## Attack Paths

### Plugin Escape
```
Plugin code (arbitrary Python)
    ↓
Import broker adapter
    ↓
Call submit_trade() directly
    ↓
External effect (bypasses CapabilityBoundBroker)
```

### CLI Escape
```
CLI command: sas quant auto-research
    ↓
Direct instantiation of QuantResearchOrchestrator
    ↓
orchestrator.run()
    ↓
Broker submission (bypasses authority if not wired)
```

### ARGO Escape
```
ARGO action: quant_status
    ↓
subprocess.run([sys.executable, "-m", "sas", ...])
    ↓
CLI command execution
    ↓
Direct effect (bypasses authority)
```

### MCP Escape
```
MCP tool call: pay_for_resource
    ↓
MCPServer.call_tool()
    ↓
String capability check: CapabilityRegistry.is_granted("process_payments")
    ↓
Tool handler execution
    ↓
External effect (weak authority)
```

---

## Closure Priority

| Priority | Boundary | Risk | Approach |
|----------|----------|------|----------|
| 1 | Plugin System | CRITICAL | Authority control + isolation model |
| 2 | CLI | HIGH | Transport, not authority |
| 3 | ARGO | HIGH | Authority preservation across subprocess |
| 4 | MCP | MEDIUM | Converge on canonical protocol |
| 5 | Payments | HIGH | Capability-bound execution |
| 6 | Identity | MEDIUM | Capability-bound execution |
