# Consequential Authority Graph

> **Date:** 2026-09-09
> **Phase:** Sovereign Infrastructure Governance
> **Tests:** 1,946 passing

---

## Purpose

The Consequential Authority Graph integrates static topology, runtime behavior, consequence observation, epistemic evidence, authority reconstruction, boundary adjudication, and governance into a unified model.

**Central question:**
> WHAT ACTORS, COMPONENTS, PROCESSES, CREDENTIALS, SUBSYSTEMS, AND PROTOCOL PATHS CAN ACTUALLY CAUSE CONSEQUENCES IN A REAL SYSTEM, UNDER WHAT CONDITIONS, AND WITH WHAT RECONSTRUCTIBLE AUTHORITY?

**Central thesis:**
> The important property of a sovereign system is not that every action is controlled by a central authority. It is that every consequential action has an identifiable authority boundary whose provenance, scope, conditions, and governance can be independently reconstructed.

---

## The Consequential Authority Graph

### Edge Types (13, NOT collapsed)

| Edge Type | Meaning |
|-----------|---------|
| CALL | Structural invocation |
| DEPENDENCY | Static or runtime dependency |
| CONSEQUENCE | Causes external effect |
| AUTHORITY | Authorizes operation |
| DELEGATION | Explicit authority transfer |
| TRUST | Trust declaration |
| GOVERNANCE | Governance policy |
| CAPABILITY | Capability verification |
| PROVENANCE | Records lineage |
| TEMPORAL | Temporal constraint |
| ENVIRONMENT | Environment-specific |
| CREDENTIAL | Credential access |
| BOUNDARY | Authority boundary |

### Reachability Types (4, NOT interchangeable)

| Type | Meaning |
|------|---------|
| STATIC_REACHABILITY | Reachable in source code |
| RUNTIME_REACHABILITY | Actually executed |
| CONSEQUENTIAL_REACHABILITY | Can cause external effect |
| AUTHORIZED_REACHABILITY | Has protocol authorization |

Example: A subprocess may be statically reachable, runtime reachable, consequentially reachable, but NOT authoritatively reachable → authority boundary finding.

---

## The Payment Fixture

A deliberately adversarial payment infrastructure with:

### Components
checkout, payment_gateway, fraud_service, customer_profile, tax_service, ledger, settlement_service, notification_service, feature_flag_service, redis, message_queue, worker, deployment_hook, admin_service, external_payment_provider, legacy_processor, credential_store

### Adversarial Properties
- Production/staging divergence (feature flags differ)
- Environment-selected endpoints
- Feature-flag-controlled dependencies
- Retry behavior
- Timeout fallback
- Cached authorization data
- Asynchronous execution
- Background workers
- Subprocess execution
- Plugin execution
- Network calls
- Filesystem-based configuration
- Credential lookup
- Privileged administrative path
- Legacy path
- Failure-only path
- Deployment-only path
- Dead code
- Substitutable provider
- Circular dependency
- Shared infrastructure

### Deliberate Discrepancies
- DOCUMENTATION ≠ IMPLEMENTATION
- IMPLEMENTATION ≠ RUNTIME
- RUNTIME ≠ GOVERNANCE

---

## Authority Cut Sets

An authority cut set is a minimal set of boundaries whose control is sufficient to prevent a consequential path.

Example: `{payment_gateway, credential_provider, payment_provider_adapter}` may form a cut set for `charge_customer`.

The cut is evaluated in terms of: consequence, authority, capability, credential, runtime path, governance.

---

## Conditional Authority

Authority is evaluated under conditions:
- feature flag enabled
- production environment
- specific merchant
- specific operation
- retry count
- failure state
- credential availability
- deployment state
- actor identity
- time window
- authorization status
- provider availability

`AUTHORITY(A)` is NOT inferred when evidence only establishes `AUTHORITY(A | CONDITION)`.

---

## New Invariants

| Invariant | Meaning |
|-----------|---------|
| DEPENDENCY ≠ AUTHORITY | Dependency edge does not imply authority |
| REACHABILITY ≠ AUTHORITY | Reachability does not imply authorization |
| CONSEQUENCE ≠ AUTHORIZATION | External effect does not imply authorization |
| CREDENTIAL POSSESSION ≠ AUTHORIZATION | Having credentials ≠ authorization |
| RUNTIME EXECUTION ≠ GOVERNANCE APPROVAL | Running code ≠ governance approval |
| TRUST ≠ AUTHORITY | Trust declaration ≠ protocol authority |
| DECLARATION ≠ EXECUTION | Declaring authority ≠ executing |
| EXECUTION ≠ EFFECT | Execution ≠ external effect |
| EFFECT ≠ AUTHORITY | Effect ≠ authority |
| CONDITIONAL AUTHORITY MUST PRESERVE CONDITIONS | Conditional scope must be preserved |
| AUTHORITY COMPOSITION MUST NOT AMPLIFY | Composition does not increase authority |
| CURRENT AUTHORITY MUST NOT RETROACT | No retroactive authority changes |
| GRAPH INFERENCE MUST NOT CREATE AUTHORITY | Inference ≠ authority |
| AUTHORITY FINDINGS MUST NOT CREATE REMEDIATION | Findings ≠ enforcement |
| CONSEQUENTIALLY REACHABLE ≠ AUTHORITATIVELY REACHABLE | Reachability ≠ authorization |

---

## Architecture

```
examples/self_audit/
├── consequential_authority.py        # Core graph model + invariants
├── authority_boundary.py             # Boundary model + classifications
├── authority_adjudication.py         # Adjudication engine
├── runtime_topology.py               # Static + runtime experiment
├── runtime_trace.py                  # Instrumentation
├── reconciliation.py                 # Static-dynamic reconciliation
└── artifacts/
    ├── runtime_topology_report.json
    ├── escape_discrimination_report.json
    └── authority_boundary_report.json

examples/payment_dependency_auditor/
├── authority_fixture/
│   ├── fixture.py                    # Adversarial payment infrastructure
│   └── integration.py                # Dependency → Authority integration
├── dependency_types.py               # Dependency ontology
├── auditor.py                        # Dependency auditor
├── epistemic_composition.py          # Composition engine
└── hypothesis_generator.py           # Hypothesis generation

tests/unit/
├── test_consequential_authority.py   # 53 tests
├── test_authority_boundary.py        # 48 tests
├── test_runtime_trace.py             # 23 tests
└── test_reconciliation.py            # 18 tests

docs/architecture/
├── CONSEQUENTIAL_AUTHORITY_GRAPH.md
├── AUTHORITY_BOUNDARY_MODEL.md
├── RUNTIME_TRACE_MODEL.md
└── STATIC_DYNAMIC_RECONCILIATION.md
```

---

## Integration Points

The Consequential Authority Graph connects to:

| Existing System | Integration |
|----------------|-------------|
| Payment Dependency Auditor | Dependency observations become graph edges |
| Runtime Topology Experiment | Runtime observations become graph edges |
| Authority Boundary Adjudication | Boundary classifications become graph edges |
| Governance Policy Engine | Governance policies become graph edges |
| Credential Boundary System | Credential access becomes graph edges |
| Temporal Authority | Temporal scope becomes edge conditions |

---

## Key Distinctions Preserved

| Distinction | Status |
|-------------|--------|
| DEPENDENCY ≠ AUTHORITY | ✅ |
| REACHABILITY ≠ AUTHORITY | ✅ |
| CONSEQUENCE ≠ AUTHORIZATION | ✅ |
| CREDENTIAL ≠ AUTHORIZATION | ✅ |
| RUNTIME ≠ GOVERNANCE | ✅ |
| TRUST ≠ AUTHORITY | ✅ |
| CONDITIONAL SCOPE PRESERVED | ✅ |
| AUTHORITY NOT AMPLIFIED BY COMPOSITION | ✅ |
| NO RETROACTIVE AUTHORITY | ✅ |
| INFERENCE ≠ AUTHORITY | ✅ |
| FINDINGS ≠ ENFORCEMENT | ✅ |
| CONSEQUENTIALLY REACHABLE ≠ AUTHORITATIVELY REACHABLE | ✅ |
