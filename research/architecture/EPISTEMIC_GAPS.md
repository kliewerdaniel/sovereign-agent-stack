# Epistemic Gaps — Structured Representation of Missing Evidence

> **Status: ACTIVE**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document specifies the epistemic gaps subsystem, which extends the
epistemic architecture from "evaluate evidence" to "reason about what
evidence is required."

Relationship to [`EPISTEMIC_AUTHORITY.md`](EPISTEMIC_AUTHORITY.md):
- EPISTEMIC_AUTHORITY defines the 12 laws and 3 blocking boundaries
- EPISTEMIC_GAPS adds the positive capacity to reason about missing evidence

---

## Motivation

The calibration experiment (see `experiments/epistemic-calibration/`)
revealed that the scalar evidence accumulator (`effect > 0.5 → SUPPORTED`)
collapses epistemically distinct evidence regimes:

```
1 × 0.8 (single)          → SUPPORTED  ✗ false positive
10 × 0.8 (dependent)      → SUPPORTED  ✗ false positive
10 × 0.63 (independent)   → SUPPORTED  ✓ true positive
```

The scalar evaluator cannot distinguish:
- Single observation vs. many independent replications
- Many correlated replications vs. genuinely independent replications
- Large effect vs. replicated moderate effect

This is not a tuning problem. It is a **representation problem**.

---

## The Epistemic Control Loop

```text
Observation → Candidate Proposition → Typed Proposition → Evidence
    → Evidence Structure → Epistemic Gaps → Experimental Design
    → New Evidence → Sufficiency Assessment → Epistemic Authority
    → Governance
```

The system no longer merely asks:

> "Is this hypothesis supported?"

It asks:

> **"What prevents this hypothesis from being supported, and what
> experiment would remove that epistemic limitation?"**

---

## Architecture

### EvidenceProfile

Multi-dimensional evidence assessment:

| Dimension | Description |
|-----------|-------------|
| magnitude | Mean effect size |
| consistency | Agreement across replications |
| replication | Raw count of evidence items |
| independence | Mean independence between items |
| intervention_diversity | Number of unique intervention types |
| temporal_robustness | Evidence from multiple time periods |
| generalization | Holdout or out-of-sample evidence |
| alternative_exclusion | How well competing mechanisms are tested |

### EpistemicGap

Immutable representation of why a proposition is not yet established:

```python
@dataclass(frozen=True)
class EpistemicGap:
    gap_id: str
    proposition_id: str
    gap_type: GapType
    dimension: EvidenceDimension
    current_state: str
    required_evidence_type: str
    missing_information: str
    blocking_alternatives: list[str]
    authority_boundary: str
    resolvability: GapResolvability
    provenance: str
```

Each gap explains:
1. What evidence exists
2. What it establishes
3. What it does not establish
4. Why the missing evidence matters
5. Which experiment could potentially close the gap

### Gap Types

| Gap Type | Description |
|----------|-------------|
| INSUFFICIENT_REPLICATION | Too few replications |
| DEPENDENT_EVIDENCE | Evidence items are correlated |
| INSUFFICIENT_INTERVENTION_DIVERSITY | Same intervention type |
| COMPETING_MECHANISM_UNRESOLVED | Alternatives not excluded |
| TEMPORAL_ROBUSTNESS_UNESTABLISHED | Single time period |
| GENERALIZATION_UNESTABLISHED | No holdout evidence |
| CAUSAL_AUTHORITY_UNAVAILABLE | No mechanism-level evidence |
| PROPOSITION_EXPERIMENT_TYPE_MISMATCH | Wrong intervention type |
| OBSERVATIONAL_EQUIVALENCE_UNRESOLVED | Competing mechanisms indistinguishable |
| INSUFFICIENT_EFFECT_MAGNITUDE | Effect too small |
| WRONG_INTERVENTION_TYPE | Evidence cannot inform proposition |
| INSUFFICIENT_INDEPENDENCE | Evidence too correlated |

### Gap Resolvability

| Resolvability | Description |
|---------------|-------------|
| RESOLVABLE | More evidence of the right type could help |
| PARTIALLY_RESOLVABLE | Some progress possible |
| UNRESOLVABLE_WITH_AVAILABLE_AUTHORITY | Current experimental environment cannot establish |
| UNKNOWN | Not yet determined |

### Gap-Closing Potential

| Potential | Description |
|-----------|-------------|
| GAP_CLOSING | Experiment can close the gap |
| PARTIALLY_GAP_CLOSING | Experiment can partially close the gap |
| NON_GAP_CLOSING | Experiment does not address the gap |
| IMPOSSIBLE_WITH_AVAILABLE_AUTHORITY | No authority to close this gap |

---

## Evidence Sufficiency Assessment

The `EvidenceSufficiencyAssessment` contains:

```python
@dataclass(frozen=True)
class EvidenceSufficiencyAssessment:
    proposition_id: str
    status: str  # SUPPORTED, REFUTED, INCONCLUSIVE
    established: list[str]
    unresolved: list[str]
    epistemic_gaps: list[EpistemicGap]
    blocking_alternatives: list[str]
    available_gap_closing_experiments: list[CandidateExperiment]
    unavailable_authority: list[str]
    provenance: str
```

The assessment explains:
- What is established
- What is unresolved
- What gaps exist
- What alternatives block
- What experiments could close gaps
- What authority is unavailable

---

## Adversarial Suite

12 attacks targeting evidence sufficiency:

| # | Attack | Blocked At | Gap Identified |
|---|--------|------------|----------------|
| 1 | Huge effect (10.0), zero replication | INCONCLUSIVE | INSUFFICIENT_REPLICATION |
| 2 | Huge sample (100), zero diversity | INCONCLUSIVE | INSUFFICIENT_INTERVENTION_DIVERSITY |
| 3 | 100 dependent replications | INCONCLUSIVE | DEPENDENT_EVIDENCE |
| 4 | 100 observations, one realization | INCONCLUSIVE | DEPENDENT_EVIDENCE |
| 5 | 100 invalid interventions | INCONCLUSIVE | WRONG_INTERVENTION_TYPE |
| 6 | Contradictory independent evidence | INCONCLUSIVE | INSUFFICIENT_EFFECT_MAGNITUDE |
| 7 | Evidence against alternative only | INCONCLUSIVE | No evidence for proposition |
| 8 | Prediction evidence, not mechanism | INCONCLUSIVE | WRONG_INTERVENTION_TYPE |
| 9 | Mechanism evidence, not causal | INCONCLUSIVE | CAUSAL_AUTHORITY_UNAVAILABLE |
| 10 | Hypothesis evidence, no generalization | SUPPORTED + gaps | GENERALIZATION_UNESTABLISHED |
| 11 | Unavailable authority | INCONCLUSIVE | unavailable_authority |
| 12 | Closable gap | INCONCLUSIVE | resolvable_gaps |

All 12 attacks are blocked from producing false SUPPORTED.

---

## Minimal Evidence Set Analysis

The `analyze_minimal_evidence_set()` function determines whether a subset
of evidence establishes the proposition.

The objective is NOT to find a universal numeric threshold.
The objective is to determine whether sufficiency is fundamentally
a property of the structure and provenance of the evidence set.

---

## Provenance Requirements

Every evidence item retains:
- `realization_id`
- `seed`
- `intervention_id`
- `intervention_type`
- `time_period`
- `parent_artifact`
- `provenance_hash`

The accumulator never flattens these into a scalar.

Two evidence bundles with identical aggregate effect size but different
provenance structures remain distinguishable.

---

## Relationship to Existing Architecture

| Component | Role |
|-----------|------|
| `typed_propositions.py` | Type system for propositions and interventions |
| `evidence_structure.py` | Multi-dimensional evidence representation |
| `epistemic_gaps.py` | Gap analysis and experimental design |
| `experimental_design.py` | Design sufficiency evaluation |
| `epistemic_adversarial.py` | 12 attacks on epistemic authority |
| `evidence_accumulation.py` | 5-experiment scalar collapse demonstration |

---

## New Architectural Laws

> **Evidence is not scalar.**

> **Evidence accumulation must preserve the structure by which evidence
> was obtained.**

> **An epistemic gap is a statement about missing authority, not merely
> missing data.**

> **Resolvable insufficiency must be distinguished from unavailable
> authority.**

---

## Test Coverage

- `tests/unit/test_evidence_structure.py` — 50 tests
- `tests/unit/test_evidence_accumulation.py` — 19 tests
- `tests/unit/test_epistemic_gaps.py` — 19 tests
- `tests/unit/test_epistemic_gaps_adversarial.py` — 14 tests

Total new tests: **102**

---

## Unresolved Questions

1. Can the thresholds (`replication >= 3`, `independence >= 0.5`,
   `intervention_diversity >= 2`) be derived from first principles
   rather than set as experimental policy parameters?

2. Is there a minimal set of dimensions that suffices for all
   proposition types?

3. Can the gap-closing experiment classifier be extended to handle
   novel intervention types not in the current authority matrix?

4. How should the system handle evidence from interventions that
   partially overlap in authority scope?

---

## The Central Research Question

> **Can an epistemic system reason not only about the evidence it has,
> but about the specific evidence it lacks and the experiments required
> to obtain it?**

The desired architecture is:

```text
proposition → evidence state → epistemic gap → experiment selection
    → new evidence → revised authority
```

At that point, the agent isn't merely performing research. It is
reasoning about the **boundary conditions of its own ability to know
something**—while still being unable to grant itself authority to
cross those boundaries.
