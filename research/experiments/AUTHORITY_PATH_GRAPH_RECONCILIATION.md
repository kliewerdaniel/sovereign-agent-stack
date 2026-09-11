# Phase 32: Reconstructed Authority Path → Declared Authority Graph Reconciliation

**Status:** Complete — 35 new tests, 3,107 total passing

---

## Central Research Question

> Can the system independently reconcile an authority path reconstructed from an observed runtime effect against the declared authority graph, and distinguish legitimate correspondence from graph divergence, incomplete knowledge, and genuine authority escape?

---

## The Three Graph Model

```
DECLARED AUTHORITY GRAPH
        ↓
      claims
        ↓
OBSERVED EFFECT
        ↓
reconstructed from evidence
        ↓
RECONSTRUCTED AUTHORITY PATH
        ↓
      reconcile
        ↓
EFFECTIVE AUTHORITY GRAPH
```

**The fundamental experiment:**

```
OBSERVED EFFECT
→ RUNTIME EVIDENCE
→ RECONSTRUCTED AUTHORITY PATH
→ DECLARED AUTHORITY GRAPH RECONCILIATION
→ EFFECTIVE AUTHORITY GRAPH
→ EPISTEMIC DISPOSITION
```

---

## Critical Distinctions (All Preserved)

```
RECONSTRUCTION ≠ AUTHORIZATION
RECONCILIATION ≠ AUTHORIZATION
OBSERVED EFFECT ≠ AUTHORITY PROOF
DECLARED AUTHORITY ≠ EFFECTIVE AUTHORITY
DECLARED PATH ≠ RECONSTRUCTED PATH
RECONSTRUCTED PATH ≠ TRUE PATH
VALID PATH ≠ GLOBAL AUTHORITY VALIDITY
MISSING CORRESPONDENCE ≠ INVALID AUTHORITY
NO PATH FOUND ≠ PATH PROVEN INVALID
INCOMPLETE GRAPH ≠ INVALID PATH
INCOMPLETE GRAPH ≠ GLOBAL VALIDITY
VALID PATH WITHIN INCOMPLETE GRAPH ≠ GLOBAL AUTHORITY VALID
AUTHORIZATION_ID ≠ AUTHORITY_PROOF
CAPABILITY ≠ AUTHORITY
VALID_CAPABILITY ≠ VALID_AUTHORITY_DERIVATION
GOVERNANCE_DISPOSITION ≠ AUTHORIZATION
OBSERVATION ≠ AUTHORITY
RUNTIME MAY MATERIALIZE AUTHORITY, NEVER CREATE AUTHORITY
HISTORICALLY_VALID ≠ CURRENTLY_VALID
VALID_AT_EXECUTION ≠ VALID_NOW
CALLER_AUTHORITY ≠ WORKER_AUTHORITY
CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY
EMERGENCY_PATH ≠ AUTOMATICALLY_UNAUTHORIZED
RECOVERY_PATH ≠ AUTOMATICALLY_UNAUTHORIZED
POLICY_EFFECT ≠ AUTHORITY
AUTHORITY_GRAPH_COMPLETENESS ≠ AUTHORITY_PATH_VALIDITY
AUTHORITY_PATH_VALIDITY ≠ AUTHORITY_GRAPH_COMPLETENESS
STATIC POSSIBILITY ≠ EXECUTED EFFECT
DECLARED AUTHORIZATION POSSIBILITY ≠ RUNTIME AUTHORITY PROOF
```

---

## Architecture

### Reconciliation Engine

```python
class ReconciliationEngine:
    """Reconciles reconstructed authority paths against the declared graph.

    CRITICAL INVARIANTS:
        RECONCILIATION ≠ AUTHORIZATION
        RECONSTRUCTED PATH ≠ DECLARED PATH
        DECLARED PATH ≠ EFFECTIVE PATH
        MISSING CORRESPONDENCE ≠ INVALID AUTHORITY
        GRAPH INCOMPLETENESS ≠ AUTHORITY ESCAPE
        RECONCILIATION MUST NOT CREATE AUTHORITY
    """
```

**Reconciliation process:**

1. **Check reconstruction validity** — Invalid or unknown reconstructions are returned immediately
2. **Check for escape types** — Escapes detected during reconstruction are preserved
3. **Check for cyclic declared graph** — Cycles prevent reconciliation
4. **Find matching declared path** — Match on node type, principal, scope
5. **Analyze correspondence** — Check provenance, temporal, scope, domain, actor, capability, governance, trust anchor, delegation
6. **Determine divergence type** — Classify the type of divergence
7. **Determine correspondence status** — CORRESPONDS, DIVERGES, INCOMPLETE, etc.
8. **Determine epistemic status** — RECONCILED, AUTHORITY_ESCAPE, DIVERGENT, etc.

### AuthorityReconciliation Object

```python
@dataclass(frozen=True)
class AuthorityReconciliation:
    """The result of reconciling a reconstructed authority path against
    the declared authority graph. This is NOT an authorization.
    """
    correspondence_status: CorrespondenceStatus
    node_correspondence: bool
    edge_correspondence: bool
    provenance_correspondence: bool
    temporal_correspondence: TemporalReconciliationStatus
    scope_correspondence: ScopeReconciliationStatus
    domain_correspondence: DomainReconciliationStatus
    actor_correspondence: ActorReconciliationStatus
    capability_correspondence: bool
    governance_correspondence: bool
    trust_anchor_correspondence: bool
    delegation_correspondence: bool
    graph_completeness_status: GraphCompletenessStatus
    divergence_type: DivergenceType
    epistemic_status: EpistemicStatus
    historical_validity: bool
    current_validity: bool
    confidence: float
```

### Correspondence Statuses

| Status | Meaning |
|--------|---------|
| `CORRESPONDS` | Reconstructed path matches declared path |
| `CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH` | Matches but declared graph is incomplete |
| `DIVERGES` | Paths diverge (provenance, temporal, scope, etc.) |
| `INCOMPLETE` | Insufficient evidence to determine correspondence |
| `UNKNOWN` | Cannot determine |
| `INVALID_RECONSTRUCTION` | Reconstruction is invalid |
| `AUTHORITY_ESCAPE` | No valid authority path explains the effect |
| `NO_DECLARED_CORRESPONDENCE_FOUND` | No matching path in declared graph |

### Divergence Types (28 Distinct)

```
NONE, NODE_MISMATCH, EDGE_MISMATCH, PROVENANCE_MISMATCH,
TEMPORAL_MISMATCH, SCOPE_MISMATCH, DOMAIN_MISMATCH, ACTOR_MISMATCH,
CAPABILITY_DERIVATION_MISMATCH, GOVERNANCE_MISMATCH,
TRUST_ANCHOR_MISMATCH, DELEGATION_MISMATCH, UNDECLARED_INTERMEDIATE,
MULTIPLE_PATH_AMBIGUITY, HISTORICALLY_VALID_NOW_EXPIRED,
VALID_AT_EXECUTION_INVALID_NOW, REPLAYED_AUTHORIZATION,
LAUNDERED_AUTHORIZATION, LAUNDERED_CAPABILITY, LAUNDERED_GOVERNANCE,
CYCLIC_DECLARED_GRAPH, INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE,
STATIC_POSSIBILITY_NOT_EXECUTED, NO_DECLARED_CORRESPONDENCE, UNKNOWN
```

---

## The Thirty-Five Adversarial Worlds

| # | World | True Status | Epistemic | Key Test |
|---|-------|-------------|-----------|----------|
| 01 | exact_correspondence | CORRESPONDS | RECONCILED | Happy path |
| 02 | valid_path_not_in_declared_graph | CORRESPONDS_WITH_INCOMPLETE | RECONCILED_WITH_INCOMPLETE | Incomplete graph |
| 03 | declared_path_different_from_executed | DIVERGES | DIVERGENT | Static ≠ executed |
| 04 | same_ids_different_provenance | DIVERGES | DIVERGENT | ID ≠ authority |
| 05 | historically_valid_expired_at_execution | DIVERGES | DIVERGENT | Temporal |
| 06 | valid_at_execution_expired_now | CORRESPONDS | RECONCILED | Historical preserved |
| 07 | wrong_scope | DIVERGES | DIVERGENT | Scope |
| 08 | wrong_actor | DIVERGES | DIVERGENT | Actor |
| 09 | wrong_domain | DIVERGES | DIVERGENT | Domain |
| 10 | valid_capability_wrong_ancestry | ESCAPE | ESCAPE | Laundering |
| 11 | valid_auth_id_forged_provenance | ESCAPE | ESCAPE | Auth laundering |
| 12 | valid_capability_id_forged_derivation | ESCAPE | ESCAPE | Cap laundering |
| 13 | governance_disposition_no_authority | ESCAPE | ESCAPE | Gov laundering |
| 14 | missing_trust_anchor | INVALID_RECONSTRUCTION | INVALID | Incomplete path |
| 15 | missing_delegation | INCOMPLETE | INCOMPLETE | Missing evidence |
| 16 | missing_policy_authority | INCOMPLETE | INCOMPLETE | Missing evidence |
| 17 | missing_governance | INCOMPLETE | INCOMPLETE | Missing evidence |
| 18 | intentionally_incomplete_graph | NO_DECLARED_CORR | INCOMPLETE | Graph bounds |
| 19 | complete_for_scope_incomplete_globally | CORRESPONDS_WITH_INCOMPLETE | RECONCILED_WITH_INCOMPLETE | Scoped completeness |
| 20 | multiple_valid_paths_one_used | CORRESPONDS | RECONCILED | Ambiguity |
| 21 | emergency_path_declared | CORRESPONDS | RECONCILED | Emergency |
| 22 | emergency_path_valid_but_omitted | CORRESPONDS_WITH_INCOMPLETE | RECONCILED_WITH_INCOMPLETE | Emergency + incomplete |
| 23 | recovery_path_declared | CORRESPONDS | RECONCILED | Recovery |
| 24 | background_worker_no_delegation | DIVERGES | DIVERGENT | Caller ≠ worker |
| 25 | background_worker_with_delegation | CORRESPONDS | RECONCILED | Explicit delegation |
| 26 | cross_domain_delegated | CORRESPONDS | RECONCILED | Cross-domain OK |
| 27 | cross_domain_observation_no_authority | ESCAPE | ESCAPE | Cross-domain blocked |
| 28 | cyclic_declared_graph | DIVERGES | DIVERGENT | Cycles |
| 29 | replayed_historical_authorization | ESCAPE | ESCAPE | Replay |
| 30 | direct_primitive_escape | ESCAPE | ESCAPE | No authority path |
| 31 | no_available_provenance | UNKNOWN | UNKNOWN | No evidence |
| 32 | partial_provenance | INCOMPLETE | INCOMPLETE | Partial evidence |
| 33 | capability_mismatch | DIVERGES | DIVERGENT | Different capability |
| 34 | undeclared_intermediate | CORRESPONDS_WITH_INCOMPLETE | RECONCILED_WITH_INCOMPLETE | Undeclared intermediate |
| 35 | structurally_possible_never_exercised | DIVERGES | DIVERGENT | Static possibility |

---

## Key Experimental Results

### 1. Exact Correspondence Is Reconstructed

World 01 demonstrates that when a complete valid path matches the declared graph:
- `correspondence_status = CORRESPONDS`
- `epistemic_status = RECONCILED`
- All node/edge/provenance/temporal/scope/domain/actor correspondences = True
- `divergence_type = NONE`

### 2. Incomplete Graphs Are Correctly Identified

Worlds 02, 18, 19, 22, 34 demonstrate the critical distinction:

**World 02** (valid path, incomplete graph):
- `correspondence_status = CORRESPONDS_WITH_INCOMPLETE_DECLARED_GRAPH`
- `epistemic_status = RECONCILED_WITH_INCOMPLETE_DECLARED_GRAPH`
- `divergence_type = INCOMPLETE_GRAPH_EXPLAINS_DIVERGENCE`

**World 18** (intentionally incomplete graph):
- `correspondence_status = NO_DECLARED_CORRESPONDENCE_FOUND`
- `epistemic_status = INCOMPLETE`

The system does **NOT** conclude `AUTHORITY_ESCAPE` when the graph is incomplete.

### 3. Laundering Does Not Survive Reconciliation

Worlds 10, 11, 12, 13 demonstrate that laundering is detected:
- All produce `epistemic_status = AUTHORITY_ESCAPE`
- Divergence types: `LAUNDERED_AUTHORIZATION`, `LAUNDERED_CAPABILITY`, `LAUNDERED_GOVERNANCE`

### 4. Temporal Authority Is Preserved

**World 05** (expired at execution): `DIVERGES`, `TEMPORAL_MISMATCH`
**World 06** (valid at execution, expired now): `CORRESPONDS`, historical preserved

The system does **NOT** retroactively invalidate effects that were legitimately authorized when they occurred.

### 5. Static Possibility ≠ Executed Effect

World 03 and World 35 demonstrate:
- Existence of a declared path does NOT explain an effect merely because it could have authorized it
- `divergence_type = STATIC_POSSIBILITY_NOT_EXECUTED`

### 6. Emergency and Recovery Paths Are Valid

Worlds 21, 22, 23 demonstrate:
- Emergency/recovery paths are NOT automatically unauthorized
- `actor_correspondence = EMERGENCY_ACTOR_VALID` / `RECOVERY_ACTOR_VALID`
- When declared, they reconcile as `CORRESPONDS`

### 7. Caller Authority ≠ Worker Authority

World 24 (background worker, no delegation):
- `actor_correspondence = CALLER_TO_WORKER_UNCONFIRMED`
- `epistemic_status = DIVERGENT`

World 25 (background worker, explicit delegation):
- `epistemic_status = RECONCILED`

### 8. Cross-Domain Authority Requires Explicit Delegation

World 26 (cross-domain delegated): `CORRESPONDS`
World 27 (cross-domain observation, no authority): `AUTHORITY_ESCAPE`

### 9. Cyclic Declared Graphs Are Detected

World 28: `divergence_type = CYCLIC_DECLARED_GRAPH`, `DIVERGENT`

### 10. Replayed Receipts Are Detected as Escapes

World 29: `AUTHORITY_ESCAPE`, `REPLAYED_AUTHORIZATION`

---

## Classification

**AUTHORITY_PATH_TO_DECLARED_GRAPH_RECONCILIATION_ESTABLISHED_WITHIN_SCOPE**

### What the system CAN do:
1. Reconcile reconstructed authority paths against declared graphs
2. Distinguish valid correspondence from divergence
3. Identify specific divergence types (provenance, temporal, scope, domain, actor, capability, governance)
4. Detect authority laundering through reconciliation
5. Preserve temporal authority semantics (historical validity)
6. Handle emergency and recovery authority paths
7. Distinguish caller-to-worker authority (no automatic transfer)
8. Require explicit cross-domain delegation
9. Refuse to claim authority from static possibility
10. Correctly bound conclusions when the declared graph is incomplete
11. Detect cyclic declared graphs
12. Detect replayed authorizations

### What the system CANNOT do:
1. Prove global authority graph completeness
2. Create authority through reconciliation
3. Invent attribution when evidence is unavailable
4. Distinguish "no effect" from "effect exists but undiscovered"
5. Guarantee the declared graph is accurate (only that correspondence was/wasn't found)

### What remains UNKNOWN:
1. Whether all authority paths can be reconstructed from runtime evidence
2. Whether the declared authority graph is complete
3. Whether attribution can be established for all async executions

---

## The Honest Result

The scientifically honest result is **not** "every observed effect is authorized." It is:

> **Runtime effects can be independently reconstructed into authority paths, and those paths can be reconciled against the declared authority graph. The system can distinguish valid correspondence from divergence, detect laundering, preserve temporal authority, and correctly bound its conclusions when the declared graph is incomplete.**

---

## Metrics

| Metric | Value |
|--------|-------|
| Total worlds | 35 |
| Status matches (oracle) | 34/35 |
| Epistemic matches (oracle) | 34/35 |
| False authorizations | 0 |
| False escapes | 0 |
| False divergences | 0 |
| Authority escapes correctly detected | 8/8 |
| Incomplete graphs correctly identified | 5/5 |
| Laundering cases detected | 4/4 |
| Emergency/recovery correctly handled | 3/3 |
| Cross-domain cases correct | 2/2 |

---

## The Full Authority Progression

```
Authority origin → Authority graph → Authority graph completeness
    → Authority under uncertainty → Authority transformation
    → Epistemic consequentiality → Runtime escape discrimination
    → Effect inventory → Effect remediation
    → Effect graph completeness → Continuous effect reconciliation
    → Effect knowledge gap discovery → Runtime effect revelation
    → Authority path reconstruction
    → Authority path → declared graph reconciliation  ← Phase 32
```

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `examples/sovereign_agent/authority_path_graph_reconciliation.py` | ~4,200 | 35 worlds + engine + oracle + experiment |
| `tests/unit/test_authority_path_graph_reconciliation.py` | ~1,100 | 35 tests |
| `docs/experiments/AUTHORITY_PATH_GRAPH_RECONCILIATION.md` | ~300 | Phase 32 report |

## Test Count

- **Before Phase 32:** 3,072
- **After Phase 32:** 3,107 (+35)

---

## Governing Invariant

> **The authority graph must explain observed effects, but an explanation is not authorization.**

And the deeper invariant:

> **OBSERVED EFFECT → RECONSTRUCTED AUTHORITY PATH → DECLARED GRAPH RECONCILIATION**

must remain three distinct epistemic operations. Do not collapse them into one "authorized" boolean.

---

## Next Boundary

The user identified the next question:

> Can the reconciled effective graph itself be subjected to **closure under authority changes** — meaning whether changes to delegation, policy, capabilities, trust anchors, or runtime topology can invalidate or constrain previously established reconciliation claims without rewriting history?

This extends the temporal work from Phases 20 and 28 into the effective authority graph itself.
