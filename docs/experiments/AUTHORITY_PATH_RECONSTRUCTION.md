# Phase 31: Observed Effect → Authority Path Reconstruction

**Status:** Complete — 46 new tests, 3,072 total passing

## Central Research Question

> When a consequential effect is observed at runtime, can the system independently reconstruct the authority path that governed that effect, and distinguish valid authorization from missing or invalid authority evidence?

## The Four Fundamental Outcomes

```
OBSERVED EFFECT
      ↓
AUTHORITY PATH RESOLUTION
      ↓
 ┌───────────────┬────────────────┬─────────────────┐
 ↓               ↓                ↓                 ↓
VALID PATH    INVALID PATH    MISSING EVIDENCE   UNKNOWN
 ↓               ↓                ↓                 ↓
AUTHORIZED?    ESCAPE?         CANNOT DETERMINE  REVALIDATE
```

## The Critical Distinctions

```
OBSERVED ≠ AUTHORIZED
AUTHORIZATION_ID ≠ AUTHORITY_PROOF
CAPABILITY ≠ AUTHORITY
VALID_CAPABILITY ≠ VALID_AUTHORITY_DERIVATION
GOVERNANCE_DISPOSITION ≠ AUTHORITY
MISSING_EVIDENCE ≠ INVALID_AUTHORITY
NO_PATH_FOUND ≠ PATH_PROVEN_INVALID
VALID_PATH_WITHIN_INCOMPLETE_GRAPH ≠ GLOBAL_AUTHORITY_VALID
HISTORICALLY_VALID ≠ CURRENTLY_VALID
RECONSTRUCTION ≠ AUTHORITY_CREATION
```

## Architecture

```
TRUST ANCHOR
    ↓
AUTHORITY ORIGIN
    ↓
DELEGATION
    ↓
POLICY AUTHORITY
    ↓
POLICY EFFECT
    ↓
GOVERNANCE DISPOSITION
    ↓
AUTHORITY
    ↓
CAPABILITY
    ↓
EXECUTION GATE
    ↓
EFFECT
    ↓
RUNTIME OBSERVATION
    ↓
AUTHORITY PATH RECONSTRUCTION
    ↺
```

**The loop is now empirically testable.**

## The Twenty Adversarial Worlds

| # | World | Validity | Escape Type | Tests |
|---|-------|----------|-------------|-------|
| 01 | complete_valid_path | VALID | NO_ESCAPE | Full path reconstruction |
| 02 | valid_path_missing_provenance | INCOMPLETE | NO_ESCAPE | Missing evidence detection |
| 03 | valid_path_expired_temporal | INVALID | TEMPORAL_EXPIRED | Temporal authority |
| 04 | valid_path_wrong_scope | INVALID | DIRECT_PRIMITIVE_BYPASS | Scope mismatch |
| 05 | valid_path_wrong_actor | INVALID | DIRECT_PRIMITIVE_BYPASS | Actor mismatch |
| 06 | valid_capability_invalid_upstream | INVALID | DIRECT_PRIMITIVE_BYPASS | Invalid delegation |
| 07 | valid_governance_missing_authority | INVALID | GOVERNANCE_LAUNDERING | Governance laundering |
| 08 | valid_authority_missing_capability | INCOMPLETE | NO_ESCAPE | Missing capability |
| 09 | capability_not_from_authority | INVALID | CAPABILITY_LAUNDERING | Capability laundering |
| 10 | direct_primitive_bypass | INVALID | DIRECT_PRIMITIVE_BYPASS | No authority path |
| 11 | forged_authorization | INVALID | AUTHORIZATION_LAUNDERING | Auth ID laundering |
| 12 | replayed_receipt | INVALID | REPLAYED_RECEIPT | Replay attack |
| 13 | cross_domain_mismatch | INVALID | CROSS_DOMAIN_MISMATCH | Domain mismatch |
| 14 | undeclared_delegation | INVALID | UNDECLARED_DELEGATION | Undeclared delegation |
| 15 | cyclic_delegation | INVALID | CYCLIC_DELEGATION | Delegation cycle |
| 16 | unrecognized_anchor | INVALID | UNRECOGNIZED_ANCHOR | Bad trust anchor |
| 17 | emergency_execution | VALID | NO_ESCAPE | Alternate authority path |
| 18 | recovery_execution | VALID | NO_ESCAPE | Alternate authority path |
| 19 | background_incomplete_attribution | INCOMPLETE | NO_ESCAPE | Async attribution |
| 20 | no_authority_evidence | UNKNOWN | DIRECT_PRIMITIVE_BYPASS | No evidence at all |

## The ReconstructedAuthorityPath Object

The core epistemic object preserves:

```python
@dataclass(frozen=True)
class ReconstructedAuthorityPath:
    path_id: str
    observation_id: str
    effect_id: str
    validity: PathValidity
    nodes: tuple[AuthorityPathNode, ...]
    trust_anchor_id: str
    delegation_chain: tuple[str, ...]
    capability_status: CapabilityStatus
    governance_status: GovernanceStatus
    temporal_status: TemporalStatus
    scope_status: ScopeStatus
    attribution_status: AttributionStatus
    escape_type: EscapeType
    completeness_status: str
    provenance: str
    confidence: float  # NOT a probability
    notes: str
    metadata: dict[str, Any]
```

**Key design decisions:**

1. **Confidence is bounded < 1.0.** A reconstructed path never claims certainty.
2. **Validity is one of four values.** VALID, INVALID, INCOMPLETE, UNKNOWN are mutually exclusive.
3. **Escape type is distinct from validity.** An INVALID path may have different escape types.
4. **Capability/governance/temporal/scope status are separate.** Each dimension is tracked independently.
5. **Provenance is required.** Every reconstruction records its evidence basis.

## The PathReconstructionEngine

```python
class PathReconstructionEngine:
    """Reconstructs authority paths from runtime evidence.

    CRITICAL INVARIANTS:
        RECONSTRUCTION ≠ AUTHORITY_CREATION
        AUTHORITY_EVIDENCE ≠ AUTHORITY
        PATH_RECONSTRUCTION ≠ AUTHORITY_DELEGATION
        OBSERVATION ≠ AUTHORIZATION
    """
```

**Reconstruction process:**

1. **Check for trust anchor** — Is there evidence of the root authority?
2. **Check for delegation** — Is there a valid delegation chain?
3. **Check for policy** — Is there policy authority?
4. **Check for governance** — Is there governance disposition?
5. **Check for capability** — Is there a valid capability?
6. **Check for execution gate** — Was the execution gate passed?
7. **Check for invalidity indicators** — forged, cyclic, expired, scope mismatch, etc.
8. **Determine validity** — VALID, INVALID, INCOMPLETE, or UNKNOWN
9. **Determine escape type** — The specific type of authority failure

## The Independent Oracle

Evaluates reconstructed paths against ground truth:

```python
class IndependentOracle:
    """Evaluates reconstructed authority paths against ground truth.

    The oracle knows the true authority path but the reconstruction engine does not.
    """
```

**Evaluation outputs:**
- `validity_match`: Does reconstructed validity match ground truth?
- `escape_match`: Does reconstructed escape type match ground truth?
- `false_authorization`: Reconstructed as VALID but actually INVALID/ESCAPE?
- `false_escape`: Reconstructed as ESCAPE but actually VALID?
- `missing_evidence_correct`: Correctly identified as INCOMPLETE?

## Key Results

### 1. Valid Paths Are Reconstructed

World 01 (complete_valid_path) with all evidence present produces:
- `validity = VALID`
- `escape_type = NO_ESCAPE`
- `nodes` includes trust_anchor → delegation → policy → governance → capability → execution_gate → effect
- `completeness_status = complete_within_declared_graph`

### 2. Missing Evidence Is Correctly Identified

World 02 (valid_path_missing_provenance) produces:
- `validity = INCOMPLETE`
- `escape_type = NO_ESCAPE` (not an escape — just missing evidence)

**Critical:** The system does NOT classify missing evidence as INVALID.

### 3. Authorization Laundering Is Detected

World 11 (forged_authorization) produces:
- `validity = INVALID`
- `escape_type = AUTHORIZATION_LAUNDERING`

The system does NOT conclude VALID merely because `has_authorization_id = True`.

### 4. Capability Laundering Is Detected

World 09 (capability_not_from_authority) produces:
- `validity = INVALID`
- `escape_type = CAPABILITY_LAUNDERING`
- `capability_status = LAUNDERED`

The system does NOT conclude VALID merely because `has_capability_id = True`.

### 5. Governance Laundering Is Detected

World 07 (valid_governance_missing_authority) produces:
- `validity = INVALID`
- `escape_type = GOVERNANCE_LAUNDERING`
- `governance_status = DISPOSITION_WITHOUT_AUTHORITY`

The system does NOT conclude VALID merely because `has_governance_disposition = True`.

### 6. Temporal Authority Is Preserved

World 03 (valid_path_expired_temporal) produces:
- `validity = INVALID`
- `escape_type = TEMPORAL_EXPIRED`
- `temporal_status = EXPIRED`

The system distinguishes HISTORICALLY_VALID from CURRENTLY_VALID.

### 7. Emergency and Recovery Paths Are Valid

World 17 (emergency_execution) and World 18 (recovery_execution) produce:
- `validity = VALID`
- `escape_type = NO_ESCAPE`

The system does NOT classify alternate authority paths as escapes.

### 8. Async Attribution Is Correctly Unknown

World 19 (background_incomplete_attribution) produces:
- `attribution_status = CALLER_TO_WORKER_UNCONFIRMED`

The system does NOT infer `CALLER_AUTHORITY = WORKER_AUTHORITY`.

### 9. Direct Primitive Bypasses Are Detected

World 10 (direct_primitive_bypass) and World 20 (no_authority_evidence) produce:
- `validity = INVALID` / `UNKNOWN`
- `escape_type = DIRECT_PRIMITIVE_BYPASS`

The system correctly identifies effects with no authority path.

### 10. Cross-Domain Mismatch Is Detected

World 13 (cross_domain_mismatch) produces:
- `validity = INVALID`
- `escape_type = CROSS_DOMAIN_MISMATCH`
- `scope_status = CROSS_DOMAIN_BLOCKED`

### 11. Cyclic Delegations Are Detected

World 15 (cyclic_delegation) produces:
- `validity = INVALID`
- `escape_type = CYCLIC_DELEGATION`

### 12. Replayed Receipts Are Detected

World 12 (replayed_receipt) produces:
- `validity = INVALID`
- `escape_type = REPLAYED_RECEIPT`

## The Critical Invariants (All Verified)

| Invariant | Test | Status |
|-----------|------|--------|
| `OBSERVED ≠ AUTHORIZED` | `test_observed_not_authorized` | ✅ |
| `AUTHORIZATION_ID ≠ AUTHORITY_PROOF` | `test_authorization_id_not_authority_proof` | ✅ |
| `CAPABILITY ≠ AUTHORITY` | `test_capability_not_authority` | ✅ |
| `GOVERNANCE_DISPOSITION ≠ AUTHORITY` | `test_governance_disposition_not_authority` | ✅ |
| `MISSING_EVIDENCE ≠ INVALID_AUTHORITY` | `test_missing_evidence_not_invalid_authority` | ✅ |
| `NO_PATH_FOUND ≠ PATH_PROVEN_INVALID` | `test_no_path_found_not_path_proven_invalid` | ✅ |
| `VALID_PATH_WITHIN_INCOMPLETE_GRAPH ≠ GLOBAL_VALID` | `test_valid_path_within_incomplete_graph_not_global_valid` | ✅ |
| `HISTORICALLY_VALID ≠ CURRENTLY_VALID` | `test_historically_valid_not_currently_valid` | ✅ |
| `RECONSTRUCTION ≠ AUTHORITY_CREATION` | `test_reconstruction_not_authority_creation` | ✅ |
| `CALLER_AUTHORITY ≠ WORKER_AUTHORITY` | `test_caller_authority_not_worker_authority` | ✅ |
| `CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY` | `test_cross_domain_observation_not_cross_domain_authority` | ✅ |
| `REPLAYED_RECEIPT ≠ CURRENT_AUTHORIZATION` | `test_replayed_receipt_not_current_authorization` | ✅ |

## Classification

**AUTHORITY_PATH_RECONSTRUCTION_ESTABLISHED_WITHIN_SCOPE**

### What the system CAN do:
1. Reconstruct authority paths from runtime evidence
2. Distinguish valid paths from invalid paths
3. Identify specific escape types (laundering, temporal, cyclic, etc.)
4. Detect authorization/capability/governance laundering
5. Preserve temporal authority semantics
6. Handle emergency and recovery authority paths
7. Correctly attribute (or mark unknown) async execution
8. Refuse to claim authority from identifiers alone

### What the system CANNOT do:
1. Prove global authority graph completeness
2. Create authority through reconstruction
3. Invent attribution when evidence is unavailable
4. Distinguish "no effect" from "effect exists but undiscovered"

### What remains UNKNOWN:
1. Whether all authority paths can be reconstructed from runtime evidence
2. Whether the declared authority graph is complete
3. Whether attribution can be established for all async executions

## The Honest Result

The scientifically honest result is **not** "every observed effect is authorized." It is:

> **Runtime effects can be independently reconstructed into authority paths. The system can distinguish missing evidence from invalid authority, and detect laundering of authorization, capability, and governance. A valid path through an incomplete graph does not prove global authority validity.**

## The Three Graphs (Preserved from Phase 26)

```
DECLARED AUTHORITY GRAPH    ← What the system believes
OBSERVED EFFECT GRAPH       ← What actually happened
EFFECTIVE AUTHORITY GRAPH   ← The path that actually governed the effect
```

**The invariant:**
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

**Three different failures:**
| Failure | Description |
|---------|-------------|
| Escape | ObservedEffect → no authority path |
| Completeness failure | Authority path → not in declared graph |
| Execution topology divergence | Declared path ≠ runtime path |

## The Updated Authority Stack

```
TRUST ANCHOR
    ↓
AUTHORITY GRAPH
    ↓
AUTHORITY GRAPH COMPLETENESS
    ↓
EFFECT INVENTORY
    ↓
EFFECT GRAPH COMPLETENESS  ← Phase 27
    ↓
CONTINUOUS EFFECT RECONCILIATION  ← Phase 28
    ↓
EFFECT KNOWLEDGE GAP DISCOVERY  ← Phase 29
    ↓
RUNTIME EFFECT REVELATION  ← Phase 30
    ↓
AUTHORITY PATH RECONSTRUCTION  ← Phase 31
    ↓
EFFECT AUTHORITY CLOSURE
    ↓
GOVERNED EXECUTION
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `examples/sovereign_agent/authority_path_reconstruction.py` | ~1,400 | 20 worlds + engine + oracle |
| `tests/unit/test_authority_path_reconstruction.py` | ~600 | 46 tests |
| `docs/experiments/AUTHORITY_PATH_RECONSTRUCTION.md` | ~300 | Phase 31 report |

## Test Count

- **Before Phase 31:** 3,026
- **After Phase 31:** 3,072 (+46)

## The Full Conceptual Progression

```
Authority origin → Authority graph → Authority graph completeness
    → Authority under uncertainty → Authority transformation
    → Epistemic consequentiality → Runtime escape discrimination
    → Effect inventory → Effect remediation
    → Effect graph completeness → Continuous effect reconciliation
    → Effect knowledge gap discovery → Runtime effect revelation
    → Authority path reconstruction  ← Phase 31
```

## Next Boundary

The system can now:
1. Detect structural gaps (Phase 29)
2. Observe runtime executions (Phase 30)
3. Reconstruct authority paths (Phase 31)

The remaining question:

**Can the system close the loop between reconstructed authority paths and the declared authority graph?**

This would determine whether the authority architecture actually explains all observed effects — or whether there are observed effects that cannot be mapped to any authority path.

The governing principle remains:

> **AN OBSERVED EFFECT MUST NEVER BE TREATED AS AUTHORIZED MERELY BECAUSE AN AUTHORIZATION REFERENCE, CAPABILITY, GOVERNANCE DISPOSITION, OR APPARENT PATH EXISTS.**
>
> **AUTHORITY MUST BE RECONSTRUCTIBLE FROM PROVENANCE-BEARING AUTHORITY TRANSITIONS.**
