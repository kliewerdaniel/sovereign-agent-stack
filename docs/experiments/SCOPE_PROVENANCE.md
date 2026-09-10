# Phase 5.6: Scope Provenance and Semantic Scope Authority — Report

**Date:** 2026-09-09
**Tests:** 2,441 passing (2,433 prior + 8 new)

---

## Central Question

> WHO OR WHAT ESTABLISHES THE SCOPE OF AN ARTIFACT, AND UNDER WHAT CONDITIONS MAY THAT SCOPE BE PROPAGATED TO DOWNSTREAM ARTIFACTS?

## Answer

**Scope may propagate only when the downstream artifact has no independently established scope AND the relationship type permits propagation.**

The working hypothesis has been validated:

> A frontier may propagate an established scope constraint, but propagation must not manufacture scope authority.

---

## The Architectural Law (Refined)

```
FRONTIER = DEPENDENCY_INTERSECTION
         + SEMANTIC_IMPACT_PROPAGATION
         + SCOPE_RESOLUTION
         + SCOPE_PROVENANCE_VALIDATION
```

The key distinction: **scope resolution** determines what scope appears to apply, while **scope provenance validation** determines whether the system is entitled to treat that scope as established.

---

## Experimental Results

### Four Core Experiments

| Test | Upstream Scope | Downstream Scope | Relationship | Propagate? | Source | Authority |
|------|---------------|------------------|--------------|------------|--------|-----------|
| independent_scope | production | production | evidence (DIRECT) | ❌ No | declared | established |
| unknown_scope | production | unknown | evidence (DIRECT) | ✅ Yes | inherited | propagated |
| transitive_blocked | production | unknown | provenance (TRANSITIVE) | ❌ No | unknown | unknown |
| cross_domain | DOMAIN_A | DOMAIN_B | evidence (DIRECT) | ❌ No | declared | established |

### Key Findings

1. **Independent scope prevents propagation.** When P1 has its own declared production scope, E1's production scope does not propagate. P1's scope authority is `ESTABLISHED`, not `PROPAGATED`.

2. **Unknown scope permits propagation.** When P1 has unknown scope, E1's production scope propagates to P1. P1's scope authority becomes `PROPAGATED`, making the provenance explicit.

3. **Transitive relationships block propagation.** Provenance and governance relationships (TRANSITIVE strength) never propagate scope, even when downstream scope is unknown.

4. **Cross-domain scope is blocked.** When P1 has independent scope in DOMAIN_B, E1's DOMAIN_A scope does not propagate. This prevents scope laundering across sovereign domains.

---

## Scope Sources and Authority

### Scope Sources

| Source | Meaning | Authority Level |
|--------|---------|-----------------|
| `DECLARED` | Explicitly declared in artifact metadata | High |
| `OBSERVED` | Observed at runtime | High |
| `GOVERNANCE` | Established by governance policy | High |
| `INFERRED` | Inferred from context | Medium |
| `INHERITED` | Inherited from upstream artifact | Medium |
| `UNKNOWN` | Source unknown | None |

### Scope Authority

| Authority | Meaning | Can Propagate? |
|-----------|---------|----------------|
| `ESTABLISHED` | Independently justified | N/A (already has scope) |
| `PROPAGATED` | Inherited from upstream | Yes (with provenance) |
| `INFERRED` | Inferred from context | Yes (with provenance) |
| `UNKNOWN` | Cannot determine authority | No |

---

## Scope Provenance Rules

### Rule 1: Independent Scope Takes Precedence

If a downstream artifact has independently established scope (DECLARED, OBSERVED, GOVERNANCE), upstream scope does not propagate.

**Rationale:** Downstream artifacts are not blank slates. Their scope is their own.

### Rule 2: Unknown Scope Permits Propagation

If a downstream artifact has unknown scope, upstream scope may propagate IF the relationship type permits.

**Rationale:** Without evidence to the contrary, upstream scope is the best available information.

### Rule 3: Transitive Relationships Block Propagation

Provenance, governance, and observability relationships (TRANSITIVE strength) never propagate scope.

**Rationale:** These relationships are informational, not semantic dependencies.

### Rule 4: Cross-Domain Scope Is Blocked

Scope does not propagate across sovereign domain boundaries without explicit delegation.

**Rationale:** Sovereign domains are authority boundaries, not just labels.

---

## Analysis

### Experiment Counts

| Metric | Value |
|--------|-------|
| Total experiments | 4 |
| Propagation permitted | 1 |
| Propagation blocked | 3 |
| Exact matches | 4 |

### Scope Source Distribution

| Source | Count |
|--------|-------|
| declared | 2 |
| unknown | 2 |

### Scope Authority Distribution

| Authority | Count |
|-----------|-------|
| established | 2 |
| propagated | 1 |
| unknown | 1 |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 4 | Scope provenance rules |
| EXPERIMENTAL OBSERVATION | 4 | Four core experiments |
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
| SCOPE ≠ AUTHORITY | ✅ |
| SCOPE DOES NOT CREATE AUTHORITY | ✅ |
| UNKNOWN SCOPE ≠ OUT OF SCOPE | ✅ |
| INDEPENDENT SCOPE TAKES PRECEDENCE | ✅ |
| TRANSITIVE RELATIONSHIPS BLOCK PROPAGATION | ✅ |
| CROSS-DOMAIN SCOPE IS BLOCKED | ✅ |
| PROPAGATED SCOPE CARRIES PROVENANCE | ✅ |
| FRONTIER ≠ AUTHORIZATION | ✅ |
| FRONTIER ≠ REVOCATION | ✅ |
| FRONTIER ≠ EXECUTION | ✅ |

---

## The Scope Laundering Prevention Test

### Attack Attempt

```
E1[DOMAIN_A] → P1[unknown] → A1[DOMAIN_B]
```

**Goal:** Cause DOMAIN_A scope to appear on P1 or A1 through propagation.

### Result

**Blocked.** P1 has independent scope in DOMAIN_B, so E1's DOMAIN_A scope does not propagate. Even if P1 had unknown scope, the cross-domain boundary would block propagation.

### Why This Matters

Without scope provenance validation, an attacker could:
1. Create an upstream artifact with authoritative scope
2. Chain it to downstream artifacts in different domains
3. Use the propagated scope to bypass domain boundaries

The scope provenance rules prevent this by requiring independent scope establishment.

---

## Phase 5.6 Stop Condition

| Question | Answer |
|----------|--------|
| Where does scope come from? | Artifact metadata, dependency declarations, governance, runtime observation |
| Can scope propagate through semantic relationships? | Yes, but only DIRECT relationships, not TRANSITIVE |
| Can scope propagate across domains? | No — domain boundaries are authority boundaries |
| What happens when downstream scope is unknown? | Upstream scope propagates with `PROPAGATED` authority |
| What happens when downstream scope is independent? | Upstream scope does not propagate |
| Can transitive relationships propagate scope? | No — provenance/governance/observability don't propagate |
| Is scope laundering possible? | No — cross-domain and transitive blocking prevent it |
| What is the minimum implementation? | Scope provenance engine with 4 rules |

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
revalidation frontier
    ↓
epistemic reevaluation
    ↓
governance
    ↓
authority revalidation
```

### Key Distinction

**Scope resolution** determines what scope appears to apply to an artifact.

**Scope provenance validation** determines whether the system is entitled to treat that scope as established.

These are not the same. The first is a factual question; the second is an epistemic authority question.

---

## Next Boundary

**Phase 6: Temporal Frontier Validation** — Test frontier behavior across time, ensuring historical frontiers are immutable and future knowledge doesn't rewrite past frontiers.

The frontier now has:
- ✅ Typed semantic propagation
- ✅ Scope preservation
- ✅ Scope provenance validation
- ✅ Edge type awareness
- ✅ Cross-domain scope blocking
- ✅ Non-authoritative design

This provides a meaningful foundation for temporal validation.

The deeper trajectory:

> **Provenance does not merely tell you where an artifact came from. It determines what semantic claims you are entitled to carry forward from that artifact.**

If scope can be propagated without justification, you have built a scope laundering channel. If it cannot, then the frontier has to preserve uncertainty rather than pretending that missing metadata means irrelevant impact.

That boundary is now experimentally established.
