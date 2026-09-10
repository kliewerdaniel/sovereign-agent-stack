"""Incremental Epistemic Revalidation — Research Model.

Formalizes the experimental model for testing whether the revalidation frontier
is sound and minimal under composition, temporal change, multi-agent dependencies,
and adversarial dependency discovery.

This module defines the experimental ground truth model. It does NOT define
new protocol abstractions — it defines how to evaluate existing ones.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class FrontierClassification(str, Enum):
    """Classification of a computed frontier against ground truth."""
    EXACT = "exact"                           # Computed = Actual
    OVER_APPROXIMATED = "over_approximated"   # Computed ⊃ Actual (safe but conservative)
    UNDER_APPROXIMATED = "under_approximated" # Computed ⊂ Actual (unsafe)
    UNKNOWN = "unknown"                       # Cannot determine


class FrontierSoundness(str, Enum):
    """Soundness of a frontier relative to ground truth."""
    SOUND = "sound"                           # Frontier catches all affected artifacts
    UNSOUND = "unsound"                       # Frontier misses affected artifacts
    UNKNOWN = "unknown"                       # Cannot determine soundness


@dataclass(frozen=True)
class WorldChange:
    """A controlled world change for experimentation.
    
    This is the experimental input — what actually changed in the world.
    """
    change_id: str
    timestamp: str
    description: str
    added_dependencies: list[str] = field(default_factory=list)
    removed_dependencies: list[str] = field(default_factory=list)
    changed_propositions: list[str] = field(default_factory=list)
    changed_authorizations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActualAffectedSet:
    """The ground truth affected set — what actually changed.
    
    This is computed independently from the protocol's frontier computation.
    It represents what SHOULD be revalidated based on the actual world state.
    """
    affected_set_id: str
    change_id: str
    affected_dependencies: list[str] = field(default_factory=list)
    affected_propositions: list[str] = field(default_factory=list)
    affected_completeness_claims: list[str] = field(default_factory=list)
    affected_authorizations: list[str] = field(default_factory=list)
    affected_epistemic_states: list[str] = field(default_factory=list)
    scope: dict[str, Any] = field(default_factory=dict)

    def to_set(self) -> set[str]:
        """Convert to a flat set of artifact IDs."""
        return set(
            self.affected_dependencies
            + self.affected_propositions
            + self.affected_completeness_claims
            + self.affected_authorizations
            + self.affected_epistemic_states
        )


@dataclass(frozen=True)
class FrontierEvaluation:
    """Evaluation of a computed frontier against ground truth.
    
    This is the experimental result — how well did the protocol do?
    """
    evaluation_id: str
    change_id: str
    computed_frontier: set[str]
    actual_affected_set: set[str]
    classification: FrontierClassification
    soundness: FrontierSoundness
    missing_artifacts: list[str] = field(default_factory=list)   # In actual, not in computed
    extra_artifacts: list[str] = field(default_factory=list)     # In computed, not in actual
    unknown_artifacts: list[str] = field(default_factory=list)   # Cannot determine
    timestamp: str = ""
    provenance: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def is_exact(self) -> bool:
        return self.classification == FrontierClassification.EXACT

    @property
    def is_sound(self) -> bool:
        return self.soundness == FrontierSoundness.SOUND

    @property
    def is_over_approximated(self) -> bool:
        return self.classification == FrontierClassification.OVER_APPROXIMATED

    @property
    def is_under_approximated(self) -> bool:
        return self.classification == FrontierClassification.UNDER_APPROXIMATED


@dataclass
class RevalidationExperiment:
    """Experimental environment for frontier soundness testing.
    
    This is the core experimental harness. It:
    1. Creates controlled worlds with known ground truth
    2. Applies world changes
    3. Computes frontiers using the existing protocol
    4. Compares computed frontiers to actual affected sets
    5. Classifies results
    """

    evaluations: list[FrontierEvaluation] = field(default_factory=list)

    def evaluate_frontier(
        self,
        change: WorldChange,
        computed_frontier: set[str],
        actual_affected: ActualAffectedSet,
    ) -> FrontierEvaluation:
        """Evaluate a computed frontier against ground truth."""
        actual_set = actual_affected.to_set()

        # Determine classification
        if computed_frontier == actual_set:
            classification = FrontierClassification.EXACT
        elif computed_frontier.issuperset(actual_set):
            classification = FrontierClassification.OVER_APPROXIMATED
        elif computed_frontier.issubset(actual_set):
            classification = FrontierClassification.UNDER_APPROXIMATED
        else:
            # Partial overlap — could be either
            if computed_frontier - actual_set:
                classification = FrontierClassification.OVER_APPROXIMATED
            else:
                classification = FrontierClassification.UNDER_APPROXIMATED

        # Determine soundness
        missing = actual_set - computed_frontier
        if not missing:
            soundness = FrontierSoundness.SOUND
        else:
            soundness = FrontierSoundness.UNSOUND

        evaluation = FrontierEvaluation(
            evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
            change_id=change.change_id,
            computed_frontier=computed_frontier,
            actual_affected_set=actual_set,
            classification=classification,
            soundness=soundness,
            missing_artifacts=sorted(missing),
            extra_artifacts=sorted(computed_frontier - actual_set),
            timestamp=datetime.utcnow().isoformat(),
            provenance=["revalidation_experiment"],
        )

        self.evaluations.append(evaluation)
        return evaluation

    def get_exact_count(self) -> int:
        return sum(1 for e in self.evaluations if e.is_exact)

    def get_sound_count(self) -> int:
        return sum(1 for e in self.evaluations if e.is_sound)

    def get_over_approximated_count(self) -> int:
        return sum(1 for e in self.evaluations if e.is_over_approximated)

    def get_under_approximated_count(self) -> int:
        return sum(1 for e in self.evaluations if e.is_under_approximated)

    def summary(self) -> dict[str, Any]:
        total = len(self.evaluations)
        if total == 0:
            return {"total": 0}

        return {
            "total": total,
            "exact": self.get_exact_count(),
            "sound": self.get_sound_count(),
            "over_approximated": self.get_over_approximated_count(),
            "under_approximated": self.get_under_approximated_count(),
            "accuracy": self.get_exact_count() / total,
            "soundness_rate": self.get_sound_count() / total,
        }


def create_dependency_graph(
    dependencies: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Create a dependency graph from a mapping.
    
    Format: {entity: [dependency_ids]}
    
    Example:
        create_dependency_graph({
            "A": ["E1", "E2", "E3"],
            "B": ["E4", "E5"],
            "C": ["E6"],
        })
    """
    return dependencies


def compute_actual_affected_set(
    change: WorldChange,
    dependency_graph: dict[str, list[str]],
    propositions: dict[str, list[str]],
    authorizations: dict[str, list[str]],
) -> ActualAffectedSet:
    """Compute the actual affected set from a world change.
    
    This is the ground truth — what actually changed.
    It is computed independently from the protocol's frontier computation.
    
    The algorithm:
    1. Find all dependencies that were added or removed
    2. Find all entities that depend on those dependencies
    3. Find all propositions that depend on affected entities
    4. Find all authorizations that depend on affected propositions
    """
    affected_deps = set(change.added_dependencies + change.removed_dependencies)
    affected_entities = set()
    affected_propositions = set()
    affected_authorizations = set()
    affected_completeness_claims = set()
    affected_epistemic_states = set()

    # Find entities that depend on affected dependencies
    for entity, deps in dependency_graph.items():
        if any(dep in affected_deps for dep in deps):
            affected_entities.add(entity)
            affected_completeness_claims.add(f"claim_{entity}")

    # Find propositions that depend on affected entities
    for prop, entities in propositions.items():
        if any(entity in affected_entities for entity in entities):
            affected_propositions.add(prop)
            affected_epistemic_states.add(f"es_{prop}")

    # Find authorizations that depend on affected propositions
    for auth, props in authorizations.items():
        if any(prop in affected_propositions for prop in props):
            affected_authorizations.add(auth)

    return ActualAffectedSet(
        affected_set_id=f"actual_{change.change_id}",
        change_id=change.change_id,
        affected_dependencies=sorted(affected_deps),
        affected_propositions=sorted(affected_propositions),
        affected_completeness_claims=sorted(affected_completeness_claims),
        affected_authorizations=sorted(affected_authorizations),
        affected_epistemic_states=sorted(affected_epistemic_states),
    )
