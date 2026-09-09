# Epistemically Dependent Authorization

## Experiment Overview

**Date:** 2026-09-09
**Tests:** 2,272 passing (2,248 prior + 24 new)

## Central Research Question

> What makes an authorization remain justified after the epistemic state that produced it changes?

And the deeper question:

> Can authority remain bounded by the epistemic conditions that justified it without making every new observation an authority revocation event?

## Thesis

```
AUTHORIZATION VALIDITY ≠ EPISTEMIC VALIDITY ≠ WORLD STATE VALIDITY
```

But they may have **explicit dependency relationships**.

## Architecture

```
Evidence E1
    ↓
Proposition P
    ↓
Epistemic State
    ↓
Recommendation
    ↓
Governance
    ↓
Authorization A
    ↓
Capability
    ↓
Execution

Then:

Evidence E2 arrives
    ↓
Does E2 intersect A's dependencies?
    ↓
YES → Suspend / Reevaluate
NO → Preserve
```

## Authorization Dependency Graph

Each authorization now carries an explicit provenance-backed dependency graph:

| Dependency Type | Strength | Description |
|----------------|----------|-------------|
| EVIDENCE | Direct | Specific evidence that supports the authorization |
| PROPOSITION | Direct | Proposition that justifies the authorization |
| EPISTEMIC_STATE | Direct | Epistemic state at authorization time |
| EXPERIMENT | Transitive | Experiment that produced supporting evidence |
| GOVERNANCE_POLICY | Direct | Governance policy in effect |
| RESOURCE_IDENTITY | Direct | Resource that was the authorization target |
| TEMPORAL_INTERVAL | Direct | Temporal interval for authorization validity |
| RECOMMENDATION | Transitive | Recommendation that led to governance decision |

### Key Distinctions

```
DIRECT DEPENDENCY: Authorization directly depends on this
TRANSITIVE DEPENDENCY: Authorization depends on this through a chain
UNRELATED: No dependency relationship
CONTRADICTORY: Evidence contradicts a dependency
DEPENDENCY_CHANGED: Dependency has been modified but not contradicted
```

## Dependency Intersection Results

### Test Cases

| Case | Evidence Relation | Decision | Governance Review |
|------|------------------|----------|-------------------|
| A: Unrelated | unrelated | PRESERVE | No |
| B: Relevant | relevant | REEVALUATE | Yes |
| C: Weakens | weakens | REEVALUATE | Yes |
| D: Contradicts | contradicts | SUSPEND | Yes |
| E: Invalidates experiment | invalidates_experiment | SUSPEND | Yes |
| F: Resource change | changes_resource | REEVALUATE | Yes |
| G: Governance change | changes_governance | REEVALUATE | Yes |
| H: Historical | historical | PRESERVE | No |

### Key Finding

The critical operation is not:
> "did new evidence appear?"

It is:
> "does the new evidence intersect a dependency of this authorization?"

## Epistemic Dependency Cycles

### Cycle Detection

The system detects:
```
Authorization A
    ↓ depends on
Proposition P
    ↓ supported by
Evidence E
    ↓ produced by
Experiment X
    ↓ permitted by
Authorization A
```

This creates: `A → P → E → X → A`

### Classification

| Cycle Type | Description | Valid? |
|-----------|-------------|--------|
| NONE | No cycle detected | Yes |
| VALID_DEPENDENCY | Legitimate dependency chain | Yes |
| CIRCULAR_EPISTEMIC | Epistemic circularity | No |
| AUTHORITY_BOOTSTRAP | Self-justifying authority | No |
| SELF_JUSTIFYING | Authorization justifies itself | No |

### Experimental Result

When experiment `exp_001` is mapped to authorization `auth_001`:
- Cycle path: `auth_001 → exp_001 → auth_001`
- Classification: `AUTHORITY_BOOTSTRAP`
- Governance review: Required

## Staleness Dimensions

The system distinguishes:

| Staleness Type | Meaning |
|---------------|---------|
| AUTHORITY_STALE | Authorization itself is stale |
| EPISTEMICALLY_STALE | Epistemic basis has changed |
| RESOURCE_STALE | Resource state has changed |
| GOVERNANCE_STALE | Governance policy has changed |
| TEMPORALLY_STALE | Temporal interval has expired |
| PROVENANCE_STALE | Provenance chain is broken |

An authorization may be:
- Temporally valid while epistemically stale
- Epistemically valid while resource-stale
- Valid in all dimensions except governance

## Suspension vs. Revocation

### Critical Distinction

```
SUSPENDED: Authorization is temporarily inactive pending governance review
REVOKED: Authorization has been terminated by governance
```

New evidence can only **suspend** an authorization.
Only **governance** can revoke.

This preserves the invariant:
> EVIDENCE DOES NOT CREATE REVOCATION AUTHORITY

## Partial Invalidation

### Scenario

Plan: `A → B → C`

When B becomes invalid:
- **A**: Historically valid (preserved)
- **B**: Invalid (suspended)
- **C**: Requires reevaluation (depends on B)

The system distinguishes:
```
INVALID_COMPONENT: B
INVALID_DEPENDENT_COMPONENT: C
UNRELATED_COMPONENT: D (if it existed)
HISTORICALLY_VALID_COMPONENT: A
```

## Counterexamples 011-020

All resolved:

| ID | Title | Classification | Status |
|----|-------|---------------|--------|
| COUNTEREXAMPLE-011 | Unrelated evidence after authorization | VALID_REJECTION | Resolved |
| COUNTEREXAMPLE-012 | Relevant evidence after authorization | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-013 | Contradictory evidence after authorization | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-014 | Evidence invalidates original experiment | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-015 | Resource state changes without epistemic change | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-016 | Governance state changes without evidence change | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-017 | Epistemic dependency cycle | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-018 | Multi-agent evidence invalidation | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-019 | Partial plan invalidation | EXPECTED_BEHAVIOR | Resolved |
| COUNTEREXAMPLE-020 | Dependent authorization stale while independent valid | EXPECTED_BEHAVIOR | Resolved |

## Invariants Verified

| Invariant | Status |
|-----------|--------|
| NEW EVIDENCE DOES NOT AUTOMATICALLY INVALIDATE AUTHORIZATION | ✅ |
| UNRELATED EVIDENCE DOES NOT INVALIDATE AUTHORIZATION | ✅ |
| RELEVANT EVIDENCE MUST BE EVALUATED AGAINST AUTHORIZATION DEPENDENCIES | ✅ |
| EVIDENCE DOES NOT CREATE REVOCATION AUTHORITY | ✅ |
| EVIDENCE DOES NOT CREATE GOVERNANCE AUTHORITY | ✅ |
| EPISTEMIC STALENESS ≠ AUTOMATIC REVOCATION | ✅ |
| AUTHORIZATION DEPENDENCIES MUST BE PROVENANCE-BACKED | ✅ |
| DIRECT DEPENDENCY ≠ TRANSITIVE DEPENDENCY | ✅ |
| TRANSITIVE DEPENDENCY DOES NOT AMPLIFY AUTHORITY | ✅ |
| SUSPENSION ≠ REVOCATION | ✅ |
| RESTORATION REQUIRES EXPLICIT GOVERNANCE | ✅ |
| EPISTEMIC CONTRADICTION ≠ AUTOMATIC EXECUTION INVALIDITY | ✅ |
| WORLD STATE CHANGE ≠ EPISTEMIC CHANGE | ✅ |
| EPISTEMIC CHANGE ≠ GOVERNANCE CHANGE | ✅ |
| GOVERNANCE CHANGE ≠ AUTOMATIC RETROACTIVE INVALIDATION | ✅ |
| HISTORICAL AUTHORITY REMAINS IMMUTABLE | ✅ |
| CIRCULAR EPISTEMIC DEPENDENCY MUST NOT BOOTSTRAP AUTHORITY | ✅ |
| AUTHORIZATION MUST NOT DERIVE ITS OWN EVIDENCE | ✅ |
| AUTHORIZATION MUST NOT CREATE THE CONDITIONS REQUIRED TO JUSTIFY ITSELF | ✅ |

## Classification of Results

| Result Type | Count | Examples |
|-------------|-------|----------|
| IMPLEMENTED GUARANTEE | 19 | All epistemic invariants |
| EXPERIMENTAL OBSERVATION | 8 | Dependency intersection cases |
| EMPIRICAL RESULT | 4 | Staleness tracking, cycle detection |
| COUNTEREXAMPLE | 10 | All resolved |
| UNRESOLVED QUESTION | 0 | All addressed |

## Conclusion

The experiment demonstrates:

1. **Authorization can preserve explicit epistemic dependencies** without making every new observation a revocation event.

2. **Dependency-sensitive invalidation** is more precise than time-based or novelty-based invalidation.

3. **Evidence triggers suspension, not revocation** — governance authority is preserved.

4. **Epistemic dependency cycles** can be detected and prevented from bootstrapping authority.

5. **Partial invalidation** correctly propagates through dependency graphs without over-invalidating.

The architecture now supports:

> **Authority may depend on epistemic state, but epistemic state must never derive authority merely from the authorization it is supposed to justify.**

## Next Boundary

The next question is: **How does this architecture behave under adversarial epistemic manipulation?** Can an attacker carefully craft evidence to selectively invalidate specific authorizations while preserving others? This is the natural next experiment.
