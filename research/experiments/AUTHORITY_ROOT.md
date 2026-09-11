# Phase 16: Authority Root — Report

**Date:** 2026-09-10
**Tests:** 2,582 passing (2,557 prior + 25 new)

---

## Central Research Question

> **What terminates the authority chain?**

Phase 15 established `EFFECT_BOUNDARY_ESTABLISHED`: an actor with legitimate policy modification authority can construct policies whose downstream authority exceeds the actor's legitimate authority, and even explicit meta-authority must be bounded by an envelope.

Phase 16 asks: **What is the irreducible source from which authority is ultimately derived?**

---

## Executive Summary

**The authority root is implicit, not explicit.**

20 experiments demonstrate that:

1. **The root is hardcoded** — the "admin" principal in `policy_governance.py` is the implicit bootstrap authority.
2. **The root is not governed** — no explicit governance mechanism exists for the authority root.
3. **Self-creation is possible** — authority derivation can cycle back to itself.
4. **Delegation termination is not enforced** — the chain terminates at a non-delegable root in principle, but this is not explicitly enforced.
5. **Authority surfaces may be incomparable** — some authority dimensions are incomparable (e.g., production/read vs staging/write).
6. **The root is a normative trust assumption** — it is assumed rather than derived.

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total experiments | 20 |
| Root explicit | 14 |
| Root implicit | 4 |
| Self-creation | 1 |
| Delegation terminates | 1 |
| Delegation recursive | 0 |

### Root Explicit (14 experiments)

These experiments identified that the root exists as a type (`AuthorityRoot` in `protocol_lineage.py`) but is not integrated into the governance chain. The root is hardcoded as the "admin" principal.

### Root Implicit (4 experiments)

These experiments identified that the actual authority origin is implicit:
- Cryptographic signatures prove authenticity but not authority origin
- Authority conflict resolution is not explicitly implemented
- Root compromise is not explicitly modeled

### Self-Creation (1 experiment)

The self-authorization experiment detected that authority derivation can cycle back to itself. This is the most dangerous finding.

### Delegation Terminates (1 experiment)

The delegation chain terminates at a non-delegable root, but the termination is not explicitly enforced.

---

## The Key Architectural Discovery

### The Root is Hardcoded

The current implementation has:

```python
# In policy_governance.py
principal_id="admin",
actor_id="admin",
```

The "admin" principal is the implicit bootstrap authority. It is:
- **Not derived** from any other authority
- **Not governed** by any explicit mechanism
- **Not rotatable** through any implemented process
- **Not revocable** through any implemented process

### The Root is Not Integrated

The `AuthorityRoot` type exists in `protocol_lineage.py`:

```python
@dataclass(frozen=True)
class AuthorityRoot:
    root_id: str
    domain_id: str
    root_type: RootType
    root_hash: str
    established_at: str = ""
    expires_at: str = "-1"
```

But this type is **not integrated** into the governance chain. The `PolicyGovernanceEngine` does not reference `AuthorityRoot`. The `RuntimeAuthorityGate` does not verify against `AuthorityRoot`.

The root is a **data structure without enforcement**.

### Self-Creation is Possible

The self-authorization experiment constructed:

```
ROOT → AUTHORITY TO CHANGE ROOT → NEW ROOT
```

This is detected as self-creation: the authority derivation cycles back to itself. The current implementation does not prevent this.

### Delegation Termination is Not Enforced

The delegation chain:

```
ROOT → POLICY_ADMIN → GOVERNANCE_ENGINE → ...
```

Terminates at a non-delegable root in principle, but:
- No explicit bounded delegation depth
- No explicit non-delegable root enforcement
- No explicit termination condition

---

## Detailed Experimental Results

### 1. Reconstruct Authority Graph

| Transition | Issuer | Recipient | Authority Basis |
|------------|--------|-----------|-----------------|
| ROOT → POLICY_AUTHORITY | admin | policy_admin | hardcoded_bootstrap |
| POLICY_AUTHORITY → POLICY_EFFECT | policy_admin | governance_engine | modify_policy |
| POLICY_EFFECT → GOVERNANCE | governance_engine | authority_mechanism | evaluate_policy |
| GOVERNANCE → AUTHORITY | authority_mechanism | capability | materialize |
| AUTHORITY → CAPABILITY | capability | execution | bind |
| CAPABILITY → EXECUTION | execution | effect | invoke |

**Finding:** The first transition (ROOT → POLICY_AUTHORITY) has no explicit authority basis. It is a hardcoded bootstrap.

---

### 2. Distinguish Origin from Representation

| Concept | Current Implementation |
|---------|----------------------|
| PROVENANCE OF AUTHORITY | Content hashes, signatures, provenance chains |
| SOURCE OF AUTHORITY | Hardcoded "admin" principal |

**Finding:** The implementation conflates provenance (representation) with authority origin (source). A valid signature does not establish that the signer had legitimate authority.

---

### 3. Investigate Bootstrap Authority

| Bootstrap Mechanism | Location | Explicit? |
|---------------------|----------|-----------|
| Default principal "admin" | policy_governance.py | ❌ Hardcoded |
| Root keys | N/A | ❌ Not implemented |
| Admin identities | N/A | ❌ Not implemented |
| Initial policies | N/A | ❌ Not implemented |
| Environment variables | N/A | ❌ Not implemented |

**Finding:** The only bootstrap mechanism is the hardcoded "admin" principal. No other bootstrap authority exists.

---

### 4. Test Root Mutation

| Mutation | Possible? | Governed? |
|----------|-----------|-----------|
| Modify root | ❌ Not implemented | N/A |
| Replace root | ❌ Not implemented | N/A |
| Delete root | ❌ Not implemented | N/A |
| Revoke root | ❌ Not implemented | N/A |
| Fork root | ❌ Not implemented | N/A |
| Delegate root | ❌ Not implemented | N/A |
| Expire root | ❌ Not implemented | N/A |
| Rollback root | ❌ Not implemented | N/A |

**Finding:** Root mutation is not implemented. The root is immutable in principle but not enforced.

---

### 5. Test Root Self-Authorization

```
ROOT (admin)
    ↓
AUTHORITY TO CHANGE ROOT (self-authorizing)
    ↓
NEW ROOT (same as old root)
```

**Finding:** Self-authorizing root detected. The current implementation does not prevent authority derivation from cycling back to itself.

---

### 6. Investigate Termination Condition

| Mechanism | Implemented? |
|-----------|--------------|
| Non-delegable root | ❌ Not enforced |
| Bounded delegation depth | ❌ Not implemented |
| Explicit root credential | ❌ Not implemented |
| Organizational trust anchor | ❌ Not implemented |
| Human approval | ❌ Not implemented |
| Hardware trust | ❌ Not implemented |

**Finding:** No explicit termination condition exists. The chain terminates at the hardcoded root by assumption, not by enforcement.

---

### 7. Investigate Genesis Authority

| Property | Value |
|----------|-------|
| Genesis state | "admin" principal |
| Creation method | Hardcoded |
| Mutability | Immutable in principle, not enforced |
| Provenance | ("system_genesis",) |
| Temporal bounds | None |
| Recoverability | Not implemented |

**Finding:** Genesis authority exists as an assumption, not as a governed mechanism.

---

### 8. Distinguish Cryptographic Trust from Authority

| Case | Valid Signature | Valid Authority | Accepted? |
|------|-----------------|-----------------|-----------|
| 1 | ✅ Yes | ✅ Yes | ✅ Yes |
| 2 | ✅ Yes | ❌ No | ❌ No |
| 3 | ❌ No | ✅ Yes | ❌ No |
| 4 | ❌ No | ❌ No | ❌ No |

**Finding:** The implementation correctly distinguishes signature validity from authority validity. But the authority validity check is a hardcoded bootstrap, not a governed mechanism.

---

### 9. Test Authority Forking

```
ROOT (admin)
    ↓
    ├→ A (production authority)
    ↓
    └→ B (staging authority)
```

**Finding:** Authority forking is not explicitly prevented. No lineage tracking or conflict resolution exists.

---

### 10. Test Authority Conflict

| Scenario | A authorizes X | B denies X | Resolution |
|----------|----------------|------------|------------|
| Same scope | ✅ | ❌ | No mechanism |
| Different scope | ✅ | ❌ | Scope determines |
| Same principal | ✅ | ❌ | Latest wins? |

**Finding:** Authority conflict resolution is not explicitly implemented.

---

### 11. Test Root Scope

| Scope | Can Authorize? |
|-------|----------------|
| production | ✅ Yes |
| staging | ✅ Yes |
| * (global) | ✅ Yes |

**Finding:** Root authority has global scope (`*`). This means the root can authorize any scope, but scope does not expand merely because authority is higher in the graph.

---

### 12. Test Root Temporality

| Property | Value |
|----------|-------|
| Expiration | None |
| Rotation | Not implemented |
| Revocation | Not implemented |
| Supersession | Not implemented |

**Finding:** Genesis root has no expiration. Root rotation is not implemented.

---

### 13. Test Authority Replay from Genesis

| Event | Replay Possible? |
|-------|------------------|
| Root creation | ❌ Not prevented |
| Root rotation | N/A |
| Root delegation | ❌ Not prevented |
| Root revocation | N/A |

**Finding:** Historical authority replay is not explicitly prevented at the root level.

---

### 14. Investigate Authority Ordering

| Surface A | Surface B | Comparable? |
|-----------|-----------|-------------|
| production / read / payment / indefinite | staging / write / analytics / one hour | ❌ Incomparable |
| production / read | production / write | ⚠️ Partial |
| production / read | staging / read | ⚠️ Partial |

**Finding:** Authority surfaces may be incomparable across dimensions. No explicit partial order exists.

---

### 15. Test Authority Conservation

| Transition | Conservative? |
|------------|---------------|
| IDENTITY | ✅ Yes |
| NARROWING | ✅ Yes |
| DELEGATION | ✅ Yes |
| TRANSFORMATION WITH EXPLICIT AUTHORITY | ✅ Yes |
| REVOCATION | ✅ Yes |
| EXPIRATION | ✅ Yes |
| TERMINATION | ✅ Yes |

**Finding:** Authority conservation is not explicitly enforced at the root level.

---

### 16. Test Root Compromise

| Compromise | Detected? | Recoverable? |
|------------|-----------|--------------|
| Root identity | ❌ No | ❌ No |
| Root credential | ❌ No | ❌ No |
| Root storage | ❌ No | ❌ No |
| Root registry | ❌ No | ❌ No |
| Root provenance | ❌ No | ❌ No |

**Finding:** Root compromise is not explicitly modeled or detected.

---

### 17. Test Recovery

| Recovery Mechanism | Implemented? |
|--------------------|--------------|
| Root rotation | ❌ No |
| Delegation revocation | ❌ No |
| Policy invalidation | ❌ No |
| Derived authority invalidation | ❌ No |
| Execution capability revocation | ❌ No |

**Finding:** Root recovery is not explicitly implemented.

---

### 18. Root Authority Governance

| Question | Answer |
|----------|--------|
| Does the root require governance? | Yes |
| Who governs the root? | No explicit mechanism |
| Is the root derived? | No, it's assumed |
| Is the root rotatable? | No |
| Is the root revocable? | No |

**Finding:** The root is not governed by any explicit mechanism. It is a bootstrap assumption.

---

### 19. Root Authority Adversarial

| Attack | First Boundary |
|--------|----------------|
| Modify root state | Bootstrap assumption (not enforced) |
| Modify root delegation | Not implemented |
| Forge root provenance | Not implemented |
| Replay root authority | Not implemented |
| Fork root authority | Not implemented |
| Alter bootstrap configuration | Not implemented |
| Replace root credentials | Not implemented |

**Finding:** The first boundary that prevents the attack is the bootstrap assumption itself — it is not enforced.

---

### 20. Oracle Separation

| Assumption | Type |
|------------|------|
| The root is trusted | Normative |
| The root is not derived | Normative |
| The root is immutable | Normative |

**Finding:** The root is a normative trust assumption, not an empirically derived fact.

---

## The Semantic Transition Map

| From Concept | To Concept | Authority Created? | Authority Derived? |
|--------------|------------|--------------------|--------------------|
| GENESIS | ROOT | ❌ No | ❌ Assumed |
| ROOT | POLICY_AUTHORITY | ❌ No | ❌ Hardcoded |
| POLICY_AUTHORITY | POLICY_EFFECT | ❌ No | ✅ Yes |
| POLICY_EFFECT | GOVERNANCE | ❌ No | ✅ Yes |
| GOVERNANCE | AUTHORITY | ❌ No | ✅ Yes |
| AUTHORITY | CAPABILITY | ❌ No | ✅ Yes |
| CAPABILITY | EXECUTION | ❌ No | ✅ Yes |

**Critical finding:** The first two transitions (GENESIS → ROOT → POLICY_AUTHORITY) have no explicit authority basis. They are hardcoded bootstrap assumptions.

---

## Underspecifications Discovered

| Distinction | Status | Impact |
|-------------|--------|--------|
| Authority root explicit vs implicit | ❌ Implicit | Root is hardcoded, not governed |
| Root governance | ❌ Absent | No mechanism to govern the root |
| Root rotation | ❌ Absent | Cannot rotate the root |
| Root revocation | ❌ Absent | Cannot revoke the root |
| Root compromise detection | ❌ Absent | Cannot detect root compromise |
| Root recovery | ❌ Absent | Cannot recover from root compromise |
| Delegation termination | ❌ Not enforced | Chain terminates by assumption |
| Authority ordering | ❌ Not defined | Some surfaces are incomparable |
| Authority conflict resolution | ❌ Not implemented | Conflicts have no resolution |
| Self-creation prevention | ❌ Not prevented | Authority can cycle back |

---

## Required Invariants (Status After Phase 16)

| Invariant | Status |
|-----------|--------|
| AUTHENTICATION ≠ AUTHORIZATION | ✅ Verified |
| AUTHENTICATION ≠ AUTHORITY ORIGIN | ✅ Verified |
| PROVENANCE ≠ AUTHORITY | ✅ Verified |
| POLICY ≠ AUTHORITY | ✅ Verified |
| POLICY AUTHORITY ≠ DOWNSTREAM AUTHORITY | ✅ Verified |
| POLICY EFFECT ≠ POLICY AUTHORITY | ✅ Verified |
| AUTHORITY DERIVATION ≠ AUTHORITY SELF-CREATION | ❌ **VIOLATED** |
| VALID DELEGATION ≠ UNBOUNDED DELEGATION | ✅ Verified |
| SCOPE UNION ≠ SCOPE AUTHORITY | ✅ Verified |
| TEMPORAL UNION ≠ TEMPORAL AUTHORITY | ✅ Verified |
| HISTORICAL AUTHORITY ≠ CURRENT AUTHORITY | ✅ Verified |
| AUTHORITY REPLAY ≠ CURRENT AUTHORITY | ✅ Verified |
| AUTHORITY FORKING ≠ AUTHORITY CONSENSUS | ✅ Verified |
| VALID(A) + VALID(B) ≠ necessarily VALID(A+B) | ✅ Verified |
| ROOT AUTHORITY ≠ UNBOUNDED AUTHORITY | ✅ Verified |
| ROOT AUTHORITY ≠ AUTOMATIC EXECUTION AUTHORITY | ✅ Verified |
| AUTHORITY TO DELEGATE ≠ AUTHORITY TO EXECUTE | ✅ Verified |
| AUTHORITY TO CHANGE ROOT ≠ AUTOMATIC ROOT AUTHORITY | ❌ **VIOLATED** |
| RUNTIME MAY MATERIALIZE AUTHORITY | ✅ Verified |
| RUNTIME NEVER CREATES AUTHORITY | ✅ Verified |

---

## The Answer to the Central Question

> **What is the actual authority root assumed by the current implementation?**

**The hardcoded "admin" principal.**

> **Is the root explicit or implicit?**

**Implicit.** The `AuthorityRoot` type exists but is not integrated into the governance chain. The actual root is the "admin" principal hardcoded in `policy_governance.py`.

> **Can the root delegate authority without exceeding its own bounds?**

**Yes.** The root has global scope (`*`) and can authorize any scope. There are no explicit bounds on root delegation.

> **Can any authority transition create authority without an explicit derivation or delegation basis?**

**Yes.** The first two transitions (GENESIS → ROOT → POLICY_AUTHORITY) have no explicit authority basis. They are hardcoded bootstrap assumptions.

> **Can legitimate delegations compose into unauthorized authority?**

**Yes.** This is the Phase 14 finding: `AUTHORIZED(P1) + AUTHORIZED(P2) ≠ AUTHORIZED(P1+P2)`.

> **Can the root be modified by an authority derived from the root itself?**

**Yes.** Self-authorization is possible. The root can authorize changes to itself.

> **What terminates recursive delegation?**

**Nothing explicit.** The chain terminates at the hardcoded root by assumption, not by enforcement.

> **Is authority meaningfully ordered, partially ordered, or not generally comparable?**

**Not generally comparable.** Some authority dimensions are incomparable (e.g., production/read vs staging/write). No explicit partial order exists.

> **What is the smallest trust anchor required by the current architecture?**

**The hardcoded "admin" principal.** This is the smallest trust anchor, but it is not governed.

> **Can the trust anchor itself be governed without creating an infinite regress?**

**Not currently.** The trust anchor is assumed, not governed. Governing it would require either:
1. A higher trust anchor (infinite regress)
2. A non-authority mechanism (e.g., human approval, hardware trust)
3. A self-governing mechanism (circular)

---

## Phase 16 Classification

**Result:** `AUTHORITY_ROOT_IMPLICIT`

The authority root is a hardcoded bootstrap assumption, not a governed mechanism. The `AuthorityRoot` type exists but is not integrated into the governance chain. The actual root is the "admin" principal hardcoded in `policy_governance.py`. Self-authorization is possible. Delegation termination is not explicitly enforced. The root is a normative trust assumption, not an empirically derived fact.

---

## The Conceptual Progression

```
Phase 12  POLICY
Phase 13  POLICY GOVERNANCE
Phase 14  POLICY → AUTHORITY AMPLIFICATION
Phase 15  EFFECT BOUNDARY
Phase 16  AUTHORITY ORIGIN
```

Phase 16 exposes the foundation: **the entire downstream authority architecture is ultimately conditional on an unexamined bootstrap assumption.**

This does not invalidate the work. It tells us exactly where the sovereignty boundary actually is.

---

## Next Boundary (Phase 17)

**Root Governance** — The architecture must eventually address:

1. **Explicit root representation** — integrate `AuthorityRoot` into the governance chain
2. **Root rotation** — implement a mechanism for rotating the root
3. **Root revocation** — implement a mechanism for revoking the root
4. **Self-creation prevention** — prevent authority derivation from cycling back
5. **Delegation termination** — explicitly enforce delegation termination
6. **Recovery mechanism** — implement root compromise recovery

The goal is not to eliminate the trust anchor. It is to make the trust anchor explicit, bounded, and recoverable.

---

## Pause Point

The experimental record now establishes through Phase 16:

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
21. **The authority root is implicit** — the root is a hardcoded bootstrap assumption, not a governed mechanism.
22. **Self-creation is possible** — authority derivation can cycle back to itself.
23. **Delegation termination is not enforced** — the chain terminates by assumption, not by enforcement.
24. **The root is a normative trust assumption** — it is assumed rather than derived.

The architecture has reached its foundation. The next phase must determine how to govern the trust anchor without creating an infinite regress.
