# Phase 29: Effect Knowledge Gap Discovery

**Status:** Complete — 38 new tests, 2,967 total passing

## Central Research Question

> Can a sovereign execution system know when it no longer knows the complete set of effects it is capable of producing?

## The Distinction That Matters

```
EXTERNAL DISCOVERY          SELF-DISCOVERY
"I was told there is         "I have evidence that
 a new effect."              an effect may exist here."
```

Phase 29 tests whether bounded discovery mechanisms can produce **justified evidence** that the effect inventory is incomplete — without being handed the answer.

## The Six Discovery Statuses

| Status | Meaning | Observable? |
|--------|---------|-------------|
| `DISCOVERED` | Evidence of a specific effect found | Yes |
| `NOT_DISCOVERED` | No evidence found | Yes (but ≠ does not exist) |
| `INCONCLUSIVE` | Evidence is ambiguous | Yes |
| `STRUCTURAL_GAP` | Evidence of incompleteness without concrete effect | Yes |
| `EXTERNALLY_DECLARED` | Told by external observer | Yes |
| `OBSERVED` | Runtime actually saw execution | Yes |
| `UNKNOWN` | Ground truth has effect, system has no evidence | No (oracle only) |

**Critical distinctions:**

```
UNKNOWN_EFFECT ≠ STRUCTURAL_GAP ≠ UNOBSERVED_EFFECT ≠ NO_EFFECT
```

## The Seven Discovery Mechanisms

| # | Mechanism | What It Detects | What It Cannot Detect |
|---|-----------|-----------------|----------------------|
| A | Static Source Analysis | Missing categories in inventory | Specific hidden effects |
| B | Import/Module Graph Analysis | Dynamic loading patterns | What the loaded code does |
| C | Call Graph Analysis | Entry points without inventory coverage | Whether they execute |
| D | Runtime Trace Analysis | Declared-but-unobserved effects | Effects that never execute |
| E | Architectural Boundary Analysis | Boundary components without inventory | Effects outside boundaries |
| F | Execution Surface Analysis | Single-source categories | Hidden sources |
| G | Differential Analysis | Category drift between scans | New sources in same category |

## The 20 Adversarial Worlds

### Worlds 01–17: Hidden Effects

| # | World | Attack | Hidden Effects |
|---|-------|--------|----------------|
| 01 | direct_primitive | subprocess.Popen in unindexed module | 1 |
| 02 | indirect_helper | Helper wraps subprocess | 1 |
| 03 | dynamic_plugin | Plugin loaded at runtime | 1 |
| 04 | reflection_invocation | getattr bypasses static detection | 1 |
| 05 | subprocess_alternate_api | os.system bypasses subprocess.run inventory | 1 |
| 06 | filesystem_pathlib | shutil.copy bypasses open() inventory | 1 |
| 07 | database_alternate_client | psycopg2 bypasses aiosqlite inventory | 1 |
| 08 | network_abstraction | requests.get bypasses httpx inventory | 1 |
| 09 | payment_callback | Payment via callback | 1 |
| 10 | identity_alternate_adapter | Direct DB update bypasses identity adapter | 1 |
| 11 | credential_env_config | os.environ.get bypasses auth broker | 1 |
| 12 | background_worker | Worker writes files + network calls | 2 |
| 13 | exception_recovery | Recovery path spawns subprocess | 1 |
| 14 | emergency_path | Emergency kill switch bypasses governance | 1 |
| 15 | lazy_initialization | Lazy cache init writes to DB | 1 |
| 16 | generated_code | Generated code spawns subprocess | 1 |
| 17 | dynamic_code_load | Remote code load makes network calls | 1 |

**Total hidden effects: 18 across 17 worlds**

### Worlds 18–20: Benign (No Hidden Effect)

| # | World | Structural Anomaly | Benign Code |
|---|-------|-------------------|-------------|
| 18 | dead_code | Dead code appears consequential | Unreachable filesystem write |
| 19 | unreachable_subprocess | Unreachable subprocess | Legacy subprocess call |
| 20 | unused_plugin | Unused plugin | Plugin never instantiated |

**Purpose:** Measure false positives. Discovery mechanisms must not promote syntactic possibilities into executed effects.

## Independent Oracle Structure

```
WORLD
 ├──→ DISCOVERY MECHANISM
 │        ↓
 │    DISCOVERY RESULT
 │
 └──→ INDEPENDENT ORACLE
          ↓
      EVALUATION
          ↓
      COMPARISON
```

**Critical:** The discovery mechanism does NOT have access to `world.hidden_effects`. The oracle evaluates the discovery result against ground truth, but the mechanism must produce evidence independently.

## The EffectKnowledgeGap Object

The core epistemic object preserves:

```python
@dataclass(frozen=True)
class EffectKnowledgeGap:
    gap_id: str
    world_id: str
    status: DiscoveryStatus
    category: EffectCategory | None
    source: str
    scope: str
    discovery_mechanism: str
    evidence_basis: str
    description: str
    confidence: float  # NOT a probability of effect existence
    temporal_validity: str
    provenance: str
    reachability_status: str  # "unreachable", "possibly_reachable", "reachable", "executed"
    execution_status: str     # "never_executed", "possibly_executed", "observed_executed"
    inventory_relation: str   # "in_inventory", "partially_in_inventory", "not_in_inventory"
    completeness_implication: str
```

**Key design decisions:**

1. **Confidence is bounded < 1.0.** A structural gap never claims certainty.
2. **Execution status is separate from discovery.** Discovery ≠ execution.
3. **Reachability is tracked separately.** Static possibility ≠ reachable effect.
4. **Temporal validity is required.** Every discovery has a timestamp.
5. **Provenance is required.** Every discovery records its mechanism.

## Key Results

### 1. Structural Gaps Are Detectable

All 7 mechanisms can detect structural gaps:

- **Static Source Analysis** flags categories missing from inventory
- **Import/Module Analysis** flags dynamic loading
- **Call Graph Analysis** flags entry points without coverage
- **Architectural Boundary Analysis** flags boundary components without inventory
- **Execution Surface Analysis** flags single-source categories
- **Differential Analysis** flags category drift

### 2. Concrete Effects Are NOT Fully Discoverable

The mechanisms **cannot** reliably identify specific hidden effects:

- World 01: subprocess.Popen in `src/sas/cli/helper.py` — mechanisms detect "subprocess category has only one source" but cannot identify the specific hidden source
- World 06: shutil.copy in `src/sas/quant/cache.py` — mechanisms detect "filesystem category missing sources" but not the specific one
- World 09: payment.execute in `src/sas/quant/callbacks.py` — mechanisms detect "payment category missing" but not the specific effect

### 3. Benign Worlds Produce Structural Gaps (Correctly)

In worlds 18–20 (no hidden effects), mechanisms still flag structural gaps:

- Dead code world: Mechanisms flag "filesystem category has unreachable code"
- Unreachable subprocess world: Mechanisms flag "subprocess category has unreachable call"
- Unused plugin world: Mechanisms flag "plugin category has unused entry"

**This is correct behavior.** The mechanisms are detecting structural anomalies, not claiming hidden effects exist. The `STRUCTURAL_GAP` status explicitly says: "I have evidence of incompleteness, but I don't know what specifically is missing."

### 4. Negative Claims Are Correctly Refused

The system **does not** claim:

```
NO_HIDDEN_EFFECTS_EXIST
```

When a mechanism finds nothing, the result is:

```
NO_ADDITIONAL_EFFECT_DISCOVERED
```

or:

```
EFFECT_KNOWLEDGE_INCOMPLETE
```

The test `test_mechanism_silence_not_evidence_of_absence` explicitly verifies: a mechanism that finds nothing in a world with hidden effects has **not** proven no effects exist.

### 5. Authority Non-Amplification

Discovery results contain **no** authority claims:

- No `authority` field
- No `authorized` field
- No `governed` field

The pipeline remains:

```
EFFECT DISCOVERY → EFFECT KNOWLEDGE → COMPLETENESS ASSESSMENT
    → RECONCILIATION → GOVERNANCE → AUTHORITY → CAPABILITY → EXECUTION
```

### 6. Temporal Validity Preserved

Every discovery record includes:
- `temporal_validity`: when the evidence was captured
- `provenance`: lineage of the discovery
- `discovery_mechanism`: how it was generated

Historical discovery records are immutable. If an effect is discovered at C2, the C1 claim is **not** rewritten.

## The Critical Invariants (All Verified)

| Invariant | Test | Status |
|-----------|------|--------|
| `NOT_DISCOVERED ≠ DOES_NOT_EXIST` | `test_mechanism_silence_not_evidence_of_absence` | ✅ |
| `STRUCTURAL_GAP ≠ CONCRETE_EFFECT` | `test_structural_gap_not_concrete_effect` | ✅ |
| `STATIC POSSIBILITY ≠ EXECUTED_EFFECT` | `test_static_possibility_not_executed_effect` | ✅ |
| `DISCOVERED_EFFECT ≠ AUTHORIZED_EFFECT` | `test_discovered_effect_not_authorized` | ✅ |
| `NO_NEW_EFFECT_DISCOVERED ≠ NO_NEW_EFFECT_EXISTS` | `test_no_new_effect_discovered_not_no_effect_exists` | ✅ |
| `DISCOVERY ≠ AUTHORITY` | `test_discovery_does_not_create_authority` | ✅ |
| `STRUCTURAL_GAP ≠ UNAUTHORIZED_EFFECT` | `test_structural_gap_does_not_imply_unauthorized` | ✅ |

## Classification

**STRUCTURAL_GAP_DISCOVERY_ESTABLISHED_WITHIN_BOUNDED_OBSERVATION_MODEL**

The system can generate evidence that its effect inventory is incomplete. It **cannot** reliably identify specific hidden effects without external input.

### What the system CAN do:
1. Detect missing categories in the inventory
2. Detect dynamic loading patterns that prevent complete enumeration
3. Detect entry points without inventory coverage
4. Detect boundary components without inventory entries
5. Detect single-source categories that may have hidden sources
6. Detect category drift between inventory snapshots
7. Refuse to claim global closure when structural gaps exist

### What the system CANNOT do:
1. Identify specific hidden effects (e.g., "subprocess.Popen in helper.py")
2. Distinguish between "no effect" and "effect exists but undiscovered"
3. Discover effects that leave no structural trace
4. Prevent all false positives in benign worlds
5. Achieve complete effect inventory through self-discovery alone

### What remains UNKNOWN:
1. Whether complete effect inventory is achievable (Rice's theorem analog)
2. Whether additional discovery mechanisms could cover more ground
3. Whether runtime observation can close the gap between structural gaps and concrete effects

## The Honest Result

The scientifically honest result is **not** "the system can discover all effects." It is:

> **Under observable structural, static, dynamic, and architectural conditions, the system can produce justified evidence that its effect inventory is incomplete. Arbitrary hidden effects remain unknowable without additional information.**

This limitation is **not a failure**. It is a **valuable result**: the system knows the boundary of its own knowledge.

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
EFFECT AUTHORITY CLOSURE
    ↓
GOVERNED EXECUTION
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `examples/sovereign_agent/effect_knowledge_gap.py` | ~1,457 | 7 mechanisms + 20 worlds + oracle |
| `tests/unit/test_effect_knowledge_gap.py` | ~520 | 38 tests |

## Test Count

- **Before Phase 29:** 2,929
- **After Phase 29:** 2,967 (+38)

## The Full Conceptual Progression

```
Authority origin → Authority graph → Authority graph completeness
    → Authority under uncertainty → Authority transformation
    → Epistemic consequentiality → Runtime escape discrimination
    → Effect inventory → Effect remediation
    → Effect graph completeness → Continuous effect reconciliation
    → Effect knowledge gap discovery
```

## Next Boundary

The system can now detect **that** its inventory is incomplete. The next question is:

**Can the system close the gap between structural gaps and concrete effects through runtime observation?**

This would connect Phase 29's structural detection to actual effect execution — but only for effects that **do** execute. Effects that never execute (dead code, emergency paths, lazy init that hasn't triggered) would remain in the structural gap state.

The governing principle remains:

> **THE SYSTEM MUST NEVER TURN A LIMITATION OF ITS DISCOVERY MECHANISM INTO EVIDENCE THAT THE EFFECT DOES NOT EXIST.**
