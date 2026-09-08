# Proposition Evidence Matrix Report

## Summary

- Total conditions: 1080
- Path A (mechanism) and Path B (proposition) agree: 4.7%
- Path B more informative than Path A: 95.3%

### Path A Status Distribution (Mechanism → Frozen Evaluator)

- inconclusive: 1080 (100.0%)

### Path B Status Distribution (Proposition → Proposition Evaluation)

- inconclusive: 51 (4.7%)
- refuted: 996 (92.2%)
- supported: 33 (3.1%)

---

## Analysis by World Type

| World Type | Total | Agreement | B More Informative |
|---|---|---|---|
| confounded | 324 | 0.0% | 100.0% |
| known_signal | 216 | 0.0% | 100.0% |
| non_identifiable | 324 | 0.0% | 100.0% |
| null | 108 | 47.2% | 52.8% |
| wrong_mechanism | 108 | 0.0% | 100.0% |

---

## Analysis by Signal Strength

| Signal Strength | Total | Agreement | B More Informative |
|---|---|---|---|
| 0.00 | 432 | 11.8% | 88.2% |
| 0.30 | 324 | 0.0% | 100.0% |
| 0.70 | 324 | 0.0% | 100.0% |

---

## Analysis by Sample Size

| Sample Size | Total | Agreement | B More Informative |
|---|---|---|---|
| 126 | 360 | 2.5% | 97.5% |
| 252 | 360 | 6.7% | 93.3% |
| 504 | 360 | 5.0% | 95.0% |

---

## Architectural Finding

### The Semantic Impedance Mismatch

The experiment compares two paths:

**Path A**: Evidence → ObservedMechanismArtifact → Frozen Evaluator
**Path B**: Evidence → Proposition Evidence Bundle → Proposition Evaluation

If Path B produces more decisive outcomes (SUPPORTED/REFUTED) than Path A,
this indicates that the mechanism classification step is **lossy** —
information in the evidence is being discarded before it reaches the evaluator.

### Interpretation

Path B is more informative in 95.3% of conditions. This strongly suggests that the mechanism classification step is discarding evidence that is relevant to the proposition.

### Recommendation

1. If Path B >> Path A: enrich the evidence representation or bypass the mechanism classification step
2. If Path B ≈ Path A: the evidence itself is insufficient — investigate richer investigation types
3. If Path B is worse: the mechanism classification is actually filtering noise — preserve it
