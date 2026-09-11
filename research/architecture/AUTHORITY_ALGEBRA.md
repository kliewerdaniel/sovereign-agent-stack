# Authority Algebra — Compositional Properties of the Authority Protocol

> **Status: ACTIVE**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document specifies the algebraic properties of authority composition
in the Sovereign Agent Stack. It extends the epistemic architecture to
investigate whether the protocol is actually closed under arbitrary
composition.

---

## Preamble

The previous architecture established that:

- Each boundary must be independently valid
- Individual validity does not imply compositional validity

This architecture addresses the next boundary:

> Is authority actually conserved by the protocol?

The system does not assume the answer. It experimentally attacks the
algebra of authority composition.

---

## The Epistemic Chain (Extended)

```text
Observation → Hypothesis → Experiment → Intervention → Evidence →
Proposition → Epistemic State → Verification → Consensus →
Governance → Authorization → Execution

With composition:

Individual Artifact Validity
        ↓
Composition Operation
        ↓
Algebraic Property Verification
        ↓
Closure Verification
        ↓
Authority Conservation Check
        ↓
Execution
```

---

## Problem Statement

The architecture currently establishes:

> Each boundary must be independently valid.

Now investigate:

> Does validity compose?

Consider:

```text
A = valid epistemic state
B = valid verifier assertion
C = valid governance policy
D = valid identity
E = valid capability
F = valid authorization
```

It does NOT automatically follow that:

```text
A + B + C + D + E + F
```

constitutes a valid executable authority context.

The composition itself must be verified.

---

## Algebraic Properties

### Composition Laws

| Law | Status | Notes |
|-----|--------|-------|
| Associativity | HOLDS | (A⊕B)⊕C = A⊕(B⊕C) when contexts are compatible |
| Commutativity | ORDER_DEPENDENT | A⊕B = B⊕A for references, but not for ordered operations |
| Idempotence | HOLDS | A⊕A = A (duplicates detected) |
| Identity | NOT_APPLICABLE | Empty context is not an identity element |
| Monotonicity | HOLDS | Adding valid artifacts cannot increase authority |
| Non-Interference | PARTIAL | Unrelated authority doesn't affect unrelated actions |

### Associativity

```text
(A ⊕ B) ⊕ C = A ⊕ (B ⊕ C)
```

**Status: HOLDS** when contexts are compatible (same actor).

When contexts have different actors, both sides fail equally, preserving
equivalence.

### Commutativity

```text
A ⊕ B = B ⊕ A
```

**Status: ORDER_DEPENDENT** for references (sets), but **ORDER_DEPENDENT**
for operations like revocation, expiration, and delegation.

### Idempotence

```text
A ⊕ A = A
```

**Status: HOLDS** — duplicate artifacts are detected and deduplicated.

### Identity

```text
A ⊕ ∅ = A
```

**Status: NOT_APPLICABLE** — an empty context is not an identity element.
It simply contributes no authority.

### Monotonicity

```text
A ⊆ B → Authority(B) ≥ Authority(A)
```

**Status: HOLDS** — adding valid artifacts cannot increase authority beyond
what the governance policy permits.

### Non-Interference

```text
Authorize(X, A) = Authorize(X, A ⊕ B)  when B ⟂ X
```

**Status: PARTIAL** — unrelated authority generally doesn't affect
unrelated actions, but composition can change merge results.

---

## Authority Context

### Concept

An immutable structure representing the complete context used to
authorize an action. The context must be reconstructable.

### Invariants

- A context is NOT `authorized = true`
- It contains the exact artifacts from which authorization was derived
- Every dependency is explicitly referenced

### Fields

- `context_id` — unique identifier
- `action_proposal_ref` — reference to the action proposal
- `epistemic_state_refs` — references to epistemic states
- `verification_assertion_refs` — references to verification assertions
- `consensus_refs` — references to consensus artifacts
- `governance_policy_refs` — references to governance policies
- `actor_identity_ref` — reference to actor identity
- `capability_refs` — references to capabilities
- `delegation_refs` — references to delegations
- `resource_constraint_refs` — references to resource constraints
- `temporal_constraints` — temporal validity window
- `revocation_refs` — references to revocations
- `provenance_refs` — references to provenance artifacts
- `created_at` — creation timestamp
- `valid_from` — start of validity
- `valid_until` — end of validity
- `derivation_hash` — hash of the complete context

---

## Authority Closure

### Concept

A structural answer to: Given an action proposal and all referenced
artifacts, is the complete authority derivation closed?

### Closure Conditions

A closed authority context must satisfy:

1. All required dependencies exist
2. All dependencies are valid
3. All semantic relationships are valid
4. All provenance links resolve
5. All temporal constraints hold
6. All revocations are accounted for
7. All policy predicates are satisfied
8. All identity/capability constraints hold
9. No hidden authority dependency exists
10. No circular dependency exists
11. No scope expansion occurred
12. No conflicting branch remains unresolved

### Closure Status

| Status | Meaning |
|--------|---------|
| `CLOSED` | All conditions satisfied |
| `OPEN` | Not yet verified |
| `CIRCULAR` | Circular dependency detected |
| `MISSING_DEPENDENCY` | Required dependency missing |
| `TEMPORAL_MISMATCH` | Temporal constraints violated |
| `SCOPE_AMPLIFICATION` | Scope expanded without authorization |
| `RESOURCE_VIOLATION` | Resource constraints violated |
| `REVOCATION_VIOLATION` | Revoked authorization used |
| `POLICY_CONFLICT` | Conflicting policies |
| `DELEGATION_AMPLIFICATION` | Delegation scope exceeded |

---

## Resource Budget

### Concept

Tracks resource consumption across authorizations to prevent aggregate
violations.

### Invariants

- Resources cannot be created from nothing
- Allocation cannot exceed available budget
- Reserved resources are unavailable for other authorizations
- Budget is immutable (operations return new budgets)

### Fields

- `budget_id` — unique identifier
- `resource_type` — type of resource
- `total_limit` — total available
- `consumed` — amount consumed
- `reserved` — amount reserved

---

## Delegation

### Concept

Explicit delegation of authority with scope, duration, and constraints.

### Invariants

- Delegation cannot amplify authority without explicit authorization
- Delegation chains must terminate in an explicit authority root
- Delegation scope is strictly bounded
- Expired delegations are invalid

### Fields

- `delegation_id` — unique identifier
- `delegator_id` — who delegates
- `delegate_id` — who receives
- `capability` — what is delegated
- `scope` — scope of delegation
- `valid_from` — start of validity
- `valid_until` — end of validity
- `constraints` — additional constraints
- `provenance_hash` — provenance hash

---

## Branch Merging

### Concept

Merges authority branches with conflict detection.

### Merge Rules

1. Actors must match
2. Temporal windows must overlap
3. Authorization status must be compatible
4. Conflicts produce `CONFLICT` status
5. Merged scope is intersection of input scopes
6. Merged authorization is most restrictive of inputs

### Merge Status

| Status | Meaning |
|--------|---------|
| `MERGED` | Branches merged successfully |
| `CONFLICT` | Branches conflict |
| `INCOMPATIBLE` | Branches cannot be merged |

---

## Authority Accounting

### Concept

Tracks authority through composition.

```text
Authority(output) ≤ Authority(inputs) + Explicit Transformations
```

Any unexplained authority is flagged as `UNACCOUNTED`.

### Fields

- `accounting_id` — unique identifier
- `context_id` — context being accounted
- `input_authority` — list of input authority roots
- `output_authority` — list of output authority roots
- `explicit_transformations` — list of explicit transformations
- `unaccounted_authority` — list of unexplained authority
- `is_conserved` — whether authority is conserved

---

## Composition Attack Suite

### Attack Categories

| Category | Count | Description |
|----------|-------|-------------|
| Grouping | 1 | Alternate association |
| Ordering | 1 | Reorder operations |
| Duplication | 1 | Duplicate artifacts |
| Identity | 1 | Empty context |
| Monotonicity | 1 | Add irrelevant artifacts |
| Non-Interference | 1 | Unrelated authority |
| Conservation | 1 | Metadata authority |
| Cross-Domain | 1 | Cross-domain composition |
| Partial Composition | 1 | Missing dependencies |
| Serialization | 1 | Round-trip serialization |
| Resource Aggregation | 1 | Aggregate resource violation |
| Policy Composition | 1 | Policy conflicts |
| Delegation Chain | 1 | Delegation amplification |
| Branch Replay | 1 | Replay after revocation |
| Self-Justifying | 1 | Circular authority |

### Attack Results

All attacks are detected by the system. The attacks verify that:

1. Grouping doesn't amplify authority
2. Ordering doesn't affect reference sets
3. Duplicates are deduplicated
4. Empty context adds no authority
5. Irrelevant artifacts don't increase authority
6. Unrelated authority doesn't affect unrelated actions
7. Authority from metadata is unaccounted
8. Cross-domain composition is blocked
9. Missing dependencies are detected
10. Serialization preserves semantics
11. Aggregate resource violations are detected
12. Policy conflicts are detected
13. Delegation scope is bounded
14. Revocations are detected
15. Circular authority is detected

---

## The Fifteen Laws

### Law 1 — Individual validity does not imply compositional validity

`VALID(A) + VALID(B) + VALID(C) ≠ necessarily VALID(A⊕B⊕C)`

Composition must be explicitly verified.

### Law 2 — Authority is closed over its complete dependency graph

Every dependency must be valid simultaneously at the point where
authority is exercised.

### Law 3 — Authority cannot appear from nowhere

Every execution authority must have a traceable derivation to an
explicit authority root.

### Law 4 — Composition may constrain, preserve, or explicitly transform authority

Composition may not spontaneously create authority.

### Law 5 — Delegation cannot amplify authority without explicit authorization

Delegation chains must terminate in explicit authority roots.

### Law 6 — Unrelated valid authority must not affect unrelated actions

Non-interference is a first-class property.

### Law 7 — Historical validity does not imply current validity

Temporal constraints must hold at execution time.

### Law 8 — Current validity does not rewrite historical validity

Historical states are preserved.

### Law 9 — Execution outcomes do not create authorization

Successful execution does not retroactively establish authorization.

### Law 10 — Authorization does not create epistemic evidence

Authorization does not retroactively validate evidence.

### Law 11 — Epistemic authority does not automatically propagate to execution authority

Governance must explicitly map epistemic authority to authorization.

### Law 12 — No authority may be created by circular derivation

Authority must have an acyclic derivation graph.

### Law 13 — Every execution authority must terminate in an explicit authority root

Authority roots are: policies, actor identities, delegations.

### Law 14 — Correlated authority sources do not constitute independent authority

Verifier independence is determined by provenance, not identity.

### Law 15 — A complete protocol must verify the composition of valid artifacts

Not merely the validity of individual artifacts.

---

## Attack Coverage

### Grouping Attack

**Setup:** `(A⊕B)⊕C` vs `A⊕(B⊕C)`

**Result:** HOLDS — Both produce equivalent results.

### Ordering Attack

**Setup:** `A⊕B` vs `B⊕A`

**Result:** HOLDS for references (sets). ORDER_DEPENDENT for operations.

### Duplication Attack

**Setup:** `A⊕A`

**RESULT:** Idempotent — duplicates are deduplicated.

### Empty Context Attack

**Setup:** `A⊕∅`

**RESULT:** Empty context adds no authority.

### Monotonicity Attack

**Setup:** Add irrelevant artifacts

**RESULT:** Authority doesn't increase.

### Non-Interference Attack

**Setup:** Unrelated authority B, action X

**RESULT:** B doesn't affect X.

### Conservation Attack

**Setup:** Authority from metadata

**RESULT:** Unaccounted authority detected.

### Cross-Domain Attack

**Setup:** Financial + Admin authority

**RESULT:** Merge conflict detected.

### Partial Composition Attack

**Setup:** Remove one dependency

**RESULT:** Missing dependency detected.

### Serialization Attack

**Setup:** Round-trip serialization

**RESULT:** Semantics preserved.

### Resource Aggregation Attack

**Setup:** Three 40% requests

**RESULT:** Aggregate violation detected.

### Policy Composition Attack

**Setup:** Conflicting policies

**RESULT:** Policy conflict detected.

### Delegation Chain Attack

**Setup:** A→B→C with scope amplification

**RESULT:** Scope amplification detected.

### Branch Replay Attack

**Setup:** Replay after revocation

**RESULT:** Revocation detected.

### Self-Justifying Attack

**Setup:** `A→A`

**RESULT:** Circular authority detected.

---

## Trust Boundaries

### What Is Trusted

- Evidence with valid authority scope
- Provenance hashes
- Semantic rules applied consistently
- Verifier implementations

### What Is NOT Trusted

- Agent self-report
- Model output
- Evaluator claims
- State labels
- Confidence values
- Composition results (must be verified)

### What Must Be Independently Verified

- State from evidence
- Transition authority
- Consensus from assertions
- Authorization from policy + state + identity
- Composition from individual artifacts
- Closure from dependency graph
- Conservation from accounting

---

## Residual Authority Assumptions

1. **Evidence authority** — Evidence with valid authority scope can
   inform propositions within that scope.

2. **Provenance integrity** — Provenance hashes accurately reflect
   artifact lineage.

3. **Semantic rule consistency** — Semantic rules are applied
   consistently within a rule version.

4. **Implementation correctness** — Verifier implementations
   correctly implement their declared semantics.

5. **Identity uniqueness** — Verifier identities are unique and
   not forged.

6. **Policy authority** — Governance policies are authoritative
   within their jurisdiction.

7. **Actor identity** — Actor identities are established through
   a separate identity system.

---

## Architectural Question Answered

> If every artifact in the authorization chain is individually valid,
> what additional conditions must hold before the composed authority
> context is valid?

**Answer:**

```text
Individual Artifact Validity
        ↓
Dependency Resolution (all deps exist)
        ↓
Semantic Compatibility (actors match, policies compatible)
        ↓
Temporal Compatibility (simultaneously valid)
        ↓
Scope Compatibility (no amplification)
        ↓
Authority Non-Amplification (conservation holds)
        ↓
Resource Closure (no aggregate violations)
        ↓
Revocation Closure (no revoked auths)
        ↓
Provenance Closure (all links resolve)
        ↓
No Circular Authority (acyclic graph)
        ↓
Authority Root Resolution (all roots explicit)
        ↓
Authority Closure
        ↓
Execution-Time Revalidation
        ↓
Execution
```

---

## Five Critical Questions Answered

### 1. Can individually valid artifacts compose into invalid authority?

**Yes.** Two valid contexts with different actors cannot be merged.
The composition verifier detects this.

### 2. Can authority increase through composition without an explicit rule?

**No.** Resource budgets prevent aggregate violations. Delegation
chains don't amplify scope. Branch merging takes the most restrictive
interpretation.

### 3. Can unrelated authority affect unrelated actions?

**No.** Authority contexts are actor-specific and scope-specific.
Cross-actor composition is detected as a conflict.

### 4. Can every execution authority be traced to an explicit authority root?

**Yes.** Every closed authority context identifies its authority
roots: policies, actor identities, and delegations.

### 5. Is the protocol closed under composition?

**Yes.** The `AuthorityContextVerifier` checks all closure conditions,
and the `AuthorityAlgebraVerifier` validates algebraic properties.

---

## Known Limitations

1. **Identity system is minimal** — The current actor identity system
   is a placeholder.

2. **No delegation revocation propagation** — Revocation of a
   delegator does not automatically revoke delegates.

3. **Single policy composition** — Multi-policy composition is
   detected but not resolved.

4. **No cryptographic signing** — Artifacts use hash-based integrity
   but not cryptographic signatures.

5. **Non-interference is partial** — In some cases, composition can
   change merge results.

---

## Future Work

1. **Delegation revocation propagation** — Cascading revocations.

2. **Multi-policy resolution** — Procedures to resolve policy
   conflicts.

3. **Cryptographic signing** — Signing artifacts for non-repudiation.

4. **Distributed composition** — Composition across execution
   environments.

5. **Formal verification** — Machine-checkable closure proofs.

---

## File Reference

| File | Purpose |
|------|---------|
| `src/sas/quant/experiment/authority_algebra.py` | Algebra implementation |
| `tests/unit/test_authority_algebra.py` | Algebra tests |
| `docs/architecture/AUTHORITY_ALGEBRA.md` | This document |
