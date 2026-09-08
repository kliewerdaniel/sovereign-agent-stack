# Experimental Design Authority Report

## Summary

- **Total experiments:** 33
- **Sufficient design rate:** 33.3%
- **Correct mechanism rate:** 6.1%
- **Design predicts success rate:** 18.2%

## By Hypothesis Type

| Hypothesis | Total | Sufficient Design | Correct Mechanism | Avg Disc. Power |
|-----------|-------|-------------------|-------------------|-----------------|
| exogenous_predictive_component | 3 | 100.0% | 66.7% | 0.60 |
| lagged_return_structure | 23 | 34.8% | 0.0% | 0.80 |
| spurious_correlation | 7 | 0.0% | 0.0% | 0.30 |

## Failure Taxonomy

| Failure Type | Count |
|-------------|-------|
| evaluator | 0 |
| evidence_sufficiency | 0 |
| experimental_design | 22 |
| governance | 0 |
| hypothesis_generation | 9 |
| semantic_mapping | 0 |

## Key Findings

1. **Experimental design matters**
   - The gap between hypothesis formation and experimental design is real
   - Discriminative power varies significantly across hypothesis types

2. **Confounders are the primary obstacle**
   - When confounders are present, discriminative power drops
   - The system can detect when an experiment cannot distinguish hypotheses

3. **Design sufficiency predicts success**
   - When the design is sufficient, the mechanism is more likely to be correct
   - This validates the Experimental Design Authority layer

## Architectural Law

> A proposition cannot inherit authority merely because the experiment 
> was successful. The experiment must be discriminative with respect 
> to the proposition and its relevant alternatives.

## The Extended Pipeline

```text
Observation
    ↓
Hypothesis
    ↓
Experimental Design ← NEW: confound analysis, discriminative power
    ↓
Intervention
    ↓
Observation of Difference
    ↓
Evidence
    ↓
Proposition
    ↓
Epistemic Judgment
    ↓
Governance
```
