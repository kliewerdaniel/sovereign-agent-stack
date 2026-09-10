# Phase 28: Continuous Effect Reconciliation

**Status:** Complete — 30 new tests, 2,929 total passing

## Central Research Question

> Can a sovereign execution system know when it no longer knows the complete set of effects it is capable of producing?

## The Problem Phase 27 Left Open

Phase 27 established that the declared effect inventory is **incomplete** — 23 hidden effects exist across 16 adversarial worlds. The critical invariant:

```
100% CLOSURE OF AN INCOMPLETE EFFECT INVENTORY ≠ GLOBAL EFFECT CLOSURE
```

But Phase 27 was a **point-in-time** assessment. It answered: "Is the inventory complete *now*?" It did not address: "What happens when the system *changes*?"

## The Phase 28 Hypothesis

> A system can maintain the epistemic status of its effect inventory over time by treating completeness claims as **temporally bounded** — valid at commit C1, expired (not invalidated) at commit C2 when the executable system changes.

## The Critical Distinction

```
COMPLETENESS CLAIM AT C1: VALID
    ↓ (system changes)
COMPLETENESS CLAIM AT C1: EXPIRED (not invalidated)
COMPLETENESS CLAIM AT C2: UNKNOWN / INCOMPLETE
```

**Key insight:** Expiry ≠ invalidation. The C1 claim was true at C1. It simply does not extend to C2. This is the same temporal semantics as the earlier temporal authority work.

## Architecture

```
SOURCE / BUILD / RUNTIME CHANGE
              ↓
       EFFECT DISCOVERY
              ↓
       INVENTORY DELTA
              ↓
     COMPLETENESS ASSESSMENT
              ↓
       ┌──────┴──────┐
       ↓             ↓
    COMPLETE      UNKNOWN /
                   INCOMPLETE
       ↓             ↓
 EFFECT CLOSURE   REVALIDATION
       ↓             ↓
       └──────┬──────┘
              ↓
      GLOBAL CLAIM BOUNDARY
```

## The Continuous Effect Reconciler

The core component is `ContinuousEffectReconciler`, which:

1. **Registers a baseline** completeness claim at commit C1
2. **Computes deltas** between inventory snapshots (using effect identity = category+source+target+operation, not UUID)
3. **Reconciles changes** by determining:
   - Scope impact: unchanged / new_category / extended / narrowed
   - Action: no_action / revalidation_required / inventory_extended / completeness_invalidated / scope_narrowed
   - Temporal impact: no_invalidation / revalidation_required
4. **Creates new claims** when the system changes, expiring (not invalidating) prior claims

## Key Invariants

| Invariant | Meaning |
|-----------|---------|
| `INVENTORY_CHANGE_INVALIDATES_COMPLETENESS_CLAIM_ONLY_WITHIN_CHANGED_SCOPE` | Adding payment effects doesn't invalidate subprocess completeness |
| `REVALIDATION_REQUIREMENT ≠ RETROACTIVE_INVALIDATION` | New claim at C2 doesn't rewrite history at C1 |
| `COMPLETENESS_CLAIM_IS_TEMPORALLY_BOUNDED` | Every claim has valid_from / valid_until |
| `EFFECT_DISCOVERY_TRIGGERS_REVALIDATION_WITHOUT_INVALIDATING_HISTORY` | Discovery triggers revalidation, not retroactive invalidation |

## The Five Reconciliation Actions

| Action | Trigger | Scope Impact | Temporal Impact |
|--------|---------|--------------|-----------------|
| `NO_ACTION` | No change in effects | unchanged | no_invalidation |
| `REVALIDATION_REQUIRED` | No baseline claim exists | — | — |
| `INVENTORY_EXTENDED` | New effects in existing categories | extended | revalidation_required |
| `COMPLETENESS_INVALIDATED` | New effect category discovered | new_category | revalidation_required |
| `SCOPE_NARROWED` | Effects removed | narrowed | no_invalidation |

## Experimental Design

Phase 28 runs 7 scenarios:

| Scenario | Change | Expected Action |
|----------|--------|-----------------|
| Baseline registration | Initial inventory | Creates current claim |
| No change | Config change, no effect changes | NO_ACTION |
| New category discovery | Payment effect added | COMPLETENESS_INVALIDATED |
| Existing category extension | New subprocess effect in CLI helper | INVENTORY_EXTENDED |
| Effect removal | CLI helper module removed | SCOPE_NARROWED |
| Multiple sequential changes | Network → Plugin added | 2× COMPLETENESS_INVALIDATED |
| Temporal validity chain | All scenarios combined | Chain of expired + current claims |

## Key Results

### 1. Temporal Validity Chain

After all scenarios, the claim chain shows:

```
Claim 1 (baseline):     EXPIRED at first change
Claim 2 (after payment): EXPIRED at next change
Claim 3 (after network): EXPIRED at next change
Claim 4 (after plugin):  CURRENT
```

**Only the latest claim is current.** Historical claims are expired, not invalidated.

### 2. Scope Impact Is Correctly Bounded

- Adding a **new category** (payment) → `COMPLETENESS_INVALIDATED` (new scope)
- Adding to **existing category** (subprocess) → `INVENTORY_EXTENDED` (same scope, more effects)
- **Removing** effects → `SCOPE_NARROWED` (no revalidation needed)

### 3. Historical Claims Are Preserved

For every expired claim:
- Status at time of creation was valid (`COMPLETE_WITHIN_SCOPE`, `UNKNOWN`, or `INCOMPLETE`)
- Expiry timestamp marks when the system changed
- No retroactive invalidation occurs

### 4. The `requires_revalidation` Property

```python
@property
def requires_revalidation(self) -> bool:
    return self.action in (
        ReconciliationAction.REVALIDATION_REQUIRED,
        ReconciliationAction.COMPLETENESS_INVALIDATED,
        ReconciliationAction.INVENTORY_EXTENDED,
    )
```

Both `COMPLETENESS_INVALIDATED` and `INVENTORY_EXTENDED` require revalidation. `SCOPE_NARROWED` does not.

## The Deeper Result

Phase 28 demonstrates that the system can maintain a **continuous epistemic state** about its effect inventory:

```
At commit C1:
  inventory = {subprocess, filesystem, database}
  completeness = COMPLETE_WITHIN_SCOPE
  closure = 100%

At commit C2 (payment module added):
  inventory = {subprocess, filesystem, database, payment}
  completeness = INCOMPLETE (new category discovered)
  closure = 100% of declared inventory
  global closure claim = REFUSED (inventory incomplete)

At commit C3 (CLI helper removed):
  inventory = {subprocess, database, payment}
  completeness = INCOMPLETE (still missing categories)
  closure = 100% of declared inventory
```

The system **knows** it doesn't know the complete set of effects. It refuses to claim global closure when the inventory is known to be incomplete.

## What Phase 28 Does NOT Claim

1. **A mechanism for achieving complete inventory.** The inventory remains incomplete after all scenarios.

2. **That complete inventory is achievable.** Effect inventory may be inherently open-ended.

3. **That the delta computation is perfect.** The experiment uses a static model; real-world effect discovery is harder.

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
EFFECT AUTHORITY CLOSURE
    ↓
GOVERNED EXECUTION
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `examples/sovereign_agent/continuous_effect_reconciliation.py` | ~941 | Reconciler + experiments |
| `tests/unit/test_continuous_effect_reconciliation.py` | ~530 | 30 tests |

## Test Count

- **Before Phase 28:** 2,899
- **After Phase 28:** 2,929 (+30)

## The Full Conceptual Progression

```
Authority origin
        ↓
Authority graph
        ↓
Authority graph completeness
        ↓
Authority under uncertainty
        ↓
Authority transformation
        ↓
Epistemic consequentiality
        ↓
Runtime escape discrimination
        ↓
Effect inventory
        ↓
Effect remediation
        ↓
Effect graph completeness
        ↓
Continuous effect reconciliation  ← Phase 28
```

## Next Boundary

The system can now detect when its inventory is incomplete and track that incompleteness over time. The next question is considerably harder:

**Can the system discover new effect categories autonomously, or is effect discovery fundamentally an external input?**

This connects to the earlier epistemic work: the system can know *that* it doesn't know, but can it know *what* it doesn't know?
