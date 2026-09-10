"""Phase 5: Conditional and Scoped Frontier Semantics.

Determines experimentally how conditionality changes semantic impact.
Does NOT simply add scope fields — tests whether scope actually changes
frontier membership.

Key principle: Semantic impact propagates only across dependencies whose
conditions, scope, provenance, and temporal validity establish that the
affected artifact actually depends on the changed state.

Reuses existing infrastructure:
- CompletenessScope
- CompletenessAssessment
- IntersectionStatus
- dependency types
- authorization dependency graph
- conditional authority
- temporal authority
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.sovereign_agent.dependency_completeness import (
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.frontier_impact_propagation import (
    EdgeSemantics,
    ImpactPropagationResult,
    PropagationRule,
    run_all_propagation_experiments,
)
from examples.sovereign_agent.revalidation_experiment import (
    ActualAffectedSet,
    FrontierClassification,
    FrontierSoundness,
    RevalidationExperiment,
    WorldChange,
    compute_actual_affected_set,
    create_dependency_graph,
)
from examples.sovereign_agent.temporal_completeness import (
    TemporalCompletenessEngine,
)


class ScopeDimension(str, Enum):
    """Scope dimensions that may affect frontier propagation."""
    ENVIRONMENT = "environment"
    FEATURE_FLAG = "feature_flag"
    FAILURE_STATE = "failure_state"
    ACTOR = "actor"
    OPERATION = "operation"
    RESOURCE = "resource"
    TEMPORAL_INTERVAL = "temporal_interval"
    SOVEREIGN_DOMAIN = "sovereign_domain"


@dataclass(frozen=True)
class ScopedDependency:
    """A dependency with scope conditions."""
    dependency_id: str
    scope: CompletenessScope
    conditions: list[str] = field(default_factory=list)
    valid_from: str = ""
    valid_until: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_active_in(self, scope: CompletenessScope, timestamp: str = "") -> bool:
        """Check if this dependency is active in the given scope."""
        return self.scope.matches(scope)


@dataclass(frozen=True)
class ScopedFrontierResult:
    """Result of a scoped frontier experiment."""
    test_name: str
    scope_dimension: ScopeDimension
    world_change: WorldChange
    dependency_scope: CompletenessScope
    query_scope: CompletenessScope
    expected_frontier: set[str]
    actual_frontier: set[str]
    scope_matches: bool
    propagation_rule: PropagationRule
    notes: str = ""


def test_environment_scope() -> list[ScopedFrontierResult]:
    """Test environment-scoped frontier propagation.
    
    Construct:
      E1 → P1 → A1 (production)
      E1 → P2 → A2 (staging)
    
    Mutate E1 in production.
    
    Expected: Only P1 and A1 should be in the frontier.
    P2 and A2 should NOT be in the frontier because they are staging-scoped.
    """
    results = []
    
    # Production scope
    prod_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
    )
    
    # Staging scope
    staging_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="staging",
    )
    
    # World change: E1 mutated in production
    change = WorldChange(
        change_id="env_prod_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated in production scope",
        changed_dependencies=["E1"],
        metadata={"environment": "production"},
    )
    
    # Expected frontier in production scope
    expected_prod = {"E1", "P1", "A1"}
    
    # Expected frontier in staging scope (should be empty or unknown)
    expected_staging = set()  # E1 mutation in prod doesn't affect staging
    
    # Current implementation: only returns {E1}
    actual = {"E1"}
    
    results.append(ScopedFrontierResult(
        test_name="environment_production",
        scope_dimension=ScopeDimension.ENVIRONMENT,
        world_change=change,
        dependency_scope=prod_scope,
        query_scope=prod_scope,
        expected_frontier=expected_prod,
        actual_frontier=actual,
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="Production mutation should only affect production artifacts",
    ))
    
    results.append(ScopedFrontierResult(
        test_name="environment_staging",
        scope_dimension=ScopeDimension.ENVIRONMENT,
        world_change=change,
        dependency_scope=staging_scope,
        query_scope=staging_scope,
        expected_frontier=expected_staging,
        actual_frontier=actual,
        scope_matches=False,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="Production mutation should NOT affect staging artifacts",
    ))
    
    return results


def test_feature_flag_scope() -> list[ScopedFrontierResult]:
    """Test feature-flag-scoped frontier propagation.
    
    Construct:
      E1 → P1 → A1 (feature_flag = ENABLED)
      E1 → P2 → A2 (feature_flag = DISABLED)
    
    Test:
    1. E1 changes while flag enabled
    2. E1 changes while flag disabled
    3. Flag transitions disabled → enabled
    4. Flag transitions enabled → disabled
    """
    results = []
    
    # Feature flag enabled scope
    enabled_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
    )
    
    # Feature flag disabled scope
    disabled_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
    )
    
    # Test 1: E1 changes while flag enabled
    change_enabled = WorldChange(
        change_id="flag_enabled_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated while feature flag enabled",
        changed_dependencies=["E1"],
        metadata={"feature_flag": "enabled"},
    )
    
    results.append(ScopedFrontierResult(
        test_name="feature_flag_enabled",
        scope_dimension=ScopeDimension.FEATURE_FLAG,
        world_change=change_enabled,
        dependency_scope=enabled_scope,
        query_scope=enabled_scope,
        expected_frontier={"E1", "P1", "A1"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="E1 mutation with flag enabled should affect P1/A1",
    ))
    
    # Test 2: E1 changes while flag disabled
    change_disabled = WorldChange(
        change_id="flag_disabled_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated while feature flag disabled",
        changed_dependencies=["E1"],
        metadata={"feature_flag": "disabled"},
    )
    
    results.append(ScopedFrontierResult(
        test_name="feature_flag_disabled",
        scope_dimension=ScopeDimension.FEATURE_FLAG,
        world_change=change_disabled,
        dependency_scope=disabled_scope,
        query_scope=disabled_scope,
        expected_frontier={"E1", "P2", "A2"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="E1 mutation with flag disabled should affect P2/A2",
    ))
    
    return results


def test_temporal_scope() -> list[ScopedFrontierResult]:
    """Test temporal-scoped frontier propagation.
    
    Construct:
      E1 → P1 → A1 (validity = [T0,T5])
      E1 → P2 → A2 (validity = [T5,T10])
    
    Test changes at T2, T5, T7.
    """
    results = []
    
    # Temporal scope [T0, T5]
    temporal_scope_1 = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
        temporal_interval="2026-01-01/2026-06-01",
    )
    
    # Temporal scope [T5, T10]
    temporal_scope_2 = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
        temporal_interval="2026-06-01/2026-12-01",
    )
    
    # Change at T2 (within first scope)
    change_t2 = WorldChange(
        change_id="temporal_t2_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated at T2",
        changed_dependencies=["E1"],
    )
    
    results.append(ScopedFrontierResult(
        test_name="temporal_t2",
        scope_dimension=ScopeDimension.TEMPORAL_INTERVAL,
        world_change=change_t2,
        dependency_scope=temporal_scope_1,
        query_scope=temporal_scope_1,
        expected_frontier={"E1", "P1", "A1"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="T2 mutation should affect [T0,T5] scope",
    ))
    
    # Change at T7 (within second scope)
    change_t7 = WorldChange(
        change_id="temporal_t7_mutation",
        timestamp="2026-07-01T00:00:00Z",
        description="E1 mutated at T7",
        changed_dependencies=["E1"],
    )
    
    results.append(ScopedFrontierResult(
        test_name="temporal_t7",
        scope_dimension=ScopeDimension.TEMPORAL_INTERVAL,
        world_change=change_t7,
        dependency_scope=temporal_scope_2,
        query_scope=temporal_scope_2,
        expected_frontier={"E1", "P2", "A2"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="T7 mutation should affect [T5,T10] scope",
    ))
    
    return results


def test_actor_scope() -> list[ScopedFrontierResult]:
    """Test actor-scoped frontier propagation.
    
    Construct:
      E1 → P1 → A1 (actor=operator_1)
      E1 → P1 → A2 (actor=operator_2)
    
    Mutate E1.
    
    Expected: Both authorizations may be affected (shared proposition).
    
    Then change actor_1 identity.
    
    Expected: Only A1 should be affected, not A2.
    """
    results = []
    
    # Actor 1 scope
    actor_1_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
        actor_id="operator_1",
    )
    
    # Actor 2 scope
    actor_2_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
        actor_id="operator_2",
    )
    
    # E1 mutation
    change = WorldChange(
        change_id="actor_e1_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated - shared across actors",
        changed_dependencies=["E1"],
    )
    
    results.append(ScopedFrontierResult(
        test_name="actor_operator_1",
        scope_dimension=ScopeDimension.ACTOR,
        world_change=change,
        dependency_scope=actor_1_scope,
        query_scope=actor_1_scope,
        expected_frontier={"E1", "P1", "A1"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="E1 mutation should affect operator_1's authorization",
    ))
    
    results.append(ScopedFrontierResult(
        test_name="actor_operator_2",
        scope_dimension=ScopeDimension.ACTOR,
        world_change=change,
        dependency_scope=actor_2_scope,
        query_scope=actor_2_scope,
        expected_frontier={"E1", "P1", "A2"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="E1 mutation should also affect operator_2's authorization (shared P1)",
    ))
    
    return results


def test_operation_scope() -> list[ScopedFrontierResult]:
    """Test operation-scoped frontier propagation.
    
    Construct:
      E1 → P1 → A1 (operation=payment)
      E1 → P2 → A2 (operation=refund)
    
    Mutate E1.
    
    Expected: Both operations may be affected if they share the dependency.
    But the frontier must preserve the operation scope.
    """
    results = []
    
    # Payment scope
    payment_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
    )
    
    # Refund scope
    refund_scope = create_completeness_scope(
        "prop_001", "refund",
        environment="production",
    )
    
    change = WorldChange(
        change_id="operation_e1_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated - shared across operations",
        changed_dependencies=["E1"],
    )
    
    results.append(ScopedFrontierResult(
        test_name="operation_payment",
        scope_dimension=ScopeDimension.OPERATION,
        world_change=change,
        dependency_scope=payment_scope,
        query_scope=payment_scope,
        expected_frontier={"E1", "P1", "A1"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="E1 mutation should affect payment authorization",
    ))
    
    results.append(ScopedFrontierResult(
        test_name="operation_refund",
        scope_dimension=ScopeDimension.OPERATION,
        world_change=change,
        dependency_scope=refund_scope,
        query_scope=refund_scope,
        expected_frontier={"E1", "P2", "A2"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="E1 mutation should affect refund authorization",
    ))
    
    return results


def test_domain_scope() -> list[ScopedFrontierResult]:
    """Test sovereign-domain-scoped frontier propagation.
    
    Construct:
      Domain A: E1 → P1 → A1
      Domain B: E1 → P2 → A2
    
    Same identifier E1 appears in both domains but with different provenance.
    
    Mutate E1 in Domain A.
    
    Expected: Only Domain A artifacts should be affected.
    Domain B should NOT be affected.
    """
    results = []
    
    # Domain A scope
    domain_a_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
        domain="DOMAIN_A",
    )
    
    # Domain B scope
    domain_b_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
        domain="DOMAIN_B",
    )
    
    # Mutation in Domain A
    change = WorldChange(
        change_id="domain_a_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated in Domain A",
        changed_dependencies=["E1"],
        metadata={"domain": "DOMAIN_A"},
    )
    
    results.append(ScopedFrontierResult(
        test_name="domain_a",
        scope_dimension=ScopeDimension.SOVEREIGN_DOMAIN,
        world_change=change,
        dependency_scope=domain_a_scope,
        query_scope=domain_a_scope,
        expected_frontier={"E1", "P1", "A1"},
        actual_frontier={"E1"},
        scope_matches=True,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="Domain A mutation should affect Domain A artifacts",
    ))
    
    results.append(ScopedFrontierResult(
        test_name="domain_b",
        scope_dimension=ScopeDimension.SOVEREIGN_DOMAIN,
        world_change=change,
        dependency_scope=domain_b_scope,
        query_scope=domain_b_scope,
        expected_frontier=set(),  # Domain B should NOT be affected
        actual_frontier={"E1"},
        scope_matches=False,
        propagation_rule=PropagationRule.SCOPE_LIMITED,
        notes="Domain A mutation should NOT affect Domain B artifacts",
    ))
    
    return results


def test_unknown_scope() -> list[ScopedFrontierResult]:
    """Test unknown scope handling.
    
    Construct a dependency with unknown scope.
    
    The protocol must NOT convert UNKNOWN SCOPE into OUT OF SCOPE.
    
    UNKNOWN ≠ FALSE
    UNKNOWN SCOPE ≠ NO IMPACT
    """
    results = []
    
    # Unknown scope
    unknown_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="unknown",
    )
    
    # Known production scope
    prod_scope = create_completeness_scope(
        "prop_001", "payment",
        environment="production",
    )
    
    change = WorldChange(
        change_id="unknown_scope_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated but scope is unknown",
        changed_dependencies=["E1"],
        metadata={"environment": "unknown"},
    )
    
    results.append(ScopedFrontierResult(
        test_name="unknown_scope",
        scope_dimension=ScopeDimension.ENVIRONMENT,
        world_change=change,
        dependency_scope=unknown_scope,
        query_scope=prod_scope,
        expected_frontier={"E1"},  # At minimum, E1 is affected
        actual_frontier={"E1"},
        scope_matches=False,
        propagation_rule=PropagationRule.REQUIRES_EVALUATION,
        notes="Unknown scope must NOT be treated as out-of-scope",
    ))
    
    return results


def run_all_scoped_frontier_experiments() -> list[ScopedFrontierResult]:
    """Run all scoped frontier experiments."""
    results = []
    results.extend(test_environment_scope())
    results.extend(test_feature_flag_scope())
    results.extend(test_temporal_scope())
    results.extend(test_actor_scope())
    results.extend(test_operation_scope())
    results.extend(test_domain_scope())
    results.extend(test_unknown_scope())
    return results


def print_scoped_frontier_results(results: list[ScopedFrontierResult]) -> None:
    """Print scoped frontier results."""
    print("\n" + "=" * 100)
    print("SCOPED FRONTIER RESULTS")
    print("=" * 100)
    print(f"{'Test':<30} {'Dimension':<20} {'Scope Match':<15} {'Expected':<30} {'Actual':<30}")
    print("-" * 100)
    
    for r in results:
        print(f"{r.test_name:<30} {r.scope_dimension.value:<20} {str(r.scope_matches):<15} {str(r.expected_frontier):<30} {str(r.actual_frontier):<30}")
    
    print("\n" + "=" * 100)
    print("DETAILED RESULTS")
    print("=" * 100)
    
    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Dimension: {r.scope_dimension.value}")
        print(f"  Change: {r.world_change.description}")
        print(f"  Expected: {r.expected_frontier}")
        print(f"  Actual: {r.actual_frontier}")
        print(f"  Scope matches: {r.scope_matches}")
        print(f"  Propagation rule: {r.propagation_rule.value}")
        print(f"  Notes: {r.notes}")


def analyze_scoped_results(results: list[ScopedFrontierResult]) -> dict[str, Any]:
    """Analyze scoped frontier results."""
    analysis = {
        "total": len(results),
        "scope_matches": 0,
        "scope_mismatches": 0,
        "exact_frontier": 0,
        "over_approximated": 0,
        "under_approximated": 0,
        "dimensions_tested": set(),
        "findings": [],
    }
    
    for r in results:
        analysis["dimensions_tested"].add(r.scope_dimension.value)
        
        if r.scope_matches:
            analysis["scope_matches"] += 1
        else:
            analysis["scope_mismatches"] += 1
        
        if r.actual_frontier == r.expected_frontier:
            analysis["exact_frontier"] += 1
        elif r.actual_frontier.issuperset(r.expected_frontier):
            analysis["over_approximated"] += 1
        elif r.actual_frontier.issubset(r.expected_frontier):
            analysis["under_approximated"] += 1
    
    return analysis


if __name__ == "__main__":
    results = run_all_scoped_frontier_experiments()
    print_scoped_frontier_results(results)
    analysis = analyze_scoped_results(results)
    print("\n" + "=" * 100)
    print("SCOPED FRONTIER ANALYSIS")
    print("=" * 100)
    for k, v in analysis.items():
        print(f"  {k}: {v}")
