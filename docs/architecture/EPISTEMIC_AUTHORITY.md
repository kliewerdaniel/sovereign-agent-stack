# Epistemic Authority — Architectural Contract

> **Status: FROZEN**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document is the canonical specification for the epistemic authority
subsystem of the Sovereign Agent Stack. It is an **executable contract**:
every law below is enforced by code, verified by tests, and defended by
the adversarial suite.

---

## Preamble

This architecture separates **what can be claimed** from **what is true**.

A proposition may be true and still be unauthorized. A proposition may
be false and still be supported by bad evidence. The purpose of this
subsystem is not to maximize classification accuracy. It is to ensure
that **no claim exceeds the authority of the experiment that produced it**.

The system is fail-closed: absence of authority is the default state.
Authority must be earned at every transition.

---

## The Epistemic Chain

```text
Observation → Hypothesis → Experimental Design → Intervention →
Observed Difference → Evidence → Proposition → Epistemic Judgment →
Governance
```

Each arrow is a semantic contract. Each transition must be earned.
No transition can be skipped.

---

## The Twelve Laws

### Law 1 — Observation does not imply explanation.

Raw data, no matter how voluminous, does not constitute understanding.
A time series of returns is not a mechanism. A correlation is not a cause.

**Enforcement:** The epistemic evaluator does not accept raw observations
as evidence. Evidence requires an intervention and an observed difference.

### Law 2 — Performance does not imply mechanism.

A strategy's Sharpe ratio is a performance metric, not a mechanism
attribution. High performance can arise from luck, overfitting, or
confounding.

**Enforcement:** `attack_high_sharpe` — Sharpe=20.62 is blocked at the
proposition boundary. HOLDOUT cannot inform MECHANISM_DEPENDENCY.

### Law 3 — A hypothesis does not imply an experiment.

Naming a mechanism does not authorize any particular experimental design.
The experiment must be discriminative with respect to the hypothesis and
its relevant alternatives.

**Enforcement:** `attack_correct_hypothesis_invalid_experiment` — correct
hypothesis + wrong intervention is blocked at experimental design.

### Law 4 — An experiment does not imply evidence.

Running an experiment does not guarantee that the resulting data
constitutes evidence for the intended proposition. The intervention must
have authority over the proposition's semantic scope.

**Enforcement:** The typed proposition system rejects evidence from
intervention types that cannot inform the proposition type.

### Law 5 — Evidence does not imply a proposition.

Evidence must be evaluated against a specific proposition. The evaluation
determines whether the evidence supports, refutes, or is inconclusive
with respect to that proposition.

**Enforcement:** `evaluate_typed_proposition()` requires both evidence
and a proposition. Evidence without a proposition is unevaluable.

### Law 6 — Evidence can only inform propositions within its authority scope.

An intervention of type T can only produce evidence for propositions
within the authority scope of T. Feature ablation cannot establish
mechanism claims. Holdout cannot establish causal claims.

**Enforcement:** The authority matrix `can_inform(intervention_type,
proposition_type) → bool` is structural, not statistical.

### Law 7 — A proposition cannot exceed the identifiability of its alternatives.

If two mechanisms produce observationally equivalent outcomes under all
available interventions, no proposition that distinguishes them can be
supported.

**Enforcement:** `attack_massive_sample` — observational equivalence
cannot be overcome by sample size. Discriminative power is bounded.

### Law 8 — DGP knowledge cannot become agent knowledge without an authorized epistemic path.

The experimental harness knows the true data-generating process. The agent
does not. The agent must discover mechanisms through observation and
intervention. Oracle-level knowledge cannot be counted as agent evidence.

**Enforcement:** `attack_dgp_oracle_leakage` — DGP knowledge is harness
authority, not agent authority.

### Law 9 — Confidence cannot substitute for evidence.

Agent self-reported confidence is not evidence. A confidence of 0.99 with
no authorized evidence is indistinguishable from a confidence of 0.01.

**Enforcement:** `attack_agent_confidence` — confidence without evidence
is blocked at the epistemic evaluator.

### Law 10 — Epistemic support does not imply execution authority.

A supported hypothesis is a claim about the world, not a permission to
act. Governance authority is independent of epistemic confidence.

**Enforcement:** The governance layer receives epistemic judgments but
applies independent criteria (risk, authority, provenance).

### Law 11 — Governance authority is independent of epistemic confidence.

A proposition with 99% confidence may be rejected by governance. A
proposition with 10% confidence may be accepted by governance (with
appropriate constraints). The two planes are separate.

**Enforcement:** Governance decisions record epistemic confidence as
input but do not derive from it.

### Law 12 — Every authority transition must be reconstructable from provenance.

Every judgment, every evidence bundle, every intervention, every decision
must be traceable to its source. Provenance is not optional metadata; it
is the audit trail that makes the system verifiable.

**Enforcement:** All artifacts are immutable dataclasses with provenance
fields. The provenance graph is queryable.

---

## The Three Blocking Boundaries

### PROPOSITION Boundary

```text
"This evidence cannot inform that kind of claim."
```

Triggered when:
- Evidence type is outside the proposition's authority scope
- Proposition requires evidence that does not exist
- Proposition exceeds the identifiability of its alternatives

### EXPERIMENTAL DESIGN Boundary

```text
"This experiment cannot discriminate among these hypotheses."
```

Triggered when:
- Intervention does not target the hypothesis mechanism
- Competing mechanisms predict equivalent outcomes
- Observational equivalence cannot be overcome

### EPISTEMIC EVALUATOR Boundary

```text
"No authorized evidence exists for this assertion."
```

Triggered when:
- All evidence is from wrong intervention types
- DGP knowledge is used as agent evidence
- Confidence is offered without evidence

---

## The Authority Hierarchy

```text
Level 0 — Impossible
    M1 and M2 observationally equivalent
    No available intervention distinguishes them
    Expected: INCONCLUSIVE

Level 1 — Observable
    M produces distinguishable observable consequences
    Expected: candidate evidence (not necessarily support)

Level 2 — Interventionally identifiable
    Available intervention separates M from relevant alternatives
    Expected: mechanism evidence

Level 3 — Replicated
    Multiple seeds, samples, and interventions converge
    Expected: strong mechanism evidence

Level 4 — Generalized
    Holdout / temporal replication succeeds
    Expected: generalization evidence

Level 5 — Proposition-authorized
    The proposition's required evidence contract is satisfied
    Expected: SUPPORTED
```

---

## The Asymmetry Principle

The system must satisfy:

```text
false positive ≈ 0    (under adversarial conditions)
true positive > 0     (under identifiable conditions)
```

A system with false positive = 0 and true positive = 0 is a perfect
firewall that prevents both bad knowledge and useful knowledge. This is
the failure mode of pathological conservatism.

The calibration experiment (see below) tests whether the architecture
can produce true positives without weakening the barriers that produce
false positives.

---

## The Computational Theory of Epistemic Boundaries

The 12 attacks establish:

```text
invalid semantic scope + infinite compute = invalid semantic scope
```

This is a computational theory of epistemic boundaries. More data, more
compute, more search, and better models cannot repair a semantically
invalid experiment. The boundary is structural, not statistical.

---

## Executable Specification

The adversarial suite (`tests/unit/test_epistemic_adversarial.py`) is the
executable specification for these laws. Every law maps to one or more
attack vectors. Every attack must be blocked at the correct boundary.

| Law | Attack | Blocked At |
|-----|--------|------------|
| 2 | high_sharpe | PROPOSITION |
| 7 | massive_sample | EXPERIMENTAL_DESIGN |
| 7 | huge_search_budget | EXPERIMENTAL_DESIGN |
| 6 | irrelevant_evidence | PROPOSITION |
| 3 | correct_hypothesis_invalid_experiment | EXPERIMENTAL_DESIGN |
| 7 | valid_experiment_non_identifiable | EXPERIMENTAL_DESIGN |
| 6 | correct_mechanism_insufficient_authority | PROPOSITION |
| 8 | dgp_oracle_leakage | EPISTEMIC_EVALUATOR |
| 9 | agent_confidence | EPISTEMIC_EVALUATOR |
| 6 | holdout_performance | PROPOSITION |
| 4 | convergent_non_discriminative | EXPERIMENTAL_DESIGN |
| 5 | conflicting_evidence | EPISTEMIC_EVALUATOR |

---

## Relationship to Sovereign Agent Fleet

This architecture is consistent with the broader Sovereign Agent Fleet
design:

| Fleet Layer | Epistemic Layer |
|-------------|-----------------|
| Model output | Hypothesis |
| Authorization | Experimental design |
| Verification | Epistemic evaluation |
| Provenance | Provenance |
| Governance | Governance |

In both architectures, model output is explicitly separated from
authorization and verification. The same separation appears in the
CHRIS game engine (narration-only server-side functions) and the
Rathnone auth-control plane (fail-closed, real TCP).

---

## Frozen API Surface

The following are frozen and must not change without a ratification
process:

- `EpistemicStatus`: SUPPORTED / REFUTED / INCONCLUSIVE
- `evaluate_hypothesis() → EpistemicEvaluation`
- `ObservedMechanismArtifact` structure
- `TypedProposition` structure
- `EvidenceBundle` structure
- `can_inform(intervention_type, proposition_type) → bool`
- `evaluate_typed_proposition() → TypedEvaluationResult`
- `DesignSufficiencyResult` structure
- The 12 laws above
- The three blocking boundaries
- The authority hierarchy (Levels 0-5)

---

## Next: The Calibration Experiment

The adversarial suite proves the negative: unauthorized claims are
blocked. The calibration experiment must prove the positive:
authorized claims can be reliably produced.

See `src/sas/quant/experiment/epistemic_calibration.py` for the
experimental design.

---

## The Central Research Question

> **Under what experimentally demonstrable conditions does this
> architecture permit an agent to claim that it knows something?**

And:

> **Can those conditions be characterized without granting the
> evaluator privileged knowledge of the answer?**

If these questions can be answered experimentally, the system moves
beyond a governed agent framework into a **machine-checkable epistemic
architecture**.
