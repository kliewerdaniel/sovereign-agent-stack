# Consequence Protocol

> **Status:** Active
> **Last Updated:** 2026-09-09
> **Phase:** Consequence Protocol Closure II

This document defines the canonical consequence protocol for the Sovereign Agent Stack. It is the authoritative architectural document for authority, execution, and evidence.

---

## Central Machine

The Sovereign Agent Stack is a **protocol machine** in which intelligence, authority, execution, and evidence are separate state spaces connected only by explicit derivations.

### State Transition Chain

```
MODEL
    ↓
PROPOSAL
    ↓
EXPERIMENT
    ↓
EVIDENCE
    ↓
EPISTEMIC STATE
    ↓
GOVERNANCE
    ↓
AUTHORIZATION
    ↓
CAPABILITY
    ↓
CONSEQUENCE REQUEST
    ↓
VERIFICATION
    ↓
EXECUTION
    ↓
EFFECT
    ↓
RECEIPT
    ↓
PROVENANCE
```

### State Creators

| State | Created By |
|-------|------------|
| Proposal | Model |
| Evidence | Experiment |
| Epistemic State | Epistemic state machine |
| Authorization | Governance derivation |
| Capability | Capability materializer |
| Consequence Request | Any interface (CLI, MCP, ARGO, Plugin, AgentRuntime) |
| Verification | Capability verifier |
| Effect | Executor |
| Receipt | Executor boundary |
| Provenance | Provenance recorder |

### Critical Invariant

> **NO LOWER LAYER MAY CREATE AUTHORITY FOR ITSELF.**

This means:
- Model output ≠ authority
- Credential possession ≠ authority
- Registration ≠ authority
- Discoverability ≠ authority
- CLI invocation ≠ authority
- ARGO invocation ≠ authority
- MCP invocation ≠ authority
- Plugin execution ≠ authority
- Consensus ≠ authority
- Confidence ≠ authority
- Sharpe ratio ≠ authority

---

## Authority Graph

```
                    Sovereign Authority Roots
                              │
                              ▼
                    AuthorizationArtifact
                              │
                              ▼
                    CapabilityMaterializer
                              │
                              ▼
                      ExecutionCapability
                              │
                              ▼
                     CapabilityVerifier
                              │
                              ▼
                    ConsequenceRequest
                              │
                              ▼
                     ConsequenceExecutor
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
             CLI             MCP             ARGO
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                     Consequential Effect
                              │
                              ▼
                    ExecutionReceipt
                              │
                              ▼
                         Provenance
```

---

## Consequence Taxonomy

### External-Consequential

| Type | Description |
|------|-------------|
| TOOL_INVOKE | Invocation of a registered tool handler |
| TRADE | Financial order submission to a broker |
| PAYMENT | Financial transaction |
| IDENTITY_MUTATION | Creation, modification, or revocation of an identity |
| CREDENTIAL_ACCESS | Retrieval or use of stored credentials |
| SUBPROCESS_EXECUTION | Execution of a host process |
| COMPUTE_EXECUTION | Execution of a command in a compute substrate |
| FILESYSTEM_MUTATION | Writing, deleting, or mutating filesystem state |
| NETWORK_MUTATION | Sending data over the network |
| PLUGIN_EXECUTION | Execution of plugin code |

### Authority-Management

| Type | Description |
|------|-------------|
| AUTHORITY_MUTATION | Creation, modification, or revocation of authority |

### State-Transforming

| Type | Description |
|------|-------------|
| PROVENANCE_RECORD | Appending to the provenance graph |
| KNOWLEDGE_MUTATION | Modifying the knowledge graph |
| SESSION_MUTATION | Modifying session state |

### Informational

| Type | Description |
|------|-------------|
| READ_ONLY | Read-only query with no side effects |

---

## Interface Multiplicity

Multiple interfaces may converge on the same authority protocol:

```
Python API ──┐
AgentRuntime ─┤
CLI ─────────┤
MCP ─────────┼──→ ConsequenceRequest → Verifier → Executor
ARGO ────────┤
Plugin ──────┘
```

**Rule:** Interface multiplicity is allowed. Authority multiplicity is not.

---

## Invariants

### Authority

1. **ONE AUTHORITY GRAPH** — There is exactly one authority derivation from root to effect
2. **NO SELF-AUTHORIZATION** — No component can create authority for itself
3. **EXPLICIT ROOTS** — All authority roots are documented and verified
4. **NO HIDDEN ROOTS** — No interface-specific authority semantics

### Consequence

1. **CAPABILITY DESCRIBES CONSEQUENCE** — A capability binds to the actual effect
2. **CREDENTIAL ≠ AUTHORIZATION ≠ CAPABILITY** — These are separate concepts
3. **SCOPE IS EXACT** — Domain, actor, resource, action, temporal, quantity
4. **NON-AMPLIFYING** — Delegation cannot increase authority

### Execution

1. **VERIFICATION IS CANONICAL** — One verifier for all interfaces
2. **RECEIPTS ARE GENERATED** — Every execution produces a receipt
3. **PROVENANCE SURVIVES** — Every effect has reconstructible provenance
4. **REPLAY IS PREVENTED** — Single-use capabilities remain single-use

### Evidence

1. **RECEIPT ≠ AUTHORIZATION** — A receipt is evidence, not authority
2. **EFFECT ≠ RECEIPT** — An external effect is distinct from the runtime claim
3. **PROVENANCE IS IMMUTABLE** — Historical evidence cannot be rewritten
4. **ABSENCE ≠ EVIDENCE** — Missing provenance does not prove absence

---

## Success Criteria

The protocol is closed when:

1. Every consequential primitive is classified
2. Every consequential primitive is capability-bound
3. No consequential primitive is reachable without protocol authority
4. Every interface produces equivalent authority semantics
5. Authority is conserved across interface transitions
6. Crash consistency is characterized
7. Concurrency is characterized
8. Process restart is characterized
9. Every external effect has a reconstructible authority path
10. No receipt can create authority
11. No evidence can directly create authority
12. No model output can directly create authority
13. No credential can directly create authority
14. No registry membership can directly create authority

---

## Current Status

| Criterion | Status |
|-----------|--------|
| Consequential primitives identified | 10/10 |
| Consequential primitives closed | 6/10 |
| Interface equivalence | Partial |
| Crash consistency | Characterized |
| Concurrency | Characterized |
| Process restart | Characterized |
| Authority graph | Documented |
| Authority roots | Documented |

---

## Final Architectural Law

> **AUTHORITY IS NOT A PROPERTY OF THE COMPONENT THAT EXECUTES AN ACTION. AUTHORITY IS A DERIVED PROPERTY OF THE PROTOCOL STATE THAT JUSTIFIES THE ACTION.**

And therefore:

> **NO COMPONENT MAY BECOME AUTHORITATIVE MERELY BECAUSE IT CAN PRODUCE A CONSEQUENCE.**

And the operational invariant:

> **ONE AUTHORITY GRAPH. ZERO CONSEQUENTIAL ESCAPES.**
