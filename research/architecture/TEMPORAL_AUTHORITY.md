# Temporal Authority and Historical Provenance

## Status: ACTIVE v1.0.0

## Architecture

```
MODEL
 ↓
EVIDENCE
 ↓
EPISTEMIC STATE
 ↓
VERIFICATION
 ↓
CONSENSUS
 ↓
GOVERNANCE
 ↓
AUTHORIZATION
 ↓
EXECUTION
 ↓
PROVENANCE
 ↓
RECONSTRUCTION
 ↓
DISTRIBUTED RECONSTRUCTION
 ↓
TEMPORAL RECONSTRUCTION
 ↓
CONDITIONAL CONVERGENCE
```

## Central Research Question

> **Can the system reconstruct exactly what authority existed, what was knowable, what was verified, what governance applied, and what actions were authorized at a historical point in time without allowing later knowledge to rewrite the past?**

## Temporal Model

### Logical Time

Each artifact carries multiple time dimensions:

```text
event_time        — when the underlying event occurred
observation_time  — when the system observed it
ingestion_time    — when it was ingested into the protocol
verification_time — when it was verified
authorization_time — when authorization was issued
execution_time    — when execution occurred
revocation_time   — when revocation took effect
```

These are NOT interchangeable.

### Validity Interval

```text
valid_from  — when the artifact becomes valid
valid_until — when it expires (-1 = forever)
```

An artifact may be valid but not yet observed. An artifact may have been observed but no longer be valid.

### Temporal Boundary

```text
boundary_time  — the point in time being reconstructed
boundary_type  — event_time, observation_time, authorization_time, etc.
mode           — historical_reconstruction, current_reconstruction, retrospective_audit
```

### Artifact Availability

An artifact was available at T if:
- observation_time <= T
- ingestion_time <= T

An artifact is valid at T if:
- valid_from <= T <= valid_until (or valid_until = -1)

An artifact's authority is valid at T if:
- it is valid at T AND was available at T

## Reconstruction Modes

### Historical Reconstruction

```text
reconstruct_at(T)
```

Reconstructs protocol state **as of temporal boundary T**. Only artifacts available at or before T may inform the reconstruction. Future artifacts are filtered out.

### Current Reconstruction

```text
reconstruct_current()
```

Reconstructs protocol state incorporating all currently available artifacts.

### Retrospective Audit

```text
audit_at(T_looking_at_T')
```

Evaluates whether a historical decision at T' was correct under information available at T'. May use all artifacts up to T (where T > T') but must not use future information to rewrite historical state.

## Key Distinctions

### Historical Truth vs Current Validity

```text
T1: authorization = VALID
T2: revocation = issued
T3: reconstruction occurs
```

A reconstruction at T3 must be able to say:

```text
At T1: authorization was valid.
At T2: authorization was revoked.
At T3: authorization is no longer currently valid.
```

It must NOT rewrite T1 into:

```text
authorization was never valid.
```

### Event Time vs Observation Time

```text
Evidence occurred at T1
Node observed it at T2
Verifier verified it at T3
```

A later observation must not imply that the underlying event occurred later.

```text
ingestion_time ≠ event_time
verification_time ≠ event_time
execution_time ≠ authorization_time
```

### Authority Existence vs Authority Availability

```text
Historical authorization exists
but
current node cannot observe the authorization
```

must not become:

```text
authorization does not exist
```

## Temporal Conflict Types

```text
FUTURE_KNOWLEDGE
FUTURE_EVIDENCE
FUTURE_VERIFICATION
FUTURE_POLICY
FUTURE_AUTHORIZATION
FUTURE_EXECUTION
FUTURE_OUTCOME
RETROACTIVE_REVOCATION
POLICY_RETROACTIVITY
TIMESTAMP_SUBSTITUTION
CLOCK_SKEW
TEMPORAL_INVERSION
EVENT_OBSERVATION_CONFUSION
DELAYED_OBSERVATION
LATE_EVIDENCE
STALE_AUTHORITY
VERSION_TIME_INTERACTION
```

## Invariants (Experimentally Established)

> **AUTHORITY IS NOT ONLY PROVENANCE-DEPENDENT. AUTHORITY IS TEMPORALLY BOUNDED.**

> **THE FUTURE MAY CHANGE CURRENT AUTHORITY WITHOUT CHANGING THE PAST.**

> **AN EVENT'S OCCURRENCE DOES NOT IMPLY ITS KNOWABILITY.**

> **A CURRENT RECONSTRUCTION MUST NOT BECOME A RETROACTIVE RECONSTRUCTION.**

### Formal Temporal Laws

**Temporal Non-Interference**: Future artifacts cannot alter historical authority unless the protocol explicitly defines retroactive semantics.

**Historical Immutability**: Later state transitions cannot mutate previously valid historical states.

**Temporal Availability**: An artifact's event time does not imply that the artifact was available for authority derivation at that time.

**Temporal Provenance**: Historical authority requires provenance valid at the relevant temporal boundary.

**No Lookahead**: Historical decisions cannot depend on information unavailable at the decision boundary.

**Revocation Locality**: Revocation changes authority from its effective boundary forward unless explicit retroactivity is authorized.

**Historical/Current Separation**: Historical validity and current validity are independent predicates.

**Temporal Equivalence**: Two authority states are semantically equivalent only if their temporal validity and provenance semantics are equivalent.

**Temporal Convergence**: Distributed nodes with equivalent historical provenance must reconstruct equivalent historical authority, regardless of artifact delivery order.

## The Governing Principle

> **THE RUNTIME DOES NOT OWN AUTHORITY.**
>
> **THE NETWORK DOES NOT OWN AUTHORITY.**
>
> **CONSENSUS DOES NOT CREATE AUTHORITY.**
>
> **THE PRESENT DOES NOT REWRITE AUTHORITY.**
>
> **AUTHORITY IS A DERIVABLE PROPERTY OF PROVENANCE, POLICY, IDENTITY, AND EVIDENCE AT A SPECIFIC POINT IN HISTORY.**

## Attack Suite: 55 Attacks Across 40 Categories

| Category | Attacks | Detected |
|----------|---------|----------|
| Future Knowledge | 7 | 7 |
| Late Evidence | 3 | 3 |
| Revocation | 4 | 4 |
| Policy Evolution | 2 | 2 |
| Timestamp Manipulation | 4 | 4 |
| Event/Observation Confusion | 3 | 3 |
| Causal/Temporal Confusion | 1 | 1 |
| Historical/Current Substitution | 1 | 1 |
| Replay | 1 | 1 |
| Cross-Node Temporal Divergence | 1 | 1 |
| Stale Node Reconstruction | 1 | 1 |
| Post-Execution Evidence Leakage | 1 | 1 |
| Outcome Leakage | 1 | 1 |
| Backtest Leakage | 1 | 1 |
| Version/Time Interaction | 1 | 1 |
| Partition/Time Interaction | 1 | 1 |
| Crash/Time Interaction | 1 | 1 |
| Temporal Authority Cut-Set | 1 | 1 |
| Historical Reconstruction | 1 | 1 |
| Current Reconstruction | 1 | 1 |
| Retrospective Audit | 1 | 1 |
| No-Lookahead | 1 | 1 |
| Temporal Equivalence | 1 | 1 |
| Temporal Convergence | 1 | 1 |
| Immutable History | 1 | 1 |
| Counterfactual Reconstruction | 1 | 1 |
| Clock Manipulation | 1 | 1 |
| Sequence Inversion | 1 | 1 |
| Future-Dated Artifact | 1 | 1 |
| Expired Artifact | 1 | 1 |
| Temporal Conflict | 1 | 1 |
| Authority Time Travel | 1 | 1 |
| Evidence Time Travel | 1 | 1 |
| Governance Time Travel | 1 | 1 |
| Execution Time Travel | 1 | 1 |
| Revocation Time Travel | 1 | 1 |
| Policy Time Travel | 1 | 1 |
| Complete Scenario | 1 | 1 |

## The Ultimate Experiment

### Complete Scenario

```text
T0  Policy P1 becomes active
T1  Actor A receives delegation
T2  Strategy S proposed
T3  Evidence E generated
T4  Verification V completed
T5  Governance approves
T6  Authorization issued
T7  Trade executed
T8  Authorization revoked
T9  New evidence arrives
T10 Policy P2 replaces P1
T11 Original runtime is destroyed
T12 Distributed nodes reconstruct history
```

### Three Questions

**Question 1 — Historical**: Was the trade authorized at T7?
**Answer**: YES

**Question 2 — Current**: Is the authority still valid at T12?
**Answer**: NO

**Question 3 — Retrospective**: Given everything known by T12, was the T7 authorization supported by the protocol under the rules that existed at T7?
**Answer**: YES

These three answers are:
```text
YES
NO
YES
```

That is not a contradiction. That is the behavior we want.

## Test Count: 1494 Passing

| Phase | Tests Added | Total |
|-------|-------------|-------|
| Epistemic Adversarial | 21 | 922 |
| Epistemic Calibration | 19 | 941 |
| Evidence Accumulation | 50 | 991 |
| Epistemic Gaps | 33 | 1024 |
| Experiment Selection | 20 | 1044 |
| State Transitions | 32 | 1076 |
| Verification | 23 | 1099 |
| Consensus | 43 | 1142 |
| Governance | 48 | 1190 |
| Compositional Authority | 33 | 1223 |
| Authority Algebra | 30 | 1253 |
| Non-Interference | 31 | 1284 |
| Protocol Reconstruction | 37 | 1321 |
| Distributed Authority | 86 | 1407 |
| **Temporal Authority** | **87** | **1494** |

## The Complete Invariant Chain

```
MODEL OUTPUT ≠ EVIDENCE
EVIDENCE ≠ EPISTEMIC STATE
EPISTEMIC STATE ≠ VERIFICATION
VERIFICATION ≠ CONSENSUS
CONSENSUS ≠ GOVERNANCE
GOVERNANCE ≠ AUTHORIZATION
AUTHORIZATION ≠ EXECUTION
EXECUTION ≠ EVIDENCE OF AUTHORIZATION

VALID(A) + VALID(B) + VALID(C) ≠ necessarily VALID(A⊕B⊕C)

B ⟂ X ⇒ Decision(X, A) = Decision(X, A ⊕ B)

AUTHORITY IS RECONSTRUCTABLE FROM ITS PROVENANCE.

AUTHORITY IS A FUNCTION OF PROVENANCE, NOT LOCATION.

AUTHORITY DOES NOT INCREASE BECAUSE MORE NODES OBSERVE IT.

DISTRIBUTED AGREEMENT DOES NOT CREATE AUTHORITY.

PARTIAL KNOWLEDGE MUST PRODUCE BOUNDED UNCERTAINTY.

EQUIVALENT PROVENANCE MUST PRODUCE EQUIVALENT AUTHORITY.

INCOMPLETE PROVENANCE CANNOT BE COMPLETED BY CONSENSUS ALONE.

AUTHORITY IS NOT ONLY PROVENANCE-DEPENDENT. AUTHORITY IS TEMPORALLY BOUNDED.

THE FUTURE MAY CHANGE CURRENT AUTHORITY WITHOUT CHANGING THE PAST.

AN EVENT'S OCCURRENCE DOES NOT IMPLY ITS KNOWABILITY.

A CURRENT RECONSTRUCTION MUST NOT BECOME A RETROACTIVE RECONSTRUCTION.
```

## Limitations

1. **No real-time clocks**: Temporal positions are logical only
2. **No NTP/network time**: No actual clock synchronization
3. **No formal verification**: Testing-based only
4. **No Byzantine temporal attacks**: No malicious timestamp authorities
5. **No CRDTs/conflict resolution**: No automatic merge of conflicting histories
6. **No erasure coding**: Artifacts are whole
7. **No real distributed execution**: Simulation only
8. **No wall-clock performance benchmarks**: Correctness only

## What the System Can Now Do

All previous capabilities, plus:

1. **Historical reconstruction** — Reconstruct authority at any point in time
2. **Current reconstruction** — Reconstruct authority with all available information
3. **Retrospective audit** — Evaluate historical decisions without rewriting history
4. **Temporal non-interference** — Future artifacts cannot affect historical reconstruction
5. **Historical immutability** — Historical states cannot be mutated
6. **No-lookahead** — Historical decisions use only information available at the time
7. **Revocation locality** — Revocations affect only their effective boundary forward
8. **Policy evolution** — Policies are temporal objects with validity intervals
9. **Event/observation separation** — When something happened ≠ when it was known
10. **Temporal equivalence** — Semantic equivalence requires temporal equivalence
11. **Temporal convergence** — Distributed nodes converge on historical authority
12. **55 temporal attacks** — Comprehensive temporal adversarial testing
13. **Three-mode architecture** — Historical, current, and retrospective reconstruction
14. **Multi-dimensional time** — Event, observation, ingestion, verification, authorization, execution, revocation times
15. **Validity intervals** — Artifacts have explicit validity periods
