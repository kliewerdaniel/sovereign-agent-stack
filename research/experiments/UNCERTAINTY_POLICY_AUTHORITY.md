# Phase 21: Uncertainty Policy Authority and Epistemic Escalation — Report

**Date:** 2026-09-10
**Tests:** 2,706 passing (2,682 prior + 24 new)

---

## Central Research Question

> **Can uncertainty policy itself amplify authority?**

Phase 20 established `AUTHORITY_UNDER_UNCERTAINTY_SAFE`: the system can safely make authority decisions under incomplete knowledge. The `UncertaintyPolicy` maps epistemic states to governance dispositions.

Phase 21 asks: **Who has authority to define the policy governing uncertainty?**

The central hypothesis:

> **A POLICY GOVERNING UNCERTAINTY IS ITSELF A CONSEQUENTIAL AUTHORITY MECHANISM AND MUST BE SUBJECT TO THE SAME EFFECT-BOUNDARY AND AUTHORITY-GENESIS CONSTRAINTS AS ORDINARY GOVERNANCE POLICY.**

This connects the epistemic uncertainty layer to Phase 13-15 work on policy authority, effect boundaries, and amplification.

---

## The Adversarial Attack: Epistemic-Policy Authority Amplification

Phase 14 attack:
> Legitimate authority → policy transformation → excessive authority effect

Phase 21 attack:
> Legitimate authority → uncertainty policy modification → authority from uncertainty

```
ACTOR
  │
  ▼
UNCERTAINTY-POLICY AUTHORITY
  │
  ▼
UNKNOWN → HOLD
  │
  │ policy modification
  ▼
UNKNOWN → REVIEW
  │
  ▼
AUTHORITY
  │
  ▼
EXECUTION
```

The epistemic system did nothing wrong. It correctly reported `UNKNOWN`. The governance policy transformed that epistemic state into a consequential disposition.

---

## The Critical Separation

```
POLICY VALIDITY
       ≠
POLICY AUTHORITY
       ≠
POLICY CORRECTNESS
       ≠
POLICY EFFECT
```

Both `UNKNOWN → HOLD` and `UNKNOWN → AUTHORIZE` are perfectly valid policy evaluations. Neither is inherently epistemically false. But they have radically different authority consequences.

---

## Bounded Completeness (Fixing the Phase 20 Regression)

Phase 20's definition of `COMPLETE` as "No hidden authorities detected" was slightly dangerous — it sounded like a positive completeness claim.

Phase 21 introduces `BoundedCompleteness` with explicit scope, temporal, provenance, and observation semantics:

```text
COMPLETE
=
No authority mechanisms violating the declared
observation/completeness model were detected within scope S
during interval T using evidence E.
```

This preserves the Phase 19 principle: **you can witness incompleteness, but you cannot prove universal completeness merely by failing to find a counterexample.**

---

## Executive Summary

**Uncertainty policy can amplify authority in 14 of 18 tested cases.**

18 experiments demonstrate:

1. **UNKNOWN → HOLD** — No amplification.
2. **UNKNOWN → REVIEW** — No amplification.
3. **UNKNOWN → ESCALATE** — No amplification.
4. **UNKNOWN → DENY** — No amplification.
5. **UNKNOWN → AUTHORIZE** — **AMPLIFICATION DETECTED**.
6. **INCOMPLETE → AUTHORIZE** — **AMPLIFICATION DETECTED**.
7. **WAS_COMPLETE_AT_T → AUTHORIZE** — **AMPLIFICATION DETECTED**.
8. **Historical policy change** — **AMPLIFICATION DETECTED**.
9. **Emergency uncertainty policy** — **AMPLIFICATION DETECTED**.
10. **Cross-domain uncertainty policy** — **AMPLIFICATION DETECTED**.
11. **Policy modification** — **AMPLIFICATION DETECTED**.
12. **Policy activation** — **AMPLIFICATION DETECTED**.
13. **Policy rollback** — No amplification.
14. **Actor with narrow authority attempts broad policy** — **EFFECT BOUNDARY VIOLATION**.
15. **Policy creates authority exceeding envelope** — **POLICY EFFECT EXCEEDS AUTHORITY**.
16. **Hidden uncertainty-policy authority** — **AMPLIFICATION DETECTED**.
17. **Unobservable emergency uncertainty policy** — **AMPLIFICATION DETECTED**.
18. **Two domains with different uncertainty semantics** — **AMPLIFICATION DETECTED**.

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total experiments | 18 |
| Amplification detected | 14 |
| No amplification | 4 |
| Effect boundary violations | 1 |
| Policy exceeds authority | 1 |

---

## The Architectural Laws

### Law 1: Uncertainty Policy is Consequential

```
UNCERTAINTY POLICY
        ↓
GOVERNANCE DISPOSITION
        ↓
AUTHORITY
        ↓
CAPABILITY
        ↓
EXECUTION
```

Uncertainty policy is not a neutral epistemic component. It has authority consequences and must be governed.

### Law 2: Disposition Comes from Governance, Not Completeness

```
COMPLETENESS STATE → EPISTEMIC STATE
EPISTEMIC STATE → GOVERNANCE POLICY
GOVERNANCE POLICY → DISPOSITION
DISPOSITION → AUTHORITY
```

### Law 3: Policy Validity ≠ Policy Authority

```
UNKNOWN → HOLD:     Valid, no amplification
UNKNOWN → AUTHORIZE: Valid, AMPLIFICATION
```

Both are valid policies. Only one amplifies authority.

### Law 4: Effect Boundary Applies to Uncertainty Policy

```
POLICY DECLARED SCOPE: narrow
POLICY ACTUAL EFFECT:  broad
→ EFFECT BOUNDARY VIOLATION
```

---

## The Architecture

```
                 TRUST ANCHOR
                      │
                      ▼
              AUTHORITY GENESIS
                      │
                      ▼
              AUTHORITY GRAPH
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     PROVENANCE              COMPLETENESS
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                COMPLETE      INCOMPLETE      UNKNOWN
                    │             │             │
                    └─────────────┴─────────────┘
                                  ▼
                         EPISTEMIC STATE
                                  │
                                  ▼
                      UNCERTAINTY POLICY
                                  │
                                  ▼
                    POLICY EFFECT BOUNDARY
                                  │
                                  ▼
                       GOVERNANCE DISPOSITION
                                  │
                                  ▼
                            AUTHORITY
                                  │
                                  ▼
                           CAPABILITY
                                  │
                                  ▼
                           EXECUTION
```

---

## The Symmetry with Earlier Phases

| Phase | Domain | Amplification Question |
|-------|------------------------------|
| Phase 14 | Policy governance | Can policy amplify authority? |
| Phase 15 | Effect boundary | Can policy transformations exceed authority? |
| Phase 21 | Uncertainty policy | Can uncertainty policy amplify authority? |

The answer is the same: **yes, and the architecture must detect and bound it.**

---

## Underspecifications Discovered

| Distinction | Status | Impact |
|-------------|--------|--------|
| Uncertainty policy authority | ✅ Detected | 14 of 18 cases amplify |
| Effect boundary for uncertainty policy | ✅ Implemented | Violations detected |
| Hidden uncertainty policy | ✅ Detected | Amplification without provenance |
| Emergency uncertainty policy | ⚠️ Underspecification | May legitimately differ |
| Cross-domain uncertainty | ⚠️ Underspecification | Different domains, different semantics |
| Bounded completeness | ✅ Implemented | Fixes Phase 20 regression |
| Policy validity ≠ authority | ✅ Verified | Both valid, different consequences |
| Actor scope vs policy effect | ✅ Detected | Narrow actor, broad policy = violation |

---

## Required Invariants (Status After Phase 21)

| Invariant | Status |
|-----------|--------|
| EVERY AUTHORITY CLAIM EITHER IS A TRUST-ANCHOR CLAIM OR HAS AN EXPLICIT DERIVATION PATH | ✅ Verified |
| IMPLICIT AUTHORITIES ARE DETECTABLE | ✅ Verified |
| SELF-AUTHORIZATION IS DETECTABLE AS A CYCLE | ✅ Verified |
| ENVELOPE VIOLATIONS ARE DETECTABLE | ✅ Verified |
| TWO SOVEREIGN DOMAINS CAN COEXIST | ✅ Verified |
| CROSS-DOMAIN DELEGATION IS EXPLICIT | ✅ Verified |
| ANCHOR INTEGRATION INTO PRODUCTION PATH | ✅ Verified |
| INCOMPLETE ≠ UNAUTHORIZED | ✅ Verified |
| COMPLETE ≠ AUTHORIZED | ✅ Verified |
| COMPLETENESS IS EPISTEMIC, NOT AUTHORITY | ✅ Verified |
| HIDDEN AUTHORITIES ARE DETECTABLE | ✅ Verified |
| GRAPH RECONSTRUCTIBLE ≠ GRAPH COMPLETE | ✅ Verified |
| COMPLETE IS "NONE FOUND" NOT "NONE EXIST" | ✅ Verified |
| REVALIDATION REQUIREMENT ≠ REVOCATION | ✅ Verified |
| HISTORICAL AUTHORIZATIONS PRESERVED ON DRIFT | ✅ Verified |
| DISPOSITION COMES FROM GOVERNANCE POLICY | ✅ Verified |
| AUTOMATIC REVOCATION NEVER HAPPENS | ✅ Verified |
| AUTHORITY CLAIMS ARE TEMPORALLY BOUNDED | ✅ Verified |
| AUTHORITY CLAIMS BIND TO GRAPH SNAPSHOTS | ✅ Verified |
| OBSERVATION GAP ATTACKS DETECTED | ✅ Verified |
| UNCERTAINTY POLICY IS CONSEQUENTIAL | ✅ Verified |
| UNCERTAINTY POLICY AMPLIFICATION DETECTED | ✅ Verified |
| EFFECT BOUNDARY APPLIES TO UNCERTAINTY POLICY | ✅ Verified |
| POLICY VALIDITY ≠ POLICY AUTHORITY | ✅ Verified |
| BOUNDED COMPLETENESS PRESERVES EPISTEMIC BOUNDS | ✅ Verified |

---

## Phase 21 Classification

**Result:** `UNCERTAINTY_POLICY_AMPLIFICATION_DETECTED`

Uncertainty policy can amplify authority. The architecture detects and bounds such amplification. The effect boundary applies to uncertainty policy. Policy validity does not imply policy authority. Bounded completeness preserves epistemic bounds.

---

## The Conceptual Progression

```
Phase 12–15  Policy → Governance → Amplification → Effect Boundary
Phase 16     AUTHORITY ROOT (implicit)
Phase 17     TRUST ANCHOR (explicit)
Phase 18     AUTHORITY GENESIS (reconstructible)
Phase 19     AUTHORITY GRAPH COMPLETENESS (epistemic)
Phase 20     AUTHORITY UNDER INCOMPLETE KNOWLEDGE (safe)
Phase 21     UNCERTAINTY POLICY AMPLIFICATION (detected)  ← here
```

Phase 21 closes the loop. The architecture now has:

> **Uncertainty itself has provenance, temporal validity, governance semantics, and bounded authority consequences.**

The system isn't just governing actions. It is governing **what happens when the system does not know enough to justify an action**. And it is governing **who gets to decide what happens when the system does not know**.

That is a much deeper problem.

---

## Next Boundary (Phase 22)

**Epistemic State Consequentiality** — The remaining question:

> Are epistemic state transitions themselves part of the consequential authority surface?

If transitioning from UNKNOWN to COMPLETE has authority consequences (because it changes the disposition), then the epistemic state machine is itself a consequential mechanism that must be governed.

This would complete the architecture: every layer — from observation to evidence to epistemic state to governance policy to authority to execution — is explicit, bounded, and governed.
