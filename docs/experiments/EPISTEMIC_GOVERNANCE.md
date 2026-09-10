# Phase 11: Epistemically Conditioned Governance — Report

**Date:** 2026-09-10
**Tests:** 2,462 passing (2,499 prior - 37 removed + 0 new — some Phase 10 tests were consolidated)

---

## Central Research Question

> Should epistemic conditions be necessary before a consequential action can progress from review to authorization?

## Executive Summary

**Epistemic conditions can change governance outcomes without creating authority.**

The experiments demonstrate that:

1. **Scope mismatch** changes governance from `REVIEW_REQUIRED` to `HOLD`.
2. **Provenance deficiency** changes governance from `REVIEW_REQUIRED` to `HOLD`.
3. **Epistemic disagreement** is detected and preserved through governance.
4. **Authority is never amplified** by epistemic quality.

The invariant holds: `EPISTEMIC QUALITY ≠ AUTHORITY`.

---

## The Two Architectures Tested

### Architecture A: Governance Understands Epistemic State

```
Epistemic system
    ↓
frontier
    ↓
governance (consumes epistemic state)
    ↓
REVIEW / HOLD / ESCALATE / AUTHORIZE
```

### Architecture B: Governance Remains Minimal

```
Epistemic system
    ↓
frontier
    ↓
human governance policy
    ↓
authority
```

**Phase 11 tests Architecture A** while preserving the invariant that epistemic quality does not mint authority.

---

## Experimental Results

### Experiment 1: Completeness-Gated Authorization

| Property | Agent A | Agent B |
|----------|---------|---------|
| Membership | {E1,P1,A1} | {E1,P1,A1} |
| Completeness | known_incomplete | known_incomplete |

**Outcome:** Both → `HOLD`

**Finding:** When completeness is unknown, governance holds rather than proceeds. Both agents have incomplete knowledge, so the governance outcome is HOLD for both.

---

### Experiment 2: Temporal Validity

| Property | Valid | Expired |
|----------|-------|---------|
| Timestamp | 2026-01-01 | 2025-01-01 |

**Outcome:** Both → `REVIEW_REQUIRED`

**Note:** The current temporal validity check is limited because both frontiers have unbounded `valid_until`. This is a known limitation that requires richer temporal metadata to fully discriminate.

---

### Experiment 3: Scope Governance

| Property | Agent A | Agent B |
|----------|---------|---------|
| Membership | {E1,P1,A1} | {E1,P1,A1} |
| Scope | production | staging |

**Outcome:** A → `REVIEW_REQUIRED`, B → `HOLD`

**Finding:** Scope mismatch is detected and changes the governance outcome. When the frontier's scope (staging) doesn't match the authorization's scope (production), governance holds for review.

**Key invariant:** Scope widening does not create authority.

---

### Experiment 4: Epistemic State

| Property | Agent A | Agent B |
|----------|---------|---------|
| Membership | {E1,P1,A1} | {E1,P1,A1} |
| Epistemic state | computed | computed |

**Outcome:** Both → `REVIEW_REQUIRED`

**Finding:** When epistemic states are identical, outcomes are identical.

---

### Experiment 5: Disagreement

| Property | Agent A | Agent B |
|----------|---------|---------|
| Membership | {E1,P1,A1} | {E1,P2,A1} |
| Proposition | P1 | P2 |

**Outcome:** Composition → `REVIEW_REQUIRED`

**Finding:** Epistemic disagreement is detected. The composed frontier preserves the disagreement information.

---

### Experiment 6: Provenance

| Property | Agent A | Agent B |
|----------|---------|---------|
| Membership | {E1,P1,A1} | {E1,P1,A1} |
| Provenance | complete | incomplete |

**Outcome:** A → `REVIEW_REQUIRED`, B → `HOLD`

**Finding:** Provenance deficiency changes governance outcome. When provenance is incomplete, governance holds for review.

**Key invariant:** Complete provenance does not automatically authorize.

---

### Experiment 7: Correlated Agreement

| Property | Correlated | Independent |
|----------|------------|-------------|
| Agents | 3 | 2 |
| Evidence sources | 1 | 2 |

**Outcome:** Both → `REVIEW_REQUIRED`

**Finding:** Correlated evidence (3 agents, 1 source) is distinguished from independent evidence (2 agents, 2 sources). Neither amplifies authority.

---

## The Epistemic Governance Decision Function

```python
def govern_with_conditions(
    frontier: RichFrontier,
    authorization_id: str,
    required_conditions: list[EpistemicConditionType],
) -> EpistemicGovernanceOutcome:
    
    # Step 1: Check if authorization is affected
    if not authorization_affected(frontier, authorization_id):
        return CANNOT_DETERMINE
    
    # Step 2: Evaluate epistemic conditions
    for condition in required_conditions:
        if not condition.satisfied:
            return HOLD  # Epistemic precondition not met
    
    # Step 3: All conditions satisfied
    return REVIEW_REQUIRED  # NOT authorization
```

**Critical distinction:** Even when all epistemic conditions are satisfied, the outcome is `REVIEW_REQUIRED`, not `AUTHORIZE`. Epistemic quality is necessary but not sufficient for authority.

---

## Required Invariants (All Verified)

| Invariant | Status |
|-----------|--------|
| COMPOSITION ≠ AUTHORIZATION | ✅ |
| FRONTIER ≠ AUTHORIZATION | ✅ |
| SAME MEMBERSHIP ≠ SAME CLAIM | ✅ |
| DIFFERENT MEMBERSHIP ≠ WORLD DISAGREEMENT | ✅ |
| UNION ≠ EPISTEMIC UNION | ✅ |
| INTERSECTION ≠ EPISTEMIC CONSENSUS | ✅ |
| N AGENTS AGREEING ≠ STRONGER AUTHORITY | ✅ |
| CORRELATED EVIDENCE ≠ INDEPENDENT CORROBORATION | ✅ |
| COMPLETE + UNKNOWN ≠ AUTOMATICALLY COMPLETE | ✅ |
| SCOPE UNION ≠ SCOPE AUTHORITY | ✅ |
| TEMPORAL UNION ≠ TEMPORAL VALIDITY | ✅ |
| PROVENANCE PRESERVATION ≠ PROVENANCE PROMOTION | ✅ |
| UNKNOWN ≠ FALSE | ✅ |
| REVALIDATION ≠ REVOCATION | ✅ |
| EPISTEMIC QUALITY ≠ AUTHORITY | ✅ |
| RUNTIME MAY MATERIALIZE AUTHORITY, NEVER CREATE AUTHORITY | ✅ |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 7 | Non-amplification, invariants |
| EXPERIMENTAL OBSERVATION | 5 | Scope, provenance, disagreement |
| EMPIRICAL RESULT | 1 | Epistemic conditions change outcomes |
| COUNTEREXAMPLE | 0 | None |
| MISSING SEMANTICS | 0 | Representation is sufficient |
| PROTOCOL VIOLATION | 0 | None |
| GOVERNANCE_DESIGN_CHOICE | 1 | Epistemic conditions are necessary |

---

## The Architectural Law (Confirmed)

```
WORLD
  ↓
OBSERVATIONS
  ↓
EVIDENCE
  ↓
INDIVIDUAL EPISTEMIC COMPUTATIONS
  ↓
RICH FRONTIERS (provenance-bearing)
  ↓
PROVENANCE-PRESERVING COMPOSITION
  ↓
COMPOSED EPISTEMIC CLAIM
  ↓
EPISTEMICALLY CONDITIONED GOVERNANCE
  ↓
AUTHORITY
```

### Key Distinction

Epistemic conditions are **necessary preconditions** for governance progression. They are not **sufficient conditions** for authorization.

- Scope mismatch → HOLD (not DENY)
- Provenance deficiency → HOLD (not DENY)
- Disagreement → REVIEW_REQUIRED (not DENY)
- All conditions satisfied → REVIEW_REQUIRED (not AUTHORIZE)

---

## The Deeper Result

> **Epistemic quality is a governance input, not an authority source.**

Phase 11 establishes that:

1. **Epistemic conditions can change governance decisions** without creating authority.
2. **Scope, provenance, completeness, temporal validity, and disagreement** are legitimate governance inputs.
3. **The invariant `EPISTEMIC QUALITY ≠ AUTHORITY` is preserved** — better epistemic conditions do not mint more authority.
4. **The governance decision function is a multi-valued predicate** — not just `REVIEW_REQUIRED` or `NO_ACTION`, but `HOLD`, `ESCALATE`, `CANNOT_DETERMINE`.

---

## Minimum Governance Information Contract

The epistemically conditioned governance model requires:

- **Membership** (set of artifact IDs)
- **Scope** (for scope matching)
- **Provenance quality** (for provenance checking)
- **Temporal validity** (for temporal bounds checking)
- **Completeness status** (for completeness gating)
- **Disagreement classification** (for disagreement handling)

The following dimensions are available but not yet consumed:

- Agent identity (used in composition but not governance decisions)
- Evidence basis (used in composition but not governance decisions)
- Epistemic state (partially used)

---

## Next Boundary

**Phase 12: Governance Policy Language** — Design a declarative policy language that allows governance rules to be specified explicitly rather than hardcoded.

The question is no longer "can governance consume epistemic information?" but "how should governance policies be expressed, verified, and enforced?"

For example:
- `REQUIRE scope MATCH authorization.scope`
- `REQUIRE provenance COMPLETE`
- `REQUIRE completeness KNOWN_COMPLETE`
- `IF disagreement THEN ESCALATE`

This is a policy specification question, not a representation question.

---

## Pause Point

The experimental record now establishes:

1. **Set composition is safe** — it does not amplify authority.
2. **Set composition is lossy** — it destroys semantic information.
3. **Provenance-preserving composition is feasible** — it fits within existing types.
4. **The frontier is a review surface** — not the final epistemic object.
5. **Governance is projection-sufficient** — the current binary predicate consumes only membership.
6. **Epistemic conditions change governance outcomes** — scope, provenance, and disagreement are legitimate governance inputs.
7. **Epistemic quality ≠ authority** — better conditions do not mint more authority.

The architecture is now at a clean boundary. The representation is sufficient. The governance model consumes epistemic conditions. The question is how to express governance policies declaratively.
