# Execution Capability and Authority Materialization

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
CAPABILITY MATERIALIZATION
 ↓
EXECUTION CONTEXT
 ↓
EXECUTOR
 ↓
EXECUTION RECEIPT
 ↓
EXTERNAL OBSERVATION
 ↓
VERIFIED EFFECT
 ↓
PROVENANCE
 ↓
RECONSTRUCTION
 ↓
DISTRIBUTED RECONSTRUCTION
 ↓
TEMPORAL RECONSTRUCTION
 ↓
PROTOCOL LINEAGE
 ↓
SOVEREIGN AUTHORITY DOMAINS
 ↓
EXECUTION CAPABILITY
 ↓
CONDITIONAL CONVERGENCE
```

## Central Research Question

> **Once the protocol has derived an AuthorizationArtifact, how does that authority become a bounded runtime capability without allowing the execution environment to acquire authority that was never explicitly derived?**

## The Problem

The architecture had proven:

```text
Given authorization A
        ↓
verify A is valid
        ↓
execute action
```

But there was a missing boundary:

```text
Authorization A
        ↓
Runtime R executes A
        ↓
R has ambient authority beyond A
        ↓
A's bounds are not enforced at execution
```

The runtime could silently acquire authority never explicitly derived.

## Key Distinctions

```text
AUTHORIZATION ≠ CAPABILITY

CAPABILITY ≠ EXECUTION

EXECUTION ≠ EFFECT

EXECUTOR PRIVILEGE ≠ CALLER AUTHORITY
```

## Capability Model

### ExecutionCapability

A materialized capability derived from authorization:

```text
capability_id
authorization_ref
scope (CapabilityScope)
capability_type (execute, read, write, delete, delegate, revoke, observe, verify)
replay_guard (ReplayGuard)
actor_identity_ref
resource_binding (ExecutorBinding)
domain_id
lineage_id
authority_root
provenance_root
derived_at
derived_by
derivation_proof
attenuation_chain
```

### CapabilityScope

Explicit scope of the capability:

```text
domain_id
lineage_id
actor_id
action
resource
resource_class
arguments
constraints (CapabilityConstraints)
temporal_interval (DomainValidityInterval)
delegation_chain
authorization_ref
provenance_ref
nonce
expiration
```

### CapabilityConstraints

Structural guarantees on capability usage:

```text
attenuation_type (scope_narrowing, resource_restriction, temporal_shortening, quantity_reduction)
attenuation_factor (0-1)
allowed_actions
forbidden_actions
max_quantity
min_quantity
allowed_arguments
forbidden_arguments
composition_permitted
delegation_permitted
transfer_permitted
```

### ReplayGuard

Prevents capability replay:

```text
guard_type (nonce, sequence, timestamp, single_use, bounded_use)
nonce
sequence
previous_nonce
max_uses
current_uses
created_at
```

### ExecutorBinding

Binds capability to specific executor and resource:

```text
binding_id
executor_id
resource_id
bound_resources
resource_handles
binding_type (exclusive, shared, ephemeral, persistent)
bound_at
bound_until
binding_proof
binding_verified
verification_ref
```

### ExecutionReceipt

Immutable record of what actually happened:

```text
receipt_id
capability_ref
authorization_ref
domain_id
lineage_id
actor_id
executor_id
resource_id
action
arguments_hash
start_time
completion_time
effect_summary
result_hash
external_reference
status (pending, executing, completed, failed, partial, revoked, expired, replayed, rejected)
intended_effect
observed_effect
reported_result
provenance_hash
```

## Authority Non-Amplification

The fundamental law:

```text
Capability(authority) ⊆ Authorization(authority)
```

And more generally:

```text
EffectiveExecutionAuthority
    ⊆
CapabilityAuthority
    ⊆
AuthorizationAuthority
    ⊆
GovernanceAuthority
```

No lower layer may increase the authority of a higher layer.

## Capability Attenuation

A stronger capability can produce a weaker capability:

```text
Capability:
    execute_trade
    quantity <= 100

    ↓ attenuate

Capability:
    execute_trade
    quantity <= 10
```

But never:

```text
    quantity <= 1000
```

Attenuation is structurally guaranteed:

```text
Authority(attenuate(C))
    ⊆
Authority(C)
```

## Replay Protection

Each capability carries a replay guard:

- **Single-use**: Can be executed exactly once
- **Bounded-use**: Can be executed up to N times
- **Sequence**: Must be executed in order
- **Timestamp**: Valid only within temporal window
- **Nonce**: Unique per capability instance

A valid capability must not automatically become infinitely reusable.

## Execution Receipts

Separate three distinct concepts:

```text
INTENDED EFFECT
    ≠
OBSERVED EFFECT
    ≠
REPORTED RESULT
```

A model-generated statement such as:

```text
"trade executed"
```

must never be treated as evidence that the trade executed.

The receipt establishes:

1. **Intended effect**: What the capability authorized
2. **Observed effect**: What the external system observed
3. **Reported result**: What the executor claimed

Divergence between these three is explicitly detected.

## Domain Integration

Every capability is bound to:

```text
domain_id
lineage_id
authority_root
identity_root
policy_root
provenance_root
```

A capability from domain A must not become executable in domain B merely because B understands its schema.

## Attack Suite: 8 Attacks, 100% Detection

| Category | Attacks | Detected |
|----------|---------|----------|
| Capability widening | 1 | 1 |
| Actor substitution | 1 | 1 |
| Resource substitution | 1 | 1 |
| Temporal extension | 1 | 1 |
| Replay | 1 | 1 |
| Attenuation increase | 1 | 1 |
| Domain substitution | 1 | 1 |
| Executor privilege escalation | 1 | 1 |

### Attack Descriptions

1. **Capability widening**: Attempt to widen capability scope beyond authorization
2. **Actor substitution**: Attempt to substitute actor in capability
3. **Resource substitution**: Attempt to substitute resource (broker:A → broker:B)
4. **Temporal extension**: Attempt to use capability after expiration
5. **Replay**: Attempt to replay a single-use capability
6. **Attenuation increase**: Attempt to increase authority through attenuation
7. **Domain substitution**: Attempt to use capability in wrong domain
8. **Executor privilege escalation**: Attempt to escalate privileges through executor

## Experimental Findings

### 1. Capability Scope Is Enforced

A capability with `action="execute_trade"` cannot be used for `read_data`. The scope is structurally bound.

### 2. Actor Substitution Is Detected

An authorization for `actor-1` cannot be materialized into a capability for `actor-2`. The identity binding is verified.

### 3. Resource Substitution Is Detected

A capability for `broker:A` cannot be used against `broker:B`. Resource identity is part of execution authority.

### 4. Temporal Extension Is Detected

A capability with `valid_until="2024-12-31T23:59:59Z"` cannot be used at `2025-01-01T00:00:00Z`. Temporal validity binds capability use.

### 5. Replay Is Detected

A single-use capability cannot be executed twice. The replay guard enforces this structurally.

### 6. Attenuation Increase Is Rejected

An attenuation factor > 1.0 is rejected. Authority cannot be increased through attenuation.

### 7. Domain Substitution Is Detected

A capability from `domain-a` is not compatible with `domain-b`. Domain binding is structural.

### 8. Executor Privilege Escalation Is Prevented

The capability scope is narrow and does not inherit executor privileges. Composition is disabled by default.

## New Architectural Laws (Experimentally Demonstrated)

> **AUTHORIZATION DOES NOT IMPLY CAPABILITY.**

> **CAPABILITY DOES NOT IMPLY EXECUTION.**

> **EXECUTION DOES NOT IMPLY EFFECT.**

> **EXECUTOR PRIVILEGE DOES NOT BECOME CALLER AUTHORITY.**

> **CAPABILITY AUTHORITY CANNOT EXCEED AUTHORIZATION AUTHORITY.**

> **RESOURCE IDENTITY IS PART OF EXECUTION AUTHORITY.**

> **TEMPORAL VALIDITY BINDS CAPABILITY USE.**

> **REVOCATION CHANGES CURRENT AUTHORITY WITHOUT REWRITING HISTORICAL EXECUTION.**

> **EXECUTION CLAIMS ARE NOT EXECUTION EVIDENCE.**

> **EXECUTION RECEIPTS ARE DERIVED ARTIFACTS, NOT AUTHORITY ROOTS.**

> **NO UNDECLARED EXECUTION INTERFERENCE.**

> **CAPABILITY TRANSFER DOES NOT IMPLY AUTHORITY TRANSFER.**

> **CAPABILITY COMPOSITION DOES NOT AUTOMATICALLY PRODUCE COMPOSITE AUTHORITY.**

> **CAPABILITY ATTENUATION MUST NEVER INCREASE AUTHORITY.**

> **AMBIENT PROCESS PRIVILEGE IS NOT PROTOCOL AUTHORITY.**

> **EXECUTION AUTHORITY MUST BE RECONSTRUCTABLE FROM PERSISTED PROVENANCE.**

> **EXTERNAL EFFECT MUST BE DISTINGUISHED FROM EXECUTOR ASSERTION.**

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

VALID ARTIFACT ≠ VALID ARTIFACT FOR THIS PROTOCOL.

VALID PROVENANCE ≠ VALID PROVENANCE FOR THIS AUTHORITY DOMAIN.

SAME SCHEMA ≠ SAME SOVEREIGN DOMAIN.

SAME DOMAIN ≠ SAME PROTOCOL LINEAGE.

AUTHORITY IS NOT A PROPERTY OF THE ARTIFACT ALONE.

AUTHORITY IS A PROPERTY OF AN ARTIFACT'S PROVENANCE WITHIN
A SPECIFIC SOVEREIGN PROTOCOL DOMAIN, LINEAGE, TEMPORAL
BOUNDARY, AND DELEGATION CONTEXT.

AUTHORIZATION DOES NOT IMPLY CAPABILITY.

CAPABILITY DOES NOT IMPLY EXECUTION.

EXECUTION DOES NOT IMPLY EFFECT.

EXECUTOR PRIVILEGE DOES NOT BECOME CALLER AUTHORITY.

CAPABILITY AUTHORITY CANNOT EXCEED AUTHORIZATION AUTHORITY.

RESOURCE IDENTITY IS PART OF EXECUTION AUTHORITY.

TEMPORAL VALIDITY BINDS CAPABILITY USE.

EXECUTION CLAIMS ARE NOT EXECUTION EVIDENCE.

CAPABILITY ATTENUATION MUST NEVER INCREASE AUTHORITY.

AMBIENT PROCESS PRIVILEGE IS NOT PROTOCOL AUTHORITY.
```

## Test Count: 1,635 Passing

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
| Temporal Authority | 87 | 1494 |
| Protocol Lineage | 89 | 1583 |
| **Execution Capability** | **52** | **1635** |

## The Governing Principle

> **AUTHORITY MUST SURVIVE MATERIALIZATION.**

And the stronger version:

> **THE RUNTIME MAY MATERIALIZE AUTHORITY, BUT IT MUST NEVER CREATE AUTHORITY.**

## Limitations

1. **No real-time clocks**: Temporal positions are logical only
2. **No NTP/network time**: No actual clock synchronization
3. **No formal verification**: Testing-based only
4. **No Byzantine temporal attacks**: No malicious timestamp authorities
5. **No CRDTs/conflict resolution**: No automatic merge of conflicting histories
6. **No erasure coding**: Artifacts are whole
7. **No real distributed execution**: Simulation only
8. **No wall-clock performance benchmarks**: Correctness only
9. **No cryptographic signatures**: Hash-based integrity only
10. **No PKI/certificate authorities**: Root-based trust only
11. **No hardware-backed TPM**: Capability binding is logical only
12. **No OS-level enforcement**: Capabilities are protocol-level only

## What the System Can Now Do

All previous capabilities, plus:

1. **Capability materialization** — Derive bounded capabilities from authorizations
2. **Capability scope enforcement** — Explicit scope prevents silent widening
3. **Actor binding** — Capabilities are bound to specific actors
4. **Resource binding** — Capabilities are bound to specific resources
5. **Domain binding** — Capabilities are bound to specific domains
6. **Lineage binding** — Capabilities are bound to specific lineages
7. **Replay protection** — Single-use, bounded-use, sequence, timestamp guards
8. **Attenuation** — Capabilities can be narrowed but never widened
9. **Execution receipts** — Immutable records of what actually happened
10. **Effect verification** — Distinguish intended/observed/reported effects
11. **Divergence detection** — Detect when execution diverges from authorization
12. **Non-amplification** — Structural guarantee: Capability ⊆ Authorization
13. **8 execution attacks** — Comprehensive execution adversarial testing
14. **Full materialization flow** — Authorization → Capability → Execution → Receipt
15. **Attenuation chains** — Multiple attenuations without authority increase

## The Answer to the Research Question

> **Can an independently reconstructed authorization be materialized into a capability, executed by an untrusted or over-privileged runtime, and independently reconstructed afterward without allowing the runtime to create, widen, transfer, or fabricate authority?**

**Yes**, with the following caveats:

1. **Materialization is bounded**: The CapabilityMaterializer structurally guarantees Capability ⊆ Authorization
2. **Execution is bounded**: The capability scope is explicit and enforced
3. **Replay is prevented**: ReplayGuard ensures single-use/bounded-use semantics
4. **Attenuation is safe**: Attenuation can only narrow, never widen
5. **Receipts are immutable**: ExecutionReceipt records what actually happened
6. **Divergence is detected**: Intended vs observed vs reported effects are distinguished
7. **Domain binding is structural**: Capabilities cannot cross domains without explicit bridges
8. **Actor binding is structural**: Capabilities cannot be transferred to different actors
9. **Resource binding is structural**: Capabilities are bound to specific resource identities
10. **Temporal binding is structural**: Capabilities expire and cannot be used after expiration

The runtime may materialize authority, but it cannot create authority.
