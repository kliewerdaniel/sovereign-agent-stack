# Authority Closure Report

> **Date:** 2026-09-09
> **Phase:** Consequence Protocol Closure II
> **Tests:** 1,759 passing

---

## Executive Summary

The Sovereign Agent Stack has achieved **PARTIAL CONSEQUENCE PROTOCOL CLOSURE**.

The formal authority protocol is now the actual execution architecture for:
- Quant trading (reference implementation)
- Agent tool execution
- Credential access
- Compute substrate
- Plugin execution
- CLI transport

The remaining open boundaries are:
- ARGO subprocess authority preservation
- MCP server integration
- Payment adapter
- Identity adapter

---

## Consequential Primitive Inventory

### Closed Boundaries

| # | Boundary | Entry Point | Status | Verification |
|---|----------|-------------|--------|--------------|
| 1 | Quant Trading | `QuantResearchOrchestrator.run()` | ✅ CLOSED | `CapabilityBoundBroker` |
| 2 | Agent Tools | `CapabilityBoundAgentRuntime.run()` | ✅ CLOSED | `CapabilityBoundTool` |
| 3 | Credential Access | `CapabilityBoundAuthBroker.use_credentials()` | ✅ CLOSED | `CapabilityVerifier` |
| 4 | Compute Substrate | `CapabilityBoundSubstrate.execute()` | ✅ CLOSED | `CapabilityVerifier` |
| 5 | Plugin Execution | `CapabilityBoundPluginExecutor.execute_plugin()` | ✅ CLOSED | `CapabilityVerifier` |
| 6 | CLI Transport | `CLIAuthorityResolver.resolve()` | ✅ CLOSED | `CLICommandRegistry` |

### Open Boundaries

| # | Boundary | Entry Point | Risk | Priority |
|---|----------|-------------|------|----------|
| 7 | ARGO | `argopack.py invoke()` | HIGH | Subprocess authority preservation |
| 8 | MCP Server | `MCPServer.call_tool()` | MEDIUM | String capability check |
| 9 | Payments | `VirtualCardAdapter.pay()` | HIGH | Direct financial access |
| 10 | Identity | `AgentMailAdapter.send()` | MEDIUM | External API calls |

---

## Authority Roots

### Legitimate Roots

| Root | Location | Purpose |
|------|----------|---------|
| `AuthorizationArtifact` | `epistemic_governance.py` | Formal authorization |
| `ExecutionCapability` | `execution_capability.py` | Materialized capability |
| `CapabilityVerifier` | `capability_verifier.py` | Canonical verification |

### Retired Roots

| Root | Location | Replacement |
|------|----------|-------------|
| `TradeAuthorization` | `orchestration/gate.py` | `AuthorizationArtifact` |
| `RiskEngine.authorize_trade()` | `risk/__init__.py` | `CapabilityVerifier` |
| Direct `BrokerAdapter` access | `broker/__init__.py` | `CapabilityBoundBroker` |

---

## Authority Derivation Paths

### Canonical Path

```
Sovereign Root (Identity + Policy + Domain)
    ↓
GovernancePolicy
    ↓
AuthorizationArtifact (derivation trace)
    ↓
CapabilityMaterializer
    ↓
ExecutionCapability (constraints + replay guard + executor binding)
    ↓
CapabilityVerifier
    ↓
CapabilityBoundExecutor (Broker / Tool / Auth / Substrate / Plugin)
    ↓
External Effect
    ↓
ExecutionReceipt
    ↓
ProvenanceGraph
```

### Interface Multiplicity (Allowed)

```
CLI ──┐
MCP ──┼──→ ConsequenceRequest → CapabilityVerifier → Executor
ARGO ─┤
Plugin┘
```

All interfaces converge on the same authority semantics.

---

## Adversarial Test Results

### Attacks Attempted

| Attack | Result |
|--------|--------|
| Forged authorization | ✅ REJECT |
| Forged capability | ✅ REJECT |
| Wrong domain | ✅ REJECT |
| Wrong actor | ✅ REJECT |
| Wrong resource | ✅ REJECT |
| Wrong action | ✅ REJECT |
| Expired authorization | ✅ REJECT |
| Revoked authorization | ✅ REJECT |
| Replay attack | ✅ REJECT |
| Scope widening | ✅ REJECT |
| Credential theft | ✅ REJECT |
| Model output → authority | ✅ REJECT |
| Registration → authority | ✅ REJECT |
| Discoverability → authority | ✅ REJECT |
| CLI → authority | ✅ REJECT |
| ARGO → authority | ✅ REJECT |
| MCP → authority | ✅ REJECT |
| Plugin → authority | ✅ REJECT |
| Raw broker access | ✅ REJECT |
| Raw auth broker access | ✅ REJECT |
| Raw substrate access | ✅ REJECT |
| Raw handler access | ✅ REJECT |

### Unauthorized Effects Observed

> **UNAUTHORIZED CONSEQUENTIAL EFFECTS = 0**

---

## Cross-Interface Authority Equivalence

| Interface | Same Operation | Same Authority |
|-----------|----------------|----------------|
| Python API | ✅ | ✅ |
| AgentRuntime | ✅ | ✅ |
| CLI | ✅ | ✅ |
| MCP | ⚠️ Partial | ⚠️ Partial |
| ARGO | ⚠️ Partial | ⚠️ Partial |
| Plugin | ✅ | ✅ |

---

## Crash Consistency

| Crash Point | Reconstruction |
|-------------|----------------|
| Before authorization | ✅ No effect |
| After authorization | ✅ No effect |
| After capability materialization | ✅ No effect |
| Before execution | ✅ No effect |
| During execution | ⚠️ Bounded uncertainty |
| After external effect | ✅ Receipt survives |
| Before receipt persistence | ⚠️ Bounded uncertainty |
| After receipt persistence | ✅ Receipt survives |

---

## Concurrency

| Scenario | Result |
|----------|--------|
| Single-use capability | ✅ Single use |
| Concurrent capability consumption | ✅ Single use |
| Concurrent revocation | ✅ Correct |
| Replay under concurrency | ✅ Rejected |

---

## Trusted Computing Base

### Authority TCB

- `CapabilityVerifier`
- `RuntimeAuthorityGate`
- Governance derivation

### Execution TCB

- Name-mangled private attributes in wrappers
- Raw executors (inaccessible)

### Provenance TCB

- `ProvenanceGraph`
- `ExecutionReceipt`
- `ReplayProtectionStore`

### Transport

- CLI
- MCP
- ARGO

---

## Static Coverage

### Coverage

- Consequential primitives identified: 10
- Consequential primitives closed: 6
- Consequential primitives open: 4

### Limitations

This analysis is **STATIC COVERAGE**, not formal proof. It is heuristic and may miss:
- Dynamic code paths
- Indirect invocations
- Future code additions

---

## Claims Proven by Tests

1. ✅ One canonical authority semantics
2. ✅ Explicit authority roots
3. ✅ No hidden authority roots (in closed boundaries)
4. ✅ Auth cannot create authority
5. ✅ Credentials cannot create authority
6. ✅ Registration cannot create authority
7. ✅ Plugin execution cannot silently create authority
8. ✅ Substrate execution cannot silently create authority
9. ✅ CLI cannot create authority
10. ✅ Capability cannot exceed authorization
11. ✅ Capability cannot cross domains
12. ✅ Capability cannot cross executors without delegation
13. ✅ Capability cannot cross resources
14. ✅ Revocation propagates
15. ✅ Temporal validity propagates
16. ✅ Replay protection survives restart
17. ✅ Single-use capabilities remain single-use under concurrency
18. ✅ Every closed boundary has reconstructible provenance
19. ✅ No receipt can create authority
20. ✅ No evidence can directly create authority
21. ✅ No model output can directly create authority
22. ✅ No credential can directly create authority
23. ✅ No registry membership can directly create authority

## Claims That Remain Architectural Assertions

1. ⚠️ ARGO subprocess authority preservation (not fully tested)
2. ⚠️ MCP cross-interface equivalence (not fully tested)
3. ⚠️ Payment adapter closure (not implemented)
4. ⚠️ Identity adapter closure (not implemented)
5. ⚠️ Formal proof of completeness (not achieved)

---

## Remaining Work

### High Priority

1. **ARGO subprocess authority preservation**
   - Serialize authority across subprocess boundary
   - Verify authority in subprocess
   - Test forged/modified/revoked authority

2. **Payment adapter closure**
   - Implement `CapabilityBoundPayment`
   - Bind capability to amount, destination, currency, account
   - Test payment substitution attacks

3. **Identity adapter closure**
   - Implement `CapabilityBoundIdentity`
   - Bind capability to identity resource and operation
   - Test identity substitution attacks

### Medium Priority

4. **MCP server integration**
   - Replace string capability check with `CapabilityVerifier`
   - Map MCP tools to `ConsequenceRequest`
   - Test cross-interface equivalence

5. **Plugin isolation**
   - Subprocess execution for untrusted plugins
   - Container isolation for high-risk plugins
   - IPC communication

6. **Formal verification**
   - Model checking of authority graph
   - Proof of completeness
   - Proof of non-interference

---

## Conclusion

The Sovereign Agent Stack has achieved **PARTIAL CONSEQUENCE PROTOCOL CLOSURE**.

The formal authority protocol is now the actual execution architecture for the majority of consequential boundaries. The remaining open boundaries (ARGO, MCP, payments, identity) can be migrated using the same pattern.

The key architectural property has been established:

> **ONE AUTHORITY GRAPH. MANY INTERFACES. MANY EFFECT TYPES. ZERO UNDECLARED CONSEQUENTIAL ESCAPES (in closed boundaries).**

The system is ready for the next milestone: a **real-world non-quant workload** that exercises the entire machine—agent proposal → epistemic evidence → governance → authorization → capabilities → credentials → compute → external effect → provenance.

---

## Test Count

- **Total tests:** 1,759
- **Unit tests:** ~1,600
- **Integration tests:** ~100
- **Adversarial tests:** ~59

### New Tests This Phase

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_capability_bound_auth.py` | 9 | Auth broker boundary |
| `test_capability_bound_substrate.py` | 6 | Substrate boundary |
| `test_full_stack_authority.py` | 17 | Full stack red team |
| `test_consequence_boundary.py` | 27 | Consequence boundary |
