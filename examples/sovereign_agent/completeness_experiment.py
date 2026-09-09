"""Dependency Completeness Experimental Environment.

Creates worlds where the actual dependency set is known independently
from the declared dependency set, for evaluating completeness reasoning.

World truth is used ONLY as experimental ground truth — never exposed
to the protocol as authoritative evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.sovereign_agent.dependency_completeness import (
    CompletenessAssessment,
    CompletenessDimension,
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    DimensionCoverage,
    IntersectionStatus,
    create_completeness_scope,
)


class WorldDependencyState(str, Enum):
    """Epistemic state of a dependency in the world."""
    DECLARED = "declared"
    INFERRED = "inferred"
    OBSERVED = "observed"
    VALIDATED = "validated"
    UNKNOWN = "unknown"
    REJECTED = "rejected"


@dataclass(frozen=True)
class WorldDependency:
    """A dependency in the experimental world."""
    dependency_id: str
    state: WorldDependencyState
    dimension: CompletenessDimension
    is_necessary: bool = True
    failure_condition: Optional[str] = None


@dataclass(frozen=True)
class WorldState:
    """The ground truth state of a world."""
    world_id: str
    timestamp: str
    actual_dependencies: list[WorldDependency] = field(default_factory=list)
    environment: str = "production"
    temporal_interval: str = "unbounded"
    domain: str = "sovereign"
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_by_dimension(self, dimension: CompletenessDimension) -> list[WorldDependency]:
        """Get dependencies by dimension."""
        return [d for d in self.actual_dependencies if d.dimension == dimension]

    def get_necessary(self) -> list[WorldDependency]:
        """Get necessary dependencies."""
        return [d for d in self.actual_dependencies if d.is_necessary]

    def get_ids(self) -> list[str]:
        """Get all dependency IDs."""
        return [d.dependency_id for d in self.actual_dependencies]


@dataclass(frozen=True)
class ExperimentalCondition:
    """A single experimental condition."""
    condition_id: str
    world: WorldState
    declared_ids: list[str]
    scope: CompletenessScope
    method: CompletenessMethod
    description: str = ""
    expected_status: Optional[CompletenessStatus] = None
    expected_gaps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExperimentalResult:
    """Result of a single experimental run."""
    condition: ExperimentalCondition
    assessment: CompletenessAssessment
    actual_gaps: list[str] = field(default_factory=list)
    false_completeness: bool = False
    false_incompleteness: bool = False
    unknown_completeness: bool = False
    scope_mismatch: bool = False
    temporal_mismatch: bool = False
    environment_mismatch: bool = False
    domain_mismatch: bool = False
    epistemic_insufficiency: bool = False
    authority_bootstrap: bool = False
    valid_rejection: bool = False
    notes: str = ""


@dataclass
class CompletenessExperiment:
    """Experimental environment for dependency completeness."""

    engine: CompletenessEngine = field(default_factory=CompletenessEngine)
    conditions: list[ExperimentalCondition] = field(default_factory=list)
    results: list[ExperimentalResult] = field(default_factory=list)

    def add_condition(self, condition: ExperimentalCondition) -> None:
        """Add an experimental condition."""
        self.conditions.append(condition)

    def run_all(self) -> list[ExperimentalResult]:
        """Run all experimental conditions."""
        self.results = []
        for condition in self.conditions:
            result = self._run_condition(condition)
            self.results.append(result)
        return self.results

    def _run_condition(self, condition: ExperimentalCondition) -> ExperimentalResult:
        """Run a single experimental condition."""
        assessment = self.engine.assess_completeness(
            authorization_id=f"auth_{condition.condition_id}",
            graph_id=f"graph_{condition.condition_id}",
            declared_dependencies=condition.declared_ids,
            actual_dependencies=condition.world.get_ids(),
            scope=condition.scope,
            method=condition.method,
        )

        # Compute actual gaps
        declared_set = set(condition.declared_ids)
        actual_ids = condition.world.get_ids()
        actual_gaps = [d for d in actual_ids if d not in declared_set]

        # Detect false completeness
        false_completeness = (
            assessment.overall_status == CompletenessStatus.KNOWN_COMPLETE
            and len(actual_gaps) > 0
        )

        # Detect false incompleteness
        false_incompleteness = (
            assessment.overall_status == CompletenessStatus.KNOWN_INCOMPLETE
            and len(actual_gaps) == 0
        )

        # Detect unknown completeness
        unknown_completeness = (
            assessment.overall_status == CompletenessStatus.UNKNOWN
            and len(actual_gaps) > 0
        )

        return ExperimentalResult(
            condition=condition,
            assessment=assessment,
            actual_gaps=actual_gaps,
            false_completeness=false_completeness,
            false_incompleteness=false_incompleteness,
            unknown_completeness=unknown_completeness,
            notes=self._generate_notes(condition, assessment, actual_gaps),
        )

    def _generate_notes(
        self,
        condition: ExperimentalCondition,
        assessment: CompletenessAssessment,
        actual_gaps: list[str],
    ) -> str:
        """Generate notes about the experimental result."""
        notes = []
        if assessment.overall_status == CompletenessStatus.KNOWN_COMPLETE and actual_gaps:
            notes.append(f"FALSE COMPLETENESS: {len(actual_gaps)} gaps not detected")
        if assessment.overall_status == CompletenessStatus.KNOWN_INCOMPLETE and not actual_gaps:
            notes.append("FALSE INCOMPLETION: graph is actually complete")
        if assessment.overall_status == CompletenessStatus.UNKNOWN and not actual_gaps:
            notes.append("UNKNOWN: graph is actually complete but not recognized")
        return "; ".join(notes) if notes else "Assessment matches ground truth."

    def get_false_completeness_results(self) -> list[ExperimentalResult]:
        """Get results where false completeness was detected."""
        return [r for r in self.results if r.false_completeness]

    def get_false_incompleteness_results(self) -> list[ExperimentalResult]:
        """Get results where false incompleteness was detected."""
        return [r for r in self.results if r.false_incompleteness]

    def get_unknown_results(self) -> list[ExperimentalResult]:
        """Get results with unknown completeness."""
        return [r for r in self.results if r.unknown_completeness]

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        total = len(self.results)
        if total == 0:
            return {"total": 0}

        false_comp = len(self.get_false_completeness_results())
        false_incomp = len(self.get_false_incompleteness_results())
        unknown = len(self.get_unknown_results())
        correct = total - false_comp - false_incomp

        return {
            "total": total,
            "correct": correct,
            "false_completeness": false_comp,
            "false_incompleteness": false_incomp,
            "unknown": unknown,
            "accuracy": correct / total if total > 0 else 0.0,
        }


def build_world_with_dependencies(
    world_id: str,
    declared_ids: list[str],
    actual_ids: list[str],
    unknown_ids: list[str],
    environment: str = "production",
    domain: str = "sovereign",
) -> WorldState:
    """Build a world state with known dependencies."""
    dependencies = []

    for dep_id in actual_ids:
        if dep_id in declared_ids:
            state = WorldDependencyState.DECLARED
        elif dep_id in unknown_ids:
            state = WorldDependencyState.UNKNOWN
        else:
            state = WorldDependencyState.OBSERVED

        # Determine dimension from prefix
        dimension = _infer_dimension(dep_id)

        dependencies.append(WorldDependency(
            dependency_id=dep_id,
            state=state,
            dimension=dimension,
            is_necessary=True,
        ))

    return WorldState(
        world_id=world_id,
        timestamp=datetime.utcnow().isoformat(),
        actual_dependencies=dependencies,
        environment=environment,
        domain=domain,
    )


def _infer_dimension(dep_id: str) -> CompletenessDimension:
    """Infer the dimension of a dependency from its ID prefix."""
    if dep_id.startswith("ev_"):
        return CompletenessDimension.EVIDENCE
    if dep_id.startswith("mech_"):
        return CompletenessDimension.MECHANISM
    if dep_id.startswith("res_"):
        return CompletenessDimension.RESOURCE
    if dep_id.startswith("cons_"):
        return CompletenessDimension.CONSEQUENCE
    if dep_id.startswith("actor_"):
        return CompletenessDimension.ACTOR
    if dep_id.startswith("env_"):
        return CompletenessDimension.ENVIRONMENT
    if dep_id.startswith("temp_"):
        return CompletenessDimension.TEMPORAL
    if dep_id.startswith("gov_"):
        return CompletenessDimension.GOVERNANCE
    if dep_id.startswith("exec_"):
        return CompletenessDimension.EXECUTION_PATH
    return CompletenessDimension.EVIDENCE


def build_completeness_experiment() -> CompletenessExperiment:
    """Build a comprehensive completeness experiment."""
    experiment = CompletenessExperiment()

    # Condition 1: Complete graph (all dependencies declared)
    world1 = build_world_with_dependencies(
        world_id="world_complete",
        declared_ids=["ev_001", "ev_002", "mech_001", "res_001"],
        actual_ids=["ev_001", "ev_002", "mech_001", "res_001"],
        unknown_ids=[],
    )
    scope1 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="complete_graph",
        world=world1,
        declared_ids=["ev_001", "ev_002", "mech_001", "res_001"],
        scope=scope1,
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        description="Complete graph - all dependencies declared",
        expected_status=CompletenessStatus.KNOWN_COMPLETE,
        expected_gaps=[],
    ))

    # Condition 2: Missing direct dependency
    world2 = build_world_with_dependencies(
        world_id="world_missing_direct",
        declared_ids=["ev_001"],
        actual_ids=["ev_001", "ev_002"],
        unknown_ids=["ev_002"],
    )
    scope2 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="missing_direct",
        world=world2,
        declared_ids=["ev_001"],
        scope=scope2,
        method=CompletenessMethod.STATIC_ANALYSIS_DERIVED,
        description="Missing direct dependency - ev_002 not declared",
        expected_status=CompletenessStatus.KNOWN_INCOMPLETE,
        expected_gaps=["ev_002"],
    ))

    # Condition 3: Missing transitive dependency
    world3 = build_world_with_dependencies(
        world_id="world_missing_transitive",
        declared_ids=["ev_001", "mech_001"],
        actual_ids=["ev_001", "mech_001", "ev_003"],
        unknown_ids=["ev_003"],
    )
    scope3 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="missing_transitive",
        world=world3,
        declared_ids=["ev_001", "mech_001"],
        scope=scope3,
        method=CompletenessMethod.RUNTIME_TRACE_DERIVED,
        description="Missing transitive dependency - ev_003 not declared",
        expected_status=CompletenessStatus.KNOWN_INCOMPLETE,
        expected_gaps=["ev_003"],
    ))

    # Condition 4: Over-broad dependency (extra dependencies)
    world4 = build_world_with_dependencies(
        world_id="world_over_broad",
        declared_ids=["ev_001", "ev_002", "ev_003", "ev_004", "ev_005"],
        actual_ids=["ev_001"],
        unknown_ids=[],
    )
    scope4 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="over_broad",
        world=world4,
        declared_ids=["ev_001", "ev_002", "ev_003", "ev_004", "ev_005"],
        scope=scope4,
        method=CompletenessMethod.DOCUMENTATION_DERIVED,
        description="Over-broad dependency - extra dependencies declared",
        expected_status=CompletenessStatus.OVER_APPROXIMATED,
        expected_gaps=[],
    ))

    # Condition 5: False completeness (appears complete but isn't)
    world5 = build_world_with_dependencies(
        world_id="world_false_complete",
        declared_ids=["ev_001", "ev_002"],
        actual_ids=["ev_001", "ev_002", "mech_002"],
        unknown_ids=["mech_002"],
    )
    scope5 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="false_completeness",
        world=world5,
        declared_ids=["ev_001", "ev_002"],
        scope=scope5,
        method=CompletenessMethod.MODEL_HYPOTHESIZED,
        description="False completeness - model claims complete but mech_002 missing",
        expected_status=CompletenessStatus.UNTESTED_COMPLETENESS,
        expected_gaps=["mech_002"],
    ))

    # Condition 6: Unknown completeness
    world6 = build_world_with_dependencies(
        world_id="world_unknown",
        declared_ids=["ev_001"],
        actual_ids=["ev_001", "ev_002", "mech_001", "res_001"],
        unknown_ids=["ev_002", "mech_001", "res_001"],
    )
    scope6 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="unknown_completeness",
        world=world6,
        declared_ids=["ev_001"],
        scope=scope6,
        method=CompletenessMethod.STATIC_ANALYSIS_DERIVED,
        description="Unknown completeness - many dependencies undiscovered",
        expected_status=CompletenessStatus.UNKNOWN,
        expected_gaps=["ev_002", "mech_001", "res_001"],
    ))

    # Condition 7: Conditional complete (complete under normal conditions)
    world7 = build_world_with_dependencies(
        world_id="world_conditional",
        declared_ids=["ev_001", "ev_002", "mech_001"],
        actual_ids=["ev_001", "ev_002", "mech_001", "ev_fail"],
        unknown_ids=["ev_fail"],
    )
    scope7 = create_completeness_scope("prop_001", "payment")
    experiment.add_condition(ExperimentalCondition(
        condition_id="conditional_complete",
        world=world7,
        declared_ids=["ev_001", "ev_002", "mech_001"],
        scope=scope7,
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        description="Conditional complete - complete under normal conditions",
        expected_status=CompletenessStatus.CONDITIONAL_COMPLETENESS,
        expected_gaps=["ev_fail"],
    ))

    # Condition 8: Environment-specific completeness
    world8 = build_world_with_dependencies(
        world_id="world_env_specific",
        declared_ids=["ev_001", "ev_002"],
        actual_ids=["ev_001", "ev_002"],
        unknown_ids=[],
        environment="staging",
    )
    scope8 = create_completeness_scope("prop_001", "payment", environment="production")
    experiment.add_condition(ExperimentalCondition(
        condition_id="env_specific",
        world=world8,
        declared_ids=["ev_001", "ev_002"],
        scope=scope8,
        method=CompletenessMethod.RUNTIME_TRACE_DERIVED,
        description="Environment-specific - staging graph used for production",
        expected_status=CompletenessStatus.KNOWN_COMPLETE,
        expected_gaps=[],
    ))

    # Condition 9: Temporal completeness
    world9 = build_world_with_dependencies(
        world_id="world_temporal",
        declared_ids=["ev_001", "ev_002"],
        actual_ids=["ev_001", "ev_002"],
        unknown_ids=[],
        environment="production",
    )
    scope9 = create_completeness_scope(
        "prop_001", "payment", environment="production", temporal_interval="2026-01-01/2027-01-01"
    )
    experiment.add_condition(ExperimentalCondition(
        condition_id="temporal_complete",
        world=world9,
        declared_ids=["ev_001", "ev_002"],
        scope=scope9,
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
        description="Temporal completeness - complete within temporal bounds",
        expected_status=CompletenessStatus.KNOWN_COMPLETE,
        expected_gaps=[],
    ))

    # Condition 10: Cross-domain completeness
    world10 = build_world_with_dependencies(
        world_id="world_cross_domain",
        declared_ids=["ev_001", "ev_002"],
        actual_ids=["ev_001", "ev_002"],
        unknown_ids=[],
        domain="payments",
    )
    scope10 = create_completeness_scope(
        "prop_001", "payment", domain="identity"
    )
    experiment.add_condition(ExperimentalCondition(
        condition_id="cross_domain",
        world=world10,
        declared_ids=["ev_001", "ev_002"],
        scope=scope10,
        method=CompletenessMethod.GOVERNANCE_DECLARED,
        description="Cross-domain - payments graph used for identity domain",
        expected_status=CompletenessStatus.KNOWN_COMPLETE,
        expected_gaps=[],
    ))

    return experiment
