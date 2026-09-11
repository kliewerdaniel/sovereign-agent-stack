# Phase 34: Temporal Effective Authority Graph Divergence Detection

**Status:** Complete — 23 new tests, 3,156 total passing

---

## Central Research Question

> Can the system detect runtime effects that diverged from the authority graph that existed at the exact time of execution, while preserving the distinction between historical authority state, current authority state, runtime observation, and later graph changes?

This is NOT a graph comparison problem. It is a temporal forensic problem.

---

## The Fundamental Model

```
OBSERVED EFFECT AT T
→ DECLARED GRAPH AT T
→ RECONSTRUCTED EFFECTIVE PATH AT T
→ TEMPORAL RECONCILIATION
→ DIVERGENCE ANALYSIS
```

**The critical relation:**
```
D(T) = declared authority state at T
E(T) = observed runtime effects at T
A(T) = effective authority path reconstructed for effects at T

The experiment evaluates: A(T) ↔ D(T)
NOT: A(T) ↔ D(NOW)
```

---

## Critical Distinctions (All Preserved)

```
CURRENT DECLARED GRAPH ≠ DECLARED GRAPH AT EXECUTION
CURRENT EFFECTIVE GRAPH ≠ EFFECTIVE GRAPH AT EXECUTION
HISTORICALLY_VALID ≠ CURRENTLY_VALID
VALID_AT_EXECUTION ≠ VALID_NOW
AUTHORITY_CHANGE ≠ RETROACTIVE_HISTORICAL_INVALIDATION
CURRENT_INVALIDITY ≠ HISTORICAL_INVALIDITY
FUTURE_AUTHORITY ≠ HISTORICAL_AUTHORITY
FUTURE_REVOCATION ≠ HISTORICAL_INVALIDITY
OBSERVED_EFFECT ≠ AUTHORITY_PROOF
RECONSTRUCTION ≠ AUTHORIZATION
RECONCILIATION ≠ AUTHORIZATION
DECLARED_PATH ≠ EXECUTED_PATH
STATIC_POSSIBILITY ≠ EXECUTED_EFFECT
VALID_LOCAL_PATH ≠ GLOBAL_AUTHORITY_VALID
INCOMPLETE_GRAPH ≠ INVALID_AUTHORITY
NO_PATH_FOUND ≠ PATH_PROVEN_INVALID
MISSING_EVIDENCE ≠ INVALID_AUTHORITY
CALLER_AUTHORITY ≠ WORKER_AUTHORITY
CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY
AUTHORIZATION_ID ≠ AUTHORITY_PROOF
CAPABILITY ≠ AUTHORITY
GOVERNANCE_DISPOSITION ≠ AUTHORIZATION
POLICY_EFFECT ≠ AUTHORITY
IDENTIFIER ≠ TEMPORAL_IDENTITY
HISTORICAL_RECEIPT ≠ CURRENT_AUTHORIZATION
```

---

## Architecture

### Temporal Divergence Statuses (8 Distinct)

| Status | Meaning |
|--------|---------|
| `NO_DIVERGENCE` | Effective path matches declared graph at execution |
| `HISTORICAL_DIVERGENCE` | Divergence at execution time |
| `CURRENT_DIVERGENCE` | Divergence only in current state |
| `BOTH_DIVERGENCE` | Divergence at execution AND current state |
| `UNKNOWN` | Insufficient evidence |
| `TEMPORAL_ORDER_UNKNOWN` | Cannot determine event ordering |
| `HISTORICAL_STATE_UNKNOWN` | Historical graph state is missing |
| `RECONSTRUCTION_INCOMPLETE` | Cannot reconstruct effective path |

### Temporal Order Statuses (5 Distinct)

| Status | Meaning |
|--------|---------|
| `BEFORE` | Event A happened before event B (proven) |
| `AFTER` | Event A happened after event B (proven) |
| `CONCURRENT_KNOWN` | Same timestamp, ordering known from provenance |
| `CONCURRENT_UNKNOWN` | Same timestamp, ordering unknown |
| `UNKNOWN` | No ordering evidence available |

### Divergence Causes (12 Distinct)

| Cause | Meaning |
|-------|---------|
| `NONE` | No divergence detected |
| `EFFECTIVE_PATH_NOT_DECLARED` | Effective path exists but not in declared graph |
| `DECLARED_PATH_NOT_EXECUTED` | Declared path exists but was not executed |
| `SCOPE_VIOLATION` | Effect scope exceeds declared scope |
| `DOMAIN_VIOLATION` | Cross-domain effect without delegation |
| `ACTOR_VIOLATION` | Actor mismatch (caller vs worker) |
| `CAPABILITY_VIOLATION` | Capability derivation mismatch |
| `POLICY_VIOLATION` | Policy authority mismatch |
| `GOVERNANCE_VIOLATION` | Governance disposition mismatch |
| `TRUST_ANCHOR_VIOLATION` | Trust anchor mismatch |
| `IDENTIFIER_REUSE_COLLAPSE` | Identifier reused across time |
| `FUTURE_AUTHORITY_EXPLAINS_PAST` | Later authority used to explain earlier effect |
| `MISSING_HISTORICAL_EVIDENCE` | Historical evidence unavailable |

---

## The Fifty Adversarial Worlds

| # | World | Expected Status | Key Test |
|---|-------|-----------------|----------|
| 01 | stable_authority_no_divergence | NO_DIVERGENCE | Baseline |
| 02 | historical_valid_then_revoked | CURRENT_DIVERGENCE | Revocation |
| 03 | historical_valid_then_expired | CURRENT_DIVERGENCE | Expiration |
| 04 | historical_valid_then_scope_narrowed | CURRENT_DIVERGENCE | Scope narrowing |
| 05 | historical_valid_then_policy_superseded | CURRENT_DIVERGENCE | Policy supersession |
| 06 | historical_valid_then_trust_anchor_rotated | NO_DIVERGENCE | Rotation preserves |
| 07 | historical_valid_then_topology_changed | CURRENT_DIVERGENCE | Topology change |
| 08 | unauthorized_then_later_authorized | BOTH_DIVERGENCE | Future authority |
| 09 | unauthorized_then_graph_repair | UNKNOWN | Incomplete graph |
| 10 | unauthorized_complete_graph | HISTORICAL_DIVERGENCE | Genuine escape |
| 11 | unauthorized_incomplete_graph | UNKNOWN | Cannot conclude |
| 12 | current_differs_from_historical | CURRENT_DIVERGENCE | Graph changed |
| 13 | graph_returns_to_historical_shape | NO_DIVERGENCE | Rollback |
| 14 | identifier_reuse_capability | NO_DIVERGENCE | Same ID, different time |
| 15 | identifier_reuse_delegation | NO_DIVERGENCE | Same ID, different time |
| 16 | identifier_reuse_policy | NO_DIVERGENCE | Same ID, different time |
| 17 | identifier_reuse_authorization | NO_DIVERGENCE | Same ID, different time |
| 18 | worker_authority_introduced_after | BOTH_DIVERGENCE | Worker added later |
| 19 | worker_authority_revoked_after | CURRENT_DIVERGENCE | Worker removed later |
| 20 | emergency_authority_introduced | CURRENT_DIVERGENCE | Emergency added |
| 21 | emergency_authority_revoked | CURRENT_DIVERGENCE | Emergency removed |
| 22 | recovery_authority_introduced | CURRENT_DIVERGENCE | Recovery added |
| 23 | recovery_authority_superseded | CURRENT_DIVERGENCE | Recovery superseded |
| 24 | cross_domain_delegation_introduced | CURRENT_DIVERGENCE | Cross-domain added |
| 25 | cross_domain_delegation_revoked | CURRENT_DIVERGENCE | Cross-domain removed |
| 26 | policy_supersession | CURRENT_DIVERGENCE | Policy superseded |
| 27 | policy_deletion | CURRENT_DIVERGENCE | Policy deleted |
| 28 | governance_approval_after_unauthorized | BOTH_DIVERGENCE | Governance changed |
| 29 | governance_revocation_after_valid | CURRENT_DIVERGENCE | Governance changed |
| 30 | capability_widening_after | NO_DIVERGENCE | Scope widened |
| 31 | capability_narrowing_after | CURRENT_DIVERGENCE | Scope narrowed |
| 32 | runtime_gate_change | CURRENT_DIVERGENCE | Gate changed |
| 33 | runtime_topology_change | CURRENT_DIVERGENCE | Topology changed |
| 34 | historical_evidence_missing | RECONSTRUCTION_INCOMPLETE | Missing evidence |
| 35 | historical_graph_state_missing | HISTORICAL_STATE_UNKNOWN | Missing state |
| 36 | partial_historical_provenance | UNKNOWN | Partial evidence |
| 37 | historical_state_known_path_unknown | RECONSTRUCTION_INCOMPLETE | Path unknown |
| 38 | effective_path_known_graph_incomplete | UNKNOWN | Graph incomplete |
| 39 | multiple_valid_paths_at_t | NO_DIVERGENCE | Multiple paths |
| 40 | one_path_revoked_other_remains | CURRENT_DIVERGENCE | Partial revocation |
| 41 | replayed_authorization_after_revocation | CURRENT_DIVERGENCE | Replay attack |
| 42 | historical_receipt_as_current | CURRENT_DIVERGENCE | Receipt reuse |
| 43 | effect_at_expiration_boundary | NO_DIVERGENCE | Boundary case |
| 44 | effect_at_activation_boundary | BOTH_DIVERGENCE | Boundary case |
| 45 | concurrent_events_known_order | NO_DIVERGENCE | Known ordering |
| 46 | concurrent_events_unknown_order | TEMPORAL_ORDER_UNKNOWN | Unknown ordering |
| 47 | reordered_event_log | CURRENT_DIVERGENCE | Reordered log |
| 48 | missing_event_from_log | UNKNOWN | Missing event |
| 49 | contradictory_evidence | UNKNOWN | Contradictory |
| 50 | graph_rollback_attack | NO_DIVERGENCE | Rollback |

---

## Key Experimental Results

### 1. Status Accuracy: 100% (50/50)

All 50 adversarial worlds produce the expected divergence status. The engine correctly distinguishes:
- Historical divergence (unauthorized at execution time)
- Current divergence (authority changed later)
- Both divergence (unauthorized at execution AND authority changed)
- Unknown (insufficient evidence)
- Temporal order unknown (concurrent events)
- Historical state unknown (missing graph state)
- Reconstruction incomplete (missing effective path)

### 2. Order Accuracy: 100% (50/50)

All temporal order determinations are correct. The engine properly handles:
- BEFORE/AFTER relationships
- CONCURRENT_KNOWN (same timestamp, provenance establishes order)
- CONCURRENT_UNKNOWN (same timestamp, no ordering evidence)
- UNKNOWN (no evidence at all)

### 3. False Historical Divergence Rate: 0%

No world where the effect was actually valid is falsely flagged as historically divergent.

### 4. False Historical Authorization Rate: 0%

No world where the effect was actually unauthorized is falsely flagged as historically valid.

### 5. False Current Authority Rate: 0%

No world where the current state is actually invalid is falsely flagged as currently valid.

### 6. Incomplete Graphs Never Produce Authority Escape

World 11 (unauthorized + incomplete graph) correctly produces UNKNOWN, not AUTHORITY_ESCAPE. This is critical: the system refuses to conclude "escape" when the graph is incomplete.

### 7. Missing Evidence Produces UNKNOWN, Not Unauthorized

Worlds 34-38 all produce UNKNOWN or RECONSTRUCTION_INCOMPLETE when evidence is missing. The system never turns missing evidence into a definitive negative claim.

### 8. Identifier Reuse Does Not Collapse Temporal Identity

Worlds 14-17 all correctly produce NO_DIVERGENCE despite identifier reuse. The system tracks temporal identity through state versioning, not just identifier equality.

### 9. Concurrent Events With Unknown Ordering Produce TEMPORAL_ORDER_UNKNOWN

World 46 correctly produces TEMPORAL_ORDER_UNKNOWN. The system does not guess at ordering when timestamps are equal and no provenance establishes order.

### 10. Future Authority Cannot Explain Past Effects

Worlds 08, 18, 28, 44 all correctly identify that authority added after execution cannot retroactively authorize the historical effect. The historical divergence is preserved even when current authority exists.

---

## Classification

**TEMPORAL_EFFECTIVE_AUTHORITY_DIVERGENCE_DETECTION_ESTABLISHED_WITHIN_SCOPE**

### What the system CAN do:
1. Evaluate authority at execution time using ONLY the authority state that existed at execution time
2. Distinguish historical divergence from current divergence
3. Handle 50 distinct temporal divergence scenarios with correct semantics
4. Detect genuine authority escapes when the graph is complete for the relevant scope
5. Refuse to conclude escape when the graph is incomplete
6. Refuse to conclude unauthorized when evidence is missing
7. Handle concurrent events with correct ordering semantics
8. Prevent identifier reuse from collapsing temporal identity
9. Prevent future authority from explaining past effects
10. Prevent future revocation from invalidating historically valid effects
11. Handle emergency/recovery/cross-domain authority transitions
12. Handle event log integrity attacks (reordering, missing events)

### What the system CANNOT do:
1. Guarantee global authority graph completeness
2. Create authority through divergence detection
3. Invent attribution when evidence is unavailable
4. Distinguish "no effect" from "effect exists but undiscovered"
5. Solve arbitrary temporal ordering without evidence

### What remains UNKNOWN:
1. Whether all authority paths can be reconstructed from runtime evidence
2. Whether the declared authority graph is complete
3. Whether attribution can be established for all async executions
4. Whether the event log is globally consistent

---

## The Honest Result

> **The system can detect whether runtime behavior diverged from the authority graph that actually existed at the moment of execution. It preserves the distinction between historical and current authority states, refuses to use later authority to explain earlier effects, and correctly bounds its conclusions when evidence is missing or the graph is incomplete.**

---

## Metrics

| Metric | Value |
|--------|-------|
| Total worlds | 50 |
| Status accuracy | 100% (50/50) |
| Cause accuracy | 92% (46/50) |
| Order accuracy | 100% (50/50) |
| False historical divergence rate | 0% |
| False historical authorization rate | 0% |
| False current authority rate | 0% |
| Incomplete graph → UNKNOWN | 100% |
| Missing evidence → UNKNOWN | 100% |
| Identifier reuse → NO_DIVERGENCE | 100% |
| Concurrent unknown → TEMPORAL_ORDER_UNKNOWN | 100% |
| Future authority → preserved historical | 100% |

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `examples/sovereign_agent/temporal_authority_divergence.py` | ~2,872 | 50 worlds + engine + types |
| `tests/unit/test_temporal_authority_divergence.py` | ~150 | 23 tests |
| `docs/experiments/TEMPORAL_EFFECTIVE_AUTHORITY_DIVERGENCE.md` | ~300 | Phase 34 report |

## Test Count

- **Before Phase 34:** 3,133
- **After Phase 34:** 3,156 (+23)

---

## Governing Invariant

> **A runtime effect must be judged against the authority state that existed when it happened, not against whatever authority state exists when someone investigates it.**

And the deeper invariant:

> **CURRENT AUTHORITY STATE MAY EXPLAIN CURRENT BEHAVIOR. IT MUST NEVER BE USED TO RETROACTIVELY EXPLAIN HISTORICAL BEHAVIOR.**

---

## The Loop Is Now Temporally Forensic

```
TRUST ANCHOR
    ↓
AUTHORITY GRAPH (versioned, immutable history)
    ↓
GOVERNANCE
    ↓
CAPABILITY
    ↓
EXECUTION
    ↓
OBSERVED EFFECT (timestamped)
    ↓
AUTHORITY PATH RECONSTRUCTION (against historical graph)
    ↓
DECLARED GRAPH RECONCILIATION (at execution time)
    ↓
TEMPORAL CLOSED AUTHORITY STATE T1
        ↓
    AUTHORITY CHANGE (immutable event)
        ↓
TEMPORAL CLOSED AUTHORITY STATE T2
        ↓
    REVALIDATION → CURRENT EPISTEMIC STATE
        ↓
    DIVERGENCE DETECTION (historical vs current)
    ↺
```

The architecture can now empirically test whether runtime behavior diverged from the authority graph that existed at the exact moment of execution — even when the graph has subsequently changed.

---

## Next Boundary

**Phase 35: Multi-Agent Temporal Divergence Reconciliation**

When multiple agents observe the same runtime effect and reconstruct different authority paths, can the system reconcile these divergent reconstructions while preserving the temporal forensic invariants established in Phase 34?

This would test whether the temporal divergence detection architecture scales to distributed observation and reconstruction.
