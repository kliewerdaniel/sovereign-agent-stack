# Authority Boundary Model

> **Date:** 2026-09-09
> **Phase:** Authority Boundary Adjudication
> **Tests:** 1,893 passing

---

## Purpose

The Authority Boundary Model provides the formal framework for adjudicating authority boundaries discovered through runtime topology experiments. It answers not just "Is there an escape?" but "What authority exists here, who owns it, why does it exist, and is it acceptable?"

---

## Central Principle

> **DISCOVERY OF AN AUTHORITY ESCAPE IS AN EPISTEMIC RESULT. WHETHER THAT ESCAPE IS ACCEPTABLE IS A GOVERNANCE DECISION.**

---

## New Invariants

| Invariant | Meaning |
|-----------|---------|
| TRUST IS NOT AUTHORITY | A trust declaration does not create protocol authority |
| AMBIENT PRIVILEGE IS NOT PROTOCOL AUTHORITY | OS-level capability ≠ protocol authorization |
| OUTSIDE THE PROTOCOL IS NOT EQUIVALENT TO FORBIDDEN | Non-protocol boundaries may be intentionally permitted |
| AUTHORITY INTENT MUST NOT BE INFERRED FROM EXECUTION BEHAVIOR ALONE | Running code does not imply authority intent |
| DISCOVERY OF AN AUTHORITY ESCAPE DOES NOT CREATE AUTHORITY TO ENFORCE ITS REMEDIATION | Findings ≠ enforcement authority |
| GOVERNANCE DECISIONS MUST BE PROVENANCE-BACKED | Every governance action needs reconstructible provenance |

---

## Authority Types

### Protocol Authority
Authority derived through the canonical chain:
`SOVEREIGN_ROOT → POLICY → ACTOR → GOVERNANCE → AUTHORIZATION → CAPABILITY → EXECUTION`

### Ambient Process Privilege
OS-level capability without protocol participation. The process can do it because the OS allows it, not because the protocol authorizes it.

### Trusted Subsystem Authority
Explicit trust declaration outside the protocol. A governance decision to trust a subsystem without requiring full protocol participation.

### Delegated Authority
Explicitly bounded authority transfer from one actor to another. Must have scope, constraints, and temporal bounds.

---

## Boundary Classifications

| Classification | Meaning |
|---------------|---------|
| INTENTIONAL_PROTOCOL_AUTHORITY | Authority derived through canonical chain |
| EXPLICIT_DELEGATION | Authority explicitly delegated with scope |
| TRUSTED_SUBSYSTEM | Trusted by governance, outside protocol |
| LEGACY_UNGOVERNED | Historical practice, no authority declaration |
| UNAUTHORIZED_ESCAPE | No authority basis, explicitly prohibited |
| AUTHORITY_MISMATCH | Delegation scope mismatch |
| RECONSTRUCTION_FAILURE | Authority cannot be reconstructed |
| INCONCLUSIVE | Cannot be determined |

---

## Governance Dispositions

| Disposition | Meaning |
|------------|---------|
| ACCEPTED | Boundary is permitted |
| REJECTED | Boundary is not permitted |
| DELEGATED | Authority explicitly delegated |
| CONSTRAINED | Permitted with constraints |
| PROHIBITED | Explicitly forbidden |
| PENDING_REVIEW | Requires governance review |
| LEGACY_TOLERATED | Historical, tolerated but not accepted |
| INCONCLUSIVE | Cannot be determined |

---

## The Authority Boundary Graph

The boundary graph describes semantic boundaries:

```
DOMAIN → ACTOR → CONSEQUENCE → AUTHORITY OWNER → AUTHORITY BASIS → DELEGATION → POLICY → TEMPORAL SCOPE → RECONSTRUCTION REQUIREMENT → GOVERNANCE DISPOSITION
```

This is distinct from:
- **Call Graph**: Who calls whom
- **Consequence Graph**: What causes external effects
- **Authority Graph**: What authorizes what
- **Provenance Graph**: What records lineage

---

## Separation of Concerns

```
FINDING → RECOMMENDATION → GOVERNANCE → AUTHORIZATION → ENFORCEMENT
```

The system does NOT allow:
- FINDING → ENFORCEMENT (skips governance)
- RECOMMENDATION → AUTHORIZATION (recommendation is not authority)
- TRUST DECLARATION → PROTOCOL AUTHORITY (trust is not authority)

---

## The Argopack Scenarios

### Scenario A: No Declaration
- **Classification**: LEGACY_UNGOVERNED
- **Governance**: PENDING_REVIEW
- **Meaning**: Historical practice without authority declaration

### Scenario B: Trust Declaration
- **Classification**: TRUSTED_SUBSYSTEM
- **Governance**: CONSTRAINED
- **Meaning**: Explicitly trusted but outside protocol

### Scenario C: Delegation
- **Classification**: EXPLICIT_DELEGATION
- **Governance**: DELEGATED
- **Meaning**: Explicitly bounded authority transfer

### Scenario D: Prohibition
- **Classification**: UNAUTHORIZED_ESCAPE
- **Governance**: PROHIBITED
- **Meaning**: Explicitly forbidden by governance

---

## Adversarial Tests

The model was tested against:

| Test | Result |
|------|--------|
| Forged trust declaration | Detected (low confidence) |
| Expired delegation | Not active |
| Revoked delegation | Not active |
| Delegation exceeding scope | AUTHORITY_MISMATCH |
| Wrong authority owner | INCONCLUSIVE/LEGACY |
| Ambiguous authority intent | INCONCLUSIVE |
| Multiple competing owners | Unresolved questions |

---

## Architecture

```
examples/self_audit/
├── authority_boundary.py        # Formal model
├── authority_adjudication.py    # Adjudication engine
├── runtime_topology.py          # Static + runtime experiment
├── runtime_trace.py             # Instrumentation
├── reconciliation.py            # Static-dynamic reconciliation
└── artifacts/
    ├── runtime_topology_report.json
    └── authority_boundary_report.json

tests/unit/
├── test_authority_boundary.py   # 48 tests
├── test_runtime_trace.py        # 23 tests
└── test_reconciliation.py       # 18 tests
```

---

## Key Distinctions

### Protocol Authority vs Ambient Authority
The system must never infer:
- `process privilege → protocol authority`
- `trusted subsystem → protocol authority`
- `delegation → unrestricted authority`

### Trust vs Authority
A subsystem may be trusted by governance while still operating outside the canonical authority protocol. This produces `TRUSTED_BUT_OUTSIDE_PROTOCOL`, not `UNAUTHORIZED`.

### Outside Protocol vs Forbidden
Governance must determine whether a non-protocol boundary is permitted. The system does not automatically classify outside-protocol as forbidden.

---

## Relationship to Prior Work

| Prior Layer | New Layer |
|-------------|-----------|
| Static hypothesis | Boundary classification |
| Runtime observation | Authority reconstruction |
| Reconciliation | Governance disposition |
| Epistemic state | Policy interpretation |

The architecture now supports:

```
STATIC ANALYSIS → HYPOTHESIS → RUNTIME EXPERIMENT → OBSERVATION → RECONCILIATION → EPISTEMIC STATE → AUTHORITY RECONSTRUCTION → BOUNDARY ADJUDICATION → GOVERNANCE → AUTHORIZATION → CAPABILITY → EXECUTION
```
