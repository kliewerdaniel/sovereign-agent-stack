# Epistemic Governance and Authorization Derivation

> **Status: ACTIVE**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document specifies the governance and authorization subsystem
of the Sovereign Agent Stack. It extends the epistemic architecture to
cover the boundary between **what is known** and **what is authorized**.

---

## Preamble

The previous architecture established that:

- An agent can propose a proposition
- Experiments can generate evidence
- An immutable state machine can accumulate authority
- An independent verifier can reconstruct whether authority was earned
- Multiple verifiers can be compared and their disagreement classified

This architecture addresses the next boundary:

> Can governance and authorization themselves be made independently
> derivable, provenance-backed, and resistant to authority escalation?

The system does NOT implement a generic policy engine. It treats
governance as an adversarial architectural experiment.

---

## The Epistemic Chain (Extended)

```text
Observation → Hypothesis → Experimental Design → Intervention →
Observed Difference → Evidence → Proposition → Epistemic Judgment →
Governance → Authorization → Execution

Extended with:

Agent proposes
      ↓
Evidence constrains
      ↓
Epistemic state establishes what is known
      ↓
Independent verification establishes what was actually established
      ↓
Governance evaluates policy
      ↓
Authorization is derived
      ↓
Execution protocol verifies authorization
      ↓
Action occurs
```

---

## Problem Statement

The architecture currently establishes:

> What does the system have authority to believe?

Now it must establish:

> What does the system have authority to do?

These are fundamentally different. A proposition may be `SUPPORTED`
while the corresponding action is `NOT_AUTHORIZED`.

---

## Four Layers

### Epistemic Layer

**Question:** What is established?

**Answer:** Epistemic state, verification assertions, consensus artifacts.

**Authority:** Evidence-backed, independently verifiable.

### Governance Layer

**Question:** What rules apply?

**Answer:** Governance policies, identity requirements, resource limits.

**Authority:** Policy-backed, versioned, immutable.

### Authorization Layer

**Question:** What action is permitted?

**Answer:** Authorization artifacts with full derivation basis.

**Authority:** Derived from epistemic state + governance policy + identity + constraints.

### Execution Layer

**Question:** What actually happened?

**Answer:** Execution artifacts with provenance.

**Authorization:** Independently verified before execution.

---

## Action Proposal

### Concept

A typed representation of an action request. An action proposal is
NOT authorization. It is merely:

> Someone is asking to perform this action.

### Invariants

- The proposer may be an agent
- The proposer must never become authoritative merely by creating the proposal
- A proposal has no authority until processed through governance

### Fields

- `action_id` — unique identifier
- `proposer_id` — who proposed the action
- `action_type` — type of action (e.g., TRADE, TRANSFER)
- `target` — target of the action
- `parameters` — action parameters
- `required_capabilities` — capabilities needed
- `epistemic_dependencies` — propositions this action depends on
- `evidence_refs` — evidence supporting the action
- `requested_scope` — scope of the action
- `requested_resources` — resources requested
- `requested_time_window` — when the action should occur

---

## Recommendation vs Authorization

### Critical Distinction

```text
Recommendation ≠ Authorization ≠ Execution
```

A model may produce:

```text
Recommendation: BUY_ASSET_X
```

That does NOT imply:

```text
Authorization: BUY_ASSET_X
```

And authorization does NOT imply:

```text
Execution: BUY_ASSET_X_OCCURRED
```

### Recommendation Artifact

- `recommendation_id` — unique identifier
- `proposer_id` — who made the recommendation
- `action_type` — recommended action
- `target` — target
- `confidence` — model confidence (NOT authority)
- `reasoning` — reasoning provided
- `evidence_refs` — supporting evidence

**Confidence is not authority.** A recommendation with confidence=0.999
has no more authority than one with confidence=0.5 unless governance
explicitly defines a mechanism for confidence to inform authorization.

---

## Governance Policy

### Concept

An immutable governance policy. The policy establishes the conditions
under which authorization **may** be derived. It does NOT automatically
grant authorization.

### Invariants

- Policy is immutable
- Changing policy creates a new policy artifact
- Historical policy is never mutated
- Policy versions are preserved

### Fields

- `policy_id` — unique identifier
- `policy_version` — version string
- `jurisdiction` — scope of applicability
- `allowed_actions` — actions that may be authorized
- `prohibited_actions` — actions that are denied
- `required_epistemic_dimensions` — dimension-specific requirements
- `required_verification_conditions` — verification requirements
- `required_identity_conditions` — identity/capability requirements
- `resource_limits` — resource constraints
- `temporal_constraints` — time-based constraints
- `escalation_requirements` — escalation rules
- `expiration` — when the policy expires
- `semantic_version` — semantic version of the policy

---

## Authorization Artifact

### Concept

A derived artifact representing authorization. Authorization must
contain the derivation basis, not just a boolean.

### Invariants

- Authorization is derived, not declared
- The executor must be able to independently verify authorization
- Authorization binds to specific action, actor, scope, and time
- Historical authorization is never mutated

### Fields

- `authorization_id` — unique identifier
- `action_proposal_ref` — reference to the action proposal
- `proposition_refs` — propositions this authorization depends on
- `epistemic_state_refs` — epistemic states used
- `verification_assertion_refs` — verification assertions used
- `consensus_conflict_refs` — consensus/conflict artifacts
- `governance_policy_ref` — policy used for derivation
- `policy_version` — policy version
- `identity_ref` — actor identity
- `capability_refs` — actor capabilities
- `resource_constraints` — resource limits applied
- `temporal_constraints` — temporal limits applied
- `authorization_scope` — scope of authorization
- `derivation_trace` — step-by-step derivation
- `expiration` — when authorization expires
- `provenance_hash` — provenance hash
- `derivation_hash` — derivation hash
- `status` — authorization status

---

## Authorization Status

### Status Values

| Status | Meaning |
|--------|---------|
| `AUTHORIZED` | All conditions satisfied |
| `DENIED` | Action prohibited or conditions not met |
| `INCONCLUSIVE` | Cannot determine authorization |
| `EXPIRED` | Authorization has expired |
| `SCOPE_MISMATCH` | Requested scope exceeds authorization |
| `MISSING_AUTHORITY` | Actor lacks required authority |
| `POLICY_CONFLICT` | Conflicting policies |
| `EPISTEMIC_PREREQUISITE_UNMET` | Epistemic state insufficient |
| `VERIFICATION_CONFLICT` | Verification disagreement |
| `PROVENANCE_INVALID` | Provenance verification failed |
| `REVOKED` | Authorization has been revoked |
| `ACTOR_MISMATCH` | Actor does not match authorization |
| `CAPABILITY_MISSING` | Actor lacks required capability |
| `RESOURCE_CONSTRAINT_VIOLATION` | Resource limit exceeded |
| `TEMPORAL_CONSTRAINT_VIOLATION` | Outside authorized time window |

### Critical Distinctions

- `DENIED` ≠ `NOT PROVEN`
- `INCONCLUSIVE` ≠ `DENIED`
- `AUTHORIZED` ≠ `EXECUTED`

---

## Revocation

### Concept

Revocation does NOT mutate the original authorization. It creates
a new artifact that references the original.

### Invariants

- Historical authorization remains intact
- Revocation is immutable
- Revocation is scoped
- Revocation is independently verifiable

### Fields

- `revocation_id` — unique identifier
- `authorization_ref` — authorization being revoked
- `revoker_id` — who revoked the authorization
- `reason` — why it was revoked
- `scope` — scope of revocation

---

## Execution Artifact

### Concept

An immutable record of an executed action. Execution does NOT
retroactively establish authorization.

### Invariants

- Execution is recorded, not authorized
- Execution binds to authorization
- Execution has its own provenance
- Outcome ≠ authorization

### Fields

- `execution_id` — unique identifier
- `action_type` — action performed
- `target` — target of the action
- `actor_id` — who performed the action
- `authorization_ref` — authorization used
- `parameters` — actual parameters
- `timestamp` — when execution occurred
- `result` — outcome of execution
- `result_details` — detailed results

---

## Authorization Derivation

### Process

1. Check if action is prohibited
2. Check if action is allowed
3. Check epistemic prerequisites
4. Check verification conditions
5. Check identity conditions
6. Check resource constraints
7. Check temporal constraints
8. If all pass: AUTHORIZED

### Deterministic

The derivation is deterministic given the same inputs. No model
confidence, reputation, or majority vote enters the derivation.

---

## Authorization Verifier

### Concept

The executor must NOT blindly trust an authorization artifact.
The verifier independently reconstructs whether the action is
actually authorized from the underlying components.

### Verification Steps

1. Verify action proposal integrity
2. Verify epistemic state references
3. Verify verification assertions
4. Verify consensus reference
5. Verify policy reference
6. Verify actor identity
7. Verify scope
8. Verify expiration
9. Verify revocations
10. Re-derive authorization

### Independent Reconstruction

The verifier re-derives authorization from the underlying components
and compares to the claimed authorization. If they differ, the
authorization is invalid.

---

## Execution Protocol

### Process

1. Verify authorization (full independent verification)
2. Check authorization status
3. Create execution artifact
4. Record execution

### No Execution Without Authorization

The protocol will not execute an action without a valid, verified,
non-expired, non-revoked authorization.

---

## The Thirty Laws

### Law 1 — MODEL OUTPUT ≠ EVIDENCE

Model output is not evidence. It may become evidence only through
a valid intervention and observed difference.

### Law 2 — EVIDENCE ≠ EPISTEMIC STATE

Evidence informs epistemic state. It does not determine it.

### Law 3 — EPISTEMIC STATE ≠ VERIFICATION

Epistemic state is verified by independent reconstruction.

### Law 4 — VERIFICATION ≠ CONSENSUS

Verification assertions are compared to produce consensus.

### Law 5 — CONSENSUS ≠ GOVERNANCE

Consensus does not override governance. Governance consumes consensus.

### Law 6 — GOVERNANCE ≠ AUTHORIZATION

Governance establishes conditions. Authorization is derived.

### Law 7 — AUTHORIZATION ≠ EXECUTION

Authorization permits execution. It does not cause it.

### Law 8 — EXECUTION ≠ EVIDENCE OF AUTHORIZATION

Successful execution does not retroactively establish authorization.

### Law 9 — Recommendation ≠ Authorization

A model recommendation has no authority unless governance explicitly
defines a mechanism for it.

### Law 10 — Confidence ≠ Authority

Model confidence is not authority. It may inform evidence under
specific conditions, but it does not authorize.

### Law 11 — Reputation ≠ Authority

Reputation is not authority unless governance explicitly defines
a provenance-backed mechanism for it.

### Law 12 — Majority ≠ Authorization

Majority vote does not authorize. Authorization is derived from
governance policy.

### Law 13 — Epistemic authority ≠ Execution authority

A supported proposition does not imply the corresponding action
is authorized.

### Law 14 — Authorization scope is specific

Authorization binds to specific action, actor, scope, and time.
It does not transfer.

### Law 15 — Authorization expires

Authorization has a temporal bound. After expiration, it is no
longer valid.

### Law 16 — Revocation is explicit

Revocation requires a separate, immutable artifact. It does not
mutate the original authorization.

### Law 17 — Historical authorization is preserved

Revocation does not rewrite history. The historical authorization
remains valid at the time it was issued.

### Law 18 — Policy is immutable

Policy versions are preserved. Changing policy creates a new artifact.

### Law 19 — Policy substitution is detected

Authorization derived under one policy cannot be used under another.

### Law 20 — Policy downgrade is detected

Substituting a weaker policy version is an authority escalation attack.

### Law 21 — Identity is part of authorization

Authorization binds to a specific actor. It does not transfer.

### Law 22 — Capability is required

Actor must have explicit capabilities. Having a different capability
does not substitute.

### Law 23 — Resource constraints are enforced

Authorization includes resource limits. Exceeding them is a violation.

### Law 24 — Epistemic prerequisites are dimension-specific

Policy requiring mechanism=REPLICATED is not satisfied by
mechanism=ROBUST. Each dimension is checked independently.

### Law 25 — Verification conflict blocks authorization

If verifiers disagree and policy requires consensus, authorization
is blocked.

### Law 26 — Governance conflict blocks authorization

If policies conflict and there is no resolution rule, authorization
is blocked.

### Law 27 — Execution requires independent verification

The execution protocol independently verifies authorization before
executing.

### Law 28 — TOCTOU is mitigated

Authorization is revalidated at execution time. Conditions that
changed between authorization and execution are detected.

### Law 29 — Execution evidence is separate

Execution has its own provenance. It does not derive from authorization.

### Law 30 — No component becomes authoritative by producing a plausible result

Authority must be derived through an explicit, provenance-backed
transition across the appropriate boundary.

---

## Attack Coverage

### Attack 1 — Agent Self-Authorization

**Setup:** Agent produces Recommendation + Authorization.

**Result:** REJECTED. The execution layer does not trust
agent-generated authorization.

### Attack 2 — Epistemic Status Injection

**Setup:** Agent creates epistemic_state = SUPPORTED without
valid transition.

**Result:** REJECTED. Epistemic status labels are not authority.

### Attack 3 — Consensus Injection

**Setup:** Agent creates EpistemicConsensus without valid verifier
assertions.

**Result:** REJECTED. Consensus is derived, not declared.

### Attack 4 — Majority Authorization

**Setup:** 9 agents say AUTHORIZED, 1 says DENIED.

**Result:** No implicit majority authorization. Authorization is
derived from governance policy.

### Attack 5 — Majority Verifier Escalation

**Setup:** 100 correlated verifiers supporting an action.

**Result:** Correlated assertions do not satisfy independent
verification requirements.

### Attack 6 — Stale Authorization

**Setup:** Authorization valid at T1, execution at T2 after expiration.

**Result:** EXPIRED. Historical authorization remains immutable.

### Attack 7 — Scope Escalation

**Setup:** Authorize trade(asset=A, quantity=10). Attempt quantity=1000.

**Result:** SCOPE_MISMATCH.

### Attack 8 — Parameter Mutation

**Setup:** Authorize transfer $100. Attempt transfer $10,000.

**Result:** REJECTED. Parameter substitution detected.

### Attack 9 — Identity Substitution

**Setup:** Authorization for Actor A. Attempt execution as Actor B.

**Result:** ACTOR_MISMATCH.

### Attack 10 — Capability Escalation

**Setup:** Actor has READ_DATA. Authorization requests EXECUTE_TRADE.

**Result:** MISSING_AUTHORITY.

### Attack 11 — Epistemic Prerequisite Substitution

**Setup:** Policy requires mechanism=REPLICATED, generalization=ROBUST.
Action supplies mechanism=ROBUST, generalization=UNRESOLVED.

**Result:** EPISTEMIC_PREREQUISITE_UNMET.

### Attack 12 — Verification Conflict

**Setup:** Verifier A: SUPPORTED. Verifier B: REFUTED.

**Result:** VERIFICATION_CONFLICT. Authorization blocked.

### Attack 13 — Governance Conflict

**Setup:** Policy A: AUTHORIZED. Policy B: DENIED.

**Result:** POLICY_CONFLICT. No arbitrary selection.

### Attack 14 — Policy Substitution

**Setup:** Authorization derived under Policy P1. Attempt execution
with Policy P2.

**Result:** REJECTED. Policy reference mismatch.

### Attack 15 — Policy Downgrade

**Setup:** Action requires policy version 7. Agent substitutes version 3.

**Result:** REJECTED. Policy version mismatch.

### Attack 16 — Evidence Substitution

**Setup:** Authorization references E1. Replace with E2 (same content,
different provenance).

**Result:** REJECTED. Provenance verification fails.

### Attack 17 — State Substitution

**Setup:** Authorization derived from State S7. Replace with forged S8.

**Result:** REJECTED. State reference mismatch.

### Attack 18 — Retroactive Revocation

**Setup:** Historical authorization at T1. Later policy at T2.

**Result:** Historical authorization preserved. Current authorization
is a derived view.

### Attack 19 — Revocation

**Setup:** Authorization A. Revocation R. Attempt execution.

**Result:** REJECTED. Revocation blocks execution.

### Attack 20 — Revocation Forgery

**Setup:** Forge revoked=true without valid revocation artifact.

**Result:** REJECTED. Revocation must be provenance-backed.

### Attack 21 — Expiration Forgery

**Setup:** Modify expiration=future without valid provenance.

**Result:** REJECTED. Derivation verification fails.

### Attack 22 — Resource Constraint Violation

**Setup:** Authorization max exposure $10,000. Attempt $10,001.

**Result:** REJECTED. Resource constraint enforced.

### Attack 23 — TOCTOU

**Setup:** Authorization verified at T1. Execution at T2 after
conditions change.

**Result:** REJECTED. Revalidation at execution time.

### Attack 24 — Agent Claims Successful Execution

**Setup:** Agent reports execution=SUCCESS without execution artifact.

**Result:** No execution authority. Self-reported execution is not
evidence.

### Attack 25 — Execution Forgery

**Setup:** Execution artifact claiming action occurred without valid
authorization.

**Result:** INVALID_EXECUTION. Execution provenance must bind
authorization.

### Attack 26 — Authorization Replay

**Setup:** Valid authorization for action A at T1. Replay against
action B.

**Result:** REJECTED. Authorization scope mismatch.

### Attack 27 — Cross-Proposition Confusion

**Setup:** Authorization depends on P1. Attempt to satisfy with P2.

**Result:** REJECTED. Semantic similarity is not epistemic identity.

### Attack 28 — Confidence Injection

**Setup:** Agent says confidence=0.999.

**Result:** Confidence has no authority.

### Attack 29 — Reputation Injection

**Setup:** Agent claims trusted=true, reputation=high.

**Result:** Reputation is not authority.

### Attack 30 — Authorization by Consensus

**Setup:** 100 verifiers say SUPPORTED. Governance says DENIED.

**Result:** DENIED. Epistemic consensus cannot override governance.

---

## Trust Boundaries

### What Is Trusted

- Evidence with valid authority scope
- Provenance hashes
- Semantic rules applied consistently within a rule version
- Verifier implementations correctly implementing declared semantics

### What Is NOT Trusted

- Agent self-report
- Model output
- Evaluator claims
- State labels
- Confidence values
- Execution environment claims
- Self-attested identity claims
- Consensus artifacts (must be derived)
- Authorization artifacts (must be verified)

### What Must Be Independently Verified

- State from evidence
- Transition authority from evidence authority
- Consensus from assertions
- Authorization from policy + state + identity + constraints
- Execution from authorization

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

> If an untrusted agent produces a recommendation, what exact chain
> of independently verifiable artifacts must exist before the system
> is entitled to execute the proposed action?

**Answer:**

```text
Agent Recommendation
        ↓
Action Proposal
        ↓
Required Epistemic Predicates
        ↓
Immutable Epistemic State
        ↓
Independent Verification
        ↓
Applicable Governance Policy
        ↓
Actor Identity + Capability
        ↓
Resource / Temporal Constraints
        ↓
Authorization Derivation
        ↓
Independent Authorization Verification
        ↓
Execution-Time Revalidation
        ↓
Execution
        ↓
Immutable Execution Artifact
```

Each arrow is a semantic contract. Each transition must be earned.
No transition can be skipped.

The system is NOT entitled to execute if any arrow is satisfied by:

- Model confidence
- Agent assertion
- Majority vote
- Reputation
- Identity count
- Unverifiable metadata
- Mutable state
- Stale policy
- Execution outcome
- Circular authorization

---

## Known Limitations

1. **Identity system is minimal** — The current actor identity system
   is a placeholder. A production system would need a full identity
   infrastructure.

2. **No delegation** — Authority delegation is not yet implemented.

3. **No resolution procedures** — The system classifies governance
   conflicts but does not resolve them.

4. **Single policy** — The system handles one policy at a time.
   Multi-policy composition is future work.

5. **No cryptographic signing** — Artifacts use hash-based integrity
   but not cryptographic signatures.

---

## Future Work

1. **Delegation** — Explicit authority delegation with scope and
   constraints.

2. **Multi-policy composition** — Composing multiple governance
   policies.

3. **Resolution procedures** — Procedures to resolve governance
   conflicts.

4. **Cryptographic signing** — Signing artifacts for non-repudiation.

5. **Distributed authorization** — Authorization across execution
   environments.

6. **Dynamic policy** — Policy that adapts based on context while
   preserving immutability.

---

## File Reference

| File | Purpose |
|------|---------|
| `src/sas/quant/experiment/epistemic_governance.py` | Governance implementation |
| `tests/unit/test_epistemic_governance.py` | Governance tests |
| `docs/architecture/EPISTEMIC_GOVERNANCE.md` | This document |
