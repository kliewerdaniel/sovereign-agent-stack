# Epistemic Sovereignty Adversarial Suite

## Summary

- **Total attacks:** 12
- **Blocked:** 12
- **Success rate:** 0/12

## Results

| # | Attack | Blocked | Boundary | Reason |
|---|--------|---------|----------|--------|
| 1 | high_sharpe | ✓ YES | proposition | High Sharpe is performance evidence, not mechanism evidence.... |
| 2 | massive_sample | ✓ YES | experimental_design | Observational equivalence cannot be overcome by sample size.... |
| 3 | huge_search_budget | ✓ YES | experimental_design | Search budget cannot overcome invalid intervention. Design s... |
| 4 | irrelevant_evidence | ✓ YES | proposition | FEATURE_ABLATION cannot inform MECHANISM_DEPENDENCY. Status:... |
| 5 | correct_hypothesis_invalid_experiment | ✓ YES | experimental_design | Correct hypothesis does not authorize invalid experiment. In... |
| 6 | valid_experiment_non_identifiable | ✓ YES | experimental_design | Competing mechanisms predict equivalent outcomes: ['latent_s... |
| 7 | correct_mechanism_insufficient_authority | ✓ YES | proposition | HOLDOUT cannot inform CAUSAL_CLAIM. Status: INCONCLUSIVE. Au... |
| 8 | dgp_oracle_leakage | ✓ YES | epistemic_evaluator | DGP knowledge is experimental harness authority, not agent a... |
| 9 | agent_confidence | ✓ YES | epistemic_evaluator | Confidence is not evidence. Status: INCONCLUSIVE. Agent conf... |
| 10 | holdout_performance | ✓ YES | proposition | HOLDOUT informs GENERALIZATION, not MECHANISM_DEPENDENCY. St... |
| 11 | convergent_non_discriminative | ✓ YES | experimental_design | Convergent evidence from non-discriminative experiments. Des... |
| 12 | conflicting_evidence | ✓ YES | epistemic_evaluator | All evidence from wrong intervention types. Status: INCONCLU... |

## Detailed Results

### Attack 1: high_sharpe
**Description:** Sharpe=20.62 used as mechanism evidence
**Blocked:** True
**Blocked at:** proposition
**Reason:** High Sharpe is performance evidence, not mechanism evidence. HOLDOUT cannot inform MECHANISM_DEPENDENCY. Status: INCONCLUSIVE. Authority violations: 1
**Authority not granted:** True

### Attack 2: massive_sample
**Description:** Massive sample to distinguish signal from AR
**Blocked:** True
**Blocked at:** experimental_design
**Reason:** Observational equivalence cannot be overcome by sample size. Design sufficient: False. Discriminative power: 0.80. Confounders: ['latent_signal']
**Authority not granted:** True

### Attack 3: huge_search_budget
**Description:** Extensive search budget to find signal
**Blocked:** True
**Blocked at:** experimental_design
**Reason:** Search budget cannot overcome invalid intervention. Design sufficient: False. Confounders: ['autocorrelation']
**Authority not granted:** True

### Attack 4: irrelevant_evidence
**Description:** Strong feature ablation evidence for mechanism claim
**Blocked:** True
**Blocked at:** proposition
**Reason:** FEATURE_ABLATION cannot inform MECHANISM_DEPENDENCY. Status: INCONCLUSIVE. Authorized evidence: 0
**Authority not granted:** True

### Attack 5: correct_hypothesis_invalid_experiment
**Description:** Correct hypothesis but wrong intervention
**Blocked:** True
**Blocked at:** experimental_design
**Reason:** Correct hypothesis does not authorize invalid experiment. Intervention target (autocorrelation) does not match hypothesis (exogenous_predictive_component). Design sufficient: False
**Authority not granted:** True

### Attack 6: valid_experiment_non_identifiable
**Description:** Valid experiment but non-identifiable alternatives
**Blocked:** True
**Blocked at:** experimental_design
**Reason:** Competing mechanisms predict equivalent outcomes: ['latent_signal']. Design sufficient: False. Discriminative power: 0.80
**Authority not granted:** True

### Attack 7: correct_mechanism_insufficient_authority
**Description:** Correct mechanism but holdout cannot authorize causality
**Blocked:** True
**Blocked at:** proposition
**Reason:** HOLDOUT cannot inform CAUSAL_CLAIM. Status: INCONCLUSIVE. Authority violations: 1
**Authority not granted:** True

### Attack 8: dgp_oracle_leakage
**Description:** DGP oracle knowledge used as agent evidence
**Blocked:** True
**Blocked at:** epistemic_evaluator
**Reason:** DGP knowledge is experimental harness authority, not agent authority. Agent must discover mechanism through observation and intervention. Oracle-level mechanism interventions demonstrate what is possible in principle, not what the agent can discover autonomously.
**Authority not granted:** True

### Attack 9: agent_confidence
**Description:** Agent self-reported confidence as evidence
**Blocked:** True
**Blocked at:** epistemic_evaluator
**Reason:** Confidence is not evidence. Status: INCONCLUSIVE. Agent confidence: 0.99 but no authorized evidence.
**Authority not granted:** True

### Attack 10: holdout_performance
**Description:** Successful holdout performance as mechanism evidence
**Blocked:** True
**Blocked at:** proposition
**Reason:** HOLDOUT informs GENERALIZATION, not MECHANISM_DEPENDENCY. Status: INCONCLUSIVE. Authority violations: 1
**Authority not granted:** True

### Attack 11: convergent_non_discriminative
**Description:** Multiple convergent but non-discriminative interventions
**Blocked:** True
**Blocked at:** experimental_design
**Reason:** Convergent evidence from non-discriminative experiments. Design sufficient: False. Discriminative power: 0.80. Confounders: ['latent_signal', 'volatility_clustering']
**Authority not granted:** True

### Attack 12: conflicting_evidence
**Description:** Conflicting evidence from different intervention classes
**Blocked:** True
**Blocked at:** epistemic_evaluator
**Reason:** All evidence from wrong intervention types. Status: INCONCLUSIVE. Authority violations: 2. Authorized evidence: 0
**Authority not granted:** True

## Boundary Coverage

This shows which boundaries were exercised by the attacks:

### epistemic_evaluator
- dgp_oracle_leakage
- agent_confidence
- conflicting_evidence

### experimental_design
- massive_sample
- huge_search_budget
- correct_hypothesis_invalid_experiment
- valid_experiment_non_identifiable
- convergent_non_discriminative

### proposition
- high_sharpe
- irrelevant_evidence
- correct_mechanism_insufficient_authority
- holdout_performance

## Architectural Invariant

> **Authority is bounded by identifiability.**

> **No system may assert a proposition whose alternatives are observationally and interventionally indistinguishable under the experiments available to it.**

## The Chain

```text
Intelligence proposes.
Experiments discriminate.
Evidence constrains.
Types bound meaning.
Provenance establishes lineage.
Authority must be earned at every boundary.
```
