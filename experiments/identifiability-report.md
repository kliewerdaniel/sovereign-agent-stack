# Mechanism Intervention & Identifiability Characterization

## Summary

- Total paired worlds tested: 27
- Feature interventions distinguishable: 92.6%
- Mechanism interventions distinguishable: 100.0%

## Interpretation

Both feature and mechanism interventions show some distinguishability.
The mechanisms are partially identifiable from the evidence.

---

## By Pair Type

| Pair Type | Total | Feature Dist. | Mech Dist. |
|---|---|---|---|
| confounding: pure signal vs signal + AR confounder | 9 | 100.0% | 100.0% |
| generative mechanism: signal vs autocorrelation | 9 | 77.8% | 100.0% |
| latent mechanism vs spurious correlation | 9 | 100.0% | 100.0% |

---

## By Sample Size

| n | Total | Feature Dist. | Mech Dist. |
|---|---|---|---|
| 126 | 9 | 100.0% | 100.0% |
| 252 | 9 | 88.9% | 100.0% |
| 504 | 9 | 88.9% | 100.0% |

---

## Architectural Finding

### The Intervention Hierarchy

The experiment establishes a clean evidence hierarchy:

```text
Observation
    │
    ▼
Feature Evidence
    │
    ├── feature ablation
    ├── permutation
    └── feature substitution
    │
    ▼
Representation Dependency
    │
    │
    └──────────────┐
                   ▼
             Mechanism Evidence
                   │
             ┌─────┼─────┐
             ▼     ▼     ▼
        mechanism  temporal  competing
        intervention ordering mechanisms
             │     │     │
             └─────┼─────┘
                   ▼
             Proposition Evidence
                   │
                   ▼
          Epistemic Evaluation
```

### The Authority Invariant

> **The system may only assert a mechanism when the experiment performed
> has authority over the mechanism being asserted.**

This is a deeper rule than 'don't overfit.' It means the epistemic architecture understands what kind of experiment is capable of answering what kind of question.

### Implications

1. Feature interventions alone cannot establish mechanism identity
2. Mechanism interventions can break observational equivalence
3. Paired worlds with identical observables should produce INCONCLUSIVE
4. More observations do not help unless they break the equivalence
5. The epistemic system needs both intervention types, separately tracked