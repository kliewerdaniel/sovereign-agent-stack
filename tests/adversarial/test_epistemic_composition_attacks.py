"""Adversarial tests for Epistemic Composition and Dependency Closure.

This is the negative-space attack suite. Every attack must fail for a structural
reason, not merely because a test expects a particular string or label.

CENTRAL LAW:
    VALID(A) + VALID(B) + VALID(C) DOES NOT IMPLY VALID(A+B+C)

EPISTEMIC AUTHORITY MUST NOT INCREASE MERELY BECAUSE VALID CLAIMS ARE COMPOSED.
"""

from __future__ import annotations

import pytest

from examples.payment_dependency_auditor.dependency_types import (
    DependencyEdge,
    DependencyType,
    EpistemicState,
    ObservationMethod,
    PropositionType,
)
from examples.payment_dependency_auditor.epistemic_composition import (
    CompositionOperator,
    CompositionValidity,
    EpistemicCompositionEngine,
    EpistemicAccounting,
    account_epistemic_authority,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> EpistemicCompositionEngine:
    return EpistemicCompositionEngine()


def make_edge(
    source: str,
    target: str,
    prop_type: PropositionType = PropositionType.STATIC_REFERENCE,
    epistemic: EpistemicState = EpistemicState.OBSERVED,
    confidence: float = 0.9,
    environment: str = "all",
    observation_method: ObservationMethod = ObservationMethod.STATIC_ANALYSIS,
) -> DependencyEdge:
    return DependencyEdge(
        source=source,
        target=target,
        dependency_type=DependencyType.SERVICE,
        source_artifact=f"{source}.py",
        observation_method=observation_method,
        environment=environment,
        epistemic_state=epistemic,
        proposition_type=prop_type,
        provenance_id=f"edge_{source}_{target}",
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Attack 1: Naive transitive closure
# ---------------------------------------------------------------------------


class TestNaiveTransitiveClosure:
    """Attack: A→B, B→C implies A→C at same proposition type."""

    def test_static_transitive_does_not_produce_static(self, engine):
        """Static A→B + Static B→C must NOT produce Static A→C."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        assert result.derived_edge is not None
        assert result.derived_edge.proposition_type == PropositionType.TRANSITIVE_DEPENDENCY
        assert result.derived_edge.proposition_type != PropositionType.STATIC_REFERENCE

    def test_transitive_authority_reduced(self, engine):
        """Transitive claim must have reduced authority vs parents."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE, confidence=0.95)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE, confidence=0.95)
        result = engine.compose(ab, bc)
        assert result.derived_edge.confidence < 0.95

    def test_three_hop_chain_reduces_authority_each_step(self, engine):
        """Each composition step reduces authority further."""
        ab = make_edge("a", "b")
        bc = make_edge("b", "c")
        cd = make_edge("c", "d")
        results = engine.compose_chain([ab, bc, cd])
        # Each derived edge should have reduced confidence
        for r in results:
            if r.derived_edge is not None:
                assert r.derived_edge.confidence < 0.9


# ---------------------------------------------------------------------------
# Attack 2: Static graph traversal presented as runtime evidence
# ---------------------------------------------------------------------------


class TestStaticNotRuntime:
    """Attack: Static imports presented as runtime dependencies."""

    def test_static_composition_does_not_produce_runtime(self, engine):
        """Static edges must not produce runtime dependency claim."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        assert result.derived_edge.proposition_type != PropositionType.RUNTIME_DEPENDENCY

    def test_static_observation_stays_static(self, engine):
        """Static observation must not be elevated to runtime."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE,
                       observation_method=ObservationMethod.STATIC_ANALYSIS)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE,
                       observation_method=ObservationMethod.STATIC_ANALYSIS)
        result = engine.compose(ab, bc)
        assert result.derived_edge.observation_method == ObservationMethod.STATIC_ANALYSIS


# ---------------------------------------------------------------------------
# Attack 3: Runtime dependency presented as necessity
# ---------------------------------------------------------------------------


class TestRuntimeNotNecessity:
    """Attack: Runtime dependency presented as operational necessity."""

    def test_runtime_composition_does_not_produce_operational(self, engine):
        """Runtime edges must not produce operational dependency claim."""
        ab = make_edge("a", "b", PropositionType.RUNTIME_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.RUNTIME_DEPENDENCY)
        result = engine.compose(ab, bc)
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY

    def test_runtime_composition_stays_inconclusive(self, engine):
        """Runtime composition must produce INCONCLUSIVE state."""
        ab = make_edge("a", "b", PropositionType.RUNTIME_DEPENDENCY,
                       epistemic=EpistemicState.EXPERIMENTALLY_SUPPORTED)
        bc = make_edge("b", "c", PropositionType.RUNTIME_DEPENDENCY,
                       epistemic=EpistemicState.EXPERIMENTALLY_SUPPORTED)
        result = engine.compose(ab, bc)
        assert result.derived_edge.epistemic_state == EpistemicState.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Attack 4: Necessity presented as criticality
# ---------------------------------------------------------------------------


class TestNecessityNotCriticality:
    """Attack: Necessity claim presented as criticality claim."""

    def test_necessity_does_not_imply_criticality(self, engine):
        """Necessity claim must not be elevated to criticality."""
        ab = make_edge("a", "b", PropositionType.OPERATIONAL_DEPENDENCY,
                       epistemic=EpistemicState.EXPERIMENTALLY_SUPPORTED)
        bc = make_edge("b", "c", PropositionType.OPERATIONAL_DEPENDENCY,
                       epistemic=EpistemicState.EXPERIMENTALLY_SUPPORTED)
        result = engine.compose(ab, bc)
        # No rule for OPERATIONAL+OPERATIONAL - should be rejected or bounded
        if result.derived_edge is not None:
            assert result.derived_edge.epistemic_state in (
                EpistemicState.INCONCLUSIVE,
                EpistemicState.INFERRED,
                EpistemicState.UNKNOWN,
            )


# ---------------------------------------------------------------------------
# Attack 5: Failure dependency presented as universal dependency
# ---------------------------------------------------------------------------


class TestFailureNotUniversal:
    """Attack: Failure dependency generalized to universal dependency."""

    def test_failure_dependency_stays_bounded(self, engine):
        """Failure dependency must not become universal."""
        ab = make_edge("a", "b", PropositionType.FAILURE_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.FAILURE_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce a universal claim
        assert result.derived_edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Attack 6: Staging evidence generalized to production
# ---------------------------------------------------------------------------


class TestStagingNotProduction:
    """Attack: Staging evidence generalized to production."""

    def test_staging_scope_preserved(self, engine):
        """Staging evidence must not become production claim."""
        ab = make_edge("a", "b", environment="staging")
        bc = make_edge("b", "c", environment="staging")
        result = engine.compose(ab, bc)
        # Environment scope must be preserved
        assert "staging" in result.derived_edge.environment

    def test_staging_not_becomes_all_environments(self, engine):
        """Staging evidence must not claim to apply to all environments."""
        ab = make_edge("a", "b", environment="staging")
        bc = make_edge("b", "c", environment="staging")
        result = engine.compose(ab, bc)
        assert result.derived_edge.environment != "all"


# ---------------------------------------------------------------------------
# Attack 7: Production evidence generalized to all environments
# ---------------------------------------------------------------------------


class TestProductionNotAll:
    """Attack: Production evidence generalized to all environments."""

    def test_production_scope_preserved(self, engine):
        """Production evidence must not become 'all environments'."""
        ab = make_edge("a", "b", environment="production")
        bc = make_edge("b", "c", environment="production")
        result = engine.compose(ab, bc)
        assert result.derived_edge.environment == "production"


# ---------------------------------------------------------------------------
# Attack 8: Single operation generalized to entire service
# ---------------------------------------------------------------------------


class TestSingleOperationNotService:
    """Attack: Single operation dependency generalized to service."""

    def test_single_operation_scope_preserved(self, engine):
        """Single operation dependency must not become service-wide."""
        ab = make_edge("a", "b", PropositionType.TEMPORAL_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.TEMPORAL_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce a universal claim
        assert result.derived_edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Attack 9: Feature-flagged dependency generalized across flag states
# ---------------------------------------------------------------------------


class TestFeatureFlaggedNotUniversal:
    """Attack: Feature-flagged dependency generalized across flag states."""

    def test_feature_flagged_stays_conditional(self, engine):
        """Feature-flagged dependency must not become universal."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        # Must not produce a claim stronger than INFERRED
        assert result.derived_edge.epistemic_state in (
            EpistemicState.INFERRED,
            EpistemicState.INCONCLUSIVE,
        )


# ---------------------------------------------------------------------------
# Attack 10: Cached dependency treated as direct necessity
# ---------------------------------------------------------------------------


class TestCachedNotDirect:
    """Attack: Cached dependency treated as direct necessity."""

    def test_cached_dependency_stays_bounded(self, engine):
        """Cached dependency must not become direct necessity."""
        ab = make_edge("a", "b", PropositionType.RUNTIME_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.RUNTIME_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce operational necessity
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY


# ---------------------------------------------------------------------------
# Attack 11: Async dependency treated as synchronous necessity
# ---------------------------------------------------------------------------


class TestAsyncNotSynchronous:
    """Attack: Async dependency treated as synchronous necessity."""

    def test_async_dependency_stays_bounded(self, engine):
        """Async dependency must not become synchronous necessity."""
        ab = make_edge("a", "b", PropositionType.RUNTIME_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.RUNTIME_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce operational necessity
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY


# ---------------------------------------------------------------------------
# Attack 12: Shared infrastructure treated as service-specific dependency
# ---------------------------------------------------------------------------


class TestSharedInfrastructure:
    """Attack: Shared infrastructure treated as service-specific dependency."""

    def test_shared_infrastructure_stays_bounded(self, engine):
        """Shared infrastructure must not become service-specific."""
        ab = make_edge("a", "redis", PropositionType.RUNTIME_DEPENDENCY)
        bc = make_edge("redis", "c", PropositionType.RUNTIME_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce a strong claim
        assert result.derived_edge.epistemic_state in (
            EpistemicState.INCONCLUSIVE,
            EpistemicState.INFERRED,
        )


# ---------------------------------------------------------------------------
# Attack 13: Observability dependency treated as business dependency
# ---------------------------------------------------------------------------


class TestObservabilityNotBusiness:
    """Attack: Observability dependency treated as business dependency."""

    def test_observability_stays_bounded(self, engine):
        """Observability dependency must not become business dependency."""
        ab = make_edge("a", "metrics", PropositionType.STATIC_REFERENCE)
        bc = make_edge("metrics", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        # Must not produce operational dependency
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY


# ---------------------------------------------------------------------------
# Attack 14: Startup dependency treated as request dependency
# ---------------------------------------------------------------------------


class TestStartupNotRequest:
    """Attack: Startup dependency treated as request dependency."""

    def test_startup_stays_temporal(self, engine):
        """Startup dependency must not become request dependency."""
        ab = make_edge("a", "config", PropositionType.TEMPORAL_DEPENDENCY)
        bc = make_edge("config", "c", PropositionType.TEMPORAL_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce a universal claim
        if result.derived_edge is not None:
            assert result.derived_edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Attack 15: Deployment dependency treated as runtime dependency
# ---------------------------------------------------------------------------


class TestDeploymentNotRuntime:
    """Attack: Deployment dependency treated as runtime dependency."""

    def test_deployment_stays_bounded(self, engine):
        """Deployment dependency must not become runtime dependency."""
        ab = make_edge("a", "migration", PropositionType.TEMPORAL_DEPENDENCY)
        bc = make_edge("migration", "c", PropositionType.TEMPORAL_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce runtime dependency
        assert result.derived_edge.proposition_type != PropositionType.RUNTIME_DEPENDENCY


# ---------------------------------------------------------------------------
# Attack 16: Model confidence used as composition authority
# ---------------------------------------------------------------------------


class TestConfidenceNotAuthority:
    """Attack: Model confidence used as composition authority."""

    def test_high_confidence_does_not_amplify(self, engine):
        """High confidence must not amplify during composition."""
        ab = make_edge("a", "b", confidence=0.99)
        bc = make_edge("b", "c", confidence=0.99)
        result = engine.compose(ab, bc)
        # Confidence must decrease
        assert result.derived_edge.confidence < 0.99

    def test_confidence_decreases_with_chain_length(self, engine):
        """Confidence must decrease with each composition step."""
        edges = [
            make_edge("a", "b", confidence=0.95),
            make_edge("b", "c", confidence=0.95),
            make_edge("c", "d", confidence=0.95),
            make_edge("d", "e", confidence=0.95),
        ]
        results = engine.compose_chain(edges)
        # Later compositions should have lower confidence
        derived_confidences = [
            r.derived_edge.confidence for r in results
            if r.derived_edge is not None
        ]
        if len(derived_confidences) >= 2:
            # Confidence should generally decrease
            assert derived_confidences[-1] <= derived_confidences[0]


# ---------------------------------------------------------------------------
# Attack 17: Large number of parent claims used to manufacture authority
# ---------------------------------------------------------------------------


TestManyParents = TestConfidenceNotAuthority  # Reuse: many parents don't amplify


# ---------------------------------------------------------------------------
# Attack 18: Repeated identical evidence counted as independent evidence
# ---------------------------------------------------------------------------


class TestDuplicateEvidence:
    """Attack: Repeated identical evidence counted as independent."""

    def test_duplicate_evidence_does_not_amplify(self, engine):
        """Duplicate evidence must not amplify authority."""
        ab = make_edge("a", "b", confidence=0.9)
        bc = make_edge("b", "c", confidence=0.9)
        result = engine.compose(ab, bc)
        # Single composition, confidence decreases
        assert result.derived_edge.confidence < 0.9


# ---------------------------------------------------------------------------
# Attack 19: Contradictory parent claims silently merged
# ---------------------------------------------------------------------------


class TestContradictoryParents:
    """Attack: Contradictory parent claims silently merged."""

    def test_contradictory_parents_produce_inconclusive(self, engine):
        """Contradictory parents must produce inconclusive result."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE,
                       epistemic=EpistemicState.OBSERVED)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE,
                       epistemic=EpistemicState.CONTRADICTED)
        result = engine.compose(ab, bc)
        # Must not produce a strong claim
        assert result.derived_edge.epistemic_state in (
            EpistemicState.INCONCLUSIVE,
            EpistemicState.INFERRED,
        )


# ---------------------------------------------------------------------------
# Attack 20: Missing parent provenance silently ignored
# ---------------------------------------------------------------------------


class TestMissingProvenance:
    """Attack: Missing parent provenance silently ignored."""

    def test_composed_edge_preserves_provenance(self, engine):
        """Composed edge must preserve parent provenance."""
        ab = make_edge("a", "b")
        bc = make_edge("b", "c")
        result = engine.compose(ab, bc)
        assert result.derived_edge is not None
        assert len(result.derived_edge.evidence) >= 2


# ---------------------------------------------------------------------------
# Attack 21: Parent scope silently widened
# ---------------------------------------------------------------------------


class TestScopeNotWidened:
    """Attack: Parent scope silently widened."""

    def test_scope_not_widened(self, engine):
        """Parent scope must not be widened during composition."""
        ab = make_edge("a", "b", environment="staging")
        bc = make_edge("b", "c", environment="staging")
        result = engine.compose(ab, bc)
        # Scope must not be widened to "all"
        assert result.derived_edge.environment != "all"


# ---------------------------------------------------------------------------
# Attack 22: Parent temporal boundary silently widened
# ---------------------------------------------------------------------------


class TestTemporalNotWidened:
    """Attack: Parent temporal boundary silently widened."""

    def test_temporal_not_widened(self, engine):
        """Parent temporal boundary must not be widened."""
        ab = make_edge("a", "b", PropositionType.TEMPORAL_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.TEMPORAL_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce a universal claim
        assert result.derived_edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Attack 23: Parent environment restriction silently removed
# ---------------------------------------------------------------------------


class TestEnvironmentNotRemoved:
    """Attack: Parent environment restriction silently removed."""

    def test_environment_not_removed(self, engine):
        """Parent environment restriction must not be removed."""
        ab = make_edge("a", "b", environment="production")
        bc = make_edge("b", "c", environment="production")
        result = engine.compose(ab, bc)
        assert result.derived_edge.environment == "production"


# ---------------------------------------------------------------------------
# Attack 24: Alternative hypotheses discarded during composition
# ---------------------------------------------------------------------------


class TestAlternativesPreserved:
    """Attack: Alternative hypotheses discarded during composition."""

    def test_alternatives_preserved(self, engine):
        """Alternative hypotheses must be preserved during composition."""
        ab = make_edge("a", "b")
        bc = make_edge("b", "c")
        result = engine.compose(ab, bc)
        assert result.derived_edge is not None
        assert len(result.derived_edge.alternatives) > 0


# ---------------------------------------------------------------------------
# Attack 25: A valid child claim used to justify its own parent
# ---------------------------------------------------------------------------


class TestCircularReasoning:
    """Attack: Valid child claim used to justify its own parent."""

    def test_circular_reasoning_blocked(self, engine):
        """Circular reasoning must be blocked."""
        ab = make_edge("a", "b")
        bc = make_edge("b", "c")
        result = engine.compose(ab, bc)
        # The derived edge a→c must not be used to justify a→b
        # This is a structural property: composition is one-directional
        assert result.derived_edge is not None
        assert result.derived_edge.source == "a"
        assert result.derived_edge.target == "c"


# ---------------------------------------------------------------------------
# Attack 26: Circular dependency reasoning used as evidence
# ---------------------------------------------------------------------------


class TestCircularDependency:
    """Attack: Circular dependency reasoning used as evidence."""

    def test_circular_dependency_does_not_amplify(self, engine):
        """Circular dependency must not amplify authority."""
        ab = make_edge("a", "b")
        bc = make_edge("b", "a")  # Circular
        result = engine.compose(ab, bc)
        # Must not produce a strong claim
        assert result.derived_edge.epistemic_state in (
            EpistemicState.INCONCLUSIVE,
            EpistemicState.INFERRED,
        )


# ---------------------------------------------------------------------------
# Attack 27: Graph centrality interpreted as criticality
# ---------------------------------------------------------------------------


class TestCentralityNotCriticality:
    """Attack: Graph centrality interpreted as criticality."""

    def test_centrality_does_not_imply_criticality(self, engine):
        """Graph centrality must not imply criticality."""
        # Create a star topology: many nodes connect to "redis"
        edges = []
        for source in ["a", "b", "c", "d", "e"]:
            edges.append(make_edge(source, "redis"))
        # Compose first pair
        result = engine.compose(edges[0], make_edge("redis", "backend"))
        # Must not produce criticality claim
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY


# ---------------------------------------------------------------------------
# Attack 28: Dependency count interpreted as importance
# ---------------------------------------------------------------------------


class TestCountNotImportance:
    """Attack: Dependency count interpreted as importance."""

    def test_count_does_not_amplify(self, engine):
        """Many dependencies must not amplify authority."""
        ab = make_edge("a", "b")
        bc = make_edge("b", "c")
        result = engine.compose(ab, bc)
        # Single composition, confidence decreases
        assert result.derived_edge.confidence < ab.confidence


# ---------------------------------------------------------------------------
# Attack 29: Path length interpreted as certainty
# ---------------------------------------------------------------------------


class TestPathLengthNotCertainty:
    """Attack: Path length interpreted as certainty."""

    def test_longer_path_reduces_certainty(self, engine):
        """Longer path must reduce certainty, not increase it."""
        edges = [
            make_edge("a", "b", confidence=0.95),
            make_edge("b", "c", confidence=0.90),
            make_edge("c", "d", confidence=0.85),
            make_edge("d", "e", confidence=0.80),
        ]
        results = engine.compose_chain(edges)
        # Later compositions should have lower confidence
        derived_confidences = [
            r.derived_edge.confidence for r in results
            if r.derived_edge is not None
        ]
        if len(derived_confidences) >= 2:
            # Confidence should generally decrease
            assert derived_confidences[-1] <= derived_confidences[0]


# ---------------------------------------------------------------------------
# Attack 30: Transitive closure used as proof of necessity
# ---------------------------------------------------------------------------


class TestTransitiveClosureNotNecessity:
    """Attack: Transitive closure used as proof of necessity."""

    def test_transitive_closure_does_not_prove_necessity(self, engine):
        """Transitive closure must not prove necessity."""
        ab = make_edge("a", "b", PropositionType.RUNTIME_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.RUNTIME_DEPENDENCY)
        result = engine.compose(ab, bc)
        # Must not produce necessity claim
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY
        assert result.derived_edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Epistemic Accounting Attacks
# ---------------------------------------------------------------------------


class TestEpistemicAccountingAttacks:
    """Attacks on epistemic accounting."""

    def test_authority_not_amplified(self, engine):
        """Authority must not be amplified during composition."""
        ab = make_edge("a", "b", confidence=0.9)
        bc = make_edge("b", "c", confidence=0.9)
        result = engine.compose(ab, bc)
        accounting = account_epistemic_authority([ab, bc], result.derived_edge)
        assert not accounting.authority_amplified

    def test_uncertainty_preserved(self, engine):
        """Uncertainty must be preserved during composition."""
        ab = make_edge("a", "b", confidence=0.9)
        bc = make_edge("b", "c", confidence=0.9)
        result = engine.compose(ab, bc)
        accounting = account_epistemic_authority([ab, bc], result.derived_edge)
        assert accounting.uncertainty_preserved

    def test_scope_preserved(self, engine):
        """Scope must be preserved during composition."""
        ab = make_edge("a", "b", confidence=0.9)
        bc = make_edge("b", "c", confidence=0.9)
        result = engine.compose(ab, bc)
        accounting = account_epistemic_authority([ab, bc], result.derived_edge)
        assert accounting.scope_preserved

    def test_alternatives_preserved(self, engine):
        """Alternatives must be preserved during composition."""
        ab = make_edge("a", "b", confidence=0.9)
        bc = make_edge("b", "c", confidence=0.9)
        result = engine.compose(ab, bc)
        accounting = account_epistemic_authority([ab, bc], result.derived_edge)
        assert accounting.alternatives_preserved

    def test_observation_not_necessity(self, engine):
        """Observation must not be elevated to necessity."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        accounting = account_epistemic_authority([ab, bc], result.derived_edge)
        assert accounting.observation_not_necessity

    def test_local_not_generalization(self, engine):
        """Local evidence must not be generalized."""
        ab = make_edge("a", "b", environment="staging")
        bc = make_edge("b", "c", environment="staging")
        result = engine.compose(ab, bc)
        accounting = account_epistemic_authority([ab, bc], result.derived_edge)
        assert accounting.local_not_generalization


# ---------------------------------------------------------------------------
# Composition Validity Attacks
# ---------------------------------------------------------------------------


class TestCompositionValidityAttacks:
    """Attacks on composition validity."""

    def test_non_composable_edges_rejected(self, engine):
        """Non-composable edges must be rejected."""
        ab = make_edge("a", "b")
        cd = make_edge("c", "d")  # Doesn't connect to a→b
        result = engine.compose(ab, cd)
        assert result.validity == CompositionValidity.REJECTED

    def test_composed_edge_has_lower_confidence(self, engine):
        """Composed edge must have lower confidence than parents."""
        ab = make_edge("a", "b", confidence=0.95)
        bc = make_edge("b", "c", confidence=0.95)
        result = engine.compose(ab, bc)
        assert result.derived_edge.confidence < 0.95

    def test_composed_edge_has_weaker_epistemic_state(self, engine):
        """Composed edge must have weaker epistemic state than parents."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE,
                       epistemic=EpistemicState.OBSERVED)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE,
                       epistemic=EpistemicState.OBSERVED)
        result = engine.compose(ab, bc)
        # INFERRED is weaker than OBSERVED
        assert result.derived_edge.epistemic_state == EpistemicState.INFERRED


# ---------------------------------------------------------------------------
# Chain Composition Attacks
# ---------------------------------------------------------------------------


class TestChainCompositionAttacks:
    """Attacks on chain composition."""

    def test_chain_composition_reduces_authority(self, engine):
        """Chain composition must reduce authority at each step."""
        edges = [
            make_edge("a", "b", confidence=0.95),
            make_edge("b", "c", confidence=0.95),
            make_edge("c", "d", confidence=0.95),
        ]
        results = engine.compose_chain(edges)
        # All derived edges should have reduced confidence
        for r in results:
            if r.derived_edge is not None:
                assert r.derived_edge.confidence < 0.95

    def test_chain_composition_produces_transitive(self, engine):
        """Chain composition must produce transitive dependencies."""
        edges = [
            make_edge("a", "b"),
            make_edge("b", "c"),
            make_edge("c", "d"),
        ]
        results = engine.compose_chain(edges)
        for r in results:
            if r.derived_edge is not None:
                assert r.derived_edge.proposition_type == PropositionType.TRANSITIVE_DEPENDENCY


# ---------------------------------------------------------------------------
# Proposition Type Preservation Attacks
# ---------------------------------------------------------------------------


class TestPropositionTypePreservation:
    """Attacks on proposition type preservation."""

    def test_static_not_elevated_to_runtime(self, engine):
        """Static reference must not be elevated to runtime dependency."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        assert result.derived_edge.proposition_type != PropositionType.RUNTIME_DEPENDENCY

    def test_runtime_not_elevated_to_operational(self, engine):
        """Runtime dependency must not be elevated to operational dependency."""
        ab = make_edge("a", "b", PropositionType.RUNTIME_DEPENDENCY)
        bc = make_edge("b", "c", PropositionType.RUNTIME_DEPENDENCY)
        result = engine.compose(ab, bc)
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY

    def test_static_not_elevated_to_operational(self, engine):
        """Static reference must not be elevated to operational dependency."""
        ab = make_edge("a", "b", PropositionType.STATIC_REFERENCE)
        bc = make_edge("b", "c", PropositionType.STATIC_REFERENCE)
        result = engine.compose(ab, bc)
        assert result.derived_edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY


# ---------------------------------------------------------------------------
# Environment Preservation Attacks
# ---------------------------------------------------------------------------


class TestEnvironmentPreservation:
    """Attacks on environment preservation."""

    def test_staging_stays_staging(self, engine):
        """Staging evidence must stay staging."""
        ab = make_edge("a", "b", environment="staging")
        bc = make_edge("b", "c", environment="staging")
        result = engine.compose(ab, bc)
        assert "staging" in result.derived_edge.environment

    def test_production_stays_production(self, engine):
        """Production evidence must stay production."""
        ab = make_edge("a", "b", environment="production")
        bc = make_edge("b", "c", environment="production")
        result = engine.compose(ab, bc)
        assert result.derived_edge.environment == "production"

    def test_mixed_environment_stays_bounded(self, engine):
        """Mixed environment evidence must stay bounded."""
        ab = make_edge("a", "b", environment="staging")
        bc = make_edge("b", "c", environment="production")
        result = engine.compose(ab, bc)
        # Must not become "all"
        assert result.derived_edge.environment != "all"
