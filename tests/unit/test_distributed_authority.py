"""Tests for Distributed Authority Convergence."""

from __future__ import annotations

import pytest

from sas.quant.experiment.distributed_authority import (
    ArtifactAvailability,
    ConvergenceStatus,
    ReconciliationStatus,
    PartitionState,
    DeliveryEvent,
    ArtifactReplica,
    ArtifactManifest,
    ProvenanceFragment,
    CausalDependency,
    AuthorityObservation,
    DistributedView,
    AuthorityView,
    ViewReconciliation,
    ProtocolNode,
    DistributedReconstructor,
    DistributedAttackResult,
    DistributedAttackSuite,
    run_distributed_attack_suite,
    reconstruct_from_view,
    reconcile_views,
    check_convergence,
)
from sas.quant.experiment.protocol_reconstruction import (
    ReconstructionStatus,
)


# ---------------------------------------------------------------------------
# Test: Artifact Availability
# ---------------------------------------------------------------------------


class TestArtifactAvailability:
    def test_all_statuses_present(self):
        statuses = list(ArtifactAvailability)
        assert len(statuses) == 9
        assert ArtifactAvailability.UNKNOWN in statuses
        assert ArtifactAvailability.MISSING in statuses
        assert ArtifactAvailability.AVAILABLE in statuses
        assert ArtifactAvailability.VERIFIED in statuses
        assert ArtifactAvailability.REVOKED in statuses
        assert ArtifactAvailability.SUPERSEDED in statuses


# ---------------------------------------------------------------------------
# Test: Convergence Status
# ---------------------------------------------------------------------------


class TestConvergenceStatus:
    def test_all_statuses_present(self):
        statuses = list(ConvergenceStatus)
        assert len(statuses) == 7
        assert ConvergenceStatus.CONVERGED in statuses
        assert ConvergenceStatus.NON_CONVERGENT in statuses
        assert ConvergenceStatus.PARTIALLY_CONVERGED in statuses
        assert ConvergenceStatus.CONFLICTING in statuses
        assert ConvergenceStatus.INSUFFICIENT_KNOWLEDGE in statuses
        assert ConvergenceStatus.VERSION_MISMATCH in statuses


# ---------------------------------------------------------------------------
# Test: Artifact Replica
# ---------------------------------------------------------------------------


class TestArtifactReplica:
    def test_create_replica(self):
        replica = ArtifactReplica(
            replica_id="r1",
            artifact_type="evidence",
            artifact_hash="abc123",
            availability=ArtifactAvailability.AVAILABLE,
        )
        assert replica.artifact_type == "evidence"
        assert replica.availability == ArtifactAvailability.AVAILABLE

    def test_replica_is_frozen(self):
        replica = ArtifactReplica(
            replica_id="r1",
            artifact_type="evidence",
            artifact_hash="abc123",
            availability=ArtifactAvailability.AVAILABLE,
        )
        with pytest.raises(AttributeError):
            replica.artifact_type = "modified"


# ---------------------------------------------------------------------------
# Test: Artifact Manifest
# ---------------------------------------------------------------------------


class TestArtifactManifest:
    def test_has_artifact(self):
        manifest = ArtifactManifest(
            manifest_id="m1",
            artifacts={
                "evidence": ArtifactReplica(
                    replica_id="r1",
                    artifact_type="evidence",
                    artifact_hash="abc",
                    availability=ArtifactAvailability.AVAILABLE,
                ),
            },
        )
        assert manifest.has_artifact("evidence")
        assert not manifest.has_artifact("proposition")

    def test_get_availability(self):
        manifest = ArtifactManifest(
            manifest_id="m1",
            artifacts={
                "evidence": ArtifactReplica(
                    replica_id="r1",
                    artifact_type="evidence",
                    artifact_hash="abc",
                    availability=ArtifactAvailability.AVAILABLE,
                ),
            },
        )
        assert manifest.get_availability("evidence") == ArtifactAvailability.AVAILABLE
        assert manifest.get_availability("proposition") == ArtifactAvailability.UNKNOWN

    def test_compute_hash(self):
        manifest = ArtifactManifest(manifest_id="m1")
        hash1 = manifest.compute_hash()
        hash2 = manifest.compute_hash()
        assert hash1 == hash2


# ---------------------------------------------------------------------------
# Test: Distributed View
# ---------------------------------------------------------------------------


class TestDistributedView:
    def test_create_view(self):
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
        )
        assert view.view_id == "v1"
        assert view.node_id == "A"

    def test_has_artifact(self):
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(
                manifest_id="m1",
                artifacts={
                    "evidence": ArtifactReplica(
                        replica_id="r1",
                        artifact_type="evidence",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        assert view.has_artifact("evidence")
        assert not view.has_artifact("proposition")

    def test_partition_state(self):
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
            partition_state=PartitionState.PARTITIONED,
        )
        assert view.partition_state == PartitionState.PARTITIONED


# ---------------------------------------------------------------------------
# Test: Protocol Node
# ---------------------------------------------------------------------------


class TestProtocolNode:
    def test_create_node(self):
        node = ProtocolNode(node_id="A")
        assert node.node_id == "A"
        assert node.protocol_version == "1.0.0"

    def test_receive_artifact(self):
        node = ProtocolNode(node_id="A")
        event = DeliveryEvent(
            event_id="e1",
            artifact_type="evidence",
            artifact_hash="abc",
            source_node="B",
            target_node="A",
            timestamp=1,
        )
        replica = ArtifactReplica(
            replica_id="r1",
            artifact_type="evidence",
            artifact_hash="abc",
            availability=ArtifactAvailability.AVAILABLE,
        )
        node.receive_artifact(event, replica)
        assert node.manifest.has_artifact("evidence")
        assert len(node.received_events) == 1

    def test_get_view(self):
        node = ProtocolNode(node_id="A")
        view = node.get_view()
        assert isinstance(view, DistributedView)
        assert view.node_id == "A"


# ---------------------------------------------------------------------------
# Test: Distributed Reconstructor
# ---------------------------------------------------------------------------


class TestDistributedReconstructor:
    def test_reconstruct_from_view(self):
        reconstructor = DistributedReconstructor()
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(
                manifest_id="m1",
                artifacts={
                    "proposition": ArtifactReplica(
                        replica_id="r1",
                        artifact_type="proposition",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "evidence": ArtifactReplica(
                        replica_id="r2",
                        artifact_type="evidence",
                        artifact_hash="def",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "epistemic_state": ArtifactReplica(
                        replica_id="r3",
                        artifact_type="epistemic_state",
                        artifact_hash="ghi",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "governance": ArtifactReplica(
                        replica_id="r4",
                        artifact_type="governance",
                        artifact_hash="jkl",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "actor": ArtifactReplica(
                        replica_id="r5",
                        artifact_type="actor",
                        artifact_hash="mno",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        result = reconstructor.reconstruct_from_view(view)
        assert result.status.value in ("reconstructed", "partial")

    def test_reconstruct_version_mismatch(self):
        reconstructor = DistributedReconstructor(protocol_version="2.0.0")
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
            protocol_version="1.0.0",
        )
        result = reconstructor.reconstruct_from_view(view)
        assert result.status == ReconstructionStatus.VERSION_MISMATCH

    def test_reconstruct_partitioned(self):
        reconstructor = DistributedReconstructor()
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
            partition_state=PartitionState.PARTITIONED,
        )
        result = reconstructor.reconstruct_from_view(view)
        assert result.status == ReconstructionStatus.PARTIAL

    def test_reconcile_views(self):
        reconstructor = DistributedReconstructor()
        view_a = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(
                manifest_id="m1",
                artifacts={
                    "evidence": ArtifactReplica(
                        replica_id="r1",
                        artifact_type="evidence",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        view_b = DistributedView(
            view_id="v2",
            node_id="B",
            manifest=ArtifactManifest(
                manifest_id="m2",
                artifacts={
                    "evidence": ArtifactReplica(
                        replica_id="r2",
                        artifact_type="evidence",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        result = reconstructor.reconcile_views(view_a, view_b)
        assert isinstance(result, ViewReconciliation)

    def test_check_convergence(self):
        reconstructor = DistributedReconstructor()
        view_a = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(
                manifest_id="m1",
                artifacts={
                    "proposition": ArtifactReplica(
                        replica_id="r1",
                        artifact_type="proposition",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "evidence": ArtifactReplica(
                        replica_id="r2",
                        artifact_type="evidence",
                        artifact_hash="def",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "epistemic_state": ArtifactReplica(
                        replica_id="r3",
                        artifact_type="epistemic_state",
                        artifact_hash="ghi",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "governance": ArtifactReplica(
                        replica_id="r4",
                        artifact_type="governance",
                        artifact_hash="jkl",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "actor": ArtifactReplica(
                        replica_id="r5",
                        artifact_type="actor",
                        artifact_hash="mno",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        view_b = DistributedView(
            view_id="v2",
            node_id="B",
            manifest=ArtifactManifest(
                manifest_id="m2",
                artifacts={
                    "proposition": ArtifactReplica(
                        replica_id="r1",
                        artifact_type="proposition",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "evidence": ArtifactReplica(
                        replica_id="r2",
                        artifact_type="evidence",
                        artifact_hash="def",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "epistemic_state": ArtifactReplica(
                        replica_id="r3",
                        artifact_type="epistemic_state",
                        artifact_hash="ghi",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "governance": ArtifactReplica(
                        replica_id="r4",
                        artifact_type="governance",
                        artifact_hash="jkl",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                    "actor": ArtifactReplica(
                        replica_id="r5",
                        artifact_type="actor",
                        artifact_hash="mno",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        result = reconstructor.check_convergence([view_a, view_b])
        assert result == ConvergenceStatus.CONVERGED


# ---------------------------------------------------------------------------
# Test: Distributed Attack Suite
# ---------------------------------------------------------------------------


class TestDistributedAttackSuite:
    def test_run_all_attacks(self):
        suite = DistributedAttackSuite()
        results = suite.run_all_attacks()
        assert len(results) >= 50

    def test_partial_knowledge_proposition(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partial_knowledge_proposition()
        assert result.detected

    def test_partial_knowledge_evidence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partial_knowledge_evidence()
        assert result.detected

    def test_partial_knowledge_governance(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partial_knowledge_governance()
        assert result.detected

    def test_partial_knowledge_actor(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partial_knowledge_actor()
        assert result.detected

    def test_omit_proposition(self):
        suite = DistributedAttackSuite()
        result = suite.attack_omit_proposition()
        assert result.detected

    def test_omit_evidence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_omit_evidence()
        assert result.detected

    def test_omit_governance(self):
        suite = DistributedAttackSuite()
        result = suite.attack_omit_governance()
        assert result.detected

    def test_substitute_evidence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_substitute_evidence()
        assert result.detected

    def test_substitute_policy(self):
        suite = DistributedAttackSuite()
        result = suite.attack_substitute_policy()
        assert result.detected

    def test_substitute_actor(self):
        suite = DistributedAttackSuite()
        result = suite.attack_substitute_actor()
        assert result.detected

    def test_duplicate_evidence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_duplicate_evidence()
        assert result.detected

    def test_reorder_delivery(self):
        suite = DistributedAttackSuite()
        result = suite.attack_reorder_delivery()
        assert result.detected

    def test_delayed_evidence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_delayed_evidence()
        assert result.detected

    def test_delayed_revocation(self):
        suite = DistributedAttackSuite()
        result = suite.attack_delayed_revocation()
        assert result.detected

    def test_replay_authorization(self):
        suite = DistributedAttackSuite()
        result = suite.attack_replay_authorization()
        assert result.detected

    def test_revocation_delay(self):
        suite = DistributedAttackSuite()
        result = suite.attack_revocation_delay()
        assert result.detected

    def test_temporal_inversion(self):
        suite = DistributedAttackSuite()
        result = suite.attack_temporal_inversion()
        assert result.detected

    def test_policy_conflict(self):
        suite = DistributedAttackSuite()
        result = suite.attack_policy_conflict()
        assert result.detected

    def test_verification_conflict(self):
        suite = DistributedAttackSuite()
        result = suite.attack_verification_conflict()
        assert result.detected

    def test_governance_conflict(self):
        suite = DistributedAttackSuite()
        result = suite.attack_governance_conflict()
        assert result.detected

    def test_identity_substitution(self):
        suite = DistributedAttackSuite()
        result = suite.attack_identity_substitution()
        assert result.detected

    def test_delegation_substitution(self):
        suite = DistributedAttackSuite()
        result = suite.attack_delegation_substitution()
        assert result.detected

    def test_cross_domain_artifact(self):
        suite = DistributedAttackSuite()
        result = suite.attack_cross_domain_artifact()
        assert result.detected

    def test_byzantine_forged_evidence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_byzantine_forged_evidence()
        assert result.detected

    def test_byzantine_stale_artifact(self):
        suite = DistributedAttackSuite()
        result = suite.attack_byzantine_stale_artifact()
        assert result.detected

    def test_sybil_identity(self):
        suite = DistributedAttackSuite()
        result = suite.attack_sybil_identity()
        assert result.detected

    def test_provenance_fragmentation(self):
        suite = DistributedAttackSuite()
        result = suite.attack_provenance_fragmentation()
        assert result.detected

    def test_version_divergence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_version_divergence()
        assert result.detected

    def test_partition(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partition()
        assert result.detected

    def test_partition_healing(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partition_healing()
        assert result.detected

    def test_crash_recovery(self):
        suite = DistributedAttackSuite()
        result = suite.attack_crash_recovery()
        assert result.detected

    def test_historical_current_confusion(self):
        suite = DistributedAttackSuite()
        result = suite.attack_historical_current_confusion()
        assert result.detected

    def test_stale_authority(self):
        suite = DistributedAttackSuite()
        result = suite.attack_stale_authority()
        assert result.detected

    def test_conflicting_roots(self):
        suite = DistributedAttackSuite()
        result = suite.attack_conflicting_roots()
        assert result.detected

    def test_dependency_omission(self):
        suite = DistributedAttackSuite()
        result = suite.attack_dependency_omission()
        assert result.detected

    def test_resource_contention(self):
        suite = DistributedAttackSuite()
        result = suite.attack_resource_contention()
        assert result.detected

    def test_authority_cutset(self):
        suite = DistributedAttackSuite()
        result = suite.attack_authority_cutset()
        assert result.detected

    def test_monotonic_knowledge(self):
        suite = DistributedAttackSuite()
        result = suite.attack_monotonic_knowledge()
        assert result.detected

    def test_non_monotonic_revocation(self):
        suite = DistributedAttackSuite()
        result = suite.attack_non_monotonic_revocation()
        assert result.detected

    def test_non_monotonic_supersession(self):
        suite = DistributedAttackSuite()
        result = suite.attack_non_monotonic_supersession()
        assert result.detected

    def test_async_evidence_before_proposition(self):
        suite = DistributedAttackSuite()
        result = suite.attack_async_evidence_before_proposition()
        assert result.detected

    def test_async_revocation_before_authorization(self):
        suite = DistributedAttackSuite()
        result = suite.attack_async_revocation_before_authorization()
        assert result.detected

    def test_deterministic_convergence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_deterministic_convergence()
        assert result.detected

    def test_authority_availability_vs_existence(self):
        suite = DistributedAttackSuite()
        result = suite.attack_authority_availability_vs_existence()
        assert result.detected

    def test_forged_provenance(self):
        suite = DistributedAttackSuite()
        result = suite.attack_forged_provenance()
        assert result.detected

    def test_manipulated_timestamp(self):
        suite = DistributedAttackSuite()
        result = suite.attack_manipulated_timestamp()
        assert result.detected

    def test_identity_multiplicity(self):
        suite = DistributedAttackSuite()
        result = suite.attack_identity_multiplicity()
        assert result.detected

    def test_version_downgrade(self):
        suite = DistributedAttackSuite()
        result = suite.attack_version_downgrade()
        assert result.detected

    def test_replay_across_nodes(self):
        suite = DistributedAttackSuite()
        result = suite.attack_replay_across_nodes()
        assert result.detected

    def test_distributed_crash(self):
        suite = DistributedAttackSuite()
        result = suite.attack_distributed_crash()
        assert result.detected

    def test_agreement_does_not_create_authority(self):
        suite = DistributedAttackSuite()
        result = suite.attack_agreement_does_not_create_authority()
        assert result.detected

    def test_partial_knowledge_bounded_uncertainty(self):
        suite = DistributedAttackSuite()
        result = suite.attack_partial_knowledge_bounded_uncertainty()
        assert result.detected

    def test_incomplete_provenance_no_consensus(self):
        suite = DistributedAttackSuite()
        result = suite.attack_incomplete_provenance_no_consensus()
        # Different nodes have different artifacts with no conflicts = partially converged
        assert result.actual_convergence == ConvergenceStatus.PARTIALLY_CONVERGED


# ---------------------------------------------------------------------------
# Test: Convenience Functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_run_distributed_attack_suite(self):
        results = run_distributed_attack_suite()
        assert len(results) >= 50
        for result in results:
            assert isinstance(result, DistributedAttackResult)

    def test_reconstruct_from_view(self):
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
        )
        result = reconstruct_from_view(view)
        assert result.status.value in ("reconstructed", "partial")

    def test_reconcile_views(self):
        view_a = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
        )
        view_b = DistributedView(
            view_id="v2",
            node_id="B",
            manifest=ArtifactManifest(manifest_id="m2"),
        )
        result = reconcile_views(view_a, view_b)
        assert isinstance(result, ViewReconciliation)

    def test_check_convergence(self):
        view_a = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(manifest_id="m1"),
        )
        view_b = DistributedView(
            view_id="v2",
            node_id="B",
            manifest=ArtifactManifest(manifest_id="m2"),
        )
        result = check_convergence([view_a, view_b])
        assert isinstance(result, ConvergenceStatus)


# ---------------------------------------------------------------------------
# Test: Invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_partial_knowledge_does_not_imply_absence(self):
        """A node that lacks an artifact must not conclude it doesn't exist."""
        reconstructor = DistributedReconstructor()
        view = DistributedView(
            view_id="v1",
            node_id="A",
            manifest=ArtifactManifest(
                manifest_id="m1",
                artifacts={
                    "proposition": ArtifactReplica(
                        replica_id="r1",
                        artifact_type="proposition",
                        artifact_hash="abc",
                        availability=ArtifactAvailability.AVAILABLE,
                    ),
                },
            ),
        )
        result = reconstructor.reconstruct_from_view(view)
        # Should be partial, not "evidence doesn't exist"
        assert result.status == ReconstructionStatus.PARTIAL

    def test_agreement_does_not_create_authority(self):
        """Multiple nodes agreeing doesn't create authority."""
        suite = DistributedAttackSuite()
        result = suite.attack_agreement_does_not_create_authority()
        # Even with 3 nodes agreeing, without evidence, authority is not established
        assert result.actual_convergence == ConvergenceStatus.INSUFFICIENT_KNOWLEDGE

    def test_version_mismatch_prevents_convergence(self):
        """Different protocol versions prevent convergence."""
        suite = DistributedAttackSuite()
        result = suite.attack_version_divergence()
        assert result.actual_convergence == ConvergenceStatus.VERSION_MISMATCH

    def test_byzantine_node_detected(self):
        """Byzantine nodes providing forged artifacts are detected."""
        suite = DistributedAttackSuite()
        result = suite.attack_byzantine_forged_evidence()
        assert result.actual_convergence == ConvergenceStatus.NON_CONVERGENT

    def test_partition_prevents_full_convergence(self):
        """Network partition prevents full convergence."""
        suite = DistributedAttackSuite()
        result = suite.attack_partition()
        assert result.actual_convergence == ConvergenceStatus.PARTIALLY_CONVERGED

    def test_revocation_invalidates_authorization(self):
        """Revocation invalidates previously valid authorization."""
        suite = DistributedAttackSuite()
        result = suite.attack_non_monotonic_revocation()
        # After revocation, authority should not be AUTHORIZED
        assert result.detected

    def test_provenance_fragmentation_partial(self):
        """Fragmented provenance results in partial convergence."""
        suite = DistributedAttackSuite()
        result = suite.attack_provenance_fragmentation()
        assert result.actual_convergence == ConvergenceStatus.PARTIALLY_CONVERGED

    def test_duplicate_evidence_idempotent(self):
        """Duplicate evidence doesn't change convergence."""
        suite = DistributedAttackSuite()
        result = suite.attack_duplicate_evidence()
        assert result.actual_convergence == ConvergenceStatus.CONVERGED

    def test_reorder_robust(self):
        """Delivery order doesn't affect final convergence."""
        suite = DistributedAttackSuite()
        result = suite.attack_reorder_delivery()
        assert result.actual_convergence == ConvergenceStatus.CONVERGED

    def test_sybil_identity_not_independent(self):
        """Sybil identities don't create independent authority."""
        suite = DistributedAttackSuite()
        result = suite.attack_sybil_identity()
        # Multiple nodes with same artifacts = converged, not independent
        assert result.actual_convergence == ConvergenceStatus.CONVERGED
