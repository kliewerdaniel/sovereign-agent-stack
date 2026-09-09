# Authority Boundary Adjudication — Results

> **Date:** 2026-09-09
> **Phase:** Authority Boundary Adjudication
> **Tests:** 1,893 passing

---

## Executive Summary

The Authority Boundary Adjudication subsystem was implemented and tested against the Argopack subprocess path. The system successfully distinguished between four governance scenarios, producing correct classifications and governance dispositions for each.

---

## Scenarios Tested

### Scenario A: No Declaration

| Field | Value |
|-------|-------|
| Classification | LEGACY_UNGOVERNED |
| Governance Disposition | PENDING_REVIEW |
| Confidence | 0.7 |
| Authority Basis | UNKNOWN |

**Interpretation**: The boundary has runtime evidence but no authority declaration. This is a legacy practice requiring governance review. No automatic enforcement is triggered.

### Scenario B: Trust Declaration

| Field | Value |
|-------|-------|
| Classification | TRUSTED_SUBSYSTEM |
| Governance Disposition | CONSTRAINED |
| Confidence | 0.8 |
| Authority Basis | TRUST_DECLARATION |

**Interpretation**: ARGO is explicitly trusted to perform subprocess operations. The trust declaration provides authority basis, but the subsystem operates outside the canonical protocol. Constraints are applied.

### Scenario C: Delegation

| Field | Value |
|-------|-------|
| Classification | EXPLICIT_DELEGATION |
| Governance Disposition | DELEGATED |
| Confidence | 0.8 |
| Authority Basis | EXPLICIT_DELEGATION |

**Interpretation**: A governed actor delegates subprocess authority to ARGO. The delegation is explicit, bounded by scope, and active. Authority does not exceed the delegation scope.

### Scenario D: Prohibition

| Field | Value |
|-------|-------|
| Classification | UNAUTHORIZED_ESCAPE |
| Governance Disposition | PROHIBITED |
| Confidence | 0.75 |
| Authority Basis | NONE |

**Interpretation**: Governance policy explicitly prohibits ARGO from exercising subprocess authority. The boundary is an unauthorized escape.

---

## Adversarial Tests

| Test | Result |
|------|--------|
| Forged trust declaration | Detected (confidence < 0.8) |
| Expired delegation | Not active, not classified as delegation |
| Revoked delegation | Not active, not classified as delegation |
| Delegation exceeding scope | AUTHORITY_MISMATCH |
| Wrong authority owner | INCONCLUSIVE/LEGACY |
| Ambiguous authority intent | INCONCLUSIVE |
| Multiple competing owners | Unresolved questions generated |

---

## Invariant Verification

| Invariant | Status |
|-----------|--------|
| TRUST IS NOT AUTHORITY | ✅ Held |
| AMBIENT PRIVILEGE IS NOT PROTOCOL AUTHORITY | ✅ Held |
| OUTSIDE THE PROTOCOL IS NOT EQUIVALENT TO FORBIDDEN | ✅ Held |
| AUTHORITY INTENT MUST NOT BE INFERRED FROM EXECUTION | ✅ Held |
| DISCOVERY DOES NOT CREATE ENFORCEMENT AUTHORITY | ✅ Held |

---

## Key Findings

1. **The adjudicator correctly distinguishes between scenarios.** No declaration produces LEGACY_UNGOVERNED, trust produces TRUSTED_SUBSYSTEM, delegation produces EXPLICIT_DELEGATION, and prohibition produces UNAUTHORIZED_ESCAPE.

2. **Governance disposition is separate from classification.** Each classification maps to an appropriate governance disposition (PENDING_REVIEW, CONSTRAINED, DELEGATED, PROHIBITED).

3. **Adversarial cases are handled correctly.** Forged declarations, expired/revoked delegations, and scope mismatches are all detected.

4. **The system does not infer authority from execution.** Scenarios without declarations are classified as LEGACY_UNGOVERNED, not UNAUTHORIZED_ESCAPE.

5. **Trust is not protocol authority.** The trust scenario produces TRUSTED_SUBSYSTEM, not INTENTIONAL_PROTOCOL_AUTHORITY.

---

## Provenance Chain

Every adjudication preserves:
- Runtime observation IDs
- Static hypothesis IDs
- Reconciliation IDs
- Authority reconstruction IDs
- Declaration IDs
- Policy IDs
- Temporal context
- Limitations

---

## Limitations

1. **Declaration input**: The system relies on provided declarations. It does not discover declarations from source code.
2. **Policy evaluation**: Policy matching is string-based, not semantic.
3. **Single boundary**: Each adjudication addresses one boundary. Cross-boundary analysis is not yet implemented.
4. **No enforcement**: The system produces recommendations, not enforcement directives.

---

## Architecture

```
examples/self_audit/
├── authority_boundary.py        # Formal model (AuthorityBoundary, AuthorityOwner, etc.)
├── authority_adjudication.py    # Adjudication engine + Argopack scenarios
├── runtime_topology.py          # Static graph + runtime experiment
├── runtime_trace.py             # Instrumentation infrastructure
├── reconciliation.py            # Static-dynamic reconciliation
└── artifacts/
    ├── runtime_topology_report.json
    └── authority_boundary_report.json

tests/unit/
├── test_authority_boundary.py   # 48 tests
├── test_runtime_trace.py        # 23 tests
└── test_reconciliation.py       # 18 tests

docs/architecture/
├── AUTHORITY_BOUNDARY_MODEL.md
├── RUNTIME_TRACE_MODEL.md
└── STATIC_DYNAMIC_RECONCILIATION.md
```

---

## Conclusion

The Authority Boundary Adjudication subsystem successfully demonstrates that SAS can reason about authority boundaries once they are discovered. The system distinguishes between:

- **What authority exists** (protocol, delegated, trusted, ambient)
- **Who owns it** (governance, actor, subsystem)
- **Why it exists** (declaration, policy, historical practice)
- **What governance permits** (accepted, constrained, prohibited)

The Argopack finding is now properly contextualized:
- It IS an authority escape (epistemic fact)
- Whether it is acceptable depends on governance (policy decision)
- The system preserves this distinction

> **An authority escape is an epistemic fact before it is a policy violation.**
