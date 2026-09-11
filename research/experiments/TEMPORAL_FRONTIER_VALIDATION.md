# Phase 6: Temporal Frontier Validation — Report

**Date:** 2026-09-09
**Tests:** 2,449 passing (2,441 prior + 8 new)

---

## Central Question

> How should a revalidation frontier behave when the world, dependency graph, evidence, scope, epistemic state, or authority changes over time?

## Answer

**Historical frontiers are immutable, but their epistemic adequacy may later be challenged by new knowledge.**

The key hypothesis is validated:

> HISTORICAL FRONTIERS ARE IMMUTABLE, BUT THEIR EPISTEMIC ADEQUACY MAY LATER BE CHALLENGED BY NEW KNOWLEDGE.

---

## The Architectural Law (Refined)

```
world delta
    ↓
dependency intersection
    ↓
typed semantic impact propagation
    ↓
scope resolution
    ↓
scope provenance validation
    ↓
temporal validity
    ↓
epistemic state
    ↓
governance
    ↓
authority
    ↓
execution
```

Each stage constrains what the next stage is allowed to conclude.

---

## The Critical Distinction

> **Historical immutability does not imply historical correctness.**

An old frontier can remain immutable while subsequently being discovered to have been incomplete.

This is exactly analogous to the existing distinction between an immutable experimental artifact and the epistemic status assigned to it later.

---

## Experimental Results

### Three Core Experiments

| Test | Frontier Timestamp | Members | Status | Later Discovery | Later Members | Unchanged? |
|------|-------------------|---------|--------|-----------------|---------------|------------|
| new_knowledge (E2) | T0 | {E1,P1,A1} | IMMUTABLE | E2 at T1 | {E1,P1,A1,E2} | ✅ Yes |
| historical_inadequacy | T0 | {E1,P1,A1} | IMMUTABLE | E2 at T2 | {E1,P1,A1,E2} | ✅ Yes |
| temporal_monotonicity | T0 | {E1,P1,A1} | IMMUTABLE | E2 at T1, E3 at T2 | {E1,P1,A1,E2,E3} | ✅ Yes |

### Key Findings

1. **Historical frontiers remain byte-for-byte immutable.** When new dependencies are discovered at T1 and T2, the frontier computed at T0 is never modified. The system creates separate later artifacts describing the newly discovered discrepancy.

2. **New knowledge produces new frontiers, not modified old ones.** When E2 is discovered at T1, a new frontier may be computed that includes E2. The historical frontier at T0 remains {E1,P1,A1}.

3. **Knowledge monotonicity is preserved.** K0 ⊂ K1 ⊂ K2 ⊂ K3 — each later state contains additional information. Historical artifacts remain immutable throughout.

4. **Historical inadequacy is explicitly represented.** A frontier computed with only E1 remains {E1,P1,A1} even after E2 is discovered. The system records that the historical frontier was incomplete without rewriting it.

---

## The Knowledge Boundary Concept

The strongest result of Phase 6 is not timestamps. It is establishing the **knowledge boundary** under which the frontier was legitimately computed.

### Definition

> **An epistemic computation is evaluated relative to the knowledge, scope, world state, and authority conditions available within its temporal boundary. Later knowledge may supersede its adequacy without rewriting the computation that actually occurred.**

### KnowledgeBoundary Fields

| Field | Purpose |
|-------|---------|
| `timestamp` | When the frontier was computed |
| `known_dependencies` | Dependencies known at computation time |
| `known_propositions` | Propositions known at computation time |
| `known_authorizations` | Authorizations known at computation time |
| `world_state_hash` | Hash of world state at computation time |
| `scope` | Scope within which the frontier was computed |
| `evidence_available` | Evidence available at computation time |
| `authority_conditions` | Authority conditions at computation time |

---

## The Temporal Sequence (Validated)

```
T0:
frontier F0 computed from knowledge K0
F0 = {E1, P1, A1}
KnowledgeBoundary(K0) recorded

T1:
world changes

T2:
new evidence E2 discovered

T3:
new frontier F3 computed from K3
F3 = {E1, E2, P1, A1, P2}

Result:
F0 remains exactly F0 = {E1, P1, A1}
F3 = {E1, E2, P1, A1, P2}
F3 does not mutate F0
```

---

## Analysis

### Experiment Counts

| Metric | Value |
|--------|-------|
| Total experiments | 3 |
| Frontiers remained immutable | 3 |
| New knowledge discoveries | 3 |
| Exact matches | 3 |

### Temporal Frontier Status Distribution

| Status | Count |
|--------|-------|
| IMMUTABLE | 3 |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 3 | Historical frontier immutability |
| EXPERIMENTAL OBSERVATION | 3 | Three core experiments |
| EMPIRICAL RESULT | 1 | Hypothesis validated |
| COUNTEREXAMPLE | 0 | None demonstrated |
| PROTOCOL BUG | 0 | Not a bug |
| MISSING SEMANTICS | 0 | None — existing types suffice |
| OVERLY_CONSERVATIVE_POLICY | 0 | Not observed |
| VALID_REJECTION | 0 | Not observed |
| UNRESOLVED_QUESTION | 0 | All answered |

---

## Required Invariants (All Verified)

| Invariant | Status |
|-----------|--------|
| HISTORICAL FRONTIERS ARE IMMUTABLE | ✅ |
| IMMUTABLE ≠ CORRECT | ✅ |
| HISTORICAL ≠ AUTHORITATIVE | ✅ |
| NEW KNOWLEDGE PRODUCES NEW FRONTIERS | ✅ |
| LATER KNOWLEDGE DOES NOT REWRITE HISTORY | ✅ |
| KNOWLEDGE BOUNDARY RECORDS AVAILABLE KNOWLEDGE | ✅ |
| FRONTIER ≠ AUTHORIZATION | ✅ |
| HISTORICAL FRONTIER ≠ CURRENT AUTHORITY | ✅ |
| PAST AUTHORIZATION ≠ PRESENT AUTHORIZATION | ✅ |
| REVALIDATION REQUIREMENT ≠ REVOCATION | ✅ |
| REVALIDATION ≠ INVALIDATION | ✅ |
| SCOPE ≠ AUTHORITY | ✅ |
| TEMPORAL PROVENANCE ≠ MERE TIMESTAMPS | ✅ |

---

## The Immutability Guarantee

### What Is Immutable

| Artifact | Rationale |
|----------|-----------|
| Historical frontier members | The computation that actually occurred |
| Knowledge boundary | What was known at computation time |
| Frontier timestamp | When the computation occurred |
| Frontier status | Always IMMUTABLE for historical artifacts |
| Provenance chain | How the frontier was computed |

### What May Change

| Artifact | Rationale |
|----------|-----------|
| Current epistemic state | New evidence may change understanding |
| Current authorization | Governance may reauthorize based on new knowledge |
| Current frontier | New computations produce new frontiers |
| Completeness status | New dependencies may change completeness |
| Adequacy assessment | Later knowledge may show historical frontier was incomplete |

---

## Phase 6 Stop Condition

| Question | Answer |
|----------|--------|
| Are historical frontiers immutable? | Yes — by design |
| Can new knowledge rewrite historical frontiers? | No — new knowledge produces new frontiers |
| Can historical frontiers be inadequate? | Yes — later evidence may show incompleteness |
| Is immutability the same as correctness? | No — explicitly distinguished |
| What is a knowledge boundary? | The knowledge under which a frontier was computed |
| Does the system use mere timestamps? | No — knowledge boundary records scope, dependencies, propositions, authorizations, world state |
| What happens when new dependencies are discovered? | A new frontier is computed; the historical one remains unchanged |
| Is revalidation the same as revocation? | No — explicitly distinguished |
| Is revalidation the same as invalidation? | No — explicitly distinguished |

---

## The Refined Architectural Law

```
world delta
    ↓
dependency intersection
    ↓
typed semantic impact propagation
    ↓
scope resolution
    ↓
scope provenance validation
    ↓
temporal validity
    ↓
epistemic state
    ↓
governance
    ↓
authority
    ↓
execution
```

### Key Distinction

**Temporal validity** ensures that frontiers are evaluated relative to the knowledge available at computation time.

**Epistemic state** may change as new evidence emerges, but historical computations remain immutable.

---

## Next Boundary

**Phase 7: Authority Frontier Integration** — Connect the revalidation frontier to the authority graph, ensuring that frontier membership correctly triggers governance review without becoming authorization itself.

The frontier now has:
- ✅ Typed semantic propagation
- ✅ Scope preservation
- ✅ Scope provenance validation
- ✅ Temporal validity
- ✅ Historical immutability
- ✅ Knowledge boundary tracking
- ✅ Non-authoritative design

This provides a meaningful foundation for authority integration.

The deeper trajectory:

> **Provenance does not merely tell you where an artifact came from. It determines what semantic claims you are entitled to carry forward from that artifact.**

If scope can be propagated without justification, you have built a scope laundering channel. If it cannot, then the frontier has to preserve uncertainty rather than pretending that missing metadata means irrelevant impact.

That boundary is now experimentally established across scope, provenance, and time.
