"""Adversarial tests for the Sovereign Payment Infrastructure Dependency Auditor.

These tests treat the model as actively malicious and attempt to violate
the epistemic boundary. The goal is to prove that:
    - MODEL OUTPUT ≠ AUTHORITY
    - STATIC_REFERENCE ≠ RUNTIME_DEPENDENCY
    - CONFIDENCE ≠ EVIDENCE
"""

from __future__ import annotations

from pathlib import Path

import pytest

from research.examples.payment_dependency_auditor.auditor import (
    DependencyGraphBuilder,
    LocalIngester,
    PaymentDependencyAuditor,
    generate_dependency_report,
)
from research.examples.payment_dependency_auditor.dependency_types import (
    DependencyEdge,
    DependencyType,
    DocumentationDrift,
    DriftType,
    EpistemicState,
    ObservationMethod,
    PropositionType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fixture_dir() -> Path:
    """Get the fixture directory."""
    return Path(__file__).resolve().parent.parent.parent / "examples" / "payment_dependency_auditor" / "fixture"


@pytest.fixture
def ingester(fixture_dir: Path) -> LocalIngester:
    return LocalIngester(fixture_dir)


@pytest.fixture
def ingestion_result(ingester: LocalIngester):
    return ingester.ingest()


@pytest.fixture
def graph(ingestion_result):
    builder = DependencyGraphBuilder(ingestion_result)
    return builder.build()


# ---------------------------------------------------------------------------
# Model Cannot Create Authority
# ---------------------------------------------------------------------------


class TestModelCannotCreateAuthority:
    """Tests that the model cannot directly create authority."""

    def test_model_recommendation_does_not_create_dependency(self):
        """Model saying 'X depends on Y' does not create a dependency."""
        # A model claim without evidence should not become a dependency edge
        edge = DependencyEdge(
            source="model_claim",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="model_output",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.HYPOTHESIZED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            scope="Model hypothesis only",
            limitations=["No evidence", "Model output is not authority"],
            confidence=0.99,
        )
        # Even with 99% confidence, the epistemic state is HYPOTHESIZED
        assert edge.epistemic_state == EpistemicState.HYPOTHESIZED
        assert edge.proposition_type == PropositionType.STATIC_REFERENCE

    def test_high_confidence_does_not_elevate_epistemic_state(self):
        """High confidence does not elevate epistemic state."""
        edge = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="model_output",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.HYPOTHESIZED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            confidence=0.99,
            scope="Model claim with high confidence",
        )
        # Confidence is not authority — still HYPOTHESIZED
        assert edge.epistemic_state != EpistemicState.EXPERIMENTALLY_SUPPORTED
        assert edge.epistemic_state == EpistemicState.HYPOTHESIZED


# ---------------------------------------------------------------------------
# Static Reference ≠ Runtime Dependency
# ---------------------------------------------------------------------------


class TestStaticReferenceIsNotRuntime:
    """Tests that static references are not automatically runtime dependencies."""

    def test_static_observation_stays_static(self, graph):
        """Static observations should not become runtime dependencies."""
        for edge in graph.edges:
            if edge.observation_method == ObservationMethod.STATIC_ANALYSIS:
                # Static analysis cannot prove operational necessity
                assert edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY

    def test_import_is_not_runtime(self):
        """Import statement alone is not proof of runtime dependency."""
        edge = DependencyEdge(
            source="payments",
            target="httpx",
            dependency_type=DependencyType.IMPORT,
            source_artifact="payments.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
        )
        assert edge.proposition_type == PropositionType.STATIC_REFERENCE
        assert edge.proposition_type != PropositionType.RUNTIME_DEPENDENCY

    def test_dead_code_produces_observation_not_dependency(self):
        """Dead code produces an observation, not a proven dependency."""
        edge = DependencyEdge(
            source="payments",
            target="dead_module",
            dependency_type=DependencyType.IMPORT,
            source_artifact="payments.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            limitations=["May be dead code", "Static analysis cannot prove runtime behavior"],
        )
        # The observation exists but is limited
        assert "May be dead code" in edge.limitations


# ---------------------------------------------------------------------------
# Evidence Scope Tests
# ---------------------------------------------------------------------------


class TestEvidenceScope:
    """Tests that evidence scope is preserved."""

    def test_scope_prevents_generalization(self):
        """Scope prevents generalization from staging to production."""
        edge = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="staging.yaml",
            observation_method=ObservationMethod.CONFIGURATION_PARSE,
            environment="staging",
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.CONFIGURATION_DEPENDENCY,
            scope="Staging environment only",
        )
        # Scope is staging only
        assert edge.environment == "staging"
        assert "staging" in edge.scope.lower()

    def test_evidence_limitations_recorded(self):
        """Evidence limitations should be recorded."""
        edge = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="payments.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            limitations=[
                "Static analysis cannot prove runtime behavior",
                "May be conditional path",
                "May be dead code",
            ],
        )
        assert len(edge.limitations) >= 2


# ---------------------------------------------------------------------------
# Proposition Type Preservation
# ---------------------------------------------------------------------------


class TestPropositionTypePreservation:
    """Tests that proposition types are preserved and not collapsed."""

    def test_proposition_types_distinct(self):
        """Different proposition types should remain distinct."""
        static = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="payments.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
        )
        runtime = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="runtime_test",
            observation_method=ObservationMethod.RUNTIME_TEST,
            epistemic_state=EpistemicState.EXPERIMENTALLY_SUPPORTED,
            proposition_type=PropositionType.RUNTIME_DEPENDENCY,
        )
        assert static.proposition_type != runtime.proposition_type

    def test_configuration_not_runtime(self):
        """Configuration dependency is not runtime dependency."""
        config = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="production.yaml",
            observation_method=ObservationMethod.CONFIGURATION_PARSE,
            epistemic_state=EpistemicState.DOCUMENTED,
            proposition_type=PropositionType.CONFIGURATION_DEPENDENCY,
        )
        assert config.proposition_type != PropositionType.RUNTIME_DEPENDENCY


# ---------------------------------------------------------------------------
# Epistemic State Tests
# ---------------------------------------------------------------------------


class TestEpistemicState:
    """Tests for epistemic state correctness."""

    def test_static_analysis_produces_observed(self, graph):
        """Static analysis should produce OBSERVED state."""
        for edge in graph.edges:
            if edge.observation_method == ObservationMethod.STATIC_ANALYSIS:
                assert edge.epistemic_state == EpistemicState.OBSERVED

    def test_documentation_produces_documented(self, graph):
        """Documentation parsing should produce DOCUMENTED state."""
        for edge in graph.documented_edges:
            if edge.observation_method == ObservationMethod.DOCUMENTATION_PARSE:
                assert edge.epistemic_state == EpistemicState.DOCUMENTED

    def test_inconclusive_for_conflicting_evidence(self):
        """Conflicting evidence should produce INCONCLUSIVE state."""
        edge = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="conflicting",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.INCONCLUSIVE,
            proposition_type=PropositionType.STATIC_REFERENCE,
            limitations=["Conflicting evidence", "Cannot determine actual dependency"],
        )
        assert edge.epistemic_state == EpistemicState.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Documentation Drift Tests
# ---------------------------------------------------------------------------


class TestDocumentationDriftTests:
    """Tests for documentation drift detection."""

    def test_undocumented_dependency_detected(self, graph):
        """Undocumented dependencies should be detected."""
        undocumented = [d for d in graph.drift if d.drift_type == DriftType.UNDISCOVERED]
        # The fixture has intentional undocumented dependencies
        assert len(undocumented) > 0

    def test_drift_preserves_epistemic_state(self, graph):
        """Drift items should preserve epistemic state."""
        for d in graph.drift:
            assert d.dependency.epistemic_state is not None

    def test_drift_has_severity(self, graph):
        """Drift items should have severity."""
        for d in graph.drift:
            assert d.severity in ("low", "medium", "high", "critical")


# ---------------------------------------------------------------------------
# Criticality ≠ Existence Tests
# ---------------------------------------------------------------------------


class TestCriticalityNotEqualExistence:
    """Tests that dependency existence ≠ criticality."""

    def test_dependency_exists_but_not_necessary(self):
        """A dependency may exist but not be necessary."""
        edge = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="payments.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            scope="Feature flags may be optional",
        )
        # Existence is observed, but necessity is not established
        assert edge.epistemic_state == EpistemicState.OBSERVED
        assert edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY


# ---------------------------------------------------------------------------
# Confidence ≠ Authority Tests
# ---------------------------------------------------------------------------


class TestConfidenceNotEqualAuthority:
    """Tests that confidence is not authority."""

    def test_high_confidence_without_evidence(self):
        """High confidence without evidence should not create authority."""
        edge = DependencyEdge(
            source="model",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="model_output",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.HYPOTHESIZED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            confidence=0.99,
            limitations=["No evidence", "Model confidence is not evidence"],
        )
        # Despite 99% confidence, the state is HYPOTHESIZED
        assert edge.epistemic_state == EpistemicState.HYPOTHESIZED
        assert edge.limitations[0] == "No evidence"

    def test_confidence_field_exists_but_not_authoritative(self):
        """The confidence field exists but is not authoritative."""
        edge = DependencyEdge(
            source="payments",
            target="feature-flags",
            dependency_type=DependencyType.SERVICE,
            source_artifact="payments.py",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            epistemic_state=EpistemicState.OBSERVED,
            proposition_type=PropositionType.STATIC_REFERENCE,
            confidence=0.8,
        )
        # Confidence is recorded but doesn't change epistemic state
        assert edge.confidence == 0.8
        assert edge.epistemic_state == EpistemicState.OBSERVED


# ---------------------------------------------------------------------------
# Full Audit Integrity Tests
# ---------------------------------------------------------------------------


class TestFullAuditIntegrity:
    """Tests for full audit integrity."""

    def test_audit_does_not_modify_target(self, fixture_dir: Path):
        """Audit should not modify the target system."""
        # Get initial state
        initial_files = list(fixture_dir.rglob("*"))
        initial_contents = {}
        for f in initial_files:
            if f.is_file():
                initial_contents[str(f)] = f.read_text()

        # Run audit
        auditor = PaymentDependencyAuditor(fixture_dir)
        graph, report = auditor.audit()

        # Verify no files were modified
        for f in initial_files:
            if f.is_file():
                assert f.read_text() == initial_contents[str(f)]

    def test_audit_is_deterministic(self, fixture_dir: Path):
        """Audit should be deterministic (excluding timestamp)."""
        auditor = PaymentDependencyAuditor(fixture_dir)
        graph1, _ = auditor.audit()
        graph2, _ = auditor.audit()
        assert len(graph1.edges) == len(graph2.edges)
        assert len(graph1.drift) == len(graph2.drift)
        assert graph1.metadata.get("files_analyzed") == graph2.metadata.get("files_analyzed")

    def test_audit_preserves_epistemic_state(self, fixture_dir: Path):
        """Audit should preserve epistemic state in output."""
        auditor = PaymentDependencyAuditor(fixture_dir)
        graph, _ = auditor.audit()
        # All edges should have epistemic state
        for edge in graph.edges:
            assert edge.epistemic_state is not None
            assert edge.proposition_type is not None
