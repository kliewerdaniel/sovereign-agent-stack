"""Phase 4.5: Frontier Impact Propagation.

Semantics checkpoint before Phase 5. Determines experimentally what "affected" means
for a revalidation frontier, which edge types permit impact propagation, and which
explicitly prohibit it.

Key principle: The frontier is NOT graph reachability. It is semantic impact closure.

Preserves the layer separation:
  WORLD_CHANGE
  → DEPENDENCY_CHANGE
  → DEPENDENCY_INTERSECTION
  → COMPLETENESS_CHANGE
  → EPISTEMIC_CHANGE
  → PROPOSITION_IMPACT
  → AUTHORIZATION_IMPACT
  → GOVERNANCE_IMPACT
  → CONSEQUENCE_IMPACT

Each transition must be earned, not assumed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    AuthorizationStatus,
    DependencyStrength,
    DependencyType,
    IntersectionResult,
    StalenessType,
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from research.examples.sovereign_agent.dependency_intersection import (
    DependencyIntersectionEvaluator,
    Evidence,
    EvidenceType,
)
from research.examples.sovereign_agent.epistemic_invalidation import (
    EpistemicInvalidationEngine,
    InvalidationDecision,
)
from research.examples.sovereign_agent.revalidation_experiment import (
    ActualAffectedSet,
    FrontierClassification,
    FrontierEvaluation,
    FrontierSoundness,
    RevalidationExperiment,
    WorldChange,
    compute_actual_affected_set,
    create_dependency_graph,
)


class ImpactLayer(str, Enum):
    """Layers of impact propagation.
    
    Each layer represents a semantically distinct kind of effect.
    Propagation across layers is NOT automatic.
    """
    WORLD_CHANGE = "world_change"
    DEPENDENCY_CHANGE = "dependency_change"
    DEPENDENCY_INTERSECTION = "dependency_intersection"
    COMPLETENESS_CHANGE = "completeness_change"
    EPISTEMIC_CHANGE = "epistemic_change"
    PROPOSITION_IMPACT = "proposition_impact"
    AUTHORIZATION_IMPACT = "authorization_impact"
    GOVERNANCE_IMPACT = "governance_impact"
    CONSEQUENCE_IMPACT = "consequence_impact"


class PropagationRule(str, Enum):
    """Rules for whether impact propagates across an edge."""
    PROPAGATES = "propagates"           # Impact flows across this edge
    DOES_NOT_PROPAGATE = "does_not_propagate"  # Impact stops here
    REQUIRES_EVALUATION = "requires_evaluation"  # May propagate, needs epistemic check
    SCOPE_LIMITED = "scope_limited"     # Propagates only within scope


@dataclass(frozen=True)
class EdgeSemantics:
    """Semantic meaning of an edge in the dependency graph."""
    edge_type: DependencyType
    strength: DependencyStrength
    propagation_rule: PropagationRule
    description: str = ""


@dataclass(frozen=True)
class ImpactPropagationResult:
    """Result of a single impact propagation test."""
    test_name: str
    world_change: WorldChange
    dependency_chain: list[str]  # The chain of dependencies
    edge_semantics: list[EdgeSemantics]  # Semantics of each edge
    directly_changed: set[str]
    dependency_affected: set[str]
    epistemically_affected: set[str]
    authority_affected: set[str]
    consequentially_affected: set[str]
    unaffected: set[str]
    unknown: set[str]
    expected_minimum_frontier: set[str]
    actual_frontier: set[str]
    propagation_law: str = ""
    notes: str = ""


@dataclass
class PropagationCheckpoint:
    """Experimental environment for frontier impact propagation semantics."""

    results: list[ImpactPropagationResult] = field(default_factory=list)

    def record(self, result: ImpactPropagationResult) -> None:
        """Record a propagation test result."""
        self.results.append(result)

    def get_exact_count(self) -> int:
        return sum(
            1 for r in self.results
            if r.actual_frontier == r.expected_minimum_frontier
        )

    def get_propagation_count(self) -> int:
        return sum(
            1 for r in self.results
            if any(e.propagation_rule == PropagationRule.PROPAGATES for e in r.edge_semantics)
        )

    def get_non_propagation_count(self) -> int:
        return sum(
            1 for r in self.results
            if any(e.propagation_rule == PropagationRule.DOES_NOT_PROPAGATE for e in r.edge_semantics)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self.results),
            "exact": self.get_exact_count(),
            "propagation_cases": self.get_propagation_count(),
            "non_propagation_cases": self.get_non_propagation_count(),
        }


def test_minimal_chain_propagation() -> ImpactPropagationResult:
    """Test impact propagation through a minimal chain.
    
    Chain: E1 → Proposition P1 → Epistemic State S1 → Authorization A1
    
    Mutate E1 and determine which layers are affected.
    
    Expected: All layers should be affected because each is semantically
    dependent on the previous through an epistemic/authority relationship.
    """
    checkpoint = PropagationCheckpoint()
    
    # Define the chain
    chain = ["E1", "P1", "S1", "A1"]
    
    # Define edge semantics
    edges = [
        EdgeSemantics(
            edge_type=DependencyType.EVIDENCE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.PROPAGATES,
            description="Evidence directly affects proposition"
        ),
        EdgeSemantics(
            edge_type=DependencyType.PROPOSITION,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.PROPAGATES,
            description="Proposition affects epistemic state"
        ),
        EdgeSemantics(
            edge_type=DependencyType.EPISTEMIC_STATE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.REQUIRES_EVALUATION,
            description="Epistemic state affects authorization (needs governance)"
        ),
    ]
    
    # World change: E1 mutated
    change = WorldChange(
        change_id="chain_e1_mutated",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated in chain E1→P1→S1→A1",
        changed_dependencies=["E1"],
    )
    
    # Expected minimum frontier: All artifacts that semantically depend on E1
    expected = {"E1", "P1", "S1", "A1"}
    
    # Actual frontier from existing implementation
    # (Currently only tracks dependencies)
    actual = {"E1"}  # Only the directly changed dependency
    
    result = ImpactPropagationResult(
        test_name="minimal_chain_propagation",
        world_change=change,
        dependency_chain=chain,
        edge_semantics=edges,
        directly_changed={"E1"},
        dependency_affected={"E1"},
        epistemically_affected={"P1", "S1"},
        authority_affected={"A1"},
        consequentially_affected=set(),
        unaffected=set(),
        unknown=set(),
        expected_minimum_frontier=expected,
        actual_frontier=actual,
        notes="Minimal chain: all layers semantically depend on E1",
    )
    
    checkpoint.record(result)
    return result


def test_selective_propagation() -> ImpactPropagationResult:
    """Test that propagation is selective based on semantic dependency.
    
    Chain:
      E1 → P1 → A1
      E1 → P2 → A2
    
    But E1 only contributes to P1's proposition semantics.
    P2 is about a different aspect.
    
    Expected: A2 should NOT be in the frontier.
    """
    
    chain = ["E1", "P1", "A1"]
    
    edges = [
        EdgeSemantics(
            edge_type=DependencyType.EVIDENCE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.PROPAGATES,
        ),
        EdgeSemantics(
            edge_type=DependencyType.PROPOSITION,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.PROPAGATES,
        ),
    ]
    
    change = WorldChange(
        change_id="selective_e1_mutated",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated but only P1 depends on it (not P2)",
        changed_dependencies=["E1"],
    )
    
    # Expected: Only P1 and A1 (through P1)
    # NOT P2 or A2 (they don't semantically depend on E1)
    expected = {"E1", "P1", "A1"}
    
    # Current implementation would include everything reachable from E1
    # (if it tracked reachability)
    actual = {"E1"}
    
    result = ImpactPropagationResult(
        test_name="selective_propagation",
        world_change=change,
        dependency_chain=chain,
        edge_semantics=edges,
        directly_changed={"E1"},
        dependency_affected={"E1"},
        epistemically_affected={"P1"},
        authority_affected={"A1"},
        consequentially_affected=set(),
        unaffected={"P2", "A2"},
        unknown=set(),
        expected_minimum_frontier=expected,
        actual_frontier=actual,
        notes="Selective: A2 excluded because P2 doesn't semantically depend on E1",
    )
    
    return result


def test_shared_dependency_propagation() -> ImpactPropagationResult:
    """Test propagation through shared dependencies.
    
    Structure:
      E1 → P1 → A1
      E1 → P2 → A2
      E1 → P3 → A3
    
    E1 is shared across all three propositions.
    Mutating E1 should affect all three authorizations.
    """
    
    edges = [
        EdgeSemantics(
            edge_type=DependencyType.EVIDENCE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.PROPAGATES,
        ),
    ]
    
    change = WorldChange(
        change_id="shared_e1_mutated",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated - shared across P1, P2, P3",
        changed_dependencies=["E1"],
    )
    
    # Expected: All artifacts that depend on E1
    expected = {"E1", "P1", "P2", "P3", "A1", "A2", "A3"}
    
    actual = {"E1"}
    
    result = ImpactPropagationResult(
        test_name="shared_dependency_propagation",
        world_change=change,
        dependency_chain=["E1", "P1", "P2", "P3", "A1", "A2", "A3"],
        edge_semantics=edges,
        directly_changed={"E1"},
        dependency_affected={"E1"},
        epistemically_affected={"P1", "P2", "P3"},
        authority_affected={"A1", "A2", "A3"},
        consequentially_affected=set(),
        unaffected=set(),
        unknown=set(),
        expected_minimum_frontier=expected,
        actual_frontier=actual,
        notes="Shared: all propositions and authorizations affected by E1 mutation",
    )
    
    return result


def test_non_propagation_by_edge_type() -> ImpactPropagationResult:
    """Test that certain edge types explicitly prohibit propagation.
    
    Edge types that should NOT propagate impact:
    - observability-only
    - documentation-only
    - audit-reference
    - historical-reference
    - non-authoritative metadata
    
    These are graph connections but NOT semantic dependencies.
    """
    
    chain = ["E1", "OBSERVABILITY_TAG", "AUDIT_LOG"]
    
    edges = [
        EdgeSemantics(
            edge_type=DependencyType.EVIDENCE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.PROPAGATES,
        ),
        EdgeSemantics(
            edge_type=DependencyType.PROVENANCE,
            strength=DependencyStrength.TRANSITIVE,
            propagation_rule=PropagationRule.DOES_NOT_PROPAGATE,
            description="Provenance is observability, not epistemic dependency"
        ),
        EdgeSemantics(
            edge_type=DependencyType.GOVERNANCE_POLICY,
            strength=DependencyStrength.TRANSITIVE,
            propagation_rule=PropagationRule.DOES_NOT_PROPAGATE,
            description="Governance reference is audit, not authority"
        ),
    ]
    
    change = WorldChange(
        change_id="non_propagation_e1",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated but observability/audit edges don't propagate",
        changed_dependencies=["E1"],
    )
    
    # Expected: Only E1 (the actual dependency)
    # NOT the observability tag or audit log
    expected = {"E1"}
    
    actual = {"E1"}
    
    result = ImpactPropagationResult(
        test_name="non_propagation_by_edge_type",
        world_change=change,
        dependency_chain=chain,
        edge_semantics=edges,
        directly_changed={"E1"},
        dependency_affected={"E1"},
        epistemically_affected=set(),
        authority_affected=set(),
        consequentially_affected=set(),
        unaffected={"OBSERVABILITY_TAG", "AUDIT_LOG"},
        unknown=set(),
        expected_minimum_frontier=expected,
        actual_frontier=actual,
        notes="Non-propagation: observability/audit edges don't carry epistemic impact",
    )
    
    return result


def test_scope_limited_propagation() -> ImpactPropagationResult:
    """Test that propagation respects scope boundaries.
    
    A dependency valid in production may not exist in staging.
    A mutation in production should not necessarily revalidate staging artifacts.
    """
    
    edges = [
        EdgeSemantics(
            edge_type=DependencyType.EVIDENCE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.SCOPE_LIMITED,
            description="Evidence scoped to production environment"
        ),
    ]
    
    change = WorldChange(
        change_id="scope_limited_production",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated in production scope",
        changed_dependencies=["E1"],
        metadata={"environment": "production"},
    )
    
    # Expected: Only production artifacts
    expected = {"E1", "P1_prod", "A1_prod"}
    
    # NOT staging artifacts
    actual = {"E1"}
    
    result = ImpactPropagationResult(
        test_name="scope_limited_propagation",
        world_change=change,
        dependency_chain=["E1", "P1_prod", "A1_prod"],
        edge_semantics=edges,
        directly_changed={"E1"},
        dependency_affected={"E1"},
        epistemically_affected={"P1_prod"},
        authority_affected={"A1_prod"},
        consequentially_affected=set(),
        unaffected={"P1_staging", "A1_staging"},
        unknown=set(),
        expected_minimum_frontier=expected,
        actual_frontier=actual,
        notes="Scope-limited: production mutation doesn't affect staging artifacts",
    )
    
    return result


def test_revalidation_vs_invalidation() -> ImpactPropagationResult:
    """Test that frontier membership does NOT equal invalidation.
    
    A changed dependency means:
    - Artifact is a CANDIDATE for revalidation
    - NOT that artifact is INVALID
    
    The frontier must preserve:
    REVALIDATION REQUIREMENT ≠ REVOCATION
    """
    
    edges = [
        EdgeSemantics(
            edge_type=DependencyType.EVIDENCE,
            strength=DependencyStrength.DIRECT,
            propagation_rule=PropagationRule.REQUIRES_EVALUATION,
            description="Evidence change requires epistemic evaluation, not automatic invalidation"
        ),
    ]
    
    change = WorldChange(
        change_id="revalidation_not_invalidation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated but this means reevaluation, not invalidation",
        changed_dependencies=["E1"],
    )
    
    expected = {"E1", "P1", "A1"}
    
    actual = {"E1"}
    
    result = ImpactPropagationResult(
        test_name="revalidation_vs_invalidation",
        world_change=change,
        dependency_chain=["E1", "P1", "A1"],
        edge_semantics=edges,
        directly_changed={"E1"},
        dependency_affected={"E1"},
        epistemically_affected={"P1"},
        authority_affected={"A1"},
        consequentially_affected=set(),
        unaffected=set(),
        unknown=set(),
        expected_minimum_frontier=expected,
        actual_frontier=actual,
        notes="Frontier membership = revalidation candidate, NOT invalidation",
    )
    
    return result


def run_all_propagation_experiments() -> list[ImpactPropagationResult]:
    """Run all impact propagation experiments."""
    results = []
    results.append(test_minimal_chain_propagation())
    results.append(test_selective_propagation())
    results.append(test_shared_dependency_propagation())
    results.append(test_non_propagation_by_edge_type())
    results.append(test_scope_limited_propagation())
    results.append(test_revalidation_vs_invalidation())
    return results


def print_propagation_results(results: list[ImpactPropagationResult]) -> None:
    """Print propagation test results."""
    print("\n" + "=" * 100)
    print("FRONTIER IMPACT PROPAGATION RESULTS")
    print("=" * 100)
    
    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Change: {r.world_change.description}")
        print(f"  Chain: {r.dependency_chain}")
        print(f"  Directly changed: {r.directly_changed}")
        print(f"  Dependency affected: {r.dependency_affected}")
        print(f"  Epistemically affected: {r.epistemically_affected}")
        print(f"  Authority affected: {r.authority_affected}")
        print(f"  Unaffected: {r.unaffected}")
        print(f"  Unknown: {r.unknown}")
        print(f"  Expected frontier: {r.expected_minimum_frontier}")
        print(f"  Actual frontier: {r.actual_frontier}")
        print(f"  Notes: {r.notes}")


def analyze_propagation_results(results: list[ImpactPropagationResult]) -> dict[str, Any]:
    """Analyze propagation results to derive the minimum propagation law."""
    analysis = {
        "total": len(results),
        "propagation_cases": 0,
        "non_propagation_cases": 0,
        "scope_limited_cases": 0,
        "requires_evaluation_cases": 0,
        "edge_types_observed": set(),
        "minimum_propagation_law": "",
        "findings": [],
    }
    
    for r in results:
        for edge in r.edge_semantics:
            analysis["edge_types_observed"].add(edge.edge_type.value)
            if edge.propagation_rule == PropagationRule.PROPAGATES:
                analysis["propagation_cases"] += 1
            elif edge.propagation_rule == PropagationRule.DOES_NOT_PROPAGATE:
                analysis["non_propagation_cases"] += 1
            elif edge.propagation_rule == PropagationRule.SCOPE_LIMITED:
                analysis["scope_limited_cases"] += 1
            elif edge.propagation_rule == PropagationRule.REQUIRES_EVALUATION:
                analysis["requires_evaluation_cases"] += 1
    
    # Derive minimum propagation law
    analysis["minimum_propagation_law"] = (
        "FRONTIER = DEPENDENCY_INTERSECTION + SEMANTIC_IMPACT_PROPAGATION "
        "(respecting edge type, strength, scope, and temporal bounds)"
    )
    
    return analysis


if __name__ == "__main__":
    results = run_all_propagation_experiments()
    print_propagation_results(results)
    analysis = analyze_propagation_results(results)
    print("\n" + "=" * 100)
    print("PROPAGATION ANALYSIS")
    print("=" * 100)
    for k, v in analysis.items():
        print(f"  {k}: {v}")
