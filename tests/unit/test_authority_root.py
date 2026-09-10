"""Phase 16 tests: Authority Root.

Tests investigate what terminates the authority chain.

Key finding: The authority root is a bootstrap assumption, not a governed
mechanism. The root is hardcoded as the "admin" principal and is not
subject to the same governance as downstream authority.
"""

import pytest
from examples.sovereign_agent.authority_root import (
    AuthorityRootEngine,
    AuthorityRootExperimentResult,
    AuthorityRootType,
    DelegationLink,
    RootStatus,
    run_all_phase16_experiments,
    run_distinguish_cryptographic_trust_from_authority,
    run_distinguish_origin_from_representation,
    run_investigate_authority_ordering,
    run_investigate_bootstrap_authority,
    run_investigate_genesis_authority,
    run_investigate_termination_condition,
    run_reconstruct_authority_graph,
    run_root_authority_adversarial,
    run_root_authority_governance,
    run_test_authority_conflict,
    run_test_authority_conservation,
    run_test_authority_forking,
    run_test_authority_replay_from_genesis,
    run_test_recovery,
    run_test_root_compromise,
    run_test_root_mutation,
    run_test_root_scope,
    run_test_root_self_authorization,
    run_test_root_temporality,
    run_oracle_separation,
)


class TestAuthorityRootRecord:
    """Test authority root records."""

    def test_genesis_root(self):
        """Test that genesis root is correctly identified."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
            is_derived=False,
        )
        assert root.is_genesis is True
        assert root.is_active is True

    def test_derived_root(self):
        """Test that derived root is not genesis."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.ACTIVE,
            principal="admin",
            is_derived=True,
            parent_root_id="parent_root",
        )
        assert root.is_genesis is False
        assert root.is_active is True

    def test_expired_root(self):
        """Test that expired root is not active."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.EXPIRED,
            principal="admin",
        )
        assert root.is_active is False

    def test_root_scope(self):
        """Test root scope authorization."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
            scope="*",
        )
        assert root.can_authorize("production") is True
        assert root.can_authorize("staging") is True

    def test_scoped_root(self):
        """Test scoped root authorization."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
            scope="production",
        )
        assert root.can_authorize("production") is True
        assert root.can_authorize("staging") is False


class TestDelegationChain:
    """Test delegation chains."""

    def test_chain_depth(self):
        """Test delegation chain depth."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
        )
        link1 = DelegationLink(
            link_id="link_001",
            delegator_id=root.root_id,
            delegate_id="policy_admin",
            capability="modify_policy",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        link2 = DelegationLink(
            link_id="link_002",
            delegator_id="policy_admin",
            delegate_id="governance_engine",
            capability="evaluate_policy",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        chain = engine.create_delegation_chain(
            root_id=root.root_id,
            links=[link1, link2],
        )
        assert chain.depth == 2
        assert chain.is_terminated is False

    def test_terminated_chain(self):
        """Test terminated delegation chain."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
        )
        link1 = DelegationLink(
            link_id="link_001",
            delegator_id=root.root_id,
            delegate_id="policy_admin",
            capability="modify_policy",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
            is_terminal=True,
        )
        chain = engine.create_delegation_chain(
            root_id=root.root_id,
            links=[link1],
        )
        assert chain.is_terminated is True

    def test_recursive_chain(self):
        """Test recursive delegation chain."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
        )
        # Create a chain that cycles: root → admin → admin (self-delegation)
        link1 = DelegationLink(
            link_id="link_001",
            delegator_id=root.root_id,
            delegate_id="admin",
            capability="modify_policy",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        link2 = DelegationLink(
            link_id="link_002",
            delegator_id="admin",
            delegate_id="admin",  # Self-delegation creates cycle
            capability="modify_policy",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        chain = engine.create_delegation_chain(
            root_id=root.root_id,
            links=[link1, link2],
        )
        assert chain.is_recursive is True


class TestReconstructAuthorityGraph:
    """Test reconstructing the authority graph."""

    def test_reconstruct_graph(self):
        """Test reconstructing the complete authority graph."""
        engine = AuthorityRootEngine()
        result = run_reconstruct_authority_graph(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_EXPLICIT
        assert result.root_record is not None
        assert result.root_record.is_genesis is True


class TestDistinguishOriginFromRepresentation:
    """Test distinguishing authority origin from representation."""

    def test_origin_vs_representation(self):
        """Test that origin and representation are distinguished."""
        engine = AuthorityRootEngine()
        result = run_distinguish_origin_from_representation(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_IMPLICIT


class TestInvestigateBootstrapAuthority:
    """Test investigating bootstrap authority."""

    def test_bootstrap_authority(self):
        """Test that bootstrap authority is identified."""
        engine = AuthorityRootEngine()
        result = run_investigate_bootstrap_authority(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_EXPLICIT
        assert result.root_record is not None
        assert result.root_record.derivation_basis == "hardcoded_bootstrap"


class TestTestRootSelfAuthorization:
    """Test root self-authorization."""

    def test_self_authorization(self):
        """Test that self-authorizing root is detected."""
        engine = AuthorityRootEngine()
        result = run_test_root_self_authorization(engine)
        assert result.result == AuthorityRootExperimentResult.SELF_CREATION
        assert result.self_creation_detected is True


class TestInvestigateTerminationCondition:
    """Test investigating the termination condition."""

    def test_termination_condition(self):
        """Test that delegation termination is identified."""
        engine = AuthorityRootEngine()
        result = run_investigate_termination_condition(engine)
        assert result.result == AuthorityRootExperimentResult.DELEGATION_TERMINATES
        assert result.delegation_chain is not None
        assert result.delegation_chain.is_terminated is True


class TestInvestigateGenesisAuthority:
    """Test investigating genesis authority."""

    def test_genesis_authority(self):
        """Test that genesis authority is identified."""
        engine = AuthorityRootEngine()
        result = run_investigate_genesis_authority(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_EXPLICIT
        assert result.root_record is not None
        assert result.root_record.is_genesis is True


class TestRootAuthorityGovernance:
    """Test root authority governance."""

    def test_root_governance(self):
        """Test that root governance gap is identified."""
        engine = AuthorityRootEngine()
        result = run_root_authority_governance(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_EXPLICIT
        assert result.root_record is not None
        assert "ungoverned" in result.root_record.derivation_basis or "bootstrap" in result.root_record.derivation_basis


class TestRootAuthorityAdversarial:
    """Test root authority adversarial experiment."""

    def test_adversarial(self):
        """Test that adversarial attack on root is identified."""
        engine = AuthorityRootEngine()
        result = run_root_authority_adversarial(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_EXPLICIT


class TestOracleSeparation:
    """Test oracle separation."""

    def test_oracle_separation(self):
        """Test that oracle separation is maintained."""
        engine = AuthorityRootEngine()
        result = run_oracle_separation(engine)
        assert result.result == AuthorityRootExperimentResult.ROOT_EXPLICIT
        assert len(result.normative_assumptions) > 0


class TestAllPhase16Experiments:
    """Test all Phase 16 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 16 experiments run."""
        results = run_all_phase16_experiments()
        assert results["total_experiments"] == 20

    def test_genesis_root_explicit(self):
        """Test that genesis root is explicitly identified."""
        results = run_all_phase16_experiments()
        assert results["experiments"]["investigate_genesis_authority"].result == AuthorityRootExperimentResult.ROOT_EXPLICIT

    def test_self_creation_detected(self):
        """Test that self-creation is detected."""
        results = run_all_phase16_experiments()
        assert results["experiments"]["test_root_self_authorization"].self_creation_detected is True

    def test_delegation_terminates(self):
        """Test that delegation termination is identified."""
        results = run_all_phase16_experiments()
        assert results["experiments"]["investigate_termination_condition"].result == AuthorityRootExperimentResult.DELEGATION_TERMINATES

    def test_root_governance_underspecified(self):
        """Test that root governance is underspecified."""
        results = run_all_phase16_experiments()
        exp = results["experiments"]["root_authority_governance"]
        assert len(exp.underspecifications) > 0


class TestAuthorityRootEngine:
    """Test authority root engine."""

    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = AuthorityRootEngine()
        assert len(engine.experiments) == 0
        assert len(engine.root_records) == 0

    def test_root_record_creation(self):
        """Test that root records are created correctly."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
        )
        assert root.root_id.startswith("root_")
        assert root.root_type == AuthorityRootType.AUTHORITY
        assert root.status == RootStatus.GENESIS

    def test_delegation_chain_creation(self):
        """Test that delegation chains are created correctly."""
        engine = AuthorityRootEngine()
        root = engine.create_root_record(
            root_type=AuthorityRootType.AUTHORITY,
            status=RootStatus.GENESIS,
            principal="admin",
        )
        link = DelegationLink(
            link_id="link_001",
            delegator_id=root.root_id,
            delegate_id="admin",
            capability="modify_policy",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        chain = engine.create_delegation_chain(
            root_id=root.root_id,
            links=[link],
        )
        assert chain.chain_id.startswith("chain_")
        assert chain.depth == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
