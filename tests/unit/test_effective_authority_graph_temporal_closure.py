"""Tests for Phase 33: Effective Authority Graph Closure Under Authority Change."""

import pytest
from research.examples.sovereign_agent.effective_authority_graph_temporal_closure import (
    AdversarialWorldGenerator,
    AuthorityChangeType,
    AuthorityState,
    AuthorityStateTransition,
    Phase33Experiment,
    TemporalClosureEngine,
    TemporalClosureWorld,
    TemporalValidityStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> TemporalClosureEngine:
    return TemporalClosureEngine("test-engine")


@pytest.fixture
def worlds() -> list[TemporalClosureWorld]:
    return AdversarialWorldGenerator().generate_all_worlds()


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------


class TestWorldGeneration:
    def test_generates_45_worlds(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        assert len(worlds) == 45

    def test_worlds_have_unique_ids(self):
        worlds = AdversarialWorldGenerator().generate_all_worlds()
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_world_01_no_authority_change(self, worlds):
        world = worlds[0]
        assert world.world_id == "world_01_no_authority_change"
        assert world.expected_current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT

    def test_world_02_delegation_revoked(self, worlds):
        world = worlds[1]
        assert world.world_id == "world_02_delegation_revoked"
        assert world.expected_current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
        assert world.change_type == AuthorityChangeType.DELEGATION_REVOCATION

    def test_world_09_policy_superseded(self, worlds):
        world = worlds[8]
        assert world.world_id == "world_09_policy_superseded"
        assert world.is_policy_supersession
        assert world.expected_current_validity == TemporalValidityStatus.SUPERSEDED

    def test_world_13_trust_anchor_rotated(self, worlds):
        world = worlds[12]
        assert world.world_id == "world_13_trust_anchor_rotated"
        assert world.is_trust_anchor_rotation
        assert world.expected_current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT

    def test_world_38_delegation_revoked_recreated(self, worlds):
        world = worlds[37]
        assert world.world_id == "world_38_delegation_revoked_recreated"
        assert world.is_identifier_reuse
        assert world.identifier_reuse

    def test_world_42_replay_after_revocation(self, worlds):
        world = worlds[41]
        assert world.world_id == "world_42_replay_after_revocation"
        assert world.is_replay


# ---------------------------------------------------------------------------
# Temporal closure engine tests
# ---------------------------------------------------------------------------


class TestTemporalClosureEngine:
    def test_no_authority_change_preserves_validity(self, engine):
        state = AuthorityState(
            state_id="test", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state,
            authority_state_t2=None,
            transition=None,
            has_transition=False,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
        )
        assert result.historical_validity is True
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
        assert result.revalidation_required is False

    def test_delegation_revoked_invalidates_current(self, engine):
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=(),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )
        assert result.historical_validity is True
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW
        assert result.revalidation_required is True

    def test_historical_validity_preserved(self, engine):
        """Historical validity is never destroyed by authority change."""
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=(),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )
        # Historical validity preserved
        assert result.historical_validity is True

    def test_trust_anchor_rotation_preserves_current_validity(self, engine):
        """Trust anchor rotation should preserve current validity."""
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001",
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-002",
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            is_trust_anchor_rotation=True,
        )
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
        assert result.revalidation_required is False

    def test_policy_supersession_marks_superseded(self, engine):
        """Policy supersession should mark as superseded."""
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", policy_ids=("pol-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", policy_ids=("pol-002",),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.POLICY_SUPERSESSION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.SUPERSEDED,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.POLICY_SUPERSESSION,
            is_policy_supersession=True,
        )
        assert result.current_validity == TemporalValidityStatus.SUPERSEDED
        assert result.revalidation_required is True

    def test_scope_widening_does_not_affect_historical(self, engine):
        """Scope widening should not affect historical validity."""
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", scope="staging",
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", scope="runtime",
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_SCOPE_WIDENING,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_SCOPE_WIDENING,
            is_scope_widening=True,
        )
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT
        assert result.revalidation_required is False

    def test_replay_detected(self, engine):
        """Replay attack should be detected."""
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=(),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            is_replay=True,
        )
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW

    def test_future_authority_cannot_authorize_past(self, engine):
        """Future authority cannot retroactively authorize past effects."""
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=(),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001",),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_RECREATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=False,
            expected_current_validity=TemporalValidityStatus.CURRENTLY_VALID,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_RECREATION,
            is_future_authority=True,
        )
        # Historical invalidity preserved
        assert result.historical_validity is False
        # Current validity independent
        assert result.current_validity == TemporalValidityStatus.CURRENTLY_VALID


# ---------------------------------------------------------------------------
# Phase 33 invariants
# ---------------------------------------------------------------------------


class TestPhase33Invariants:
    def test_historical_reconciliation_is_immutable(self):
        """Historical reconciliation cannot be mutated by authority change."""
        engine = TemporalClosureEngine("test")
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=(),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )
        # Historical validity is preserved (not mutated)
        assert result.historical_validity is True
        # Current validity changed
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW

    def test_future_revocation_cannot_invalidate_historical(self):
        """Future revocation cannot invalidate historically valid effects."""
        engine = TemporalClosureEngine("test")
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=(),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            is_future_revocation=True,
        )
        # Historical validity preserved
        assert result.historical_validity is True

    def test_unrelated_authority_changes_do_not_invalidate_unaffected_paths(self):
        """Unrelated authority changes do not invalidate unaffected paths."""
        engine = TemporalClosureEngine("test")
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001", "del-002"),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", delegation_ids=("del-001", "del-003"),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
            affected_authority_ids=("del-002", "del-003"),
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.DELEGATION_REVOCATION,
        )
        # Historical validity preserved
        assert result.historical_validity is True

    def test_scope_narrowing_affects_future_not_past(self):
        """Scope narrowing affects future execution but not historical validity."""
        engine = TemporalClosureEngine("test")
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", scope="runtime",
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", scope="staging",
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.DELEGATION_SCOPE_NARROWING,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.DELEGATION_SCOPE_NARROWING,
            is_scope_narrowing=True,
        )
        # Historical validity preserved
        assert result.historical_validity is True

    def test_policy_deletion_does_not_erase_historical_evidence(self):
        """Policy deletion does not erase historical evidence."""
        engine = TemporalClosureEngine("test")
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001", policy_ids=("pol-001",),
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-001", policy_ids=(),
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.POLICY_DELETION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_INVALID_NOW,
            expected_revalidation_required=True,
            change_type=AuthorityChangeType.POLICY_DELETION,
            is_policy_deletion=True,
        )
        # Historical validity preserved
        assert result.historical_validity is True

    def test_trust_anchor_rotation_requires_explicit_semantics(self):
        """Trust anchor rotation requires explicit semantics."""
        engine = TemporalClosureEngine("test")
        state_t1 = AuthorityState(
            state_id="test-t1", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001",
        )
        state_t2 = AuthorityState(
            state_id="test-t2", version="t2", timestamp="2026-02-01T00:00:00Z",
            trust_anchor_id="ta-002",
        )
        transition = AuthorityStateTransition(
            transition_id="trans-001",
            change_type=AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            timestamp="2026-02-01T00:00:00Z",
            actor="admin",
            source="test",
            prior_state_ref="test-t1",
            new_state_ref="test-t2",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state_t1,
            authority_state_t2=state_t2,
            transition=transition,
            has_transition=True,
            historical_validity=True,
            expected_current_validity=TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT,
            expected_revalidation_required=False,
            change_type=AuthorityChangeType.TRUST_ANCHOR_ROTATION,
            is_trust_anchor_rotation=True,
        )
        # Rotation preserves validity
        assert result.current_validity == TemporalValidityStatus.VALID_AT_EXECUTION_AND_CURRENT

    def test_reconciliation_does_not_create_authority(self):
        """Reconciliation does not create authority."""
        engine = TemporalClosureEngine("test")
        state = AuthorityState(
            state_id="test", version="t1", timestamp="2026-01-01T00:00:00Z",
            trust_anchor_id="ta-001",
        )
        result = engine.evaluate_temporal_closure(
            authority_state_t1=state,
            authority_state_t2=None,
            transition=None,
            has_transition=False,
            historical_validity=False,
            expected_current_validity=TemporalValidityStatus.CURRENTLY_INVALID,
            expected_revalidation_required=False,
        )
        # Reconciliation doesn't make invalid valid
        assert result.historical_validity is False
        assert result.current_validity == TemporalValidityStatus.CURRENTLY_INVALID


# ---------------------------------------------------------------------------
# Full experiment test
# ---------------------------------------------------------------------------


class TestPhase33Experiment:
    def test_runs_all_worlds(self):
        exp = Phase33Experiment()
        results = exp.run_all()
        assert results["total_worlds"] == 45

    def test_summary_generated(self):
        exp = Phase33Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_worlds"] == 45
        assert summary["total_temporal_reconciliations"] == 45

    def test_validity_matches_count(self):
        exp = Phase33Experiment()
        exp.run_all()
        summary = exp.summary()
        # All validity predictions should match
        assert summary["validity_accuracy"] == 1.0
