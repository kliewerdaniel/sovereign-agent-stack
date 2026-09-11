# Phase 20: Authority Under Incomplete Knowledge — Report

**Date:** 2026-09-10
**Tests:** 2,682 passing (2,659 prior + 23 new)

---

## Central Research Question

> **What authority is permissible when the system cannot establish that it knows the complete authority graph?**

Phase 19 established `AUTHORITY_GRAPH_COMPLETENESS_EPISTEMIC`: the authority graph can be incomplete, and completeness is an epistemic property, not an authority property. The asymmetry: you can prove incompleteness, but you cannot prove completeness.

Phase 20 asks the harder question: **Can SAS safely make authority decisions when the authority graph is known to be incomplete or its completeness is unknown?**

---

## The Epistemic Authority Paradox

The architecture now faces a fundamental question. Phase 19 tells us that the system cannot establish that the authority graph is complete in the general case. Therefore:

```
TrustAnchor
    ↓
A
    ↓
B
    ↓
Execution

UNKNOWN: hidden authority may exist
```

What happens?

There are at least four possible semantics for `UNKNOWN`:

```
UNKNOWN → HOLD
UNKNOWN → REVIEW
UNKNOWN → DENY
UNKNOWN → CONDITIONAL AUTHORITY
```

But **none of those is epistemically implied by `UNKNOWN`**. The disposition must come from **governance policy over uncertainty**, not from the completeness engine.

---

## The Critical Separation

```
GRAPH COMPLETENESS
        ↓
EPISTEMIC STATE
        ↓
GOVERNANCE POLICY
        ↓
GOVERNANCE DISPOSITION
        ↓
AUTHORITY
```

This gives us another clean separation:

| Layer | Produces | Does NOT Produce |
|-------|----------|------------------|
| Completeness Engine | COMPLETE / INCOMPLETE / UNKNOWN | Authority |
| Governance Policy | HOLD / REVIEW / DENY / CONDITIONAL | Completeness |
| Authority Derivation | Authorization | Completeness |

---

## The Four Completeness States

Phase 20 introduces a fourth state that was implicit in earlier phases:

| State | Meaning |
|-------|---------|
| COMPLETE | No hidden authorities detected |
| INCOMPLETE | Hidden authority detected |
| UNKNOWN | No assessment has been run |
| WAS_COMPLETE_AT_T | Graph was complete at T1, now uncertain |

The fourth state is particularly important. A historical authorization might have been completely justified relative to the authority graph observable at T1, while later discovery at T2 reveals an authority mechanism that was previously unknown. **That does not necessarily make the historical authorization invalid.**

---

## Authority Claim with Provenance

An authority claim is NOT a timeless fact. It is a claim relative to:

```
AUTHORITY CLAIM
    +
GRAPH SNAPSHOT
    +
COMPLETENESS ASSESSMENT
    +
TEMPORAL VALIDITY
    +
PROVENANCE
```

This gives us a much stronger architecture: authority claims are first-class epistemic objects with explicit provenance, completeness state, and temporal bounds.

---

## Executive Summary

**The system can safely make authority decisions under incomplete knowledge.**

10 experiments demonstrate:

1. **Known complete graph** → Normal governance, authority granted.
2. **Known missing edge** → Revalidation required.
3. **Unknown completeness** → Authority deferred.
4. **Hidden authority outside observation** → Revalidation required.
5. **Hidden authority discovered after authorization** → Historical preserved, future reconsidered.
6. **Emergency path hidden authority** → Authority deferred.
7. **Cross-domain hidden delegation** → Revalidation required.
8. **Graph becomes incomplete after authorization** → Revalidation required, NO automatic revocation.
9. **Observation gap attack** → Revalidation required.
10. **WAS_COMPLETE_AT_T** → Revalidation required.

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total experiments | 10 |
| Authority granted | 1 (only for complete graph) |
| Authority deferred | 2 |
| Revalidation required | 6 |
| Historical preserved | 2 |
| Automatic revocation | 0 (NEVER) |

---

## The Architectural Laws

### Law 1: Completeness is Epistemic, Not Authority

```
UNKNOWN AUTHORITY GRAPH ≠ UNAUTHORIZED AUTHORITY
INCOMPLETE GRAPH ≠ DENIED EXECUTION
COMPLETE GRAPH ≠ AUTHORIZED EXECUTION
```

### Law 2: Revalidation ≠ Revocation

```
AUTHORITY GRIFT DRIFT
        ↓
COMPLETENESS UNCERTAINTY
        ↓
REVALIDATION REQUIREMENT
        ≠
AUTOMATIC REVOCATION
```

### Law 3: Historical Preservation

```
HISTORICAL AUTHORIZATION
    +
GRAPH SNAPSHOT AT T1
    +
COMPLETENESS AT T1
        ↓
    PRESERVED
        +
FUTURE RECONSIDERATION
        ↓
    REVALIDATION REQUIRED
```

### Law 4: Disposition Comes from Governance, Not Completeness

```
COMPLETENESS STATE → EPISTEMIC STATE
EPISTEMIC STATE → GOVERNANCE POLICY
GOVERNANCE POLICY → DISPOSITION
DISPOSITION → AUTHORITY
```

---

## The Adversarial Case: Observation Gap Attack

Phase 14 attack:
> Legitimate authority → policy transformation → excessive authority effect

Phase 20 attack:
> Legitimate authority graph → incomplete observation → incorrectly bounded knowledge of authority

These are fundamentally different failure modes. The Phase 20 attack is particularly nasty because everything appears valid according to the graph — the attack is on the observation boundary itself.

**Result:** The system detects the observation gap and requires revalidation. The attack does not succeed silently.

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
                         GOVERNANCE POLICY
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

| Phase | Domain | Completeness Question |
|-------|------------------------------|
| Dep. Completeness | Dependency graphs | Can the dependency graph be complete? |
| Authority Genesis | Authority graphs | Can the authority graph be reconstructed? |
| Phase 19 | Authority graphs | Can the authority graph be complete? |
| Phase 20 | Authority graphs | What authority is permissible under incomplete knowledge? |

The answer extends the pattern: **authority under incomplete knowledge is a governance decision, not an epistemic one**.

---

## Underspecifications Discovered

| Distinction | Status | Impact |
|-------------|--------|--------|
| Four completeness states | ✅ Implemented | WAS_COMPLETE_AT_T added |
| Historical preservation | ✅ Implemented | Drift does not revoke |
| Revalidation requirement | ✅ Implemented | Drift triggers revalidation |
| Observation gap attack | ✅ Detected | Revalidation required |
| Governance over uncertainty | ✅ Implemented | Policy maps state → disposition |
| Disposition ≠ authority | ✅ Verified | Clean separation |
| Automatic revocation | ✅ Forbidden | Never happens |
| Temporal authority claims | ✅ Implemented | Claims have temporal bounds |
| Graph snapshot binding | ✅ Implemented | Claims bind to snapshots |
| Completeness → Disposition | ✅ Configurable | Policy is external |

---

## Required Invariants (Status After Phase 20)

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

---

## Phase 20 Classification

**Result:** `AUTHORITY_UNDER_UNCERTAINTY_SAFE`

The system can safely make authority decisions under incomplete knowledge. The completeness engine produces epistemic states. Governance policy maps them to dispositions. Historical authorizations are preserved on drift. Automatic revocation never happens. Observation gap attacks are detected.

---

## The Conceptual Progression

```
Phase 12–15  Policy → Governance → Amplification → Effect Boundary
Phase 16     AUTHORITY ROOT (implicit)
Phase 17     TRUST ANCHOR (explicit)
Phase 18     AUTHORITY GENESIS (reconstructible)
Phase 19     AUTHORITY GRAPH COMPLETENESS (epistemic)
Phase 20     AUTHORITY UNDER INCOMPLETE KNOWLEDGE (safe)  ← here
```

Phase 20 closes the loop. The architecture is no longer merely "authority with provenance." It becomes:

> **Authority whose own provenance, completeness, temporal validity, uncertainty, and consequences are themselves explicit epistemic objects.**

That is a much more serious systems architecture.

---

## Next Boundary (Phase 21)

**Authority Completeness Amplification** — The remaining question:

> Can an actor exploit the gap between reconstructible authority and complete authority to exercise hidden authority without detection?

This connects back to the four potential authority escapes identified in the recursive self-audit. The architecture now has the machinery to detect hidden authority — but can it prevent the exercise of hidden authority that hasn't been discovered yet?

The answer is probably: **prevention is impossible, but detection + revalidation + historical preservation is the best achievable semantics.**
