"""Phase 23 tests: Epistemic State Consequentiality.

Tests verify that epistemic state transitions themselves are part of
the consequential authority surface.
"""

import pytest
from examples.sovereign_agent.epistemic_state_consequentiality import (
    EpistemicStateMachine,
    EpistemicStateConsequentialityEngine,
    EpistemicTransitionConsequence,
    EpistemicTransitionType,
    classify_epistemic_transition,
    run_all_phase23_experiments,
    run_unknown_to_complete,
    run_complete_to_incomplete,
    run_complete_to_unknown,
    run_unknown_to_incomplete,
    run_was_complete_to_incomplete,
    run_complete_to_complete,
    run_epistemic_creates_authority,
    run_epistemic_constrains_authority,
    run_temporal_epistemic,
    run_epistemic_governance,
)


class TestUnknownToComplete:
    """UNKNOWN → COMPLETE: Creates authority."""

    def test_creates_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_unknown_to_complete(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CREATES_AUTHORITY


class TestCompleteToIncomplete:
    """COMPLETE → INCOMPLETE: Constrains authority."""

    def test_constrains_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_complete_to_incomplete(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY


class TestCompleteToUnknown:
    """COMPLETE → UNKNOWN: Constrains authority."""

    def test_constrains_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_complete_to_unknown(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY


class TestUnknownToIncomplete:
    """UNKNOWN → INCOMPLETE: Constrains authority."""

    def test_constrains_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_unknown_to_incomplete(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY


class TestWasCompleteToIncomplete:
    """WAS_COMPLETE_AT_T → INCOMPLETE: Historical revision."""

    def test_constrains_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_was_complete_to_incomplete(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY


class TestCompleteToComplete:
    """COMPLETE → COMPLETE: No change."""

    def test_no_effect(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_complete_to_complete(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.NO_AUTHORITY_EFFECT


class TestEpistemicCreatesAuthority:
    """Epistemic transition creates authority."""

    def test_creates_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_epistemic_creates_authority(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CREATES_AUTHORITY


class TestEpistemicConstrainsAuthority:
    """Epistemic transition constrains authority."""

    def test_constrains_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_epistemic_constrains_authority(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY


class TestTemporalEpistemic:
    """Temporal epistemic transition."""

    def test_constrains_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_temporal_epistemic(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY


class TestEpistemicGovernance:
    """Epistemic state machine governance."""

    def test_creates_authority(self):
        engine = EpistemicStateConsequentialityEngine()
        result = run_epistemic_governance(engine)
        assert result.transition.classification == EpistemicTransitionConsequence.CREATES_AUTHORITY


class TestAllPhase23Experiments:
    """Test all Phase 23 experiments."""

    def test_all_experiments_run(self):
        results = run_all_phase23_experiments()
        assert results["total_experiments"] == 10

    def test_creates_authority(self):
        results = run_all_phase23_experiments()
        assert results["creates_authority_count"] >= 2

    def test_constrains_authority(self):
        results = run_all_phase23_experiments()
        assert results["constrains_authority_count"] >= 4

    def test_no_effect(self):
        results = run_all_phase23_experiments()
        assert results["no_effect_count"] >= 1


class TestEpistemicStateMachine:
    """Test epistemic state machine."""

    def test_set_state(self):
        machine = EpistemicStateMachine()
        transition = machine.set_state("entity_001", "complete", "observer", "authority")
        assert transition.from_state == "unknown"
        assert transition.to_state == "complete"
        assert transition.transition_type == EpistemicTransitionType.GAIN_KNOWLEDGE

    def test_no_change(self):
        machine = EpistemicStateMachine()
        machine.set_state("entity_001", "complete", "observer", "authority")
        transition = machine.set_state("entity_001", "complete", "observer", "authority")
        assert transition.transition_type == EpistemicTransitionType.NO_CHANGE

    def test_lose_knowledge(self):
        machine = EpistemicStateMachine()
        machine.set_state("entity_001", "complete", "observer", "authority")
        transition = machine.set_state("entity_001", "incomplete", "observer", "authority")
        assert transition.transition_type == EpistemicTransitionType.LOSE_KNOWLEDGE


class TestEpistemicTransitionClassifier:
    """Test epistemic transition classifier."""

    def test_gain_knowledge(self):
        from examples.sovereign_agent.epistemic_state_consequentiality import EpistemicStateTransition
        transition = EpistemicStateTransition(
            transition_id="test",
            from_state="unknown",
            to_state="complete",
            transition_type=EpistemicTransitionType.GAIN_KNOWLEDGE,
            actor="observer",
            authority_basis="authority",
        )
        assert classify_epistemic_transition(transition) == EpistemicTransitionConsequence.CREATES_AUTHORITY

    def test_lose_knowledge(self):
        from examples.sovereign_agent.epistemic_state_consequentiality import EpistemicStateTransition
        transition = EpistemicStateTransition(
            transition_id="test",
            from_state="complete",
            to_state="incomplete",
            transition_type=EpistemicTransitionType.LOSE_KNOWLEDGE,
            actor="observer",
            authority_basis="authority",
        )
        assert classify_epistemic_transition(transition) == EpistemicTransitionConsequence.CONSTRAINS_AUTHORITY

    def test_no_change(self):
        from examples.sovereign_agent.epistemic_state_consequentiality import EpistemicStateTransition
        transition = EpistemicStateTransition(
            transition_id="test",
            from_state="complete",
            to_state="complete",
            transition_type=EpistemicTransitionType.NO_CHANGE,
            actor="observer",
            authority_basis="authority",
        )
        assert classify_epistemic_transition(transition) == EpistemicTransitionConsequence.NO_AUTHORITY_EFFECT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
