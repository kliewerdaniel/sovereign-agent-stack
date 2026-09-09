"""Integration tests for the Epistemic Composition Engine."""

from __future__ import annotations

from pathlib import Path

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
    account_epistemic_authority,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> EpistemicCompositionEngine:
    return EpistemicCompositionEngine()


@pytest.fixture
def static_edge_ab() -> DependencyEdge:
    return DependencyEdge(
        source="checkout",
        target="payments",
        dependency_type=DependencyType.SERVICE,
        source_artifact="checkout.py",
        observation_method=ObservationMethod.STATIC_ANALYSIS,
        epistemic_state=EpistemicState.OBSERVED,
        proposition_type=PropositionType.STATIC_REFERENCE,
        provenance_id="edge_ab_1",
        confidence=0.9,
    )


@pytest.fixture
def static_edge_bc() -> DependencyEdge:
    return DependencyEdge(
        source="payments",
        target="ledger",
        dependency_type=DependencyType.SERVICE,
        source_artifact="payments.py",
        observation_method=ObservationMethod.STATIC_ANALYSIS,
        epistemic_state=EpistemicState.OBSERVED,
        proposition_type=PropositionType.STATIC_REFERENCE,
        provenance_id="edge_bc_1",
        confidence=0.9,
    )


@pytest.fixture
def runtime_edge_ab() -> DependencyEdge:
    return DependencyEdge(
        source="checkout",
        target="payments",
        dependency_type=DependencyType.SERVICE,
        source_artifact="checkout.py",
        observation_method=ObservationMethod.RUNTIME_TEST,
        epistemic_state=EpistemicState.EXPERIMENTALLY_SUPPORTED,
        proposition_type=PropositionType.RUNTIME_DEPENDENCY,
        provenance_id="edge_ab_runtime",
        confidence=0.85,
    )


@pytest.fixture
def runtime_edge_bc() -> DependencyEdge:
    return DependencyEdge(
        source="payments",
        target="ledger",
        dependency_type=DependencyType.SERVICE,
        source_artifact="payments.py",
        observation_method=ObservationMethod.RUNTIME_TEST,
        epistemic_state=EpistemicState.EXPERIMENTALLY_SUPPORTED,
        proposition_type=PropositionType.RUNTIME_DEPENDENCY,
        provenance_id="edge_bc_runtime",
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# Composition Tests
# ---------------------------------------------------------------------------


class TestComposition:
    """Tests for basic composition functionality."""

    def test_compose_static_edges(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composing two static edges should produce a transitive dependency."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.source == "checkout"
        assert result.derived_edge.target == "ledger"
        assert result.derived_edge.proposition_type == PropositionType.TRANSITIVE_DEPENDENCY

    def test_compose_preserves_source_target(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition should preserve source from first edge and target from second."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.source == static_edge_ab.source
        assert result.derived_edge.target == static_edge_bc.target

    def test_compose_reduces_authority(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition should reduce authority (confidence)."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.confidence < static_edge_ab.confidence
        assert result.derived_edge.confidence < static_edge_bc.confidence

    def test_compose_non_composable_edges(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
    ):
        """Edges with non-matching intermediate nodes should be rejected."""
        edge_bc = DependencyEdge(
            source="other",  # Doesn't match edge_ab.target ("payments")
            target="ledger",
            dependency_type=DependencyType.SERVICE,
            source_artifact="other.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            provenance_id="edge_other",
            confidence=0.9,
        )
        result = engine.compose(static_edge_ab, edge_bc)
        assert result.validity == CompositionValidity.REJECTED
        assert result.derived_edge is None

    def test_compose_runtime_edges(
        self,
        engine: EpistemicCompositionEngine,
        runtime_edge_ab: DependencyEdge,
        runtime_edge_bc: DependencyEdge,
    ):
        """Composing runtime edges should produce transitive dependency."""
        result = engine.compose(runtime_edge_ab, runtime_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.proposition_type == PropositionType.TRANSITIVE_DEPENDENCY

    def test_compose_mixed_types(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        runtime_edge_bc: DependencyEdge,
    ):
        """Composing static with runtime should still produce a result."""
        result = engine.compose(static_edge_ab, runtime_edge_bc)
        assert result.derived_edge is not None

    def test_compose_chain(
        self,
        engine: EpistemicCompositionEngine,
    ):
        """Composing a chain of edges should produce multiple results."""
        edges = [
            DependencyEdge(
                source="a", target="b",
                dependency_type=DependencyType.SERVICE,
                source_artifact="a.py",
                observation_method=ObservationMethod.STATIC_ANALYSIS,
                epistemic_state=EpistemicState.OBSERVED,
                proposition_type=PropositionType.STATIC_REFERENCE,
                provenance_id="e1",
                confidence=0.9,
            ),
            DependencyEdge(
                source="b", target="c",
                dependency_type=DependencyType.SERVICE,
                source_artifact="b.py",
                observation_method=ObservationMethod.STATIC_ANALYSIS,
                epistemic_state=EpistemicState.OBSERVED,
                proposition_type=PropositionType.STATIC_REFERENCE,
                provenance_id="e2",
                confidence=0.9,
            ),
            DependencyEdge(
                source="c", target="d",
                dependency_type=DependencyType.SERVICE,
                source_artifact="c.py",
                observation_method=ObservationMethod.STATIC_ANALYSIS,
                epistemic_state=EpistemicState.OBSERVED,
                proposition_type=PropositionType.STATIC_REFERENCE,
                provenance_id="e3",
                confidence=0.9,
            ),
        ]
        results = engine.compose_chain(edges)
        assert len(results) >= 2  # At least adjacent pairs composed


# ---------------------------------------------------------------------------
# Epistemic State Tests
# ---------------------------------------------------------------------------


class TestEpistemicState:
    """Tests for epistemic state preservation during composition."""

    def test_static_composition_produces_inferred(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Static composition should produce INFERRED state."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.epistemic_state == EpistemicState.INFERRED

    def test_runtime_composition_produces_inconclusive(
        self,
        engine: EpistemicCompositionEngine,
        runtime_edge_ab: DependencyEdge,
        runtime_edge_bc: DependencyEdge,
    ):
        """Runtime composition should produce INCONCLUSIVE state."""
        result = engine.compose(runtime_edge_ab, runtime_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.epistemic_state == EpistemicState.INCONCLUSIVE

    def test_composed_state_not_stronger_than_parents(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composed edge should not have stronger epistemic state than parents."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        # INFERRED is weaker than OBSERVED
        assert result.derived_edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Epistemic Accounting Tests
# ---------------------------------------------------------------------------


class TestEpistemicAccounting:
    """Tests for epistemic authority accounting."""

    def test_authority_not_amplified(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition should not amplify authority."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        accounting = account_epistemic_authority(
            [static_edge_ab, static_edge_bc],
            result.derived_edge,
        )
        assert not accounting.authority_amplified
        assert accounting.authority_preserved

    def test_uncertainty_preserved(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition should preserve uncertainty."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        accounting = account_epistemic_authority(
            [static_edge_ab, static_edge_bc],
            result.derived_edge,
        )
        assert accounting.uncertainty_preserved

    def test_scope_preserved(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition should preserve scope."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        accounting = account_epistemic_authority(
            [static_edge_ab, static_edge_bc],
            result.derived_edge,
        )
        assert accounting.scope_preserved

    def test_alternatives_preserved(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition should preserve alternatives."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        accounting = account_epistemic_authority(
            [static_edge_ab, static_edge_bc],
            result.derived_edge,
        )
        assert accounting.alternatives_preserved


# ---------------------------------------------------------------------------
# Provenance Tests
# ---------------------------------------------------------------------------


class TestProvenance:
    """Tests for provenance preservation."""

    def test_composed_edge_has_provenance(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composed edge should reference parent provenance."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        assert f"composed_from:{static_edge_ab.provenance_id}" in result.derived_edge.evidence
        assert f"composed_from:{static_edge_bc.provenance_id}" in result.derived_edge.evidence

    def test_composed_edge_has_unique_provenance_id(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composed edge should have its own provenance ID."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.derived_edge is not None
        assert result.derived_edge.provenance_id != static_edge_ab.provenance_id
        assert result.derived_edge.provenance_id != static_edge_bc.provenance_id

    def test_composition_result_has_provenance(
        self,
        engine: EpistemicCompositionEngine,
        static_edge_ab: DependencyEdge,
        static_edge_bc: DependencyEdge,
    ):
        """Composition result should have provenance ID."""
        result = engine.compose(static_edge_ab, static_edge_bc)
        assert result.provenance_id != ""
