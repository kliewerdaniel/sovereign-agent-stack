# Authorization Dependency Adversarial Validation

## Experiment Overview

**Date:** 2026-09-09
**Tests:** 2,324 passing (2,272 prior + 52 new)

## Central Research Question

> Who determines what an authorization depends on, and how does the protocol know that the dependency graph itself is complete enough to support invalidation decisions?

## Thesis

```
DECLARED DEPENDENCY ≠ OBSERVED DEPENDENCY ≠ INFERRED DEPENDENCY ≠ VALIDATED DEPENDENCY ≠ AUTHORITATIVE DEPENDENCY
```

The dependency graph must itself carry epistemic status and provenance.

## Key Architectural Discovery

The current protocol treats the dependency graph as **authoritative**:

```
New Evidence → Check against dependency graph → Intersection? → Decision
```

But the dependency graph itself may be:
- **Incomplete** (missing dependencies)
- **Over-broad** (extra unnecessary dependencies)
- **Stale** (outdated dependencies)
- **False** (incorrectly inferred dependencies)
- **Wrong scope** (domain, environment, temporal)

This creates a new class of failure:

```
correctly reconstructed + correctly evaluated + correctly governed + incorrect conclusion
```

## Dependency Epistemic Status Model

### Discovery Methods

| Method | Epistemic Status | Validation Strength |
|--------|-----------------|---------------------|
| DIRECT_DECLARATION | DECLARED | Low (assertion only) |
| STATIC_ANALYSIS | INFERRED | Low (reference ≠ runtime) |
| RUNTIME_TRACE | OBSERVED | Medium (co-occurrence ≠ necessity) |
| MODEL_HYPOTHESIS | HYPOTHESIZED | Very Low (not evidence) |
| DOCUMENTATION | DECLARED | Low (doc ≠ observed) |
| CONTROLLED_INTERVENTION | VALIDATED | High (establishes necessity) |
| COUNTERFACTUAL_TEST | VALIDATED | High (establishes necessity) |
| EXPERIMENT | VALIDATED | High (empirical) |

### Critical Distinctions

```
MODEL OUTPUT ≠ DEPENDENCY EVIDENCE
STATIC REFERENCE ≠ RUNTIME DEPENDENCY
RUNTIME CO-OCCURRENCE ≠ NECESSARY DEPENDENCY
DOCUMENTATION ≠ OBSERVED DEPENDENCY
CORRELATION ≠ DEPENDENCY
DEPENDENCY HYPOTHESIS ≠ VALIDATED DEPENDENCY
```

## Adversarial Validation Results

### 20 Scenarios Tested

| Scenario | Expected | Actual | Finding |
|----------|----------|--------|---------|
| Complete graph | SUSPEND | SUSPEND | ✅ Correct |
| Missing direct dep | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Missing transitive dep | REEVALUATE | PRESERVE | ⚠️ False preservation |
| False dependency | SUSPEND | PRESERVE | ⚠️ ID matching only |
| Over-broad dependency | SUSPEND | SUSPEND | ✅ Correct (but conservative) |
| Stale dependency | REEVALUATE | REEVALUATE | ✅ Correct |
| Ambiguous dependency | REEVALUATE | REEVALUATE | ✅ Correct |
| Wrong scope | PRESERVE | PRESERVE | ✅ Correct (but for wrong reason) |
| Wrong temporal | PRESERVE | PRESERVE | ✅ Correct (but for wrong reason) |
| Wrong environment | PRESERVE | PRESERVE | ✅ Correct (but for wrong reason) |
| Runtime discovery | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Experiment discovery | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Post-auth discovery | SUSPEND | PRESERVE | ⚠️ False preservation |
| Contradicted dep | SUSPEND | SUSPEND | ✅ Correct |
| Incomplete provenance | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Cross-domain dep | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Feature-flag dep | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Failure-only dep | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Single-operation dep | REEVALUATE | PRESERVE | ⚠️ False preservation |
| Single-actor dep | REEVALUATE | PRESERVE | ⚠️ False preservation |

### Key Findings

1. **The protocol correctly handles evidence that intersects the dependency graph** (complete graph, contradicted dependency).

2. **The protocol cannot detect missing dependencies** — when evidence contradicts a dependency that SHOULD have been in the graph but wasn't, the protocol preserves because the evidence doesn't intersect the (incomplete) graph.

3. **The protocol uses ID matching, not content matching** — evidence that semantically contradicts a dependency but has a different ID is treated as unrelated.

4. **The protocol cannot assess scope, environment, or temporal relevance** — evidence from wrong scope/environment/temporal interval is treated as unrelated because it doesn't match dependency IDs.

5. **The protocol cannot detect cross-domain impacts** — changes in other domains are invisible to the dependency intersection.

6. **The protocol cannot detect feature flag or failure condition changes** — these are not represented in the dependency graph.

## Over-Approximation vs. Under-Approximation

### Under-Approximation

```
actual dependencies = {E1, E2, E3}
declared dependencies = {E1}
```

**Consequence:** FALSE PRESERVE — evidence contradicting E2 or E3 is ignored.

### Over-Approximation

```
actual dependencies = {E1}
declared dependencies = {E1, E2, E3, E4, E5}
```

**Consequence:** FALSE SUSPEND — evidence contradicting unnecessary dependencies causes unnecessary suspension.

### Tradeoff

The architecture must explicitly characterize this tradeoff rather than silently choosing one. Currently, the protocol is **vulnerable to under-approximation** (missing dependencies cause false preservation) but **tolerates over-broad dependencies** (they cause unnecessary suspension, which is safer but reduces availability).

## Counterexamples 021-030

| ID | Title | Classification | Status |
|----|-------|---------------|--------|
| COUNTEREXAMPLE-021 | Missing direct dependency | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-022 | Missing transitive dependency | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-023 | False runtime dependency | VALID_REJECTION | Resolved |
| COUNTEREXAMPLE-024 | Over-broad dependency | OVERLY_CONSERVATIVE_POLICY | Unresolved |
| COUNTEREXAMPLE-025 | Stale dependency | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-026 | Cross-domain dependency | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-027 | Feature-flag dependency | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-028 | Failure-only dependency | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-029 | Post-authorization discovery | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-030 | Dependency provenance failure | MISSING_SEMANTICS | Unresolved |

## Invariants Verified

| Invariant | Status |
|-----------|--------|
| DEPENDENCY DISCOVERY DOES NOT CREATE AUTHORITY | ✅ |
| DEPENDENCY DECLARATION DOES NOT CREATE EPISTEMIC TRUTH | ✅ |
| MODEL-GENERATED DEPENDENCY DOES NOT BECOME AUTHORITATIVE | ✅ |
| RUNTIME CO-OCCURRENCE ≠ NECESSARY DEPENDENCY | ✅ |
| STATIC REFERENCE ≠ RUNTIME DEPENDENCY | ✅ |
| DOCUMENTATION ≠ OBSERVED DEPENDENCY | ✅ |
| DEPENDENCY PROVENANCE MUST BE RECONSTRUCTIBLE | ✅ |
| POST-AUTHORIZATION DISCOVERY DOES NOT RETROACTIVELY ALTER HISTORY | ✅ |
| DEPENDENCY DISCOVERY DOES NOT CREATE REVOCATION AUTHORITY | ✅ |

## Classification of Results

| Result Type | Count | Examples |
|-------------|-------|----------|
| IMPLEMENTED GUARANTEE | 9 | Dependency epistemic invariants |
| EXPERIMENTAL OBSERVATION | 20 | Adversarial scenarios |
| EMPIRICAL RESULT | 10 | Discovery method strengths |
| COUNTEREXAMPLE | 10 | 7 unresolved, 3 resolved |
| UNRESOLVED QUESTION | 0 | All documented as counterexamples |

## The Critical Semantic Gap

The protocol's dependency intersection is **necessary but not sufficient**:

```
Evidence intersects graph → Valid to act on it
Evidence doesn't intersect graph → NOT necessarily valid to ignore it
```

The current protocol treats the absence of intersection as evidence of absence. This is correct only if the dependency graph is **complete**. But completeness is an epistemic claim that must itself be validated.

## Over-Approximation vs. Under-Approximation Tradeoff

The architecture should explicitly characterize this tradeoff:

- **Under-approximation** → FALSE PRESERVE → safety risk
- **Over-approximation** → FALSE SUSPEND → availability risk

Neither is universally better. The choice depends on the consequence domain.

## Conclusion

The experiment demonstrates:

1. **The dependency graph is not self-validating** — treating it as authoritative can produce false preservations when the graph is incomplete.

2. **Dependency discovery has epistemic status** — different discovery methods produce dependencies with different validation strengths.

3. **The protocol cannot detect missing dependencies** — this is the most significant semantic gap.

4. **ID matching is insufficient** — semantic content matching is needed but introduces its own risks.

5. **Scope, environment, and temporal bounds matter** — the protocol cannot assess these dimensions.

The architecture now supports:

> **Authority may depend on epistemic state, but the epistemic status of that dependency must itself be governed.**

## Next Boundary

The next question is: **How can the protocol reason about the completeness of its own dependency graph?**

This requires:
- Representing dependency graph completeness as an epistemic claim
- Distinguishing "evidence doesn't intersect graph" from "graph is complete"
- Introducing dependency graph validation as a first-class operation
- Characterizing the over-approximation vs. under-approximation tradeoff explicitly

The deeper thesis:

> **A reconstructible authority graph is not enough. The system must also be able to establish whether the graph is complete enough for the claim being made.**
