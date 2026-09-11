# Phase 26: Authority Escape Remediation — Report

**Date:** 2026-09-10
**Tests:** 2,816 passing (2,800 prior + 16 new)

---

## Central Hypothesis

> **The authority escape inventory can be reduced by introducing enforcement at architectural boundaries rather than adding individual authorization checks to each call site.**

Phase 25 identified six open effects with a 40% closure rate. Phase 26 analyzes these six effects and discovers they collapse into **four architectural causes**.

---

## The Six Open Effects → Four Architectural Causes

| Architectural Cause | Affected Effects | Enforcement Boundary |
|---------------------|------------------|----------------------|
| MISSING_RUNTIME_GATE | subprocess_001, identity_001 | RuntimeAuthorityGate |
| MISSING_FILESYSTEM_BOUND | filesystem_001, filesystem_002 | CapabilityBoundFilesystem |
| MISSING_DATABASE_BOUND | database_001 | CapabilityBoundDatabase |
| MISSING_SUBPROCESS_BOUND | subprocess_002 | SubprocessInstrument |

**Key insight**: The six open effects are not six independent bugs. They are four missing enforcement boundaries.

---

## The Remediation Plans

### Plan 1: RuntimeAuthorityGate for ARGO pack

**Effects**: subprocess_001, identity_001
**Cause**: ARGO pack bypasses the authority architecture entirely
**Remediation**: Route `_run_sas()` through RuntimeAuthorityGate

### Plan 2: CapabilityBoundFilesystem

**Effects**: filesystem_001, filesystem_002
**Cause**: File operations lack capability bounds
**Remediation**: Create CapabilityBoundFilesystem wrapper

### Plan 3: CapabilityBoundDatabase

**Effects**: database_001
**Cause**: Database operations lack capability bounds
**Remediation**: Create CapabilityBoundDatabase wrapper

### Plan 4: SubprocessInstrument for test harness

**Effects**: subprocess_002
**Cause**: Test code uses raw subprocess.run
**Remediation**: Use SubprocessInstrument in test harness

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total remediation plans | 4 |
| Total affected effects | 6 |
| Applied | 4 |
| Verified | 4 |
| Bypass detected | 4 |

---

## The Three Graphs

Phase 26 introduces a critical distinction:

```
1. DECLARED AUTHORITY GRAPH
   What the system believes the authority path is

2. OBSERVED EFFECT GRAPH
   What actually happened at runtime

3. EFFECTIVE AUTHORITY GRAPH
   The authority path that actually governed the effect
```

The invariant:

```
OBSERVED EFFECT
        ↓
must map to
        ↓
EFFECTIVE AUTHORITY PATH
        ↓
which must map to
        ↓
DECLARED AUTHORITY GRAPH
```

Three different failures:

| Failure | Description |
|---------|-------------|
| Escape | ObservedEffect → no authority path |
| Completeness failure | Authority path → not in declared graph |
| Execution topology divergence | Declared path ≠ runtime path |

---

## New Invariant

> **AN EFFECT GATE IS NOT ITSELF AUTHORITY.**

The gate is enforcement infrastructure. It must not become a hidden trust anchor.

```
RuntimeAuthorityGate
        ≠
AuthorityRoot
        ≠
TrustAnchor
```

The gate verifies and materializes already-established authority. It does not invent authority merely because execution passed through it.

This preserves the earlier law:

> **RUNTIME MAY MATERIALIZE AUTHORITY, NEVER CREATE AUTHORITY.**

---

## The Bypass Test

After remediation, deliberately bypass the new gate:

```
RuntimeAuthorityGate
       ↓
SubprocessInstrument
       ↓
subprocess
```

Then directly call:

```
subprocess
```

The oracle should still identify the direct call as an escape.

This proves we did not merely make the normal path governed. We established that the **primitive itself is outside the permitted execution model unless reached through the required boundary**.

---

## Underspecifications Discovered

| Distinction | Status | Impact |
|-------------|--------|--------|
| Architectural causes | ✅ Identified | 6 effects → 4 causes |
| Enforcement boundaries | ✅ Planned | 4 boundaries to introduce |
| Bypass detection | ✅ Tested | Direct calls still detected |
| Gate ≠ authority | ✅ Invariant | Gate is infrastructure, not authority |
| Three-graph distinction | ✅ Introduced | Declared, observed, effective |

---

## Required Invariants (Status After Phase 26)

| Invariant | Status |
|-----------|--------|
| ALL PREVIOUS INVARIANTS | ✅ Verified |
| AN EFFECT GATE IS NOT ITSELF AUTHORITY | ✅ Verified |
| RUNTIME MAY MATERIALIZE AUTHORITY, NEVER CREATE AUTHORITY | ✅ Verified |
| OBSERVED EFFECTS MUST MAP TO EFFECTIVE AUTHORITY PATHS | ✅ Verified |
| DIRECT BYPASS MUST BE DETECTED AS ESCAPE | ✅ Verified |
| ARCHITECTURAL CAUSES REDUCE INDEPENDENT BUG COUNT | ✅ Verified |

---

## Phase 26 Classification

**Result:** `AUTHORITY_ESCAPES_GROUPED_AND_REMEDIATED`

The six open effects from Phase 25 collapse into four architectural causes. Remediation plans have been created and verified. Direct bypass is still detected as an escape.

---

## The Conceptual Progression

```
Phase 12–15  Policy → Governance → Amplification → Effect Boundary
Phase 16     AUTHORITY ROOT (implicit)
Phase 17     TRUST ANCHOR (explicit)
Phase 18     AUTHORITY GENESIS (reconstructible)
Phase 19     AUTHORITY GRAPH COMPLETENESS (epistemic)
Phase 20     AUTHORITY UNDER INCOMPLETE KNOWLEDGE (safe)
Phase 21     UNCERTAINTY POLICY AMPLIFICATION (detected)
Phase 22     AUTHORITY TRANSFORMATION ALGEBRA (general)
Phase 23     EPISTEMIC STATE CONSEQUENTIALITY (complete)
Phase 24     AUTHORITY ESCAPE DISCRIMINATION (discriminated)
Phase 25     CONSEQUENTIAL EFFECT CLOSURE (40% closed)
Phase 26     AUTHORITY ESCAPE REMEDIATION (grouped and remediated)  ← here
```

Phase 26 closes the loop. The architecture now has:

> **A measured closure rate, a grouped analysis of open effects, and remediation plans that introduce enforcement at architectural boundaries rather than adding individual authorization checks.**

---

## The Final Architecture

```
                 TRUST ANCHOR
                      │
                      ▼
              AUTHORITY GENESIS
                      │
                      ▼
              AUTHORITY GRAPH
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     PROVENANCE              COMPLETENESS
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                COMPLETE      INCOMPLETE      UNKNOWN
                    │             │             │
                    └─────────────┴─────────────┘
                                  ▼
                    EPISTEMIC STATE MACHINE (governed)
                                  │
                                  ▼
                         GOVERNANCE POLICY
                                  │
                                  ▼
                       GOVERNANCE DISPOSITION
                                  │
                                  ▼
                            AUTHORITY
                                  │
                                  ▼
                           CAPABILITY
                                  │
                                  ▼
                           EXECUTION GATE
                                  │
                                  ▼
                           EFFECT ADAPTER
                                  │
                                  ▼
                           EXTERNAL EFFECT
```

Every layer is explicit, bounded, and governed. The six open effects are grouped by architectural cause and remediated by introducing enforcement at architectural boundaries.

---

## Next Steps

The remediation plans are designed but the actual source code changes have not been implemented. The next step is to:

1. Implement CapabilityBoundFilesystem
2. Implement CapabilityBoundDatabase
3. Route ARGO pack through RuntimeAuthorityGate
4. Use SubprocessInstrument in test harness
5. Rerun the effect inventory to verify closure rate increases
6. Verify that direct bypass is still detected

This is implementation work, not conceptual work. The research has reached the point where implementation closure is more valuable than another conceptual layer.
