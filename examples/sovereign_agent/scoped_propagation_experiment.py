"""Phase 5.5 experiments: Scoped Impact Propagation validation.

Validates the ScopedImpactPropagationEngine against the semantic requirements
established in Phase 4.5 and Phase 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from examples.self_audit.authority_drift import AuthorityDriftEvent
from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    DependencyStrength,
    DependencyType,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_completeness import (
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.scoped_impact_propagation import (
    ScopedFrontier,
    ScopedImpactPropagationEngine,
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)


@dataclass
class PropagationExperimentResult:
    """Result of a propagation experiment."""
    test_name: str
    changed_dependency: str
    expected_members: set[str]
    actual_members: set[str]
    expected_by_type: dict[str, set[str]]
    actual_by_type: dict[str, set[str]]
    completeness_status: CompletenessStatus
    intersection_status: IntersectionStatus
    scope_matches: bool
    notes: str = ""


def run_typed_propagation_experiment() -> list[PropagationExperimentResult]:
    """Test typed semantic propagation through the chain.
    
    Chain: E1 → P1 → S1 → A1
    
    Expected: Impact propagates through each typed relationship.
    """
    engine = ScopedImpactPropagationEngine()
    scope = create_completeness_scope("prop_001", "payment")

    dep_graph = build_authorization_dependency_graph(
        authorization_id="auth_001",
        evidence_ids=["E1"],
        proposition_id="P1",
        epistemic_state_id="S1",
        experiment_id="exp_001",
        recommendation_id="rec_001",
        governance_policy_id="gov_001",
        resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01",
        provenance=["src_001"],
    )

    proposition_graph = create_scoped_proposition_graph({"P1": ["E1"]})
    authorization_graph = create_scoped_authorization_graph({"A1": ["P1"]})

    change = AuthorityDriftEvent(
        event_id="typed_e1_mutated",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E1 mutated",
        affected_actor="A1",
        affected_component="A1",
        previous_state={"E1": "old"},
        new_state={"E1": "new"},
    )

    frontier = engine.compute_scoped_frontier(
        world_change=change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        actual_dependencies=["E1"],
    )

    expected = {"E1", "P1", "A1"}
    actual = frontier.get_member_ids()

    return [PropagationExperimentResult(
        test_name="typed_propagation",
        changed_dependency="E1",
        expected_members=expected,
        actual_members=actual,
        expected_by_type={"dependency": {"E1"}, "proposition": {"P1"}, "authorization": {"A1"}},
        actual_by_type={
            "dependency": {m.artifact_id for m in frontier.get_members_by_type("dependency")},
            "proposition": {m.artifact_id for m in frontier.get_members_by_type("proposition")},
            "authorization": {m.artifact_id for m in frontier.get_members_by_type("authorization")},
        },
        completeness_status=frontier.completeness_status,
        intersection_status=frontier.intersection_status,
        scope_matches=True,
        notes="Typed propagation: E1→P1→A1",
    )]


def run_scope_mismatch_experiment() -> list[PropagationExperimentResult]:
    """Test scope mismatch handling.
    
    Without artifact-specific scope metadata, the system cannot determine
    that P1 and A1 are production-scoped, so they are included in the frontier.
    
    This documents a limitation: artifact-specific scope metadata is needed
    for proper scope enforcement.
    """
    engine = ScopedImpactPropagationEngine()
    scope = create_completeness_scope("prop_001", "payment", environment="staging")

    dep_graph = build_authorization_dependency_graph(
        authorization_id="auth_001",
        evidence_ids=["E1"],
        proposition_id="P1",
        epistemic_state_id="S1",
        experiment_id="exp_001",
        recommendation_id="rec_001",
        governance_policy_id="gov_001",
        resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01",
        provenance=["src_001"],
    )

    proposition_graph = create_scoped_proposition_graph({"P1": ["E1"]})
    authorization_graph = create_scoped_authorization_graph({"A1": ["P1"]})

    change = AuthorityDriftEvent(
        event_id="scope_mismatch_e1",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E1 mutated",
        affected_actor="A1",
        affected_component="A1",
        previous_state={"E1": "old"},
        new_state={"E1": "new"},
    )

    frontier = engine.compute_scoped_frontier(
        world_change=change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        actual_dependencies=["E1"],
    )

    # WITHOUT artifact-specific scope metadata, the system includes all artifacts
    # This documents a limitation that requires scope metadata on artifacts
    expected = {"E1"}  # Minimum: the dependency itself
    actual = frontier.get_member_ids()
    
    # Note: Actual includes P1 and A1 because there's no scope metadata to exclude them
    # This is a known limitation that requires artifact-specific scope metadata

    return [PropagationExperimentResult(
        test_name="scope_mismatch",
        changed_dependency="E1",
        expected_members=expected,
        actual_members=actual,
        expected_by_type={"dependency": {"E1"}},
        actual_by_type={
            "dependency": {m.artifact_id for m in frontier.get_members_by_type("dependency")},
            "proposition": {m.artifact_id for m in frontier.get_members_by_type("proposition")},
            "authorization": {m.artifact_id for m in frontier.get_members_by_type("authorization")},
        },
        completeness_status=frontier.completeness_status,
        intersection_status=frontier.intersection_status,
        scope_matches=False,
        notes="LIMITATION: Without artifact scope metadata, system includes all artifacts",
    )]


def run_unknown_scope_experiment() -> list[PropagationExperimentResult]:
    """Test unknown scope handling.
    
    E1 changed, scope = unknown.
    
    Expected: UNKNOWN, not empty frontier.
    """
    engine = ScopedImpactPropagationEngine()
    scope = create_completeness_scope("prop_001", "payment", environment="unknown")

    dep_graph = build_authorization_dependency_graph(
        authorization_id="auth_001",
        evidence_ids=["E1"],
        proposition_id="P1",
        epistemic_state_id="S1",
        experiment_id="exp_001",
        recommendation_id="rec_001",
        governance_policy_id="gov_001",
        resource_id="res_001",
        temporal_interval="2026-01-01/2027-01-01",
        provenance=["src_001"],
    )

    proposition_graph = create_scoped_proposition_graph({"P1": ["E1"]})
    authorization_graph = create_scoped_authorization_graph({"A1": ["P1"]})

    change = AuthorityDriftEvent(
        event_id="unknown_scope_e1",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E1 mutated",
        affected_actor="A1",
        affected_component="A1",
        previous_state={"E1": "old"},
        new_state={"E1": "new"},
    )

    frontier = engine.compute_scoped_frontier(
        world_change=change,
        authorization_id="auth_001",
        dependency_graph=dep_graph,
        proposition_graph=proposition_graph,
        authorization_graph=authorization_graph,
        scope=scope,
        actual_dependencies=["E1"],
    )

    # Expected: E1 (at minimum), but completeness should be unknown
    expected = {"E1"}
    actual = frontier.get_member_ids()

    return [PropagationExperimentResult(
        test_name="unknown_scope",
        changed_dependency="E1",
        expected_members=expected,
        actual_members=actual,
        expected_by_type={"dependency": {"E1"}},
        actual_by_type={
            "dependency": {m.artifact_id for m in frontier.get_members_by_type("dependency")},
            "proposition": {m.artifact_id for m in frontier.get_members_by_type("proposition")},
            "authorization": {m.artifact_id for m in frontier.get_members_by_type("authorization")},
        },
        completeness_status=frontier.completeness_status,
        intersection_status=frontier.intersection_status,
        scope_matches=False,
        notes="Unknown scope: should not be treated as out-of-scope",
    )]


def run_all_propagation_experiments() -> list[PropagationExperimentResult]:
    """Run all propagation experiments."""
    results = []
    results.extend(run_typed_propagation_experiment())
    results.extend(run_scope_mismatch_experiment())
    results.extend(run_unknown_scope_experiment())
    return results


def print_experiment_results(results: list[PropagationExperimentResult]) -> None:
    """Print experiment results."""
    print("\n" + "=" * 100)
    print("SCOPED IMPACT PROPAGATION EXPERIMENTS")
    print("=" * 100)
    print(f"{'Test':<40} {'Expected':<25} {'Actual':<25} {'Match?':<10}")
    print("-" * 100)

    for r in results:
        match = "✅" if r.expected_members == r.actual_members else "❌"
        print(f"{r.test_name:<40} {str(r.expected_members):<25} {str(r.actual_members):<25} {match:<10}")

    print("\n" + "=" * 100)
    print("DETAILED RESULTS")
    print("=" * 100)

    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Changed: {r.changed_dependency}")
        print(f"  Expected: {r.expected_members}")
        print(f"  Actual: {r.actual_members}")
        print(f"  Expected by type: {r.expected_by_type}")
        print(f"  Actual by type: {r.actual_by_type}")
        print(f"  Completeness: {r.completeness_status.value}")
        print(f"  Intersection: {r.intersection_status.value}")
        print(f"  Scope matches: {r.scope_matches}")
        print(f"  Notes: {r.notes}")


if __name__ == "__main__":
    results = run_all_propagation_experiments()
    print_experiment_results(results)
