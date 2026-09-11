"""Phase 2: Baseline Frontier Soundness.

Tests whether the existing RevalidationFrontier correctly identifies:
- Direct dependency changes
- Transitive dependency changes
- Unrelated dependency changes
- Shared dependency changes

Uses the existing TemporalCompletenessEngine.compute_revalidation_frontier()
and compares computed frontiers against ground truth affected sets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessScope,
    create_completeness_scope,
)
from research.examples.sovereign_agent.revalidation_experiment import (
    ActualAffectedSet,
    FrontierEvaluation,
    RevalidationExperiment,
    WorldChange,
    compute_actual_affected_set,
    create_dependency_graph,
)
from research.examples.sovereign_agent.temporal_completeness import (
    TemporalCompletenessEngine,
)


@dataclass
class BaselineSoundnessResult:
    """Result of a single baseline soundness test."""
    test_name: str
    change: WorldChange
    dependency_graph: dict[str, list[str]]
    computed_frontier: set[str]
    actual_affected: ActualAffectedSet
    evaluation: FrontierEvaluation


def run_baseline_frontier_soundness() -> list[BaselineSoundnessResult]:
    """Run baseline frontier soundness experiments."""
    engine = TemporalCompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")
    experiment = RevalidationExperiment()
    results = []

    # ============================================================
    # Test 1: Direct dependency change
    # ============================================================
    # A depends on E1, E2, E3
    # Change: E2 added (new dependency)
    # Expected: A is affected
    graph_1 = create_dependency_graph({
        "A": ["E1", "E2", "E3"],
    })
    change_1 = WorldChange(
        change_id="change_direct",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 added as dependency of A",
        added_dependencies=["E2"],
    )
    propositions_1 = {"prop_001": ["A"]}
    authorizations_1 = {"auth_001": ["prop_001"]}

    actual_1 = compute_actual_affected_set(
        change_1, graph_1, propositions_1, authorizations_1,
    )

    # Compute frontier using the protocol
    drift_event_1 = AuthorityDriftEvent(
        event_id="event_direct",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_added",
        description="E2 added",
        affected_actor="A",
        affected_component="A",
        previous_state={"deps": ["E1", "E3"]},
        new_state={"deps": ["E1", "E2", "E3"]},
    )
    frontier_1 = engine.compute_revalidation_frontier(
        drift_event_1,
        "auth_001",
        ["E1", "E2", "E3"],
        "prop_001",
        "payment",
        scope,
    )

    evaluation_1 = experiment.evaluate_frontier(
        change_1,
        set(frontier_1.affected_dependencies + frontier_1.affected_authorizations),
        actual_1,
    )

    results.append(BaselineSoundnessResult(
        test_name="direct_dependency",
        change=change_1,
        dependency_graph=graph_1,
        computed_frontier=set(frontier_1.affected_dependencies),
        actual_affected=actual_1,
        evaluation=evaluation_1,
    ))

    # ============================================================
    # Test 2: Transitive dependency change
    # ============================================================
    # A depends on B, B depends on E1
    # Change: E1 added
    # Expected: B and A are affected (transitive)
    graph_2 = create_dependency_graph({
        "A": ["B"],
        "B": ["E1"],
    })
    change_2 = WorldChange(
        change_id="change_transitive",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 added as dependency of B (transitive to A)",
        added_dependencies=["E1"],
    )
    propositions_2 = {"prop_001": ["A", "B"]}
    authorizations_2 = {"auth_001": ["prop_001"]}

    actual_2 = compute_actual_affected_set(
        change_2, graph_2, propositions_2, authorizations_2,
    )

    drift_event_2 = AuthorityDriftEvent(
        event_id="event_transitive",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_added",
        description="E1 added",
        affected_actor="B",
        affected_component="B",
        previous_state={"deps": []},
        new_state={"deps": ["E1"]},
    )
    frontier_2 = engine.compute_revalidation_frontier(
        drift_event_2,
        "auth_001",
        ["B", "E1"],
        "prop_001",
        "payment",
        scope,
    )

    evaluation_2 = experiment.evaluate_frontier(
        change_2,
        set(frontier_2.affected_dependencies + frontier_2.affected_authorizations),
        actual_2,
    )

    results.append(BaselineSoundnessResult(
        test_name="transitive_dependency",
        change=change_2,
        dependency_graph=graph_2,
        computed_frontier=set(frontier_2.affected_dependencies),
        actual_affected=actual_2,
        evaluation=evaluation_2,
    ))

    # ============================================================
    # Test 3: Unrelated dependency change
    # ============================================================
    # A depends on E1, E2
    # C depends on E3
    # Change: E3 added (unrelated to A)
    # Expected: C is affected, A is NOT affected
    graph_3 = create_dependency_graph({
        "A": ["E1", "E2"],
        "C": ["E3"],
    })
    change_3 = WorldChange(
        change_id="change_unrelated",
        timestamp="2026-02-01T00:00:00Z",
        description="E3 added as dependency of C (unrelated to A)",
        added_dependencies=["E3"],
    )
    propositions_3 = {"prop_001": ["A"], "prop_002": ["C"]}
    authorizations_3 = {"auth_001": ["prop_001"], "auth_002": ["prop_002"]}

    actual_3 = compute_actual_affected_set(
        change_3, graph_3, propositions_3, authorizations_3,
    )

    drift_event_3 = AuthorityDriftEvent(
        event_id="event_unrelated",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_added",
        description="E3 added",
        affected_actor="C",
        affected_component="C",
        previous_state={"deps": []},
        new_state={"deps": ["E3"]},
    )
    frontier_3 = engine.compute_revalidation_frontier(
        drift_event_3,
        "auth_001",
        ["E1", "E2"],
        "prop_001",
        "payment",
        scope,
    )

    evaluation_3 = experiment.evaluate_frontier(
        change_3,
        set(frontier_3.affected_dependencies + frontier_3.affected_authorizations),
        actual_3,
    )

    results.append(BaselineSoundnessResult(
        test_name="unrelated_dependency",
        change=change_3,
        dependency_graph=graph_3,
        computed_frontier=set(frontier_3.affected_dependencies),
        actual_affected=actual_3,
        evaluation=evaluation_3,
    ))

    # ============================================================
    # Test 4: Shared dependency change
    # ============================================================
    # A depends on E1, E2
    # B depends on E2, E3
    # Change: E2 added (shared between A and B)
    # Expected: Both A and B are affected
    graph_4 = create_dependency_graph({
        "A": ["E1", "E2"],
        "B": ["E2", "E3"],
    })
    change_4 = WorldChange(
        change_id="change_shared",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 added as shared dependency of A and B",
        added_dependencies=["E2"],
    )
    propositions_4 = {"prop_001": ["A"], "prop_002": ["B"]}
    authorizations_4 = {"auth_001": ["prop_001"], "auth_002": ["prop_002"]}

    actual_4 = compute_actual_affected_set(
        change_4, graph_4, propositions_4, authorizations_4,
    )

    drift_event_4 = AuthorityDriftEvent(
        event_id="event_shared",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_added",
        description="E2 added",
        affected_actor="A",
        affected_component="A",
        previous_state={"deps": ["E1"]},
        new_state={"deps": ["E1", "E2"]},
    )
    frontier_4 = engine.compute_revalidation_frontier(
        drift_event_4,
        "auth_001",
        ["E1", "E2"],
        "prop_001",
        "payment",
        scope,
    )

    evaluation_4 = experiment.evaluate_frontier(
        change_4,
        set(frontier_4.affected_dependencies + frontier_4.affected_authorizations),
        actual_4,
    )

    results.append(BaselineSoundnessResult(
        test_name="shared_dependency",
        change=change_4,
        dependency_graph=graph_4,
        computed_frontier=set(frontier_4.affected_dependencies),
        actual_affected=actual_4,
        evaluation=evaluation_4,
    ))

    return results


def print_baseline_results(results: list[BaselineSoundnessResult]) -> None:
    """Print baseline soundness results."""
    for r in results:
        print(f"\n{'='*60}")
        print(f"Test: {r.test_name}")
        print(f"Change: {r.change.description}")
        print(f"Graph: {r.dependency_graph}")
        print(f"Computed frontier: {r.computed_frontier}")
        print(f"Actual affected: {r.actual_affected.to_set()}")
        print(f"Classification: {r.evaluation.classification}")
        print(f"Soundness: {r.evaluation.soundness}")
        if r.evaluation.missing_artifacts:
            print(f"Missing: {r.evaluation.missing_artifacts}")
        if r.evaluation.extra_artifacts:
            print(f"Extra: {r.evaluation.extra_artifacts}")


if __name__ == "__main__":
    results = run_baseline_frontier_soundness()
    print_baseline_results(results)
