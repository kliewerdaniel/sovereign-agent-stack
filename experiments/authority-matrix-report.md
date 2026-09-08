# Epistemic Authority Matrix

This matrix defines which interventions can inform which proposition types.

## Authority Rules

- **bootstrap** → generalization, predictive_relationship
- **feature_ablation** → feature_dependency, representation_dependency
- **feature_permutation** → feature_dependency, representation_dependency
- **feature_substitution** → feature_dependency, representation_dependency
- **holdout** → generalization, predictive_relationship
- **mechanism_amplification** → causal_claim, mechanism_dependency
- **mechanism_decorrelation** → causal_claim, mechanism_dependency
- **mechanism_removal** → causal_claim, mechanism_dependency
- **subsample** → generalization, predictive_relationship
- **temporal_perturbation** → feature_dependency, temporal_dependency

## Key Structural Rules

1. **Feature interventions cannot authorize mechanism claims**
   - `FEATURE_ABLATION` → `FEATURE_DEPENDENCY` (not `MECHANISM_DEPENDENCY`)

2. **Mechanism interventions can authorize mechanism claims**
   - `MECHANISM_REMOVAL` → `MECHANISM_DEPENDENCY`

3. **Holdout informs generalization, not mechanism**
   - `HOLDOUT` → `GENERALIZATION` (not `CAUSAL_CLAIM`)

4. **No single intervention type informs all propositions**
   - Each proposition type requires specific intervention types

## Impossibility Proofs

### More samples cannot overcome observational equivalence
**Type:** information_theoretic | **Result:** ✓ HOLDS
**Reasoning:** If two mechanisms produce identical observation distributions, no number of samples (tested up to 1000) can distinguish them. Observational equivalence is a property of the DGP, not the sample size.

### Higher Sharpe cannot overcome an invalid intervention
**Type:** semantic_scope | **Result:** ✓ HOLDS
**Reasoning:** Sharpe ratio measures risk-adjusted return. Even Sharpe > 3.0 does not imply mechanism identification. Performance evidence operates at the observation level; mechanism claims require mechanism-level evidence.

### Feature intervention cannot authorize a mechanism claim
**Type:** type_system | **Result:** ✓ HOLDS
**Reasoning:** Feature interventions operate on observable columns. Mechanism claims require evidence about latent generative components. Even with 10 features, feature-level evidence cannot establish mechanism-level claims without a valid mapping.

### DGP oracle cannot be counted as agent-discovered evidence
**Type:** epistemic_authority | **Result:** ✓ HOLDS
**Reasoning:** DGP knowledge is experimental harness authority, not agent authority. The agent must discover the mechanism through observation and intervention. Oracle-level mechanism interventions demonstrate what is possible in principle, not what the agent can discover autonomously.

### Mechanism evidence cannot automatically establish causality
**Type:** epistemic_scope | **Result:** ✓ HOLDS
**Reasoning:** Mechanism dependency shows that a mechanism is implicated. Causality requires additional evidence: temporal ordering, confound exclusion, and counterfactual reasoning. Mechanism evidence is one input to causal claims, not sufficient.

### Hypothesis support cannot automatically authorize execution
**Type:** governance_separation | **Result:** ✓ HOLDS
**Reasoning:** Epistemic status (SUPPORTED) is a necessary condition for execution but not sufficient. Governance evaluates additional factors: risk, uncertainty, externalities, and alignment. The epistemic layer bounds claims; the governance layer permits action.
