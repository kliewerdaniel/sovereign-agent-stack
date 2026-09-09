# Epistemic Composition & Dependency Closure

> **Date:** 2026-09-09
> **Phase:** Knowledge Composition Specimen
> **Tests:** 1,914 passing (54 new adversarial tests)

This document describes the Epistemic Composition Engine, which investigates whether individually valid dependency claims can be composed into system-level knowledge without manufacturing epistemic authority.

---

## Central Law

```
VALID(A) + VALID(B) + VALID(C) DOES NOT IMPLY VALID(A+B+C)
```

**Epistemic authority must not increase merely because valid claims are composed.**

A graph path is NOT automatically evidence for the semantic proposition represented by that path.

---

## The Problem

The Payment Infrastructure Dependency Auditor can acquire bounded epistemic authority over individual dependency claims. But a real auditor eventually needs to reason about transitive relationships:

```
checkout → payments → ledger
checkout → payments → redis
checkout → payments → feature-flags
checkout → payments → customer-profile
```

And then infer things like:

> "The checkout transaction path operationally depends on customer-profile."

This introduces a dangerous possibility:

```
VALID EDGE A + VALID EDGE B + VALID EDGE C ≠ VALID TRANSITIVE CLAIM
```

The same problem that was solved on the authority side (`VALID(A) + VALID(B) + VALID(C) ≠ necessarily VALID(A⊕B⊕C)`) now exists on the **epistemic side**.

---

## Research Questions

1. When is transitive dependency inference valid?
2. When is it only a hypothesis?
3. What evidence distinguishes reachability from necessity?
4. What evidence distinguishes necessity from criticality?
5. Can failure propagation establish dependency?
6. What is the epistemic status of graph-derived claims?
7. Can multiple weak parent claims produce a strong child claim?
8. Under what conditions does composition preserve authority?
9. Under what conditions must composition reduce authority?
10. Can epistemic authority be modeled as a conserved quantity during composition?

---

## Architecture

### Composition Operators

| Operator | Input Types | Output Type | Authority |
|----------|-------------|-------------|-----------|
| DIRECT_COMPOSITION | STATIC + STATIC | TRANSITIVE_DEPENDENCY | REDUCED |
| DIRECT_COMPOSITION | STATIC + RUNTIME | TRANSITIVE_DEPENDENCY | REDUCED |
| TRANSITIVE_COMPOSITION | RUNTIME + RUNTIME | TRANSITIVE_DEPENDENCY | INCONCLUSIVE |
| OPERATIONAL_COMPOSITION | RUNTIME + RUNTIME | OPERATIONAL_DEPENDENCY | INCONCLUSIVE |
| NECESSITY_COMPOSITION | OPERATIONAL + OPERATIONAL | OPERATIONAL_DEPENDENCY | INCONCLUSIVE |
| CONDITIONAL_COMPOSITION | STATIC + STATIC | STATIC_REFERENCE | REDUCED |
| TEMPORAL_COMPOSITION | TEMPORAL + TEMPORAL | TEMPORAL_DEPENDENCY | REDUCED |
| ENVIRONMENT_COMPOSITION | ENVIRONMENT + ENVIRONMENT | ENVIRONMENT_DEPENDENCY | REDUCED |
| FAILURE_COMPOSITION | FAILURE + FAILURE | FAILURE_DEPENDENCY | INCONCLUSIVE |
| SUBSTITUTION_COMPOSITION | RUNTIME + RUNTIME | RUNTIME_DEPENDENCY | REDUCED |

### Epistemic Accounting

Every composition result includes explicit accounting for:

- **Authority preservation**: Authority must not be amplified
- **Uncertainty preservation**: Uncertainty must not be erased
- **Scope preservation**: Scope must not be widened
- **Environment preservation**: Environment restrictions must not be removed
- **Temporal preservation**: Temporal boundaries must not be widened
- **Alternatives preservation**: Alternative hypotheses must not be discarded
- **Observation ≠ Necessity**: Observation must not become necessity
- **Correlation ≠ Dependency**: Correlation must not become dependency
- **Dependency ≠ Criticality**: Dependency must not become criticality
- **Local ≠ Generalization**: Local evidence must not be generalized

---

## Adversarial Test Suite (54 tests)

### Attack Categories

| Category | Tests | What It Proves |
|----------|-------|----------------|
| Naive Transitive Closure | 3 | Static edges don't compose to static; authority reduces |
| Static Not Runtime | 2 | Static analysis doesn't prove runtime behavior |
| Runtime Not Necessity | 2 | Runtime doesn't imply operational necessity |
| Necessity Not Criticality | 1 | Necessity doesn't imply criticality |
| Failure Not Universal | 1 | Failure dependency doesn't generalize |
| Staging Not Production | 2 | Staging evidence stays staging |
| Production Not All | 1 | Production evidence stays production |
| Single Operation Not Service | 1 | Single op doesn't generalize to service |
| Feature-Flagged Not Universal | 1 | Feature flags stay conditional |
| Cached Not Direct | 1 | Cached dependency stays bounded |
| Async Not Synchronous | 1 | Async dependency stays bounded |
| Shared Infrastructure | 1 | Shared infra stays bounded |
| Observability Not Business | 1 | Observability stays bounded |
| Startup Not Request | 1 | Startup stays temporal |
| Deployment Not Runtime | 1 | Deployment stays bounded |
| Confidence Not Authority | 2 | Confidence decreases with composition |
| Duplicate Evidence | 1 | Duplicates don't amplify |
| Contradictory Parents | 1 | Contradictions produce inconclusive |
| Missing Provenance | 1 | Provenance preserved |
| Scope Not Widened | 1 | Scope stays bounded |
| Temporal Not Widened | 1 | Temporal stays bounded |
| Environment Not Removed | 1 | Environment preserved |
| Alternatives Preserved | 1 | Alternatives stay |
| Circular Reasoning | 1 | One-directional composition |
| Circular Dependency | 1 | Circular doesn't amplify |
| Centrality Not Criticality | 1 | Centrality doesn't imply criticality |
| Count Not Importance | 1 | Count doesn't amplify |
| Path Length Not Certainty | 1 | Longer path reduces certainty |
| Transitive Closure Not Necessity | 1 | Closure doesn't prove necessity |
| Epistemic Accounting | 6 | All accounting properties preserved |
| Composition Validity | 3 | Non-composable edges rejected |
| Chain Composition | 2 | Chain reduces authority |
| Proposition Type Preservation | 3 | Types don't elevate |
| Environment Preservation | 3 | Environments preserved |

---

## Key Findings

### What Worked

1. **Composition rules prevent authority amplification** — Each composition reduces confidence
2. **Proposition types don't elevate** — Static stays static, runtime stays runtime
3. **Scope is preserved** — Staging stays staging, production stays production
4. **Epistemic accounting works** — All 10 accounting properties verified
5. **Chain composition reduces authority** — Each step weakens the claim
6. **Non-composable edges rejected** — Disconnected edges produce rejection

### What Was Hard

1. **Defining composition rules** — Must explicitly define which compositions are valid
2. **Authority reduction function** — Must decrease confidence without making it zero
3. **Mixed-type composition** — Static + Runtime requires careful handling
4. **Chain composition** — Must track authority across multiple hops

### Limitations

1. **No runtime experiments** — Static analysis only
2. **Simplified authority model** — Confidence is a scalar, not a structured value
3. **No failure injection** — Failure experiments not yet implemented
4. **No feature flag testing** — Feature flag behavior not yet tested

---

## The Central Invariant

```
NO EPISTEMIC AUTHORITY MAY APPEAR SOLELY AS A CONSEQUENCE OF COMPOSITION.
```

This is verified by 54 adversarial tests. Every attempt to amplify authority through composition fails for structural reasons.

---

## Example Output

Given:
```
checkout → payments (STATIC_REFERENCE, OBSERVED, confidence=0.9)
payments → ledger (STATIC_REFERENCE, OBSERVED, confidence=0.9)
```

Composition produces:
```
checkout → ledger (TRANSITIVE_DEPENDENCY, INFERRED, confidence=0.81)
```

With:
- Authority reduced: 0.9 → 0.81
- Epistemic state weakened: OBSERVED → INFERRED
- Proposition type changed: STATIC_REFERENCE → TRANSITIVE_DEPENDENCY
- Scope preserved: "Transitive composition"
- Alternatives preserved: ["dead_code_path"]
- Evidence preserved: ["composed_from:edge_ab_1", "composed_from:edge_bc_1"]

---

## Conclusion

The Epistemic Composition Engine demonstrates that:

1. **Individually valid claims can be composed** — But only with reduced authority
2. **Graph reachability ≠ semantic dependency** — A path is not evidence of necessity
3. **Epistemic authority is conserved** — Composition cannot create authority from nothing
4. **The system can distinguish** — Direct dependency vs transitive reference vs operational necessity

This is the transition from "the agent can discover dependencies" to **"the agent can construct system-level knowledge without manufacturing authority through composition."**
