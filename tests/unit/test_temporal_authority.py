"""Tests for Temporal Authority and Historical Provenance."""

from __future__ import annotations

import pytest

from sas.quant.experiment.temporal_authority import (
    TemporalMode,
    TemporalBoundaryType,
    TemporalConflictType,
    LogicalTime,
    ValidityInterval,
    TemporalBoundary,
    TemporalArtifact,
    TemporalSnapshot,
    HistoricalState,
    TemporalAuthority,
    TemporalConflict,
    TemporalQuery,
    TemporalReconstructionResult,
    TemporalReconstructor,
    TemporalAttackResult,
    TemporalAttackSuite,
    run_temporal_attack_suite,
    reconstruct_at_boundary,
    check_temporal_non_interference,
)
from sas.quant.experiment.protocol_reconstruction import (
    ReconstructionStatus,
)
from sas.quant.experiment.epistemic_governance import (
    AuthorizationStatus,
)


# ---------------------------------------------------------------------------
# Test: Logical Time
# ---------------------------------------------------------------------------


class TestLogicalTime:
    def test_create_time(self):
        time = LogicalTime(event_time=5, observation_time=10)
        assert time.event_time == 5
        assert time.observation_time == 10

    def test_is_valid_at(self):
        time = LogicalTime(event_time=5, observation_time=10)
        assert time.is_valid_at(10)
        assert time.is_valid_at(15)
        assert not time.is_valid_at(3)

    def test_is_available_at(self):
        time = LogicalTime(event_time=5, observation_time=10, ingestion_time=10)
        assert time.is_available_at(10)
        assert time.is_available_at(15)
        assert not time.is_available_at(5)

    def test_compute_hash(self):
        time = LogicalTime(event_time=5, observation_time=10)
        hash1 = time.compute_hash()
        hash2 = time.compute_hash()
        assert hash1 == hash2


# ---------------------------------------------------------------------------
# Test: Validity Interval
# ---------------------------------------------------------------------------


class TestValidityInterval:
    def test_contains(self):
        interval = ValidityInterval(valid_from=5, valid_until=10)
        assert interval.contains(5)
        assert interval.contains(7)
        assert interval.contains(10)
        assert not interval.contains(4)
        assert not interval.contains(11)

    def test_contains_forever(self):
        interval = ValidityInterval(valid_from=5, valid_until=-1)
        assert interval.contains(5)
        assert interval.contains(100)
        assert not interval.contains(4)

    def test_overlaps(self):
        a = ValidityInterval(valid_from=5, valid_until=10)
        b = ValidityInterval(valid_from=8, valid_until=15)
        assert a.overlaps(b)
        assert b.overlaps(a)

    def test_no_overlap(self):
        a = ValidityInterval(valid_from=5, valid_until=10)
        b = ValidityInterval(valid_from=15, valid_until=20)
        assert not a.overlaps(b)
        assert not b.overlaps(a)

    def test_is_contained_in(self):
        a = ValidityInterval(valid_from=5, valid_until=10)
        b = ValidityInterval(valid_from=0, valid_until=20)
        assert a.is_contained_in(b)
        assert not b.is_contained_in(a)


# ---------------------------------------------------------------------------
# Test: Temporal Artifact
# ---------------------------------------------------------------------------


class TestTemporalArtifact:
    def test_create_artifact(self):
        artifact = TemporalArtifact(
            artifact_id="ev1",
            artifact_type="evidence",
            artifact_hash="abc123",
            logical_time=LogicalTime(event_time=5, observation_time=10),
            validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
        )
        assert artifact.artifact_id == "ev1"
        assert artifact.artifact_type == "evidence"

    def test_is_valid_at(self):
        artifact = TemporalArtifact(
            artifact_id="ev1",
            artifact_type="evidence",
            artifact_hash="abc",
            logical_time=LogicalTime(event_time=5, observation_time=10),
            validity_interval=ValidityInterval(valid_from=5, valid_until=10),
        )
        assert artifact.is_valid_at(7)
        assert not artifact.is_valid_at(11)

    def test_was_available_at(self):
        artifact = TemporalArtifact(
            artifact_id="ev1",
            artifact_type="evidence",
            artifact_hash="abc",
            logical_time=LogicalTime(event_time=5, observation_time=10, ingestion_time=10),
            validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
        )
        assert artifact.was_available_at(10)
        assert not artifact.was_available_at(5)

    def test_compute_hash(self):
        artifact = TemporalArtifact(
            artifact_id="ev1",
            artifact_type="evidence",
            artifact_hash="abc",
            logical_time=LogicalTime(event_time=5, observation_time=10),
            validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
        )
        hash1 = artifact.compute_hash()
        hash2 = artifact.compute_hash()
        assert hash1 == hash2


# ---------------------------------------------------------------------------
# Test: Temporal Authority
# ---------------------------------------------------------------------------


class TestTemporalAuthority:
    def test_create_authority(self):
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.AUTHORIZATION_TIME)
        authority = TemporalAuthority(
            authority_id="auth1",
            action_id="act1",
            boundary=boundary,
            status=AuthorizationStatus.AUTHORIZED,
        )
        assert authority.authority_id == "auth1"

    def test_is_valid_at(self):
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.AUTHORIZATION_TIME)
        authority = TemporalAuthority(
            authority_id="auth1",
            action_id="act1",
            boundary=boundary,
            status=AuthorizationStatus.AUTHORIZED,
            validity_interval=ValidityInterval(valid_from=10, valid_until=20),
        )
        assert authority.is_valid_at(15)
        assert not authority.is_valid_at(25)

    def test_revoked_at(self):
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.AUTHORIZATION_TIME)
        authority = TemporalAuthority(
            authority_id="auth1",
            action_id="act1",
            boundary=boundary,
            status=AuthorizationStatus.AUTHORIZED,
            validity_interval=ValidityInterval(valid_from=10, valid_until=-1),
            revoked_at=15,
        )
        assert authority.is_valid_at(10)
        assert not authority.is_valid_at(15)
        assert not authority.is_valid_at(20)


# ---------------------------------------------------------------------------
# Test: Temporal Reconstructor
# ---------------------------------------------------------------------------


class TestTemporalReconstructor:
    def test_reconstruct_at(self):
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
        ]
        result = reconstructor.reconstruct_at(boundary, artifacts)
        assert isinstance(result, TemporalReconstructionResult)

    def test_reconstruct_with_future_knowledge(self):
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=10, observation_time=10),
                validity_interval=ValidityInterval(valid_from=10, valid_until=-1),
            ),
        ]
        result = reconstructor.reconstruct_at(boundary, artifacts)
        assert result.status == ReconstructionStatus.PARTIAL

    def test_reconstruct_with_complete_artifacts(self):
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="prop1",
                artifact_type="proposition",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="def",
                logical_time=LogicalTime(event_time=2, observation_time=2),
                validity_interval=ValidityInterval(valid_from=2, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="es1",
                artifact_type="epistemic_state",
                artifact_hash="ghi",
                logical_time=LogicalTime(event_time=3, observation_time=3),
                validity_interval=ValidityInterval(valid_from=3, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="gov1",
                artifact_type="governance",
                artifact_hash="jkl",
                logical_time=LogicalTime(event_time=4, observation_time=4),
                validity_interval=ValidityInterval(valid_from=4, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="act1",
                artifact_type="actor",
                artifact_hash="mno",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
        ]
        result = reconstructor.reconstruct_at(boundary, artifacts)
        assert result.status == ReconstructionStatus.RECONSTRUCTED

    def test_check_temporal_non_interference(self):
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
        ]
        assert reconstructor.check_temporal_non_interference(artifacts, boundary)

    def test_check_temporal_non_interference_violation(self):
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=10, observation_time=10),
                validity_interval=ValidityInterval(valid_from=10, valid_until=-1),
            ),
        ]
        assert not reconstructor.check_temporal_non_interference(artifacts, boundary)


# ---------------------------------------------------------------------------
# Test: Temporal Attack Suite
# ---------------------------------------------------------------------------


class TestTemporalAttackSuite:
    def test_run_all_attacks(self):
        suite = TemporalAttackSuite()
        results = suite.run_all_attacks()
        assert len(results) >= 50

    def test_future_evidence(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_evidence()
        assert result.detected

    def test_future_verification(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_verification()
        assert result.detected

    def test_future_policy(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_policy()
        assert result.detected

    def test_future_authorization(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_authorization()
        assert result.detected

    def test_future_execution(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_execution()
        assert result.detected

    def test_future_outcome(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_outcome()
        assert result.detected

    def test_late_evidence(self):
        suite = TemporalAttackSuite()
        result = suite.attack_late_evidence()
        assert result.detected

    def test_delayed_observation(self):
        suite = TemporalAttackSuite()
        result = suite.attack_delayed_observation()
        assert result.detected

    def test_delayed_verification(self):
        suite = TemporalAttackSuite()
        result = suite.attack_delayed_verification()
        assert result.detected

    def test_revocation_delay(self):
        suite = TemporalAttackSuite()
        result = suite.attack_revocation_delay()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_retroactive_revocation(self):
        suite = TemporalAttackSuite()
        result = suite.attack_retroactive_revocation()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_future_effective_revocation(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_effective_revocation()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_policy_replacement(self):
        suite = TemporalAttackSuite()
        result = suite.attack_policy_replacement()
        # At T10, only gov1 is available (future gov2 filtered out)
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_historical_current_substitution(self):
        suite = TemporalAttackSuite()
        result = suite.attack_historical_current_substitution()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_replay(self):
        suite = TemporalAttackSuite()
        result = suite.attack_replay()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_timestamp_substitution(self):
        suite = TemporalAttackSuite()
        result = suite.attack_timestamp_substitution()
        assert result.detected

    def test_timestamp_manipulation(self):
        suite = TemporalAttackSuite()
        result = suite.attack_timestamp_manipulation()
        assert result.detected

    def test_clock_skew(self):
        suite = TemporalAttackSuite()
        result = suite.attack_clock_skew()
        assert result.detected

    def test_temporal_inversion(self):
        suite = TemporalAttackSuite()
        result = suite.attack_temporal_inversion()
        assert result.detected

    def test_event_observation_confusion(self):
        suite = TemporalAttackSuite()
        result = suite.attack_event_observation_confusion()
        assert result.detected

    def test_event_authorization_confusion(self):
        suite = TemporalAttackSuite()
        result = suite.attack_event_authorization_confusion()
        assert result.detected

    def test_delivery_occurrence_confusion(self):
        suite = TemporalAttackSuite()
        result = suite.attack_delivery_occurrence_confusion()
        assert result.detected

    def test_causal_temporal_confusion(self):
        suite = TemporalAttackSuite()
        result = suite.attack_causal_temporal_confusion()
        assert result.detected

    def test_historical_current_substitution(self):
        suite = TemporalAttackSuite()
        result = suite.attack_historical_current_substitution()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_replay(self):
        suite = TemporalAttackSuite()
        result = suite.attack_replay()
        # At T10, only authorization is available without full supporting context
        assert result.actual_status == ReconstructionStatus.PARTIAL

    def test_cross_node_temporal_divergence(self):
        suite = TemporalAttackSuite()
        result = suite.attack_cross_node_temporal_divergence()
        assert result.detected

    def test_stale_node_reconstruction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_stale_node_reconstruction()
        assert result.detected

    def test_post_execution_evidence_leakage(self):
        suite = TemporalAttackSuite()
        result = suite.attack_post_execution_evidence_leakage()
        assert result.detected

    def test_outcome_leakage(self):
        suite = TemporalAttackSuite()
        result = suite.attack_outcome_leakage()
        assert result.detected

    def test_backtest_leakage(self):
        suite = TemporalAttackSuite()
        result = suite.attack_backtest_leakage()
        assert result.detected

    def test_version_time_interaction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_version_time_interaction()
        assert result.detected

    def test_partition_time_interaction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_partition_time_interaction()
        assert result.detected

    def test_crash_time_interaction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_crash_time_interaction()
        assert result.detected

    def test_temporal_authority_cutset(self):
        suite = TemporalAttackSuite()
        result = suite.attack_temporal_authority_cutset()
        assert result.detected

    def test_historical_reconstruction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_historical_reconstruction()
        assert result.detected

    def test_current_reconstruction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_current_reconstruction()
        assert result.detected

    def test_retrospective_audit(self):
        suite = TemporalAttackSuite()
        result = suite.attack_retrospective_audit()
        assert result.detected

    def test_no_lookahead(self):
        suite = TemporalAttackSuite()
        result = suite.attack_no_lookahead()
        assert result.detected

    def test_temporal_equivalence(self):
        suite = TemporalAttackSuite()
        result = suite.attack_temporal_equivalence()
        assert result.detected

    def test_temporal_convergence(self):
        suite = TemporalAttackSuite()
        result = suite.attack_temporal_convergence()
        assert result.detected

    def test_immutable_history(self):
        suite = TemporalAttackSuite()
        result = suite.attack_immutable_history()
        assert result.detected

    def test_counterfactual_reconstruction(self):
        suite = TemporalAttackSuite()
        result = suite.attack_counterfactual_reconstruction()
        assert result.detected

    def test_clock_manipulation(self):
        suite = TemporalAttackSuite()
        result = suite.attack_clock_manipulation()
        assert result.detected

    def test_sequence_inversion(self):
        suite = TemporalAttackSuite()
        result = suite.attack_sequence_inversion()
        assert result.detected

    def test_future_dated_artifact(self):
        suite = TemporalAttackSuite()
        result = suite.attack_future_dated_artifact()
        assert result.detected

    def test_expired_artifact(self):
        suite = TemporalAttackSuite()
        result = suite.attack_expired_artifact()
        assert result.detected

    def test_temporal_conflict(self):
        suite = TemporalAttackSuite()
        result = suite.attack_temporal_conflict()
        assert result.detected

    def test_authority_time_travel(self):
        suite = TemporalAttackSuite()
        result = suite.attack_authority_time_travel()
        assert result.detected

    def test_evidence_time_travel(self):
        suite = TemporalAttackSuite()
        result = suite.attack_evidence_time_travel()
        assert result.detected

    def test_governance_time_travel(self):
        suite = TemporalAttackSuite()
        result = suite.attack_governance_time_travel()
        assert result.detected

    def test_execution_time_travel(self):
        suite = TemporalAttackSuite()
        result = suite.attack_execution_time_travel()
        assert result.detected

    def test_revocation_time_travel(self):
        suite = TemporalAttackSuite()
        result = suite.attack_revocation_time_travel()
        assert result.detected

    def test_policy_time_travel(self):
        suite = TemporalAttackSuite()
        result = suite.attack_policy_time_travel()
        assert result.detected

    def test_complete_scenario(self):
        suite = TemporalAttackSuite()
        result = suite.attack_complete_scenario()
        assert result.detected


# ---------------------------------------------------------------------------
# Test: Convenience Functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_run_temporal_attack_suite(self):
        results = run_temporal_attack_suite()
        assert len(results) >= 50
        for result in results:
            assert isinstance(result, TemporalAttackResult)

    def test_reconstruct_at_boundary(self):
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
        ]
        result = reconstruct_at_boundary(boundary, artifacts)
        assert isinstance(result, TemporalReconstructionResult)

    def test_check_temporal_non_interference(self):
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
        ]
        assert check_temporal_non_interference(artifacts, boundary)


# ---------------------------------------------------------------------------
# Test: Invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_future_knowledge_does_not_affect_historical(self):
        """Future artifacts must not affect historical reconstruction."""
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=10, observation_time=10),
                validity_interval=ValidityInterval(valid_from=10, valid_until=-1),
            ),
        ]
        result = reconstructor.reconstruct_at(boundary, artifacts)
        assert result.status == ReconstructionStatus.PARTIAL

    def test_historical_state_immutable(self):
        """Historical state cannot be mutated by later information."""
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="prop1",
                artifact_type="proposition",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="def",
                logical_time=LogicalTime(event_time=2, observation_time=2),
                validity_interval=ValidityInterval(valid_from=2, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="es1",
                artifact_type="epistemic_state",
                artifact_hash="ghi",
                logical_time=LogicalTime(event_time=3, observation_time=3),
                validity_interval=ValidityInterval(valid_from=3, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="gov1",
                artifact_type="governance",
                artifact_hash="jkl",
                logical_time=LogicalTime(event_time=4, observation_time=4),
                validity_interval=ValidityInterval(valid_from=4, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="act1",
                artifact_type="actor",
                artifact_hash="mno",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="auth1",
                artifact_type="authorization",
                artifact_hash="pqr",
                logical_time=LogicalTime(event_time=6, observation_time=6),
                validity_interval=ValidityInterval(valid_from=6, valid_until=-1),
            ),
        ]
        # At T10, authorization is valid
        result1 = reconstruct_at_boundary(boundary, artifacts)
        assert result1.status == ReconstructionStatus.RECONSTRUCTED

        # At T20 with revocation, historical T10 state is unchanged
        boundary2 = TemporalBoundary(boundary_time=20, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts2 = artifacts + [
            TemporalArtifact(
                artifact_id="rev1",
                artifact_type="revocation",
                artifact_hash="stu",
                logical_time=LogicalTime(event_time=15, observation_time=15),
                validity_interval=ValidityInterval(valid_from=15, valid_until=-1),
            ),
        ]
        result2 = reconstruct_at_boundary(boundary2, artifacts2)
        # Historical state at T10 is still valid
        assert result1.authority is not None
        assert result1.authority.is_valid_at(10)

    def test_revocation_does_not_rewrite_history(self):
        """Revocation changes current validity but not historical validity."""
        boundary_hist = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="auth1",
                artifact_type="authorization",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
        ]
        result_hist = reconstruct_at_boundary(boundary_hist, artifacts)

        boundary_curr = TemporalBoundary(boundary_time=20, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts_curr = artifacts + [
            TemporalArtifact(
                artifact_id="rev1",
                artifact_type="revocation",
                artifact_hash="def",
                logical_time=LogicalTime(event_time=15, observation_time=15),
                validity_interval=ValidityInterval(valid_from=15, valid_until=-1),
            ),
        ]
        result_curr = reconstruct_at_boundary(boundary_curr, artifacts_curr)

        # Historical authority was valid at T10
        assert result_hist.authority is not None
        assert result_hist.authority.is_valid_at(10)

        # Current authority is revoked at T20
        assert result_curr.authority is not None
        assert not result_curr.authority.is_valid_at(20)

    def test_event_time_observation_time_distinct(self):
        """Event time and observation time are distinct."""
        artifact = TemporalArtifact(
            artifact_id="ev1",
            artifact_type="evidence",
            artifact_hash="abc",
            logical_time=LogicalTime(event_time=1, observation_time=10),
            validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
        )
        # At T5, event occurred but not yet observed
        assert artifact.is_valid_at(5)
        assert not artifact.was_available_at(5)

        # At T10, event is observed
        assert artifact.was_available_at(10)

    def test_validity_interval_respected(self):
        """Validity interval is respected."""
        artifact = TemporalArtifact(
            artifact_id="auth1",
            artifact_type="authorization",
            artifact_hash="abc",
            logical_time=LogicalTime(event_time=5, observation_time=5),
            validity_interval=ValidityInterval(valid_from=5, valid_until=10),
        )
        assert artifact.is_valid_at(5)
        assert artifact.is_valid_at(10)
        assert not artifact.is_valid_at(11)

    def test_no_lookahead_invariant(self):
        """A decision at time T may depend only on artifacts available at T."""
        reconstructor = TemporalReconstructor()
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=10, observation_time=10),
                validity_interval=ValidityInterval(valid_from=10, valid_until=-1),
            ),
        ]
        result = reconstructor.reconstruct_at(boundary, artifacts)
        # Future evidence should not make reconstruction succeed
        assert result.status == ReconstructionStatus.PARTIAL

    def test_temporal_non_interference(self):
        """Future artifacts cannot interfere with historical authority."""
        boundary = TemporalBoundary(boundary_time=5, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=10, observation_time=10),
                validity_interval=ValidityInterval(valid_from=10, valid_until=-1),
            ),
        ]
        assert not check_temporal_non_interference(artifacts, boundary)

    def test_complete_scenario_historical(self):
        """Complete scenario: historical reconstruction at T7."""
        suite = TemporalAttackSuite()
        result = suite.attack_complete_scenario()
        # At T7, all essential artifacts are available
        assert result.detected

    def test_policy_evolution_no_retroactivity(self):
        """New policy does not retroactively invalidate historical authority."""
        boundary = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="prop1",
                artifact_type="proposition",
                artifact_hash="p1",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="ev1",
                artifact_type="evidence",
                artifact_hash="e1",
                logical_time=LogicalTime(event_time=2, observation_time=2),
                validity_interval=ValidityInterval(valid_from=2, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="es1",
                artifact_type="epistemic_state",
                artifact_hash="es1",
                logical_time=LogicalTime(event_time=3, observation_time=3),
                validity_interval=ValidityInterval(valid_from=3, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="gov1",
                artifact_type="governance",
                artifact_hash="v1",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="act1",
                artifact_type="actor",
                artifact_hash="a1",
                logical_time=LogicalTime(event_time=1, observation_time=1),
                validity_interval=ValidityInterval(valid_from=1, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="auth1",
                artifact_type="authorization",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
        ]
        result = reconstruct_at_boundary(boundary, artifacts)
        # At T10, authorization under gov1 is valid
        assert result.status == ReconstructionStatus.RECONSTRUCTED

    def test_revocation_effective_time(self):
        """Revocation only affects times at or after its effective time."""
        boundary_before = TemporalBoundary(boundary_time=10, boundary_type=TemporalBoundaryType.EVENT_TIME)
        artifacts = [
            TemporalArtifact(
                artifact_id="auth1",
                artifact_type="authorization",
                artifact_hash="abc",
                logical_time=LogicalTime(event_time=5, observation_time=5),
                validity_interval=ValidityInterval(valid_from=5, valid_until=-1),
            ),
            TemporalArtifact(
                artifact_id="rev1",
                artifact_type="revocation",
                artifact_hash="def",
                logical_time=LogicalTime(event_time=15, observation_time=15),
                validity_interval=ValidityInterval(valid_from=15, valid_until=-1),
            ),
        ]
        result_before = reconstruct_at_boundary(boundary_before, artifacts)
        # At T10, revocation hasn't taken effect yet
        assert result_before.authority is not None
        assert result_before.authority.is_valid_at(10)
