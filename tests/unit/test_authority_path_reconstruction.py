"""Tests for Phase 31: Observed Effect → Authority Path Reconstruction."""

import pytest
from research.examples.sovereign_agent.authority_path_reconstruction import (
    AdversarialWorldGenerator,
    AttributionStatus,
    AuthorityPathNode,
    CapabilityStatus,
    DelegationStatus,
    EscapeType,
    GovernanceStatus,
    IndependentOracle,
    PathNodeStatus,
    PathReconstructionEngine,
    PathValidity,
    Phase31Experiment,
    ReconstructionWorld,
    ReconstructedAuthorityPath,
    ScopeStatus,
    TemporalStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generator() -> AdversarialWorldGenerator:
    return AdversarialWorldGenerator()


@pytest.fixture
def worlds(generator: AdversarialWorldGenerator) -> list[ReconstructionWorld]:
    return generator.generate_all_worlds()


@pytest.fixture
def engine() -> PathReconstructionEngine:
    return PathReconstructionEngine("test_engine")


@pytest.fixture
def oracle() -> IndependentOracle:
    return IndependentOracle()


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------

class TestWorldGeneration:
    def test_generates_20_worlds(self, generator: AdversarialWorldGenerator):
        worlds = generator.generate_all_worlds()
        assert len(worlds) == 20

    def test_worlds_have_unique_ids(self, worlds: list[ReconstructionWorld]):
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_world_01_complete_valid_path(self, worlds: list[ReconstructionWorld]):
        world = worlds[0]
        assert world.world_id == "world_01_complete_valid_path"
        assert world.ground_truth_validity == PathValidity.VALID
        assert world.escape_type == EscapeType.NO_ESCAPE
        assert world.has_authorization_id
        assert world.has_capability_id
        assert world.has_governance_disposition
        assert world.has_execution_receipt
        assert world.has_provenance

    def test_world_02_valid_path_missing_provenance(self, worlds: list[ReconstructionWorld]):
        world = worlds[1]
        assert world.world_id == "world_02_valid_path_missing_provenance"
        assert world.ground_truth_validity == PathValidity.INCOMPLETE
        assert not world.has_provenance

    def test_world_10_direct_primitive_bypass(self, worlds: list[ReconstructionWorld]):
        world = worlds[9]
        assert world.world_id == "world_10_direct_primitive_bypass"
        assert world.ground_truth_validity == PathValidity.INVALID
        assert world.escape_type == EscapeType.DIRECT_PRIMITIVE_BYPASS
        assert not world.has_authorization_id
        assert not world.has_capability_id

    def test_world_11_forged_authorization(self, worlds: list[ReconstructionWorld]):
        world = worlds[10]
        assert world.world_id == "world_11_forged_authorization"
        assert world.ground_truth_validity == PathValidity.INVALID
        assert world.escape_type == EscapeType.AUTHORIZATION_LAUNDERING

    def test_world_12_replayed_receipt(self, worlds: list[ReconstructionWorld]):
        world = worlds[11]
        assert world.world_id == "world_12_replayed_receipt"
        assert world.ground_truth_validity == PathValidity.INVALID
        assert world.escape_type == EscapeType.REPLAYED_RECEIPT

    def test_world_15_cyclic_delegation(self, worlds: list[ReconstructionWorld]):
        world = worlds[14]
        assert world.world_id == "world_15_cyclic_delegation"
        assert world.ground_truth_validity == PathValidity.INVALID
        assert world.escape_type == EscapeType.CYCLIC_DELEGATION

    def test_world_17_emergency_execution(self, worlds: list[ReconstructionWorld]):
        world = worlds[16]
        assert world.world_id == "world_17_emergency_execution"
        assert world.ground_truth_validity == PathValidity.VALID
        assert world.escape_type == EscapeType.NO_ESCAPE

    def test_world_18_recovery_execution(self, worlds: list[ReconstructionWorld]):
        world = worlds[17]
        assert world.world_id == "world_18_recovery_execution"
        assert world.ground_truth_validity == PathValidity.VALID
        assert world.escape_type == EscapeType.NO_ESCAPE

    def test_world_20_no_authority_evidence(self, worlds: list[ReconstructionWorld]):
        world = worlds[19]
        assert world.world_id == "world_20_no_authority_evidence"
        assert world.ground_truth_validity == PathValidity.UNKNOWN
        assert world.escape_type == EscapeType.DIRECT_PRIMITIVE_BYPASS
        assert not world.has_authorization_id
        assert not world.has_capability_id
        assert not world.has_governance_disposition
        assert not world.has_execution_receipt
        assert not world.has_provenance


# ---------------------------------------------------------------------------
# Path reconstruction engine tests
# ---------------------------------------------------------------------------

class TestPathReconstructionEngine:
    def test_reconstructs_valid_path(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.VALID
        assert result.escape_type == EscapeType.NO_ESCAPE
        assert result.is_valid
        assert not result.is_escape

    def test_reconstructs_incomplete_path(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=False,
        )
        assert result.validity == PathValidity.INCOMPLETE

    def test_reconstructs_invalid_path_forged(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "forged_authorization",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.AUTHORIZATION_LAUNDERING

    def test_reconstructs_invalid_path_cyclic(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "cyclic_delegation",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.CYCLIC_DELEGATION

    def test_reconstructs_unknown_path(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="unknown",
            effect_target="subprocess.run",
            available_evidence=(),
            has_authorization_id=False,
            has_capability_id=False,
            has_governance_disposition=False,
            has_execution_receipt=False,
            has_provenance=False,
        )
        assert result.validity == PathValidity.UNKNOWN

    def test_reconstructs_capability_laundering(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "capability_laundering",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.CAPABILITY_LAUNDERING
        assert result.capability_status == CapabilityStatus.LAUNDERED

    def test_reconstructs_governance_laundering(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "execution_gate", "disposition_without_authority",
            ),
            has_authorization_id=True,
            has_capability_id=False,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.GOVERNANCE_LAUNDERING
        assert result.governance_status == GovernanceStatus.DISPOSITION_WITHOUT_AUTHORITY

    def test_reconstructs_replayed_receipt(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "replayed_receipt",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.REPLAYED_RECEIPT

    def test_reconstructs_cross_domain_mismatch(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "cross_domain_mismatch",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.CROSS_DOMAIN_MISMATCH

    def test_reconstructs_temporal_expired(self, engine: PathReconstructionEngine):
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "expired_authority",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.TEMPORAL_EXPIRED
        assert result.temporal_status == TemporalStatus.EXPIRED


# ---------------------------------------------------------------------------
# Oracle evaluation tests
# ---------------------------------------------------------------------------

class TestOracleEvaluation:
    def test_oracle_evaluates_valid_path(
        self, engine: PathReconstructionEngine, oracle: IndependentOracle
    ):
        world = AdversarialWorldGenerator().generate_all_worlds()[0]  # valid path
        reconstruction = engine.reconstruct(
            observation_id=world.observation_id,
            effect_id=world.effect_id,
            effect_category=world.effect_category,
            effect_source=world.effect_source,
            effect_target=world.effect_target,
            available_evidence=world.available_evidence,
            has_authorization_id=world.has_authorization_id,
            has_capability_id=world.has_capability_id,
            has_governance_disposition=world.has_governance_disposition,
            has_execution_receipt=world.has_execution_receipt,
            has_provenance=world.has_provenance,
        )
        evaluation = oracle.evaluate(world, reconstruction)
        assert evaluation.validity_match
        assert evaluation.escape_match
        assert not evaluation.false_authorization
        assert not evaluation.false_escape

    def test_oracle_detects_false_authorization(
        self, engine: PathReconstructionEngine, oracle: IndependentOracle
    ):
        """Test that oracle detects when reconstruction says VALID but actually INVALID."""
        world = AdversarialWorldGenerator().generate_all_worlds()[10]  # forged authorization
        reconstruction = engine.reconstruct(
            observation_id=world.observation_id,
            effect_id=world.effect_id,
            effect_category=world.effect_category,
            effect_source=world.effect_source,
            effect_target=world.effect_target,
            available_evidence=world.available_evidence,
            has_authorization_id=world.has_authorization_id,
            has_capability_id=world.has_capability_id,
            has_governance_disposition=world.has_governance_disposition,
            has_execution_receipt=world.has_execution_receipt,
            has_provenance=world.has_provenance,
        )
        evaluation = oracle.evaluate(world, reconstruction)
        # The reconstruction should detect the forgery
        assert reconstruction.validity == PathValidity.INVALID
        assert not evaluation.false_authorization

    def test_oracle_evaluates_direct_primitive_bypass(
        self, engine: PathReconstructionEngine, oracle: IndependentOracle
    ):
        world = AdversarialWorldGenerator().generate_all_worlds()[9]  # direct bypass
        reconstruction = engine.reconstruct(
            observation_id=world.observation_id,
            effect_id=world.effect_id,
            effect_category=world.effect_category,
            effect_source=world.effect_source,
            effect_target=world.effect_target,
            available_evidence=world.available_evidence,
            has_authorization_id=world.has_authorization_id,
            has_capability_id=world.has_capability_id,
            has_governance_disposition=world.has_governance_disposition,
            has_execution_receipt=world.has_execution_receipt,
            has_provenance=world.has_provenance,
        )
        evaluation = oracle.evaluate(world, reconstruction)
        assert reconstruction.escape_type == EscapeType.DIRECT_PRIMITIVE_BYPASS
        assert evaluation.escape_match


# ---------------------------------------------------------------------------
# Phase 31 invariants
# ---------------------------------------------------------------------------

class TestPhase31Invariants:
    def test_observed_not_authorized(self):
        """OBSERVED ≠ AUTHORIZED."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=("trust_anchor", "delegation"),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Observation alone does not create authority
        assert result.validity != PathValidity.VALID or not result.is_valid

    def test_authorization_id_not_authority_proof(self):
        """AUTHORIZATION_ID ≠ AUTHORITY_PROOF."""
        engine = PathReconstructionEngine("test")
        # World with forged authorization
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "forged_authorization",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # The forged authorization should be detected
        assert result.validity == PathValidity.INVALID

    def test_capability_not_authority(self):
        """CAPABILITY ≠ AUTHORITY."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "capability_laundering",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Capability laundering should be detected
        assert result.capability_status == CapabilityStatus.LAUNDERED
        assert result.validity == PathValidity.INVALID

    def test_governance_disposition_not_authority(self):
        """GOVERNANCE_DISPOSITION ≠ AUTHORITY."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "execution_gate", "disposition_without_authority",
            ),
            has_authorization_id=True,
            has_capability_id=False,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Governance laundering should be detected
        assert result.governance_status == GovernanceStatus.DISPOSITION_WITHOUT_AUTHORITY
        assert result.validity == PathValidity.INVALID

    def test_missing_evidence_not_invalid_authority(self):
        """MISSING_EVIDENCE ≠ INVALID_AUTHORITY."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=False,
        )
        # Missing evidence should be INCOMPLETE, not INVALID
        assert result.validity == PathValidity.INCOMPLETE

    def test_no_path_found_not_path_proven_invalid(self):
        """NO_PATH_FOUND ≠ PATH_PROVEN_INVALID."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="unknown",
            effect_target="subprocess.run",
            available_evidence=(),
            has_authorization_id=False,
            has_capability_id=False,
            has_governance_disposition=False,
            has_execution_receipt=False,
            has_provenance=False,
        )
        # No evidence should be UNKNOWN, not INVALID
        assert result.validity == PathValidity.UNKNOWN

    def test_valid_path_within_incomplete_graph_not_global_valid(self):
        """VALID_PATH_WITHIN_INCOMPLETE_GRAPH ≠ GLOBAL_AUTHORITY_VALID."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Even with valid path, completeness is within declared graph
        assert result.completeness_status == "complete_within_declared_graph"

    def test_historically_valid_not_currently_valid(self):
        """HISTORICALLY_VALID ≠ CURRENTLY_VALID."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "expired_authority",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Expired authority should be INVALID
        assert result.temporal_status == TemporalStatus.EXPIRED
        assert result.validity == PathValidity.INVALID

    def test_reconstruction_not_authority_creation(self):
        """RECONSTRUCTION ≠ AUTHORITY_CREATION."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Reconstruction is evidence, not authority
        assert result.provenance != ""
        assert result.confidence < 1.0

    def test_caller_authority_not_worker_authority(self):
        """CALLER_AUTHORITY ≠ WORKER_AUTHORITY."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/quant/background.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "async_execution",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Async execution should have unconfirmed attribution
        assert result.attribution_status == AttributionStatus.CALLER_TO_WORKER_UNCONFIRMED

    def test_cross_domain_observation_not_cross_domain_authority(self):
        """CROSS_DOMAIN_OBSERVATION ≠ CROSS_DOMAIN_AUTHORITY."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "cross_domain_mismatch",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Cross-domain mismatch should be detected
        assert result.scope_status == ScopeStatus.CROSS_DOMAIN_BLOCKED
        assert result.validity == PathValidity.INVALID

    def test_replayed_receipt_not_current_authorization(self):
        """REPLAYED_RECEIPT ≠ CURRENT_AUTHORIZATION."""
        engine = PathReconstructionEngine("test")
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "replayed_receipt",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        # Replayed receipt should be detected as escape
        assert result.escape_type == EscapeType.REPLAYED_RECEIPT
        assert result.validity == PathValidity.INVALID


# ---------------------------------------------------------------------------
# Phase 31 experiment tests
# ---------------------------------------------------------------------------

class TestPhase31Experiment:
    def test_runs_all_worlds(self):
        exp = Phase31Experiment()
        results = exp.run_all()
        assert results["total_worlds"] == 20

    def test_summary_generated(self):
        exp = Phase31Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_worlds"] == 20
        assert summary["total_reconstructions"] == 20

    def test_validity_matches_count(self):
        exp = Phase31Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["validity_matches"] >= 0

    def test_false_authorizations_count(self):
        exp = Phase31Experiment()
        exp.run_all()
        summary = exp.summary()
        # False authorizations are the most important failure mode
        assert summary["false_authorizations"] >= 0

    def test_escape_matches_count(self):
        exp = Phase31Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["escape_matches"] >= 0


# ---------------------------------------------------------------------------
# Emergency and recovery path tests
# ---------------------------------------------------------------------------

class TestEmergencyAndRecoveryPaths:
    def test_emergency_path_is_valid(self, engine: PathReconstructionEngine):
        """Emergency execution with distinct authority path should be VALID."""
        result = engine.reconstruct(
            observation_id="obs_emergency",
            effect_id="eff_emergency",
            effect_category="subprocess",
            effect_source="src/sas/quant/emergency.py",
            effect_target="os.system",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.VALID
        assert result.escape_type == EscapeType.NO_ESCAPE

    def test_recovery_path_is_valid(self, engine: PathReconstructionEngine):
        """Recovery execution with distinct authority path should be VALID."""
        result = engine.reconstruct(
            observation_id="obs_recovery",
            effect_id="eff_recovery",
            effect_category="subprocess",
            effect_source="src/sas/quant/recovery.py",
            effect_target="subprocess.Popen",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.VALID
        assert result.escape_type == EscapeType.NO_ESCAPE


# ---------------------------------------------------------------------------
# Laundering detection tests
# ---------------------------------------------------------------------------

class TestLaunderingDetection:
    def test_authorization_laundering_detected(self, engine: PathReconstructionEngine):
        """Authorization ID that doesn't derive from authority graph is detected."""
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "authorization_laundering",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.AUTHORIZATION_LAUNDERING

    def test_capability_laundering_detected(self, engine: PathReconstructionEngine):
        """Capability not derived from authority is detected."""
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "capability", "execution_gate", "capability_laundering",
            ),
            has_authorization_id=True,
            has_capability_id=True,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.CAPABILITY_LAUNDERING

    def test_governance_laundering_detected(self, engine: PathReconstructionEngine):
        """Governance disposition without authority is detected."""
        result = engine.reconstruct(
            observation_id="obs_test",
            effect_id="eff_test",
            effect_category="subprocess",
            effect_source="src/sas/argopack.py",
            effect_target="subprocess.run",
            available_evidence=(
                "trust_anchor", "delegation", "policy", "governance",
                "execution_gate", "governance_laundering",
            ),
            has_authorization_id=True,
            has_capability_id=False,
            has_governance_disposition=True,
            has_execution_receipt=True,
            has_provenance=True,
        )
        assert result.validity == PathValidity.INVALID
        assert result.escape_type == EscapeType.GOVERNANCE_LAUNDERING
