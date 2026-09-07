# Evidence Sufficiency Characterization Report

## Aggregate Metrics

- Total conditions: 1080
- Support rate: 0.0% (0)
- Inconclusive rate: 100.0% (1080)
- Refutation rate: 0.0% (0)
- False positive rate: 0.0% (0)
- False negative rate: 6.7% (72)
- Mechanism identification rate: 7.8%
- Governance acceptance rate: 0.0%

---

# Evidence Sufficiency Matrix

Epistemic outcomes across experimental dimensions.
Cells show: support% / inconclusive% / refutation% (n worlds).

## Sample Size: 126

| Signal Strength | Support % | Inconclusive % | Refutation % | n |
|---|---|---|---|---|
| 0.00 | 0.0% | 100.0% | 0.0% | 144 |
| 0.30 | 0.0% | 100.0% | 0.0% | 108 |
| 0.70 | 0.0% | 100.0% | 0.0% | 108 |

## Sample Size: 252

| Signal Strength | Support % | Inconclusive % | Refutation % | n |
|---|---|---|---|---|
| 0.00 | 0.0% | 100.0% | 0.0% | 144 |
| 0.30 | 0.0% | 100.0% | 0.0% | 108 |
| 0.70 | 0.0% | 100.0% | 0.0% | 108 |

## Sample Size: 504

| Signal Strength | Support % | Inconclusive % | Refutation % | n |
|---|---|---|---|---|
| 0.00 | 0.0% | 100.0% | 0.0% | 144 |
| 0.30 | 0.0% | 100.0% | 0.0% | 108 |
| 0.70 | 0.0% | 100.0% | 0.0% | 108 |


---

# Epistemic Operating Envelope

Regions where different epistemic outcomes dominate.

## World Type: confounded

- Total conditions: 324
- Support rate: 0.0%
- Inconclusive rate: 100.0%
- Refutation rate: 0.0%
- False positive rate: 0.0%

### By Sample Size

| n | Support % | Inconclusive % | Refutation % |
|---|---|---|---|
| 126 | 0.0% | 100.0% | 0.0% |
| 252 | 0.0% | 100.0% | 0.0% |
| 504 | 0.0% | 100.0% | 0.0% |

## World Type: known_signal

- Total conditions: 216
- Support rate: 0.0%
- Inconclusive rate: 100.0%
- Refutation rate: 0.0%
- False positive rate: 0.0%

### By Sample Size

| n | Support % | Inconclusive % | Refutation % |
|---|---|---|---|
| 126 | 0.0% | 100.0% | 0.0% |
| 252 | 0.0% | 100.0% | 0.0% |
| 504 | 0.0% | 100.0% | 0.0% |

## World Type: non_identifiable

- Total conditions: 324
- Support rate: 0.0%
- Inconclusive rate: 100.0%
- Refutation rate: 0.0%
- False positive rate: 0.0%

### By Sample Size

| n | Support % | Inconclusive % | Refutation % |
|---|---|---|---|
| 126 | 0.0% | 100.0% | 0.0% |
| 252 | 0.0% | 100.0% | 0.0% |
| 504 | 0.0% | 100.0% | 0.0% |

## World Type: null

- Total conditions: 108
- Support rate: 0.0%
- Inconclusive rate: 100.0%
- Refutation rate: 0.0%
- False positive rate: 0.0%

### By Sample Size

| n | Support % | Inconclusive % | Refutation % |
|---|---|---|---|
| 126 | 0.0% | 100.0% | 0.0% |
| 252 | 0.0% | 100.0% | 0.0% |
| 504 | 0.0% | 100.0% | 0.0% |

## World Type: wrong_mechanism

- Total conditions: 108
- Support rate: 0.0%
- Inconclusive rate: 100.0%
- Refutation rate: 0.0%
- False positive rate: 0.0%

### By Sample Size

| n | Support % | Inconclusive % | Refutation % |
|---|---|---|---|
| 126 | 0.0% | 100.0% | 0.0% |
| 252 | 0.0% | 100.0% | 0.0% |
| 504 | 0.0% | 100.0% | 0.0% |


---

# Monotonicity Analysis

Do stronger evidence conditions produce more decisive epistemic outcomes?

## Dimension: sample_size

**Monotonic**: YES

**Notes**: Support rate is monotonically increasing.

| Level | Support Rate |
|---|---|
| 126 | 0.0% |
| 252 | 0.0% |
| 504 | 0.0% |

## Dimension: signal_strength

**Monotonic**: YES

**Notes**: Support rate is monotonically increasing.

| Level | Support Rate |
|---|---|
| 0.0 | 0.0% |
| 0.3 | 0.0% |
| 0.7 | 0.0% |

## Dimension: search_budget

**Monotonic**: YES

**Notes**: Support rate is monotonically increasing.

| Level | Support Rate |
|---|---|
| 10 | 0.0% |
| 50 | 0.0% |

## Dimension: intervention_strength

**Monotonic**: YES

**Notes**: Support rate is monotonically increasing.

| Level | Support Rate |
|---|---|
| weak | 0.0% |
| strong | 0.0% |


---

# Failure Analysis

For every surprising transition, identify the likely cause.

Found 72 surprising transitions.

### unexpected_non_support: c0216

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -3.96 → -0.78 (Δ=-3.17). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -3.96 → -8.75 (Δ=4.79). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0217

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -2.25 → 0.75 (Δ=-3.01). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -2.25 → -7.62 (Δ=5.37). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0218

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 5.23
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -4.40 → 0.00 (Δ=-4.40). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-4.40 → -4.40). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -4.40 → 0.64 (Δ=-5.03). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -4.40. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -4.40 → -7.92 (Δ=3.52). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0219

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -3.96 → -0.72 (Δ=-3.24). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe persisted (-3.96 → -3.94). Evidence consistent with timing-invariant structure.

### unexpected_non_support: c0220

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -2.25 → 0.96 (Δ=-3.22). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe changed -2.25 → -1.70 (Δ=-0.55). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0221

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 5.23
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -4.40 → 0.00 (Δ=-4.40). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-4.40 → -4.40). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -4.40 → 0.50 (Δ=-4.90). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -4.40. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe changed -4.40 → -3.43 (Δ=-0.97). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0222

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -3.96 → -0.78 (Δ=-3.17). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -3.96 → -8.75 (Δ=4.79). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0223

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -2.25 → 0.75 (Δ=-3.01). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -2.25 → -7.62 (Δ=5.37). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0224

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 5.23
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -4.40 → 0.00 (Δ=-4.40). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-4.40 → -4.40). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -4.40 → 0.64 (Δ=-5.03). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -4.40. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -4.40 → -7.92 (Δ=3.52). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0225

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -3.96 → -0.72 (Δ=-3.24). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe persisted (-3.96 → -3.94). Evidence consistent with timing-invariant structure.

### unexpected_non_support: c0226

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -2.25 → 0.96 (Δ=-3.22). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe changed -2.25 → -1.70 (Δ=-0.55). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0227

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 5.23
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -4.40 → 0.00 (Δ=-4.40). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-4.40 → -4.40). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -4.40 → 0.50 (Δ=-4.90). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -4.40. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe changed -4.40 → -3.43 (Δ=-0.97). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0228

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -3.96 → -0.78 (Δ=-3.17). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -3.96 → -8.75 (Δ=4.79). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0229

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -2.25 → 0.75 (Δ=-3.01). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -2.25 → -7.62 (Δ=5.37). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0230

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 5.23
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -4.40 → 0.00 (Δ=-4.40). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-4.40 → -4.40). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -4.40 → 0.64 (Δ=-5.03). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -4.40. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -4.40 → -7.92 (Δ=3.52). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0231

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -3.96 → -0.72 (Δ=-3.24). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe persisted (-3.96 → -3.94). Evidence consistent with timing-invariant structure.

### unexpected_non_support: c0232

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -2.25 → 0.96 (Δ=-3.22). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe changed -2.25 → -1.70 (Δ=-0.55). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0233

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 5.23
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -4.40 → 0.00 (Δ=-4.40). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-4.40 → -4.40). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 20x. Sharpe changed -4.40 → 0.50 (Δ=-4.90). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -4.40. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-10 periods. Sharpe changed -4.40 → -3.43 (Δ=-0.97). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0234

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.44
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -3.96 → 0.00 (Δ=-3.96). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-3.96 → -3.96). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -3.96 → -0.78 (Δ=-3.17). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -3.96. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -3.96 → -8.75 (Δ=4.79). Evidence consistent with timing-sensitive strategy.

### unexpected_non_support: c0235

- World: known_signal
- Sample size: 252
- Signal strength: 0.7
- Agent Sharpe: 4.59
- Epistemic status: inconclusive

- Mechanism type: unknown
- Features used: ['close']
- Dependency measure: 0.10

**Investigation evidence**:
- Feature ablation: returns removed. Sharpe changed -2.25 → 0.00 (Δ=-2.25). Evidence consistent with feature contributing to outcome.
- Feature ablation: signal removed. Sharpe unchanged (-2.25 → -2.25). Evidence consistent with strategy not depending on this feature.
- Permutation test: returns shuffled 5x. Sharpe changed -2.25 → 0.75 (Δ=-3.01). Evidence consistent with temporal ordering carrying information.
- Competing mechanism: Signal ablation changed Sharpe by 0.00, momentum ablation by -2.25. Evidence ambiguous — strategy may depend on both or neither.
- Temporal perturbation: returns shifted 1-2 periods. Sharpe changed -2.25 → -7.62 (Δ=5.37). Evidence consistent with timing-sensitive strategy.
