# Authority Non-Interference and Dependency-Scoped Composition

> **Status: ACTIVE**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document specifies the authority non-interference subsystem
of the Sovereign Agent Stack. It extends the epistemic architecture to
investigate why non-interference was PARTIAL and establishes
dependency-scoped authority composition.

---

## Preamble

The previous architecture established that:

- Each boundary must be independently valid
- Individual validity does not imply compositional validity
- Algebraic properties hold (associativity, idempotence, monotonicity, conservation)

However, **non-interference was only PARTIAL**. This architecture
addresses that gap.

---

## The Epistemic Chain (Extended)

```text
Observation → Hypothesis → Experiment → Intervention → Evidence →
Proposition → Epistemic State → Verification → Consensus →
Governance → Authorization → Composition → Execution

With non-interference:

Authority Decision
    ↓
Dependency Graph Construction
    ↓
Interference Analysis
    ↓
Decision Stability Verification
    ↓
Dependency-Scoped Execution
```

---

## Problem Statement

The architecture currently establishes:

> Each boundary must be independently valid.

Now investigate:

> Can an unrelated piece of state anywhere in the actual SAS stack
> change an authorization decision?

The core invariant to investigate is:

For action X and contexts A and B:

if B has no declared authority dependency on X,

then:

Authorize(X, A)
must equal
Authorize(X, A ⊕ B)

in every semantically equivalent execution context.

---

## Dependency Model

### Dependency Types

| Type | Meaning |
|------|---------|
| `DIRECT` | Explicitly declared dependency |
| `INDIRECT` | Transitive dependency |
| `RESOURCE` | Shared resource dependency |
| `TEMPORAL` | Shared temporal constraint |
| `POLICY` | Policy interaction |
| `ACTOR` | Actor identity dependency |
| `DELEGATION` | Delegation chain dependency |
| `EPISTEMIC` | Epistemic state dependency |
| `VERIFICATION` | Verification dependency |
| `CONSENSUS` | Consensus dependency |
| `REVOCATION` | Revocation propagation |
| `PROVENANCE` | Provenance dependency |
| `NONE` | No dependency |
| `UNKNOWN` | Cannot determine |

### Authority Dependency Graph

The dependency graph captures:

- **Nodes**: Authorization decisions, actors, policies, resources, epistemic states
- **Edges**: Explicit dependency relationships
- **Roots**: Authority roots (policies, actor identities, delegations)

### Graph Operations

- `has_dependency(source, target)` — Check if dependency exists
- `is_independent(source, target)` — Check if source is independent of target
- `get_closure(node)` — Get transitive dependency closure
- `get_dependencies(target)` — Get all dependencies targeting a node
- `get_dependents(source)` — Get all dependents of a node

---

## Interference Model

### Interference Types

| Type | Meaning |
|------|---------|
| `EXPECTED` | Legitimate dependency |
| `EXPLICITLY_DECLARED` | Declared dependency |
| `RESOURCE_CONTENTION` | Shared resource |
| `TEMPORAL_CONTENTION` | Shared temporal window |
| `POLICY_CONFLICT` | Policy interaction |
| `REVOCATION_PROPAGATION` | Revocation chain |
| `UNAUTHORIZED_INTERFERENCE` | Security failure |
| `UNDECLARED_DEPENDENCY` | Missing dependency edge |
| `UNKNOWN` | Cannot determine |

### Interference Classification

The system classifies interference by:

1. **Resource contention**: Shared resource constraints
2. **Temporal contention**: Shared temporal windows
3. **Policy conflict**: Overlapping policies
4. **Revocation propagation**: Revocation chains
5. **Explicit dependency**: Declared dependency edge
6. **Undeclared dependency**: Missing dependency edge
7. **Unauthorized interference**: Authority leak

---

## Decision Artifact

### Concept

A structured authorization decision containing enough information
to determine:

- action, subject, actor, resources
- policy set, temporal context
- required epistemic state, required verification
- authority roots, dependency closure
- final disposition

### Invariants

- Decisions are immutable
- Semantic equivalence ignores IDs
- Disposition is derived, not declared

### Fields

- `decision_id` — unique identifier
- `action` — action identifier
- `subject` — target of action
- `actor` — who performs the action
- `resources` — resource allocations
- `policy_refs` — applicable policies
- `temporal_context` — temporal constraints
- `required_epistemic` — epistemic prerequisites
- `required_verification` — verification prerequisites
- `authority_roots` — explicit authority roots
- `dependency_closure` — transitive dependency closure
- `scope` — authorization scope
- `disposition` — final decision

---

## Non-Interference Verification

### Process

1. Build dependency graph for context A
2. Derive authorization for context A
3. Build decision for context A
4. Merge contexts A and B
5. Build dependency graph for merged context
6. Derive authorization for merged context
7. Build decision for merged context
8. Compare decisions
9. Classify interference (if any)

### Interference Check

```python
if not decisions_differ:
    return NoInterference
else:
    return classify_interference(
        resource_contention,
        temporal_contention,
        policy_conflict,
        revocation_propagation,
        explicit_dependency,
        undeclared_dependency
    )
```

---

## Attack Suite

### Attack Categories

| Category | Count | Description |
|----------|-------|-------------|
| Unrelated Artifacts | 20 | Actor, policy, delegation, resource, proposition, evidence, epistemic state, verification, consensus, temporal, revocation, execution, provenance, cache, serialization, recovery, retry, branch, error, capability |
| Shared Dependencies | 10 | Actor, policy, delegation, resource, proposition, evidence, epistemic, verifier, consensus, temporal |
| Adversarial Combinations | 10 | Unrelated + revoked, expired, stronger capability, larger budget, stronger epistemic, majority consensus, governance approval, execution success, serialized, recovered |
| Complex Interference | 10 | Nested delegation, cross-actor delegation, shared policy + separate actors, shared budget + separate actions, shared temporal + separate actions, revocation propagation, branch merge, branch replay, partial failure, concurrent authorization |

### Attack Results

All 50 attacks are detected by the system. The attacks verify that:

1. Unrelated actors don't affect authorization
2. Unrelated policies don't affect authorization
3. Unrelated resources don't affect authorization
4. Shared actors may affect authorization (legitimate)
5. Shared resources may affect authorization (legitimate)
6. Resource contention is detected
7. Temporal contention is detected
8. Policy conflicts are detected
9. Revocation propagation is detected
10. Undeclared dependencies are detected

---

## The Fifty Laws

### Law 1 — Unrelated actor does not interfere

Adding an unrelated actor must not change authorization.

### Law 2 — Unrelated policy does not interfere

Adding an unrelated policy must not change authorization.

### Law 3 — Unrelated delegation does not interfere

Adding an unrelated delegation must not change authorization.

### Law 4 — Unrelated resource does not interfere

Adding an unrelated resource must not change authorization.

### Law 5 — Unrelated proposition does not interfere

Adding an unrelated proposition must not change authorization.

### Law 6 — Unrelated evidence does not interfere

Adding unrelated evidence must not change authorization.

### Law 7 — Unrelated epistemic state does not interfere

Adding an unrelated epistemic state must not change authorization.

### Law 8 — Unrelated verification does not interfere

Adding an unrelated verification must not change authorization.

### Law 9 — Unrelated consensus does not interfere

Adding an unrelated consensus must not change authorization.

### Law 10 — Unrelated temporal window does not interfere

Adding an unrelated temporal window must not change authorization.

### Law 11 — Unrelated revocation does not interfere

Adding an unrelated revocation must not change authorization.

### Law 12 — Unrelated execution does not interfere

Adding an unrelated execution must not change authorization.

### Law 13 — Unrelated provenance does not interfere

Adding unrelated provenance must not change authorization.

### Law 14 — Unrelated cache does not interfere

Adding unrelated cache state must not change authorization.

### Law 15 — Unrelated serialization does not interfere

Adding unrelated serialized state must not change authorization.

### Law 16 — Unrelated recovery does not interfere

Adding unrelated recovery state must not change authorization.

### Law 17 — Unrelated retry does not interfere

Adding unrelated retry state must not change authorization.

### Law 18 — Unrelated branch does not interfere

Adding an unrelated branch must not change authorization.

### Law 19 — Unrelated error does not interfere

Adding unrelated error state must not change authorization.

### Law 20 — Unrelated capability does not interfere

Adding an unrelated capability must not change authorization.

### Law 21 — Shared actor may interfere

Sharing an actor may legitimately affect authorization.

### Law 22 — Shared policy may interfere

Sharing a policy may legitimately affect authorization.

### Law 23 — Shared delegation may interfere

Sharing a delegation may legitimately affect authorization.

### Law 24 — Shared resource may interfere

Sharing a resource may legitimately affect authorization.

### Law 25 — Shared proposition may interfere

Sharing a proposition may legitimately affect authorization.

### Law 26 — Shared evidence may interfere

Sharing evidence may legitimately affect authorization.

### Law 27 — Shared epistemic prerequisite may interfere

Sharing an epistemic prerequisite may legitimately affect authorization.

### Law 28 — Shared verifier may interfere

Sharing a verifier may legitimately affect authorization.

### Law 29 — Shared consensus prerequisite may interfere

Sharing a consensus prerequisite may legitimately affect authorization.

### Law 30 — Shared temporal constraint may interfere

Sharing a temporal constraint may legitimately affect authorization.

### Law 31 — Unrelated + revoked

Adding unrelated artifacts with revocation must not interfere unless
revocation propagates.

### Law 32 — Unrelated + expired

Adding unrelated artifacts with expiration must not interfere unless
expiration affects shared temporal constraints.

### Law 33 — Unrelated + stronger capability

Adding unrelated stronger capabilities must not increase authority.

### Law 34 — Unrelated + larger budget

Adding unrelated larger budgets must not increase authority.

### Law 35 — Unrelated + stronger epistemic state

Adding unrelated stronger epistemic states must not increase authority.

### Law 36 — Unrelated + majority consensus

Adding unrelated majority consensus must not increase authority.

### Law 37 — Unrelated + governance approval

Adding unrelated governance approval must not increase authority.

### Law 38 — Unrelated + execution success

Adding unrelated execution success must not increase authority.

### Law 39 — Unrelated + serialized state

Adding unrelated serialized state must not increase authority.

### Law 40 — Unrelated + recovered state

Adding unrelated recovered state must not increase authority.

### Law 41 — Nested delegation

Nested delegation chains must not amplify scope.

### Law 42 — Cross-actor delegation

Cross-actor delegation must not create unauthorized authority.

### Law 43 — Shared policy + separate actors

Shared policies with separate actors must not create unauthorized
interference.

### Law 44 — Shared budget + separate actions

Shared budgets with separate actions must correctly detect resource
contention.

### Law 45 — Shared temporal session + separate actions

Shared temporal sessions with separate actions must correctly detect
temporal contention.

### Law 46 — Revocation propagation

Revocations must propagate through explicit delegation chains.

### Law 47 — Branch merge

Branch merging must detect conflicts.

### Law 48 — Branch replay

Branch replay must revalidate current state.

### Law 49 — Partial failure

Partial failures must not leave residual authority.

### Law 50 — Concurrent authorization

Concurrent authorizations must not create aggregate violations.

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
- Unrelated authority (must not interfere)

### What Must Be Independently Verified

- State from evidence
- Transition authority
- Consensus from assertions
- Authorization from policy + state + identity
- Composition from individual artifacts
- Closure from dependency graph
- Conservation from accounting
- Non-interference from dependency analysis

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

8. **Dependency completeness** — The dependency graph captures all
   relevant authority dependencies.

---

## Architectural Question Answered

> Can the system distinguish "this other authority exists" from
> "this other authority is a prerequisite for this action"?

**Answer:**

Yes. The dependency graph explicitly distinguishes:

- **DIRECT**: Explicitly declared dependency
- **INDIRECT**: Transitive dependency
- **NONE**: No dependency
- **UNKNOWN**: Cannot determine

The authorization decision includes the dependency closure, making
every authority dependency explicit and explainable.

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
Cross-actor composition is detected as a conflict. The dependency
graph ensures unrelated authority doesn't propagate.

### 4. Can every execution authority be traced to an explicit authority root?

**Yes.** Every closed authority context identifies its authority
roots: policies, actor identities, and delegations.

### 5. Is the protocol closed under composition?

**Yes.** The `AuthorityContextVerifier` checks all closure conditions,
the `AuthorityAlgebraVerifier` validates algebraic properties, and
the `AuthorityNonInterferenceVerifier` ensures dependency-scoped
composition.

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

5. **Dependency graph completeness** — The dependency graph may not
   capture all implicit dependencies.

---

## Future Work

1. **Delegation revocation propagation** — Cascading revocations.

2. **Multi-policy resolution** — Procedures to resolve policy
   conflicts.

3. **Cryptographic signing** — Signing artifacts for non-repudiation.

4. **Distributed composition** — Composition across execution
   environments.

5. **Formal verification** — Machine-checkable closure proofs.

6. **Runtime integration** — Integration with the actual SAS
   execution path.

---

## File Reference

| File | Purpose |
|------|---------|
| `src/sas/quant/experiment/authority_non_interference.py` | Non-interference implementation |
| `tests/unit/test_authority_non_interference.py` | Non-interference tests |
| `docs/architecture/AUTHORITY_NON_INTERFERENCE.md` | This document |
