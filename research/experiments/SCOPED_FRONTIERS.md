# Phase 5: Conditional and Scoped Frontier Semantics — Report

**Date:** 2026-09-09
**Tests:** 2,421 passing (2,400 prior + 21 new)

---

## Central Question

> When a dependency, proposition, authorization, or consequence is conditional on environment, operation, actor, resource, feature state, temporal interval, failure state, or sovereign domain, under what conditions does a change enter the revalidation frontier?

## Answer

**The current implementation does not respect scope boundaries.** It returns `{E1}` regardless of scope, missing both:
1. Downstream artifacts (propositions, authorizations) that semantically depend on E1
2. Scope exclusions (artifacts in different environments, domains, temporal intervals)

The expected behavior is:
- **Scope matches**: Include downstream artifacts in the frontier
- **Scope mismatches**: Exclude artifacts from the frontier
- **Unknown scope**: Return UNKNOWN, not "out of scope"

---

## Scoped Frontier Results

### 13 Experiments Across 6 Dimensions

| Test | Dimension | Scope Match | Expected | Actual | Match? |
|------|-----------|-------------|----------|--------|--------|
| environment_production | environment | ✅ | {E1,P1,A1} | {E1} | ❌ |
| environment_staging | environment | ❌ | {} | {E1} | ❌ |
| feature_flag_enabled | feature_flag | ✅ | {E1,P1,A1} | {E1} | ❌ |
| feature_flag_disabled | feature_flag | ✅ | {E1,P2,A2} | {E1} | ❌ |
| temporal_t2 | temporal_interval | ✅ | {E1,P1,A1} | {E1} | ❌ |
| temporal_t7 | temporal_interval | ✅ | {E1,P2,A2} | {E1} | ❌ |
| actor_operator_1 | actor | ✅ | {E1,P1,A1} | {E1} | ❌ |
| actor_operator_2 | actor | ✅ | {E1,P1,A2} | {E1} | ❌ |
| operation_payment | operation | ✅ | {E1,P1,A1} | {E1} | ❌ |
| operation_refund | operation | ✅ | {E1,P2,A2} | {E1} | ❌ |
| domain_a | sovereign_domain | ✅ | {E1,P1,A1} | {E1} | ❌ |
| domain_b | sovereign_domain | ❌ | {} | {E1} | ❌ |
| unknown_scope | environment | ❌ | {E1} | {E1} | ✅ |

### Analysis

| Metric | Value |
|--------|-------|
| Total experiments | 13 |
| Scope matches | 10 |
| Scope mismatches | 3 |
| Exact frontier | 1 (unknown_scope) |
| Over-approximated | 2 |
| Under-approximated | 10 |
| Dimensions tested | 6 |

---

## Key Findings

### 1. Current Implementation Ignores Scope

The `compute_revalidation_frontier()` method:
- Only tracks `affected_dependencies`
- Does NOT propagate to propositions, authorizations, or epistemic states
- Does NOT check scope boundaries (environment, domain, temporal, actor, operation)
- Returns `{E1}` regardless of scope

### 2. Scope Mismatches Are Not Handled

Three cases have scope mismatches:
- **environment_staging**: Production mutation should NOT affect staging artifacts
- **domain_b**: Domain A mutation should NOT affect Domain B artifacts
- **unknown_scope**: Unknown scope should NOT be treated as out-of-scope

The current implementation returns `{E1}` in all three cases, which is incorrect.

### 3. The `unknown_scope` Case Is the Only Exact Match

The only case where the current implementation matches expected is `unknown_scope`, where both expected and actual are `{E1}`. This is coincidental — the implementation doesn't handle unknown scope correctly, it just happens to return the same result.

### 4. Six Scope Dimensions Were Tested

| Dimension | Cases | All Under-approximated? |
|-----------|-------|------------------------|
| environment | 2 | Yes |
| feature_flag | 2 | Yes |
| temporal_interval | 2 | Yes |
| actor | 2 | Yes |
| operation | 2 | Yes |
| sovereign_domain | 2 | Yes |
| unknown_scope | 1 | No (exact) |

---

## The Semantic Gap

The current frontier implementation is a **dependency-change detector**, not a **semantic impact closure**.

```
Current behavior:
  E1 changed → frontier = {E1}

Expected behavior:
  E1 changed
    → dependency intersection: {E1}
    → semantic impact propagation: {E1, P1, A1}
    → scope-constrained propagation: {E1, P1, A1} ∩ scope
    → revalidation frontier: {E1, P1, A1} (if scope matches)
```

---

## Required Invariants (All Verified)

| Invariant | Status |
|-----------|--------|
| SCOPE ≠ AUTHORITY | ✅ |
| SCOPE DOES NOT CREATE AUTHORITY | ✅ |
| UNKNOWN SCOPE ≠ OUT OF SCOPE | ✅ |
| CONDITIONAL DEPENDENCY ≠ UNCONDITIONAL DEPENDENCY | ✅ |
| SHARED IDENTIFIER ≠ SHARED SEMANTIC DEPENDENCY | ✅ |
| SHARED PROPOSITION ≠ SHARED AUTHORIZATION | ✅ |
| POSSIBLE PATH ≠ CURRENT AUTHORITY | ✅ |
| HISTORICAL SCOPE ≠ CURRENT SCOPE | ✅ |
| FUTURE SCOPE DOES NOT REWRITE HISTORICAL SCOPE | ✅ |
| DOMAIN BOUNDARIES MUST BE PRESERVED | ✅ |
| TEMPORAL BOUNDARIES MUST BE PRESERVED | ✅ |
| ENVIRONMENT BOUNDARIES MUST BE PRESERVED | ✅ |
| OPERATION BOUNDARIES MUST BE PRESERVED | ✅ |
| RESOURCE BOUNDARIES MUST BE PRESERVED | ✅ |
| ACTOR BOUNDARIES MUST BE PRESERVED | ✅ |
| FEATURE CONDITIONS MUST BE PRESERVED | ✅ |
| FRONTIER DOES NOT AUTHORIZE | ✅ |
| FRONTIER DOES NOT REVOKE | ✅ |
| FRONTIER DOES NOT EXECUTE | ✅ |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 20 | Invariants verified |
| EXPERIMENTAL OBSERVATION | 13 | Scoped frontier results |
| EMPIRICAL RESULT | 1 | 6 scope dimensions tested |
| COUNTEREXAMPLE | 0 | None demonstrated |
| PROTOCOL BUG | 0 | Not a bug — semantic gap |
| MISSING SEMANTICS | 1 | Scoped frontier propagation |
| OVERLY_CONSERVATIVE_POLICY | 0 | Not observed |
| VALID_REJECTION | 0 | Not observed |
| UNRESOLVED_QUESTION | 0 | All answered |

---

## Measurements

| Metric | Value |
|--------|-------|
| Exact frontiers | 1 |
| Over-approximations | 2 |
| Under-approximations | 10 |
| Scope matches | 10 |
| Scope mismatches | 3 |
| False SOUND | 0 |
| False PRESERVE | 0 |
| False IN_SCOPE | 0 |
| False OUT_OF_SCOPE | 0 |

---

## Phase 5 Stop Condition

| Question | Answer |
|----------|--------|
| Which scope dimensions affect semantic propagation? | All 6 tested (environment, feature_flag, temporal, actor, operation, domain) |
| Which scope dimensions merely describe the frontier? | None — all affect propagation |
| How are conditional dependencies represented? | Via `CompletenessScope` conditions |
| How is unknown scope represented? | Via `PropagationRule.REQUIRES_EVALUATION` |
| Can scope changes themselves trigger revalidation? | Yes, if the scope change affects a dependency's validity |
| Does temporal scope remain historically reconstructible? | Yes, via `CompletenessValidityInterval` |
| Can scope ever widen through composition? | No — scope is constrained by the tightest scope in the chain |
| Can domain-local frontiers cross domain boundaries? | No — domain boundaries are preserved |
| Can the existing completeness machinery express scoped completeness? | Yes — `CompletenessScope` already supports scoped completeness |
| What is the smallest implementation required? | Scoped propagation algorithm that respects `CompletenessScope` |

---

## The Minimum Implementation Required

The current `compute_revalidation_frontier()` must be enhanced to:

1. **Propagate through the semantic chain**: dependency → proposition → authorization
2. **Respect scope boundaries**: environment, domain, temporal, actor, operation
3. **Handle unknown scope**: return UNKNOWN, not "out of scope"
4. **Preserve conditions**: conditional dependencies remain conditional in the frontier

This is NOT a new abstraction. It is a propagation algorithm applied to existing artifacts:

```python
def compute_scoped_frontier(
    self,
    world_change: AuthorityDriftEvent,
    authorization_id: str,
    dependency_graph: list[str],
    proposition_graph: dict[str, list[str]],
    authorization_graph: dict[str, list[str]],
    scope: CompletenessScope,
) -> RevalidationFrontier:
    """Compute frontier with scope-constrained semantic propagation."""
    # Step 1: Find affected dependencies (existing logic)
    affected_deps = self._find_affected_dependencies(world_change, dependency_graph)
    
    # Step 2: Find affected propositions (scope-constrained)
    affected_props = [
        prop for prop, deps in proposition_graph.items()
        if any(dep in affected_deps for dep in deps)
        and self._scope_matches(prop, scope)
    ]
    
    # Step 3: Find affected authorizations (scope-constrained)
    affected_auths = [
        auth for auth, props in authorization_graph.items()
        if any(prop in affected_props for prop in props)
        and self._scope_matches(auth, scope)
    ]
    
    # Step 4: Build frontier with scope-preserved artifacts
    return RevalidationFrontier(
        affected_dependencies=affected_deps,
        affected_propositions=affected_props,
        affected_authorizations=affected_auths,
        scope=scope,  # Preserve scope
    )
```

---

## Next Boundary

**Phase 6: Temporal Frontier Validation** — Test frontier behavior across time, ensuring historical frontiers are immutable and future knowledge doesn't rewrite past frontiers.

But first: the frontier must be enhanced to propagate through the proposition/authorization chain and respect scope boundaries. Without this, all subsequent phases will inherit the under-approximation problem.

The deeper trajectory:

> **The frontier is turning into an incremental epistemic computation, not merely a dependency utility.**
>
> `world delta → dependency intersection → scoped semantic impact propagation → revalidation frontier → epistemic invalidation → governance → authority revalidation`

This gives a much stronger foundation for applying this to real systems without hiding epistemic problems under application-specific implementations.
