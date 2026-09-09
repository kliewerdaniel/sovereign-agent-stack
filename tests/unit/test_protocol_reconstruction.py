"""Tests for Protocol Reconstruction."""

from __future__ import annotations

import pytest

from sas.quant.experiment.protocol_reconstruction import (
    ReconstructionStatus,
    EquivalenceType,
    ArtifactRole,
    ArtifactSufficiency,
    ArtifactInventoryItem,
    ProtocolArtifactStore,
    ReconstructedProtocolState,
    ProtocolReconstructor,
    ReconstructionAttackResult,
    ReconstructionAttackSuite,
    run_reconstruction_attack_suite,
    reconstruct_protocol,
    compare_reconstruction,
)
from sas.quant.experiment.epistemic_state import (
    EpistemicStatus,
    StateDimension,
    DimensionStatus,
    EpistemicState,
    EpistemicStateMachine,
)
from sas.quant.experiment.evidence_structure import (
    StructuredEvidenceBundle,
)
from sas.quant.experiment.typed_propositions import (
    InterventionType,
    PropositionType,
    TypedProposition,
)
from sas.quant.experiment.epistemic_governance import (
    AuthorizationStatus,
    ActionProposal,
    GovernancePolicy,
    AuthorizationArtifact,
    ActorIdentity,
    RevocationArtifact,
    create_action_proposal,
    create_governance_policy,
    create_actor_identity,
)
from sas.quant.experiment.epistemic_consensus import (
    EpistemicConsensus,
)


# ---------------------------------------------------------------------------
# Test: Reconstruction Status
# ---------------------------------------------------------------------------


class TestReconstructionStatus:
    def test_all_statuses_present(self):
        statuses = list(ReconstructionStatus)
        assert len(statuses) == 8
        assert ReconstructionStatus.RECONSTRUCTED in statuses
        assert ReconstructionStatus.PARTIAL in statuses
        assert ReconstructionStatus.FAILED in statuses


# ---------------------------------------------------------------------------
# Test: Equivalence Types
# ---------------------------------------------------------------------------


class TestEquivalenceTypes:
    def test_all_types_present(self):
        types = list(EquivalenceType)
        assert len(types) == 10
        assert EquivalenceType.SEMANTICALLY_EQUIVALENT in types
        assert EquivalenceType.BYTE_IDENTICAL in types
        assert EquivalenceType.DISPOSITION_MISMATCH in types


# ---------------------------------------------------------------------------
# Test: Protocol Artifact Store
# ---------------------------------------------------------------------------


class TestProtocolArtifactStore:
    def test_compute_hash(self):
        store = ProtocolArtifactStore(store_id="s1")
        hash1 = store.compute_hash()
        hash2 = store.compute_hash()
        assert hash1 == hash2

    def test_store_with_artifacts(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        store = ProtocolArtifactStore(
            store_id="s1",
            proposition=proposition,
        )
        assert store.proposition == proposition


# ---------------------------------------------------------------------------
# Test: Protocol Reconstructor
# ---------------------------------------------------------------------------


class TestProtocolReconstructor:
    def test_reconstruct_valid_store(self):
        reconstructor = ProtocolReconstructor()
        store = self._create_valid_store()
        result = reconstructor.reconstruct(store)
        assert isinstance(result, ReconstructedProtocolState)

    def test_reconstruct_missing_artifacts(self):
        reconstructor = ProtocolReconstructor()
        store = ProtocolArtifactStore(store_id="empty")
        result = reconstructor.reconstruct(store)
        assert result.status == ReconstructionStatus.PARTIAL
        assert len(result.missing_artifacts) > 0

    def test_reconstruct_version_mismatch(self):
        reconstructor = ProtocolReconstructor(protocol_version="2.0.0")
        store = self._create_valid_store()
        result = reconstructor.reconstruct(store)
        assert result.status == ReconstructionStatus.VERSION_MISMATCH

    def test_compare_with_historical(self):
        reconstructor = ProtocolReconstructor()
        store = self._create_valid_store()
        result = reconstructor.reconstruct(store)
        equivalence = reconstructor.compare_with_historical(result, store)
        assert isinstance(equivalence, EquivalenceType)

    def _create_valid_store(self) -> ProtocolArtifactStore:
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
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
        machine = EpistemicStateMachine(proposition)
        state = machine.create_initial_state()
        _, state = machine.apply_evidence(evidence)

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_epistemic_dimensions={"mechanism": "identified"},
            required_identity_conditions=["trader"],
        )
        actor = ActorIdentity(actor_id="actor1", capabilities=["trader"])
        action = ActionProposal(action_id="a1", proposer_id="agent1", action_type="TRADE", target="AAPL")

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            identity_ref="actor1",
        )

        return ProtocolArtifactStore(
            store_id="valid_store",
            protocol_version="1.0.0",
            proposition=proposition,
            evidence_bundles=evidence,
            epistemic_state=state,
            governance_policies=[policy],
            action_proposal=action,
            actor_identity=actor,
            authorization=auth,
        )


# ---------------------------------------------------------------------------
# Test: Reconstruction Attack Suite
# ---------------------------------------------------------------------------


class TestReconstructionAttackSuite:
    def test_run_all_attacks(self):
        suite = ReconstructionAttackSuite()
        results = suite.run_all_attacks()
        assert len(results) > 0

    def test_omit_proposition(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_omit_proposition()
        assert result.detected

    def test_omit_evidence(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_omit_evidence()
        assert result.detected

    def test_omit_epistemic_state(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_omit_epistemic_state()
        assert result.detected

    def test_omit_governance(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_omit_governance()
        assert result.detected

    def test_omit_actor(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_omit_actor()
        assert result.detected

    def test_substitute_evidence(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_substitute_evidence()
        assert result.detected

    def test_substitute_policy(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_substitute_policy()
        assert result.detected

    def test_substitute_actor(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_substitute_actor()
        assert result.detected

    def test_version_downgrade(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_version_downgrade()
        assert result.detected

    def test_version_mismatch(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_version_mismatch()
        assert result.detected

    def test_duplicate_evidence(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_duplicate_evidence()
        assert result.detected

    def test_reorder_evidence(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_reorder_evidence()
        assert result.detected

    def test_revocation_replay(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_revocation_replay()
        assert result.detected

    def test_crash_recovery(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_crash_recovery()
        assert result.detected

    def test_partial_execution(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_partial_execution()
        assert result.detected

    def test_forged_provenance(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_forged_provenance()
        assert result.detected

    def test_forged_historical_state(self):
        suite = ReconstructionAttackSuite()
        result = suite.attack_forged_historical_state()
        assert result.detected


# ---------------------------------------------------------------------------
# Test: Convenience Functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_run_reconstruction_attack_suite(self):
        results = run_reconstruction_attack_suite()
        assert len(results) > 0
        for result in results:
            assert isinstance(result, ReconstructionAttackResult)

    def test_reconstruct_protocol(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        store = ProtocolArtifactStore(
            store_id="s1",
            proposition=proposition,
        )
        result = reconstruct_protocol(store)
        assert isinstance(result, ReconstructedProtocolState)

    def test_compare_reconstruction(self):
        proposition = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        store = ProtocolArtifactStore(
            store_id="s1",
            proposition=proposition,
        )
        result = reconstruct_protocol(store)
        equivalence = compare_reconstruction(result, store)
        assert isinstance(equivalence, EquivalenceType)


# ---------------------------------------------------------------------------
# Test: Invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_artifact_sufficiency_essential(self):
        """Essential artifacts cannot be omitted."""
        reconstructor = ProtocolReconstructor()
        store = ProtocolArtifactStore(store_id="empty")
        result = reconstructor.reconstruct(store)
        assert result.status == ReconstructionStatus.PARTIAL
        assert "epistemic_state" in result.missing_artifacts
        assert "governance_policies" in result.missing_artifacts

    def test_substitution_detected(self):
        """Substituting artifacts is detected."""
        suite = ReconstructionAttackSuite()
        result = suite.attack_substitute_policy()
        assert result.detected

    def test_version_mismatch_detected(self):
        """Version mismatches are detected."""
        reconstructor = ProtocolReconstructor(protocol_version="2.0.0")
        store = ProtocolArtifactStore(store_id="s1", protocol_version="1.0.0")
        result = reconstructor.reconstruct(store)
        assert result.status == ReconstructionStatus.VERSION_MISMATCH

    def test_revocation_propagation(self):
        """Revocations propagate through the dependency graph."""
        suite = ReconstructionAttackSuite()
        result = suite.attack_revocation_replay()
        assert result.detected

    def test_duplicate_evidence_idempotent(self):
        """Duplicate evidence doesn't change authorization."""
        suite = ReconstructionAttackSuite()
        result = suite.attack_duplicate_evidence()
        assert result.detected

    def test_reordering_robust(self):
        """Reordering evidence doesn't change authorization."""
        suite = ReconstructionAttackSuite()
        result = suite.attack_reorder_evidence()
        assert result.detected

    def test_forged_state_detected(self):
        """Forged historical state is detected."""
        suite = ReconstructionAttackSuite()
        result = suite.attack_forged_historical_state()
        assert result.detected

    def test_partial_failure_handled(self):
        """Partial failures are handled gracefully."""
        suite = ReconstructionAttackSuite()
        result = suite.attack_partial_failure()
        assert result.detected
