"""Tests for Execution Capability and Authority Materialization."""

from __future__ import annotations

import pytest

from sas.quant.experiment.execution_capability import (
    AttenuationType,
    BindingType,
    CapabilityConstraints,
    CapabilityMaterializer,
    CapabilityScope,
    CapabilityType,
    ExecutionContext,
    ExecutionCapability,
    ExecutionReceipt,
    ExecutionStatus,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
    create_execution_capability,
    generate_execution_capability_attack_report,
    run_execution_capability_attack_suite,
)
from sas.quant.experiment.epistemic_governance import (
    ActionProposal,
    ActorIdentity,
    AuthorizationArtifact,
    AuthorizationStatus,
    GovernancePolicy,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    ProtocolDomain,
    create_protocol_domain,
)


# ---------------------------------------------------------------------------
# Replay Guard Tests
# ---------------------------------------------------------------------------


class TestReplayGuard:
    def test_create_guard(self):
        guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce="nonce-1",
            sequence=0,
            max_uses=1,
        )
        assert guard.nonce == "nonce-1"
        assert guard.guard_type == ReplayProtectionType.SINGLE_USE

    def test_guard_hash(self):
        guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce="nonce-1",
        )
        h = guard.compute_hash()
        assert len(h) == 16

    def test_single_use_exhaustion(self):
        guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce="nonce-1",
            max_uses=1,
            current_uses=0,
        )
        assert guard.can_execute()
        assert not guard.is_exhausted()

        used = guard.record_use()
        assert not used.can_execute()
        assert used.is_exhausted()

    def test_bounded_use(self):
        guard = ReplayGuard(
            guard_type=ReplayProtectionType.BOUNDED_USE,
            nonce="nonce-1",
            max_uses=3,
            current_uses=0,
        )
        assert guard.can_execute()

        used1 = guard.record_use()
        assert used1.can_execute()

        used2 = used1.record_use()
        assert used2.can_execute()

        used3 = used2.record_use()
        assert not used3.can_execute()

    def test_unlimited_uses(self):
        guard = ReplayGuard(
            guard_type=ReplayProtectionType.BOUNDED_USE,
            nonce="nonce-1",
            max_uses=-1,
            current_uses=0,
        )
        assert guard.can_execute()

        used = guard.record_use()
        assert used.can_execute()

    def test_follows_sequence(self):
        guard1 = ReplayGuard(
            guard_type=ReplayProtectionType.SEQUENCE,
            nonce="nonce-1",
            sequence=0,
        )
        guard2 = ReplayGuard(
            guard_type=ReplayProtectionType.SEQUENCE,
            nonce="nonce-2",
            sequence=1,
            previous_nonce="nonce-1",
        )
        assert guard2.follows(guard1)
        assert not guard1.follows(guard2)


# ---------------------------------------------------------------------------
# Capability Constraints Tests
# ---------------------------------------------------------------------------


class TestCapabilityConstraints:
    def test_create_constraints(self):
        constraints = CapabilityConstraints(
            allowed_actions=["execute_trade"],
            max_quantity=100,
        )
        assert constraints.allowed_actions == ["execute_trade"]
        assert constraints.max_quantity == 100

    def test_constraints_hash(self):
        constraints = CapabilityConstraints(
            allowed_actions=["execute_trade"],
        )
        h = constraints.compute_hash()
        assert len(h) == 16

    def test_permits_action_allowed(self):
        constraints = CapabilityConstraints(
            allowed_actions=["execute_trade", "read_data"],
        )
        assert constraints.permits_action("execute_trade")
        assert constraints.permits_action("read_data")

    def test_permits_action_forbidden(self):
        constraints = CapabilityConstraints(
            allowed_actions=["execute_trade"],
            forbidden_actions=["delete_data"],
        )
        assert not constraints.permits_action("delete_data")

    def test_permits_action_not_in_allowed(self):
        constraints = CapabilityConstraints(
            allowed_actions=["execute_trade"],
        )
        assert not constraints.permits_action("read_data")

    def test_permits_quantity(self):
        constraints = CapabilityConstraints(
            min_quantity=10,
            max_quantity=100,
        )
        assert constraints.permits_quantity(50)
        assert constraints.permits_quantity(10)
        assert constraints.permits_quantity(100)
        assert not constraints.permits_quantity(5)
        assert not constraints.permits_quantity(101)


# ---------------------------------------------------------------------------
# Capability Scope Tests
# ---------------------------------------------------------------------------


class TestCapabilityScope:
    def test_create_scope(self):
        scope = CapabilityScope(
            domain_id="domain-1",
            actor_id="actor-1",
            action="execute_trade",
            resource="broker:A",
        )
        assert scope.domain_id == "domain-1"
        assert scope.action == "execute_trade"

    def test_scope_hash(self):
        scope = CapabilityScope(
            domain_id="domain-1",
            action="execute_trade",
        )
        h = scope.compute_hash()
        assert len(h) == 16

    def test_is_valid_at(self):
        from sas.quant.experiment.protocol_lineage import DomainValidityInterval
        scope = CapabilityScope(
            temporal_interval=DomainValidityInterval(
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2024-12-31T23:59:59Z",
            ),
        )
        assert scope.is_valid_at("2024-06-01T00:00:00Z")
        assert not scope.is_valid_at("2025-01-01T00:00:00Z")
        assert not scope.is_valid_at("2023-01-01T00:00:00Z")

    def test_is_compatible_with_domain(self):
        scope = CapabilityScope(domain_id="domain-1")
        domain = create_protocol_domain("domain-1")
        assert scope.is_compatible_with_domain(domain)

    def test_is_incompatible_with_wrong_domain(self):
        scope = CapabilityScope(domain_id="domain-1")
        domain = create_protocol_domain("domain-2")
        assert not scope.is_compatible_with_domain(domain)

    def test_permits_action(self):
        scope = CapabilityScope(action="execute_trade")
        assert scope.permits_action("execute_trade")
        assert not scope.permits_action("read_data")


# ---------------------------------------------------------------------------
# Executor Binding Tests
# ---------------------------------------------------------------------------


class TestExecutorBinding:
    def test_create_binding(self):
        binding = ExecutorBinding(
            binding_id="bind-1",
            executor_id="executor-1",
            resource_id="broker:A",
        )
        assert binding.binding_id == "bind-1"
        assert binding.executor_id == "executor-1"

    def test_binding_hash(self):
        binding = ExecutorBinding(
            binding_id="bind-1",
            executor_id="executor-1",
            resource_id="broker:A",
        )
        h = binding.compute_hash()
        assert len(h) == 16

    def test_is_valid_at(self):
        binding = ExecutorBinding(
            binding_id="bind-1",
            executor_id="executor-1",
            resource_id="broker:A",
            bound_at="2024-01-01T00:00:00Z",
            bound_until="2024-12-31T23:59:59Z",
        )
        assert binding.is_valid_at("2024-06-01T00:00:00Z")
        assert not binding.is_valid_at("2025-01-01T00:00:00Z")

    def test_binds_resource(self):
        binding = ExecutorBinding(
            binding_id="bind-1",
            executor_id="executor-1",
            resource_id="broker:A",
            bound_resources=["broker:A", "broker:B"],
        )
        assert binding.binds_resource("broker:A")
        assert binding.binds_resource("broker:B")
        assert not binding.binds_resource("broker:C")


# ---------------------------------------------------------------------------
# Execution Context Tests
# ---------------------------------------------------------------------------


class TestExecutionContext:
    def test_create_context(self):
        context = ExecutionContext(
            context_id="ctx-1",
            capability_ref="cap-1",
            executor_id="executor-1",
            resource_id="broker:A",
            actor_id="actor-1",
        )
        assert context.context_id == "ctx-1"
        assert context.status == ExecutionStatus.PENDING

    def test_context_hash(self):
        context = ExecutionContext(
            context_id="ctx-1",
            capability_ref="cap-1",
            executor_id="executor-1",
            resource_id="broker:A",
            actor_id="actor-1",
        )
        h = context.compute_hash()
        assert len(h) == 16

    def test_is_active(self):
        context = ExecutionContext(
            context_id="ctx-1",
            capability_ref="cap-1",
            executor_id="executor-1",
            resource_id="broker:A",
            actor_id="actor-1",
            status=ExecutionStatus.EXECUTING,
        )
        assert context.is_active()

    def test_is_complete(self):
        context = ExecutionContext(
            context_id="ctx-1",
            capability_ref="cap-1",
            executor_id="executor-1",
            resource_id="broker:A",
            actor_id="actor-1",
            status=ExecutionStatus.COMPLETED,
        )
        assert context.is_complete()

    def test_is_not_complete_when_pending(self):
        context = ExecutionContext(
            context_id="ctx-1",
            capability_ref="cap-1",
            executor_id="executor-1",
            resource_id="broker:A",
            actor_id="actor-1",
            status=ExecutionStatus.PENDING,
        )
        assert not context.is_complete()


# ---------------------------------------------------------------------------
# Execution Receipt Tests
# ---------------------------------------------------------------------------


class TestExecutionReceipt:
    def test_create_receipt(self):
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref="cap-1",
            authorization_ref="auth-1",
        )
        assert receipt.receipt_id == "receipt-1"
        assert receipt.status == ExecutionStatus.PENDING

    def test_receipt_hash(self):
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref="cap-1",
            authorization_ref="auth-1",
        )
        h = receipt.compute_hash()
        assert len(h) == 16

    def test_is_verified(self):
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref="cap-1",
            authorization_ref="auth-1",
            observed_effect="trade_executed",
            reported_result="SUCCESS",
        )
        assert receipt.is_verified()

    def test_is_not_verified_without_observation(self):
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref="cap-1",
            authorization_ref="auth-1",
            reported_result="SUCCESS",
        )
        assert not receipt.is_verified()

    def test_has_divergence(self):
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref="cap-1",
            authorization_ref="auth-1",
            intended_effect="buy_100_AAPL",
            observed_effect="buy_50_AAPL",
        )
        assert receipt.has_divergence()

    def test_no_divergence(self):
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref="cap-1",
            authorization_ref="auth-1",
            intended_effect="buy_100_AAPL",
            observed_effect="buy_100_AAPL",
        )
        assert not receipt.has_divergence()


# ---------------------------------------------------------------------------
# Capability Materializer Tests
# ---------------------------------------------------------------------------


class TestCapabilityMaterializer:
    def setup_method(self):
        self.domain = create_protocol_domain("trading-domain")
        self.materializer = CapabilityMaterializer(self.domain)
        self.actor = ActorIdentity(
            actor_id="actor-1",
            capabilities=["execute_trade"],
        )
        self.policy = GovernancePolicy(
            policy_id="policy-1",
            policy_version="1.0.0",
            allowed_actions=["execute_trade"],
        )
        self.proposal = ActionProposal(
            action_id="action-1",
            proposer_id="agent-1",
            action_type="execute_trade",
            target="AAPL",
            parameters={"quantity": 100, "account": "account_1"},
        )
        self.authorization = AuthorizationArtifact(
            authorization_id="auth-1",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.AUTHORIZED,
            identity_ref="actor-1",
            authorization_scope={
                "allowed_actions": ["execute_trade"],
                "target_resources": ["broker:A"],
            },
            expiration="2024-12-31T23:59:59Z",
        )

    def test_materialize_capability(self):
        result = self.materializer.materialize(
            self.authorization,
            self.proposal,
            self.actor,
            self.policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )
        assert result.is_valid
        assert result.capability is not None
        assert result.capability.capability_id == "cap_auth-1"
        assert result.capability.scope.action == "execute_trade"
        assert result.capability.scope.resource == "broker:A"

    def test_materialize_rejects_wrong_actor(self):
        wrong_actor = ActorIdentity(actor_id="actor-2", capabilities=["execute_trade"])
        result = self.materializer.materialize(
            self.authorization,
            self.proposal,
            wrong_actor,
            self.policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )
        assert not result.is_valid

    def test_materialize_rejects_expired_authorization(self):
        expired_auth = AuthorizationArtifact(
            authorization_id="auth-expired",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.AUTHORIZED,
            identity_ref="actor-1",
            expiration="2024-01-31T23:59:59Z",
        )
        result = self.materializer.materialize(
            expired_auth,
            self.proposal,
            self.actor,
            self.policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )
        assert not result.is_valid

    def test_materialize_rejects_non_authorized_status(self):
        non_auth = AuthorizationArtifact(
            authorization_id="auth-denied",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.DENIED,
            identity_ref="actor-1",
        )
        result = self.materializer.materialize(
            non_auth,
            self.proposal,
            self.actor,
            self.policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )
        assert not result.is_valid

    def test_attenuate_capability(self):
        result = self.materializer.materialize(
            self.authorization,
            self.proposal,
            self.actor,
            self.policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )
        assert result.capability is not None

        attenuated = self.materializer.attenuate(
            result.capability,
            CapabilityConstraints(
                attenuation_type=AttenuationType.QUANTITY_REDUCTION,
                attenuation_factor=0.5,
                max_quantity=50,
            ),
        )
        assert attenuated.is_valid
        assert attenuated.capability is not None
        assert attenuated.capability.scope.constraints.max_quantity == 50

    def test_attenuate_rejects_increase(self):
        result = self.materializer.materialize(
            self.authorization,
            self.proposal,
            self.actor,
            self.policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )
        assert result.capability is not None

        bad_attenuation = self.materializer.attenuate(
            result.capability,
            CapabilityConstraints(
                attenuation_type=AttenuationType.QUANTITY_REDUCTION,
                attenuation_factor=2.0,  # This should be rejected
                max_quantity=1000,
            ),
        )
        assert not bad_attenuation.is_valid


# ---------------------------------------------------------------------------
# Execution Capability Attack Suite Tests
# ---------------------------------------------------------------------------


class TestExecutionCapabilityAttackSuite:
    def test_capability_widening_detected(self):
        suite = run_execution_capability_attack_suite()
        widening = [r for r in suite if r.attack_name == "capability_widening"]
        assert len(widening) == 1
        assert widening[0].detected

    def test_actor_substitution_detected(self):
        suite = run_execution_capability_attack_suite()
        substitution = [r for r in suite if r.attack_name == "actor_substitution"]
        assert len(substitution) == 1
        assert substitution[0].detected

    def test_resource_substitution_detected(self):
        suite = run_execution_capability_attack_suite()
        substitution = [r for r in suite if r.attack_name == "resource_substitution"]
        assert len(substitution) == 1
        assert substitution[0].detected

    def test_temporal_extension_detected(self):
        suite = run_execution_capability_attack_suite()
        extension = [r for r in suite if r.attack_name == "temporal_extension"]
        assert len(extension) == 1
        assert extension[0].detected

    def test_replay_detected(self):
        suite = run_execution_capability_attack_suite()
        replay = [r for r in suite if r.attack_name == "replay"]
        assert len(replay) == 1
        assert replay[0].detected

    def test_attenuation_increase_detected(self):
        suite = run_execution_capability_attack_suite()
        attenuation = [r for r in suite if r.attack_name == "attenuation_increase"]
        assert len(attenuation) == 1
        assert attenuation[0].detected

    def test_domain_substitution_detected(self):
        suite = run_execution_capability_attack_suite()
        substitution = [r for r in suite if r.attack_name == "domain_substitution"]
        assert len(substitution) == 1
        assert substitution[0].detected

    def test_executor_privilege_escalation_detected(self):
        suite = run_execution_capability_attack_suite()
        escalation = [r for r in suite if r.attack_name == "executor_privilege_escalation"]
        assert len(escalation) == 1
        assert escalation[0].detected

    def test_all_attacks_run(self):
        suite = run_execution_capability_attack_suite()
        assert len(suite) >= 8

    def test_all_attacks_detected(self):
        suite = run_execution_capability_attack_suite()
        failures = [r for r in suite if not r.detected]
        assert len(failures) == 0, f"Failed attacks: {[f.attack_name for f in failures]}"


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_full_materialization_flow(self):
        """Test the full flow from authorization to capability to receipt."""
        domain = create_protocol_domain("trading-domain")
        materializer = CapabilityMaterializer(domain)

        # Create authorization
        authorization = AuthorizationArtifact(
            authorization_id="auth-1",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.AUTHORIZED,
            identity_ref="actor-1",
            authorization_scope={
                "allowed_actions": ["execute_trade"],
                "target_resources": ["broker:A"],
            },
            expiration="2024-12-31T23:59:59Z",
        )

        # Create proposal
        proposal = ActionProposal(
            action_id="action-1",
            proposer_id="agent-1",
            action_type="execute_trade",
            target="AAPL",
            parameters={"quantity": 100},
        )

        # Create actor
        actor = ActorIdentity(
            actor_id="actor-1",
            capabilities=["execute_trade"],
        )

        # Create policy
        policy = GovernancePolicy(
            policy_id="policy-1",
            policy_version="1.0.0",
            allowed_actions=["execute_trade"],
        )

        # Materialize capability
        result = materializer.materialize(
            authorization,
            proposal,
            actor,
            policy,
            "2024-06-01T00:00:00Z",
            "broker:A",
        )

        assert result.is_valid
        assert result.capability is not None

        # Verify capability properties
        cap = result.capability
        assert cap.domain_id == domain.domain_id
        assert cap.authority_root == domain.authority_root
        assert cap.provenance_root == domain.provenance_root
        assert cap.scope.action == "execute_trade"
        assert cap.scope.resource == "broker:A"
        assert cap.can_execute()

        # Create execution context
        context = ExecutionContext(
            context_id="ctx-1",
            capability_ref=cap.capability_id,
            executor_id="executor-1",
            resource_id="broker:A",
            actor_id="actor-1",
            domain_id=domain.domain_id,
            status=ExecutionStatus.EXECUTING,
        )

        assert context.is_active()

        # Create execution receipt
        receipt = ExecutionReceipt(
            receipt_id="receipt-1",
            capability_ref=cap.capability_id,
            authorization_ref=authorization.authorization_id,
            domain_id=domain.domain_id,
            actor_id="actor-1",
            executor_id="executor-1",
            resource_id="broker:A",
            action="execute_trade",
            status=ExecutionStatus.COMPLETED,
            intended_effect="buy_100_AAPL",
            observed_effect="buy_100_AAPL",
            reported_result="SUCCESS",
        )

        assert receipt.is_verified()
        assert not receipt.has_divergence()

    def test_attenuation_chain(self):
        """Test that attenuation can be chained without increasing authority."""
        domain = create_protocol_domain("trading-domain")
        materializer = CapabilityMaterializer(domain)

        authorization = AuthorizationArtifact(
            authorization_id="auth-1",
            action_proposal_ref="action-1",
            status=AuthorizationStatus.AUTHORIZED,
            identity_ref="actor-1",
            expiration="2024-12-31T23:59:59Z",
        )

        proposal = ActionProposal(
            action_id="action-1",
            proposer_id="agent-1",
            action_type="execute_trade",
            target="AAPL",
            parameters={"quantity": 100},
        )

        actor = ActorIdentity(actor_id="actor-1", capabilities=["execute_trade"])
        policy = GovernancePolicy(
            policy_id="policy-1",
            policy_version="1.0.0",
            allowed_actions=["execute_trade"],
        )

        result = materializer.materialize(
            authorization, proposal, actor, policy, "2024-06-01T00:00:00Z", "broker:A"
        )

        assert result.capability is not None
        cap = result.capability

        # First attenuation
        att1 = materializer.attenuate(
            cap,
            CapabilityConstraints(max_quantity=50),
        )
        assert att1.is_valid
        assert att1.capability is not None

        # Second attenuation
        att2 = materializer.attenuate(
            att1.capability,
            CapabilityConstraints(max_quantity=25),
        )
        assert att2.is_valid
        assert att2.capability is not None

        # Verify chain
        assert len(att2.capability.attenuation_chain) == 2

    def test_generate_report(self):
        suite = run_execution_capability_attack_suite()
        report = generate_execution_capability_attack_report(suite)
        assert "Execution Capability" in report
        assert "Total attacks:" in report
