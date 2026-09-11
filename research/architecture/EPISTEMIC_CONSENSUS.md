# Epistemic Consensus, Verifier Disagreement, and Authority Reconciliation

> **Status: ACTIVE**
> **Version: 1.0.0**
> **Last updated: 2026-09-08**

This document specifies the consensus and disagreement resolution subsystem
of the Sovereign Agent Stack. It extends the epistemic architecture to
handle multiple independent verifiers that may disagree about epistemic
states.

---

## Preamble

The previous architecture established that:

- An agent can propose a proposition
- Experiments can generate evidence
- An immutable state machine can accumulate authority
- An independent verifier can reconstruct whether authority was earned

This architecture addresses the next boundary:

> What happens when multiple independently valid verifiers produce
> different results?

The system does NOT resolve this by making one verifier the "real"
verifier. That would simply relocate the authority root.

The purpose of this subsystem is to establish whether epistemic
authority can remain bounded when independent authorities disagree.

---

## The Epistemic Chain (Extended)

```text
Observation → Hypothesis → Experimental Design → Intervention →
Observed Difference → Evidence → Proposition → Epistemic Judgment →
Governance

Extended with:

Evidence → Epistemic State Machine → Immutable State → Attestation
    → Multiple Independent Verifiers → Verification Assertions
    → Structured Comparison → Agreement / Divergence Classification
    → Epistemic Conflict or Consensus Artifact
    → Governance → Authorization → Execution
```

---

## Problem Statement

When two independently valid verifiers disagree, the system must
determine what it is actually entitled to conclude.

Disagreement may arise from:

1. Different evidence
2. Different provenance
3. Different proposition interpretation
4. Different epistemic rule versions
5. Different authority policies
6. Different intervention semantics
7. Different reconstruction algorithms
8. Different lifecycle assumptions
9. Different available artifacts
10. Actual verification failure

The system must preserve these distinctions.

---

## Verifier Identity

### Concept

An immutable identifier that establishes:

> Which verifier and semantic regime produced this verification result?

### Invariants

- Verifier identity does NOT itself establish epistemic authority
- Identity is NOT equivalent to trust
- Same identity → derived results (not independent)
- Different identity ≠ independent results

### Fields

- `verifier_id` — unique identifier
- `implementation_id` — implementation identifier
- `implementation_version` — implementation version
- `epistemic_rule_version` — epistemic rule version
- `proposition_semantics_version` — proposition semantics version
- `intervention_semantics_version` — intervention semantics version
- `provenance_rules_version` — provenance rules version
- `lifecycle_rules_version` — lifecycle rules version

---

## Verification Assertions

### Concept

An immutable structure representing what a verifier actually
established. Does NOT simply store `status = SUPPORTED`. It preserves
the derivation basis.

### Invariants

- A verifier should be able to say:
  - `mechanism = VERIFIED`
  - `generalization = UNRESOLVED`
  - `causal_authority = ABSENT`
- Rather than collapsing the entire epistemic state into one label

### Fields

- `assertion_id` — unique identifier
- `verifier_identity` — the verifier's identity
- `attestation_hash` — hash of the attestation being verified
- `verified_dimensions` — dimension-specific verified results
- `failed_dimensions` — dimension-specific failed results
- `unresolved_dimensions` — dimension-specific unresolved results
- `verification_trace_hash` — hash of the verification trace
- `semantic_rule_version` — semantic rule version used
- `evidence_refs` — references to evidence
- `provenance_refs` — references to provenance
- `overall_status` — overall verification status
- `result_hash` — self-hash

---

## Disagreement Taxonomy

### Classification

| Class | Meaning |
|-------|---------|
| `AGREEMENT` | Verifiers agree on all dimensions |
| `EVIDENCE_DIVERGENCE` | Different evidence sets |
| `PROVENANCE_DIVERGENCE` | Different provenance |
| `SEMANTIC_DIVERGENCE` | Different semantic rule versions |
| `RULE_VERSION_DIVERGENCE` | Different epistemic rule versions |
| `AUTHORITY_POLICY_DIVERGENCE` | Different authority policies |
| `LIFECYCLE_DIVERGENCE` | Different lifecycle rules |
| `RECONSTRUCTION_DIVERGENCE` | Different reconstruction results |
| `UNRESOLVED_VERIFICATION_CONFLICT` | Cannot classify disagreement |

### Deterministic Classification

The classification is deterministic based on structural comparison:

1. Different attestation → `UNRESOLVED_VERIFICATION_CONFLICT`
2. Different evidence → `EVIDENCE_DIVERGENCE`
3. Different provenance → `PROVENANCE_DIVERGENCE`
4. Different semantics → `SEMANTIC_DIVERGENCE`
5. Different rules → `RULE_VERSION_DIVERGENCE`
6. Different lifecycle → `LIFECYCLE_DIVERGENCE`
7. Dimension disagreement → `RECONSTRUCTION_DIVERGENCE`
8. All dimensions agree → `AGREEMENT`

---

## Verifier Comparison

### Concept

Deterministic comparison of two verification assertions. Operates
structurally, not just on final status labels.

### Structural Comparison

- `same_attestation` — same attestation hash
- `same_proposition` — same proposition
- `same_evidence` — same evidence set
- `same_semantics` — same semantic rule version
- `same_rules` — same epistemic rule version
- `same_lifecycle` — same lifecycle rules
- `same_provenance` — same provenance

### Dimension-Level Comparison

- `agreement_dimensions` — dimensions with same status
- `disagreement_dimensions` — dimensions with different status

---

## Independence Relationships

### Classification

| Relationship | Meaning |
|--------------|---------|
| `INDEPENDENT` | Verifiers are independent |
| `DERIVED_FROM` | One derives from the other |
| `WRAPS` | One wraps the other |
| `REUSES` | One reuses the other |
| `SHARES_IMPLEMENTATION` | Same implementation |
| `SHARES_RULE_ENGINE` | Same rule engine |
| `SHARES_EVALUATOR` | Same evaluator |
| `SHARES_EVIDENCE` | Same evidence |
| `UNKNOWN` | Cannot determine |

### Determined By Provenance

Independence is established through:
- Implementation identity
- Rule engine version
- Evidence overlap

NOT through self-assertion.

---

## Epistemic Conflict

### Concept

Produced when two verifiers produce incompatible results under
compatible semantics. NOT resolved by majority vote.

### Invariants

- A valid minority disagreement must not be erased by majority consensus
- An unresolved verifier disagreement is not equivalent to refutation
- Independent disagreement must preserve uncertainty rather than manufacture certainty

### Fields

- `conflict_id` — unique identifier
- `proposition_id` — proposition being evaluated
- `assertions` — assertions involved
- `common_evidence` — shared evidence
- `divergent_evidence` — different evidence
- `semantic_regime` — semantic regime
- `conflicting_dimensions` — dimensions in conflict
- `possible_resolution_paths` — possible ways to resolve
- `unresolved` — whether conflict is unresolved

---

## Epistemic Consensus

### Concept

Derived artifact representing the relationship between verifiers.

NOT a scalar `consensus_score`. Instead a structural representation
of agreement and disagreement.

### Invariants

- A consensus artifact must never simply contain `consensus = true`
- It must contain the derivation basis for that conclusion
- Consensus is a derived artifact, not an authority root
- Consensus cannot be stronger than the independence of its constituent verifiers

### Fields

- `consensus_id` — unique identifier
- `proposition_id` — proposition being evaluated
- `assertion_refs` — references to assertions
- `comparison_refs` — references to comparisons
- `agreement_dimensions` — dimensions with agreement
- `disagreement_dimensions` — dimensions with disagreement
- `unresolved_conflicts` — unresolved conflicts
- `semantic_regime` — semantic regime
- `independence_evidence` — evidence of independence
- `provenance_hash` — provenance hash
- `derivation_hash` — derivation hash
- `has_consensus` — whether consensus exists
- `consensus_basis` — basis for consensus

---

## Consensus is a Partial Order

The system does NOT implement a scalar:

```python
consensus_score = 0.87  # NO
```

Instead it represents the relationship structurally:

```text
A agrees with B on:
  mechanism
  temporal

A disagrees with B on:
  generalization

C cannot verify:
  causal

D uses incompatible semantic rules
```

This is a graph / relation structure, not a score.

---

## The Twenty-Three Laws

### Law 1 — Verifier agreement is not epistemic truth.

Multiple verifiers agreeing does not make a proposition true.
It only means multiple implementations produced the same result.

### Law 2 — Verifier disagreement is itself an epistemic artifact.

Disagreement is data. It must be classified, not resolved away.

### Law 3 — Identity multiplicity does not imply epistemic independence.

100 verifier identities backed by the same implementation are not
100 independent authorities.

### Law 4 — Consensus cannot be stronger than the independence of its constituent verifiers.

If all verifiers share the same implementation, consensus does not
increase epistemic authority.

### Law 5 — Historical verification does not imply current semantic agreement.

A verifier using rule version 1.0.0 and a verifier using version 2.0.0
may produce different results for the same historical attestation.

### Law 6 — A valid minority disagreement must not be erased by majority consensus.

9 verifiers saying SUPPORTED and 1 saying INCONCLUSIVE must not
collapse to SUPPORTED.

### Law 7 — An unresolved verifier disagreement is not equivalent to refutation.

Disagreement means uncertainty, not falsity.

### Law 8 — Evidence divergence is distinct from verification disagreement.

Different evidence sets produce different epistemic observation points,
not necessarily disagreement about history.

### Law 9 — Semantic divergence is distinct from implementation disagreement.

Different rule versions produce different semantic regimes, not
necessarily implementation bugs.

### Law 10 — Governance disagreement does not invalidate epistemic agreement.

Two verifiers may agree on mechanism while two governance policies
disagree on execution.

### Law 11 — Consensus is a derived artifact, not an authority root.

Consensus must be derived from independently verifiable assertions.
It cannot be asserted.

### Law 12 — Epistemic independence must be established by provenance rather than asserted by participants.

A verifier claiming "I am independent" is not evidence of independence.

### Law 13 — A verifier cannot inherit authority merely by inheriting the identity of another verifier.

Identity inheritance does not imply authority inheritance.

### Law 14 — No epistemic authority may increase solely because more identities repeat the same conclusion.

100 correlated verifiers are not more authoritative than 1.

### Law 15 — Independent disagreement must preserve uncertainty rather than manufacture certainty.

A: SUPPORTED, B: REFUTED must not resolve to SUPPORTED, REFUTED, or 50/50.

### Law 16 — Verification agreement is not epistemic agreement.

Two verifiers may agree on verification while disagreeing on
epistemic substance.

### Law 17 — Epistemic agreement is not governance agreement.

Two verifiers may agree on mechanism while governance disagrees on
authorization.

### Law 18 — Governance agreement is not execution authorization.

Governance agreement is necessary but not sufficient for execution.

### Law 19 — A verifier cannot authorize execution merely by verifying a proposition.

Verification and authorization are separate boundaries.

### Law 20 — A consensus artifact cannot authorize execution merely by existing.

Consensus is a description of agreement, not an authorization.

### Law 21 — A conflict artifact cannot prohibit execution merely by existing.

Conflict is a description of disagreement, not a prohibition.

### Law 22 — Historical verification does not imply current re-evaluation.

Verifying a historical state under historical rules is different from
evaluating under current rules.

### Law 23 — Current re-evaluation must not rewrite historical verification.

Current rules must not retroactively mutate the meaning of historical
states.

---

## Attack Coverage

### Attack 1 — Majority Vote

**Setup:** 9 verifiers → VALID, 1 verifier → INCONCLUSIVE

**Result:** System does NOT override the minority. Disagreement is
preserved.

**Classification:** `RECONSTRUCTION_DIVERGENCE`

### Attack 2 — One Strict Verifier

**Setup:** Verifier A accepts, Verifier B applies stricter rules and rejects

**Result:** System does NOT conclude "A has more votes." Disagreement
is preserved.

**Classification:** `SEMANTIC_DIVERGENCE`

### Attack 3 — Different Rule Versions

**Setup:** Verifier A uses rules v1, Verifier B uses rules v2

**Result:** System classifies as `SEMANTIC_DIVERGENCE`, not as one being
wrong.

### Attack 4 — Evidence Divergence

**Setup:** Verifier A has E1,E2,E3. Verifier B has E1,E2,E3,E4

**Result:** System distinguishes same historical state from new evidence
state.

**Classification:** `EVIDENCE_DIVERGENCE`

### Attack 5 — Provenance Divergence

**Setup:** Two evidence artifacts with same content but different provenance

**Result:** System detects they are not interchangeable.

**Classification:** `PROVENANCE_DIVERGENCE`

### Attack 6 — Semantic Equivalence

**Setup:** Two verifiers with different implementations but identical declared semantics

**Result:** System reaches epistemic agreement despite implementation differences.

**Classification:** `AGREEMENT`

### Attack 7 — Implementation Diversity

**Setup:** Two genuinely different verifier implementations

**Result:** System establishes that implementation diversity can coexist
with semantic agreement.

**Classification:** `AGREEMENT`

### Attack 8 — Correlated Verifiers

**Setup:** Three verifiers that are wrappers around the same evaluator

**Result:** System does NOT treat 3 identical correlated implementations
as 3 independent verifiers.

**Classification:** `SHARES_IMPLEMENTATION`

### Attack 9 — Sybil Verifiers

**Setup:** 100 verifier identities backed by the same implementation

**Result:** System rejects the implication: 100 identities ≠ 100
independent authorities.

**Classification:** `SHARES_IMPLEMENTATION`

### Attack 10 — Self-Attested Independence

**Setup:** A verifier claims "I am independent"

**Result:** System does not trust the claim. Independence must be
established through provenance.

**Classification:** `UNKNOWN` (not `INDEPENDENT`)

### Attack 11 — Valid Minority

**Setup:** Verifier A: VALID, Verifier B: VALID, Verifier C: INCONCLUSIVE

**Result:** System preserves the gap. Consensus does not erase epistemic
uncertainty.

### Attack 12 — Valid Contradiction

**Setup:** Verifier A: VALID, Verifier B: INVALID

**Result:** System produces structured contradiction object. Does NOT
resolve by majority vote.

**Classification:** `RECONSTRUCTION_DIVERGENCE`

### Attack 13 — Governance Conflict

**Setup:** Two verifiers agree mechanism=VERIFIED. Two governance
policies disagree.

**Result:** System preserves epistemic agreement while noting governance
disagreement.

### Attack 14 — Verification vs Re-Evaluation

**Setup:** Verifier A verifies historical state under historical rules.
Verifier B evaluates same evidence under current rules.

**Result:** System distinguishes `HISTORICAL_VERIFICATION` from
`CURRENT_RE_EVALUATION`.

### Attack 15 — Partial Agreement

**Setup:** Verifier A: mechanism=REPLICATED, generalization=UNRESOLVED.
Verifier B: mechanism=REPLICATED, generalization=VERIFIED.

**Result:** System reports agreement on mechanism, disagreement on
generalization.

### Attack 16 — Compatible Partial States

**Setup:** Verifier A: mechanism=VERIFIED, generalization=UNRESOLVED.
Verifier B: mechanism=VERIFIED, generalization=VERIFIED.

**Result:** System classifies as partial agreement, not contradiction.

### Attack 17 — Different Available Artifacts

**Setup:** Verifier A cannot access E4. Verifier B can access E4.

**Result:** System represents knowledge boundary as distinct from
verification failure.

### Attack 18 — Missing Semantics

**Setup:** Verifier B has evidence but cannot interpret intervention
semantics.

**Result:** System produces `INCONCLUSIVE`, not `REFUTED`.

### Attack 19 — Forged Consensus

**Setup:** Malicious artifact claiming "Verifier A and B agree"

**Result:** System does not trust the consensus artifact. Consensus must
be derived from independently verifiable assertions.

### Attack 20 — Consensus Forgery

**Setup:** Valid assertions from A and B, forged consensus object claiming
they agree.

**Result:** System reconstructs the comparison itself. Consensus is a
derived artifact.

---

## Trust Boundaries

### What the Verifier Trusts

- Artifacts whose integrity can be independently validated
- Evidence with verifiable provenance
- Transitions that follow from evidence authority
- States that can be reconstructed from artifacts

### What the Verifier Does NOT Trust

- Agent self-report
- Model output
- Evaluator claims
- State labels
- Confidence values
- Execution environment claims
- Self-attested identity claims
- Consensus artifacts (must be derived)

### What Must Be Independently Reconstructed

- State from evidence
- Transition authority from evidence authority
- Consensus from assertions
- Independence from provenance

### What Is Merely Integrity Checked

- Proposition hash
- Evidence hash
- Attestation hash
- State hash

### What Is Semantically Interpreted

- Dimension status
- Authority scope
- Transition authorization
- Disagreement classification

### What Is Inherited

- Verifier identity
- Rule versions
- Semantic versions

### What Remains an Authority Root

- Evidence
- Provenance
- Intervention authority
- Semantic rules

---

## Residual Authority Assumptions

The system does NOT claim to be "trustless." It has the following
residual trust assumptions:

1. **Evidence authority** — The system trusts that evidence with valid
   authority scope can inform propositions within that scope.

2. **Provenance integrity** — The system trusts that provenance hashes
   accurately reflect artifact lineage.

3. **Semantic rule consistency** — The system trusts that semantic
   rules are applied consistently within a rule version.

4. **Implementation correctness** — The system trusts that verifier
   implementations correctly implement their declared semantics.

5. **Identity uniqueness** — The system trusts that verifier identities
   are unique and not forged.

These assumptions are explicit and auditable.

---

## Experimental Findings

### Finding 1 — Majority Vote Does Not Override Minority

9 verifiers saying VALID and 1 saying INCONCLUSIVE does NOT produce
consensus. The disagreement is preserved.

### Finding 2 — Strict Verifier Preserves Disagreement

A verifier applying stricter rules produces a different result. The
system does not conclude the majority is correct.

### Finding 3 — Different Rule Versions Are Classified

Verifiers with different rule versions produce `SEMANTIC_DIVERGENCE`,
not `VERIFIER_A_CORRECT`.

### Finding 4 — Evidence Divergence Is Distinguishable

Different evidence sets produce `EVIDENCE_DIVERGENCE`, not disagreement
about history.

### Finding 5 — Provenance Divergence Is Detectable

Same content with different provenance is detected as
`PROVENANCE_DIVERGENCE`.

### Finding 6 — Semantic Equivalence Enables Agreement

Different implementations with identical semantics can reach epistemic
agreement.

### Finding 7 — Implementation Diversity Can Agree

Genuinely different verifier implementations can produce the same
epistemic result.

### Finding 8 — Correlated Verifiers Are Detected

Verifiers sharing implementation are detected as `SHARES_IMPLEMENTATION`.

### Finding 9 — Sybil Verifiers Are Resistant

100 identities with the same implementation are not treated as 100
independent authorities.

### Finding 10 — Self-Attested Independence Is Not Trusted

A verifier claiming independence is not evidence of independence.

### Finding 11 — Valid Minority Preserves Gap

2 VALID + 1 INCONCLUSIVE does not produce consensus.

### Finding 12 — Valid Contradiction Is Preserved

VALID + INVALID produces structured contradiction, not resolution.

### Finding 13 — Governance Conflict Preserves Epistemic Agreement

Epistemic agreement is preserved despite governance disagreement.

### Finding 14 — Verification vs Re-Evaluation Is Distinguished

Historical verification and current re-evaluation are different
operations.

### Finding 15 — Partial Agreement Is Reported

Agreement on some dimensions and disagreement on others is reported
structurally.

### Finding 16 — Compatible Partial States Are Not Contradictory

UNRESOLVED is not contradictory to VERIFIED.

### Finding 17 — Knowledge Boundary Is Distinct from Failure

Missing evidence is not verification failure.

### Finding 18 — Unverifiable Is Not Refuted

Missing semantics produces INCONCLUSIVE, not REFUTED.

### Finding 19 — Forged Consensus Is Detected

Consensus must be derived, not asserted.

### Finding 20 — Consensus Forgery Is Detected

Consensus is reconstructed from assertions, not trusted from a
consensus artifact.

---

## Architectural Question Answered

> If two independent verifiers disagree, what is the strongest statement
> the system is actually entitled to make?

**Answer:**

The system is entitled to say:

```text
Evidence
    ↓
Independent derivations
    ↓
Verification assertions
    ↓
Structured comparison
    ↓
Agreement / divergence classification
    ↓
Epistemic conflict or consensus artifact
    ↓
Governance
    ↓
Authorization
```

Specifically:

1. **If disagreement is structural** (different evidence, provenance,
   semantics, rules), the system is entitled to say: "The verifiers
   are operating under different epistemic regimes. Their disagreement
   is not a contradiction but a divergence."

2. **If disagreement is implementational** (same semantics, different
   results), the system is entitled to say: "The verifiers produce
   incompatible results under compatible semantics. This is an
   unresolved verification conflict."

3. **If disagreement is dimensional** (agree on some dimensions,
   disagree on others), the system is entitled to say: "The verifiers
   agree on these dimensions and disagree on those dimensions. The
   epistemic state is partially resolved."

4. **If disagreement is governance** (epistemic agreement, governance
   disagreement), the system is entitled to say: "The epistemic layer
   agrees. The governance layer disagrees. Authorization is not granted."

The system is NOT entitled to say:

- "The majority is correct"
- "The proposition is true/false"
- "Execution is authorized/prohibited"
- "The verifier is right/wrong"

---

## Known Limitations

1. **Independence is not proven** — The system classifies independence
   based on identity and provenance, but cannot prove independence.

2. **Semantic equivalence is assumed** — The system assumes that
   identical declared semantics produce identical results, but this is
   not verified.

3. **Single implementation** — The current verifier implementations
   share a common codebase. True cross-implementation verification is
   future work.

4. **No resolution procedure** — The system classifies disagreement but
   does not provide a procedure to resolve it.

5. **No governance integration** — The system produces consensus
   artifacts but does not integrate with governance policies.

---

## Future Work

1. **Cross-implementation verification** — Build genuinely different
   verifier implementations to test semantic equivalence.

2. **Resolution procedures** — Develop procedures to resolve
   disagreement when appropriate.

3. **Governance integration** — Integrate consensus artifacts with
   governance policies.

4. **Dynamic verifier registration** — Allow verifiers to be
   registered and unregistered dynamically.

5. **Verifier reputation** — Track verifier performance over time
   without making reputation authoritative.

6. **Distributed consensus** — Explore consensus across execution
   environments.

---

## File Reference

| File | Purpose |
|------|---------|
| `src/sas/quant/experiment/epistemic_consensus.py` | Consensus implementation |
| `tests/unit/test_epistemic_consensus.py` | Consensus tests |
| `docs/architecture/EPISTEMIC_CONSENSUS.md` | This document |
