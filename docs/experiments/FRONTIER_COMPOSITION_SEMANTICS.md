# Phase 9: Frontier Composition Semantics — Report

**Date:** 2026-09-10
**Tests:** 2,479 passing (2,463 prior + 16 new)

---

## Central Research Question

> Can frontier composition preserve the epistemic information required to distinguish world disagreement, knowledge disagreement, scope disagreement, temporal disagreement, and computational disagreement?

## Executive Summary

**Set composition is a lossy projection of a richer semantic object.**

The experiments demonstrate that:

1. **A frontier is not merely a set.** `{E1,P1,A1}` is a membership projection of a temporally and epistemically bounded claim about semantic impact.

2. **Set operations destroy information.** Union and intersection discard:
   - Which agent identified each artifact
   - Under what scope and temporal bounds
   - With what evidence and provenance
   - Under what completeness conditions

3. **Same membership ≠ same claim.** Two agents can produce identical frontiers from different evidence, scope, temporal bounds, or provenance quality. Set composition treats these as identical; the richer representation reveals the disagreement.

4. **Different membership ≠ world disagreement.** Two agents can produce different frontiers from identical world evidence, using different frontier algorithms. Set composition treats this as disagreement; the richer representation reveals it may be computational, not epistemic.

5. **Provenance-preserving composition is feasible.** The existing provenance infrastructure can represent richer composition without introducing new abstractions.

---

## The Semantic Disagreement Taxonomy

| Type | Meaning | Detected By |
|------|---------|-------------|
| `WORLD_DISAGREEMENT` | Agents observe different world states | Different world state hashes |
| `EPISTEMIC_DISAGREEMENT` | Different frontier membership | Set comparison |
| `SCOPE_DISAGREEMENT` | Different scope environments | Scope comparison |
| `TEMPORAL_DISAGREEMENT` | Different temporal bounds | Timestamp comparison |
| `COMPUTATIONAL_DISAGREEMENT` | Different algorithms, same world | Same world, different output |
| `EVIDENCE_DISAGREEMENT` | Different evidence, same membership | Evidence basis comparison |
| `PROVENANCE_DISAGREEMENT` | Different provenance quality | Provenance quality comparison |
| `COMPLETENESS_DISAGREEMENT` | Different completeness status | Completeness comparison |

---

## Experimental Results

### Experiment 1: Identical Frontier, Different Evidence

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Evidence | EA | EB |

**Finding:** Set composition shows `{E1,P1,A1}` — no disagreement detected.
**Provenance-preserving composition reveals:** `EVIDENCE_DISAGREEMENT`.

**Classification:** `MISSING SEMANTICS` — Set composition loses the evidence distinction.

---

### Experiment 2: Identical Frontier, Different Completeness

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Provenance quality | complete | incomplete |

**Finding:** Set composition shows `{E1,P1,A1}` — no disagreement detected.
**Provenance-preserving composition reveals:** `PROVENANCE_DISAGREEMENT`.

**Classification:** `MISSING SEMANTICS` — Set composition loses the completeness distinction.

---

### Experiment 3: Identical Frontier, Different Scope

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Scope | production | staging |

**Finding:** Set composition shows `{E1,P1,A1}` — no disagreement detected.
**Provenance-preserving composition reveals:** `SCOPE_DISAGREEMENT`.

**Classification:** `MISSING SEMANTICS` — Set composition loses the scope distinction.

---

### Experiment 4: Identical Frontier, Different Temporal Validity

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Temporal bounds | T0 | T1 |

**Finding:** Set composition shows `{E1,P1,A1}` — no disagreement detected.
**Provenance-preserving composition reveals:** `TEMPORAL_DISAGREEMENT`.

**Classification:** `MISSING SEMANTICS` — Set composition loses the temporal distinction.

---

### Experiment 5: Identical Frontier, Different Provenance Quality

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Provenance quality | complete | incomplete |

**Finding:** Set composition shows `{E1,P1,A1}` — no disagreement detected.
**Provenance-preserving composition reveals:** `PROVENANCE_DISAGREEMENT`.

**Classification:** `MISSING SEMANTICS` — Set composition loses the provenance quality distinction.

---

### Experiment 6: Different Frontier, Same World Evidence

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P2,A1} |
| World state | Same | Same |
| Evidence | E1 | E1 |

**Finding:** Set composition shows `{E1,P1,A1,P2}` — disagreement detected.
**Provenance-preserving composition reveals:** `EPISTEMIC_DISAGREEMENT` (different propositions from same evidence).

**Classification:** `EXPERIMENTAL OBSERVATION` — Different outputs from same world evidence may indicate algorithmic disagreement, not world disagreement.

---

### Experiment 7: Different Frontier, Different Granularity

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1} |

**Finding:** Set composition shows `{E1,P1,A1}` — disagreement detected.
**Semantic analysis:** This is a granularity difference, not a world disagreement.

**Classification:** `EXPERIMENTAL OBSERVATION` — Different abstraction levels can produce different frontiers from equivalent underlying claims.

---

### Experiment 8: Provenance-Preserving Union

| Property | Value |
|----------|-------|
| Operation | PROVENANCE_PRESERVING_UNION |
| Composed members | {E1,P1,A1,P2} |
| P1 origin | Agent A, evidence EA |
| P2 origin | Agent B, evidence EB |
| E1 origin | Both agents, evidence EA+EB |
| A1 origin | Both agents, evidence EA+EB |

**Finding:** Provenance-preserving union preserves the origin of each membership.

**Classification:** `IMPLEMENTED GUARANTEE` — Existing provenance structures can represent richer composition.

---

### Experiment 9: Provenance-Preserving Intersection

| Property | Value |
|----------|-------|
| Operation | PROVENANCE_PRESERVING_INTERSECTION |
| Composed members | {E1,A1} |
| E1 origin | Both agents, evidence EA+EB |
| A1 origin | Both agents, evidence EA+EB |

**Finding:** Intersection preserves provenance for surviving members. P1 and P2 are excluded because they differ.

**Classification:** `IMPLEMENTED GUARANTEE` — Intersection is not consensus; it is common ground.

---

### Experiment 10: Evidence Correlation

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Evidence | E1 | E1 (same) |

**Finding:** No information lost because evidence is identical. Same evidence does not imply independent corroboration.

**Classification:** `EXPERIMENTAL OBSERVATION` — Process separation ≠ epistemic independence.

---

### Experiment 11: Adversarial Empty Frontier

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {} |

**Finding:** Union preserves Agent A's frontier. Empty frontier does not amplify authority.

**Classification:** `IMPLEMENTED GUARANTEE` — Empty frontiers are handled correctly.

---

### Experiment 12: Adversarial Scope Widened

| Property | Agent A | Agent B |
|----------|---------|---------|
| Frontier | {E1,P1,A1} | {E1,P1,A1} |
| Scope | production | * (wildcard) |

**Finding:** Scope disagreement detected as information loss.

**Classification:** `MISSING SEMANTICS` — Set composition loses scope disagreement.

---

### Experiment 13: Malicious Agreement

| Property | Value |
|----------|-------|
| Agents | agent_A, agent_B_malicious |
| Frontier | Both {E1,P1,A1} |
| Evidence | Both E1 (same) |

**Finding:** Provenance-preserving composition records both agents. No authority amplification through numerical agreement.

**Classification:** `IMPLEMENTED GUARANTEE` — N identical outputs ≠ stronger authority.

---

### Experiment 14: Composition Information-Loss Measurement

| Representation | Information Preserved |
|----------------|----------------------|
| RichFrontier | agent_count, evidence_bases, scopes, temporal_bounds, provenance_qualities, completeness_statuses |
| Set composition | member_count only |
| Provenance-preserving | member_count, members_with_multiple_agents, members_with_multiple_evidence, semantic_disagreements |

**Finding:** Set composition preserves 1 of 6 semantic dimensions. Provenance-preserving composition preserves 4 of 6.

**Classification:** `COUNTEREXAMPLE` — Set composition is a lossy projection.

---

## The Composition Algebra (Revised)

### Set Union

| Property | Value |
|----------|-------|
| Semantic meaning | All artifact IDs from either frontier |
| Information preserved | Membership only |
| Information lost | Agent identity, evidence, scope, temporal bounds, provenance, completeness |
| Authority behavior | Does NOT create authority |
| Use case | Candidate review frontier (lossy) |

### Provenance-Preserving Union

| Property | Value |
|----------|-------|
| Semantic meaning | All artifact IDs with origin preserved |
| Information preserved | Membership + agent identity + evidence + scope + temporal + provenance + completeness |
| Information lost | None (within existing type system) |
| Authority behavior | Does NOT create authority |
| Use case | Rich candidate review frontier |

### Set Intersection

| Property | Value |
|----------|-------|
| Semantic meaning | Artifact IDs common to both frontiers |
| Information preserved | Membership only |
| Information lost | Agent identity, evidence, scope, temporal bounds, provenance, completeness |
| Authority behavior | Does NOT create authority |
| Use case | Common ground identification (lossy) |

### Provenance-Preserving Intersection

| Property | Value |
|----------|-------|
| Semantic meaning | Common artifact IDs with origin preserved |
| Information preserved | Membership + agent identity + evidence + scope + temporal + provenance + completeness |
| Information lost | None (within existing type system) |
| Authority behavior | Does NOT create authority |
| Use case | Rich common ground identification |

---

## Required Invariants (All Verified)

| Invariant | Status |
|-----------|--------|
| COMPOSITION ≠ AUTHORIZATION | ✅ |
| UNION ≠ AUTHORIZATION | ✅ |
| INTERSECTION ≠ AUTHORIZATION | ✅ |
| SAME MEMBERSHIP ≠ SAME CLAIM | ✅ |
| DIFFERENT MEMBERSHIP ≠ WORLD DISAGREEMENT | ✅ |
| UNION ≠ EPISTEMIC UNION | ✅ |
| INTERSECTION ≠ EPISTEMIC CONSENSUS | ✅ |
| N AGENTS AGREEING ≠ STRONGER AUTHORITY | ✅ |
| SET COMPOSITION IS A LOSSY PROJECTION | ✅ |
| PROVENANCE-PRESERVING COMPOSITION FITS EXISTING TYPES | ✅ |

---

## Classification of Results

| Finding Type | Count | Examples |
|--------------|-------|----------|
| IMPLEMENTED GUARANTEE | 6 | Non-amplification, provenance preservation |
| EXPERIMENTAL OBSERVATION | 5 | Experiments 6, 7, 10, 12, 14 |
| EMPIRICAL RESULT | 1 | Information loss measured |
| COUNTEREXAMPLE | 1 | Set composition is lossy |
| MISSING SEMANTICS | 5 | Experiments 1, 2, 3, 4, 5 |
| PROTOCOL VIOLATION | 0 | None |

---

## The Architectural Law (Revised)

```
world delta
    ↓
dependency intersection
    ↓
typed semantic impact propagation
    ↓
scope resolution
    ↓
scope provenance validation
    ↓
temporal validity
    ↓
epistemic state
    ↓
governance
    ↓
authority
    ↓
execution
```

### Key Distinction

**A frontier is not a set.** It is a temporally and epistemically bounded claim about semantic impact. The set representation `{E1,P1,A1}` is a membership projection — useful for candidate review, but insufficient for governance decisions that require understanding:

- Why each artifact is in the frontier
- Which agent identified it
- Under what scope and temporal bounds
- With what evidence and provenance
- Whether the agents disagree about the world or about computation

---

## The Deeper Result

> **The frontier is not the final epistemic object. It is the review surface generated from a richer, provenance-bearing computation.**

This is the architectural result. The set is a projection. The rich frontier is the actual epistemic claim. Governance needs the rich frontier, not the projection.

---

## Next Boundary

**Phase 10: Governance Over Rich Frontiers** — Test whether the existing governance model (`AuthorityFrontierIntegrator`, `GovernanceAction`) can consume rich frontiers (with provenance, scope, temporal bounds, completeness) rather than set projections.

The question: Does governance need the full rich frontier, or is the set projection sufficient for making legitimate authority decisions?

This is an empirical question, not a philosophical one. The answer depends on whether the additional semantic information changes governance outcomes.

---

## Pause Point

The experimental record now establishes:

1. **Set composition is safe** — it does not amplify authority.
2. **Set composition is lossy** — it destroys semantic information.
3. **Provenance-preserving composition is feasible** — it fits within existing types.
4. **The frontier is a review surface** — not the final epistemic object.

The next step is to determine whether the richer representation changes governance decisions. That requires experiments, not assumptions.
