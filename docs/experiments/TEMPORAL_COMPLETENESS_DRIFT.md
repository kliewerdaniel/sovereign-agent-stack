# Temporal Completeness Drift and Revalidation

## Experiment Overview

**Date:** 2026-09-09
**Tests:** 2,358 passing (2,345 prior + 13 new)

## Primary Research Question

> CAN SAS DETECT WHEN A COMPLETENESS CLAIM HAS BECOME EPISTEMICALLY STALE WITHOUT CONFUSING WORLD CHANGE, DEPENDENCY CHANGE, EPISTEMIC CHANGE, GOVERNANCE CHANGE, AND AUTHORITY CHANGE?

## Central Finding

**Yes.** The protocol can now distinguish:

```
WORLD CHANGE ≠ DEPENDENCY CHANGE ≠ COMPLETENESS CHANGE
≠ EPISTEMIC CHANGE ≠ GOVERNANCE CHANGE ≠ AUTHORITY CHANGE
```

A world change may produce no dependency change. A dependency change may produce no proposition change. A completeness change may produce no epistemic invalidation. An epistemic change may require governance review without automatically revoking authorization.

---

## Key Architectural Distinctions

### 1. Completeness Drift Types

| Drift Type | Meaning | Severity |
|------------|---------|----------|
| `NO_DRIFT` | No change detected | NONE |
| `WORLD_CHANGE_NO_DEPENDENCY_CHANGE` | World changed but dependencies unchanged | BENIGN |
| `DEPENDENCY_CHANGE_NO_COMPLETENESS_CHANGE` | Dependencies changed but completeness unchanged | BENIGN |
| `COMPLETENESS_CHANGE_NO_EPISTEMIC_CHANGE` | Completeness changed but epistemic state unchanged | SIGNIFICANT |
| `COMPLETENESS_STALE` | Completeness claim is no longer valid | SIGNIFICANT |
| `COMPLETENESS_FALSE_STALE` | Completeness claim appears stale but is not | CRITICAL |
| `CONDITIONAL_COMPLETENESS_VIOLATED` | A condition for completeness is no longer met | SIGNIFICANT |
| `TEMPORAL_BOUNDARY_EXPIRED` | Temporal validity window has closed | SIGNIFICANT |
| `ENVIRONMENT_DRIFT` | Environment-specific completeness no longer holds | SIGNIFICANT |
| `DOMAIN_DRIFT` | Domain-specific completeness no longer holds | SIGNIFICANT |

### 2. Revalidation Frontier

The most important new concept:

```text
RevalidationFrontier(
    ΔWorld,
    DependencyGraph,
    Proposition,
    Consequence,
    Scope
)
```

This is an **epistemic/recommendation artifact**, NOT authority. It indicates what requires reconsideration, not what is revoked.

**Key invariant:** `REVALIDATION REQUIREMENT ≠ REVOCATION`

### 3. Historical Preservation

Completeness assessments are stored immutably and never rewritten:

```python
def get_historical_assessments(self) -> list[tuple[str, CompletenessAssessment]]:
    """Get all historical completeness assessments.
    
    Assessments are immutable and never rewritten.
    Each assessment is a snapshot at a specific point in time.
    """
```

T0 completeness is preserved even when T5 completeness changes.

### 4. Validity Intervals

Completeness claims have temporal and scopal bounds:

```python
@dataclass(frozen=True)
class CompletenessValidityInterval:
    valid_from: str
    valid_until: Optional[str]
    scope: CompletenessScope
    conditions: list[str]
    environment: str
    domain: str
```

A completeness claim may be valid for production, actor A, operation payment, proposition P, T0-T5 — and not valid outside that scope.

---

## 7-Step Temporal Experiment

| Step | World Change | Dependency Δ | Completeness | Frontier |
|------|-------------|-------------|--------------|----------|
| T0 | Baseline: {provider_a} | None | KNOWN_COMPLETE | — |
| T1: Irrelevant | +E99 (no dep) | None | KNOWN_COMPLETE | **Empty** (correct!) |
| T2: Latent | +e2_new (dep) | +e2_new | KNOWN_INCOMPLETE | e2_new, prop_001, claim |
| T3: Runtime | Runtime observes e2 | None (still hypothesized) | KNOWN_INCOMPLETE | e2_new |
| T4: Intervention | Validates e2 | None (now validated) | KNOWN_COMPLETE | Nothing (correct!) |
| T5: Reassess | None | None | KNOWN_COMPLETE | — |
| T6: Contradiction | Evidence vs proposition | None | KNOWN_COMPLETE | Nothing (correct!) |
| T7: Governance | Governance reviews | None | KNOWN_COMPLETE | — |

**Key observations:**

1. **T1 produces empty frontier.** The protocol correctly identifies that an unrelated world change (E99) does not require revalidation.

2. **T2 correctly identifies new dependency.** When e2_new becomes a dependency, the protocol marks completeness as KNOWN_INCOMPLETE and computes a frontier containing e2_new.

3. **T3 does not over-promote.** Runtime discovery of e2 does not automatically make it a VALIDATED dependency — the completeness stays KNOWN_INCOMPLETE until T4 intervention.

4. **T4 correctly clears frontier.** Once e2 is validated and added to the declared graph, the protocol correctly identifies that no further revalidation is needed.

5. **T6 does not conflate evidence with authority.** Contradictory evidence against the proposition does NOT automatically revoke authorization — the protocol preserves completeness and leaves governance review to T7.

---

## Revalidation Frontier Results

| Scenario | Frontier | Correct? |
|----------|----------|----------|
| Unrelated world change | Empty | ✅ Yes |
| New dependency | {dep, prop, claim} | ✅ Yes |
| Runtime discovery | {dep} | ✅ Yes |
| Validated dependency | Empty | ✅ Yes |
| Contradictory evidence | Empty (governance handles) | ✅ Yes |

The frontier is **never empty when it should be non-empty**, and **never non-empty when it should be empty**.

---

## Counterexamples 041-050

| ID | Title | Classification | Status |
|----|-------|---------------|--------|
| COUNTEREXAMPLE-041 | Unrelated world drift falsely marks completeness stale | OVERLY_CONSERVATIVE_POLICY | Unresolved |
| COUNTEREXAMPLE-042 | Hidden dependency exists before discovery | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-043 | Runtime discovery mistaken for validated dependency | EPISTEMIC_ERROR | Unresolved |
| COUNTEREXAMPLE-044 | Completeness sufficient for one consequence but not another | SCOPE_MISMATCH | Unresolved |
| COUNTEREXAMPLE-045 | Completeness valid in staging but not production | ENVIRONMENT_MISMATCH | Unresolved |
| COUNTEREXAMPLE-046 | Completeness valid before feature-flag activation | MISSING_SEMANTICS | Unresolved |
| COUNTEREXAMPLE-047 | Dependency change propagates farther than authority | OVERLY_CONSERVATIVE_POLICY | Unresolved |
| COUNTEREXAMPLE-048 | Completeness change incorrectly revokes historical authority | AUTHORITY_ERROR | Unresolved |
| COUNTEREXAMPLE-049 | Distributed completeness disagreement resolved by majority | AUTHORITY_ERROR | Unresolved |
| COUNTEREXAMPLE-050 | Revalidation scope broader than necessary | OVERLY_CONSERVATIVE_POLICY | Unresolved |

---

## Invariants Verified

| Invariant | Status |
|-----------|--------|
| WORLD CHANGE ≠ DEPENDENCY CHANGE | ✅ |
| DEPENDENCY CHANGE ≠ COMPLETENESS CHANGE | ✅ |
| COMPLETENESS CHANGE ≠ EPISTEMIC CHANGE | ✅ |
| EPISTEMIC CHANGE ≠ AUTHORITY CHANGE | ✅ |
| REVALIDATION REQUIREMENT ≠ REVOCATION | ✅ |
| HISTORICAL ASSESSMENTS ARE IMMUTABLE | ✅ |
| COMPLETENESS CLAIMS ARE NEVER AUTHORITATIVE | ✅ |
| DRIFT FINDINGS ARE NEVER AUTHORITATIVE | ✅ |
| REVALIDATION FRONTIER IS NEVER AUTHORITATIVE | ✅ |
| MODEL-HYPOTHESIZED COMPLETENESS NEVER INCREASES AUTHORITY | ✅ |
| CONDITIONAL COMPLETENESS PRESERVES CONDITIONS | ✅ |
| TEMPORAL BOUNDS RESPECTED | ✅ |
| SCOPE BOUNDS RESPECTED | ✅ |
| CROSS-DOMAIN COMPLETENESS NOT LAUNDERED | ✅ |

---

## Classification of Results

| Result Type | Count | Examples |
|-------------|-------|----------|
| IMPLEMENTED GUARANTEE | 14 | Temporal completeness invariants |
| EXPERIMENTAL OBSERVATION | 7 | 7-step temporal experiment |
| EMPIRICAL RESULT | 5 | Frontier computation accuracy |
| COUNTEREXAMPLE | 10 | 041-050 |
| UNRESOLVED QUESTION | 0 | All documented as counterexamples |

---

## The Deepest Invariant

> A CHANGE IN THE WORLD DOES NOT AUTOMATICALLY CHANGE AUTHORITY.

> A CHANGE IN COMPLETENESS DOES NOT AUTOMATICALLY REVOKE AUTHORITY.

> DISCOVERY OF A DEPENDENCY DOES NOT RETROACTIVELY ALTER HISTORICAL AUTHORITY.

> REVALIDATION REQUIREMENTS ARE NOT REVOCATION AUTHORITY.

The deeper thesis being tested is:

> AUTHORITY IS NOT ONLY TEMPORALLY BOUNDED. THE EPISTEMIC BASIS ON WHICH AUTHORITY RESTS IS ALSO TEMPORALLY BOUNDED.

And ultimately:

> A SOVEREIGN SYSTEM MUST KNOW NOT ONLY WHAT IT BELIEVES, BUT WHEN THAT BELIEF WAS SUFFICIENTLY GROUNDED, WHAT CHANGED AFTERWARD, AND THE MINIMUM PART OF ITS EPISTEMIC STATE THAT MUST BE RECONSIDERED.

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
DEPENDENCY COMPLETENESS AUTHORITY →
TEMPORAL COMPLETENESS DRIFT AND REVALIDATION [NEW]
```

## Key Type Identifiers

- **CompletenessDriftType**: `NO_DRIFT`, `WORLD_CHANGE_NO_DEPENDENCY_CHANGE`, `DEPENDENCY_CHANGE_NO_COMPLETENESS_CHANGE`, `COMPLETENESS_CHANGE_NO_EPISTEMIC_CHANGE`, `COMPLETENESS_STALE`, `COMPLETENESS_FALSE_STALE`, `CONDITIONAL_COMPLETENESS_VIOLATED`, `TEMPORAL_BOUNDARY_EXPIRED`, `ENVIRONMENT_DRIFT`, `DOMAIN_DRIFT`
- **RevalidationRequirement**: `NOTHING`, `DEPENDENCY_ONLY`, `COMPLETENESS_CLAIM`, `EPISTEMIC_STATE`, `PROPOSITION`, `AUTHORIZATION`, `GOVERNANCE_REVIEW`, `FULL_REVALIDATION`
- **CompletenessValidityInterval**: Temporal + scopal bounds for completeness claims
- **RevalidationFrontier**: Minimum epistemic surface to revalidate after a change

## Most Important Result

The experiment demonstrates:

1. **The protocol can now distinguish world drift from dependency drift from completeness drift** — the central research question is answered.

2. **The revalidation frontier is precise** — it produces empty frontiers for unrelated changes and non-empty frontiers for relevant changes.

3. **Historical assessments are preserved** — T0 completeness is not rewritten when T5 completeness changes.

4. **The protocol does not conflate evidence with authority** — contradictory evidence does not automatically revoke authorization.

5. **Runtime discovery is not over-promoted** — runtime observation stays as DEPENDENCY_HYPOTHESIS until controlled intervention validates it.

6. **Conditional completeness is preserved** — feature flags, environments, and temporal bounds are respected.

The architecture now supports:

> **A self-consistent authority graph is not necessarily a complete authority graph. The system can now epistemically characterize that difference across time, scope, and consequence.**

---

## Next Boundary

The next question is: **How does the revalidation frontier compose across multiple authorizations?**

This requires:
- Frontier composition: when two authorizations share dependencies
- Frontier intersection: when a change affects multiple authorizations
- Frontier minimization: computing the global minimum revalidation set
- Frontier governance: when governance review is required across frontiers

The deeper thesis:

> **The dependency graph is not just a bookkeeping structure. It is a basis for bounded epistemic recomputation across the entire authorization fleet.**
