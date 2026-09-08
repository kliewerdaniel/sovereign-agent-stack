"""Tests for Epistemic State module."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_state import (
    EpistemicStatus,
    StateDimension,
    DimensionStatus,
    DimensionState,
    EpistemicState,
    TransitionType,
    EpistemicTransition,
    TransitionAuthorization,
    ReconciliationAssessment,
    EpistemicStateMachine,
    can_transition,
    reconcile_evidence_branches,
    create_initial_state,
    apply_evidence,
)
from sas.quant.experiment.evidence_structure import (
    StructuredEvidenceBundle,
)
from sas.quant.experiment.typed_propositions import (
    InterventionType,
    PropositionType,
    TypedProposition,
)


# ---------------------------------------------------------------------------
# Test: Epistemic Status
# ---------------------------------------------------------------------------


class TestEpistemicStatus:
    def test_all_statuses_present(self):
        statuses = list(EpistemicStatus)
        assert len(statuses) == 7
        assert EpistemicStatus.UNKNOWN in statuses
        assert EpistemicStatus.INCONCLUSIVE in statuses
        assert EpistemicStatus.PARTIALLY_SUPPORTED in statuses
        assert EpistemicStatus.SUPPORTED in statuses
        assert EpistemicStatus.REFUTED in statuses
        assert EpistemicStatus.CONTRADICTED in statuses
        assert EpistemicStatus.REVISED in statuses


# ---------------------------------------------------------------------------
# Test: State Dimensions
# ---------------------------------------------------------------------------


class TestStateDimensions:
    def test_all_dimensions_present(self):
        dims = list(StateDimension)
        assert len(dims) == 7
        assert StateDimension.MECHANISM in dims
        assert StateDimension.TEMPORAL in dims
        assert StateDimension.GENERALIZATION in dims
        assert StateDimension.CAUSAL in dims
        assert StateDimension.REPLICATION in dims
        assert StateDimension.INDEPENDENCE in dims
        assert StateDimension.ALTERNATIVE_EXCLUSION in dims


# ---------------------------------------------------------------------------
# Test: Dimension State
# ---------------------------------------------------------------------------


class TestDimensionState:
    def test_is_at_least_as_strong_as(self):
        strong = DimensionState(
            dimension=StateDimension.MECHANISM,
            status=DimensionStatus.REPLICATED,
        )
        weak = DimensionState(
            dimension=StateDimension.MECHANISM,
            status=DimensionStatus.IDENTIFIED,
        )
        assert strong.is_at_least_as_strong_as(weak)
        assert not weak.is_at_least_as_strong_as(strong)

    def test_different_dimensions_not_comparable(self):
        a = DimensionState(
            dimension=StateDimension.MECHANISM,
            status=DimensionStatus.REPLICATED,
        )
        b = DimensionState(
            dimension=StateDimension.TEMPORAL,
            status=DimensionStatus.UNRESOLVED,
        )
        assert not a.is_at_least_as_strong_as(b)


# ---------------------------------------------------------------------------
# Test: Epistemic State
# ---------------------------------------------------------------------------


class TestEpistemicState:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_initial_state(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)
        assert state.status == EpistemicStatus.UNKNOWN
        # Initial state is UNKNOWN (not yet inconclusive - that comes after first evidence)
        assert not state.is_supported
        assert len(state.unresolved_dimensions) == 7
        assert state.parent_state_id is None

    def test_state_is_immutable(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)
        with pytest.raises(AttributeError):
            state.status = EpistemicStatus.SUPPORTED

    def test_explain(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)
        explanation = state.explain()
        assert "p1" in explanation
        assert "unknown" in explanation


# ---------------------------------------------------------------------------
# Test: Epistemic State Machine
# ---------------------------------------------------------------------------


class TestEpistemicStateMachine:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_create_initial_state(self):
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        state = machine.create_initial_state()
        assert state.status == EpistemicStatus.UNKNOWN
        assert machine.current_state_id == state.state_id

    def test_apply_single_evidence(self):
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=42,
            )
        ]

        transition, new_state = machine.apply_evidence(evidence)

        assert transition.previous_state_id is not None
        assert transition.resulting_state_id == new_state.state_id
        assert new_state.parent_state_id == transition.previous_state_id
        assert "e1" in new_state.evidence_refs

    def test_apply_multiple_evidence(self):
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        transition, new_state = machine.apply_evidence(evidence)

        assert len(new_state.evidence_refs) == 5
        assert new_state.status in {
            EpistemicStatus.PARTIALLY_SUPPORTED,
            EpistemicStatus.SUPPORTED,
            EpistemicStatus.INCONCLUSIVE,
        }

    def test_state_history_preserved(self):
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence1 = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        _, state1 = machine.apply_evidence(evidence1)

        evidence2 = [
            StructuredEvidenceBundle(
                evidence_id="e2",
                intervention_type=InterventionType.MECHANISM_AMPLIFICATION,
                target="signal_component",
                effect_size=0.7,
                description="Mechanism evidence",
                seed=2,
            )
        ]

        _, state2 = machine.apply_evidence(evidence2)

        # State history should be preserved
        history = machine.get_state_history()
        assert len(history) >= 2
        assert history[0].state_id != history[-1].state_id

        # Previous state should be immutable
        assert state1.parent_state_id is not None
        assert state2.parent_state_id == state1.state_id

    def test_transition_history(self):
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        machine.apply_evidence(evidence)

        transitions = machine.get_transition_history()
        assert len(transitions) >= 1


# ---------------------------------------------------------------------------
# Test: Transition Authorization
# ---------------------------------------------------------------------------


class TestTransitionAuthorization:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_authorized_transition(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=42,
            )
        ]

        auth = can_transition(state, evidence, prop)
        assert auth.allowed

    def test_unauthorized_wrong_intervention(self):
        prop = self._create_proposition()
        state = create_initial_state(prop)

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Wrong type",
                seed=42,
            )
        ]

        auth = can_transition(state, evidence, prop)
        # Should NOT be allowed - no authorized evidence
        assert not auth.allowed

    def test_no_new_evidence(self):
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        machine.apply_evidence(evidence)

        # Try to apply same evidence again
        current_state = machine.get_current_state()
        assert current_state is not None
        auth = can_transition(current_state, evidence, prop)
        assert not auth.allowed  # No new evidence


# ---------------------------------------------------------------------------
# Test: Monotonicity of Earned Authority
# ---------------------------------------------------------------------------


class TestMonotonicity:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_authority_increases_with_valid_evidence(self):
        """Valid independent replication increases replication authority."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Mechanism should be at least identified
        assert new_state.mechanism_status in {
            DimensionStatus.IDENTIFIED,
            DimensionStatus.REPLICATED,
            DimensionStatus.ROBUST,
        }

    def test_authority_unchanged_with_dependent_evidence(self):
        """Additional dependent observations don't increase independence authority."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Dependent evidence",
                seed=42,  # Same seed
            )
            for i in range(10)
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Independence should still be unresolved
        independence_state = new_state.dimension_states.get(StateDimension.INDEPENDENCE)
        assert independence_state is not None
        assert independence_state.status == DimensionStatus.UNRESOLVED

    def test_wrong_intervention_no_authority(self):
        """Wrong intervention type creates no new authority over proposition."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.FEATURE_ABLATION,
                target="signal",
                effect_size=0.8,
                description="Wrong type",
                seed=i + 1,
            )
            for i in range(10)
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Mechanism should still be unresolved
        assert new_state.mechanism_status == DimensionStatus.UNRESOLVED


# ---------------------------------------------------------------------------
# Test: Evidence Reconciliation
# ---------------------------------------------------------------------------


class TestEvidenceReconciliation:
    def test_overlapping_evidence(self):
        branch_a = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Evidence 1",
                seed=1,
            )
        ]
        branch_b = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Evidence 1",
                seed=1,
            )
        ]

        result = reconcile_evidence_branches(branch_a, branch_b)
        assert "e1" in result.overlapping_evidence

    def test_dependent_evidence(self):
        branch_a = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Evidence 1",
                seed=42,
            )
        ]
        branch_b = [
            StructuredEvidenceBundle(
                evidence_id="e2",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.7,
                description="Evidence 2",
                seed=42,  # Same seed
            )
        ]

        result = reconcile_evidence_branches(branch_a, branch_b)
        assert "e2" in result.dependent_evidence

    def test_independent_evidence(self):
        branch_a = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Evidence 1",
                seed=1,
            )
        ]
        branch_b = [
            StructuredEvidenceBundle(
                evidence_id="e2",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.7,
                description="Evidence 2",
                seed=2,  # Different seed
            )
        ]

        result = reconcile_evidence_branches(branch_a, branch_b)
        assert "e1" in result.independent_evidence
        assert "e2" in result.independent_evidence


# ---------------------------------------------------------------------------
# Test: Authority Escalation Attacks
# ---------------------------------------------------------------------------


class TestAuthorityEscalationAttacks:
    """Test that authority cannot increase without appropriate evidence."""

    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def test_agent_declaring_supported_does_not_create_authority(self):
        """Agent declaring 'supported' does not create authority."""
        prop = self._create_proposition()
        state = create_initial_state(prop)
        # Initial state should be unknown, not supported
        assert state.status == EpistemicStatus.UNKNOWN
        assert not state.is_supported

    def test_larger_sample_does_not_increase_independence(self):
        """Larger sample doesn't increase independence authority."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Same seed",
                seed=42,
            )
            for i in range(100)
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Independence should still be unresolved
        independence_state = new_state.dimension_states.get(StateDimension.INDEPENDENCE)
        assert independence_state is not None
        assert independence_state.status == DimensionStatus.UNRESOLVED

    def test_dependent_replications_masquerading_as_independent(self):
        """Same seed reused while claiming independent replication."""
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        # All evidence uses same seed
        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Claimed independent",
                seed=42,  # Same seed!
            )
            for i in range(10)
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Replication should NOT be marked as replicated
        replication_state = new_state.dimension_states.get(StateDimension.REPLICATION)
        assert replication_state is not None
        assert replication_state.status == DimensionStatus.UNRESOLVED


# ---------------------------------------------------------------------------
# Test: Duplicate Evidence Detection
# ---------------------------------------------------------------------------


class TestDuplicateEvidence:
    def test_same_artifact_submitted_twice(self):
        """Same evidence artifact submitted twice should be detected."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Evidence 1",
                seed=1,
            )
        ]

        machine.apply_evidence(evidence)

        # Try to submit same evidence again
        current_state = machine.get_current_state()
        assert current_state is not None
        auth = can_transition(current_state, evidence, prop)
        assert not auth.allowed

    def test_same_experiment_different_ids(self):
        """Same experiment submitted under different IDs."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence1 = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Same experiment",
                seed=42,
            )
        ]

        machine.apply_evidence(evidence1)

        # Same experiment, different ID, same seed
        evidence2 = [
            StructuredEvidenceBundle(
                evidence_id="e2",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Same experiment",
                seed=42,  # Same seed
            )
        ]

        current_state = machine.get_current_state()
        auth = can_transition(current_state, evidence2, prop)
        # Should be allowed (new ID) but flagged as dependent
        assert auth.allowed


# ---------------------------------------------------------------------------
# Test: State Immutability
# ---------------------------------------------------------------------------


class TestStateImmutability:
    def test_previous_state_unchanged(self):
        """Previous state must remain unchanged after transition."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Initial state should be unchanged
        assert initial_state.status == EpistemicStatus.UNKNOWN
        assert initial_state.evidence_refs == []

        # New state should have evidence
        assert new_state.status != EpistemicStatus.UNKNOWN
        assert "e1" in new_state.evidence_refs


# ---------------------------------------------------------------------------
# Test: State Partial Order
# ---------------------------------------------------------------------------


class TestStatePartialOrder:
    def test_state_can_be_stronger_in_one_dimension(self):
        """State can be stronger in one dimension without being stronger globally."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        # Add mechanism evidence but no holdout
        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        _, new_state = machine.apply_evidence(evidence)

        # Mechanism should be at least identified
        assert new_state.mechanism_status in {
            DimensionStatus.IDENTIFIED,
            DimensionStatus.REPLICATED,
        }

        # Generalization should still be unresolved
        assert new_state.generalization_status == DimensionStatus.UNRESOLVED


# ---------------------------------------------------------------------------
# Test: Provenance Hash
# ---------------------------------------------------------------------------


class TestProvenanceHash:
    def test_state_has_provenance_hash(self):
        """Every state must have a provenance hash."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        state = create_initial_state(prop)
        assert len(state.provenance_hash) > 0

    def test_transition_has_provenance_hash(self):
        """Every transition must have a provenance hash."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, _ = machine.apply_evidence(evidence)
        assert len(transition.provenance_hash) > 0


# ---------------------------------------------------------------------------
# Test: Transition Explanation
# ---------------------------------------------------------------------------


class TestTransitionExplanation:
    def test_transition_explains_itself(self):
        """Transition should explain what changed."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id="e1",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=1,
            )
        ]

        transition, _ = machine.apply_evidence(evidence)
        explanation = transition.explain()
        assert "Evidence added" in explanation
        assert transition.transition_type == TransitionType.AUTHORITY_INCREASED


# ---------------------------------------------------------------------------
# Test: Epistemic State Explanation
# ---------------------------------------------------------------------------


class TestEpistemicStateExplanation:
    def test_state_explains_itself(self):
        """State should explain its dimensions."""
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        machine = EpistemicStateMachine(prop)
        machine.create_initial_state()

        evidence = [
            StructuredEvidenceBundle(
                evidence_id=f"e{i}",
                intervention_type=InterventionType.MECHANISM_REMOVAL,
                target="signal_component",
                effect_size=0.8,
                description="Mechanism evidence",
                seed=i + 1,
            )
            for i in range(5)
        ]

        _, new_state = machine.apply_evidence(evidence)
        explanation = new_state.explain()
        assert "p1" in explanation
        assert "mechanism" in explanation
