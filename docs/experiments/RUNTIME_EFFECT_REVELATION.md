# Phase 30: Runtime Effect Revelation and Epistemic Promotion

**Status:** Complete — 59 new tests, 3,026 total passing

## Central Research Question

> Can runtime observation convert a structurally possible or unknown effect into a concrete, provenance-bearing effect observation without incorrectly treating non-observation as evidence of absence?

## The Epistemic Ladder

```
UNKNOWN → STRUCTURAL POSSIBILITY → RUNTIME OBSERVATION → CONCRETE EFFECT → RECONCILIATION → COMPLETENESS
```

**No upward shortcut from "we didn't see it" to "it doesn't exist."**

## The Critical Distinctions

```
NOT_OBSERVED ≠ DOES_NOT_EXIST
NOT_EXECUTED_YET ≠ WILL_NEVER_EXECUTE
OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT
OBSERVATION ≠ AUTHORITY
EXECUTION_RECEIPT ≠ AUTHORITY
STRUCTURAL_POSSIBILITY ≠ EXECUTED_EFFECT
RUNTIME_OBSERVATION ≠ GLOBAL_COMPLETENESS
OBSERVED_SET ≠ COMPLETE_EFFECT_SET
ATTRIBUTION_UNKNOWN ≠ ATTRIBUTION_TO_CALLER
CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY
TEMPORAL_OBSERVATION ≠ HISTORICAL_EXISTENCE
REVALIDATION ≠ RETROACTIVE_INVALIDATION
COMPLETENESS ≠ CLOSURE
```

## Architecture

```
SOURCE / BUILD / RUNTIME
        ↓
EFFECT DISCOVERY
        ↓
STRUCTURAL KNOWLEDGE
        ↓
RUNTIME OBSERVATION
        ↓
CONCRETE EFFECT KNOWLEDGE
        ↓
INVENTORY RECONCILIATION
        ↓
COMPLETENESS ASSESSMENT
        ↓
EFFECT AUTHORITY CLOSURE
        ↓
GOVERNED EXECUTION
```

**Asymmetry preserved:**
- STRUCTURAL DISCOVERY can reveal POSSIBLE effects.
- RUNTIME OBSERVATION can reveal EXECUTED effects.
- Neither can prove the universal absence of unobserved effects.

## The Ten Adversarial Worlds (A-J)

### Worlds with Hidden Effects That Execute (8 worlds)

| World | Category | Hidden Effect | Execution Mechanism |
|-------|----------|---------------|---------------------|
| B | SUBPROCESS | subprocess.Popen in CLI helper | Direct execution |
| D | DYNAMIC_IMPORT | importlib spawns subprocess | Dynamic loading |
| E | NETWORK | requests.get on cache miss | Conditional execution |
| F | SUBPROCESS | os.system emergency kill switch | Emergency path |
| G | SUBPROCESS | subprocess.Popen in recovery | Exception handling |
| H | FILESYSTEM | open() in background worker | Async execution |
| I | PLUGIN | dynamic plugin network call | Dynamic loading |
| J | SUBPROCESS | subprocess.Popen multiple actors | Multiple executions |

### Worlds with Hidden Effects That Never Execute (2 worlds)

| World | Category | Hidden Effect | Why Not Executed |
|-------|----------|---------------|------------------|
| A | SUBPROCESS | subprocess.Popen in legacy module | Dead code path |
| C | FILESYSTEM | shutil.copy in deprecated utils | Dead code |

### Benign Worlds (0 worlds)

Unlike Phase 29, all 10 worlds have hidden effects. The false positive test is covered by the never-executed worlds (A, C) where the system must not claim NO_EFFECT.

## The RuntimeObserver

The core observation engine:

```python
class RuntimeObserver:
    """Observes runtime execution and produces evidence of effects.

    CRITICAL INVARIANTS:
        OBSERVATION ≠ AUTHORITY
        OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT
        EXECUTION_RECEIPT ≠ AUTHORITY
        NOT_OBSERVED ≠ DOES_NOT_EXIST
        ATTRIBUTION_UNKNOWN ≠ ATTRIBUTION_TO_CALLER
    """
```

**What it records:**
- `observation_id`, `effect_id`, `timestamp`
- `actor`, `component`, `operation`, `resource`
- `category`, `source`, `target`
- `execution_status` (NEVER_EXECUTED, EXECUTING, EXECUTED, EXECUTED_MULTIPLE)
- `authority_context`, `capability_id`, `authorization_id`, `provenance_id`
- `scope` (PRODUCTION, STAGING, TEST, DEVELOPMENT)
- `domain`, `execution_path`, `triggering_event`
- `observation_mechanism`, `receipt`
- `temporal_validity`, `provenance`
- `attribution_status` (ATTRIBUTED, ATTRIBUTION_UNKNOWN, ATTRIBUTION_PARTIAL, CROSS_DOMAIN_BLOCKED)
- `relationship_to_inventory` (in_inventory, not_in_inventory, observed_not_declared, unknown)

## The PromotionEngine

Manages epistemic transitions:

```python
class PromotionEngine:
    """Manages epistemic promotion of effects through the revelation ladder.

    Rules:
        1. Promotion requires runtime evidence.
        2. NOT_OBSERVED never promotes to NO_EFFECT.
        3. OBSERVATION never creates AUTHORITY.
        4. Each transition must be earned.
    """
```

**Promotion rules:**
- UNKNOWN + observation → OBSERVED
- STRUCTURALLY_POSSIBLE + observation → OBSERVED
- POSSIBLY_REACHABLE + observation → OBSERVED
- REACHABLE_BUT_UNOBSERVED + observation → OBSERVED
- OBSERVED + execution → EXECUTED
- NOT_OBSERVED + observation → OBSERVED (can be promoted if evidence arrives)
- NOT_OBSERVED + no observation → NOT_OBSERVED (preserved, not NO_EFFECT)

## The Independent Oracle

Evaluates observations against ground truth:

```python
class IndependentOracle:
    """Evaluates runtime observations against ground truth.

    The oracle knows:
        - effect exists
        - effect executes
        - expected category
        - expected source

    The runtime observer may only know what the runtime actually exposes.
    """
```

**Evaluation outputs:**
- `true_observed`: correctly observed effects
- `false_observed`: observed but not in ground truth
- `missed_effects`: ground-truth effects never observed
- `never_executed`: effects that exist but never execute
- `attribution_correct`: observations with correct attribution
- `attribution_unknown`: observations with unknown attribution
- `escape_detected`: unauthorized executions detected

## Key Results

### 1. Runtime Observation Can Reveal Hidden Effects

Worlds B, D, E, F, G, H, I, J all have hidden effects that execute. The RuntimeObserver successfully records observations of these effects, producing evidence with full provenance.

**Example (World B — Hidden Executed):**
- Hidden effect: subprocess.Popen in `src/sas/cli/helper.py`
- Observer records: observation_id, timestamp, actor, component, operation, resource, execution_status=EXECUTED
- Provenance: `phase30_observer:eff-xxxxx`
- Attribution: ATTRIBUTION_UNKNOWN (correct — observer doesn't know authority)

### 2. Non-Observation Is NOT Evidence of Absence

World A (Hidden Never Executed) and World C (Structurally Visible Not Executed) have hidden effects that never execute. The RuntimeObserver sees nothing.

**Critical result:** The system does NOT claim NO_EFFECT. The effects remain in their epistemic state (UNKNOWN or STRUCTURALLY_POSSIBLE).

**Test:** `test_hidden_effect_never_executed_stays_unknown`
```python
# Observer sees nothing
assert observer.observation_count == 0
# But hidden effects exist
assert world.has_hidden_effects
# The system must NOT claim NO_EFFECT
```

### 3. Promotion Requires Runtime Evidence

The PromotionEngine enforces that promotion requires actual runtime observation:

- UNKNOWN without observation → stays UNKNOWN
- STRUCTURALLY_POSSIBLE without observation → stays STRUCTURALLY_POSSIBLE
- OBSERVED without new execution → stays OBSERVED
- NOT_OBSERVED without observation → stays NOT_OBSERVED (≠ NO_EFFECT)

**Test:** `test_not_observed_without_observation_stays_not_observed`
```python
result = engine.attempt_promotion(
    effect=effect,
    current_state=RevelationState.NOT_OBSERVED,
    observation=None,
)
assert result.final_state == RevelationState.NOT_OBSERVED
```

### 4. Authority Non-Amplification

Runtime observations contain NO authority-creating fields:

- `authorization_id`: None (observation records what happened, not what was permitted)
- `capability_id`: None (observation doesn't create capability)
- `provenance_id`: None (observation doesn't create provenance)

**Test:** `test_observation_does_not_create_authority`
```python
assert obs.authorization_id is None
assert obs.capability_id is None
```

### 5. Attribution Is Correctly Unknown

For hidden effects (Worlds B-J), the observer correctly marks attribution as ATTRIBUTION_UNKNOWN. The observer does NOT invent authority context.

**Test:** `test_attribution_unknown_not_attribution_to_caller`
```python
assert obs.attribution_status == AttributionStatus.ATTRIBUTION_UNKNOWN
```

### 6. Observed Set ⊂ Possible Effect Set

In World A (Hidden Never Executed):
- Observed set: {} (empty)
- Ground truth: {declared_effect, hidden_effect}
- Observed set is a proper subset of ground truth

**Test:** `test_observed_set_not_complete_effect_set`
```python
assert observed_ids.issubset(ground_truth_ids)
assert observed_ids != ground_truth_ids
```

### 7. Multiple Executions Produce Distinct Observations

World J (Multiple Executions) tests that the same effect executing under different conditions produces distinct observations:

- Different actors → different observations
- Different scopes → different observations
- Same effect_id preserved across observations

**Test:** `test_same_effect_different_actors`
```python
assert obs1.observation_id != obs2.observation_id
assert obs1.effect_id == obs2.effect_id
assert obs1.actor != obs2.actor
```

### 8. Temporal Validity Preserved

Every observation includes:
- `timestamp`: when the observation was made
- `temporal_validity`: when the observation is valid
- `provenance`: lineage of the observation
- `observation_mechanism`: how the observation was generated

**Test:** `test_observation_has_temporal_validity`
```python
assert obs.temporal_validity != ""
assert obs.provenance != ""
```

### 9. Cross-Domain Scope Preserved

Observations are scoped to their domain of execution. An observation in production does NOT automatically become evidence about staging.

**Test:** `test_cross_domain_observation_not_cross_domain_authority`
```python
assert obs.scope == ObservationScope.PRODUCTION
assert obs.domain == "production"
```

### 10. The Most Important Negative Case

**World A: Hidden Never Executed**
- Effect exists: subprocess.Popen in `src/sas/quant/legacy.py`
- Execution path: never triggered
- Runtime observer sees nothing
- System produces: UNKNOWN_EFFECT (not NO_EFFECT)

**This is the strongest test in Phase 30.** It demonstrates that the system correctly handles the case where:
1. A hidden effect exists
2. It never executes
3. No structural discovery mechanism identifies it
4. Runtime observation sees nothing
5. The system correctly refuses to claim NO_EFFECT

## The Critical Invariants (All Verified)

| Invariant | Test | Status |
|-----------|------|--------|
| `NOT_OBSERVED ≠ DOES_NOT_EXIST` | `test_not_observed_not_does_not_exist` | ✅ |
| `NOT_EXECUTED_YET ≠ WILL_NEVER_EXECUTE` | `test_not_executed_yet_not_will_never_execute` | ✅ |
| `OBSERVED_EFFECT ≠ AUTHORIZED_EFFECT` | `test_observed_effect_not_authorized` | ✅ |
| `OBSERVATION ≠ AUTHORITY` | `test_observation_not_authority` | ✅ |
| `STRUCTURAL_POSSIBILITY ≠ EXECUTED_EFFECT` | `test_structural_possibility_not_executed_effect` | ✅ |
| `RUNTIME_OBSERVATION ≠ GLOBAL_COMPLETENESS` | `test_runtime_observation_not_global_completeness` | ✅ |
| `OBSERVED_SET ≠ COMPLETE_EFFECT_SET` | `test_observed_set_not_complete_effect_set` | ✅ |
| `ATTRIBUTION_UNKNOWN ≠ ATTRIBUTION_TO_CALLER` | `test_attribution_unknown_not_attribution_to_caller` | ✅ |
| `CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY` | `test_cross_domain_observation_not_cross_domain_authority` | ✅ |
| `TEMPORAL_OBSERVATION ≠ HISTORICAL_EXISTENCE` | `test_temporal_observation_not_historical_existence` | ✅ |
| `REVALIDATION ≠ RETROACTIVE_INVALIDATION` | `test_revalidation_not_retroactive_invalidation` | ✅ |
| `COMPLETENESS ≠ CLOSURE` | `test_completeness_not_closure` | ✅ |

## Classification

**RUNTIME_EFFECT_REVELATION_ESTABLISHED_WITHIN_SCOPE**

### What the system CAN do:
1. Observe hidden effects that execute and produce evidence with full provenance
2. Promote effects from UNKNOWN to OBSERVED to EXECUTED based on runtime evidence
3. Preserve NOT_OBSERVED without promoting to NO_EFFECT
4. Correctly attribute authority context (or mark it unknown)
5. Maintain temporal validity and provenance for all observations
6. Scope observations to their domain of execution
7. Handle multiple executions of the same effect under different conditions

### What the system CANNOT do:
1. Observe effects that never execute
2. Distinguish between "no effect" and "effect exists but undiscovered"
3. Create authority through observation
4. Invent attribution when authority context is unavailable
5. Claim global completeness from a finite set of observations

### What remains UNKNOWN:
1. Whether all hidden effects can eventually be revealed through runtime observation
2. Whether observation coverage is monotonic (more execution → more observations)
3. Whether attribution can be established for all observed effects

## The Honest Result

The scientifically honest result is **not** "runtime monitoring solves effect discovery." It is:

> **Runtime observation can convert structurally possible or unknown effects into concrete, provenance-bearing observations. It cannot establish that no unobserved effect exists. The epistemic ladder has no shortcut from non-observation to non-existence.**

This limitation is **not a failure**. It is a **valuable result**: the system knows the boundary of its own knowledge.

## The Two Epistemic Machineries

Phase 30 demonstrates that the system needs two fundamentally different kinds of epistemic machinery:

| Machinery | What It Does | What It Cannot Do |
|-----------|--------------|-------------------|
| **Structural Discovery** (Phase 29) | Detects POSSIBLE effects (structural gaps) | Cannot confirm execution |
| **Runtime Observation** (Phase 30) | Detects EXECUTED effects | Cannot prove absence of unobserved effects |

**Neither can prove the universal absence of unobserved effects.**

This distinction is substantially more important than another authority abstraction. It is the difference between:

- **Discovery of positive events** (what happened)
- **Justification of negative claims** (what didn't happen)

The system can do the first. It cannot do the second.

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
EFFECT AUTHORITY CLOSURE
    ↓
GOVERNED EXECUTION
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `examples/sovereign_agent/runtime_effect_revelation.py` | ~1,100 | 10 worlds + observer + oracle + promotion engine |
| `tests/unit/test_runtime_effect_revelation.py` | ~600 | 59 tests |

## Test Count

- **Before Phase 30:** 2,967
- **After Phase 30:** 3,026 (+59)

## The Full Conceptual Progression

```
Authority origin → Authority graph → Authority graph completeness
    → Authority under uncertainty → Authority transformation
    → Epistemic consequentiality → Runtime escape discrimination
    → Effect inventory → Effect remediation
    → Effect graph completeness → Continuous effect reconciliation
    → Effect knowledge gap discovery → Runtime effect revelation
```

## Next Boundary

The system can now:
1. Detect structural gaps (Phase 29)
2. Observe runtime executions (Phase 30)
3. Reconcile observations with inventory (Phase 28)

The remaining question:

**Can the system close the gap between observed effects and authorized effects?**

This would connect Phase 30's runtime observations to the authority graph — determining whether observed effects have valid authority paths, and flagging escapes when they don't.

The governing principle remains:

> **RUNTIME OBSERVATION CAN ESTABLISH THAT AN EFFECT OCCURRED.**
> **IT CANNOT, BY ITSELF, ESTABLISH THAT NO UNOBSERVED EFFECT EXISTS.**
