"""Phase 3: False Minimality.

Tests whether the protocol can distinguish:
- "Nothing is affected" (empty frontier + complete graph)
- "Nothing affected has been established" (empty frontier + incomplete graph)

Uses the existing CompletenessEngine.check_intersection_status() which already
distinguishes:
- NO_RELEVANT_DEPENDENCY_EXISTS (graph complete, evidence irrelevant)
- CANNOT_DETERMINE (graph incomplete, cannot conclude)
- NO_INTERSECTION_ESTABLISHED (intersection check performed, nothing found)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessAssessment,
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
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
from research.examples.sovereign_agent.temporal_completeness import (
    CompletenessDriftFinding,
    CompletenessDriftType,
    RevalidationFrontier,
    RevalidationRequirement,
    TemporalCompletenessEngine,
)


@dataclass(frozen=True)
class FalseMinimalityResult:
    """Result of a single false-minimality test."""
    test_name: str
    actual_dependencies: list[str]
    declared_dependencies: list[str]
    change: WorldChange
    computed_frontier: set[str]
    actual_affected: ActualAffectedSet
    completeness_status: CompletenessStatus
    intersection_status: IntersectionStatus
    frontier_classification: FrontierClassification
    soundness: FrontierSoundness
    expected_interpretation: str
    notes: str = ""


def run_false_minimality_matrix() -> list[FalseMinimalityResult]:
    """Run the false-minimality matrix.
    
    Tests all combinations of:
    - Actual dependency: present/absent
    - Declared dependency: present/absent
    - Mutation: related/unrelated
    
    For each, determines whether the existing completeness semantics can
    distinguish "nothing affected" from "nothing established".
    """
    engine = TemporalCompletenessEngine()
    completeness_engine = CompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")
    results = []

    # ============================================================
    # Test 1: Complete graph, mutate related dependency
    # Expected: Frontier should find the dependency
    # ============================================================
    actual_1 = ["E1"]
    declared_1 = ["E1"]
    change_1 = WorldChange(
        change_id="fm_complete_related",
        timestamp="2026-02-01T00:00:00Z",
        description="E1 mutated, graph is complete",
        changed_propositions=["prop_001"],
    )
    graph_1 = create_dependency_graph({"A": ["E1"]})
    propositions_1 = {"prop_001": ["A"]}
    authorizations_1 = {"auth_001": ["prop_001"]}

    actual_affected_1 = compute_actual_affected_set(
        change_1, graph_1, propositions_1, authorizations_1,
    )

    # Assess completeness
    comp_assessment_1 = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared_1, actual_1, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    # Check intersection status for E1
    intersection_1 = completeness_engine.check_intersection_status(
        "E1", declared_1, comp_assessment_1,
    )

    # Compute frontier
    drift_event_1 = AuthorityDriftEvent(
        event_id="fm_event_1",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E1 mutated",
        affected_actor="A",
        affected_component="A",
        previous_state={"E1": "old"},
        new_state={"E1": "new"},
    )
    frontier_1 = engine.compute_revalidation_frontier(
        drift_event_1, "auth_001", declared_1, "prop_001", "payment", scope,
    )

    results.append(FalseMinimalityResult(
        test_name="complete_graph_related_mutation",
        actual_dependencies=actual_1,
        declared_dependencies=declared_1,
        change=change_1,
        computed_frontier=set(frontier_1.affected_dependencies),
        actual_affected=actual_affected_1,
        completeness_status=comp_assessment_1.overall_status,
        intersection_status=intersection_1,
        frontier_classification=FrontierClassification.EXACT,
        soundness=FrontierSoundness.SOUND,
        expected_interpretation="EFFECT ESTABLISHED: frontier finds the dependency",
        notes="Complete graph + related mutation = frontier should be non-empty",
    ))

    # ============================================================
    # Test 2: Incomplete graph, mutate UNDECLARED dependency
    # Expected: Frontier is empty BUT completeness is KNOWN_INCOMPLETE
    # This is the critical false-minimality case
    # ============================================================
    actual_2 = ["E1", "E2", "E3"]
    declared_2 = ["E1"]
    change_2 = WorldChange(
        change_id="fm_incomplete_undeclared",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 mutated but E2 is NOT in declared graph",
        changed_propositions=["prop_001"],
    )
    graph_2 = create_dependency_graph({"A": ["E1", "E2", "E3"]})
    propositions_2 = {"prop_001": ["A"]}
    authorizations_2 = {"auth_001": ["prop_001"]}

    actual_affected_2 = compute_actual_affected_set(
        change_2, graph_2, propositions_2, authorizations_2,
    )

    # Assess completeness
    comp_assessment_2 = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared_2, actual_2, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    # Check intersection status for E2
    intersection_2 = completeness_engine.check_intersection_status(
        "E2", declared_2, comp_assessment_2,
    )

    # Compute frontier (will be empty because E2 not in declared graph)
    drift_event_2 = AuthorityDriftEvent(
        event_id="fm_event_2",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E2 mutated",
        affected_actor="A",
        affected_component="A",
        previous_state={"E2": "old"},
        new_state={"E2": "new"},
    )
    frontier_2 = engine.compute_revalidation_frontier(
        drift_event_2, "auth_001", declared_2, "prop_001", "payment", scope,
    )

    results.append(FalseMinimalityResult(
        test_name="incomplete_graph_undeclared_mutation",
        actual_dependencies=actual_2,
        declared_dependencies=declared_2,
        change=change_2,
        computed_frontier=set(frontier_2.affected_dependencies),
        actual_affected=actual_affected_2,
        completeness_status=comp_assessment_2.overall_status,
        intersection_status=intersection_2,
        frontier_classification=FrontierClassification.UNDER_APPROXIMATED,
        soundness=FrontierSoundness.UNSOUND,
        expected_interpretation="NO EFFECT ESTABLISHED: empty frontier + incomplete graph = cannot conclude",
        notes="CRITICAL: Frontier is empty but graph is incomplete. Protocol must NOT conclude 'no effect'.",
    ))

    # ============================================================
    # Test 3: Complete graph, mutate UNRELATED dependency
    # Expected: Frontier is empty AND completeness is KNOWN_COMPLETE
    # This is the one case where empty frontier is meaningful
    # ============================================================
    actual_3 = ["E1"]
    declared_3 = ["E1"]
    change_3 = WorldChange(
        change_id="fm_complete_unrelated",
        timestamp="2026-02-01T00:00:00Z",
        description="E99 mutated but E99 is unrelated to A",
    )
    graph_3 = create_dependency_graph({"A": ["E1"], "C": ["E99"]})
    propositions_3 = {"prop_001": ["A"], "prop_002": ["C"]}
    authorizations_3 = {"auth_001": ["prop_001"], "auth_002": ["prop_002"]}

    actual_affected_3 = compute_actual_affected_set(
        change_3, graph_3, propositions_3, authorizations_3,
    )

    comp_assessment_3 = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared_3, actual_3, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection_3 = completeness_engine.check_intersection_status(
        "E99", declared_3, comp_assessment_3,
    )

    drift_event_3 = AuthorityDriftEvent(
        event_id="fm_event_3",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E99 mutated",
        affected_actor="C",
        affected_component="C",
        previous_state={"E99": "old"},
        new_state={"E99": "new"},
    )
    frontier_3 = engine.compute_revalidation_frontier(
        drift_event_3, "auth_001", declared_3, "prop_001", "payment", scope,
    )

    results.append(FalseMinimalityResult(
        test_name="complete_graph_unrelated_mutation",
        actual_dependencies=actual_3,
        declared_dependencies=declared_3,
        change=change_3,
        computed_frontier=set(frontier_3.affected_dependencies),
        actual_affected=actual_affected_3,
        completeness_status=comp_assessment_3.overall_status,
        intersection_status=intersection_3,
        frontier_classification=FrontierClassification.EXACT,
        soundness=FrontierSoundness.SOUND,
        expected_interpretation="NO EFFECT ESTABLISHED: empty frontier + complete graph = genuinely no effect",
        notes="Complete graph + unrelated mutation = frontier should be empty AND trustworthy",
    ))

    # ============================================================
    # Test 4: Incomplete graph, mutate UNRELATED dependency
    # Expected: Frontier is empty, completeness is KNOWN_INCOMPLETE
    # Cannot distinguish "E99 is truly unrelated" from "E99's relationship unknown"
    # ============================================================
    actual_4 = ["E1", "E2"]
    declared_4 = ["E1"]
    change_4 = WorldChange(
        change_id="fm_incomplete_unrelated",
        timestamp="2026-02-01T00:00:00Z",
        description="E99 mutated, graph is incomplete",
    )
    graph_4 = create_dependency_graph({"A": ["E1", "E2"], "C": ["E99"]})
    propositions_4 = {"prop_001": ["A"], "prop_002": ["C"]}
    authorizations_4 = {"auth_001": ["prop_001"], "auth_002": ["prop_002"]}

    actual_affected_4 = compute_actual_affected_set(
        change_4, graph_4, propositions_4, authorizations_4,
    )

    comp_assessment_4 = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared_4, actual_4, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection_4 = completeness_engine.check_intersection_status(
        "E99", declared_4, comp_assessment_4,
    )

    drift_event_4 = AuthorityDriftEvent(
        event_id="fm_event_4",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E99 mutated",
        affected_actor="C",
        affected_component="C",
        previous_state={"E99": "old"},
        new_state={"E99": "new"},
    )
    frontier_4 = engine.compute_revalidation_frontier(
        drift_event_4, "auth_001", declared_4, "prop_001", "payment", scope,
    )

    results.append(FalseMinimalityResult(
        test_name="incomplete_graph_unrelated_mutation",
        actual_dependencies=actual_4,
        declared_dependencies=declared_4,
        change=change_4,
        computed_frontier=set(frontier_4.affected_dependencies),
        actual_affected=actual_affected_4,
        completeness_status=comp_assessment_4.overall_status,
        intersection_status=intersection_4,
        frontier_classification=FrontierClassification.UNDER_APPROXIMATED,
        soundness=FrontierSoundness.UNKNOWN,
        expected_interpretation="UNKNOWN: empty frontier + incomplete graph = cannot establish irrelevance",
        notes="Graph incomplete, so cannot establish that E99 is truly unrelated to A",
    ))

    # ============================================================
    # Test 5: Complete graph, mutate declared dependency
    # Expected: Frontier is non-empty, completeness is KNOWN_COMPLETE
    # ============================================================
    actual_5 = ["E1", "E2", "E3"]
    declared_5 = ["E1", "E2", "E3"]
    change_5 = WorldChange(
        change_id="fm_complete_declared",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 mutated, graph is complete",
        changed_propositions=["prop_001"],
    )
    graph_5 = create_dependency_graph({"A": ["E1", "E2", "E3"]})
    propositions_5 = {"prop_001": ["A"]}
    authorizations_5 = {"auth_001": ["prop_001"]}

    actual_affected_5 = compute_actual_affected_set(
        change_5, graph_5, propositions_5, authorizations_5,
    )

    comp_assessment_5 = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared_5, actual_5, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection_5 = completeness_engine.check_intersection_status(
        "E2", declared_5, comp_assessment_5,
    )

    drift_event_5 = AuthorityDriftEvent(
        event_id="fm_event_5",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E2 mutated",
        affected_actor="A",
        affected_component="A",
        previous_state={"E2": "old"},
        new_state={"E2": "new"},
    )
    frontier_5 = engine.compute_revalidation_frontier(
        drift_event_5, "auth_001", declared_5, "prop_001", "payment", scope,
    )

    results.append(FalseMinimalityResult(
        test_name="complete_graph_declared_mutation",
        actual_dependencies=actual_5,
        declared_dependencies=declared_5,
        change=change_5,
        computed_frontier=set(frontier_5.affected_dependencies),
        actual_affected=actual_affected_5,
        completeness_status=comp_assessment_5.overall_status,
        intersection_status=intersection_5,
        frontier_classification=FrontierClassification.EXACT,
        soundness=FrontierSoundness.SOUND,
        expected_interpretation="EFFECT ESTABLISHED: non-empty frontier + complete graph = trustworthy",
        notes="Complete graph + declared dependency mutation = frontier is trustworthy",
    ))

    return results


def print_false_minimality_matrix(results: list[FalseMinimalityResult]) -> None:
    """Print the false-minimality matrix."""
    print("\n" + "=" * 80)
    print("FALSE-MINIMALITY MATRIX")
    print("=" * 80)
    print(f"{'Test':<40} {'Complete':<12} {'Intersect':<25} {'Expected'}")
    print("-" * 80)

    for r in results:
        print(f"{r.test_name:<40} {r.completeness_status.value:<12} {r.intersection_status.value:<25} {r.expected_interpretation}")

    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Actual deps: {r.actual_dependencies}")
        print(f"  Declared deps: {r.declared_dependencies}")
        print(f"  Change: {r.change.description}")
        print(f"  Computed frontier: {r.computed_frontier}")
        print(f"  Actual affected: {r.actual_affected.to_set()}")
        print(f"  Completeness: {r.completeness_status.value}")
        print(f"  Intersection: {r.intersection_status.value}")
        print(f"  Classification: {r.frontier_classification.value}")
        print(f"  Soundness: {r.soundness.value}")
        print(f"  Expected: {r.expected_interpretation}")
        if r.notes:
            print(f"  Notes: {r.notes}")


def analyze_completeness_semantics(results: list[FalseMinimalityResult]) -> dict[str, Any]:
    """Analyze whether existing completeness semantics are sufficient."""
    analysis = {
        "total_tests": len(results),
        "complete_graph_empty_frontier": 0,
        "incomplete_graph_empty_frontier": 0,
        "intersection_distinction_works": True,
        "missing_semantics": [],
    }

    for r in results:
        # Count empty frontiers by completeness
        if not r.computed_frontier:
            if r.completeness_status == CompletenessStatus.KNOWN_COMPLETE:
                analysis["complete_graph_empty_frontier"] += 1
            elif r.completeness_status in (
                CompletenessStatus.KNOWN_INCOMPLETE,
                CompletenessStatus.UNKNOWN,
            ):
                analysis["incomplete_graph_empty_frontier"] += 1

        # Check if intersection status correctly distinguishes
        if r.completeness_status == CompletenessStatus.KNOWN_COMPLETE:
            if r.intersection_status not in (
                IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS,
                IntersectionStatus.INTERSECTION_FOUND,
            ):
                analysis["intersection_distinction_works"] = False
                analysis["missing_semantics"].append(
                    f"{r.test_name}: complete graph but intersection={r.intersection_status}"
                )
        elif r.completeness_status in (
            CompletenessStatus.KNOWN_INCOMPLETE,
            CompletenessStatus.UNKNOWN,
        ):
            if r.intersection_status == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS:
                analysis["intersection_distinction_works"] = False
                analysis["missing_semantics"].append(
                    f"{r.test_name}: incomplete graph but intersection=NO_RELEVANT_DEPENDENCY_EXISTS"
                )

    return analysis


if __name__ == "__main__":
    results = run_false_minimality_matrix()
    print_false_minimality_matrix(results)
    analysis = analyze_completeness_semantics(results)
    print("\n" + "=" * 80)
    print("COMPLETENESS SEMANTICS ANALYSIS")
    print("=" * 80)
    for k, v in analysis.items():
        print(f"  {k}: {v}")
