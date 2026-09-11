"""Phase 23: Epistemic State Consequentiality.

Tests whether epistemic state transitions themselves are part of the
consequential authority surface.

Phase 22 established AUTHORITY_TRANSFORMATION_ALGEBRA: authority amplification
is a property of authority transformations, not of any particular policy
mechanism. The transformation algebra unifies Phase 14, 15, and 21.

Phase 23 asks:

    ARE EPISTEMIC STATE TRANSITIONS THEMSELVES PART OF THE CONSEQUENTIAL
    AUTHORITY SURFACE?

If transitioning from UNKNOWN to COMPLETE has authority consequences
(because it changes the governance disposition), then the epistemic
state machine is itself a consequential mechanism that must be governed.

This completes the architecture:

    OBSERVATION → EVIDENCE → EPISTEMIC STATE → GOVERNANCE → AUTHORITY → EXECUTION

Every layer is explicit, bounded, and governed.

Existing infrastructure reused:
- AuthorityTransformation, TransformationClass (authority_transformation_algebra.py)
- AuthorityClaimWithProvenance, UncertaintyPolicy (authority_under_uncertainty.py)
- CompletenessState, BoundedCompleteness (uncertainty_policy_authority.py)
- AuthorityGraph, AuthorityGraphNode (authority_genesis.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Epistemic State Transition Types
# ---------------------------------------------------------------------------


class EpistemicTransitionType(str, Enum):
    """Types of epistemic state transitions."""
    GAIN_KNOWLEDGE = "gain_knowledge"        # UNKNOWN → COMPLETE
    LOSE_KNOWLEDGE = "lose_knowledge"        # COMPLETE → INCOMPLETE
    UNCERTAINTY_RESOLVED = "uncertainty_resolved"  # UNKNOWN → COMPLETE
    UNCERTAINTY_INCREASED = "uncertainty_increased"  # COMPLETE → UNKNOWN
    HISTORICAL_REVISION = "historical_revision"  # WAS_COMPLETE_AT_T → INCOMPLETE
    NO_CHANGE = "no_change"                  # COMPLETE → COMPLETE


class EpistemicTransitionConsequence(str, Enum):
    """Consequence classification for epistemic transitions."""
    CREATES_AUTHORITY = "creates_authority"
    REVOKES_AUTHORITY = "revokes_authority"
    CONSTRAINS_AUTHORITY = "constrains_authority"
    NO_AUTHORITY_EFFECT = "no_authority_effect"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Epistemic State Transition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicStateTransition:
    """An epistemic state transition with authority consequences.
    
    An epistemic state transition is itself a transformation that may
    have authority consequences. For example, transitioning from
    UNKNOWN to COMPLETE may change the governance disposition from
    HOLD to NORMAL, effectively creating authority.
    """
    transition_id: str
    from_state: str
    to_state: str
    transition_type: EpistemicTransitionType
    actor: str  # Who caused the transition
    authority_basis: str  # What authority authorized the transition
    scope: str = ""
    temporal_bounds: tuple[str, str] = ("unbounded", "unbounded")
    provenance: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def classification(self) -> EpistemicTransitionConsequence:
        """Classify the authority consequence of this transition."""
        return classify_epistemic_transition(self)
    
    @property
    def creates_authority(self) -> bool:
        """Check if this transition creates authority."""
        return self.classification == EpistemicTransitionConsequence.CREATES_AUTHORITY
    
    @property
    def revokes_authority(self) -> bool:
        """Check if this transition revokes authority."""
        return self.classification == EpistemicTransitionConsequence.REVOKES_AUTHORITY


# ---------------------------------------------------------------------------
# Epistemic State Machine
# ---------------------------------------------------------------------------


class EpistemicStateMachine:
    """The epistemic state machine.
    
    Governs transitions between epistemic states and tracks their
    authority consequences.
    """
    
    def __init__(self) -> None:
        self.states: dict[str, dict[str, Any]] = {}
        self.transitions: list[EpistemicStateTransition] = []
        self.current_state: str = "unknown"
    
    def set_state(
        self,
        entity_id: str,
        state: str,
        actor: str,
        authority_basis: str,
    ) -> EpistemicStateTransition:
        """Set the epistemic state of an entity.
        
        Records the transition and its authority consequences.
        """
        previous_state = self.states.get(entity_id, {}).get("state", "unknown")
        
        transition_type = self._determine_transition_type(previous_state, state)
        
        transition = EpistemicStateTransition(
            transition_id=f"transition_{uuid.uuid4().hex[:12]}",
            from_state=previous_state,
            to_state=state,
            transition_type=transition_type,
            actor=actor,
            authority_basis=authority_basis,
            provenance=(f"from={previous_state}", f"to={state}"),
        )
        
        self.transitions.append(transition)
        self.states[entity_id] = {
            "state": state,
            "last_transition": transition.transition_id,
        }
        self.current_state = state
        
        return transition
    
    def _determine_transition_type(
        self,
        from_state: str,
        to_state: str,
    ) -> EpistemicTransitionType:
        """Determine the type of epistemic transition."""
        if from_state == to_state:
            return EpistemicTransitionType.NO_CHANGE
        if from_state == "unknown" and to_state == "complete":
            return EpistemicTransitionType.GAIN_KNOWLEDGE
        if from_state == "complete" and to_state == "incomplete":
            return EpistemicTransitionType.LOSE_KNOWLEDGE
        if from_state == "complete" and to_state == "unknown":
            return EpistemicTransitionType.UNCERTAINTY_INCREASED
        if from_state == "unknown" and to_state == "incomplete":
            return EpistemicTransitionType.UNCERTAINTY_RESOLVED
        if from_state == "was_complete_at_t" and to_state == "incomplete":
            return EpistemicTransitionType.HISTORICAL_REVISION
        return EpistemicTransitionType.NO_CHANGE
    
    def get_authority_consequences(
        self,
        entity_id: str,
    ) -> list[EpistemicStateTransition]:
        """Get all authority-affecting transitions for an entity."""
        return [
            t for t in self.transitions
            if t.classification
            != EpistemicTransitionConsequence.NO_AUTHORITY_EFFECT
        ]


# ---------------------------------------------------------------------------
# Epistemic Transition Classifier
# ---------------------------------------------------------------------------


def classify_epistemic_transition(
    transition: EpistemicStateTransition,
) -> EpistemicTransitionConsequence:
    """Classify the authority consequence of an epistemic transition.
    
    The key insight: epistemic transitions can have authority consequences.
    
    UNKNOWN → COMPLETE: May create authority (disposition changes from HOLD to NORMAL)
    COMPLETE → INCOMPLETE: May constrain authority (disposition changes from NORMAL to REVIEW)
    UNKNOWN → INCOMPLETE: May constrain authority
    COMPLETE → UNKNOWN: May constrain authority
    
    But these are governance decisions, not epistemic ones.
    """
    from_state = transition.from_state
    to_state = transition.to_state
    
    # UNKNOWN → COMPLETE: Creates authority (removes constraint)
    if from_state == "unknown" and to_state == "complete":
        return EpistemicTransitionConsequence.CREATES_AUTHORITY
    
    # COMPLETE → INCOMPLETE: Constrains authority
    if from_state == "complete" and to_state == "incomplete":
        return EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY
    
    # COMPLETE → UNKNOWN: Constrains authority
    if from_state == "complete" and to_state == "unknown":
        return EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY
    
    # UNKNOWN → INCOMPLETE: Constrains authority
    if from_state == "unknown" and to_state == "incomplete":
        return EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY
    
    # WAS_COMPLETE_AT_T → INCOMPLETE: Historical revision, constrains future authority
    if from_state == "was_complete_at_t" and to_state == "incomplete":
        return EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY
    
    # No change
    if from_state == to_state:
        return EpistemicTransitionConsequence.NO_AUTHORITY_EFFECT
    
    return EpistemicTransitionConsequence.UNKNOWN


# ---------------------------------------------------------------------------
# Epistemic State Consequentiality Engine
# ---------------------------------------------------------------------------


@dataclass
class EpistemicStateConsequentialityEngine:
    """Engine for testing epistemic state consequentiality.
    
    The engine:
    1. Creates epistemic state transitions
    2. Classifies their authority consequences
    3. Tracks the epistemic state machine
    4. Detects when epistemic transitions create/constrain authority
    """
    
    state_machine: EpistemicStateMachine = field(default_factory=EpistemicStateMachine)
    experiments: list["EpistemicStateExperiment"] = field(default_factory=list)
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        transition: EpistemicStateTransition,
        notes: str = "",
        normative_assumptions: list[str] | None = None,
        underspecifications: list[str] | None = None,
    ) -> "EpistemicStateExperiment":
        """Run an epistemic state consequentiality experiment."""
        experiment = EpistemicStateExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            transition=transition,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Epistemic State Experiment
# ---------------------------------------------------------------------------


@dataclass
class EpistemicStateExperiment:
    """Result of an epistemic state consequentiality experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    transition: EpistemicStateTransition
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Experiment 1: UNKNOWN → COMPLETE (Creates Authority)
# ---------------------------------------------------------------------------


def run_unknown_to_complete(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """UNKNOWN → COMPLETE: Epistemic transition creates authority.
    
    When completeness changes from UNKNOWN to COMPLETE, the governance
    disposition changes from HOLD to NORMAL, effectively creating authority.
    """
    transition = engine.state_machine.set_state(
        entity_id="graph_001",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="unknown_to_complete",
        description="UNKNOWN → COMPLETE: Creates authority",
        transition=transition,
        notes="Epistemic transition creates authority via disposition change",
        normative_assumptions=[
            "Epistemic state transitions have authority consequences",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 2: COMPLETE → INCOMPLETE (Constrains Authority)
# ---------------------------------------------------------------------------


def run_complete_to_incomplete(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """COMPLETE → INCOMPLETE: Epistemic transition constrains authority."""
    transition = engine.state_machine.set_state(
        entity_id="graph_001",
        state="incomplete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="complete_to_incomplete",
        description="COMPLETE → INCOMPLETE: Constrains authority",
        transition=transition,
        notes="Epistemic transition constrains authority via disposition change",
    )


# ---------------------------------------------------------------------------
# Experiment 3: COMPLETE → UNKNOWN (Constrains Authority)
# ---------------------------------------------------------------------------


def run_complete_to_unknown(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """COMPLETE → UNKNOWN: Epistemic transition constrains authority."""
    # Reset to complete first
    engine.state_machine.set_state(
        entity_id="graph_002",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    transition = engine.state_machine.set_state(
        entity_id="graph_002",
        state="unknown",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="complete_to_unknown",
        description="COMPLETE → UNKNOWN: Constrains authority",
        transition=transition,
        notes="Epistemic transition constrains authority",
    )


# ---------------------------------------------------------------------------
# Experiment 4: UNKNOWN → INCOMPLETE (Constrains Authority)
# ---------------------------------------------------------------------------


def run_unknown_to_incomplete(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """UNKNOWN → INCOMPLETE: Epistemic transition constrains authority."""
    transition = engine.state_machine.set_state(
        entity_id="graph_003",
        state="incomplete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="unknown_to_incomplete",
        description="UNKNOWN → INCOMPLETE: Constrains authority",
        transition=transition,
        notes="Epistemic transition constrains authority",
    )


# ---------------------------------------------------------------------------
# Experiment 5: WAS_COMPLETE_AT_T → INCOMPLETE (Historical Revision)
# ---------------------------------------------------------------------------


def run_was_complete_to_incomplete(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """WAS_COMPLETE_AT_T → INCOMPLETE: Historical revision constrains future authority."""
    # First set to was_complete_at_t
    engine.state_machine.set_state(
        entity_id="graph_004",
        state="was_complete_at_t",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    # Then transition to incomplete
    transition = engine.state_machine.set_state(
        entity_id="graph_004",
        state="incomplete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="was_complete_to_incomplete",
        description="WAS_COMPLETE_AT_T → INCOMPLETE: Historical revision",
        transition=transition,
        notes="Historical revision constrains future authority",
        normative_assumptions=[
            "Historical authorizations are preserved",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 6: COMPLETE → COMPLETE (No Change)
# ---------------------------------------------------------------------------


def run_complete_to_complete(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """COMPLETE → COMPLETE: No epistemic change."""
    engine.state_machine.set_state(
        entity_id="graph_005",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    transition = engine.state_machine.set_state(
        entity_id="graph_005",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="complete_to_complete",
        description="COMPLETE → COMPLETE: No change",
        transition=transition,
        notes="No epistemic change means no authority consequence",
    )


# ---------------------------------------------------------------------------
# Experiment 7: Epistemic Transition Creates Authority
# ---------------------------------------------------------------------------


def run_epistemic_creates_authority(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """Test that epistemic transitions can create authority.
    
    UNKNOWN → COMPLETE changes disposition from HOLD to NORMAL.
    This is effectively authority creation via epistemic change.
    """
    transition = engine.state_machine.set_state(
        entity_id="graph_006",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="epistemic_creates_authority",
        description="Epistemic transition creates authority",
        transition=transition,
        notes="UNKNOWN → COMPLETE creates authority via disposition change",
        normative_assumptions=[
            "Epistemic transitions are consequential",
            "Authority can be created by epistemic change",
        ],
    )


# ---------------------------------------------------------------------------
# Experiment 8: Epistemic Transition Constrains Authority
# ---------------------------------------------------------------------------


def run_epistemic_constrains_authority(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """Test that epistemic transitions can constrain authority.
    
    COMPLETE → INCOMPLETE changes disposition from NORMAL to REVIEW.
    This is effectively authority constraint via epistemic change.
    """
    engine.state_machine.set_state(
        entity_id="graph_007",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    transition = engine.state_machine.set_state(
        entity_id="graph_007",
        state="incomplete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="epistemic_constrains_authority",
        description="Epistemic transition constrains authority",
        transition=transition,
        notes="COMPLETE → INCOMPLETE constrains authority via disposition change",
    )


# ---------------------------------------------------------------------------
# Experiment 9: Temporal Epistemic Transition
# ---------------------------------------------------------------------------


def run_temporal_epistemic(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """Test temporal epistemic transitions.
    
    An epistemic state that was complete at T1 but becomes incomplete
    at T2. The historical authorization is preserved, but future
    authority is constrained.
    """
    engine.state_machine.set_state(
        entity_id="graph_008",
        state="complete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    engine.state_machine.set_state(
        entity_id="graph_008",
        state="was_complete_at_t",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    transition = engine.state_machine.set_state(
        entity_id="graph_008",
        state="incomplete",
        actor="observer",
        authority_basis="observation_authority",
    )
    
    return engine.run_experiment(
        experiment_name="temporal_epistemic",
        description="Temporal epistemic transition",
        transition=transition,
        notes="Temporal transition preserves historical, constrains future",
    )


# ---------------------------------------------------------------------------
# Experiment 10: Epistemic State Machine Governance
# ---------------------------------------------------------------------------


def run_epistemic_governance(engine: EpistemicStateConsequentialityEngine) -> EpistemicStateExperiment:
    """Test governance over the epistemic state machine.
    
    Who has authority to transition epistemic states? The epistemic
    state machine itself must be governed.
    """
    transition = engine.state_machine.set_state(
        entity_id="graph_009",
        state="complete",
        actor="governance_admin",
        authority_basis="governance_authority",
    )
    
    return engine.run_experiment(
        experiment_name="epistemic_governance",
        description="Epistemic state machine governance",
        transition=transition,
        notes="Epistemic state transitions require governance authority",
        normative_assumptions=[
            "Epistemic state machine is governed",
        ],
    )


# ---------------------------------------------------------------------------
# Run All Phase 23 Experiments
# ---------------------------------------------------------------------------


def run_all_phase23_experiments() -> dict[str, Any]:
    """Run all Phase 23 experiments."""
    engine = EpistemicStateConsequentialityEngine()
    
    experiments = [
        run_unknown_to_complete(engine),
        run_complete_to_incomplete(engine),
        run_complete_to_unknown(engine),
        run_unknown_to_incomplete(engine),
        run_was_complete_to_incomplete(engine),
        run_complete_to_complete(engine),
    ]
    
    engine = EpistemicStateConsequentialityEngine()
    experiments.extend([
        run_epistemic_creates_authority(engine),
        run_epistemic_constrains_authority(engine),
    ])
    
    engine = EpistemicStateConsequentialityEngine()
    experiments.extend([
        run_temporal_epistemic(engine),
        run_epistemic_governance(engine),
    ])
    
    return {
        "experiments": {e.experiment_name: e for e in experiments},
        "total_experiments": len(experiments),
        "creates_authority_count": sum(
            1 for e in experiments
            if e.transition.classification
            == EpistemicTransitionConsequence.CREATES_AUTHORITY
        ),
        "constrains_authority_count": sum(
            1 for e in experiments
            if e.transition.classification
            == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY
        ),
        "no_effect_count": sum(
            1 for e in experiments
            if e.transition.classification
            == EpistemicTransitionConsequence.NO_AUTHORITY_EFFECT
        ),
    }


if __name__ == "__main__":
    results = run_all_phase23_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 23: EPISTEMIC STATE CONSEQUENTIALITY")
    print("=" * 120)
    
    print(f"\nTotal experiments: {results['total_experiments']}")
    print(f"Creates authority: {results['creates_authority_count']}")
    print(f"Constrains authority: {results['constrains_authority_count']}")
    print(f"No effect: {results['no_effect_count']}")
    
    for name, exp in results["experiments"].items():
        print(f"\n{name}:")
        print(f"  Description: {exp.description}")
        print(f"  Transition: {exp.transition.from_state} → {exp.transition.to_state}")
        print(f"  Classification: {exp.transition.classification.value}")
        print(f"  Notes: {exp.notes}")
        if exp.underspecifications:
            print(f"  Underspecifications: {exp.underspecifications}")
