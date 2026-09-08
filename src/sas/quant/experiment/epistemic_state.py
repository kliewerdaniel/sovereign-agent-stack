"""Epistemic State Transitions — immutable state machine for epistemic authority.

Implements the architectural transition from "evaluate evidence" to
"maintain a provenance-backed epistemic state that updates through
explicit, deterministic transitions."

The central research question:
    Can the system maintain a provenance-backed epistemic state for a
    proposition and update that state through explicit, deterministic
    transitions when new evidence arrives?

This is NOT a confidence tracker.
This is NOT a Bayesian belief system.
This is NOT a probability-of-truth model.
This is NOT a mutable status field.

Architecture:
    Proposition → Initial Epistemic State → Evidence → Epistemic Assessment
        → Epistemic Transition → New Immutable State → Gap Analysis
        → Experiment Selection → Governance → Execution → Evidence → ...

Invariants:
    An epistemic state is not a belief held by an agent. It is a
    provenance-backed description of what the system is currently
    authorized to conclude from a particular body of evidence.

    Epistemic authority is a state transition, not a scalar.

    Historical epistemic states must remain immutable.

    New evidence may revise authority without rewriting history.

    Authority cannot increase without a provenance-backed transition.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    InterventionType,
    PropositionType,
    TypedProposition,
)
from sas.quant.experiment.evidence_structure import (
    EvidenceAccumulator,
    EvidenceDimension,
    EvidenceProfile,
    StructuredEvidenceBundle,
    evaluate_structured_proposition,
)
from sas.quant.experiment.epistemic_gaps import (
    EpistemicGap,
    GapType,
    GapResolvability,
    GapClosingPotential,
    EvidenceSufficiencyAssessment,
    analyze_evidence_gaps,
)


# ---------------------------------------------------------------------------
# Epistemic Status
# ---------------------------------------------------------------------------


class EpistemicStatus(str, Enum):
    """Status of a proposition's epistemic state.

    This is ONE projection of the state, not the entire state.
    The actual epistemic state is the structured collection of
    evidence, authority, gaps, alternatives, scope, and provenance.
    """
    UNKNOWN = "unknown"
    INCONCLUSIVE = "inconclusive"
    PARTIALLY_SUPPORTED = "partially_supported"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    CONTRADICTED = "contradicted"
    REVISED = "revised"


# ---------------------------------------------------------------------------
# State Dimensions
# ---------------------------------------------------------------------------


class StateDimension(str, Enum):
    """Dimensions along which epistemic state can vary.

    A proposition may simultaneously become stronger in one dimension
    while remaining unresolved in another.
    """
    MECHANISM = "mechanism"
    TEMPORAL = "temporal"
    GENERALIZATION = "generalization"
    CAUSAL = "causal"
    REPLICATION = "replication"
    INDEPENDENCE = "independence"
    ALTERNATIVE_EXCLUSION = "alternative_exclusion"


class DimensionStatus(str, Enum):
    """Status of a single dimension."""
    UNRESOLVED = "unresolved"
    IDENTIFIED = "identified"
    REPLICATED = "replicated"
    ROBUST = "robust"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class DimensionState:
    """State of a single epistemic dimension."""
    dimension: StateDimension
    status: DimensionStatus
    evidence_count: int = 0
    authority_basis: str = ""
    provenance: str = ""

    def is_at_least_as_strong_as(self, other: "DimensionState") -> bool:
        """Check if this dimension is at least as strong as other."""
        if self.dimension != other.dimension:
            return False
        strength_order = {
            DimensionStatus.UNRESOLVED: 0,
            DimensionStatus.IDENTIFIED: 1,
            DimensionStatus.REPLICATED: 2,
            DimensionStatus.ROBUST: 3,
            DimensionStatus.AVAILABLE: 3,
            DimensionStatus.UNAVAILABLE: 0,
        }
        return strength_order.get(self.status, 0) >= strength_order.get(other.status, 0)


# ---------------------------------------------------------------------------
# Epistemic State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicState:
    """Immutable epistemic state of a proposition.

    Contains enough information to reconstruct exactly why the proposition
    currently occupies its state.

    The status is only one projection of the state. The actual epistemic
    state is the structured collection of evidence, authority, gaps,
    alternatives, scope, and provenance.
    """
    state_id: str
    proposition_id: str
    proposition_type: PropositionType

    status: EpistemicStatus

    # Dimension-specific states
    dimension_states: dict[StateDimension, DimensionState] = field(default_factory=dict)

    # Established and unresolved
    established_dimensions: list[StateDimension] = field(default_factory=list)
    unresolved_dimensions: list[StateDimension] = field(default_factory=list)

    # Gaps
    epistemic_gaps: list[EpistemicGap] = field(default_factory=list)

    # References to evidence and experiments
    evidence_refs: list[str] = field(default_factory=list)
    experiment_refs: list[str] = field(default_factory=list)
    intervention_refs: list[InterventionType] = field(default_factory=list)

    # Scope
    authority_scope: set[InterventionType] = field(default_factory=set)
    generalization_scope: str = ""
    temporal_scope: str = ""

    # Blocking alternatives
    blocking_alternatives: list[str] = field(default_factory=list)

    # Lineage
    parent_state_id: Optional[str] = None
    transition_id: Optional[str] = None

    # Provenance
    provenance_hash: str = ""
    policy_version: str = "1.0.0"

    @property
    def is_supported(self) -> bool:
        return self.status == EpistemicStatus.SUPPORTED

    @property
    def is_inconclusive(self) -> bool:
        return self.status == EpistemicStatus.INCONCLUSIVE

    @property
    def is_refuted(self) -> bool:
        return self.status == EpistemicStatus.REFUTED

    @property
    def is_contradicted(self) -> bool:
        return self.status == EpistemicStatus.CONTRADICTED

    @property
    def has_gaps(self) -> bool:
        return len(self.epistemic_gaps) > 0

    @property
    def mechanism_status(self) -> Optional[DimensionStatus]:
        return self.dimension_states.get(StateDimension.MECHANISM, DimensionState(
            dimension=StateDimension.MECHANISM,
            status=DimensionStatus.UNRESOLVED,
        )).status

    @property
    def generalization_status(self) -> Optional[DimensionStatus]:
        return self.dimension_states.get(StateDimension.GENERALIZATION, DimensionState(
            dimension=StateDimension.GENERALIZATION,
            status=DimensionStatus.UNRESOLVED,
        )).status

    def explain(self) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"Epistemic State: {self.state_id}",
            f"Proposition: {self.proposition_id}",
            f"Status: {self.status.value}",
            "",
        ]
        if self.dimension_states:
            lines.append("Dimensions:")
            for dim, state in self.dimension_states.items():
                lines.append(f"  {dim.value}: {state.status.value}")
            lines.append("")
        if self.established_dimensions:
            lines.append(f"Established: {[d.value for d in self.established_dimensions]}")
        if self.unresolved_dimensions:
            lines.append(f"Unresolved: {[d.value for d in self.unresolved_dimensions]}")
        if self.epistemic_gaps:
            lines.append(f"Gaps: {len(self.epistemic_gaps)}")
        if self.blocking_alternatives:
            lines.append(f"Blocking alternatives: {self.blocking_alternatives}")
        if self.parent_state_id:
            lines.append(f"Parent: {self.parent_state_id}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Epistemic Transition
# ---------------------------------------------------------------------------


class TransitionType(str, Enum):
    """Type of epistemic transition."""
    INITIAL = "initial"
    EVIDENCE_ADDED = "evidence_added"
    AUTHORITY_INCREASED = "authority_increased"
    AUTHORITY_RETRACTED = "authority_retracted"
    GAP_CLOSED = "gap_closed"
    GAP_OPENED = "gap_opened"
    ALTERNATIVE_ELIMINATED = "alternative_eliminated"
    ALTERNATIVE_REOPENED = "alternative_reopened"
    CONTRADICTION_INTRODUCED = "contradiction_introduced"
    STATE_REVISED = "state_revised"


@dataclass(frozen=True)
class EpistemicTransition:
    """Immutable epistemic transition.

    A transition never mutates the previous state. Instead:
        S0 → T1 → S1
    and S0 remains immutable forever.
    """
    transition_id: str
    proposition_id: str

    previous_state_id: str
    resulting_state_id: str

    transition_type: TransitionType

    # What triggered the transition
    triggering_artifact: str = ""

    # Evidence changes
    evidence_added: list[str] = field(default_factory=list)
    evidence_removed: list[str] = field(default_factory=list)

    # Gap changes
    gaps_closed: list[str] = field(default_factory=list)
    gaps_opened: list[str] = field(default_factory=list)

    # Authority changes
    authority_added: dict[str, str] = field(default_factory=dict)
    authority_unchanged: list[str] = field(default_factory=list)
    authority_retracted: dict[str, str] = field(default_factory=dict)

    # Alternative changes
    alternatives_eliminated: list[str] = field(default_factory=list)
    alternatives_reopened: list[str] = field(default_factory=list)

    # Reasoning
    transition_reason: str = ""

    # Versioning
    policy_version: str = "1.0.0"
    evaluator_version: str = "1.0.0"

    # Provenance
    provenance_hash: str = ""

    def explain(self) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"Transition: {self.transition_id}",
            f"Type: {self.transition_type.value}",
            f"Previous: {self.previous_state_id}",
            f"Resulting: {self.resulting_state_id}",
            "",
        ]
        if self.evidence_added:
            lines.append(f"Evidence added: {self.evidence_added}")
        if self.gaps_closed:
            lines.append(f"Gaps closed: {self.gaps_closed}")
        if self.gaps_opened:
            lines.append(f"Gaps opened: {self.gaps_opened}")
        if self.authority_added:
            lines.append(f"Authority added: {self.authority_added}")
        if self.authority_retracted:
            lines.append(f"Authority retracted: {self.authority_retracted}")
        if self.transition_reason:
            lines.append(f"Reason: {self.transition_reason}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Transition Authorization
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransitionAuthorization:
    """Authorization for a state transition.

    Transition recommendation ≠ transition authorization.
    The agent may propose a transition. The deterministic epistemic layer
    must authorize it based on artifacts.
    """
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    authority_basis: str = ""
    blocked_gaps: list[str] = field(default_factory=list)


def can_transition(
    previous_state: EpistemicState,
    evidence: list[StructuredEvidenceBundle],
    proposition: TypedProposition,
    authority_policy: str = "strict",
) -> TransitionAuthorization:
    """Determine whether a transition is authorized.

    Checks that new evidence satisfies authority requirements.
    """
    reasons: list[str] = []
    required_evidence: list[str] = []
    blocked_gaps: list[str] = []

    # Check that evidence has authority over proposition
    authorized_evidence = []
    for bundle in evidence:
        if proposition.accepts_evidence_from(bundle.intervention_type):
            authorized_evidence.append(bundle)
        else:
            reasons.append(
                f"Evidence {bundle.evidence_id} from {bundle.intervention_type.value} "
                f"cannot inform {proposition.proposition_type.value}"
            )

    if not authorized_evidence:
        return TransitionAuthorization(
            allowed=False,
            reasons=reasons + ["No authorized evidence for transition"],
            required_evidence=[f"evidence from {proposition.proposition_type.value}-authorized interventions"],
            blocked_gaps=[g.gap_id for g in previous_state.epistemic_gaps],
        )

    # Check for duplicate evidence
    existing_ids = set(previous_state.evidence_refs)
    new_evidence = [b for b in authorized_evidence if b.evidence_id not in existing_ids]
    if not new_evidence:
        return TransitionAuthorization(
            allowed=False,
            reasons=["No new evidence (all evidence already in state)"],
        )

    # Check for dependent evidence
    existing_seeds = set()
    for ref in previous_state.evidence_refs:
        # Parse seed from evidence ref (simplified)
        if "seed=" in ref:
            seed = int(ref.split("seed=")[1].split(",")[0])
            existing_seeds.add(seed)

    independent_evidence = []
    for bundle in new_evidence:
        if bundle.seed == 0 or bundle.seed not in existing_seeds:
            independent_evidence.append(bundle)
        else:
            reasons.append(
                f"Evidence {bundle.evidence_id} uses seed {bundle.seed} "
                f"which already exists in state"
            )

    # Transition is allowed if there's at least some new evidence
    allowed = len(new_evidence) > 0

    return TransitionAuthorization(
        allowed=allowed,
        reasons=reasons if reasons else ["Transition authorized"],
        required_evidence=required_evidence,
        authority_basis=f"Evidence from authorized interventions: {[b.intervention_type.value for b in new_evidence]}",
        blocked_gaps=blocked_gaps,
    )


# ---------------------------------------------------------------------------
# Epistemic State Machine
# ---------------------------------------------------------------------------


class EpistemicStateMachine:
    """Manages the chain of epistemic states for a proposition.

    States are immutable. Transitions are immutable.
    History is preserved. No rewriting.
    """

    def __init__(self, proposition: TypedProposition):
        self.proposition = proposition
        self.states: dict[str, EpistemicState] = {}
        self.transitions: dict[str, EpistemicTransition] = {}
        self.current_state_id: Optional[str] = None
        self.state_counter: int = 0
        self.transition_counter: int = 0

    def _generate_state_id(self) -> str:
        self.state_counter += 1
        return f"state_{self.proposition.proposition_id}_{self.state_counter:04d}"

    def _generate_transition_id(self) -> str:
        self.transition_counter += 1
        return f"transition_{self.proposition.proposition_id}_{self.transition_counter:04d}"

    def _compute_provenance_hash(self, *args) -> str:
        """Compute a provenance hash from arguments."""
        content = json.dumps([str(a) for a in args], sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def create_initial_state(self) -> EpistemicState:
        """Create the initial epistemic state for the proposition."""
        state_id = self._generate_state_id()

        state = EpistemicState(
            state_id=state_id,
            proposition_id=self.proposition.proposition_id,
            proposition_type=self.proposition.proposition_type,
            status=EpistemicStatus.UNKNOWN,
            dimension_states={
                dim: DimensionState(
                    dimension=dim,
                    status=DimensionStatus.UNRESOLVED,
                )
                for dim in StateDimension
            },
            unresolved_dimensions=list(StateDimension),
            authority_scope=set(),
            provenance_hash=self._compute_provenance_hash("initial", self.proposition.proposition_id),
        )

        self.states[state_id] = state
        self.current_state_id = state_id
        return state

    def apply_evidence(
        self,
        evidence: list[StructuredEvidenceBundle],
        experiment_id: str = "",
    ) -> tuple[EpistemicTransition, EpistemicState]:
        """Apply new evidence to create a new epistemic state.

        Returns the transition and the new state.
        The previous state remains immutable.
        """
        if self.current_state_id is None:
            self.create_initial_state()

        assert self.current_state_id is not None
        previous_state = self.states[self.current_state_id]

        # Authorize transition
        auth = can_transition(previous_state, evidence, self.proposition)

        if not auth.allowed:
            # Create a "rejected" transition
            transition = EpistemicTransition(
                transition_id=self._generate_transition_id(),
                proposition_id=self.proposition.proposition_id,
                previous_state_id=previous_state.state_id,
                resulting_state_id=previous_state.state_id,
                transition_type=TransitionType.STATE_REVISED,
                transition_reason=f"Transition not allowed: {'; '.join(auth.reasons)}",
            )
            return transition, previous_state

        # Build new evidence accumulator
        accumulator = EvidenceAccumulator()
        for ref in previous_state.evidence_refs:
            # In a real system, we'd reconstruct from storage
            # For now, we track refs
            pass
        for bundle in evidence:
            accumulator.add(bundle)

        # Analyze gaps
        assessment = analyze_evidence_gaps(self.proposition, accumulator)

        # Compute new dimension states
        new_dimension_states = dict(previous_state.dimension_states)
        authority_added = {}
        authority_retracted = {}
        gaps_closed = []
        gaps_opened = []

        # Update mechanism dimension
        mechanism_evidence = [
            b for b in evidence
            if b.intervention_type in {
                InterventionType.MECHANISM_REMOVAL,
                InterventionType.MECHANISM_AMPLIFICATION,
                InterventionType.MECHANISM_DECORRELATION,
            }
        ]
        if mechanism_evidence:
            current = new_dimension_states.get(StateDimension.MECHANISM)
            if current is None or current.status == DimensionStatus.UNRESOLVED:
                new_dimension_states[StateDimension.MECHANISM] = DimensionState(
                    dimension=StateDimension.MECHANISM,
                    status=DimensionStatus.IDENTIFIED,
                    evidence_count=len(mechanism_evidence),
                    authority_basis=f"Evidence from {mechanism_evidence[0].intervention_type.value}",
                )
                authority_added["mechanism"] = f"identified via {len(mechanism_evidence)} mechanism interventions"
            elif current.status == DimensionStatus.IDENTIFIED:
                # Check for replication
                total_count = current.evidence_count + len(mechanism_evidence)
                if total_count >= 3:
                    new_dimension_states[StateDimension.MECHANISM] = DimensionState(
                        dimension=StateDimension.MECHANISM,
                        status=DimensionStatus.REPLICATED,
                        evidence_count=total_count,
                        authority_basis=f"Replicated across {total_count} mechanism interventions",
                    )
                    authority_added["mechanism"] = f"replicated ({total_count} interventions)"

        # Update generalization dimension
        generalization_evidence = [
            b for b in evidence
            if b.intervention_type in {
                InterventionType.HOLDOUT,
                InterventionType.BOOTSTRAP,
                InterventionType.SUBSAMPLE,
            }
        ]
        if generalization_evidence:
            current = new_dimension_states.get(StateDimension.GENERALIZATION)
            if current is None or current.status == DimensionStatus.UNRESOLVED:
                new_dimension_states[StateDimension.GENERALIZATION] = DimensionState(
                    dimension=StateDimension.GENERALIZATION,
                    status=DimensionStatus.IDENTIFIED,
                    evidence_count=len(generalization_evidence),
                    authority_basis=f"Evidence from {generalization_evidence[0].intervention_type.value}",
                )
                authority_added["generalization"] = f"identified via {len(generalization_evidence)} holdout interventions"

        # Update replication dimension
        new_seeds = set(b.seed for b in evidence if b.seed != 0)
        if len(new_seeds) >= 3:
            current = new_dimension_states.get(StateDimension.REPLICATION)
            if current is None or current.status == DimensionStatus.UNRESOLVED:
                new_dimension_states[StateDimension.REPLICATION] = DimensionState(
                    dimension=StateDimension.REPLICATION,
                    status=DimensionStatus.REPLICATED,
                    evidence_count=len(new_seeds),
                    authority_basis=f"Independent replications with {len(new_seeds)} seeds",
                )
                authority_added["replication"] = f"replicated across {len(new_seeds)} seeds"

        # Update independence dimension
        if len(new_seeds) >= 3:
            current = new_dimension_states.get(StateDimension.INDEPENDENCE)
            if current is None or current.status == DimensionStatus.UNRESOLVED:
                new_dimension_states[StateDimension.INDEPENDENCE] = DimensionState(
                    dimension=StateDimension.INDEPENDENCE,
                    status=DimensionStatus.IDENTIFIED,
                    evidence_count=len(new_seeds),
                    authority_basis=f"Evidence from {len(new_seeds)} independent seeds",
                )
                authority_added["independence"] = f"independent evidence from {len(new_seeds)} seeds"

        # Check for contradictions
        # If new evidence contradicts previous evidence, mark as contradicted
        has_contradiction = self._check_contradiction(previous_state, evidence)

        # Determine new status
        if has_contradiction:
            new_status = EpistemicStatus.CONTRADICTED
        elif assessment.status == "SUPPORTED":
            new_status = EpistemicStatus.SUPPORTED
        elif assessment.status == "REFUTED":
            new_status = EpistemicStatus.REFUTED
        elif len(authority_added) > 0:
            new_status = EpistemicStatus.PARTIALLY_SUPPORTED
        else:
            new_status = EpistemicStatus.INCONCLUSIVE

        # Determine established and unresolved dimensions
        established = [
            dim for dim, state in new_dimension_states.items()
            if state.status not in {DimensionStatus.UNRESOLVED, DimensionStatus.UNAVAILABLE}
        ]
        unresolved = [
            dim for dim, state in new_dimension_states.items()
            if state.status in {DimensionStatus.UNRESOLVED, DimensionStatus.UNAVAILABLE}
        ]

        # Build new state
        new_state_id = self._generate_state_id()
        new_state = EpistemicState(
            state_id=new_state_id,
            proposition_id=self.proposition.proposition_id,
            proposition_type=self.proposition.proposition_type,
            status=new_status,
            dimension_states=new_dimension_states,
            established_dimensions=established,
            unresolved_dimensions=unresolved,
            epistemic_gaps=assessment.epistemic_gaps,
            evidence_refs=previous_state.evidence_refs + [b.evidence_id for b in evidence],
            experiment_refs=previous_state.experiment_refs + ([experiment_id] if experiment_id else []),
            intervention_refs=list(set(previous_state.intervention_refs + [b.intervention_type for b in evidence])),
            authority_scope=previous_state.authority_scope | {b.intervention_type for b in evidence},
            blocking_alternatives=assessment.blocking_alternatives,
            parent_state_id=previous_state.state_id,
            transition_id=None,  # Will be set after transition creation
            provenance_hash=self._compute_provenance_hash(
                previous_state.provenance_hash,
                [b.evidence_id for b in evidence],
            ),
        )

        # Determine transition type
        if has_contradiction:
            transition_type = TransitionType.CONTRADICTION_INTRODUCED
        elif len(authority_added) > 0:
            transition_type = TransitionType.AUTHORITY_INCREASED
        elif len(authority_retracted) > 0:
            transition_type = TransitionType.AUTHORITY_RETRACTED
        else:
            transition_type = TransitionType.EVIDENCE_ADDED

        # Create transition
        transition = EpistemicTransition(
            transition_id=self._generate_transition_id(),
            proposition_id=self.proposition.proposition_id,
            previous_state_id=previous_state.state_id,
            resulting_state_id=new_state_id,
            transition_type=transition_type,
            triggering_artifact=evidence[0].evidence_id if evidence else "",
            evidence_added=[b.evidence_id for b in evidence],
            gaps_closed=gaps_closed,
            gaps_opened=gaps_opened,
            authority_added=authority_added,
            authority_unchanged=[],
            authority_retracted=authority_retracted,
            alternatives_eliminated=[],
            alternatives_reopened=[],
            transition_reason=f"Applied {len(evidence)} evidence items",
            provenance_hash=self._compute_provenance_hash(
                previous_state.state_id,
                [b.evidence_id for b in evidence],
            ),
        )

        # Update state with transition ID
        new_state = EpistemicState(
            state_id=new_state_id,
            proposition_id=self.proposition.proposition_id,
            proposition_type=self.proposition.proposition_type,
            status=new_status,
            dimension_states=new_dimension_states,
            established_dimensions=established,
            unresolved_dimensions=unresolved,
            epistemic_gaps=assessment.epistemic_gaps,
            evidence_refs=previous_state.evidence_refs + [b.evidence_id for b in evidence],
            experiment_refs=previous_state.experiment_refs + ([experiment_id] if experiment_id else []),
            intervention_refs=list(set(previous_state.intervention_refs + [b.intervention_type for b in evidence])),
            authority_scope=previous_state.authority_scope | {b.intervention_type for b in evidence},
            blocking_alternatives=assessment.blocking_alternatives,
            parent_state_id=previous_state.state_id,
            transition_id=transition.transition_id,
            provenance_hash=self._compute_provenance_hash(
                previous_state.provenance_hash,
                [b.evidence_id for b in evidence],
            ),
        )

        # Store
        self.states[new_state_id] = new_state
        self.transitions[transition.transition_id] = transition
        self.current_state_id = new_state_id

        return transition, new_state

    def _check_contradiction(
        self,
        previous_state: EpistemicState,
        new_evidence: list[StructuredEvidenceBundle],
    ) -> bool:
        """Check if new evidence contradicts previous evidence."""
        # Simplified: check if previous state was supported and new evidence has opposite effect
        if previous_state.status in {EpistemicStatus.SUPPORTED, EpistemicStatus.PARTIALLY_SUPPORTED}:
            # Check if new evidence has opposite sign
            # This is a simplified check - a full implementation would
            # compare effect sizes more carefully
            return False
        return False

    def get_current_state(self) -> Optional[EpistemicState]:
        """Get the current epistemic state."""
        if self.current_state_id is None:
            return None
        return self.states[self.current_state_id]

    def get_state_history(self) -> list[EpistemicState]:
        """Get the full state history."""
        history = []
        current = self.get_current_state()
        while current is not None:
            history.append(current)
            if current.parent_state_id is not None:
                current = self.states.get(current.parent_state_id)
            else:
                break
        return list(reversed(history))

    def get_transition_history(self) -> list[EpistemicTransition]:
        """Get the full transition history."""
        history = []
        current = self.get_current_state()
        while current is not None and current.transition_id is not None:
            transition = self.transitions.get(current.transition_id)
            if transition is not None:
                history.append(transition)
            if current.parent_state_id is not None:
                current = self.states.get(current.parent_state_id)
            else:
                break
        return list(reversed(history))


# ---------------------------------------------------------------------------
# Evidence Reconciliation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconciliationAssessment:
    """Assessment of reconciling two evidence branches."""
    agreements: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    overlapping_evidence: list[str] = field(default_factory=list)
    dependent_evidence: list[str] = field(default_factory=list)
    independent_evidence: list[str] = field(default_factory=list)
    reopened_gaps: list[str] = field(default_factory=list)
    authority_changes: dict[str, str] = field(default_factory=dict)
    unresolved_conflicts: list[str] = field(default_factory=list)


def reconcile_evidence_branches(
    branch_a: list[StructuredEvidenceBundle],
    branch_b: list[StructuredEvidenceBundle],
) -> ReconciliationAssessment:
    """Reconcile two independently produced evidence histories.

    Does not simply merge lists. Preserves provenance and dependency structure.
    """
    agreements = []
    contradictions = []
    overlapping = []
    dependent = []
    independent = []

    # Find overlapping evidence (same ID)
    ids_a = {b.evidence_id for b in branch_a}
    ids_b = {b.evidence_id for b in branch_b}
    overlapping_ids = ids_a & ids_b

    for b in branch_a:
        if b.evidence_id in overlapping_ids:
            overlapping.append(b.evidence_id)

    # Find dependent evidence (same seed)
    seeds_a = {b.seed for b in branch_a if b.seed != 0}
    seeds_b = {b.seed for b in branch_b if b.seed != 0}
    shared_seeds = seeds_a & seeds_b

    for b in branch_a + branch_b:
        if b.seed in shared_seeds and b.evidence_id not in overlapping_ids:
            dependent.append(b.evidence_id)

    # Find independent evidence
    for b in branch_a + branch_b:
        if b.evidence_id not in overlapping_ids and b.seed not in shared_seeds:
            independent.append(b.evidence_id)

    return ReconciliationAssessment(
        agreements=agreements,
        contradictions=contradictions,
        overlapping_evidence=overlapping,
        dependent_evidence=dependent,
        independent_evidence=independent,
    )


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_initial_state(proposition: TypedProposition) -> EpistemicState:
    """Create an initial epistemic state for a proposition."""
    machine = EpistemicStateMachine(proposition)
    return machine.create_initial_state()


def apply_evidence(
    machine: EpistemicStateMachine,
    evidence: list[StructuredEvidenceBundle],
) -> tuple[EpistemicTransition, EpistemicState]:
    """Apply evidence to the state machine."""
    return machine.apply_evidence(evidence)
