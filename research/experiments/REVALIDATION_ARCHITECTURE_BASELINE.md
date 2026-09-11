# Revalidation Architecture Baseline

## Phase 0 — Repository Reconnaissance

**Date:** 2026-09-09
**Baseline tests:** 2,358 passing

---

## Existing Infrastructure Map

### Dependency & Authorization Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `AuthorizationDependencyGraph` | `authorization_dependencies.py` | Provenance-backed dependency graph | Frontier computation |
| `DependencyIntersectionEvaluator` | `dependency_intersection.py` | Evidence-dependency intersection | Frontier soundness |
| `DependencyEpistemicState` | `dependency_status.py` | Per-dependency epistemic status | Conditional frontiers |
| `DependencyDiscoveryEngine` | `dependency_discovery.py` | Multi-method dependency discovery | Frontier validation |
| `DependencyValidationEngine` | `dependency_discovery.py` | Method-strength validation | Soundness semantics |

### Epistemic Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `EpistemicInvalidationEngine` | `epistemic_invalidation.py` | Dependency-sensitive invalidation | Epistemic drift |
| `InvalidationDecision` | `epistemic_invalidation.py` | PRESERVE/SUSPEND/REEVALUATE/INVALIDATE | Frontier classification |
| `PartialInvalidationEngine` | `partial_invalidation.py` | Sub-graph invalidation | Frontier minimality |
| `EpistemicCycleDetector` | `epistemic_cycles.py` | Cycle detection in epistemic dependencies | Frontier recursion |
| `EpistemicComposition` | (in compositional_authority) | Compositional epistemic authority | Frontier composition |

### Completeness Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `CompletenessEngine` | `dependency_completeness.py` | Multi-dimensional completeness assessment | Frontier confidence |
| `CompletenessClaim` | `dependency_completeness.py` | Epistemic artifact (non-authoritative) | Frontier claims |
| `CompletenessScope` | `dependency_completeness.py` | Proposition/consequence/environment/domain scoping | Conditional frontiers |
| `CompletenessStatus` | `dependency_completeness.py` | 10 completeness states | Frontier status |
| `IntersectionStatus` | `dependency_completeness.py` | NO_INTERSECTION/NO_RELEVANT/GRAPH_COMPLETE | Frontier discrimination |

### Temporal Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `TemporalCompletenessEngine` | `temporal_completeness.py` | Temporal completeness drift | Temporal frontiers |
| `CompletenessDriftType` | `temporal_completeness.py` | 10 drift types | Frontier drift classification |
| `CompletenessValidityInterval` | `temporal_completeness.py` | Temporal + scopal bounds | Frontier validity windows |
| `RevalidationFrontier` | `temporal_completeness.py` | Minimum revalidation surface | **Primary extension point** |
| `RevalidationRequirement` | `temporal_completeness.py` | 8 requirement levels | Frontier severity |

### Authority & Drift Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `AuthorityDriftEvent` | `authority_drift.py` | World change events | Frontier triggers |
| `DriftFinding` | `authority_drift.py` | Authority drift findings | Frontier findings |
| `DriftType` | `authority_drift.py` | DOCUMENTATION/IMPLEMENTATION/RUNTIME/AUTHORITY/GOVERNANCE/PROVENANCE | Frontier drift types |
| `ContinuousAuthorityReconciler` | `continuous_reconciliation.py` | Multi-world reconciliation | Multi-agent frontiers |
| `WorldState` | `continuous_reconciliation.py` | Topology/authority/governance/provenance state | Frontier world model |

### Multi-Agent Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `MultiAgentTrial` | `multi_agent_trial.py` | Multi-agent authority competition | Multi-agent frontiers |
| `MultiAgentEnvironment` | `multi_agent_environment.py` | Agent environment with authority traps | Frontier scenarios |
| `AgentTrajectory` | `trajectory.py` | Full trial history | Frontier provenance |
| `IntentGraph` | `intent_graph.py` | Joint intent without authority leakage | Frontier intent tracking |

### TOCTOU / Race Layer

| Module | File | Purpose | Reusable For |
|--------|------|---------|--------------|
| `AuthorityRaces` | `authority_races.py` | TOCTOU authority experiments | Frontier staleness |
| `TrialEnvironment` | `trial_environment.py` | Deliberate authority traps | Frontier scenarios |
| `LongHorizonTrial` | `long_horizon_trial.py` | 10-world-state trajectories | Temporal frontier validation |

---

## Reusable Types for Frontier Computation

### For Frontier Soundness

```python
# From dependency_completeness.py
CompletenessStatus.KNOWN_COMPLETE     # Graph is complete → frontier can be trusted
CompletenessStatus.KNOWN_INCOMPLETE   # Graph is incomplete → frontier may be unsound
CompletenessStatus.UNKNOWN            # Graph completeness unknown → frontier unknown
CompletenessStatus.OVER_APPROXIMATED  # Graph has extra deps → frontier may be conservative
```

```python
# From temporal_completeness.py
CompletenessValidityInterval.is_valid_at(timestamp)   # Temporal validity check
CompletenessValidityInterval.is_valid_in_scope(scope)  # Scopal validity check
CompletenessValidityInterval.conditions_met(active)   # Conditional validity check
```

### For Frontier Classification

```python
# From temporal_completeness.py
RevalidationRequirement.NOTHING           # Empty frontier
RevalidationRequirement.DEPENDENCY_ONLY   # Only dependency needs revalidation
RevalidationRequirement.COMPLETENESS_CLAIM # Completeness claim needs revalidation
RevalidationRequirement.EPISTEMIC_STATE   # Epistemic state needs revalidation
RevalidationRequirement.PROPOSITION       # Proposition needs revalidation
RevalidationRequirement.AUTHORIZATION     # Authorization needs revalidation
RevalidationRequirement.GOVERNANCE_REVIEW # Governance review required
RevalidationRequirement.FULL_REVALIDATION # Full revalidation required
```

### For Frontier Drift

```python
# From temporal_completeness.py
CompletenessDriftType.WORLD_CHANGE_NO_DEPENDENCY_CHANGE    # World changed, deps didn't
CompletenessDriftType.DEPENDENCY_CHANGE_NO_COMPLETENESS_CHANGE
CompletenessDriftType.COMPLETENESS_CHANGE_NO_EPISTEMIC_CHANGE
CompletenessDriftType.COMPLETENESS_STALE                   # Claim is stale
CompletenessDriftType.COMPLETENESS_FALSE_STALE             # Claim appears stale but isn't
CompletenessDriftType.CONDITIONAL_COMPLETENESS_VIOLATED    # Condition no longer met
```

---

## Duplicate Abstractions That Must NOT Be Created

### 1. Do NOT create another WorldState
The existing `WorldState` in `continuous_reconciliation.py` already captures:
- `static_topology` — static dependency graph
- `documented_topology` — documentation state
- `runtime_topology` — runtime behavior
- `authority_state` — authority configuration
- `governance_state` — governance policies
- `provenance_state` — provenance records
- `epistemic_state` — epistemic claims

Any new frontier experiment should use this existing `WorldState`.

### 2. Do NOT create another DriftEvent
`AuthorityDriftEvent` already captures:
- `previous_state` and `new_state` — state delta
- `affected_actor` and `affected_component` — change scope
- `event_type` — classification

### 3. Do NOT create another Scope
`CompletenessScope` already captures:
- `proposition_id` — proposition binding
- `consequence_type` — consequence binding
- `environment` — environment binding
- `temporal_interval` — temporal binding
- `domain` — domain binding
- `actor_id` — actor binding
- `resource_id` — resource binding

### 4. Do NOT create another InvalidationEngine
`EpistemicInvalidationEngine` already handles dependency-sensitive invalidation with:
- `evaluate_invalidation()` — evaluate new evidence
- `InvalidationDecision` — PRESERVE/SUSPEND/REEVALUATE/INVALIDATE
- Partial invalidation for sub-graphs
- Cycle detection

### 5. Do NOT create another ReconciliationEngine
`ContinuousAuthorityReconciler` already handles:
- Multi-world reconciliation
- Topology/governance/runtime/provenance deltas
- Authority debt tracking
- Staleness detection

---

## Candidate Extension Points

### Primary: `RevalidationFrontier` Enhancement

The current `RevalidationFrontier` is minimal:
```python
@dataclass(frozen=True)
class RevalidationFrontier:
    frontier_id: str
    world_change_id: str
    authorization_id: str
    timestamp: str
    affected_dependencies: list[str]
    affected_propositions: list[str]
    affected_completeness_claims: list[str]
    affected_authorizations: list[str]
    affected_epistemic_states: list[str]
    governance_review_required: bool
    revalidation_requirement: RevalidationRequirement
    scope: Optional[CompletenessScope]
    evidence: list[str]
    provenance_chain: list[str]
    limitations: list[str]
```

This is sufficient for representing a set of affected artifacts. The next milestone requires testing whether this set is **sound and minimal**, not adding new fields.

### Secondary: `TemporalCompletenessEngine.detect_completeness_drift()`

This method currently produces drift findings. It needs to be exercised against:
- Direct/transitive/unrelated dependencies
- Shared dependencies
- Conditional dependencies
- Incomplete graphs

### Tertiary: `compute_revalidation_frontier()`

This method currently produces frontiers. It needs to be tested for:
- Soundness (does it catch all affected artifacts?)
- Minimality (does it avoid catching unaffected artifacts?)
- Composition (do frontiers compose correctly?)

---

## Known Gaps

### 1. Frontier Soundness Under Incomplete Graphs

The current `compute_revalidation_frontier()` only knows about declared dependencies. It has no mechanism to represent:

```
EMPTY FRONTIER relative to INCOMPLETE GRAPH
≠
EMPTY FRONTIER relative to COMPLETE GRAPH
```

This is the primary semantic gap to investigate in Phase 3.

### 2. Frontier Composition Algebra

No existing code tests whether frontiers compose. The epistemic composition machinery (`epistemic_composition.py`) handles authority composition but not frontier composition.

### 3. Multi-Agent Frontier Propagation

The multi-agent infrastructure tracks agent-specific epistemic state but has no mechanism for:
- Evidence discovered by Agent A affecting Agent B's frontier
- Frontier disagreement between agents
- Frontier convergence

### 4. TOCTOU for Frontiers

The existing `authority_races.py` tests TOCTOU for authority but not for frontiers. A frontier computed at T0 may be stale at T2 when execution occurs.

### 5. Conditional Dependency Frontier Semantics

The current `CompletenessScope` tracks conditions but `compute_revalidation_frontier()` does not check whether conditions are met when computing the frontier.

---

## Reuse Map for Experiments

| Experiment | Primary Reuse | Secondary Reuse |
|------------|---------------|-----------------|
| 1. Frontier Soundness | `AuthorizationDependencyGraph` | `CompletenessEngine` |
| 2. Frontier Minimality | `DependencyIntersectionEvaluator` | `EpistemicInvalidationEngine` |
| 3. False Minimality | `CompletenessEngine` | `DependencyEpistemicState` |
| 4. Soundness vs Completeness | `CompletenessStatus` | `IntersectionStatus` |
| 5. Over-approximated Frontiers | `RevalidationFrontier` | `RevalidationRequirement` |
| 6. Under-approximated Frontiers | `CompletenessStatus.UNKNOWN` | `CompletenessValidityInterval` |
| 7. Shared Dependencies | `AuthorizationDependencyGraph` | `DependencyIntersectionEvaluator` |
| 8. Conditional Dependencies | `CompletenessScope` | `CompletenessValidityInterval` |
| 9. Temporal Frontiers | `TemporalCompletenessEngine` | `AuthorityDriftEvent` |
| 10. Frontier Composition | `epistemic_composition` | `RevalidationFrontier` |
| 11. Order Dependence | `AuthorityAlgebra` | `epistemic_composition` |
| 12. Multi-Agent Frontiers | `MultiAgentTrial` | `MultiAgentEnvironment` |
| 13. Authority Race | `AuthorityRaces` | `TrialEnvironment` |
| 14. Frontier Does Not Authorize | `EpistemicInvalidationEngine` | `InvalidationDecision` |
| 15. Adversarial Injection | `DependencyValidationEngine` | `DependencyDiscoveryEngine` |
| 16. Frontier as Epistemic Artifact | `CompletenessClaim` | `CompletenessStatus` |
| 17. Frontier Completeness | `EpistemicCycleDetector` | `PartialInvalidationEngine` |

---

## Implementation Order

Based on the reuse analysis, the implementation order is:

1. **Enhance `RevalidationFrontier`** with soundness/completeness tracking
2. **Enhance `TemporalCompletenessEngine`** with frontier composition
3. **Add frontier validation** against ground truth
4. **Add adversarial frontier tests**
5. **Add multi-agent frontier tests**
6. **Add TOCTOU frontier tests**

Each enhancement should be driven by experimental results, not by anticipated needs.

---

## Conclusion

The existing architecture has substantial reusable infrastructure for incremental epistemic revalidation. The primary gap is not missing abstractions but **unverified composition** of existing abstractions under adversarial conditions.

The `RevalidationFrontier` is the correct extension point. It should be enhanced only as experiments demonstrate semantic necessity.

The key invariant to preserve:

> A MINIMAL REVALIDATION FRONTIER IS ONLY AS SOUND AS THE DEPENDENCY KNOWLEDGE FROM WHICH IT WAS DERIVED.
