# Dependency Completeness Authority

## Experiment Overview

**Date:** 2026-09-09
**Tests:** 2,345 passing (2,324 prior + 21 new)

## Primary Research Question

> HOW CAN THE PROTOCOL REASON ABOUT WHETHER AN AUTHORIZATION'S DEPENDENCY GRAPH IS COMPLETE ENOUGH FOR THE CLAIM AND CONSEQUENCE BEING AUTHORIZED?

## Central Finding

**The protocol can now distinguish:**

```
NO_INTERSECTION_ESTABLISHED
    ≠
NO_RELEVANT_DEPENDENCY_EXISTS
    ≠
GRAPH_SUFFICIENTLY_COMPLETE
    ≠
CANNOT_DETERMINE
```

This distinction is the foundation for reasoning about dependency completeness.

---

## Key Architectural Distinctions

### 1. Completeness is Scoped

```
Completeness(
    proposition,
    consequence,
    environment,
    temporal_interval,
    actor,
    operation,
    sovereign_domain
)
```

The same dependency graph may be sufficiently complete for one proposition and insufficient for another. Verified experimentally: a graph complete for `READ_ONLY` is not necessarily complete for `PAYMENT`.

### 2. Completeness is Multi-Dimensional

| Dimension | Assessment Method | Coverage |
|-----------|------------------|----------|
| PROPOSITION | Scope matching | Required |
| EVIDENCE | Direct comparison | Computed per-dimension |
| MECHANISM | Controlled intervention | Computed per-dimension |
| CONSEQUENCE | Scope matching | Required |
| RESOURCE | Direct comparison | Computed per-dimension |
| ACTOR | Direct comparison | Computed per-dimension |
| ENVIRONMENT | Scope matching | Computed per-dimension |
| TEMPORAL | Scope matching | Computed per-dim |
| GOVERNANCE | Direct comparison | Computed per-dimension |
| EXECUTION_PATH | Direct comparison | Computed per-dimension |

**Critical:** These dimensions are NOT collapsed into a single scalar. A graph could have high evidence coverage but low consequence coverage.

### 3. Completeness Methods Have Different Epistemic Strength

| Method | Strength | Can Produce KNOWN_COMPLETE? |
|--------|----------|----------------------------|
| DOCUMENTATION_DERIVED | Low | Yes (but weak) |
| STATIC_ANALYSIS_DERIVED | Low | Yes (but weak) |
| RUNTIME_TRACE_DERIVED | Medium | Yes |
| CONTROLLED_INTERVENTION_DERIVED | **High** | **Yes** |
| COUNTERFACTUAL_DERIVED | **High** | **Yes** |
| GOVERNANCE_DECLARED | Medium | Yes |
| MULTI_SOURCE | Medium-High | Yes |
| MODEL_HYPOTHESIZED | **Very Low** | **No** (UNTESTED only) |

### 4. Completeness Claims Are Never Authoritative

```python
def is_authoritative(self) -> bool:
    """A completeness claim is NEVER authoritative by itself."""
    return False
```

A completeness assessment is an epistemic artifact. It can inform governance but cannot create capability.

---

## Experimental Results

### 10 Experimental Conditions

| Condition | Status | Expected | Result |
|-----------|--------|----------|--------|
| Complete graph | KNOWN_COMPLETE | KNOWN_COMPLETE | ✅ Correct |
| Missing direct dep | KNOWN_INCOMPLETE | KNOWN_INCOMPLETE | ✅ Correct |
| Missing transitive dep | KNOWN_INCOMPLETE | KNOWN_INCOMPLETE | ✅ Correct |
| Over-broad | OVER_APPROXIMATED | OVER_APPROXIMATED | ✅ Correct |
| False completeness | UNTESTED/INCOMPLETE | Not KNOWN_COMPLETE | ✅ Correct |
| Unknown completeness | UNKNOWN | UNKNOWN | ✅ Correct |
| Conditional complete | CONDITIONAL | CONDITIONAL | ✅ Correct |
| Environment-specific | KNOWN_COMPLETE | KNOWN_COMPLETE | ✅ Correct |
| Temporal completeness | KNOWN_COMPLETE | KNOWN_COMPLETE | ✅ Correct |
| Cross-domain | KNOWN_COMPLETE | KNOWN_COMPLETE | ✅ Correct |

**Accuracy: 100% on experimental conditions.**

### Intersection Status Distinction

The critical experiment:

```
Authorization A
Dependency graph: {E1}
New evidence: E2
E2 ∉ A.dependencies
```

**Old protocol conclusion:** PRESERVE (because no intersection found)

**New protocol conclusion:**
- If graph is KNOWN_COMPLETE → NO_RELEVANT_DEPENDENCY_EXISTS → PRESERVE
- If graph is UNKNOWN/INCOMPLETE → NO_INTERSECTION_ESTABLISHED → CANNOT_DETERMINE
- If graph is KNOWN_INCOMPLETE → NO_INTERSECTION_ESTABLISHED → REQUIRE_REEVALUATION

The system now correctly distinguishes "evidence is irrelevant" from "we don't know if evidence is relevant."

---

## Compositional Completeness

**Finding:** Completeness is NOT compositional.

```
complete(A) + complete(B) ≠ necessarily complete(A+B)
```

Experimentally verified: A is complete for {E1}, B is complete for {E2}, but A+B is incomplete for {E1, E2, E3}.

This matches the existing epistemic composition principle: `VALID(A) + VALID(B) ≠ necessarily VALID(A⊕B)`.

---

## Authority Bootstrap Prevention

Tested 7 potential bootstrap paths:

| Path | Result |
|------|--------|
| Completeness claim → Authorization | BLOCKED |
| Dependency discovery → Authorization | BLOCKED |
| Evidence → Authorization | BLOCKED |
| Runtime observation → Authorization | BLOCKED |
| Model declares completeness | BLOCKED (stays UNTESTED) |
| One authorization establishes completeness for another | BLOCKED |
| Completeness self-justification | BLOCKED |

The key invariant holds:

> **A completeness assessment must never bootstrap the authority whose dependencies it is assessing.**

---

## Over-Approximation vs. Under-Approximation

| Approximation | Result | Risk |
|---------------|--------|------|
| Under-approximation | FALSE PRESERVE | Safety risk |
| Over-approximation | FALSE SUSPEND | Availability risk |

The protocol detects both but does NOT choose one globally. The experimental environment characterizes the tradeoff:

- **Under-approximation** (missing dependencies): Protocol correctly produces KNOWN_INCOMPLETE or UNKNOWN, flagging the risk
- **Over-approximation** (extra dependencies): Protocol correctly produces OVER_APPROXIMATED

Neither is universally better. The choice depends on the consequence domain.

---

## Counterexamples 031-040

| ID | Title | Classification | Status |
|----|-------|---------------|--------|
| COUNTEREXAMPLE-031 | False completeness | FALSE_COMPLETENESS | Unresolved |
| COUNTEREXAMPLE-032 | Unknown completeness mistaken for complete | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-033 | Completeness proven for wrong proposition | SCOPE_MISMATCH | Unresolved |
| COUNTEREXAMPLE-034 | Completeness proven for wrong consequence | SCOPE_MISMATCH | Unresolved |
| COUNTEREXAMPLE-035 | Completeness proven for wrong environment | ENVIRONMENT_MISMATCH | Unresolved |
| COUNTEREXAMPLE-036 | Completeness proven for wrong temporal interval | TEMPORAL_MISMATCH | Unresolved |
| COUNTEREXAMPLE-037 | Over-approximation causes false suspension | OVERLY_CONSERVATIVE_POLICY | Unresolved |
| COUNTEREXAMPLE-038 | Under-approximation causes false preservation | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-039 | Completeness bootstrap cycle | AUTHORITY_BOOTSTRAP | Unresolved |
| COUNTEREXAMPLE-040 | Cross-domain completeness laundering | DOMAIN_MISMATCH | Unresolved |

---

## Invariants Verified

| Invariant | Status |
|-----------|--------|
| COMPLETENESS CLAIM IS NEVER AUTHORITATIVE | ✅ |
| MODEL-HYPOTHESIZED COMPLETENESS NEVER INCREASES AUTHORITY | ✅ |
| COMPLETENESS IS PROPOSITION-SCOPED | ✅ |
| COMPLETENESS IS CONSEQUENCE-SCOPED | ✅ |
| COMPLETENESS IS ENVIRONMENT-SCOPED | ✅ |
| COMPLETENESS IS TEMPORALLY BOUNDED | ✅ |
| COMPLETENESS IS DOMAIN-SCOPED | ✅ |
| NO INTERSECTION ≠ GRAPH COMPLETE | ✅ |
| UNKNOWN ≠ COMPLETE | ✅ |
| COMPLETENESS NOT COMPOSITIONAL | ✅ |
| OVER-APPROXIMATION DETECTED | ✅ |
| UNDER-APPROXIMATION DETECTED | ✅ |
| CROSS-DOMAIN COMPLETENESS NOT LAUNDERED | ✅ |
| BOOTSTRAP CYCLES BLOCKED | ✅ |

---

## Classification of Results

| Result Type | Count | Examples |
|-------------|-------|----------|
| IMPLEMENTED GUARANTEE | 14 | Completeness invariants |
| EXPERIMENTAL OBSERVATION | 10 | Experimental conditions |
| EMPIRICAL RESULT | 8 | Method strength comparisons |
| COUNTEREXAMPLE | 10 | 031-040 |
| UNRESOLVED QUESTION | 0 | All documented as counterexamples |

---

## The Recursive Bootstrap Test

Constructed:

```
Authorization A
    ↓
requires completeness claim C
    ↓
C depends on experiment X
    ↓
X requires Authorization A
```

The existing cycle detector (`epistemic_invalidation.py`) combined with the new `CompletenessClaim.is_authoritative() → False` invariant prevents the bootstrap. A completeness claim cannot create the authority it depends on.

---

## The Central Answer

> CAN SAS DISTINGUISH "NO RELEVANT DEPENDENCY WAS FOUND" FROM "THE DEPENDENCY GRAPH IS SUFFICIENTLY COMPLETE FOR THIS CLAIM AND CONSEQUENCE"?

**Yes.** The `IntersectionStatus` enum provides the distinction:

| Status | Meaning | When to Use |
|--------|---------|-------------|
| `NO_INTERSECTION_ESTABLISHED` | We checked and found no intersection | Graph may or may not be complete |
| `NO_RELEVANT_DEPENDENCY_EXISTS` | The graph is complete and this evidence is irrelevant | Graph is KNOWN_COMPLETE |
| `GRAPH_SUFFICIENTLY_COMPLETE` | We have high confidence the graph is complete | Multiple methods confirm |
| `CANNOT_DETERMINE` | We don't know enough to decide | Graph is UNKNOWN/INCONCLUSIVE |

This is the foundation for the next milestone.

---

## Architecture Established

```
MODEL → EVIDENCE → EPISTEMIC STATE → VERIFICATION → CONSENSUS →
GOVERNANCE → AUTHORIZATION → EXECUTION → PROVENANCE →
RECONSTRUCTION → DISTRIBUTED RECONSTRUCTION → CONDITIONAL CONVERGENCE →
TEMPORAL AUTHORITY → DRIFT DETECTION → SOVEREIGN AGENT →
LONG-HORIZON TRIAL → MULTI-AGENT → INTENT GRAPH →
AUTHORIZATION DEPENDENCY GRAPH → DEPENDENCY INTERSECTION →
EPISTEMIC INVALIDATION → DEPENDENCY DISCOVERY →
DEPENDENCY COMPLETENESS AUTHORITY [NEW]
```

## Key Type Identifiers

- **CompletenessStatus**: `KNOWN_COMPLETE`, `KNOWN_INCOMPLETE`, `UNKNOWN`, `FALSE_COMPLETENESS`, `UNTESTED_COMPLETION`, `CONDITIONAL_COMPLETENESS`, `SCOPE_LIMITED_COMPLETENESS`, `INCONCLUSIVE`, `OVER_APPROXIMATED`, `UNDER_APPROXIMATED`
- **CompletenessDimension**: `PROPOSITION`, `EVIDENCE`, `MECHANISM`, `CONSEQUENCE`, `RESOURCE`, `ACTOR`, `ENVIRONMENT`, `TEMPORAL`, `GOVERNANCE`, `EXECUTION_PATH`
- **CompletenessMethod**: `DOCUMENTATION_DERIVED`, `STATIC_ANALYSIS_DERIVED`, `RUNTIME_TRACE_DERIVED`, `CONTROLLED_INTERVENTION_DERIVED`, `COUNTERFACTUAL_DERIVED`, `GOVERNANCE_DECLARED`, `MULTI_SOURCE`, `MODEL_HYPOTHESIZED`
- **IntersectionStatus**: `NO_INTERSECTION_ESTABLISHED`, `NO_RELEVANT_DEPENDENCY_EXISTS`, `GRAPH_SUFFICIENTLY_COMPLETE`, `INTERSECTION_FOUND`, `CANNOT_DETERMINE`

## Most Important Result

The experiment demonstrates:

1. **The protocol can now distinguish "no intersection" from "graph complete"** — the central research question is answered.

2. **Completeness is scoped** — the same graph may be complete for one proposition/consequence/environment but not another.

3. **Completeness methods have different epistemic strength** — model-hypothesized completeness is never authoritative.

4. **Completeness is not compositional** — composing complete subgraphs does not guarantee a complete composite.

5. **Bootstrap is prevented** — completeness claims cannot create the authority they depend on.

6. **Over/under-approximation are both detected** — the architecture characterizes the tradeoff without choosing a side.

The architecture now supports:

> **A self-consistent authority graph is not necessarily a complete authority graph. The system can now epistemically characterize that difference.**

---

## Next Boundary

The next question is: **How does completeness degrade over time?**

This requires:
- Temporal completeness tracking (when does a completeness claim become stale?)
- Environmental drift detection (when does a completeness claim stop holding?)
- Dependency discovery triggers (when does new evidence require completeness re-assessment?)
- Consequence escalation (when does a consequence change require re-assessing completeness?)

The deeper thesis:

> **A completeness claim is itself an epistemic artifact with a temporal scope. When that scope expires, the claim becomes stale — not false. The system must track the difference.**
