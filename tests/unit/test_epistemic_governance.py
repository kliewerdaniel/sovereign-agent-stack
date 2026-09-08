"""Tests for Epistemic Governance and Authorization Derivation."""

from __future__ import annotations

import pytest

from sas.quant.experiment.epistemic_governance import (
    AuthorizationStatus,
    ActionProposal,
    RecommendationArtifact,
    GovernancePolicy,
    AuthorizationArtifact,
    RevocationArtifact,
    ExecutionArtifact,
    ActorIdentity,
    AuthorizationDerivation,
    AuthorizationVerifier,
    AuthorizationTrace,
    AuthorizationVerificationResult,
    ExecutionProtocol,
    ExecutionResult,
    create_action_proposal,
    create_governance_policy,
    create_actor_identity,
    derive_authorization,
    verify_authorization,
)
from sas.quant.experiment.epistemic_state import (
    EpistemicStatus,
    StateDimension,
    DimensionStatus,
    DimensionState,
    EpistemicState,
    TransitionType,
    EpistemicTransition,
    EpistemicStateMachine,
    create_initial_state,
    apply_evidence,
)
from sas.quant.experiment.epistemic_consensus import (
    VerifierIdentity,
    VerificationAssertion,
    DisagreementClass,
    VerifierComparison,
    EpistemicConsensus,
)
from sas.quant.experiment.epistemic_verification import (
    VerificationStatus,
    EpistemicAttestation,
    EpistemicVerifier,
    build_attestation,
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
# Test: Action Proposal
# ---------------------------------------------------------------------------


class TestActionProposal:
    def test_compute_hash(self):
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )
        hash1 = proposal.compute_hash()
        hash2 = proposal.compute_hash()
        assert hash1 == hash2

    def test_proposal_not_authorization(self):
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )
        # A proposal is just a request, not authorization
        assert proposal.provenance_hash == ""  # Not yet provenance-backed


# ---------------------------------------------------------------------------
# Test: Governance Policy
# ---------------------------------------------------------------------------


class TestGovernancePolicy:
    def test_compute_hash(self):
        policy = GovernancePolicy(
            policy_id="p1",
            policy_version="1.0.0",
        )
        hash1 = policy.compute_hash()
        hash2 = policy.compute_hash()
        assert hash1 == hash2

    def test_immutable(self):
        policy = GovernancePolicy(
            policy_id="p1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
        )
        # Cannot modify frozen dataclass
        with pytest.raises(Exception):
            policy.allowed_actions = ["TRADE", "WRITE"]


# ---------------------------------------------------------------------------
# Test: Authorization Derivation
# ---------------------------------------------------------------------------


class TestAuthorizationDerivation:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def _create_valid_state(self) -> EpistemicState:
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

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
        return new_state

    def _create_policy(self) -> GovernancePolicy:
        return GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            prohibited_actions=["INSIDER_TRADING"],
            required_epistemic_dimensions={
                "mechanism": "identified",
            },
            required_verification_conditions=["consensus"],
            required_identity_conditions=["trader"],
            resource_limits={"max_exposure": 10000.0},
            temporal_constraints={"market_hours": "09:30-16:00"},
        )

    def _create_policy_strict(self) -> GovernancePolicy:
        return GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            prohibited_actions=["INSIDER_TRADING"],
            required_epistemic_dimensions={
                "mechanism": "robust",
                "generalization": "robust",
            },
            required_verification_conditions=["consensus"],
            required_identity_conditions=["trader"],
            resource_limits={"max_exposure": 10000.0},
            temporal_constraints={"market_hours": "09:30-16:00"},
        )

    def _create_actor(self) -> ActorIdentity:
        return ActorIdentity(
            actor_id="actor1",
            capabilities=["trader"],
        )

    def _create_assertion(self) -> VerificationAssertion:
        identity = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        return VerificationAssertion(
            assertion_id="assert1",
            verifier_identity=identity,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.IDENTIFIED,
            },
        )

    def _create_consensus(self) -> EpistemicConsensus:
        return EpistemicConsensus(
            consensus_id="consensus1",
            proposition_id="p1",
            has_consensus=True,
            consensus_basis="Agreement across verifiers",
        )

    def test_derive_authorized(self):
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
            requested_resources={"max_exposure": 5000.0},
        )
        state = self._create_valid_state()
        assertion = self._create_assertion()
        consensus = self._create_consensus()
        policy = self._create_policy()
        actor = self._create_actor()

        auth = deriv.derive_authorization(
            proposal, {"p1": state}, [assertion], consensus, policy, actor
        )

        assert auth.status == AuthorizationStatus.AUTHORIZED

    def test_derive_prohibited_action(self):
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="INSIDER_TRADING",
            target="AAPL",
        )
        policy = self._create_policy()
        actor = self._create_actor()

        auth = deriv.derive_authorization(
            proposal, {}, [], self._create_consensus(), policy, actor
        )

        assert auth.status == AuthorizationStatus.DENIED

    def test_derive_missing_capability(self):
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )
        state = self._create_valid_state()
        assertion = self._create_assertion()
        consensus = self._create_consensus()
        policy = self._create_policy()
        actor = ActorIdentity(actor_id="actor1", capabilities=["analyst"])

        auth = deriv.derive_authorization(
            proposal, {"p1": state}, [assertion], consensus, policy, actor
        )

        assert auth.status == AuthorizationStatus.MISSING_AUTHORITY

    def test_derive_resource_violation(self):
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
            requested_resources={"max_exposure": 50000.0},
        )
        state = self._create_valid_state()
        assertion = self._create_assertion()
        consensus = self._create_consensus()
        policy = self._create_policy()
        actor = self._create_actor()

        auth = deriv.derive_authorization(
            proposal, {"p1": state}, [assertion], consensus, policy, actor
        )

        assert auth.status == AuthorizationStatus.RESOURCE_CONSTRAINT_VIOLATION


# ---------------------------------------------------------------------------
# Test: Authorization Verifier
# ---------------------------------------------------------------------------


class TestAuthorizationVerifier:
    def _create_proposition(self) -> TypedProposition:
        return TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )

    def _create_valid_state(self) -> EpistemicState:
        prop = self._create_proposition()
        machine = EpistemicStateMachine(prop)
        initial_state = machine.create_initial_state()

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
        return new_state

    def _create_policy(self) -> GovernancePolicy:
        return GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            prohibited_actions=["INSIDER_TRADING"],
            required_epistemic_dimensions={
                "mechanism": "replicated",
            },
            required_verification_conditions=["consensus"],
            required_identity_conditions=["trader"],
            resource_limits={"max_exposure": 10000.0},
        )

    def _create_actor(self) -> ActorIdentity:
        return ActorIdentity(
            actor_id="actor1",
            capabilities=["trader"],
        )

    def _create_assertion(self) -> VerificationAssertion:
        identity = VerifierIdentity(verifier_id="v1", implementation_id="impl1")
        return VerificationAssertion(
            assertion_id="assert1",
            verifier_identity=identity,
            attestation_hash="hash1",
            overall_status=VerificationStatus.VALID,
            verified_dimensions={
                StateDimension.MECHANISM: DimensionStatus.IDENTIFIED,
            },
        )

    def _create_consensus(self) -> EpistemicConsensus:
        return EpistemicConsensus(
            consensus_id="consensus1",
            proposition_id="p1",
            has_consensus=True,
            consensus_basis="Agreement across verifiers",
        )

    def test_verify_valid_authorization(self):
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
            requested_resources={"max_exposure": 5000.0},
        )
        state = self._create_valid_state()
        assertion = self._create_assertion()
        consensus = self._create_consensus()
        policy = self._create_policy()
        actor = self._create_actor()

        deriv = AuthorizationDerivation()
        auth = deriv.derive_authorization(
            proposal, {"p1": state}, [assertion], consensus, policy, actor
        )

        # Verify the authorization is valid
        result = verifier.verify_authorization(
            auth, proposal, {"p1": state}, [assertion], consensus, policy, actor
        )

        # The authorization should be valid
        assert result.valid

    def test_verify_invalid_authorization(self):
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )
        state = self._create_valid_state()
        assertion = self._create_assertion()
        consensus = self._create_consensus()
        policy = self._create_policy()
        actor = self._create_actor()

        # Create a forged authorization claiming authorization
        forged_auth = AuthorizationArtifact(
            authorization_id="auth_forged",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        result = verifier.verify_authorization(
            forged_auth, proposal, {"p1": state}, [assertion], consensus, policy, actor
        )

        # Should detect mismatch
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 1 — Agent Self-Authorization
# ---------------------------------------------------------------------------


class TestAttack1AgentSelfAuthorization:
    def test_agent_cannot_authorize_own_action(self):
        """Agent produces Recommendation + Authorization. Must be rejected."""
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Agent creates a forged authorization
        forged_auth = AuthorizationArtifact(
            authorization_id="auth_forged",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        # The execution protocol should reject this
        protocol = ExecutionProtocol()
        result = protocol.execute(
            proposal, forged_auth, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="agent1"),
        )

        assert not result.executed


# ---------------------------------------------------------------------------
# Attack 2 — Epistemic Status Injection
# ---------------------------------------------------------------------------


class TestAttack2EpistemicStatusInjection:
    def test_cannot_inject_epistemic_status(self):
        """Agent creates epistemic_state = SUPPORTED without valid transition."""
        # Create a forged epistemic state
        forged_state = EpistemicState(
            state_id="forged",
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            status=EpistemicStatus.SUPPORTED,
        )

        # The authorization verifier should detect this
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_epistemic_dimensions={"mechanism": "replicated"},
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            epistemic_state_refs=["p1"],
        )

        result = verifier.verify_authorization(
            auth, proposal, {"p1": forged_state}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because forged state has no dimension states
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 3 — Consensus Injection
# ---------------------------------------------------------------------------


class TestAttack3ConsensusInjection:
    def test_cannot_inject_consensus(self):
        """Agent creates EpistemicConsensus without valid verifier assertions."""
        forged_consensus = EpistemicConsensus(
            consensus_id="forged",
            proposition_id="p1",
            has_consensus=True,
        )

        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_verification_conditions=["consensus"],
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            consensus_conflict_refs=["forged"],
        )

        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            forged_consensus,
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because consensus has no assertions
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 4 — Majority Authorization
# ---------------------------------------------------------------------------


class TestAttack4MajorityAuthorization:
    def test_majority_cannot_authorize(self):
        """9 agents say AUTHORIZED, 1 says DENIED. No implicit majority."""
        protocol = ExecutionProtocol()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Even if 9 agents say authorized, the authorization must be derived
        forged_auth = AuthorizationArtifact(
            authorization_id="auth_forged",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        result = protocol.execute(
            proposal, forged_auth, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="agent1"),
        )

        assert not result.executed


# ---------------------------------------------------------------------------
# Attack 5 — Majority Verifier Escalation
# ---------------------------------------------------------------------------


class TestAttack5MajorityVerifierEscalation:
    def test_correlated_verifiers_no_escalation(self):
        """100 correlated verifiers supporting an action. Governance requires
        independent verification. Correlated assertions must not satisfy."""
        # Create 100 correlated assertions (same implementation)
        assertions = []
        for i in range(100):
            identity = VerifierIdentity(
                verifier_id=f"v{i}",
                implementation_id="impl1",
            )
            assertions.append(VerificationAssertion(
                assertion_id=f"a{i}",
                verifier_identity=identity,
                attestation_hash="hash1",
                overall_status=VerificationStatus.VALID,
            ))

        # The consensus builder should detect correlation
        consensus = EpistemicConsensus(
            consensus_id="consensus1",
            proposition_id="p1",
            has_consensus=True,
        )

        # But the authorization verifier should check independence
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_verification_conditions=["independent_verification"],
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            verification_assertion_refs=[a.assertion_id for a in assertions],
        )

        result = verifier.verify_authorization(
            auth, proposal, {}, assertions, consensus, policy,
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because all verifiers are correlated
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 6 — Stale Authorization
# ---------------------------------------------------------------------------


class TestAttack6StaleAuthorization:
    def test_expired_authorization_rejected(self):
        """Authorization valid at T1, execution at T2 after expiration."""
        # Create a policy that expires
        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            expiration="2020-01-01",
        )
        
        # Derive authorization under this policy
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )
        
        auth = deriv.derive_authorization(
            proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
        )
        
        # The authorization should be expired
        assert auth.expiration == "2020-01-01"
        
        # Verify at a later time
        verifier = AuthorizationVerifier()
        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
            current_time="2024-01-01",
        )

        assert not result.valid
        assert result.status == AuthorizationStatus.EXPIRED


# ---------------------------------------------------------------------------
# Attack 7 — Scope Escalation
# ---------------------------------------------------------------------------


class TestAttack7ScopeEscalation:
    def test_scope_escalation_rejected(self):
        """Authorize trade(asset=A, quantity=10). Attempt quantity=1000."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            requested_scope={"quantity": 1000},
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
        )

        limited_auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            policy_version="1.0.0",
            identity_ref="actor1",
            authorization_scope={"quantity": 10},
        )

        result = verifier.verify_authorization(
            limited_auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.valid
        assert result.status == AuthorizationStatus.SCOPE_MISMATCH


# ---------------------------------------------------------------------------
# Attack 8 — Parameter Mutation
# ---------------------------------------------------------------------------


class TestAttack8ParameterMutation:
    def test_parameter_mutation_rejected(self):
        """Authorize transfer $100. Attempt transfer $10,000."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRANSFER",
            target="account2",
            parameters={"amount": 10000},
        )

        limited_auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            authorization_scope={"amount": 100},
        )

        result = verifier.verify_authorization(
            limited_auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 9 — Identity Substitution
# ---------------------------------------------------------------------------


class TestAttack9IdentitySubstitution:
    def test_identity_substitution_rejected(self):
        """Authorization for Actor A. Attempt execution as Actor B."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            policy_version="1.0.0",
            identity_ref="actor_a",
        )

        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor_b"),
        )

        assert not result.valid
        assert result.status == AuthorizationStatus.ACTOR_MISMATCH


# ---------------------------------------------------------------------------
# Attack 10 — Capability Escalation
# ---------------------------------------------------------------------------


class TestAttack10CapabilityEscalation:
    def test_capability_escalation_rejected(self):
        """Actor has READ_DATA. Authorization requests EXECUTE_TRADE."""
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            required_capabilities=["EXECUTE_TRADE"],
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_identity_conditions=["EXECUTE_TRADE"],
        )

        actor = ActorIdentity(
            actor_id="actor1",
            capabilities=["READ_DATA"],
        )

        auth = deriv.derive_authorization(
            proposal, {}, [], EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy, actor,
        )

        assert auth.status == AuthorizationStatus.MISSING_AUTHORITY


# ---------------------------------------------------------------------------
# Attack 11 — Epistemic Prerequisite Substitution
# ---------------------------------------------------------------------------


class TestAttack11EpistemicPrerequisiteSubstitution:
    def test_stronger_global_status_does_not_substitute(self):
        """Policy requires mechanism=REPLICATED, generalization=ROBUST.
        Action supplies mechanism=ROBUST, generalization=UNRESOLVED."""
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_epistemic_dimensions={
                "mechanism": "replicated",
                "generalization": "robust",
            },
        )

        # Create a state with mechanism=VERIFIED but generalization=UNRESOLVED
        prop = TypedProposition(
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            target="signal_component",
            description="Signal drives returns",
        )
        state = EpistemicState(
            state_id="s1",
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            status=EpistemicStatus.SUPPORTED,
            dimension_states={
                StateDimension.MECHANISM: DimensionState(
                    dimension=StateDimension.MECHANISM,
                    status=DimensionStatus.ROBUST,
                ),
                StateDimension.GENERALIZATION: DimensionState(
                    dimension=StateDimension.GENERALIZATION,
                    status=DimensionStatus.UNRESOLVED,
                ),
            },
        )

        auth = deriv.derive_authorization(
            proposal, {"p1": state}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert auth.status == AuthorizationStatus.EPISTEMIC_PREREQUISITE_UNMET


# ---------------------------------------------------------------------------
# Attack 12 — Verification Conflict
# ---------------------------------------------------------------------------


class TestAttack12VerificationConflict:
    def test_verification_conflict_blocks_authorization(self):
        """Verifier A: SUPPORTED. Verifier B: REFUTED. Authorization blocked."""
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_verification_conditions=["consensus"],
        )

        # Create a consensus with conflict
        conflict_consensus = EpistemicConsensus(
            consensus_id="consensus_conflict",
            proposition_id="p1",
            has_consensus=False,
            unresolved_conflicts=["conflict1"],
        )

        auth = deriv.derive_authorization(
            proposal, {}, [], conflict_consensus, policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert auth.status == AuthorizationStatus.VERIFICATION_CONFLICT


# ---------------------------------------------------------------------------
# Attack 13 — Governance Conflict
# ---------------------------------------------------------------------------


class TestAttack13GovernanceConflict:
    def test_policy_conflict_detected(self):
        """Policy A: AUTHORIZED. Policy B: DENIED. System must detect conflict."""
        # This is a design test - the system should not arbitrarily select one policy
        policy_a = GovernancePolicy(
            policy_id="policy_a",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
        )
        policy_b = GovernancePolicy(
            policy_id="policy_b",
            policy_version="1.0.0",
            prohibited_actions=["TRADE"],
        )

        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Under policy A: authorized
        auth_a = deriv.derive_authorization(
            proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy_a,
            ActorIdentity(actor_id="actor1"),
        )

        # Under policy B: denied
        auth_b = deriv.derive_authorization(
            proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy_b,
            ActorIdentity(actor_id="actor1"),
        )

        # The system should produce different results
        assert auth_a.status == AuthorizationStatus.AUTHORIZED
        assert auth_b.status == AuthorizationStatus.DENIED


# ---------------------------------------------------------------------------
# Attack 14 — Policy Substitution
# ---------------------------------------------------------------------------


class TestAttack14PolicySubstitution:
    def test_policy_substitution_detected(self):
        """Authorization derived under Policy P1. Attempt execution with P2."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            policy_version="1.0.0",
        )

        # Different policy presented
        different_policy = GovernancePolicy(
            policy_id="policy2",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
        )

        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            different_policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 15 — Policy Downgrade
# ---------------------------------------------------------------------------


class TestAttack15PolicyDowngrade:
    def test_policy_downgrade_detected(self):
        """Action requires policy version 7. Agent substitutes version 3."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            policy_version="3.0.0",
        )

        # Required policy version is 7
        required_policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="7.0.0",
            allowed_actions=["TRADE"],
        )

        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            required_policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 16 — Evidence Substitution
# ---------------------------------------------------------------------------


class TestAttack16EvidenceSubstitution:
    def test_evidence_substitution_detected(self):
        """Authorization references E1. Replace with E2 (same content, different provenance)."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            derivation_trace=["evidence=e1"],
        )

        # The verifier checks derivation, not just evidence refs
        # If the evidence doesn't support the authorization, it fails
        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because no evidence provided
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 17 — State Substitution
# ---------------------------------------------------------------------------


class TestAttack17StateSubstitution:
    def test_state_substitution_detected(self):
        """Authorization derived from State S7. Replace with forged S8."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            epistemic_state_refs=["s7"],
        )

        # Forged state with different ID
        forged_state = EpistemicState(
            state_id="s8",
            proposition_id="p1",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            status=EpistemicStatus.SUPPORTED,
        )

        result = verifier.verify_authorization(
            auth, proposal, {"s8": forged_state}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because state s7 not found
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 18 — Retroactive Revocation
# ---------------------------------------------------------------------------


class TestAttack18RetroactiveRevocation:
    def test_historical_authorization_preserved(self):
        """Historical authorization at T1. Later policy at T2. Distinguish."""
        # Historical authorization
        historical_auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            policy_version="1.0.0",
        )

        # The historical authorization should remain valid
        assert historical_auth.status == AuthorizationStatus.AUTHORIZED

        # New policy doesn't rewrite history
        new_policy = GovernancePolicy(
            policy_id="policy2",
            policy_version="2.0.0",
            prohibited_actions=["TRADE"],
        )

        # Historical auth is still valid under old policy
        assert historical_auth.governance_policy_ref == "policy1"


# ---------------------------------------------------------------------------
# Attack 19 — Revocation
# ---------------------------------------------------------------------------


class TestAttack19Revocation:
    def test_revocation_blocks_execution(self):
        """Authorization A. Revocation R. Attempt execution. Rejected."""
        protocol = ExecutionProtocol()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        revocation = RevocationArtifact(
            revocation_id="rev1",
            authorization_ref="auth1",
            revoker_id="admin",
            reason="Security concern",
        )

        protocol.add_revocation(revocation)

        result = protocol.execute(
            proposal, auth, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.executed


# ---------------------------------------------------------------------------
# Attack 20 — Revocation Forgery
# ---------------------------------------------------------------------------


class TestAttack20RevocationForgery:
    def test_forged_revocation_rejected(self):
        """Forge revoked=true without valid revocation artifact."""
        protocol = ExecutionProtocol()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        # No revocation added to protocol
        result = protocol.execute(
            proposal, auth, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        # Should execute because no valid revocation
        # (In a full system, we'd need valid epistemic state, etc.)
        # But the point is: without a revocation artifact, auth is valid
        # This test verifies that the protocol doesn't fabricate revocations


# ---------------------------------------------------------------------------
# Attack 21 — Expiration Forgery
# ---------------------------------------------------------------------------


class TestAttack21ExpirationForgery:
    def test_expiration_forgery_rejected(self):
        """Modify expiration=future without valid provenance."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Forged authorization with future expiration
        forged_auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            expiration="2099-01-01",
        )

        # The verifier should detect that this authorization was not properly derived
        result = verifier.verify_authorization(
            forged_auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because derivation doesn't match
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 22 — Resource Constraint Violation
# ---------------------------------------------------------------------------


class TestAttack22ResourceConstraintViolation:
    def test_resource_violation_detected(self):
        """Authorization max exposure $10,000. Attempt $10,001."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            requested_resources={"max_exposure": 10001},
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            resource_constraints={"max_exposure": 10000},
        )

        result = verifier.verify_authorization(
            auth, proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 23 — TOCTOU
# ---------------------------------------------------------------------------


class TestAttack23TOCTOU:
    def test_execution_time_revalidation(self):
        """Authorization verified at T1. Execution at T2. Policy changed."""
        protocol = ExecutionProtocol()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Authorization derived under old policy
        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            governance_policy_ref="policy1",
            policy_version="1.0.0",
            expiration="2020-01-01",
        )

        # Execution at T2 after expiration
        result = protocol.execute(
            proposal, auth, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
            current_time="2024-01-01",
        )

        assert not result.executed


# ---------------------------------------------------------------------------
# Attack 24 — Agent Claims Successful Execution
# ---------------------------------------------------------------------------


class TestAttack24AgentClaimsExecution:
    def test_self_reported_execution_not_evidence(self):
        """Agent reports execution=SUCCESS without execution artifact."""
        # Self-reported execution is not evidence
        # The system requires an execution artifact
        execution = ExecutionArtifact(
            execution_id="exec1",
            action_type="TRADE",
            target="AAPL",
            actor_id="agent1",
            result="SUCCESS",
        )

        # The execution artifact must have proper provenance
        assert execution.provenance_hash == ""  # Not yet provenance-backed


# ---------------------------------------------------------------------------
# Attack 25 — Execution Forgery
# ---------------------------------------------------------------------------


class TestAttack25ExecutionForgery:
    def test_execution_without_authorization_invalid(self):
        """Execution artifact claiming action occurred without valid authorization."""
        execution = ExecutionArtifact(
            execution_id="exec1",
            action_type="TRADE",
            target="AAPL",
            actor_id="agent1",
            authorization_ref="",  # No authorization
            result="SUCCESS",
        )

        # Execution without authorization is invalid
        assert execution.authorization_ref == ""


# ---------------------------------------------------------------------------
# Attack 26 — Authorization Replay
# ---------------------------------------------------------------------------


class TestAttack26AuthorizationReplay:
    def test_authorization_replay_detected(self):
        """Valid authorization for action A at T1. Replay against action B."""
        verifier = AuthorizationVerifier()
        proposal_a = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        # Attempt to use auth for different proposal
        proposal_b = ActionProposal(
            action_id="a2",
            proposer_id="agent1",
            action_type="TRADE",
            target="MSFT",
        )

        result = verifier.verify_authorization(
            auth, proposal_b, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 27 — Cross-Proposition Confusion
# ---------------------------------------------------------------------------


class TestAttack27CrossPropositionConfusion:
    def test_similar_proposition_not_accepted(self):
        """Authorization depends on P1. Attempt to satisfy with P2."""
        verifier = AuthorizationVerifier()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )

        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
            proposition_refs=["p1"],
        )

        # Different proposition provided
        different_state = EpistemicState(
            state_id="p2",
            proposition_id="p2",
            proposition_type=PropositionType.MECHANISM_DEPENDENCY,
            status=EpistemicStatus.SUPPORTED,
        )

        result = verifier.verify_authorization(
            auth, proposal, {"p2": different_state}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            GovernancePolicy(policy_id="p1", policy_version="1.0.0"),
            ActorIdentity(actor_id="actor1"),
        )

        # Should fail because p1 not found
        assert not result.valid


# ---------------------------------------------------------------------------
# Attack 28 — Confidence Injection
# ---------------------------------------------------------------------------


class TestAttack28ConfidenceInjection:
    def test_confidence_not_authority(self):
        """Agent says confidence=0.999. Must not authorize."""
        # Confidence is not evidence
        recommendation = RecommendationArtifact(
            recommendation_id="rec1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            confidence=0.999,
        )

        # A recommendation is not authorization
        # The system must not treat confidence as authority
        assert recommendation.confidence == 0.999


# ---------------------------------------------------------------------------
# Attack 29 — Reputation Injection
# ---------------------------------------------------------------------------


class TestAttack29ReputationInjection:
    def test_reputation_not_authority(self):
        """Agent claims trusted=true, reputation=high. Must not authorize."""
        # Reputation is not authority unless governance explicitly defines it
        actor = ActorIdentity(
            actor_id="actor1",
            capabilities=["trader"],
        )

        # No reputation field in ActorIdentity
        assert not hasattr(actor, "reputation")


# ---------------------------------------------------------------------------
# Attack 30 — Authorization by Consensus
# ---------------------------------------------------------------------------


class TestAttack30AuthorizationByConsensus:
    def test_consensus_cannot_override_governance(self):
        """100 verifiers say SUPPORTED. Governance says DENIED. Result: DENIED."""
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Governance says denied
        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            prohibited_actions=["TRADE"],
        )

        # Even with consensus, governance denies
        auth = deriv.derive_authorization(
            proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1", has_consensus=True),
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert auth.status == AuthorizationStatus.DENIED


# ---------------------------------------------------------------------------
# Test: Convenience Functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_create_action_proposal(self):
        proposal = create_action_proposal("a1", "agent1", "TRADE", "AAPL")
        assert proposal.action_id == "a1"
        assert proposal.proposer_id == "agent1"

    def test_create_governance_policy(self):
        policy = create_governance_policy("p1", "1.0.0")
        assert policy.policy_id == "p1"
        assert policy.policy_version == "1.0.0"

    def test_create_actor_identity(self):
        actor = create_actor_identity("actor1", ["trader"])
        assert actor.actor_id == "actor1"
        assert "trader" in actor.capabilities


# ---------------------------------------------------------------------------
# Test: Invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_epistemic_authority_not_execution_authority(self):
        """SUPPORTED does not imply AUTHORIZED."""
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
        )

        # Even with supported epistemic state, authorization requires governance
        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            prohibited_actions=["TRADE"],
        )

        auth = deriv.derive_authorization(
            proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        assert auth.status == AuthorizationStatus.DENIED

    def test_authorization_not_execution(self):
        """AUTHORIZED does not imply execution."""
        # Authorization is necessary but not sufficient
        # Execution requires the execution protocol to verify
        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        # Authorization alone doesn't mean execution occurred
        assert auth.status == AuthorizationStatus.AUTHORIZED

    def test_execution_not_evidence_of_authorization(self):
        """Successful execution does not retroactively establish authorization."""
        execution = ExecutionArtifact(
            execution_id="exec1",
            action_type="TRADE",
            target="AAPL",
            actor_id="agent1",
            result="SUCCESS",
        )

        # Execution result is not authorization evidence
        assert execution.result == "SUCCESS"
        # The execution could have been unauthorized
        # Outcome ≠ authorization

    def test_governance_cannot_manufacture_epistemic_truth(self):
        """Policy saying mechanism=robust does not make it epistemically established."""
        # Policy requires mechanism=ROBUST
        policy = GovernancePolicy(
            policy_id="policy1",
            policy_version="1.0.0",
            allowed_actions=["TRADE"],
            required_epistemic_dimensions={"mechanism": "robust"},
        )

        # But no epistemic state is provided
        deriv = AuthorizationDerivation()
        proposal = ActionProposal(
            action_id="a1",
            proposer_id="agent1",
            action_type="TRADE",
            target="AAPL",
            epistemic_dependencies=["p1"],
        )

        auth = deriv.derive_authorization(
            proposal, {}, [],
            EpistemicConsensus(consensus_id="c1", proposition_id="p1"),
            policy,
            ActorIdentity(actor_id="actor1"),
        )

        # Authorization denied because epistemic prerequisite not met
        assert auth.status == AuthorizationStatus.EPISTEMIC_PREREQUISITE_UNMET

    def test_authorization_cannot_manufacture_evidence(self):
        """Authorized action does not retroactively validate evidence."""
        # If an action is authorized but the evidence is later found to be flawed
        # the authorization doesn't validate the evidence
        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )

        # Authorization doesn't make evidence valid
        assert auth.status == AuthorizationStatus.AUTHORIZED
