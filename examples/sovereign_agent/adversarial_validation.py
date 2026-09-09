"""Adversarial Dependency Validation Environment.

Tests whether the protocol can distinguish an authorization whose dependency graph
is genuinely sufficient from one whose dependency graph is merely internally
consistent but incomplete.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    AuthorizationStatus,
    DependencyStrength,
    DependencyType,
    StalenessType,
    build_authorization_dependency_graph,
)
from examples.sovereign_agent.dependency_intersection import (
    DependencyIntersectionEvaluator,
    Evidence,
    EvidenceType,
)
from examples.sovereign_agent.epistemic_invalidation import (
    EpistemicInvalidationEngine,
    InvalidationDecision,
)
from examples.sovereign_agent.dependency_status import (
    DependencyAttestation,
    DependencyDiscoveryMethod,
    DependencyEpistemicState,
    DependencyEpistemicStatus,
    DependencyGraphEpistemicState,
    DependencyScope,
    create_attestation,
)


class AdversarialScenario(str, Enum):
    """Adversarial dependency validation scenarios."""
    COMPLETE_GRAPH = "complete_graph"
    MISSING_DIRECT_DEPENDENCY = "missing_direct_dependency"
    MISSING_TRANSITIVE_DEPENDENCY = "missing_transitive_dependency"
    FALSE_DEPENDENCY = "false_dependency"
    OVER_BROAD_DEPENDENCY = "over_broad_dependency"
    STALE_DEPENDENCY = "stale_dependency"
    AMBIGUOUS_DEPENDENCY = "ambiguous_dependency"
    WRONG_SCOPE = "wrong_scope"
    WRONG_TEMPORAL = "wrong_temporal"
    WRONG_ENVIRONMENT = "wrong_environment"
    RUNTIME_DISCOVERY = "runtime_discovery"
    EXPERIMENT_DISCOVERY = "experiment_discovery"
    POST_AUTHORIZATION_DISCOVERY = "post_authorization_discovery"
    CONTRADICTED_DEPENDENCY = "contradicted_dependency"
    INCOMPLETE_PROVENANCE = "incomplete_provenance"
    CROSS_DOMAIN_DEPENDENCY = "cross_domain_dependency"
    FEATURE_FLAG_DEPENDENCY = "feature_flag_dependency"
    FAILURE_ONLY_DEPENDENCY = "failure_only_dependency"
    SINGLE_OPERATION_DEPENDENCY = "single_operation_dependency"
    SINGLE_ACTOR_DEPENDENCY = "single_actor_dependency"


@dataclass(frozen=True)
class AdversarialResult:
    """Result of an adversarial validation test."""
    scenario: AdversarialScenario
    authorization_id: str
    expected_decision: InvalidationDecision
    actual_decision: InvalidationDecision
    dependency_graph_completeness: float
    test_passed: bool
    description: str
    notes: str = ""


@dataclass
class AdversarialValidationEngine:
    """Engine for adversarial dependency validation."""

    def run_scenario(
        self,
        scenario: AdversarialScenario,
    ) -> AdversarialResult:
        """Run an adversarial validation scenario."""
        if scenario == AdversarialScenario.COMPLETE_GRAPH:
            return self._run_complete_graph()
        elif scenario == AdversarialScenario.MISSING_DIRECT_DEPENDENCY:
            return self._run_missing_direct_dependency()
        elif scenario == AdversarialScenario.MISSING_TRANSITIVE_DEPENDENCY:
            return self._run_missing_transitive_dependency()
        elif scenario == AdversarialScenario.FALSE_DEPENDENCY:
            return self._run_false_dependency()
        elif scenario == AdversarialScenario.OVER_BROAD_DEPENDENCY:
            return self._run_over_broad_dependency()
        elif scenario == AdversarialScenario.STALE_DEPENDENCY:
            return self._run_stale_dependency()
        elif scenario == AdversarialScenario.AMBIGUOUS_DEPENDENCY:
            return self._run_ambiguous_dependency()
        elif scenario == AdversarialScenario.WRONG_SCOPE:
            return self._run_wrong_scope()
        elif scenario == AdversarialScenario.WRONG_TEMPORAL:
            return self._run_wrong_temporal()
        elif scenario == AdversarialScenario.WRONG_ENVIRONMENT:
            return self._run_wrong_environment()
        elif scenario == AdversarialScenario.RUNTIME_DISCOVERY:
            return self._run_runtime_discovery()
        elif scenario == AdversarialScenario.EXPERIMENT_DISCOVERY:
            return self._run_experiment_discovery()
        elif scenario == AdversarialScenario.POST_AUTHORIZATION_DISCOVERY:
            return self._run_post_authorization_discovery()
        elif scenario == AdversarialScenario.CONTRADICTED_DEPENDENCY:
            return self._run_contradicted_dependency()
        elif scenario == AdversarialScenario.INCOMPLETE_PROVENANCE:
            return self._run_incomplete_provenance()
        elif scenario == AdversarialScenario.CROSS_DOMAIN_DEPENDENCY:
            return self._run_cross_domain_dependency()
        elif scenario == AdversarialScenario.FEATURE_FLAG_DEPENDENCY:
            return self._run_feature_flag_dependency()
        elif scenario == AdversarialScenario.FAILURE_ONLY_DEPENDENCY:
            return self._run_failure_only_dependency()
        elif scenario == AdversarialScenario.SINGLE_OPERATION_DEPENDENCY:
            return self._run_single_operation_dependency()
        elif scenario == AdversarialScenario.SINGLE_ACTOR_DEPENDENCY:
            return self._run_single_actor_dependency()
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    def _run_complete_graph(self) -> AdversarialResult:
        """Run complete dependency graph scenario."""
        # Build a complete graph
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_complete",
            evidence_ids=["ev_001", "ev_002"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # New evidence that contradicts
        contradictory = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [contradictory])

        return AdversarialResult(
            scenario=AdversarialScenario.COMPLETE_GRAPH,
            authorization_id="auth_complete",
            expected_decision=InvalidationDecision.SUSPEND,
            actual_decision=result.decision,
            dependency_graph_completeness=1.0,
            test_passed=result.decision == InvalidationDecision.SUSPEND,
            description="Complete dependency graph with contradictory evidence",
        )

    def _run_missing_direct_dependency(self) -> AdversarialResult:
        """Run missing direct dependency scenario."""
        # Build a graph with a missing direct dependency
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_missing_direct",
            evidence_ids=["ev_001"],  # Missing ev_002
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # New evidence that would have been caught by the missing dependency
        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is contradicted by new data",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        # The protocol should detect that ev_002 is not in the dependency graph
        # and flag it as requiring reevaluation
        return AdversarialResult(
            scenario=AdversarialScenario.MISSING_DIRECT_DEPENDENCY,
            authorization_id="auth_missing_direct",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.8,
            test_passed=result.requires_governance_review,
            description="Missing direct dependency - protocol should detect incomplete graph",
        )

    def _run_missing_transitive_dependency(self) -> AdversarialResult:
        """Run missing transitive dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_missing_transitive",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Remove transitive dependencies to simulate missing transitive
        auth_graph.dependencies = [
            d for d in auth_graph.dependencies
            if d.strength != DependencyStrength.TRANSITIVE
        ]

        new_evidence = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="exp_001 was flawed",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.MISSING_TRANSITIVE_DEPENDENCY,
            authorization_id="auth_missing_transitive",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.7,
            test_passed=result.requires_governance_review,
            description="Missing transitive dependency - protocol should detect incomplete graph",
        )

    def _run_false_dependency(self) -> AdversarialResult:
        """Run false dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_false_dep",
            evidence_ids=["ev_001", "ev_fake"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Evidence that contradicts the false dependency
        new_evidence = Evidence(
            evidence_id="ev_003",
            evidence_type=EvidenceType.OBSERVATION,
            content="ev_fake is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.FALSE_DEPENDENCY,
            authorization_id="auth_false_dep",
            expected_decision=InvalidationDecision.SUSPEND,
            actual_decision=result.decision,
            dependency_graph_completeness=0.8,
            test_passed=result.decision == InvalidationDecision.SUSPEND,
            description="False dependency - protocol should detect contradiction",
        )

    def _run_over_broad_dependency(self) -> AdversarialResult:
        """Run over-broad dependency scenario."""
        # Build graph with many extra dependencies
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_over_broad",
            evidence_ids=["ev_001", "ev_002", "ev_003", "ev_004", "ev_005"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Add extra false dependencies
        for i in range(6, 11):
            auth_graph.add_dependency(AuthorizationDependency(
                dependency_id=f"dep_extra_{i}",
                dependency_type=DependencyType.EVIDENCE,
                target_id=f"ev_{i:03d}",
                description=f"Extra evidence {i}",
                strength=DependencyStrength.DIRECT,
            ))

        # Evidence that contradicts one of the extra dependencies
        new_evidence = Evidence(
            evidence_id="ev_010",
            evidence_type=EvidenceType.OBSERVATION,
            content="ev_010 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.OVER_BROAD_DEPENDENCY,
            authorization_id="auth_over_broad",
            expected_decision=InvalidationDecision.SUSPEND,
            actual_decision=result.decision,
            dependency_graph_completeness=0.5,
            test_passed=result.decision == InvalidationDecision.SUSPEND,
            description="Over-broad dependency - protocol should detect false positives",
        )

    def _run_stale_dependency(self) -> AdversarialResult:
        """Run stale dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_stale",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Mark a dependency as stale
        auth_graph.mark_stale(StalenessType.EPISTEMICALLY_STALE)

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is uncertain",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.STALE_DEPENDENCY,
            authorization_id="auth_stale",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.7,
            test_passed=result.requires_governance_review,
            description="Stale dependency - protocol should detect staleness",
        )

    def _run_ambiguous_dependency(self) -> AdversarialResult:
        """Run ambiguous dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_ambiguous",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Ambiguous evidence
        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 status is unclear",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.AMBIGUOUS_DEPENDENCY,
            authorization_id="auth_ambiguous",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.6,
            test_passed=result.requires_governance_review,
            description="Ambiguous dependency - protocol should detect ambiguity",
        )

    def _run_wrong_scope(self) -> AdversarialResult:
        """Run wrong scope scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_wrong_scope",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Evidence from wrong scope
        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 in different domain",
            timestamp="2026-01-01T00:00:00Z",
            source="external_domain",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.WRONG_SCOPE,
            authorization_id="auth_wrong_scope",
            expected_decision=InvalidationDecision.PRESERVE,
            actual_decision=result.decision,
            dependency_graph_completeness=0.9,
            test_passed=result.decision == InvalidationDecision.PRESERVE,
            description="Wrong scope - protocol should ignore out-of-scope evidence",
        )

    def _run_wrong_temporal(self) -> AdversarialResult:
        """Run wrong temporal scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_wrong_temporal",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Evidence from wrong temporal interval
        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 was different in historical state",
            timestamp="2020-01-01T00:00:00Z",
            source="historical_record",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.WRONG_TEMPORAL,
            authorization_id="auth_wrong_temporal",
            expected_decision=InvalidationDecision.PRESERVE,
            actual_decision=result.decision,
            dependency_graph_completeness=0.9,
            test_passed=result.decision == InvalidationDecision.PRESERVE,
            description="Wrong temporal - protocol should ignore historical evidence",
        )

    def _run_wrong_environment(self) -> AdversarialResult:
        """Run wrong environment scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_wrong_env",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Evidence from wrong environment
        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 in staging environment",
            timestamp="2026-01-01T00:00:00Z",
            source="staging",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.WRONG_ENVIRONMENT,
            authorization_id="auth_wrong_env",
            expected_decision=InvalidationDecision.PRESERVE,
            actual_decision=result.decision,
            dependency_graph_completeness=0.9,
            test_passed=result.decision == InvalidationDecision.PRESERVE,
            description="Wrong environment - protocol should ignore out-of-environment evidence",
        )

    def _run_runtime_discovery(self) -> AdversarialResult:
        """Run runtime discovery scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_runtime",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Runtime-discovered dependency
        new_evidence = Evidence(
            evidence_id="ev_runtime",
            evidence_type=EvidenceType.OBSERVATION,
            content="runtime dependency discovered",
            timestamp="2026-01-01T00:00:00Z",
            source="runtime_trace",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.RUNTIME_DISCOVERY,
            authorization_id="auth_runtime",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.6,
            test_passed=result.requires_governance_review,
            description="Runtime discovery - protocol should flag for reevaluation",
        )

    def _run_experiment_discovery(self) -> AdversarialResult:
        """Run experiment discovery scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_experiment",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Experiment-discovered dependency
        new_evidence = Evidence(
            evidence_id="ev_experiment",
            evidence_type=EvidenceType.EXPERIMENT_RESULT,
            content="experiment discovered new dependency",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.EXPERIMENT_DISCOVERY,
            authorization_id="auth_experiment",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.6,
            test_passed=result.requires_governance_review,
            description="Experiment discovery - protocol should flag for reevaluation",
        )

    def _run_post_authorization_discovery(self) -> AdversarialResult:
        """Run post-authorization discovery scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_post_auth",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Post-authorization discovery
        new_evidence = Evidence(
            evidence_id="ev_post_auth",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is contradicted by new data",
            timestamp="2026-06-01T00:00:00Z",
            source="post_authorization_discovery",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.POST_AUTHORIZATION_DISCOVERY,
            authorization_id="auth_post_auth",
            expected_decision=InvalidationDecision.SUSPEND,
            actual_decision=result.decision,
            dependency_graph_completeness=0.5,
            test_passed=result.decision == InvalidationDecision.SUSPEND,
            description="Post-authorization discovery - protocol should suspend",
        )

    def _run_contradicted_dependency(self) -> AdversarialResult:
        """Run contradicted dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_contradicted",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Contradictory evidence
        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="prop_001 is not valid",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.CONTRADICTED_DEPENDENCY,
            authorization_id="auth_contradicted",
            expected_decision=InvalidationDecision.SUSPEND,
            actual_decision=result.decision,
            dependency_graph_completeness=0.8,
            test_passed=result.decision == InvalidationDecision.SUSPEND,
            description="Contradicted dependency - protocol should suspend",
        )

    def _run_incomplete_provenance(self) -> AdversarialResult:
        """Run incomplete provenance scenario."""
        # Build graph with incomplete provenance
        auth_graph = AuthorizationDependencyGraph(
            authorization_id="auth_incomplete_prov",
            timestamp=datetime.utcnow().isoformat(),
            dependencies=[],
            provenance=[],  # Empty provenance
        )

        # Add a dependency with no provenance
        auth_graph.add_dependency(AuthorizationDependency(
            dependency_id="dep_001",
            dependency_type=DependencyType.EVIDENCE,
            target_id="ev_001",
            description="Evidence with no provenance",
            provenance=[],  # No provenance
        ))

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="ev_001 is uncertain",
            timestamp="2026-01-01T00:00:00Z",
            source="experiment",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.INCOMPLETE_PROVENANCE,
            authorization_id="auth_incomplete_prov",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.3,
            test_passed=result.requires_governance_review,
            description="Incomplete provenance - protocol should flag for reevaluation",
        )

    def _run_cross_domain_dependency(self) -> AdversarialResult:
        """Run cross-domain dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_cross_domain",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Add cross-domain dependency
        auth_graph.add_dependency(AuthorizationDependency(
            dependency_id="dep_cross_domain",
            dependency_type=DependencyType.ACTOR_IDENTITY,
            target_id="identity_service",
            description="Cross-domain dependency",
            provenance=["identity_domain"],
        ))

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="identity_service changed",
            timestamp="2026-01-01T00:00:00Z",
            source="identity_domain",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.CROSS_DOMAIN_DEPENDENCY,
            authorization_id="auth_cross_domain",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.7,
            test_passed=result.requires_governance_review,
            description="Cross-domain dependency - protocol should flag for reevaluation",
        )

    def _run_feature_flag_dependency(self) -> AdversarialResult:
        """Run feature flag dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_feature_flag",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Feature flag dependency
        auth_graph.add_dependency(AuthorizationDependency(
            dependency_id="dep_feature_flag",
            dependency_type=DependencyType.ENVIRONMENT,
            target_id="feature_flag_enabled",
            description="Feature flag dependency",
            provenance=["feature_flags"],
        ))

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="feature_flag_enabled changed",
            timestamp="2026-01-01T00:00:00Z",
            source="feature_flags",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.FEATURE_FLAG_DEPENDENCY,
            authorization_id="auth_feature_flag",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.7,
            test_passed=result.requires_governance_review,
            description="Feature flag dependency - protocol should flag for reevaluation",
        )

    def _run_failure_only_dependency(self) -> AdversarialResult:
        """Run failure-only dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_failure_only",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Failure-only dependency
        auth_graph.add_dependency(AuthorizationDependency(
            dependency_id="dep_failure",
            dependency_type=DependencyType.ENVIRONMENT,
            target_id="failure_condition",
            description="Failure-only dependency",
            provenance=["failure_detection"],
        ))

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="failure_condition detected",
            timestamp="2026-01-01T00:00:00Z",
            source="failure_detection",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.FAILURE_ONLY_DEPENDENCY,
            authorization_id="auth_failure_only",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.6,
            test_passed=result.requires_governance_review,
            description="Failure-only dependency - protocol should flag for reevaluation",
        )

    def _run_single_operation_dependency(self) -> AdversarialResult:
        """Run single operation dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_single_op",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Single operation dependency
        auth_graph.add_dependency(AuthorizationDependency(
            dependency_id="dep_single_op",
            dependency_type=DependencyType.CAPABILITY_CONSTRAINT,
            target_id="single_operation",
            description="Single operation dependency",
            provenance=["operation_constraint"],
        ))

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="single_operation constraint changed",
            timestamp="2026-01-01T00:00:00Z",
            source="operation",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.SINGLE_OPERATION_DEPENDENCY,
            authorization_id="auth_single_op",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.7,
            test_passed=result.requires_governance_review,
            description="Single operation dependency - protocol should flag for reevaluation",
        )

    def _run_single_actor_dependency(self) -> AdversarialResult:
        """Run single actor dependency scenario."""
        auth_graph = build_authorization_dependency_graph(
            authorization_id="auth_single_actor",
            evidence_ids=["ev_001"],
            proposition_id="prop_001",
            epistemic_state_id="es_001",
            experiment_id="exp_001",
            recommendation_id="rec_001",
            governance_policy_id="gov_001",
            resource_id="provider_a",
            temporal_interval="2026-01-01/2027-01-01",
            provenance=["source_001"],
        )

        # Single actor dependency
        auth_graph.add_dependency(AuthorizationDependency(
            dependency_id="dep_single_actor",
            dependency_type=DependencyType.ACTOR_IDENTITY,
            target_id="actor_001",
            description="Single actor dependency",
            provenance=["actor_management"],
        ))

        new_evidence = Evidence(
            evidence_id="ev_002",
            evidence_type=EvidenceType.OBSERVATION,
            content="actor_001 changed",
            timestamp="2026-01-01T00:00:00Z",
            source="actor_management",
        )

        engine = EpistemicInvalidationEngine()
        result = engine.evaluate_invalidation(auth_graph, [new_evidence])

        return AdversarialResult(
            scenario=AdversarialScenario.SINGLE_ACTOR_DEPENDENCY,
            authorization_id="auth_single_actor",
            expected_decision=InvalidationDecision.REQUIRE_REEVALUATION,
            actual_decision=result.decision,
            dependency_graph_completeness=0.7,
            test_passed=result.requires_governance_review,
            description="Single actor dependency - protocol should flag for reevaluation",
        )


def run_all_adversarial_scenarios() -> list[AdversarialResult]:
    """Run all adversarial validation scenarios."""
    engine = AdversarialValidationEngine()
    results = []
    for scenario in AdversarialScenario:
        result = engine.run_scenario(scenario)
        results.append(result)
    return results
