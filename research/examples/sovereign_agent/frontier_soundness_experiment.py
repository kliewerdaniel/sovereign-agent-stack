"""Phase 4: Frontier Soundness Semantics.

Tests whether the protocol can establish frontier soundness independently from
the dependency model that generated the frontier.

Key distinction:
- FRONTIER IS CONSISTENT WITH KNOWN DEPENDENCIES (what the protocol can establish)
- FRONTIER IS SOUND WITH RESPECT TO THE WORLD (what we want)

These are not the same. The experiment determines whether SAS can tell the difference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    FrontierSoundness,
    RevalidationExperiment,
    WorldChange,
    compute_actual_affected_set,
    create_dependency_graph,
)
from research.examples.sovereign_agent.temporal_completeness import (
    TemporalCompletenessEngine,
)


@dataclass(frozen=True)
class FrontierSoundnessResult:
    """Result of a frontier soundness experiment."""
    test_name: str
    world_name: str
    actual_dependencies: list[str]  # Ground truth
    declared_dependencies: list[str]  # Protocol knowledge
    change: WorldChange
    computed_frontier: set[str]  # What the protocol computes
    actual_affected: ActualAffectedSet  # Ground truth
    completeness_status: CompletenessStatus
    intersection_status: IntersectionStatus
    protocol_classification: FrontierClassification  # Protocol's self-classification
    experimental_classification: FrontierClassification  # Ground truth classification
    protocol_soundness: FrontierSoundness
    experimental_soundness: FrontierSoundness
    notes: str = ""


def run_world_a_exact_graph() -> list[FrontierSoundnessResult]:
    """World A: Exact graph.
    
    Actual == Declared, so the frontier should exactly match the actual affected set.
    This is the ideal case where the protocol has perfect dependency knowledge.
    """
    engine = TemporalCompletenessEngine()
    completeness_engine = CompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")
    results = []

    # A → E1, A → E2
    # Mutate E2
    actual = ["E1", "E2"]
    declared = ["E1", "E2"]
    change = WorldChange(
        change_id="world_a_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 mutated in exact graph",
        changed_dependencies=["E2"],
    )
    graph = create_dependency_graph({"A": ["E1", "E2"]})
    propositions = {"prop_001": ["A"]}
    authorizations = {"auth_001": ["prop_001"]}

    actual_affected = compute_actual_affected_set(change, graph, propositions, authorizations)

    comp = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared, actual, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection = completeness_engine.check_intersection_status("E2", declared, comp)

    drift_event = AuthorityDriftEvent(
        event_id="world_a_event",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E2 mutated",
        affected_actor="A",
        affected_component="A",
        previous_state={"E2": "old"},
        new_state={"E2": "new"},
    )
    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", declared, "prop_001", "payment", scope,
    )

    # Protocol classification: based on its own knowledge
    computed = set(frontier.affected_dependencies)
    actual_set = actual_affected.to_set()

    # Experimental classification: compare computed frontier to actual affected set
    if computed == actual_set:
        experimental_classification = FrontierClassification.EXACT
    elif computed.issuperset(actual_set):
        experimental_classification = FrontierClassification.OVER_APPROXIMATED
    elif computed.issubset(actual_set):
        experimental_classification = FrontierClassification.UNDER_APPROXIMATED
    else:
        experimental_classification = FrontierClassification.OVER_APPROXIMATED

    # Experimental soundness: does computed frontier contain all actual affected?
    if actual_set.issubset(computed):
        experimental_soundness = FrontierSoundness.SOUND
    elif computed >= actual_set:
        experimental_soundness = FrontierSoundness.SOUND
    else:
        experimental_soundness = FrontierSoundness.UNSOUND

    # Protocol soundness: based on completeness + intersection
    if comp.overall_status == CompletenessStatus.KNOWN_COMPLETE:
        if intersection == IntersectionStatus.INTERSECTION_FOUND:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        elif intersection == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        else:
            protocol_classification = FrontierClassification.UNDER_APPROXIMATED
            protocol_soundness = FrontierSoundness.UNKNOWN
    elif comp.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNSOUND
    else:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNKNOWN

    results.append(FrontierSoundnessResult(
        test_name="exact_graph",
        world_name="A",
        actual_dependencies=actual,
        declared_dependencies=declared,
        change=change,
        computed_frontier=computed,
        actual_affected=actual_affected,
        completeness_status=comp.overall_status,
        intersection_status=intersection,
        protocol_classification=protocol_classification,
        experimental_classification=experimental_classification,
        protocol_soundness=protocol_soundness,
        experimental_soundness=experimental_soundness,
        notes="Exact graph: protocol has perfect dependency knowledge",
    ))

    return results


def run_world_b_safe_over_approximation() -> list[FrontierSoundnessResult]:
    """World B: Safe over-approximation.
    
    Declared graph has extra dependencies not in actual graph.
    The frontier should be conservatively larger than the actual affected set.
    This is safe but not exact.
    """
    engine = TemporalCompletenessEngine()
    completeness_engine = CompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")
    results = []

    # Actual: A → E1
    # Declared: A → E1, A → E2, A → E3
    # Mutate E2 (which is in declared but not actual)
    actual = ["E1"]
    declared = ["E1", "E2", "E3"]
    change = WorldChange(
        change_id="world_b_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 mutated (over-approximated graph)",
        changed_dependencies=["E2"],
    )
    graph = create_dependency_graph({"A": ["E1"]})
    propositions = {"prop_001": ["A"]}
    authorizations = {"auth_001": ["prop_001"]}

    actual_affected = compute_actual_affected_set(change, graph, propositions, authorizations)

    comp = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared, actual, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection = completeness_engine.check_intersection_status("E2", declared, comp)

    drift_event = AuthorityDriftEvent(
        event_id="world_b_event",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E2 mutated",
        affected_actor="A",
        affected_component="A",
        previous_state={"E2": "old"},
        new_state={"E2": "new"},
    )
    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", declared, "prop_001", "payment", scope,
    )

    computed = set(frontier.affected_dependencies)
    actual_set = actual_affected.to_set()

    # Experimental classification
    if computed == actual_set:
        experimental_classification = FrontierClassification.EXACT
    elif computed.issuperset(actual_set):
        experimental_classification = FrontierClassification.OVER_APPROXIMATED
    elif computed.issubset(actual_set):
        experimental_classification = FrontierClassification.UNDER_APPROXIMATED
    else:
        experimental_classification = FrontierClassification.OVER_APPROXIMATED

    # Experimental soundness
    if actual_set.issubset(computed):
        experimental_soundness = FrontierSoundness.SOUND
    else:
        experimental_soundness = FrontierSoundness.UNSOUND

    # Protocol soundness: based on completeness + intersection
    if comp.overall_status == CompletenessStatus.KNOWN_COMPLETE:
        if intersection == IntersectionStatus.INTERSECTION_FOUND:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        elif intersection == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        else:
            protocol_classification = FrontierClassification.UNDER_APPROXIMATED
            protocol_soundness = FrontierSoundness.UNKNOWN
    elif comp.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNSOUND
    else:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNKNOWN

    results.append(FrontierSoundnessResult(
        test_name="safe_over_approximation",
        world_name="B",
        actual_dependencies=actual,
        declared_dependencies=declared,
        change=change,
        computed_frontier=computed,
        actual_affected=actual_affected,
        completeness_status=comp.overall_status,
        intersection_status=intersection,
        protocol_classification=protocol_classification,
        experimental_classification=experimental_classification,
        protocol_soundness=protocol_soundness,
        experimental_soundness=experimental_soundness,
        notes="Over-approximated graph: frontier is conservatively larger (safe)",
    ))

    return results


def run_world_c_unsafe_under_approximation() -> list[FrontierSoundnessResult]:
    """World C: Unsafe under-approximation.
    
    Declared graph is missing dependencies that exist in actual graph.
    The frontier will be smaller than the actual affected set.
    This is the dangerous case.
    """
    engine = TemporalCompletenessEngine()
    completeness_engine = CompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")
    results = []

    # Actual: A → E1, A → E2
    # Declared: A → E1
    # Mutate E2 (which is in actual but not declared)
    actual = ["E1", "E2"]
    declared = ["E1"]
    change = WorldChange(
        change_id="world_c_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E2 mutated (under-approximated graph)",
        changed_dependencies=["E2"],
    )
    graph = create_dependency_graph({"A": ["E1", "E2"]})
    propositions = {"prop_001": ["A"]}
    authorizations = {"auth_001": ["prop_001"]}

    actual_affected = compute_actual_affected_set(change, graph, propositions, authorizations)

    comp = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared, actual, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection = completeness_engine.check_intersection_status("E2", declared, comp)

    drift_event = AuthorityDriftEvent(
        event_id="world_c_event",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E2 mutated",
        affected_actor="A",
        affected_component="A",
        previous_state={"E2": "old"},
        new_state={"E2": "new"},
    )
    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", declared, "prop_001", "payment", scope,
    )

    computed = set(frontier.affected_dependencies)
    actual_set = actual_affected.to_set()

    # Experimental classification
    if computed == actual_set:
        experimental_classification = FrontierClassification.EXACT
    elif computed.issuperset(actual_set):
        experimental_classification = FrontierClassification.OVER_APPROXIMATED
    elif computed.issubset(actual_set):
        experimental_classification = FrontierClassification.UNDER_APPROXIMATED
    else:
        experimental_classification = FrontierClassification.UNDER_APPROXIMATED

    # Experimental soundness
    if actual_set.issubset(computed):
        experimental_soundness = FrontierSoundness.SOUND
    else:
        experimental_soundness = FrontierSoundness.UNSOUND

    # Protocol soundness: based on completeness + intersection
    if comp.overall_status == CompletenessStatus.KNOWN_COMPLETE:
        if intersection == IntersectionStatus.INTERSECTION_FOUND:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        elif intersection == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        else:
            protocol_classification = FrontierClassification.UNDER_APPROXIMATED
            protocol_soundness = FrontierSoundness.UNKNOWN
    elif comp.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNSOUND
    else:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNKNOWN

    results.append(FrontierSoundnessResult(
        test_name="unsafe_under_approximation",
        world_name="C",
        actual_dependencies=actual,
        declared_dependencies=declared,
        change=change,
        computed_frontier=computed,
        actual_affected=actual_affected,
        completeness_status=comp.overall_status,
        intersection_status=intersection,
        protocol_classification=protocol_classification,
        experimental_classification=experimental_classification,
        protocol_soundness=protocol_soundness,
        experimental_soundness=experimental_soundness,
        notes="Under-approximated graph: frontier misses affected artifacts (dangerous)",
    ))

    return results


def run_world_d_unknown() -> list[FrontierSoundnessResult]:
    """World D: Unknown.
    
    The protocol has insufficient completeness evidence to determine whether
    undeclared dependencies exist. The correct result must be UNKNOWN, not SOUND.
    """
    engine = TemporalCompletenessEngine()
    completeness_engine = CompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")
    results = []

    # Actual: A → E1, A → E2 (E2 is a hidden dependency)
    # Declared: A → E1
    # Mutate E99 (unknown relationship to A)
    actual = ["E1", "E2"]
    declared = ["E1"]
    change = WorldChange(
        change_id="world_d_mutation",
        timestamp="2026-02-01T00:00:00Z",
        description="E99 mutated (unknown relationship)",
        changed_dependencies=["E99"],
    )
    graph = create_dependency_graph({"A": ["E1", "E2"], "C": ["E99"]})
    propositions = {"prop_001": ["A"], "prop_002": ["C"]}
    authorizations = {"auth_001": ["prop_001"], "auth_002": ["prop_002"]}

    actual_affected = compute_actual_affected_set(change, graph, propositions, authorizations)

    comp = completeness_engine.assess_completeness(
        "auth_001", "graph_001", declared, actual, scope,
        CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    intersection = completeness_engine.check_intersection_status("E99", declared, comp)

    drift_event = AuthorityDriftEvent(
        event_id="world_d_event",
        timestamp="2026-02-01T00:00:00Z",
        event_type="dependency_mutated",
        description="E99 mutated",
        affected_actor="C",
        affected_component="C",
        previous_state={"E99": "old"},
        new_state={"E99": "new"},
    )
    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", declared, "prop_001", "payment", scope,
    )

    computed = set(frontier.affected_dependencies)
    actual_set = actual_affected.to_set()

    # Experimental classification
    if computed == actual_set:
        experimental_classification = FrontierClassification.EXACT
    elif computed.issuperset(actual_set):
        experimental_classification = FrontierClassification.OVER_APPROXIMATED
    elif computed.issubset(actual_set):
        experimental_classification = FrontierClassification.UNDER_APPROXIMATED
    else:
        experimental_classification = FrontierClassification.UNDER_APPROXIMATED

    # Experimental soundness
    if actual_set.issubset(computed):
        experimental_soundness = FrontierSoundness.SOUND
    else:
        experimental_soundness = FrontierSoundness.UNSOUND

    # Protocol soundness: based on completeness + intersection
    if comp.overall_status == CompletenessStatus.KNOWN_COMPLETE:
        if intersection == IntersectionStatus.INTERSECTION_FOUND:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        elif intersection == IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS:
            protocol_classification = FrontierClassification.EXACT
            protocol_soundness = FrontierSoundness.SOUND
        else:
            protocol_classification = FrontierClassification.UNDER_APPROXIMATED
            protocol_soundness = FrontierSoundness.UNKNOWN
    elif comp.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNSOUND
    else:
        protocol_classification = FrontierClassification.UNDER_APPROXIMATED
        protocol_soundness = FrontierSoundness.UNKNOWN

    results.append(FrontierSoundnessResult(
        test_name="unknown_frontier",
        world_name="D",
        actual_dependencies=actual,
        declared_dependencies=declared,
        change=change,
        computed_frontier=computed,
        actual_affected=actual_affected,
        completeness_status=comp.overall_status,
        intersection_status=intersection,
        protocol_classification=protocol_classification,
        experimental_classification=experimental_classification,
        protocol_soundness=protocol_soundness,
        experimental_soundness=experimental_soundness,
        notes="Unknown: protocol cannot establish frontier soundness due to incomplete graph",
    ))

    return results


def run_all_frontier_soundness_experiments() -> list[FrontierSoundnessResult]:
    """Run all frontier soundness experiments."""
    results = []
    results.extend(run_world_a_exact_graph())
    results.extend(run_world_b_safe_over_approximation())
    results.extend(run_world_c_unsafe_under_approximation())
    results.extend(run_world_d_unknown())
    return results


def print_frontier_soundness_results(results: list[FrontierSoundnessResult]) -> None:
    """Print frontier soundness results."""
    print("\n" + "=" * 120)
    print("FRONTIER SOUNDNESS EXPERIMENTS")
    print("=" * 120)
    print(f"{'World':<8} {'Test':<30} {'Complete':<15} {'Intersect':<25} {'Protocol':<15} {'Experimental':<15} {'Match?':<8} {'ExpSound':<10}")
    print("-" * 120)

    for r in results:
        match = "✅" if r.protocol_classification == r.experimental_classification else "❌"
        print(f"{r.world_name:<8} {r.test_name:<30} {r.completeness_status.value:<15} {r.intersection_status.value:<25} {r.protocol_classification.value:<15} {r.experimental_classification.value:<15} {match:<8} {r.experimental_soundness.value:<10}")

    print("\n" + "=" * 120)
    print("DETAILED RESULTS")
    print("=" * 120)

    for r in results:
        print(f"\nWorld {r.world_name}: {r.test_name}")
        print(f"  Actual deps: {r.actual_dependencies}")
        print(f"  Declared deps: {r.declared_dependencies}")
        print(f"  Change: {r.change.description}")
        print(f"  Computed frontier: {r.computed_frontier}")
        print(f"  Actual affected: {r.actual_affected.to_set()}")
        print(f"  Completeness: {r.completeness_status.value}")
        print(f"  Intersection: {r.intersection_status.value}")
        print(f"  Protocol classification: {r.protocol_classification.value}")
        print(f"  Experimental classification: {r.experimental_classification.value}")
        print(f"  Protocol soundness: {r.protocol_soundness.value}")
        print(f"  Experimental soundness: {r.experimental_soundness.value}")
        if r.notes:
            print(f"  Notes: {r.notes}")


def analyze_soundness_results(results: list[FrontierSoundnessResult]) -> dict[str, Any]:
    """Analyze whether protocol classifications match experimental ground truth."""
    analysis = {
        "total": len(results),
        "exact_match": 0,
        "over_approximation": 0,
        "under_approximation": 0,
        "unknown": 0,
        "protocol_correct": 0,
        "protocol_incorrect": 0,
        "false_sound": 0,
        "false_unknown": 0,
        "notes": [],
    }

    for r in results:
        # Count experimental classifications
        if r.experimental_classification == FrontierClassification.EXACT:
            analysis["exact_match"] += 1
        elif r.experimental_classification == FrontierClassification.OVER_APPROXIMATED:
            analysis["over_approximation"] += 1
        elif r.experimental_classification == FrontierClassification.UNDER_APPROXIMATED:
            analysis["under_approximation"] += 1

        # Check if protocol classification matches experimental
        if r.protocol_classification == r.experimental_classification:
            analysis["protocol_correct"] += 1
        else:
            analysis["protocol_incorrect"] += 1
            analysis["notes"].append(
                f"World {r.world_name}: protocol={r.protocol_classification.value}, "
                f"experimental={r.experimental_classification.value}"
            )

        # Check for false SOUND (protocol says SOUND but experimental says UNSOUND)
        if r.protocol_soundness == FrontierSoundness.SOUND and r.experimental_soundness == FrontierSoundness.UNSOUND:
            analysis["false_sound"] += 1
            analysis["notes"].append(f"World {r.world_name}: FALSE SOUND")

        # Check for false UNKNOWN
        if r.protocol_soundness == FrontierSoundness.UNKNOWN and r.experimental_soundness != FrontierSoundness.UNKNOWN:
            analysis["false_unknown"] += 1

    return analysis


if __name__ == "__main__":
    results = run_all_frontier_soundness_experiments()
    print_frontier_soundness_results(results)
    analysis = analyze_soundness_results(results)
    print("\n" + "=" * 120)
    print("SOUNDNESS ANALYSIS")
    print("=" * 120)
    for k, v in analysis.items():
        print(f"  {k}: {v}")
