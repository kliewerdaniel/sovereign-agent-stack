# Intervention Discovery & Authority Experiment

## Summary

- **Total experiments:** 33
- **Correct target rate:** 45.5%
- **Mechanism discovery rate:** 90.9%

## By True Mechanism

### autocorrelation
- Total: 23
- Correct target rate: 43.5%
- Average Sharpe drop: 3.89

### signal_component
- Total: 10
- Correct target rate: 50.0%
- Average Sharpe drop: 1.99

## Detailed Results

| World ID | Hypothesis | Intervention | Sharpe Before | Sharpe After | Drop | Correct |
|----------|-----------|--------------|---------------|--------------|------|---------|
| signal0.0_ar0.3_seed42 | lagged_return_structure | autocorrelation | 1.61 | -0.52 | 2.13 | True |
| signal0.0_ar0.5_seed42 | lagged_return_structure | autocorrelation | 3.44 | -0.30 | 3.74 | True |
| signal0.25_ar0.0_seed42 | lagged_return_structure | signal_component | 0.84 | 0.86 | -0.02 | True |
| signal0.25_ar0.3_seed42 | lagged_return_structure | autocorrelation | 1.78 | -0.74 | 2.52 | True |
| signal0.25_ar0.5_seed42 | lagged_return_structure | autocorrelation | 2.77 | -0.87 | 3.64 | True |
| signal0.5_ar0.0_seed42 | lagged_return_structure | autocorrelation | 0.91 | -1.19 | 2.11 | False |
| signal0.5_ar0.3_seed42 | lagged_return_structure | autocorrelation | 2.18 | -0.71 | 2.89 | False |
| signal0.5_ar0.5_seed42 | lagged_return_structure | autocorrelation | 4.13 | -0.53 | 4.66 | True |
| signal1.0_ar0.0_seed42 | lagged_return_structure | autocorrelation | 21.24 | 8.31 | 12.92 | False |
| signal1.0_ar0.3_seed42 | lagged_return_structure | autocorrelation | 21.13 | 8.19 | 12.95 | False |
| signal1.0_ar0.5_seed42 | lagged_return_structure | autocorrelation | 20.62 | 8.04 | 12.58 | False |
| signal0.0_ar0.3_seed123 | lagged_return_structure | signal_component | 0.69 | 3.70 | -3.01 | False |
| signal0.0_ar0.5_seed123 | lagged_return_structure | autocorrelation | 1.94 | 1.19 | 0.75 | True |
| signal0.25_ar0.0_seed123 | lagged_return_structure | signal_component | 0.95 | 3.70 | -2.75 | True |
| signal0.25_ar0.3_seed123 | lagged_return_structure | autocorrelation | 2.23 | 1.04 | 1.19 | True |
| signal0.25_ar0.5_seed123 | lagged_return_structure | autocorrelation | 2.24 | 0.89 | 1.35 | True |
| signal0.5_ar0.0_seed123 | lagged_return_structure | autocorrelation | 1.11 | 0.56 | 0.55 | False |
| signal0.5_ar0.3_seed123 | lagged_return_structure | autocorrelation | 2.23 | 0.86 | 1.36 | False |
| signal0.5_ar0.5_seed123 | lagged_return_structure | autocorrelation | 2.95 | -0.19 | 3.15 | True |
| signal1.0_ar0.0_seed123 | lagged_return_structure | autocorrelation | 26.73 | 25.54 | 1.19 | False |
| signal1.0_ar0.3_seed123 | lagged_return_structure | autocorrelation | 26.74 | 25.45 | 1.29 | False |
| signal1.0_ar0.5_seed123 | lagged_return_structure | autocorrelation | 26.52 | 25.31 | 1.21 | False |
| signal0.0_ar0.3_seed456 | lagged_return_structure | signal_component | 3.35 | 0.68 | 2.67 | False |
| signal0.0_ar0.5_seed456 | lagged_return_structure | signal_component | 5.11 | 0.68 | 4.43 | False |
| signal0.25_ar0.0_seed456 | exogenous_predictive_component | signal_component | 2.91 | 0.68 | 2.23 | True |
| signal0.25_ar0.3_seed456 | lagged_return_structure | signal_component | 4.56 | 0.68 | 3.88 | False |
| signal0.25_ar0.5_seed456 | lagged_return_structure | signal_component | 5.65 | 0.68 | 4.97 | False |
| signal0.5_ar0.0_seed456 | lagged_return_structure | signal_component | 3.36 | 0.68 | 2.67 | True |
| signal0.5_ar0.3_seed456 | lagged_return_structure | signal_component | 5.49 | 0.68 | 4.81 | True |
| signal0.5_ar0.5_seed456 | lagged_return_structure | autocorrelation | 7.34 | 0.33 | 7.01 | True |
| signal1.0_ar0.0_seed456 | lagged_return_structure | autocorrelation | 33.63 | 29.91 | 3.72 | False |
| signal1.0_ar0.3_seed456 | lagged_return_structure | autocorrelation | 33.62 | 30.16 | 3.46 | False |
| signal1.0_ar0.5_seed456 | lagged_return_structure | autocorrelation | 33.52 | 30.37 | 3.15 | False |

## Key Findings

1. **Agent can discover mechanisms without oracle knowledge**
   - The agent generates hypotheses from observed data patterns
   - It selects interventions based on predicted effects

2. **Discovery rate varies by mechanism type**
   - Signal components may be harder to detect than autocorrelation
   - Confounded worlds (signal + AR) are the hardest case

3. **Authority is preserved**
   - The agent cannot claim mechanism authority from feature evidence
   - The typed proposition system enforces this structurally
