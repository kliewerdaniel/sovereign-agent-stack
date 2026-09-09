# Consequence Model

> **Status:** Initial Audit
> **Last Updated:** 2026-09-09
> **Phase:** Consequence Boundary Unification

This document defines the consequence model for the Sovereign Agent Stack. The model classifies every operation into one of four categories, each with different authority requirements.

---

## Core Principle

> **CONSEQUENTIALITY IS A PROTOCOL PROPERTY, NOT A SUBSYSTEM PROPERTY.**

A trade, payment, credential access, identity mutation, process execution, filesystem mutation, network request, tool invocation, or compute operation may have completely different implementation semantics, but they must share the same authority derivation semantics.

---

## Classification

### 1. INFORMATIONAL

**Definition:** No persistent or external effect. Read-only operations that do not change state or affect anything outside the immediate reasoning process.

**Authority Requirement:** None (read-only access may be controlled separately)

**Examples:**
- Sovereignty score calculation
- Read-only knowledge graph queries
- Analysis and report generation
- Status checks
- Provenance inspection
- Audit trail reading
- Configuration reading

**Properties:**
- Idempotent
- No side effects
- Safe to repeat
- Does not change system state

### 2. STATE-TRANSFORMING

**Definition:** Changes local protocol state. Persistent effects that stay within the system's internal state.

**Authority Requirement:** Authorization required, but scope is internal

**Examples:**
- Append provenance record
- Update knowledge graph
- Store evidence
- Record execution receipt
- Update session memory
- Log audit entry
- Cache computation result

**Properties:**
- Persistent effect
- Internal only
- Reconstructible from provenance
- Does not affect external systems

### 3. EXTERNAL-CONSEQUENTIAL

**Definition:** Can affect something outside the immediate reasoning process. Operations that cross the system boundary.

**Authority Requirement:** Full authorization + capability + verification + receipt + provenance

**Examples:**
- Broker order submission
- Payment transaction
- Email sending
- SMS sending
- API mutation
- Container execution
- Filesystem mutation
- Subprocess execution
- Network write
- Identity provisioning
- Credential use

**Properties:**
- Irreversible or expensive to reverse
- External visibility
- Financial, legal, or security implications
- Requires strongest authority guarantees

### 4. AUTHORITY-MANAGEMENT

**Definition:** Changes who/what may perform future actions. Operations that modify the authority graph itself.

**Authority Requirement:** HIGHEST — must itself be authorized, must not be self-authorizing

**Examples:**
- Creating AuthorizationArtifact
- Delegation
- Revocation
- Credential registration
- Plugin registration
- Policy mutation
- Identity creation
- Capability issuance
- Authority registry mutation

**Properties:**
- Meta-level: changes the rules
- Must not be able to authorize itself
- Must prevent circular delegation
- Must prevent privilege amplification
- Must be reconstructible

---

## Critical Invariant

> **AUTHORITY-MANAGEMENT OPERATIONS MUST THEMSELVES BE AUTHORIZED.**

A system must not gain authority merely by modifying the data structure that describes authority.

This means:
- Creating an `AuthorizationArtifact` requires authorization
- Registering a credential requires authorization
- Registering a plugin requires authorization
- Mutating policy requires authorization
- Delegating authority requires authorization

---

## Consequence Execution Contract

Every consequential operation (state-transforming, external-consequential, or authority-management) must satisfy:

### Request (`ConsequentialRequest`)

| Field | Description |
|-------|-------------|
| `domain` | The protocol domain |
| `lineage` | The lineage identifier |
| `actor` | The principal performing the action |
| `action` | The action being performed |
| `resource` | The resource being targeted |
| `requested_effect` | Description of the intended effect |
| `temporal_constraints` | When the operation is valid |
| `policy_context` | The governing policy |
| `authorization_reference` | Reference to parent authorization |
| `capability_reference` | Reference to materialized capability |
| `executor_identity` | The executor performing the operation |

### Response (`ExecutionReceipt`)

| Field | Description |
|-------|-------------|
| `receipt_id` | Unique identifier |
| `capability_ref` | The capability that was verified |
| `authorization_ref` | The authorization that was resolved |
| `domain_id` | The domain of execution |
| `lineage_id` | The lineage of execution |
| `actor_id` | The actor who performed the action |
| `executor_id` | The executor that performed the action |
| `resource_id` | The resource that was affected |
| `action` | The action that was performed |
| `arguments_hash` | Hash of the arguments |
| `start_time` | When execution started |
| `completion_time` | When execution completed |
| `effect_summary` | Summary of the effect |
| `result_hash` | Hash of the result |
| `external_reference` | External identifier (e.g., broker order ID) |
| `status` | Execution status |
| `intended_effect` | What was intended |
| `observed_effect` | What was observed |
| `reported_result` | What the executor reported |
| `provenance_hash` | Hash of provenance |

---

## Authority Requirements by Classification

| Classification | Authorization | Capability | Verification | Receipt | Provenance |
|----------------|---------------|------------|--------------|---------|------------|
| Informational | ✗ | ✗ | ✗ | ✗ | ✗ |
| State-transforming | ✓ | ✓ | ✓ | ✓ | ✓ |
| External-consequential | ✓ | ✓ | ✓ | ✓ | ✓ |
| Authority-management | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |

---

## Examples by Subsystem

### Quant

| Operation | Classification |
|-----------|----------------|
| Run backtest | Informational |
| Compute statistics | Informational |
| Submit order | External-consequential |
| Register strategy | State-transforming |

### Agent Runtime

| Operation | Classification |
|-----------|----------------|
| Register tool | Authority-management |
| Invoke tool | External-consequential |
| Create session | State-transforming |
| Recall memory | Informational |

### Auth Broker

| Operation | Classification |
|-----------|----------------|
| Register credential | Authority-management |
| Get credential | External-consequential |
| Use credential in API call | External-consequential |
| Audit trail | Informational |

### Payments

| Operation | Classification |
|-----------|----------------|
| Pay for resource | External-consequential |
| Set spending limit | Authority-management |
| Get balance | Informational |

### Identity

| Operation | Classification |
|-----------|----------------|
| Provision email | External-consequential |
| Provision phone | External-consequential |
| Send email | External-consequential |
| Send SMS | External-consequential |

### Substrate

| Operation | Classification |
|-----------|----------------|
| Boot container | External-consequential |
| Execute command | External-consequential |
| Destroy container | External-consequential |
| List machines | Informational |

### CLI

| Operation | Classification |
|-----------|----------------|
| Any consequential command | External-consequential |
| Any authority-management command | Authority-management |
| Informational commands | Informational |

### Plugins

| Operation | Classification |
|-----------|----------------|
| Register plugin | Authority-management |
| Invoke plugin operation | External-consequential |
| Discover plugins | Informational |

---

## The Key Question

For every operation in SAS, ask:

> **WHAT EFFECT CAN THIS OPERATION CAUSE?**

Then classify it. Then apply the appropriate authority requirements.

Do not assume that only financial operations are consequential.

Reading a credential may be consequential.

Sending an email is consequential.

Provisioning an identity is consequential.

Starting a container may be consequential.

Executing a shell command is consequential.

Writing to a persistent knowledge store may be state-transforming.

Registering a plugin may be authority-management.

Revoking authority is itself consequential.
