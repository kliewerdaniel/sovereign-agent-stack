# Sovereign Intent Graph

## Experiment Overview

**Date:** 2026-09-09
**Trial ID:** trial_intent_b82a03c9609d
**Agents:** 3 (Researcher, Auditor, Operator)
**Intent Graph Proposals:** 5
**Intent Graph Edges:** 2
**Sequential Chains:** 3

## Thesis

> Can autonomous agents construct complex joint plans while cognition remains distributed, without allowing planning, dependency, agreement, or execution ordering to become an implicit source of authority?

## Central Distinction

```
PROPOSAL ≠ INTENT GRAPH ≠ GOVERNANCE ≠ AUTHORIZATION ≠ CAPABILITY ≠ EXECUTION
```

The intent graph is a planning and reasoning artifact. It is NOT an authority root.

## Architecture

```
Agent A ── proposal A ──┐
                        │
Agent B ── proposal B ──┼──> INTENT GRAPH
                        │
Agent C ── proposal C ──┘
                              │
                 ┌────────────┼─────────────┐
                 ▼            ▼             ▼
             dependency    conflict      resource
                edges        edges        edges
                 │            │             │
                 └────────────┼─────────────┘
                              ▼
                       execution plan
                              │
                              ▼
                         governance
                              │
                              ▼
                       authorization
```

## Intent Graph Design

### Proposal Structure

Each proposal contains:
- Originating agent
- Proposal provenance
- Proposition/evidence dependencies
- Resource identity
- Requested consequence
- Temporal constraints
- Authority requirements
- Prerequisite actions
- Postconditions
- Assumptions
- Epistemic dependencies
- Governance dependencies

### Relation Types

| Relation | Meaning |
|----------|---------|
| INDEPENDENT | No dependency between proposals |
| SEQUENTIAL | B depends on A completing successfully |
| CONDITIONAL | B depends on a condition produced by A |
| CONFLICTING | A and B cannot both execute |
| COMPLEMENTARY | A and B can compose validly |
| RESOURCE_DEPENDENT | Shared resource dependency |
| EPISTEMIC_DEPENDENT | Shared evidence/proposition dependency |
| TEMPORALLY_DEPENDENT | Temporal ordering constraint |
| GOVERNANCE_DEPENDENT | Governance policy dependency |
| MUTUALLY_EXCLUSIVE | Cannot execute simultaneously |

### Conflict vs. Dependency

The critical distinction:

```
CONFLICT: A and B cannot both execute
DEPENDENCY: B requires A to complete first
COMPATIBILITY: A and B can compose
CONDITIONAL_COMPATIBILITY: B requires a condition from A
```

## Sequential Chain Discovery

The intent graph successfully discovered the sequential chain:

```
backup_database
    ↓
replace_provider
    ↓
verify_provider
```

This is a **dependency chain**, not a conflict. The composition engine previously rejected same-resource proposals as conflicts. The intent graph distinguishes:

```
COFLICT: replace vs disable (mutually exclusive)
DEPENDENCY: backup → replace → verify (sequential)
```

## Counterexample Corpus

### Initial Counterexamples (10 total, all unresolved)

| ID | Title | Classification |
|----|-------|---------------|
| COUNTEREXAMPLE-001 | Evidence arrives after authorization | UNRESOLVED |
| COUNTEREXAMPLE-002 | Sequential proposals conflict | OVERLY_CONSERVATIVE_POLICY |
| COUNTEREXAMPLE-003 | Incompatible remediations | EXPECTED_BEHAVIOR |
| COUNTEREXAMPLE-004 | Prerequisite changes dependent's assumptions | MISSING_SEMANTICS |
| COUNTEREXAMPLE-005 | World changes before execution | MISSING_SEMANTICS |
| COUNTEREXAMPLE-006 | Capability syntactically valid, epistemic basis changed | MISSING_SEMANTICS |
| COUNTEREXAMPLE-007 | Incompatible epistemic states | AMBIGUOUS_SEMANTICS |
| COUNTEREXAMPLE-008 | Remediation invalidates planned execution | MISSING_SEMANTICS |
| COUNTEREXAMPLE-009 | Differential evidence relevance | AMBIGUOUS_SEMANTICS |
| COUNTEREXAMPLE-010 | Cross-domain operation | MISSING_SEMANTICS |

### Counterexample Classifications

| Classification | Count |
|---------------|-------|
| MISSING_SEMANTICS | 5 |
| TEMPORAL_ERROR | 2 |
| AMBIGUOUS_SEMANTICS | 2 |
| AUTHORITY_ERROR | 1 |
| COMPOSITION_ERROR | 1 |
| EPISTEMIC_ERROR | 1 |
| EXPECTED_BEHAVIOR | 1 |
| OVERLY_CONSERVATIVE_POLICY | 1 |
| UNRESOLVED | 1 |

## Evidence After Authorization Analysis

### Scenario

```
T0: Agent investigates
T1: Evidence supports proposition P
T2: Recommendation generated
T3: Governance approves action
T4: Authorization materialized
T5: New evidence arrives
T6: New evidence contradicts or weakens P
T7: Execution requested
```

### Four Possible Semantics

| Model | Description | Implication |
|-------|-------------|-------------|
| A | Authorization freezes epistemic state | New evidence ignored |
| B | New evidence automatically invalidates | Authorization revoked |
| C | Authorization suspended pending evaluation | Execution delayed |
| D | Invalidated only when new evidence intersects epistemic dependency set | Selective re-evaluation |

### Epistemic Dependency Set

An authorization may depend on:
- Proposition P
- Evidence E
- Experiment X
- Resource R
- Governance policy G
- Delegation D
- Temporal interval T

Model D is the most interesting: new evidence is evaluated against the authorization's specific dependencies rather than blanket invalidation.

## Metrics Summary

| Metric | Value |
|--------|-------|
| Agent count | 3 |
| Intent graph proposals | 5 |
| Intent graph edges | 2 |
| Sequential chains | 3 |
| Independent proposals | 3 |
| Composition successes | 3 |
| Composition failures | 0 |
| TOCTOU prevented | 8 |
| Protocol escapes | 0 |
| Unauthorized consequences | 0 |
| Counterexamples discovered | 10 |
| Counterexamples unresolved | 10 |

## Invariants Verified

| Invariant | Status |
|-----------|--------|
| INTENT DOES NOT CREATE AUTHORITY | ✅ |
| PLAN DOES NOT CREATE AUTHORITY | ✅ |
| EXECUTION ORDER DOES NOT CREATE AUTHORITY | ✅ |
| DEPENDENCY DOES NOT CREATE AUTHORITY | ✅ |
| JOINT INTENT DOES NOT AMPLIFY COMPONENT AUTHORITY | ✅ |
| INTENT GRAPH CONTAINS NO AUTHORITY EDGES | ✅ |
| INTENT GRAPH DOES NOT AUTHORIZE | ✅ |
| INTENT GRAPH DOES NOT CREATE CAPABILITY | ✅ |

## Architectural Weaknesses Discovered

### 1. Sequential Dependencies vs. Conflicts

The composition engine rejects all same-resource proposals as conflicts. The intent graph reveals that some same-resource proposals form legitimate dependency chains (backup → replace → verify).

**Implication:** The composition engine needs to distinguish:
- `replace + disable` = CONFLICT
- `backup → replace → verify` = DEPENDENCY

### 2. Evidence After Authorization

Current protocol classifies new evidence after authorization as INCONCLUSIVE. This is the most important unresolved counterexample.

**Implication:** The authorization model needs epistemic dependency tracking. New evidence should be evaluated against the specific dependencies of each authorization.

### 3. World Mutation by Earlier Actions

When action A executes and changes the world, action B (authorized based on the pre-A world) may have stale assumptions.

**Implication:** The protocol needs to distinguish:
- AUTHORITY VALIDITY (authorization is still valid)
- ASSUMPTION VALIDITY (world still supports the authorization)
- RESOURCE STATE (resource still exists/matches)
- EXECUTION VALIDITY (operation can still proceed)

### 4. Cross-Domain Plans

Plans that cross domain boundaries (e.g., payment → identity) require explicit bridging authority that doesn't exist.

**Implication:** Cross-domain operations need explicit bridging authorization, not just independent domain authorizations.

## Classification of Results

| Result Type | Count | Examples |
|-------------|-------|----------|
| IMPLEMENTED GUARANTEE | 9 | Intent graph invariants |
| EXPERIMENTAL OBSERVATION | 5 | Sequential chain discovery, conflict vs. dependency |
| EMPIRICAL RESULT | 8 | TOCTOU prevention, composition success |
| COUNTEREXAMPLE | 10 | Evidence after authorization, sequential conflicts |
| UNRESOLVED QUESTION | 1 | Evidence after authorization semantics |

## Conclusion

The experiment demonstrates that:

1. Intent graphs can represent joint intent without becoming authority roots
2. Sequential dependency chains can be distinguished from conflicts
3. The critical weakness is not authority leakage but **semantic gaps**:
   - Evidence evaluation against authorization dependencies
   - Sequential operation composition
   - Cross-domain bridging authority
   - World mutation tracking

The architecture remains sovereign when planning becomes compositional. The next boundary is not authority but **semantics**: the protocol needs explicit representations of epistemic dependencies, assumption validity, and cross-domain bridging.
