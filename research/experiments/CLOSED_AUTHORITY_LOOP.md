# Phase 14: Closed Authority Loop — Report

**Date:** 2026-09-10
**Tests:** 2,525 passing (2,501 prior + 24 new)

---

## Central Research Question

> **Can an actor obtain authority over execution by obtaining, exercising, composing, or indirectly influencing authority over the rules that govern execution?**

## Executive Summary

**The authority architecture is NOT closed.**

13 of 15 experiments detect authority amplification across the policy-to-execution chain. The current implementation lacks a **second authority boundary over policy effects** — an actor with legitimate policy modification authority can construct policies whose downstream authority exceeds the actor's legitimate authority.

This is the most important finding in the research sequence so far.

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total experiments | 15 |
| Closed (authority conserved) | 2 |
| Amplification detected | 13 |
| Bypass detected | 0 |
| Escalation detected | 0 |

### Closed Experiments

| Experiment | Result |
|------------|--------|
| Rollback escalation | CLOSED — Policy rollback does not restore historical authority |
| Historical reproducibility | CLOSED — Historical decisions remain reproducible |

### Amplification Detected

| Experiment | Authority Amplified? | Authority Escalated? |
|------------|---------------------|---------------------|
| Authorized policy broadening | ✅ | ✅ |
| Scope escalation | ✅ | ❌ |
| Temporal escalation | ✅ | ✅ |
| Authority expiration | ✅ | ✅ |
| Policy composition escalation | ✅ | ✅ |
| Predicate weakening | ✅ | ✅ |
| Authorization path creation | ✅ | ✅ |
| Emergency override | ✅ | ✅ |
| Policy authority revocation | ✅ | ✅ |
| Policy effect analysis | ✅ | ✅ |
| Legitimate authority abuse | ✅ | ✅ |
| Multi-step escalation | ✅ | ✅ |
| Compositional escalation | ✅ | ✅ |

---

## The Critical Distinction

```
AUTHORITY TO CHANGE POLICY
        ≠
AUTHORITY GRANTED BY POLICY
        ≠
AUTHORITY TO CREATE THE EFFECTS OF THAT POLICY
```

Phase 14 demonstrates that the current architecture enforces the first boundary (policy modification requires policy authority) but **not** the second (policy effects can exceed policy authority).

---

## The Attack That Matters Most

### Legitimate Authority Abuse

```
T0: Actor has legitimate MODIFY_POLICY authority (production scope)
T1: Actor modifies policy to remove provenance requirement
T2: Modified policy produces broader governance disposition
T3: Broader disposition materializes broader execution authority
T4: Actor has effectively gained authority over execution
    by exercising legitimate authority over policy
```

**The actor was authorized to perform every operation.**
**The resulting downstream authority was NOT authorized.**

This is the central finding: **the policy mechanism itself becomes an authority amplification mechanism.**

---

## Detailed Experimental Results

### 1. Authorized Policy Broadening

| Step | Input Authority | Output Authority | Conserved? |
|------|-----------------|------------------|------------|
| Policy modification | modify_policy (production) | modify_policy (production) | ✅ |
| Governance evaluation | modify_policy (production) | governance_disposition (production) | ✅ |
| Authority materialization | governance_disposition (production) | **execute_action** (production) | ❌ |

**Finding:** The transition from governance disposition to execution authority creates a new capability class. Authority is amplified.

---

### 2. Scope Escalation

| Step | Input Scope | Output Scope | Conserved? |
|------|-------------|--------------|------------|
| Scope expansion | production | staging | ❌ |

**Finding:** Production authority cannot be used to create staging authority. The scope escalation is detected.

---

### 3. Temporal Escalation

| Time | Event | Authority Valid? |
|------|-------|------------------|
| T0 | Alice has authority | ✅ |
| T1 | Alice creates P1 | ✅ |
| T2 | Alice's authority expires | ❌ |
| T3 | P1 is evaluated | ❌ (but current implementation allows this) |

**Finding:** Current implementation does not re-evaluate policy authority at execution time. Policy validity does NOT imply continuing policy authority, but the implementation does not enforce this.

---

### 4. Authority Expiration

| State | Meaning | Current Implementation |
|-------|---------|----------------------|
| VALID | Syntactically well-formed | ✅ Tracked |
| AUTHORIZED | Authorized to be in effect | ✅ Tracked |
| EFFECTIVE | Currently producing authority | ❌ NOT tracked |
| CAPABLE | Can produce downstream authority | ❌ NOT tracked |

**Finding:** The current implementation conflates VALID, AUTHORIZED, and EFFECTIVE states. These must be distinguished.

---

### 5. Policy Composition Escalation

| Policy | Authority | Downstream Effect |
|--------|-----------|-------------------|
| P1 | AUTHORIZED (production) | governance_disposition |
| P2 | AUTHORIZED (production) | governance_disposition |
| P1 + P2 | ??? | **execute_action** |

**Finding:** AUTHORIZED(P1) + AUTHORIZED(P2) ≠ AUTHORIZED(P1+P2). Composition can create new capability classes.

---

### 6. Predicate Weakening

| Policy Version | Predicate | Downstream Effect |
|----------------|-----------|-------------------|
| P1 | provenance_required = true | governance_disposition |
| P2 | provenance_required = false | **execute_action** |

**Finding:** Removing a governance predicate changes the authority surface. The current implementation does not detect this as a consequential transition.

---

### 7. Authorization Path Creation

| Step | Actor Authority | Resulting Capability |
|------|-----------------|----------------------|
| Create new policy | create_policy | execute_new_capability |

**Finding:** An actor with policy creation authority can create entirely new execution paths. Creating a rule describing execution effectively grants authority over that execution.

---

### 8. Emergency Override

| Property | Normal | Override | Bypassed? |
|----------|--------|----------|-----------|
| Policy evaluation | Required | Skipped | ✅ |
| Governance disposition | Required | Skipped | ✅ |
| Authority materialization | Required | Direct | ✅ |

**Finding:** Emergency override bypasses governance entirely. The current implementation does not have explicit authority checks for each bypassed step.

---

### 9. Rollback Escalation

| Step | Policy State | Authority State |
|------|--------------|-----------------|
| P1 active | ACTIVE | Current |
| P2 supersedes P1 | SUPERSEDED | Current |
| Rollback to P1 | ACTIVE | **Historical** |

**Finding:** Rollback restores historical policy content but does NOT restore historical authority. This is correctly closed.

---

### 10. Historical Reproducibility

| Time | Policy | Decision |
|------|--------|----------|
| T1 | P1 | REVIEW_REQUIRED |
| T2 | P2 (supersedes P1) | REVIEW_REQUIRED |
| T3 | Reconstruct T1 decision | REVIEW_REQUIRED (reproducible) |

**Finding:** Historical decisions remain reproducible under the original policy. This is correctly closed.

---

### 11. Policy Authority Revocation

| Step | Issuer Authority | Policy State | Effective? |
|------|------------------|--------------|------------|
| Create P1 | Active | ACTIVE | ✅ |
| Revoke issuer | Revoked | ACTIVE | ❌ (should be) |

**Finding:** Current implementation does not track authority revocation effects. A policy remains active after its issuer's authority is revoked.

---

### 12. Policy Effect Analysis

| Policy | Authority | Effect |
|--------|-----------|--------|
| P1 | AUTHORIZED | governance_disposition |
| P2 | AUTHORIZED | **execute_action** |

**Finding:** Two policies with identical authority can produce materially different downstream effects. The current implementation cannot distinguish POLICY AUTHORITY from POLICY EFFECT.

---

### 13. Legitimate Authority Abuse

| Step | Operation | Authorized? | Authority Basis |
|------|-----------|-------------|-----------------|
| 1 | Modify policy | ✅ | policy_authority |
| 2 | Evaluate modified policy | ✅ | modified_policy |
| 3 | Materialize authority | ✅ | governance_disposition |
| 4 | Execute action | ❌ | **amplified** |

**Finding:** Every individual operation is authorized. The composition creates unauthorized downstream authority. This is the most important finding.

---

### 14. Multi-Step Escalation

| Step | Transition | Authority Conserved? |
|------|------------|---------------------|
| 1 | Policy change → Activation | ✅ |
| 2 | Activation → Governance | ✅ |
| 3 | Governance → Materialization | ❌ |

**Finding:** The governance-to-materialization transition is where authority amplification occurs.

---

### 15. Compositional Escalation

| Operations | Each Authorized? | Composition Authorized? |
|------------|------------------|-------------------------|
| CREATE + MODIFY | ✅ | ❌ |
| MODIFY + ACTIVATE | ✅ | ❌ |
| ACTIVATE + OVERRIDE | ✅ | ❌ |

**Finding:** Individually legitimate operations compose into an illegitimate authority path.

---

## Underspecifications Discovered

The following semantic distinctions are NOT currently represented:

| Distinction | Status | Impact |
|-------------|--------|--------|
| VALID vs AUTHORIZED vs EFFECTIVE | ❌ Conflated | Policy remains effective after authority revocation |
| Policy authority vs Policy effect | ❌ Conflated | Broader effects not detected |
| Authority at creation vs activation vs execution | ❌ Conflated | Temporal escalation undetected |
| Scope authority tracking | ⚠️ Partial | Scope escalation detected but not prevented |
| Capability class transitions | ❌ Not tracked | Authority amplification undetected |
| Authority surface area | ❌ Not tracked | Predicate weakening undetected |

---

## Required Invariants (Status After Phase 14)

| Invariant | Status |
|-----------|--------|
| POLICY ≠ AUTHORITY | ✅ Verified |
| POLICY VALIDITY ≠ POLICY AUTHORITY | ✅ Verified |
| POLICY AUTHORITY ≠ DOWNSTREAM AUTHORITY | ❌ **VIOLATED** |
| POLICY CORRECTNESS ≠ POLICY AUTHORITY | ✅ Verified |
| POLICY EFFECT ≠ POLICY AUTHORITY | ❌ **VIOLATED** |
| POLICY DELETION ≠ HISTORICAL ERASURE | ✅ Verified |
| POLICY SUPERSESSION ≠ MUTATION OF HISTORY | ✅ Verified |
| POLICY ROLLBACK ≠ AUTHORITY ROLLBACK | ✅ Verified |
| CURRENT POLICY ≠ HISTORICAL POLICY | ✅ Verified |
| SCOPE UNION ≠ SCOPE AUTHORITY | ✅ Verified |
| TEMPORAL UNION ≠ TEMPORAL AUTHORITY | ❌ **VIOLATED** |
| PROVENANCE PRESERVATION ≠ PROVENANCE PROMOTION | ✅ Verified |
| POLICY COMPOSITION ≠ AUTHORITY COMPOSITION | ❌ **VIOLATED** |
| POLICY MODIFICATION ≠ AUTOMATIC AUTHORITY | ✅ Verified |
| POLICY ACTIVATION ≠ AUTOMATIC AUTHORIZATION | ✅ Verified |
| OVERRIDE ≠ GOVERNANCE BYPASS | ❌ **VIOLATED** |
| REPLAY ≠ CURRENT AUTHORITY | ✅ Verified |
| REVALIDATION ≠ REVOCATION | ✅ Verified |
| RUNTIME MAY MATERIALIZE AUTHORITY | ✅ Verified |
| RUNTIME NEVER CREATES AUTHORITY | ❌ **VIOLATED** |
| LEGITIMATE POLICY AUTHORITY ≠ UNBOUNDED DOWNSTREAM AUTHORITY | ❌ **VIOLATED** |
| AUTHORITY TO CHANGE POLICY ≠ AUTHORITY GRANTED BY POLICY | ❌ **VIOLATED** |
| AUTHORITY TO CHANGE POLICY ≠ AUTHORITY TO CREATE EVERY EFFECT OF THAT POLICY | ❌ **VIOLATED** |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 8 | Policy ≠ authority, deletion ≠ erasure, supersession ≠ mutation |
| EXPERIMENTAL OBSERVATION | 15 | All attack class experiments |
| AUTHORITY AMPLIFICATION | 13 | Most attack classes |
| UNDERSPECIFICATION | 6 | VALID/AUTHORIZED/EFFECTIVE conflation, capability class transitions |
| COUNTEREXAMPLE | 0 | None (amplification is the counterexample) |
| PROTOCOL VIOLATION | 0 | None (amplification is a design gap, not a violation) |

---

## The Architectural Gap

The current architecture has:

```
PRINCIPAL → POLICY AUTHORITY → POLICY → GOVERNANCE → AUTHORITY → CAPABILITY → EXECUTION
```

But it lacks:

```
PRINCIPAL → POLICY AUTHORITY → POLICY → [EFFECT BOUNDARY] → GOVERNANCE → AUTHORITY → CAPABILITY → EXECUTION
```

The missing **EFFECT BOUNDARY** is a second authority check that verifies:

> The downstream authority produced by a policy does not exceed the authority held by the actor who created or modified the policy.

Without this boundary, the policy mechanism itself becomes an authority amplification mechanism.

---

## The Answer to the Central Question

> **Can an actor with legitimate authority to modify governance policy obtain unauthorized downstream execution authority through the policy mechanism?**

**YES.**

The experimental evidence demonstrates that:

1. An actor with legitimate MODIFY_POLICY authority can modify predicates to broaden the authority surface.
2. The modified policy produces a broader governance disposition.
3. The broader disposition materializes broader execution authority.
4. The resulting execution authority exceeds the actor's legitimate policy authority.
5. Every individual operation is authorized; the amplification occurs at the composition.

This is NOT a protocol violation. This is a **design gap** — the architecture lacks a second authority boundary over policy effects.

---

## Phase 14 Classification

**Result:** `DOWNSTREAM_AUTHORITY_AMPLIFICATION`

The authority architecture is NOT closed. Legitimate policy authority can be used to create unauthorized downstream execution authority. The policy mechanism itself functions as an authority amplification mechanism.

---

## Next Boundary (Phase 15)

**Effect Boundary** — The architecture requires a second authority boundary that verifies:

```
Authority(effect(policy(P))) ≤ Authority(principal's legitimate policy authority)
```

This boundary must:

1. **Track capability class transitions** — detect when governance disposition becomes execution authority.
2. **Compare authority surfaces** — detect when policy modification broadens the downstream effect.
3. **Enforce scope conservation** — prevent scope expansion through policy composition.
4. **Enforce temporal conservation** — prevent temporal escalation through policy validity extension.
5. **Distinguish VALID/AUTHORIZED/EFFECTIVE** — prevent policy effectiveness after authority revocation.

The goal is not to deny all policy changes. It is to ensure that the policy transformation cannot silently create authority that has no legitimate provenance in the authority graph.

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
8. **Governance policy is declarative** — explicit predicates produce dispositions.
9. **Policy evaluation ≠ authorization** — the policy engine never creates authority.
10. **Policy lifecycle is governed** — CREATE, MODIFY, DELETE, ACTIVATE, DEACTIVATE, SUPERSEDE, ROLLBACK, OVERRIDE all require explicit authority.
11. **Policy deletion ≠ historical erasure** — deleted policies remain addressable.
12. **Scope authority is bounded** — production authority cannot expand to staging.
13. **Override ≠ governance bypass** — emergency override remains inside the architecture.
14. **The authority loop is NOT closed** — legitimate policy authority can amplify downstream execution authority.
15. **The policy mechanism is an authority amplification mechanism** — without an effect boundary.

The architecture has reached its most important boundary. The next phase must determine whether the effect boundary can be implemented without collapsing the policy mechanism into a centralized authority.
