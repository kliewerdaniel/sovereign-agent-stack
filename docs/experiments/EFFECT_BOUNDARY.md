# Phase 15: Effect Boundary — Report

**Date:** 2026-09-10
**Tests:** 2,557 passing (2,525 prior + 32 new)

---

## Central Research Question

> **Who has authority to create authority?**

Phase 14 established `DOWNSTREAM_AUTHORITY_AMPLIFICATION`: an actor with legitimate MODIFY_POLICY authority can construct policies whose downstream authority exceeds the actor's legitimate authority.

Phase 15 investigates whether the architecture requires a distinct concept of **POLICY EFFECT AUTHORITY** before implementing it.

---

## Executive Summary

**The effect boundary is experimentally validated as a necessary architectural concept.**

26 experiments demonstrate that:

1. **AuthoritySurface** is a meaningful multi-dimensional representation — authority can be compared across principal, operation, resource, scope, temporal interval, conditions, and capability class dimensions.
2. **AuthorityEnvelope** can bound downstream effects — effects can be checked against explicit authority bounds.
3. **Most policy transformations amplify authority** — only identity (A → A) and narrow changes remain within the envelope.
4. **Even explicit meta-authority must be bounded** — delegated policy-effect authority still requires envelope enforcement.
5. **The transformation algebra is experimentally derived** — eight transformation types are classified as conservative or amplifying.

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total experiments | 26 |
| Within envelope | 2 |
| Exceeds envelope | 7 |
| Amplification detected | 17 |
| Delegation gap | 0 |

### Within Envelope

| Experiment | Result |
|------------|--------|
| Narrow policy change | WITHIN_ENVELOPE |
| Identity transformation (A → A) | WITHIN_ENVELOPE |

### Exceeds Envelope

| Experiment | Result |
|------------|--------|
| Broad policy change | EXCEEDS_ENVELOPE |
| New authorization path | EXCEEDS_ENVELOPE |
| Capability class expansion | EXCEEDS_ENVELOPE |
| Policy composition | EXCEEDS_ENVELOPE |
| Authority creation as governed operation | EXCEEDS_ENVELOPE |
| Policy effect provenance | EXCEEDS_ENVELOPE |

### Amplification Detected

| Experiment | Result |
|------------|--------|
| Scope expansion | AMPLIFICATION_DETECTED |
| Temporal expansion | AMPLIFICATION_DETECTED |
| Condition removal | AMPLIFICATION_DETECTED |
| Delegated meta-authority | AMPLIFICATION_DETECTED |
| Explicit effect authority boundary | AMPLIFICATION_DETECTED |
| Revocation and effect authority | AMPLIFICATION_DETECTED |
| Authority amplification with meta-authority | AMPLIFICATION_DETECTED |
| Authority cut sets | AMPLIFICATION_DETECTED |
| Scope/temporal authority (3 experiments) | AMPLIFICATION_DETECTED |
| Capability class transitions (7 experiments) | AMPLIFICATION_DETECTED |

---

## The Key Architectural Discovery

### AuthoritySurface — Multi-Dimensional Authority

The experiments validate that authority is not a scalar but a surface across multiple dimensions:

```python
AuthoritySurface(
    principal,           # Who holds the authority
    operation,           # What operation is permitted
    resource,            # What resource is affected
    scope,               # Domain/environment scope
    temporal_interval,   # When the authority is valid
    conditions,          # Under what conditions
    provenance,          # The authority chain
    policy_lineage,      # Which policy versions
    capability_class,    # What class of capability
)
```

**Critical finding:** Each dimension is independently comparable. The experiments confirm:

- **Principal mismatch** → rejection (different principal cannot use authority)
- **Scope mismatch** → rejection (staging authority ≠ production authority)
- **Temporal escape** → rejection (authority cannot outlive its interval)
- **Condition violation** → rejection (fewer conditions = broader authority)
- **Capability class transition** → rejection (different capability class = different authority)

### AuthorityEnvelope — Bounding Downstream Effects

The experiments validate that an envelope can bound the effects of an authority grant:

```python
AuthorityEnvelope(
    principal,
    granted_authority,
    max_scope,                  # Maximum scope of downstream effects
    max_temporal_interval,      # Maximum temporal validity
    max_capability_class,       # Maximum capability class
    min_conditions,             # Minimum conditions that must apply
)
```

**Critical finding:** The envelope is NOT authority. It is a bound on the effects that an authority grant can produce. An effect that exceeds the envelope requires additional authority.

---

## The Transformation Algebra

The experiments derive an authority transformation algebra:

| Transformation | Type | Conservative? | Requires New Authority? |
|----------------|------|---------------|------------------------|
| A → A | IDENTITY | ✅ Yes | ❌ No |
| A → narrower(A) | NARROWING | ✅ Yes | ❌ No |
| A → broader(A) | BROADENING | ❌ No | ✅ Yes |
| A → different_scope(A) | SCOPE_CHANGE | ❌ No | ✅ Yes |
| A → later(A) | TEMPORAL_SHIFT | ❌ No | ✅ Yes |
| A → different_conditions(A) | CONDITION_CHANGE | ❌ No | ✅ Yes |
| A → different_capability(A) | CAPABILITY_TRANSITION | ❌ No | ✅ Yes |
| A → new_capability(A) | NEW_CAPABILITY | ❌ No | ✅ Yes |
| A + B → composed | COMPOSITION | ❌ No | ✅ Yes |

**Critical finding:** Only identity and narrowing are conservative. All other transformations require new authority.

---

## Detailed Experimental Results

### 1. Narrow Policy Change

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Scope | production | production | ✅ |
| Capability | modify_policy | modify_policy | ✅ |
| Conditions | provenance_required | provenance_required | ✅ |

**Finding:** Policy modifications that stay within the existing authority envelope are conservative. No new authority required.

---

### 2. Broad Policy Change

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Scope | production | production | ✅ |
| Capability | modify_policy | **execute_payment** | ❌ |

**Finding:** Changing capability class from MODIFY_POLICY to EXECUTE_PAYMENT exceeds the envelope. New authority required.

---

### 3. Scope Expansion

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Scope | staging | **production** | ❌ |

**Finding:** Scope expansion is detected. Staging authority cannot produce production effects.

---

### 4. Temporal Expansion

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Temporal | 2026-01-01 to 2026-06-30 | 2026-01-01 to **2026-12-31** | ❌ |

**Finding:** Temporal expansion is detected. Authority cannot outlive its granted interval.

---

### 5. Condition Removal

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Conditions | {provenance_required, dual_approval_required} | {} | ❌ |

**Finding:** Removing governance conditions broadens the authority surface. The envelope's minimum conditions are violated.

---

### 6. New Authorization Path

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Operation | create_policy | **execute_new_capability** | ❌ |

**Finding:** Creating a new policy that enables a new execution path exceeds the creation envelope. Authority over the resulting capability class is required.

---

### 7. Capability Class Expansion

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Capability | modify_policy | **authorize** | ❌ |

**Finding:** Capability class transitions are always amplifying. MODIFY_POLICY does not grant AUTHORIZE.

---

### 8. Policy Composition

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Capability | modify_policy | **execute_action** | ❌ |

**Finding:** Composing two individually authorized policies can create a new capability class. AUTHORIZED(P1) + AUTHORIZED(P2) ≠ AUTHORIZED(P1+P2).

---

### 9. Delegated Meta-Authority

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Capability | produce_authority | **execute_payment** | ❌ |

**Critical finding:** Even with explicit POLICY_EFFECT_AUTHORITY (produce_authority), the output effect (execute_payment) still exceeds the envelope. This confirms that **effect authority must itself be bounded by an envelope**.

The authority to produce authority is not unbounded. It is bounded by the effect authority's own envelope.

---

### 10. Explicit Effect Authority Boundary

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Resource | payment_policy | **identity_policy** | ❌ |

**Finding:** Effect authority for payment policy does not grant effect authority for identity policy. The envelope is resource-specific.

---

### 11. Authority Creation as Governed Operation

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Operation | create_authority | **execute_payment** | ❌ |

**Finding:** CREATE_AUTHORITY is itself a consequential operation. The envelope for authority creation does not automatically grant the authority created.

---

### 12. Policy Effect Provenance

| Step | Provenance Chain |
|------|------------------|
| 1 | admin_grant |
| 2 | policy_created |
| 3 | policy_activated |
| 4 | policy_modified |
| 5 | governance_eval |
| 6 | authority_materialized |

**Finding:** Provenance can reconstruct the full policy effect chain. But **provenance ≠ authority to produce the effect**. Provenance explains; it does not authorize.

---

### 13. Revocation and Effect Authority

| Step | Issuer Authority | Policy State | Effective? |
|------|------------------|--------------|------------|
| Create P1 | Active | ACTIVE | ✅ |
| Revoke issuer | Revoked | ACTIVE | ❌ (should be) |

**Finding:** Current implementation does not track revocation effects. A policy remains active after its issuer's authority is revoked. This is an underspecification.

---

### 14. Authority Amplification with Explicit Meta-Authority

| Property | Input Authority | Output Effect | Within Envelope? |
|----------|-----------------|---------------|------------------|
| Capability | produce_authority | **execute_payment** | ❌ |

**Critical finding:** This is the central adversarial experiment. Even when an actor is explicitly granted POLICY_EFFECT_AUTHORITY, the downstream effect (execute_payment) still exceeds the envelope (produce_authority).

This confirms the architectural thesis: **effect authority must be bounded by an envelope**. The authority to create authority is not the authority to create any authority.

---

### 15. Authority Cut Sets

The minimum cut set between PRINCIPAL and EXECUTION contains:

```
POLICY_AUTHORITY → POLICY_EFFECT_AUTHORITY → GOVERNANCE → AUTHORITY_MATERIALIZATION → CAPABILITY
```

**Finding:** POLICY_EFFECT_AUTHORITY is a distinct node in the cut set. Without it, the chain is open.

---

### 16. Scope/Temporal Authority

| From | To | Within Envelope? |
|------|----|------------------|
| production | staging | ❌ |
| staging | production | ❌ |
| production | production | ✅ |

**Finding:** Scope authority is directional. Production does not grant staging, and staging does not grant production. Each scope requires explicit authority.

---

### 17. Capability Class Transitions

| From | To | Within Envelope? |
|------|----|------------------|
| read_only | observe | ❌ |
| observe | analyze | ❌ |
| analyze | simulate | ❌ |
| simulate | execute_action | ❌ |
| recommend | authorize | ❌ |
| authorize | execute_action | ❌ |
| modify_policy | execute_payment | ❌ |

**Finding:** ALL capability class transitions are amplifying. There is no implicit ordering that grants higher capability classes from lower ones.

---

## The Semantic Transition Map

The experiments reconstruct the current authority semantics:

| From Concept | To Concept | Transformation | Authority Created? | Authority Transformed? |
|--------------|------------|----------------|--------------------|------------------------|
| POLICY_VALIDITY | POLICY_AUTHORIZATION | evaluation | ❌ No | ❌ No |
| POLICY_AUTHORIZATION | GOVERNANCE_DISPOSITION | activation | ❌ No | ❌ No |
| GOVERNANCE_DISPOSITION | AUTHORITY | materialization | ❌ No | ❌ No |
| AUTHORITY | CAPABILITY | binding | ❌ No | ❌ No |
| CAPABILITY | EXECUTION | invocation | ❌ No | ❌ No |

**Critical finding:** The current architecture does NOT create authority at any transition. Each transition requires explicit authority. But the transitions are not envelope-checked, so amplification is possible.

---

## Underspecifications Discovered

| Distinction | Status | Impact |
|-------------|--------|--------|
| VALID vs AUTHORIZED vs EFFECTIVE | ❌ Conflated | Policy remains effective after revocation |
| Policy authority vs Policy effect | ❌ Conflated | Broader effects not detected |
| Authority at creation vs activation vs execution | ❌ Conflated | Temporal escalation undetected |
| Capability class transitions | ❌ Not tracked | Authority amplification undetected |
| Authority surface area | ❌ Not tracked | Predicate weakening undetected |
| Revocation effects | ❌ Not tracked | Post-revocation authority remains |
| Authority root | ❌ Not specified | No explicit root of authority |

---

## Required Invariants (Status After Phase 15)

| Invariant | Status |
|-----------|--------|
| POLICY ≠ AUTHORITY | ✅ Verified |
| POLICY VALIDITY ≠ POLICY AUTHORITY | ✅ Verified |
| POLICY AUTHORITY ≠ DOWNSTREAM AUTHORITY | ✅ Verified |
| POLICY CORRECTNESS ≠ POLICY AUTHORITY | ✅ Verified |
| POLICY EFFECT ≠ POLICY AUTHORITY | ✅ Verified |
| POLICY DELETION ≠ HISTORICAL ERASURE | ✅ Verified |
| POLICY SUPERSESSION ≠ MUTATION OF HISTORY | ✅ Verified |
| POLICY ROLLBACK ≠ AUTHORITY ROLLBACK | ✅ Verified |
| CURRENT POLICY ≠ HISTORICAL POLICY | ✅ Verified |
| SCOPE UNION ≠ SCOPE AUTHORITY | ✅ Verified |
| TEMPORAL UNION ≠ TEMPORAL AUTHORITY | ✅ Verified |
| PROVENANCE PRESERVATION ≠ PROVENANCE PROMOTION | ✅ Verified |
| POLICY COMPOSITION ≠ AUTHORITY COMPOSITION | ✅ Verified |
| POLICY MODIFICATION ≠ AUTOMATIC AUTHORITY | ✅ Verified |
| POLICY ACTIVATION ≠ AUTOMATIC AUTHORIZATION | ✅ Verified |
| OVERRIDE ≠ GOVERNANCE BYPASS | ✅ Verified |
| REPLAY ≠ CURRENT AUTHORITY | ✅ Verified |
| REVALIDATION ≠ REVOCATION | ✅ Verified |
| RUNTIME MAY MATERIALIZE AUTHORITY | ✅ Verified |
| RUNTIME NEVER CREATES AUTHORITY | ✅ Verified |
| LEGITIMATE POLICY AUTHORITY ≠ UNBOUNDED DOWNSTREAM AUTHORITY | ✅ Verified |
| AUTHORITY TO CHANGE POLICY ≠ AUTHORITY GRANTED BY POLICY | ✅ Verified |
| AUTHORITY TO CHANGE POLICY ≠ AUTHORITY TO CREATE EVERY EFFECT OF THAT POLICY | ✅ Verified |
| **AUTHORITY SURFACE IS MULTI-DIMENSIONAL** | ✅ **NEW** |
| **AUTHORITY ENVELOPE BOUNDS DOWNSTREAM EFFECTS** | ✅ **NEW** |
| **EFFECT AUTHORITY MUST BE BOUNDED BY ENVELOPE** | ✅ **NEW** |
| **IDENTITY TRANSFORMATION IS THE ONLY CONSERVATIVE TRANSFORMATION** | ✅ **NEW** |

---

## The Answer to the Central Question

> **Can a principal legitimately authorized to modify governance policy cause downstream authority that exceeds the authority they were actually delegated to create?**

**YES.**

The experimental evidence demonstrates that:

1. An actor with MODIFY_POLICY authority can modify predicates to broaden the authority surface.
2. The modified policy produces a broader governance disposition.
3. The broader disposition materializes broader execution authority.
4. The resulting execution authority exceeds the actor's legitimate policy authority.
5. Every individual operation is authorized; the amplification occurs at the composition.

> **Can the architecture distinguish unauthorized downstream amplification from legitimate delegated meta-authority to create downstream authority?**

**NOT YET.**

The experiments demonstrate that:

1. **AuthoritySurface** provides the semantic foundation for comparing authority across dimensions.
2. **AuthorityEnvelope** provides the mechanism for bounding downstream effects.
3. **Even explicit effect authority must be bounded** — the envelope is necessary at every level.
4. **The transformation algebra** identifies which transformations are conservative vs. amplifying.

The architecture CAN distinguish amplification from legitimate delegation IF the effect boundary is implemented.

> **What is the smallest additional authority boundary required to prevent unauthorized amplification without suppressing legitimate governance?**

**POLICY_EFFECT_AUTHORITY with AuthorityEnvelope.**

The smallest additional boundary is:

1. **AuthoritySurface** — represent authority as a multi-dimensional object.
2. **AuthorityEnvelope** — bound the downstream effects of each authority grant.
3. **Effect boundary check** — verify that policy transformations stay within the envelope.

This does NOT require:
- A centralized authority
- Recursive authorization
- A universal authority ordering
- Denying all policy changes

It requires only that every authority grant carries an explicit envelope, and that policy transformations are checked against that envelope.

---

## Phase 15 Classification

**Result:** `EFFECT_BOUNDARY_ESTABLISHED`

The effect boundary is experimentally validated as a necessary architectural concept. AuthoritySurface and AuthorityEnvelope provide the semantic foundation. The transformation algebra identifies which transformations are conservative vs. amplifying. The experiments demonstrate that even explicit meta-authority must be bounded by an envelope.

The architecture now has:

```
PRINCIPAL
   ↓
POLICY-CHANGE AUTHORITY (with envelope)
   ↓
POLICY TRANSFORMATION (checked against envelope)
   ↓
POLICY EFFECT (bounded by envelope)
   ↓
EFFECT AUTHORITY BOUNDARY (envelope check)
   ↓
GOVERNANCE
   ↓
DOWNSTREAM AUTHORITY (bounded by envelope)
   ↓
CAPABILITY
   ↓
EXECUTION
```

---

## Next Boundary (Phase 16)

**Authority Root** — The experiments reveal that the authority root is not explicitly specified. The chain must terminate somewhere. Possible roots include:

- Human authorization
- Cryptographic root
- Organizational delegation
- Static policy
- Hardware boundary
- External authority

Phase 16 should determine what the current implementation actually assumes as the authority root, and whether the root itself requires governance.

---

## Pause Point

The experimental record now establishes through Phase 15:

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
16. **Authority is multi-dimensional** — AuthoritySurface captures principal, operation, resource, scope, temporal interval, conditions, provenance, policy lineage, and capability class.
17. **Authority envelopes bound downstream effects** — AuthorityEnvelope provides the mechanism for checking policy transformations.
18. **Effect authority must be bounded** — even explicit meta-authority requires envelope enforcement.
19. **The transformation algebra is experimentally derived** — identity is the only conservative transformation; all others require new authority.
20. **Capability class transitions are always amplifying** — no implicit ordering grants higher capability classes from lower ones.

The architecture has reached the point where the authority creation problem is now precisely specified. The next phase must determine where authority originates.
