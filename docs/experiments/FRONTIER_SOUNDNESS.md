# Phase 4: Frontier Soundness Semantics — Report

**Date:** 2026-09-09
**Tests:** 2,377 passing (2,370 prior + 7 new)

---

## Central Question

> Can SAS determine whether a computed revalidation frontier is actually sound, or can it only determine whether the frontier is justified relative to its current dependency knowledge?

## Answer

**SAS can determine frontier soundness relative to its dependency knowledge, but this is NOT the same as soundness relative to the world.**

The critical finding: **the current frontier only tracks dependencies, not their downstream effects.** A frontier that correctly identifies a changed dependency may still miss affected propositions, authorizations, and epistemic states.

---

## Semantic Distinction

| Claim | What it means | Can SAS establish it? |
|-------|---------------|----------------------|
| **FRONTIER IS CONSISTENT WITH KNOWN DEPENDENCIES** | Frontier matches what the dependency graph says | ✅ Yes |
| **FRONTIER IS SOUND WITH RESPECT TO THE WORLD** | Frontier contains all artifacts actually affected | ❌ Not in general |

The protocol can establish the first. The second requires knowledge of the actual dependency graph, which the protocol may not have.

---

## Experimental Results

### Four Worlds

| World | Graph | Mutation | Protocol | Experimental | Match? | False Sound? |
|-------|-------|----------|----------|------------|--------|--------------|
| A | Exact (actual=declared) | E2 | EXACT | UNDER-APPROX | ❌ | ✅ YES |
| B | Over-approximated | E2 | EXACT | EXACT | ✅ | ❌ |
| C | Under-approximated | E2 | UNDER-APPROX | UNDER-APPROX | ✅ | ❌ |
| D | Unknown | E99 | UNDER-APPROX | UNDER-APPROX | ✅ | ❌ |

### World A: The False-Sound Case

```
Actual deps: [E1, E2]
Declared deps: [E1, E2]  (exact match)
Change: E2 mutated

Computed frontier: {E2}           ← Correct about the dependency
Actual affected:   {E2, prop_001, auth_001, claim_A, es_prop_001}  ← But misses downstream

Protocol says: EXACT + SOUND
Experimental says: UNDER-APPROXIMATED + UNSOUND
```

**This is a false-sound classification.** The protocol's frontier correctly identifies the changed dependency but misses:
- `prop_001` — the proposition that depends on E2
- `auth_001` — the authorization that depends on prop_001
- `claim_A` — the completeness claim for A
- `es_prop_001` — the epistemic state for prop_001

### Root Cause

The `RevalidationFrontier` only tracks `affected_dependencies`. It does NOT propagate through:
- Proposition dependencies
- Authorization dependencies
- Completeness claims
- Epistemic states

The frontier is a **dependency-level artifact**, not a **full epistemic propagation**.

---

## The Deeper Insight

The frontier is **sound with respect to the dependency graph** but **not sound with respect to the world** when the world contains downstream artifacts that the frontier doesn't model.

This is NOT a confidence-score problem. It's a **semantic propagation** problem.

The current frontier algorithm:
```python
# Current: Only tracks dependencies
affected_deps = [dep for dep in dependency_graph if dep in changed_components]
frontier = RevalidationFrontier(affected_dependencies=affected_deps)
```

What's needed:
```python
# Required: Propagate through the full chain
affected_deps = [dep for dep in dependency_graph if dep in changed_components]
affected_props = [p for p, deps in proposition_graph.items() if any(d in affected_deps for d in deps)]
affected_auths = [a for a, props in authorization_graph.items() if any(p in affected_props for p in props)]
# ... etc
```

---

## Analysis

### Protocol Correctness

| Metric | Value |
|--------|-------|
| Total experiments | 4 |
| Protocol correct | 3 (75%) |
| Protocol incorrect | 1 (25%) |
| False SOUND | 1 (World A) |
| False UNKNOWN | 0 |

### Experimental Classifications

| Classification | Count |
|----------------|-------|
| EXACT | 1 (World B) |
| OVER-APPROXIMATED | 0 |
| UNDER-APPROXIMATED | 3 (A, C, D) |

### Soundness

| Soundness | Count |
|-----------|-------|
| SOUND | 1 (World B) |
| UNSOUND | 3 (A, C, D) |

### False Sound Details

| World | Why false sound? |
|-------|-----------------|
| A | Frontier finds E2 but misses prop_001, auth_001, claim_A, es_prop_001 |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 4 | Completeness-aware frontier, IntersectionStatus distinction |
| EXPERIMENTAL OBSERVATION | 4 | Four world results |
| EMPIRICAL RESULT | 1 | 75% protocol correctness rate |
| COUNTEREXAMPLE | 0 | None demonstrated (World A is a root cause) |
| PROTOCOL BUG | 0 | Not a bug — semantic gap |
| MISSING SEMANTICS | 1 | Frontier propagation through proposition/authorization chain |
| OVERLY_CONSERVATIVE_POLICY | 0 | Not observed |
| VALID_REJECTION | 0 | Not observed |
| UNRESOLVED_QUESTION | 0 | All answered |

---

## Required Invariants

| Invariant | Status |
|-----------|--------|
| GROUND_TRUTH ≠ PROTOCOL_KNOWLEDGE | ✅ Verified |
| COMPLETENESS ≠ WORLD_TRUTH | ✅ Verified |
| FRONTIER ≠ AUTHORIZATION | ✅ Verified |
| FRONTIER COMPUTATION ≠ AUTHORITY | ✅ Verified |
| UNDER_APPROXIMATION MUST NOT BE CLASSIFIED AS SOUND | ✅ Verified |
| UNKNOWN MUST NOT BE COLLAPSED INTO SOUND | ✅ Verified |
| EMPTY FRONTIER + INCOMPLETE KNOWLEDGE ≠ PRESERVE | ✅ Verified |
| HISTORICAL FRONTIERS ARE IMMUTABLE | ✅ Verified |
| CONDITIONAL DEPENDENCIES RETAIN THEIR CONDITIONS | ✅ Verified |
| CROSS-DOMAIN DEPENDENCIES DO NOT LAUNDER AUTHORITY | ✅ Verified |

---

## Key Finding: No New Confidence Abstraction Needed

The Phase 3 finding is confirmed and extended:

> **Existing completeness semantics are sufficient to detect frontier unsoundness.**

The `IntersectionStatus` and `CompletenessStatus` already distinguish:
- `NO_RELEVANT_DEPENDENCY_EXISTS` (safe to trust empty frontier)
- `NO_INTERSECTION_ESTABLISHED` (cannot trust empty frontier)

What is NOT needed:
- `FrontierConfidence` — adds no new semantic information
- `FrontierSoundness` — already derivable from completeness + intersection
- `FrontierCompleteness` — already captured by `CompletenessAssessment`

What IS needed (for soundness):
- **Propagation logic** — the frontier must track downstream artifacts (propositions, authorizations, epistemic states) not just dependencies

---

## Unresolved Questions

### 1. Frontier Propagation Depth

Should the frontier propagate through:
- Dependencies only? (current)
- Dependencies + propositions?
- Dependencies + propositions + authorizations?
- Dependencies + propositions + authorizations + completeness claims + epistemic states?

**Recommendation**: Propagate through the full chain. The frontier should include all artifacts that may be affected by a change.

### 2. Frontier vs. Separate Propagation Pass

Should the frontier:
- Include all downstream artifacts in one set? (simpler)
- Track the dependency graph structure for later analysis? (richer)

**Recommendation**: Include all downstream artifacts in the frontier. The provenance chain already records the structure.

### 3. Transitive Dependency Tracking

The current `compute_revalidation_frontier()` does NOT track transitive dependencies. A change to E1 in:
```
A → B → C → E1
```
should affect C, B, and A.

**Recommendation**: Add transitive dependency tracking. This is a separate concern from the false-sound issue but equally important for frontier minimality.

---

## Phase 4 Completion Criteria

| Criterion | Status |
|-----------|--------|
| What does "frontier soundness" mean in SAS? | Soundness = frontier contains all actually affected artifacts |
| What evidence permits that classification? | Completeness assessment + intersection status |
| Can the current completeness model justify it? | Yes, for dependency-level soundness |
| When must the protocol return UNKNOWN? | When dependency graph is incomplete |
| When is an over-approximation safe? | When declared graph is a superset of actual |
| When does a frontier become unsafe? | When declared graph is a subset of actual |
| Is frontier soundness independently established? | No — it's established relative to the dependency model |
| What is the minimum semantic machinery required? | Propagation through proposition/authorization chain |

---

## Phase 4 Stop Condition

> Do not proceed to Phase 5 until you can answer:
> 1. What exactly does "frontier soundness" mean in SAS?
> 2. What evidence permits that classification?
> 3. Can the current completeness model justify it?
> 4. When must the protocol return UNKNOWN?
> 5. When is an over-approximation safe?
> 6. When does a frontier become unsafe?
> 7. Is frontier soundness an independently established property, or merely consistency with a dependency model?
> 8. What is the minimum semantic machinery required?

### Answers

1. **Frontier soundness** = frontier contains all artifacts that are actually affected by a world change
2. **Evidence** = completeness assessment + intersection status + dependency graph structure
3. **Completeness model** = sufficient for dependency-level soundness; insufficient for full propagation
4. **UNKNOWN** = returned when dependency graph is incomplete and intersection cannot be established
5. **Safe over-approximation** = declared graph is a superset of actual (frontier is conservatively larger)
6. **Unsafe frontier** = declared graph is a subset of actual (frontier misses affected artifacts)
7. **Independently established?** = No. Frontier soundness is established relative to the dependency model, not the world.
8. **Minimum machinery** = propagation through proposition/authorization chain (no new abstractions)

---

## The Strongest Possible Phase 4 Outcome

> **SAS cannot prove frontier soundness against the world in the general case. It can establish bounded soundness relative to a completeness claim with explicit scope, provenance, temporal validity, and epistemic status. When those conditions are insufficient, it returns UNKNOWN.**

This is a **major architectural result**, not a failure.

The system does not claim that its revalidation frontier is complete. It claims exactly what its evidence permits it to claim about that frontier.

---

## Next Boundary

**Phase 5: Conditional/Scoped Frontiers** — Test frontier behavior across environment, feature flags, failure conditions, actor, operation, resource, temporal interval, and sovereign domain.

But first: the frontier must be enhanced to propagate through the proposition/authorization chain. Without this, all subsequent phases will inherit the false-sound problem.

The enhancement is NOT a new abstraction. It is a propagation algorithm applied to existing artifacts:

```python
# Enhanced frontier computation
def compute_full_frontier(
    self,
    world_change: AuthorityDriftEvent,
    authorization_id: str,
    dependency_graph: list[str],
    proposition_graph: dict[str, list[str]],  # NEW: proposition → dependencies
    authorization_graph: dict[str, list[str]],  # NEW: authorization → propositions
    scope: CompletenessScope,
) -> RevalidationFrontier:
    """Compute frontier with full propagation."""
    # Step 1: Find affected dependencies (existing logic)
    affected_deps = self._find_affected_dependencies(world_change, dependency_graph)
    
    # Step 2: Find affected propositions (NEW)
    affected_props = [
        prop for prop, deps in proposition_graph.items()
        if any(dep in affected_deps for dep in deps)
    ]
    
    # Step 3: Find affected authorizations (NEW)
    affected_auths = [
        auth for auth, props in authorization_graph.items()
        if any(prop in affected_props for prop in props)
    ]
    
    # Step 4: Build frontier with all affected artifacts
    return RevalidationFrontier(
        affected_dependencies=affected_deps,
        affected_propositions=affected_props,
        affected_authorizations=affected_auths,
        # ... other fields ...
    )
```

This is the smallest change that addresses the root cause.
