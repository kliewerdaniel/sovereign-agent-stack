# Authority Roots

> **Status:** Initial Audit
> **Last Updated:** 2026-09-09
> **Phase:** Consequence Boundary Unification

This document identifies every actual authority root in the Sovereign Agent Stack. An authority root is any component where authority enters the system — not merely classes named "Authorization."

---

## Authority Root Taxonomy

### 1. Formal Protocol Roots

These are the intentional authority roots established by the protocol.

| Root | Location | Creator | Authenticator | Policy | Domain | Provenance |
|------|----------|---------|---------------|--------|--------|------------|
| `AuthorizationArtifact` | `epistemic_governance.py` | Governance derivation | Derivation trace | `GovernancePolicy` | `ProtocolDomain` | `provenance_hash` |
| `ExecutionCapability` | `execution_capability.py` | `CapabilityMaterializer` | `authorization_ref` | Scope constraints | `domain_id` | `authority_root` |

### 2. Runtime Roots

These are the runtime components that participate in authority enforcement.

| Root | Location | Purpose | Derives From |
|------|----------|---------|--------------|
| `RuntimeAuthorityGate` | `runtime_authority_gate.py` | Authorization resolution | Registered `AuthorizationArtifact`s |
| `CapabilityVerifier` | `capability_verifier.py` | Canonical capability verification | `ProtocolDomain` |
| `CapabilityBoundBroker` | `capability_bound_broker.py` | Bounded broker execution | `CapabilityVerifier` |
| `CapabilityBoundTool` | `capability_bound_tool.py` | Bounded tool execution | `CapabilityVerifier` |
| `ReplayProtectionStore` | `capability_verifier.py` | Durable nonce tracking | None (operational) |

### 3. Retired Roots

These were authority roots in the previous architecture. They are no longer independent authority sources.

| Root | Location | Status | Replacement |
|------|----------|--------|-------------|
| `TradeAuthorization` | `orchestration/gate.py` | **RETIRED** | `AuthorizationArtifact` + `RuntimeAuthorityGate` |
| `RiskEngine.authorize_trade()` | `risk/__init__.py` | **RETIRED** | `CapabilityVerifier` |
| `BrokerAdapter.submit_trade()` (direct) | `broker/__init__.py` | **WRAPPED** | `CapabilityBoundBroker` |

### 4. Potential Hidden Roots

These are components that may accidentally function as authority roots. Each must be investigated.

| Component | Location | Risk | Investigation |
|-----------|----------|------|---------------|
| `PluginRegistry.register()` | `plugins.py` | Plugin registration may create authority | Audit plugin lifecycle |
| `LocalAuthBroker.register_tool()` | `auth.py` | Credential registration may create authority | Audit credential use |
| `CapabilityRegistry.grant()` | `rust_bridge/capabilities.py` | String capability grant may create authority | Audit capability semantics |
| `LocalAuthBroker.get_credentials()` | `auth.py` | Credential retrieval may create authority | Audit credential access |
| `argopack.py invoke()` | `argopack.py` | CLI subprocess may create authority | Audit ARGO boundary |
| CLI commands | `__main__.py` | Direct commands may create authority | Audit CLI boundary |

---

## Authority Flow Analysis

### Formal Protocol Flow

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
CapabilityBoundExecutor (Broker / Tool / Payment / Identity / Substrate)
    ↓
External Effect
    ↓
ExecutionReceipt
    ↓
ProvenanceGraph
```

### Retired Flow (No Longer Authoritative)

```
TradeAuthorization  ← NOT an authority root
    ↓
BrokerAdapter.submit_trade()  ← NOT an independent authority path
```

---

## Root Properties

Each authority root must satisfy:

| Property | Formal Protocol | Runtime | Retired |
|----------|-----------------|---------|---------|
| Controlled by protocol | ✅ | ✅ | N/A |
| Authenticated | ✅ | ✅ | N/A |
| Policy-constrained | ✅ | ✅ | N/A |
| Domain-owned | ✅ | ✅ | N/A |
| Provenance-established | ✅ | ✅ | N/A |
| Replay-protected | ✅ | ✅ | N/A |
| Forgery-resistant | ✅ | ✅ | N/A |
| Substitution-resistant | ✅ | ✅ | N/A |
| Revocable | ✅ | ✅ | N/A |
| Process-death survival | ✅ | ✅ | N/A |

---

## Critical Invariant

> **AUTHORITY MUST NOT BE ABLE TO AUTHORIZE ITSELF.**

This means:
- `AuthorizationArtifact` creation requires governance derivation
- `ExecutionCapability` materialization requires `AuthorizationArtifact`
- `CapabilityVerifier` requires `ExecutionCapability`
- No component can create authority without a parent authority

---

## Open Investigations

1. **Plugin Registration:** Does registering a plugin create authority? If plugins can invoke operations, then yes.
2. **Credential Registration:** Does registering a credential create authority? If credentials enable operations, then yes.
3. **String Capability Grants:** Does `CapabilityRegistry.grant("execute_trade")` create authority? If so, this is a hidden root.
4. **CLI Commands:** Do any CLI commands create authority without formal authorization?

---

## Recommendation

Every hidden authority root must be either:
1. **Eliminated** — removed as an independent authority source
2. **Integrated** — connected to the formal protocol
3. **Documented** — explicitly classified as a known trust boundary
