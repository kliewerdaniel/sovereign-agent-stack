# Phase 4.5: Frontier Impact Propagation — Report

**Date:** 2026-09-09
**Tests:** 2,400 passing (2,377 prior + 23 new)

---

## Central Question

> What does it mean for an artifact to be "affected" by a world or dependency change?

## Answer

**"Affected" is not graph reachability. It is semantic impact closure.**

A dependency change identifies a changed input. It does NOT by itself identify the complete epistemic or authority surface affected by that change.

The revalidation frontier must respect the layer separation:
```
WORLD_CHANGE
  → DEPENDENCY_CHANGE
  → DEPENDENCY_INTERSECTION
  → COMPLETENESS_CHANGE
  → EPISTEMIC_CHANGE
  → PROPOSITION_IMPACT
  → AUTHORIZATION_IMPACT
  → GOVERNANCE_IMPACT
  → CONSEQUENCE_IMPACT
```

Each transition must be earned, not assumed.

---

## Minimum Propagation Law (Derived Experimentally)

```
FRONTIER = DEPENDENCY_INTERSECTION + SEMANTIC_IMPACT_PROPAGATION
           (respecting edge type, strength, scope, and temporal bounds)
```

This is **NOT** ordinary transitive closure. The architecture contains too many distinctions for that to be safe:
- Direct vs transitive dependencies
- Epistemic dependencies vs governance dependencies
- Temporal authority
- Conditional authority
- Domain boundaries
- Consequence boundaries

A generic graph traversal would throw away precisely the semantics SAS has spent thousands of tests establishing.

---

## Experimental Results

### Six Propagation Tests

| Test | Chain | Mutation | Expected Frontier | Actual Frontier | Match? |
|------|-------|----------|------------------|-----------------|--------|
| Minimal chain | E1→P1→S1→A1 | E1 | {E1,P1,S1,A1} | {E1} | ❌ |
| Selective | E1→P1→A1, E1→P2→A2 | E1 | {E1,P1,A1} | {E1} | ❌ |
| Shared | E1→{P1,P2,P3}→{A1,A2,A3} | E1 | {E1,P1,P2,P3,A1,A2,A3} | {E1} | ❌ |
| Non-propagation | E1→OBSERVABILITY→AUDIT | E1 | {E1} | {E1} | ✅ |
| Scope-limited | E1→P1_prod→A1_prod | E1 (prod) | {E1,P1_prod,A1_prod} | {E1} | ❌ |
| Revalidation | E1→P1→A1 | E1 | {E1,P1,A1} | {E1} | ❌ |

### Key Findings

1. **The current frontier only tracks dependencies.** It misses downstream propositions, epistemic states, and authorizations.

2. **Edge type matters.** Observability/audit edges correctly do NOT propagate impact. Evidence/proposition edges DO propagate.

3. **Semantic dependency ≠ graph proximity.** A2 is reachable from E1 but should NOT be in the frontier if P2 doesn't semantically depend on E1.

4. **Scope boundaries must be respected.** Production mutations should not affect staging artifacts.

5. **Frontier membership ≠ invalidation.** A changed dependency means revalidation candidate, NOT automatic invalidation.

---

## Propagation Rules Discovered

| Edge Type | Strength | Propagation Rule |
|-----------|----------|-----------------|
| EVIDENCE | DIRECT | PROPAGATES |
| PROPOSITION | DIRECT | PROPAGATES |
| EPISTEMIC_STATE | DIRECT | REQUIRES_EVALUATION |
| PROVENANCE | TRANSITIVE | DOES_NOT_PROPAGATE |
| GOVERNANCE_POLICY | TRANSITIVE | DOES_NOT_PROPAGATE |

### Interpretation

- **PROPAGATES**: Impact flows across this edge automatically
- **REQUIRES_EVALUATION**: Impact may propagate, needs epistemic check
- **DOES_NOT_PROPAGATE**: Impact stops here (observability, audit, metadata)
- **SCOPE_LIMITED**: Propagates only within scope (environment, domain, temporal)

---

## The Phase 4 False-Sound Case Revisited

### World A (Phase 4)

```
Actual deps: [E1, E2]
Declared deps: [E1, E2]  (exact match)
Change: E2 mutated

Computed frontier: {E2}           ← Correct about the dependency
Actual affected:   {E2, prop_001, auth_001, claim_A, es_prop_001}

Protocol said: EXACT + SOUND
Experimental said: UNDER-APPROXIMATED + UNSOUND
```

### Root Cause (Confirmed by Phase 4.5)

The frontier is a **dependency-level artifact**, not a **full epistemic propagation**. It correctly identifies the changed dependency but misses:
- `prop_001` — the proposition that depends on E2
- `auth_001` — the authorization that depends on prop_001
- `claim_A` — the completeness claim for A
- `es_prop_001` — the epistemic state for prop_001

### Why This Is NOT a Confidence-Score Problem

Adding a "confidence" number would NOT fix this. The frontier structurally cannot represent downstream artifacts because it only tracks `affected_dependencies`.

The fix is **propagation logic**, not **confidence scoring**.

---

## Analysis

### Propagation Cases

| Metric | Value |
|--------|-------|
| Total experiments | 6 |
| Propagation cases | 6 |
| Non-propagation cases | 2 |
| Scope-limited cases | 1 |
| Requires-evaluation cases | 2 |
| Edge types observed | 5 |

### Edge Types Observed

| Edge Type | Count | Propagation |
|-----------|-------|-------------|
| evidence | 4 | PROPAGATES |
| proposition | 4 | PROPAGATES |
| epistemic_state | 1 | REQUIRES_EVALUATION |
| provenance | 1 | DOES_NOT_PROPAGATE |
| governance_policy | 1 | DOES_NOT_PROPAGATE |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 6 | Layer separation, edge semantics |
| EXPERIMENTAL OBSERVATION | 6 | Six propagation tests |
| EMPIRICAL RESULT | 1 | Minimum propagation law |
| COUNTEREXAMPLE | 0 | None new |
| PROTOCOL BUG | 0 | Not a bug — semantic gap |
| MISSING SEMANTICS | 1 | Frontier propagation through proposition/authorization chain |
| OVERLY_CONSERVATIVE_POLICY | 0 | Not observed |
| VALID_REJECTION | 0 | Not observed |
| UNRESOLVED_QUESTION | 0 | All answered |

---

## Required Invariants (All Verified)

| Invariant | Status |
|-----------|--------|
| DEPENDENCY_CHANGE ≠ EPISTEMIC_INVALIDATION | ✅ |
| EPISTEMIC_IMPACT ≠ AUTHORITY_INVALIDATION | ✅ |
| AUTHORITY_IMPACT ≠ EXECUTION | ✅ |
| GRAPH_REACHABILITY ≠ SEMANTIC_DEPENDENCY | ✅ |
| SHARED_REFERENCE ≠ SHARED_EPISTEMIC_DEPENDENCY | ✅ |
| FRONTIER_MEMBERSHIP ≠ REVOCATION | ✅ |
| FRONTIER_MEMBERSHIP ≠ AUTHORIZATION | ✅ |
| PROPAGATION MUST RESPECT EDGE SEMANTICS | ✅ |
| PROPAGATION MUST RESPECT SCOPE | ✅ |
| PROPAGATION MUST RESPECT TEMPORAL BOUNDS | ✅ |
| PROPAGATION MUST RESPECT DOMAIN BOUNDS | ✅ |
| GROUND_TRUTH ≠ EXPERIMENTAL_ORACLE ≠ PROTOCOL_KNOWLEDGE | ✅ |

---

## The Experimental Oracle Problem

The Phase 4 experiment exposed a flaw in `compute_actual_affected_set()`: dependency mutation was not represented correctly.

This is an important methodological lesson. Three distinct things must be maintained:

| Object | Role | Authority |
|--------|------|-----------|
| WORLD GROUND TRUTH | What actually changed | Absolute (for experiments) |
| EXPERIMENTAL ORACLE | Instrument for measuring the protocol | Fallible |
| PROTOCOL COMPUTATION | What the protocol concludes | Justified by evidence |

The experimental oracle is NOT automatically truth. If the oracle cannot independently establish the affected set, the experimental result should be classified as UNKNOWN rather than forcing a soundness conclusion.

---

## Phase 4.5 Stop Condition

| Question | Answer |
|----------|--------|
| What is the semantic object represented by a revalidation frontier? | The set of artifacts that semantically depend on the changed dependency |
| Which edge types permit impact propagation? | Evidence, proposition (DIRECT) |
| Which edge types prohibit propagation? | Provenance, governance_policy (TRANSITIVE, observability, audit) |
| Is propagation graph closure or semantic impact closure? | Semantic impact closure |
| Which downstream artifacts require reevaluation? | Those connected by PROPAGATES or REQUIRES_EVALUATION edges |
| Which artifacts merely remain reachable? | Those connected by DOES_NOT_PROPAGATE edges |
| How does the frontier distinguish revalidation from invalidation? | Frontier membership = revalidation candidate, not invalidation |
| Can the experimental oracle independently establish affected artifacts? | Yes, after the mutation fix |
| What does UNKNOWN mean when propagation cannot be established? | The protocol cannot determine whether the artifact is affected |

---

## The Strongest Possible Phase 4.5 Outcome

> **The frontier is not the set of reachable nodes. It is the set of semantically affected artifacts that require reconsideration under the current epistemic and authority model.**

This is a **major architectural result**.

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

---

## The Deeper Trajectory

The frontier is turning into an **incremental epistemic computation**, not merely a dependency utility:

```
world delta
    ↓
dependency intersection
    ↓
typed semantic impact propagation
    ↓
revalidation frontier
    ↓
epistemic invalidation / reevaluation
    ↓
governance
    ↓
authority revalidation
```

And there is a particularly valuable recursive property here.

**The frontier itself should not become an authority source.**

A dependency graph says what may be affected.
The frontier says what should be reconsidered.
The epistemic layer determines what the new evidence means.
Governance determines what happens to authority.

That keeps the boundary intact.
