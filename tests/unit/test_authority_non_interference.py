"""Tests for Authority Non-Interference."""

from __future__ import annotations

import pytest

from sas.quant.experiment.authority_non_interference import (
    DependencyType,
    AuthorityDependency,
    AuthorityDependencyGraph,
    InterferenceType,
    InterferenceResult,
    DecisionArtifact,
    AuthorityNonInterferenceVerifier,
    DecisionBuilder,
    InterferenceAttackSuite,
    run_interference_attack_suite,
    check_non_interference,
)
from sas.quant.experiment.compositional_authority import (
    AuthorityContext,
    create_authority_context,
    create_resource_budget,
)
from sas.quant.experiment.epistemic_governance import (
    AuthorizationStatus,
    ActionProposal,
    AuthorizationArtifact,
    ActorIdentity,
    GovernancePolicy,
    create_action_proposal,
    create_governance_policy,
    create_actor_identity,
)
from sas.quant.experiment.epistemic_consensus import (
    EpistemicConsensus,
)


# ---------------------------------------------------------------------------
# Test: Dependency Types
# ---------------------------------------------------------------------------


class TestDependencyTypes:
    def test_all_types_present(self):
        types = list(DependencyType)
        assert len(types) == 14
        assert DependencyType.DIRECT in types
        assert DependencyType.NONE in types
        assert DependencyType.UNKNOWN in types


# ---------------------------------------------------------------------------
# Test: Authority Dependency
# ---------------------------------------------------------------------------


class TestAuthorityDependency:
    def test_compute_hash(self):
        dep = AuthorityDependency(
            source="actor:a",
            target="policy:p",
            dependency_type=DependencyType.DIRECT,
        )
        hash1 = dep.compute_hash()
        hash2 = dep.compute_hash()
        assert hash1 == hash2

    def test_different_deps_different_hashes(self):
        dep1 = AuthorityDependency(
            source="actor:a",
            target="policy:p1",
            dependency_type=DependencyType.DIRECT,
        )
        dep2 = AuthorityDependency(
            source="actor:a",
            target="policy:p2",
            dependency_type=DependencyType.DIRECT,
        )
        assert dep1.compute_hash() != dep2.compute_hash()


# ---------------------------------------------------------------------------
# Test: Authority Dependency Graph
# ---------------------------------------------------------------------------


class TestAuthorityDependencyGraph:
    def test_compute_hash(self):
        graph = AuthorityDependencyGraph(graph_id="g1")
        hash1 = graph.compute_hash()
        hash2 = graph.compute_hash()
        assert hash1 == hash2

    def test_has_dependency(self):
        dep = AuthorityDependency(
            source="actor:a",
            target="policy:p",
            dependency_type=DependencyType.DIRECT,
        )
        graph = AuthorityDependencyGraph(graph_id="g1", dependencies=[dep])
        assert graph.has_dependency("actor:a", "policy:p")
        assert not graph.has_dependency("actor:a", "policy:q")

    def test_is_independent(self):
        dep = AuthorityDependency(
            source="actor:a",
            target="policy:p",
            dependency_type=DependencyType.DIRECT,
        )
        graph = AuthorityDependencyGraph(graph_id="g1", dependencies=[dep])
        assert graph.is_independent("actor:b", "policy:p")
        assert not graph.is_independent("actor:a", "policy:p")

    def test_get_closure(self):
        dep1 = AuthorityDependency(
            source="auth:x",
            target="state:s1",
            dependency_type=DependencyType.EPISTEMIC,
        )
        dep2 = AuthorityDependency(
            source="state:s1",
            target="evidence:e1",
            dependency_type=DependencyType.INDIRECT,
        )
        graph = AuthorityDependencyGraph(graph_id="g1", dependencies=[dep1, dep2])
        closure = graph.get_closure("auth:x")
        assert "auth:x" in closure
        assert "state:s1" in closure
        assert "evidence:e1" in closure


# ---------------------------------------------------------------------------
# Test: Decision Artifact
# ---------------------------------------------------------------------------


class TestDecisionArtifact:
    def test_compute_hash(self):
        decision = DecisionArtifact(
            decision_id="d1",
            action="a1",
            subject="AAPL",
            actor="actor1",
        )
        hash1 = decision.compute_hash()
        hash2 = decision.compute_hash()
        assert hash1 == hash2

    def test_is_semantically_equivalent(self):
        decision1 = DecisionArtifact(
            decision_id="d1",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.AUTHORIZED,
        )
        decision2 = DecisionArtifact(
            decision_id="d2",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.AUTHORIZED,
        )
        assert decision1.is_semantically_equivalent(decision2)

    def test_is_not_semantically_equivalent(self):
        decision1 = DecisionArtifact(
            decision_id="d1",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.AUTHORIZED,
        )
        decision2 = DecisionArtifact(
            decision_id="d2",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.DENIED,
        )
        assert not decision1.is_semantically_equivalent(decision2)


# ---------------------------------------------------------------------------
# Test: Interference Result
# ---------------------------------------------------------------------------


class TestInterferenceResult:
    def test_is_authorized(self):
        result = InterferenceResult(
            action="a1",
            baseline_context="c1",
            extended_context="c2",
            baseline_decision="authorized",
            extended_decision="authorized",
            interference_detected=False,
            interference_type=InterferenceType.EXPECTED,
        )
        assert result.is_authorized

    def test_unauthorized_interference(self):
        result = InterferenceResult(
            action="a1",
            baseline_context="c1",
            extended_context="c2",
            baseline_decision="authorized",
            extended_decision="denied",
            interference_detected=True,
            interference_type=InterferenceType.UNAUTHORIZED_INTERFERENCE,
        )
        assert not result.is_authorized


# ---------------------------------------------------------------------------
# Test: Authority Non-Interference Verifier
# ---------------------------------------------------------------------------


class TestAuthorityNonInterferenceVerifier:
    def test_build_dependency_graph(self):
        verifier = AuthorityNonInterferenceVerifier()
        action = create_action_proposal("a1", "agent1", "TRADE", "AAPL")
        context = create_authority_context(
            "c1", "a1",
            actor_identity_ref="actor1",
            governance_policy_refs=["policy1"],
            epistemic_state_refs=["state1"],
            resource_constraint_refs=["budget1"],
        )
        policy = create_governance_policy("policy1", "1.0", allowed_actions=["TRADE"])
        actor = create_actor_identity("actor1", capabilities=["trader"])

        graph = verifier.build_dependency_graph(
            action, context, {}, {"policy1": policy}, actor
        )

        assert graph.graph_id == "graph_a1"
        assert len(graph.dependencies) > 0
        assert "actor:actor1" in graph.roots

    def test_check_no_interference(self):
        verifier = AuthorityNonInterferenceVerifier()
        action = create_action_proposal("a1", "agent1", "TRADE", "AAPL")

        # Same decision
        decision1 = DecisionArtifact(
            decision_id="d1",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.AUTHORIZED,
        )
        decision2 = DecisionArtifact(
            decision_id="d2",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.AUTHORIZED,
        )

        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        graph = AuthorityDependencyGraph(graph_id="g1")
        result = verifier.check_interference(action, context, context, decision1, decision2, graph, graph)
        assert not result.interference_detected

    def test_check_interference_detected(self):
        verifier = AuthorityNonInterferenceVerifier()
        action = create_action_proposal("a1", "agent1", "TRADE", "AAPL")

        # Different decisions
        decision1 = DecisionArtifact(
            decision_id="d1",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.AUTHORIZED,
        )
        decision2 = DecisionArtifact(
            decision_id="d2",
            action="a1",
            subject="AAPL",
            actor="actor1",
            disposition=AuthorizationStatus.DENIED,
        )

        context = create_authority_context("c1", "a1", actor_identity_ref="actor1")
        graph = AuthorityDependencyGraph(graph_id="g1")
        result = verifier.check_interference(action, context, context, decision1, decision2, graph, graph)
        assert result.interference_detected


# ---------------------------------------------------------------------------
# Test: Decision Builder
# ---------------------------------------------------------------------------


class TestDecisionBuilder:
    def test_build_decision(self):
        builder = DecisionBuilder()
        action = create_action_proposal("a1", "agent1", "TRADE", "AAPL")
        context = create_authority_context(
            "c1", "a1",
            actor_identity_ref="actor1",
            governance_policy_refs=["policy1"],
        )
        auth = AuthorizationArtifact(
            authorization_id="auth1",
            action_proposal_ref="a1",
            status=AuthorizationStatus.AUTHORIZED,
        )
        actor = create_actor_identity("actor1", capabilities=["trader"])
        graph = AuthorityDependencyGraph(
            graph_id="g1",
            roots=["actor:actor1", "policy:policy1"],
        )

        decision = builder.build_decision(action, context, auth, actor, graph)
        assert decision.action == "a1"
        assert decision.actor == "actor1"
        assert decision.disposition == AuthorizationStatus.AUTHORIZED


# ---------------------------------------------------------------------------
# Test: Interference Attack Suite
# ---------------------------------------------------------------------------


class TestInterferenceAttackSuite:
    def test_run_all_attacks(self):
        suite = InterferenceAttackSuite()
        results = suite.run_all_attacks()
        assert len(results) > 0

    def test_attack_unrelated_actor(self):
        suite = InterferenceAttackSuite()
        result = suite.attack_unrelated_actor()
        assert isinstance(result, InterferenceResult)

    def test_attack_unrelated_policy(self):
        suite = InterferenceAttackSuite()
        result = suite.attack_unrelated_policy()
        assert isinstance(result, InterferenceResult)

    def test_attack_unrelated_resource(self):
        suite = InterferenceAttackSuite()
        result = suite.attack_unrelated_resource()
        assert isinstance(result, InterferenceResult)

    def test_attack_shared_actor(self):
        suite = InterferenceAttackSuite()
        result = suite.attack_shared_actor()
        assert isinstance(result, InterferenceResult)

    def test_attack_shared_resource(self):
        suite = InterferenceAttackSuite()
        result = suite.attack_shared_resource()
        assert isinstance(result, InterferenceResult)


# ---------------------------------------------------------------------------
# Test: Convenience Functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_run_interference_attack_suite(self):
        results = run_interference_attack_suite()
        assert len(results) > 0
        for result in results:
            assert isinstance(result, InterferenceResult)

    def test_check_non_interference(self):
        action = create_action_proposal("a1", "agent1", "TRADE", "AAPL")
        context_a = create_authority_context(
            "c1", "a1",
            actor_identity_ref="actor1",
            governance_policy_refs=["policy1"],
        )
        context_b = create_authority_context(
            "c2", "a2",
            actor_identity_ref="actor2",
            governance_policy_refs=["policy2"],
        )
        policy = create_governance_policy("policy1", "1.0", allowed_actions=["TRADE"])
        actor = create_actor_identity("actor1", capabilities=["trader"])
        budget = create_resource_budget("budget1", "capital", 10000.0)

        result = check_non_interference(action, context_a, context_b, policy, actor, budget)
        assert isinstance(result, InterferenceResult)


# ---------------------------------------------------------------------------
# Test: Invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_unrelated_actor_does_not_interfere(self):
        """Unrelated actor should not affect authorization."""
        suite = InterferenceAttackSuite()
        result = suite.attack_unrelated_actor()
        # Merge should fail due to actor mismatch (conservative)
        assert not result.interference_detected or result.is_authorized

    def test_unrelated_policy_does_not_interfere(self):
        """Unrelated policy should not affect authorization."""
        suite = InterferenceAttackSuite()
        result = suite.attack_unrelated_policy()
        assert not result.interference_detected or result.is_authorized

    def test_unrelated_resource_does_not_interfere(self):
        """Unrelated resource should not affect authorization."""
        suite = InterferenceAttackSuite()
        result = suite.attack_unrelated_resource()
        assert not result.interference_detected or result.is_authorized

    def test_shared_actor_may_interfere(self):
        """Shared actor may affect authorization (legitimate dependency)."""
        suite = InterferenceAttackSuite()
        result = suite.attack_shared_actor()
        # Shared actor means merge succeeds, which may change result
        assert isinstance(result, InterferenceResult)

    def test_shared_resource_may_interfere(self):
        """Shared resource may affect authorization (legitimate dependency)."""
        suite = InterferenceAttackSuite()
        result = suite.attack_shared_resource()
        assert isinstance(result, InterferenceResult)

    def test_dependency_graph_isolation(self):
        """Dependency graph correctly identifies isolated nodes."""
        graph = AuthorityDependencyGraph(
            graph_id="g1",
            dependencies=[
                AuthorityDependency(
                    source="actor:a",
                    target="policy:p1",
                    dependency_type=DependencyType.DIRECT,
                ),
            ],
        )
        assert graph.is_independent("actor:b", "policy:p1")
        assert not graph.is_independent("actor:a", "policy:p1")

    def test_interference_type_classification(self):
        """Interference types are correctly classified."""
        verifier = AuthorityNonInterferenceVerifier()

        # No interference
        result = InterferenceResult(
            action="a1",
            baseline_context="c1",
            extended_context="c2",
            baseline_decision="authorized",
            extended_decision="authorized",
            interference_detected=False,
            interference_type=InterferenceType.EXPECTED,
        )
        assert result.is_authorized

        # Unauthorized interference
        result = InterferenceResult(
            action="a1",
            baseline_context="c1",
            extended_context="c2",
            baseline_decision="authorized",
            extended_decision="denied",
            interference_detected=True,
            interference_type=InterferenceType.UNAUTHORIZED_INTERFERENCE,
        )
        assert not result.is_authorized
