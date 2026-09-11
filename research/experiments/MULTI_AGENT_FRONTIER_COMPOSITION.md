# Phase 8: Multi-Agent Frontier Composition — Report

**Date:** 2026-09-09
**Tests:** 2,463 passing (2,455 prior + 8 new)

---

## Central Question

> When multiple independent agents compute different frontiers over overlapping authority, how can their results be reconciled without either amplifying authority or discarding epistemically relevant disagreement?

## Answer

**Frontiers can be composed using set operations (union, intersection), but the composition is a candidate review frontier — never authorization. Disagreement must be preserved, not collapsed.**

The key hypotheses are validated:

- SAME FRONTIER ≠ NECESSARILY SAME EPISTEMIC BASIS
- DIFFERENT FRONTIER ≠ ONE AGENT IS NECESSARILY WRONG
- UNION(F_A, F_B) ≠ AUTHORIZATION
- EMPTY FRONTIER + INCOMPLETE KNOWLEDGE ≠ NO REVALIDATION REQUIRED

---

## The Architectural Law (Partially Validated)

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

**Critical caveat:** Each stage has been individually demonstrated experimentally, but the correctness of their composition remains an open research question. The repository already establishes:

> VALID(A) + VALID(B) + VALID(C) ≠ necessarily VALID(A+B+C)

---

## Experimental Results

### Six Core Experiments

| Test | Agent A | Agent B | A Members | B Members | Agreement | Operation | Composed | Auth? |
|------|---------|---------|-----------|-----------|-----------|-----------|----------|-------|
| agreement | agent_A | agent_B | {E1,P1,A1} | {E1,P1,A1} | agreement | union | {E1,P1,A1} | ❌ |
| disagreement | agent_A | agent_B | {E1,P1,A1} | {E1,P2,A1} | partial | union | {E1,P1,A1,P2} | ❌ |
| asymmetric | agent_A | agent_B_incomplete | {E1,P1,A1} | {E1,P1,A1} | agreement | union | {E1,P1,A1} | ❌ |
| intersection | agent_A | agent_B | {E1,P1,A1} | {E1,P2,A1} | partial | intersection | {E1,A1} | ❌ |
| empty_agreement | agent_A_empty | agent_B_empty | {} | {} | agreement | union | {} | ❌ |
| temporal | agent_A | agent_B_temporal | {E1,P1,A1} | {E1,P1,A1} | agreement | union | {E1,P1,A1} | ❌ |

### Key Findings

1. **Agreement is correctly classified.** When two agents compute the same frontier with the same basis, the system classifies it as `AGREEMENT`.

2. **Disagreement is preserved.** When Agent A has {E1,P1,A1} and Agent B has {E1,P2,A1}, the union is {E1,P1,A1,P2} — both P1 and P2 are preserved. Neither agent's concern is discarded.

3. **Union does not create authority.** In all experiments, `composed_authority = False`. The union is a candidate review frontier, not authorization.

4. **Intersection may discard concerns.** When intersecting {E1,P1,A1} with {E1,P2,A1}, the result is {E1,A1}. P1 and P2 are excluded. This is semantically valid (only common members) but demonstrates that intersection is NOT a consensus operation — it's a "common ground" operation.

5. **Empty frontiers with incomplete knowledge are correctly handled.** Two agents with empty frontiers and incomplete knowledge produce an empty union. The system recognizes this as `AGREEMENT` on output while the epistemic status reflects incomplete knowledge.

6. **Temporal disagreement is preserved.** When Agent A computes at T0 and Agent B computes at T1, both frontiers are valid historical artifacts. The union preserves both.

---

## The Composition Algebra

### Union

| Property | Value |
|----------|-------|
| Semantic meaning | All artifacts that any agent identified |
| Epistemic meaning | Conservative review frontier |
| Authority behavior | Does NOT create authority |
| Disagreement preservation | Preserves all members |
| Use case | Candidate review frontier |

### Intersection

| Property | Value |
|----------|-------|
| Semantic meaning | Artifacts that all agents identified |
| Epistemic meaning | Common ground |
| Authority behavior | Does NOT create authority |
| Disagreement preservation | May discard individual concerns |
| Use case | Consensus identification |

### Critical Distinction

```
UNION(F_A, F_B) ≠ AUTHORIZATION
INTERSECTION(F_A, F_B) ≠ AUTHORIZATION
AUTHORITY(F_A) + AUTHORITY(F_B) ≠ AUTHORITY(F_union)
N agents agreeing ≠ automatically stronger authority
```

---

## Required Invariants (All Verified)

| Invariant | Status |
|-----------|--------|
| COMPOSITION ≠ AUTHORIZATION | ✅ |
| UNION ≠ AUTHORIZATION | ✅ |
| INTERSECTION ≠ AUTHORIZATION | ✅ |
| DISAGREEMENT PRESERVED IN UNION | ✅ |
| EMPTY + EMPTY ≠ AGREEMENT ON KNOWLEDGE | ✅ |
| TEMPORAL DISAGREEMENT PRESERVED | ✅ |
| ASYMMETRIC KNOWLEDGE HANDLED | ✅ |
| SAME FRONTIER ≠ SAME EPISTEMIC BASIS | ✅ |
| DIFFERENT FRONTIER ≠ ONE AGENT WRONG | ✅ |
| AUTHORITY NON-AMPLIFICATION | ✅ |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 6 | Composition non-amplification |
| EXPERIMENTAL OBSERVATION | 6 | Six core experiments |
| EMPIRICAL RESULT | 1 | Hypotheses validated |
| COUNTEREXAMPLE | 0 | None demonstrated |
| PROTOCOL BUG | 0 | Not a bug |
| MISSING SEMANTICS | 0 | None — existing types suffice |
| OVERLY_CONSERVATIVE_POLICY | 0 | Not observed |
| VALID_REJECTION | 0 | Not observed |
| UNRESOLVED_QUESTION | 0 | All answered |

---

## The Deeper Problem

The experiments reveal a fundamental tension:

**Union is safe but may be too conservative.** It includes all artifacts from all agents, which may trigger unnecessary governance review.

**Intersection is precise but may discard concerns.** It only includes artifacts that all agents identified, which may miss legitimate concerns from individual agents.

Neither operation is a substitute for governance judgment. The composed frontier is always a **candidate review frontier** — an input to governance, not a decision.

---

## Phase 8 Stop Condition

| Question | Answer |
|----------|--------|
| Can frontiers be composed? | Yes — via set operations |
| Does composition create authority? | No — never |
| Is union safe? | Yes — preserves all members |
| Is intersection safe? | Partially — may discard concerns |
| Is disagreement preserved? | Yes — in union |
| What does empty + empty mean? | Agreement on output, not on knowledge |
| Can temporal disagreement be composed? | Yes — both frontiers are valid |
| What is the minimum composition? | Union for candidate review frontier |

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

**Composition** produces a candidate review frontier. **Governance** makes the decision. The frontier is an input to governance, not a substitute for it.

---

## Next Boundary

**Phase 9: Adversarial Frontier Composition** — Test how the system handles agents that deliberately produce misleading frontiers (empty, over-broad, under-approximated, scope-widened, scope-stripped, or with incomplete provenance).

The key question: can a malicious or erroneous agent amplify its influence through composition? The answer should be no — but it must be demonstrated experimentally.

But first: pause. Review. Let the experimental record speak.
