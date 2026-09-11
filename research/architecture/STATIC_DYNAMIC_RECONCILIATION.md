# Static-Dynamic Reconciliation

> **Date:** 2026-09-09
> **Phase:** Runtime Epistemology
> **Tests:** 1,845 passing

---

## Purpose

The static-dynamic reconciliation engine compares the **predicted authority topology** from static analysis against the **observed authority topology** from runtime traces. It classifies each edge into one of seven categories, preserving uncertainty when evidence is incomplete.

---

## The Reconciliation Problem

```
STATIC ANALYSIS                    RUNTIME TRACE
    │                                  │
    ▼                                  ▼
"argopack.py calls          "argopack.py called
 subprocess.run"             subprocess.run with
    │                        no capability check"
    │                                  │
    └────────────┬─────────────────────┘
                 │
                 ▼
        RECONCILIATION
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
STATIC_ONLY   AUTHORITY_    AUTHORITY_
              CONTROLLED    ESCAPE
```

---

## Reconciliation Classifications

| Classification | Meaning | Action Required |
|---------------|---------|-----------------|
| STATIC_ONLY | Predicted but not observed at runtime | May be dead code or untested |
| RUNTIME_ONLY | Observed but not predicted | Static analysis gap |
| STATIC_AND_RUNTIME | Predicted and observed | Validate authority |
| STATIC_FALSE_POSITIVE | Predicted but not actually consequential | Remove from analysis |
| RUNTIME_UNEXPECTED | Observed but not predicted | Investigate |
| AUTHORITY_CONTROLLED | Observed with reconstructible authority | None |
| AUTHORITY_ESCAPE | Observed without authority | Remediate |
| INCONCLUSIVE | Cannot be determined | More evidence needed |

---

## The Four Graphs

The reconciliation produces four distinct graphs that must NOT be collapsed:

### Call Graph
Who calls whom. Pure structural invocation.

```
A → B → C
```

### Consequence Graph
What causes external effects.

```
A → ExternalEffect
```

### Authority Graph
What authorizes what.

```
Authorization → Capability → Execution
```

### Provenance Graph
What records lineage.

```
Execution → Receipt → ProvenanceRecord
```

**Critical distinction:** `A calls B` does NOT imply `A authorized B`. `B executed` does NOT imply `B caused external effect`. `External effect occurred` does NOT imply `effect was authorized`.

---

## Authority Reconstruction

For every consequential runtime event, the system attempts to reconstruct:

```
SOVEREIGN_ROOT → POLICY → ACTOR → GOVERNANCE → AUTHORIZATION → CAPABILITY → EXECUTION → EFFECT → RECEIPT → PROVENANCE
```

Each link is marked present/missing. The overall state is:

| State | Meaning |
|-------|---------|
| AUTHORIZED_AND_RECONSTRUCTIBLE | All links present |
| AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE | Some links present |
| UNAUTHORIZED | No authority observed |
| NON_CONSEQUENTIAL | No external effect |
| INSUFFICIENT_TRACE | Cannot determine |
| UNKNOWN | Not yet analyzed |

---

## Experimental Results

### Static Graph
- 19 hypotheses generated
- 2 predicted AUTHORITY_ESCAPE
- 11 predicted STATIC_FALSE_POSITIVE
- 6 predicted INCONCLUSIVE

### Runtime Trace
- 2 events recorded (subprocess creation + completion)
- 0 capability verifications
- 0 authorization derivations
- 0 provenance records

### Reconciliation
- 1 AUTHORITY_ESCAPE (argopack subprocess)
- 7 STATIC_ONLY (not exercised)
- 11 STATIC_FALSE_POSITIVE (internal state management)

### Authority Reconstruction
- 1 reconstruction attempted
- State: UNAUTHORIZED
- Missing links: 7 of 10 (sovereign_root, policy, governance, authorization, capability, receipt, provenance)

---

## The Argopack Finding

The experiment confirmed that the argopack subprocess path is a **formal authority escape**:

```
STATIC:
  src/sas/argopack.py → subprocess.run(sys.executable, "-m", "sas")
  No capability verification
  No authorization derivation
  No provenance recording

RUNTIME:
  subprocess.run executed successfully
  No capability_id recorded
  No authorization_id recorded
  No provenance_id recorded

RECONCILIATION:
  Classification: AUTHORITY_ESCAPE
  Confidence: 0.75
  Epistemic state: UNAUTHORIZED
```

**Whether this is architecturally acceptable depends on ARGO's trust status.**

---

## Instrumentation Limitations

| Limitation | Impact |
|-----------|--------|
| Single-process scope | Cannot trace across process boundaries |
| Python-only | Cannot trace non-Python subprocesses |
| Synchronous only | Async execution may lose parent context |
| No secret recording | Credentials never in traces |
| Observation only | Traces don't prevent actions |

> **ABSENCE OF OBSERVATION ≠ OBSERVATION OF ABSENCE**

---

## Architecture

```
examples/self_audit/
├── runtime_topology.py      # Static graph + runtime experiment
├── runtime_trace.py         # Instrumentation infrastructure
├── reconciliation.py        # Reconciliation engine
└── artifacts/
    ├── runtime_topology_report.json
    └── escape_discrimination_report.json

tests/unit/
├── test_runtime_trace.py    # 23 tests
└── test_reconciliation.py   # 18 tests
```

---

## Key Invariants Verified

| Invariant | Verified |
|-----------|----------|
| STATIC PATH ≠ RUNTIME PATH | YES |
| RUNTIME PATH ≠ AUTHORIZED PATH | YES |
| AUTHORIZED PATH ≠ EXTERNAL EFFECT | YES |
| TRACE ≠ AUTHORIZATION | YES |
| TRACE INTEGRITY ≠ EPISTEMIC VALIDITY | YES |
| ABSENCE OF OBSERVATION ≠ OBSERVATION OF ABSENCE | YES |
| REACHABILITY ≠ EXECUTION | YES |
| EXECUTION ≠ CONSEQUENCE | YES |
| CONSEQUENCE ≠ AUTHORITY | YES |
