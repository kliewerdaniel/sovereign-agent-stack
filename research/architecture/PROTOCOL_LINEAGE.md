# Protocol Lineage and Sovereign Domain Integrity

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
PROTOCOL LINEAGE
 ↓
SOVEREIGN AUTHORITY DOMAINS
 ↓
EXPLICIT INTER-DOMAIN DELEGATION
 ↓
CONDITIONAL CONVERGENCE
```

## Central Research Question

> **How does the protocol establish that a collection of individually valid artifacts belongs to the same authority universe and protocol lineage?**

## The Problem

The architecture had proven:

```text
Given provenance P
        ↓
reconstruct authority
```

But there was a deeper possibility:

```text
Protocol A
   ↓
artifacts
   ↓
Protocol B reconstructs them
```

What prevents a valid artifact from one sovereign domain from being composed with valid artifacts from another domain?

## Key Distinctions

```text
VALID ARTIFACT
        ≠
VALID ARTIFACT FOR THIS PROTOCOL

VALID PROVENANCE
        ≠
VALID PROVENANCE FOR THIS AUTHORITY DOMAIN

SAME SCHEMA
        ≠
SAME SOVEREIGN DOMAIN

SAME DOMAIN
        ≠
SAME PROTOCOL LINEAGE
```

## Domain Model

### ProtocolDomain

A sovereign authority universe with:

```text
domain_id
domain_root
protocol_family
protocol_version
schema_version
semantic_version
authority_root
identity_root
policy_root
provenance_root
parent_domain_id
lineage_hash
```

### ProtocolLineage

Tracks the history of a protocol:

```text
lineage_id
domain_id
parent_lineage_id
fork_point
lineage_type (original, fork, bridge, merge, divergent)
compatibility
divergence_point
```

### DomainBridge

Explicit cross-domain delegation:

```text
bridge_id
source_domain_id
destination_domain_id
scope (allowed_actions, allowed_resources, allowed_actors)
validity_interval
policy
authority_root
delegation_chain
status (active, revoked, expired, pending, future)
```

### AuthorityRoot

The ultimate source of authority derivation:

```text
root_id
domain_id
root_type (authority, identity, policy, provenance)
root_hash
established_at
expires_at
```

## Domain-Bound Artifacts

Every authoritative artifact carries explicit domain binding:

```text
Artifact
    ↓
artifact_id
domain_id
protocol_lineage_id
schema_version
semantic_version
authority_root
provenance_root
```

An artifact must not become authoritative merely because its internal structure is valid. It must also be valid **within the authority domain in which it is being used**.

## Domain Verification

### ProtocolLineageVerifier

Verifies:

1. **Artifact domain binding** — Does this artifact belong to this domain?
2. **Bridge validity** — Is the bridge active and within temporal bounds?
3. **Cross-domain composition** — Can artifacts from different domains be composed?
4. **Lineage continuity** — Is the lineage continuous and valid?
5. **Circular bridge detection** — Are there circular bridge chains?

### Verification Rules

- Domain ID must match
- Authority root must match
- Provenance root must match
- Protocol lineage must belong to the same domain
- Multiple domains require an explicit bridge
- Multiple authority roots require an explicit bridge
- Circular bridges are detected and rejected

## Domain Attack Suite: 39 Attacks, 100% Detection

| Category | Attacks | Detected |
|----------|---------|----------|
| Cross-domain | 17 | 17 |
| Root substitution | 4 | 4 |
| Collision | 4 | 4 |
| Bridge scope | 1 | 1 |
| Bridge temporal | 1 | 1 |
| Bridge resource | 1 | 1 |
| Bridge actor | 1 | 1 |
| Bridge policy | 1 | 1 |
| Bridge replay | 1 | 1 |
| Bridge revoked | 1 | 1 |
| Bridge expired | 1 | 1 |
| Bridge future | 1 | 1 |
| Bridge historical | 1 | 1 |
| Bridge nested | 1 | 1 |
| Bridge circular | 1 | 1 |
| Fork | 2 | 2 |

### Cross-Domain Attacks

1. Cross-domain evidence
2. Cross-domain proposition
3. Cross-domain actor
4. Cross-domain policy
5. Cross-domain delegation
6. Cross-domain consensus
7. Cross-domain majority
8. Cross-domain artifact replay
9. Cross-domain provenance substitution
10. Cross-domain temporal replay
11. Cross-domain crash recovery
12. Cross-domain distributed convergence
13. Cross-domain verification
14. Cross-domain governance
15. Cross-domain authorization
16. Cross-domain execution
17. Cross-domain revocation

### Root Substitution Attacks

1. Authority root substitution
2. Identity root substitution
3. Policy root substitution
4. Provenance root substitution

### Collision Attacks

1. Schema collision
2. Semantic collision
3. Version collision
4. Lineage collision

### Bridge Attacks

1. Bridge scope escalation
2. Bridge temporal escalation
3. Bridge resource escalation
4. Bridge actor substitution
5. Bridge policy substitution
6. Bridge replay
7. Revoked bridge
8. Expired bridge
9. Future bridge
10. Historical bridge
11. Nested bridges
12. Circular bridges

### Fork Attacks

1. Protocol fork
2. Domain fork

## Experimental Findings

### 1. Individual Validity Does Not Cross Authority Domains

At T10, evidence with `domain_id="domain-b"` is correctly rejected by domain A's verifier. The reconstruction produces `is_valid=False` — it does not have authority to accept artifacts from other domains.

### 2. Schema Collision Is Detected

Two artifacts with identical schemas but different `domain_id` are correctly distinguished. Same representation does not establish same authority.

### 3. Semantic Collision Is Detected

Artifacts with identical bytes but different semantic contexts (different `authority_root`) are correctly distinguished. Byte identity does not establish semantic identity.

### 4. Bridge Scope Is Enforced

A bridge with `scope={"allowed_actions": ["read_evidence"]}` correctly rejects `execute_trade`. Scope narrowing is preserved.

### 5. Bridge Temporal Validity Is Enforced

A bridge with `valid_until="2024-12-31T23:59:59Z"` correctly rejects access at `2025-01-01T00:00:00Z`. Temporal widening is prevented.

### 6. Revoked Bridges Are Inactive

A bridge with `status=REVOKED` is correctly rejected at any timestamp. Revocation is immediate and complete.

### 7. Circular Bridges Are Detected

Bridge A → Bridge B → Bridge A is correctly detected as circular and rejected.

### 8. Protocol Forks Preserve Lineage Without Preserving Authority

A fork has its own `lineage_hash` and `authority_root`. The fork is not compatible with the original, but the lineage relationship is preserved.

### 9. Domain Independence Is Established

Two sovereign domains with different roots cannot compose without an explicit bridge. Each domain can independently validate its own authority.

### 10. Bridge Non-Amplification Holds

A bridge with `scope={"allowed_actions": ["read_evidence"]}` cannot be used to authorize `execute_trade`. The bridge cannot amplify the authority it transports.

## New Architectural Laws (Experimentally Demonstrated)

> **AN AUTHORITATIVE ARTIFACT IS VALID ONLY WITHIN AN EXPLICITLY COMPATIBLE AUTHORITY DOMAIN.**

> **EVERY AUTHORITY DERIVATION TERMINATES AT AN AUTHORIZED ROOT WITHIN THE CORRECT DOMAIN.**

> **PROTOCOL LINEAGE MUST BE ESTABLISHED INDEPENDENTLY OF ARTIFACT SCHEMA COMPATIBILITY.**

> **ARTIFACTS FROM UNRELATED AUTHORITY DOMAINS CANNOT ALTER AUTHORITY UNLESS AN EXPLICIT BRIDGE ESTABLISHES A DEPENDENCY.**

> **A CROSS-DOMAIN BRIDGE CANNOT GRANT MORE AUTHORITY THAN ITS SOURCE SCOPE AND EXPLICIT DELEGATION PERMIT.**

> **A SOVEREIGN DOMAIN DOES NOT REQUIRE EXTERNAL CONSENSUS TO ESTABLISH INTERNALLY VALID AUTHORITY.**

> **BYTE IDENTITY, SCHEMA IDENTITY, SEMANTIC IDENTITY, LINEAGE IDENTITY, AND AUTHORITY IDENTITY ARE DISTINCT PROPERTIES.**

> **CROSS-DOMAIN AUTHORITY IS VALID ONLY WITHIN THE TEMPORAL INTERVAL OF THE BRIDGE AND DELEGATED AUTHORITY.**

> **CROSS-DOMAIN AUTHORITY REQUIRES COMPLETE PROVENANCE THROUGH EVERY BRIDGE TRAVERSED.**

> **DISTRIBUTED NODES CONVERGE ONLY WHEN THEIR DOMAIN, LINEAGE, PROVENANCE, TEMPORAL STATE, AND AUTHORITY ROOTS ARE SEMANTICALLY COMPATIBLE.**

> **OBSERVATION BY AN EXTERNAL DOMAIN DOES NOT CREATE AUTHORITY WITHIN THE OBSERVED DOMAIN.**

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
```

## Test Count: 1,583 Passing

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
| **Protocol Lineage** | **89** | **1583** |

## The Governing Principle

> **AUTHORITY IS NOT A PROPERTY OF THE ARTIFACT ALONE.**
>
> **AUTHORITY IS A PROPERTY OF AN ARTIFACT'S PROVENANCE WITHIN A SPECIFIC SOVEREIGN PROTOCOL DOMAIN, LINEAGE, TEMPORAL BOUNDARY, AND DELEGATION CONTEXT.**

Or more compactly:

> **VALIDITY IS LOCAL. INTEROPERABILITY IS EXPLICIT. AUTHORITY DOES NOT CROSS A SOVEREIGN BOUNDARY WITHOUT A DERIVABLE DELEGATION.**

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

## What the System Can Now Do

All previous capabilities, plus:

1. **Domain binding** — Every artifact carries explicit domain metadata
2. **Domain verification** — Verify artifacts belong to the expected domain
3. **Lineage tracking** — Track protocol forks, bridges, and divergences
4. **Bridge enforcement** — Cross-domain composition requires explicit bridges
5. **Bridge scope** — Bridges enforce action, resource, and actor restrictions
6. **Bridge temporal validity** — Bridges have explicit validity intervals
7. **Bridge revocation** — Revoked bridges are immediately inactive
8. **Circular bridge detection** — Circular bridge chains are detected and rejected
9. **Root substitution detection** — Substituting authority/identity/policy/provenance roots is detected
10. **Schema collision detection** — Same schema ≠ same domain
11. **Semantic collision detection** — Same bytes ≠ same semantics
12. **Domain independence** — Sovereign domains can independently validate authority
13. **Bridge non-amplification** — Bridges cannot grant more authority than delegated
14. **39 domain attacks** — Comprehensive domain adversarial testing
15. **Multi-domain architecture** — Support for sovereign, federated, bridged, and forked domains
