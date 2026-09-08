# Epistemic Experiment Selection — Choosing Experiments by Epistemic Value

> **Status: ACTIVE**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document specifies the epistemic experiment selection subsystem,
which extends the epistemic architecture from "identify gaps" to
"select the experiment that most efficiently reduces the proposition's
epistemic boundary."

Relationship to other architecture documents:
- [`EPISTEMIC_AUTHORITY.md`](EPISTEMIC_AUTHORITY.md) — 12 laws, 3 blocking boundaries
- [`EPISTEMIC_GAPS.md`](EPISTEMIC_GAPS.md) — Gap analysis and missing evidence
- `EPISTEMIC_EXPERIMENT_SELECTION.md` (this document) — Experiment selection

---

## Motivation

The epistemic gaps subsystem can identify what evidence is missing.
The experiment selection subsystem decides **which experiment to perform next**.

This is NOT active learning.
This is NOT Bayesian optimization.
This is NOT maximizing predictive performance.
This is NOT maximizing statistical significance.
This is NOT maximizing raw information gain.

The objective is epistemic:
> Select the experiment that most efficiently reduces the proposition's
> epistemic boundary while remaining within authorized intervention space.

---

## The Central Distinction

**Information gain ≠ epistemic value.**

An experiment can produce enormous amounts of information while providing
no additional authority over the proposition being evaluated.

Example:

```
Experiment A
10,000 additional observations
Sharpe uncertainty ↓
Mechanism authority: unchanged
Causal authority: unchanged

Experiment B
100 observations
Mechanism intervention
Alternative mechanism eliminated
Mechanism authority: materially increased
```

A conventional optimizer might strongly prefer A.
This architecture potentially prefers B.

---

## Architecture

```text
Proposition → Evidence → Epistemic Gaps → Candidate Experiments
    → Epistemic Selection → Governance → Authorization
    → Execution → Evidence → Epistemic Assessment
```

### Three Value Dimensions

The system explicitly separates three distinct value types that are
often conflated:

| Value Type | Description | Does NOT imply |
|------------|-------------|----------------|
| StatisticalValue | Reduction in estimator variance | Epistemic progress |
| InformationValue | Reduction in uncertainty over observations | Epistemic progress |
| EpistemicValue | Reduction in an authority-relevant epistemic gap | — |

An experiment can be high on statistical and information value while
being low on epistemic value.

---

## Components

### EpistemicExperimentValue

Structured representation of why an experiment is valuable:

```python
@dataclass(frozen=True)
class EpistemicValue:
    experiment_id: str
    proposition_id: str
    targeted_gaps: list[str]
    authority_scope: str
    discriminative_power: float
    gap_closing_potential: GapClosingPotential
    alternative_elimination: float
    evidence_diversity_gain: int
    temporal_coverage_gain: bool
    replication_gain: int
    independence_gain: float
    generalization_gain: bool
    provenance: str
```

Does NOT collapse into a single scalar. The system explains WHY an
experiment is valuable.

### GapReduction

Structured representation of how an experiment reduces a gap:

```python
@dataclass(frozen=True)
class GapReduction:
    gap_type: GapType
    authority_change: str
    evidence_type_change: str
    intervention_scope_change: str
    alternative_set_change: list[str]
    replication_change: int
    independence_change: float
    temporal_scope_change: str
    generalization_scope_change: str
```

Two experiments that both eliminate one gap may have very different
epistemic consequences. This preserves that structure.

### EpistemicExperimentSelector

The core selector that:

1. Analyzes epistemic gaps
2. Assesses candidate experiments
3. Computes Pareto frontier
4. Selects the experiment that most reduces the blocking gap
5. Explains the decision

The selector does NOT authorize execution.
It recommends. Governance authorizes.

### Experiment Dominance

Experiment A dominates B if:
- A is at least as capable as B across all epistemically relevant dimensions
- A is strictly better in at least one dimension
- Both remain within the same authority boundary

If neither dominates, experiments are **incomparable** (not forced into
a total ordering).

### Pareto Frontier

Given candidate experiments, the system computes an epistemic Pareto
frontier over dimensions:
- replication
- independence
- intervention diversity
- alternative elimination
- temporal robustness
- generalization
- authority scope

The system identifies experiments that are non-dominated.
Does NOT arbitrarily collapse the frontier into one scalar score.

---

## Adversarial Suite

12 attacks targeting experiment selection:

| # | Attack | Result | Why |
|---|--------|--------|-----|
| A | Huge sample (100K) vs mechanism intervention (100) | Mechanism selected | Addresses mechanism authority gap |
| B | 100 replications vs 3 new intervention classes | Diversity selected | Addresses competing mechanism gap |
| C | Generalization vs mechanism | Identifies which gap each addresses | Correct gap targeting |
| D | Causal claim with only feature evidence | UNRESOLVABLE | No mechanism authority available |
| E | Statistical decoy (variance reduction 0.99) | Rejected | High statistical value, zero epistemic value |
| F | 100 dependent replications | Rejected | Low independence |
| G | Wrong intervention type | Rejected | Cannot inform proposition |
| H | Excellent statistics, no discriminative power | Rejected | No mechanism authority |
| I | Closes irrelevant gap | Rejected | Doesn't address blocking gap |
| J | Appears useful, can't distinguish mechanisms | Rejected | Wrong intervention type |
| K | Incomparable Pareto-optimal experiments | Preserved | Not forced into total ordering |
| L | No available experiment can close gap | UNRESOLVABLE | Correctly identified |

All 12 attacks fail closed.

---

## Recommendation vs Authorization

The architecture maintains a critical boundary:

```text
Epistemic Layer → recommends experiment
    ↓
Governance Layer → authorizes experiment
    ↓
Execution Layer → produces artifact
    ↓
Evidence Layer → updates epistemic state
```

The selector recommends. It does NOT authorize.
This separation is explicitly tested.

---

## Value Separation Results

The experiments demonstrate:

| Experiment | Statistical Value | Information Value | Epistemic Value |
|------------|------------------|-------------------|-----------------|
| Huge sample (100K) | HIGH | HIGH | LOW |
| Mechanism intervention | MEDIUM | MEDIUM | HIGH |
| 100 dependent replications | HIGH | MEDIUM | LOW |
| New intervention class | MEDIUM | MEDIUM | HIGH |

Statistical value and epistemic value are NOT correlated.

---

## Provenance Requirements

Every experiment recommendation is reconstructable from:
- proposition hash
- evidence bundle hash
- epistemic assessment hash
- candidate experiment hashes
- intervention authority
- selection policy
- selector version

The recommendation itself is an immutable artifact.

---

## New Architectural Laws

> **Information gain does not imply epistemic progress.**

> **Statistical precision does not imply increased authority.**

> **Experiment value is proposition-relative.**

> **Experiment selection is a partial-order problem, not necessarily a total-order problem.**

> **An experiment can be highly informative while being epistemically irrelevant.**

---

## Test Coverage

- `tests/unit/test_epistemic_experiment_selection.py` — 20 tests
- 12 adversarial attacks
- Experiment dominance tests
- Pareto frontier tests
- Value separation tests
- Recommendation vs authorization tests
- Provenance tests

---

## The Epistemic Control Loop

The system now approaches a closed epistemic control loop:

```text
             ┌──────────────────────┐
             │      Proposition     │
             └──────────┬───────────┘
                        ↓
                 Evidence State
                        ↓
                  Epistemic Gaps
                        ↓
               Candidate Experiments
                        ↓
              ┌─────────────────────┐
              │ Epistemic Selection  │
              └──────────┬──────────┘
                         ↓
                    Governance
                         ↓
                    Execution
                         ↓
                      Evidence
                         │
                         └──────────────→ ...
```

The system's intelligence can now be used to decide what it should
investigate next without giving that intelligence authority over the
resulting truth.

---

## Unresolved Questions

1. Can the selection policy be derived from first principles rather
   than set as a governance parameter?

2. How should the system handle novel intervention types not in the
   current authority matrix?

3. Can the Pareto frontier computation scale to large candidate sets?

4. How should the system handle evidence from interventions that
   partially overlap in authority scope?

---

## The Central Research Question

> **Can the system identify which experiment would most reduce a
> specific epistemic limitation without confusing statistical usefulness
> with authority?**

The experiments demonstrate: **yes, within the current architecture**.
