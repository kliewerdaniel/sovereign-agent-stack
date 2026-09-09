"""Integration tests for the Sovereign Payment Infrastructure Dependency Auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.payment_dependency_auditor.auditor import (
    DependencyGraphBuilder,
    LocalIngester,
    PaymentDependencyAuditor,
    generate_dependency_report,
)
from examples.payment_dependency_auditor.dependency_types import (
    DependencyType,
    EpistemicState,
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
# Ingestion Tests
# ---------------------------------------------------------------------------


class TestIngestion:
    """Tests for the local ingestion layer."""

    def test_ingestion_produces_observations(self, ingestion_result):
        """Ingestion should produce raw observations."""
        assert len(ingestion_result.observations) > 0

    def test_ingestion_produces_documented_dependencies(self, ingestion_result):
        """Ingestion should extract documented dependencies."""
        assert len(ingestion_result.documented_dependencies) > 0

    def test_ingestion_analyzes_python_files(self, ingestion_result):
        """Ingestion should analyze Python source files."""
        python_obs = [o for o in ingestion_result.observations if o.artifact.endswith(".py")]
        assert len(python_obs) > 0

    def test_ingestion_analyzes_yaml_files(self, ingestion_result):
        """Ingestion should analyze YAML config files."""
        yaml_obs = [o for o in ingestion_result.observations if o.artifact.endswith((".yaml", ".yml"))]
        assert len(yaml_obs) > 0

    def test_ingestion_analyzes_markdown_files(self, ingestion_result):
        """Ingestion should analyze Markdown documentation."""
        md_deps = [d for d in ingestion_result.documented_dependencies if d.source_artifact.endswith(".md")]
        assert len(md_deps) > 0

    def test_ingestion_counts_files(self, ingestion_result):
        """Ingestion should count analyzed files."""
        assert ingestion_result.files_analyzed > 0

    def test_ingestion_counts_lines(self, ingestion_result):
        """Ingestion should count analyzed lines."""
        assert ingestion_result.lines_analyzed > 0


# ---------------------------------------------------------------------------
# Static Analysis Tests
# ---------------------------------------------------------------------------


class TestStaticAnalysis:
    """Tests for static analysis capabilities."""

    def test_imports_detected(self, ingestion_result):
        """Import statements should be detected."""
        import_obs = [o for o in ingestion_result.observations if o.observation_type == "import"]
        assert len(import_obs) > 0

    def test_network_calls_detected(self, ingestion_result):
        """HTTP client calls should be detected."""
        network_obs = [o for o in ingestion_result.observations if o.observation_type == "network"]
        assert len(network_obs) > 0

    def test_database_connections_detected(self, ingestion_result):
        """Database connections should be detected."""
        db_obs = [o for o in ingestion_result.observations if o.observation_type == "database"]
        assert len(db_obs) > 0

    def test_configuration_references_detected(self, ingestion_result):
        """Environment variable references should be detected."""
        config_obs = [o for o in ingestion_result.observations if o.observation_type == "configuration"]
        assert len(config_obs) > 0


# ---------------------------------------------------------------------------
# Epistemic Typing Tests
# ---------------------------------------------------------------------------


class TestEpistemicTyping:
    """Tests for epistemic type preservation."""

    def test_static_reference_is_not_runtime(self, graph):
        """Static reference should not be automatically elevated to runtime dependency."""
        for edge in graph.edges:
            if edge.observation_method.value == "static_analysis":
                # Static analysis alone cannot prove runtime behavior
                assert edge.proposition_type != PropositionType.OPERATIONAL_DEPENDENCY

    def test_evidence_scope_preserved(self, graph):
        """Evidence scope should be preserved in edges."""
        for edge in graph.edges:
            assert edge.scope != ""
            assert len(edge.limitations) > 0

    def test_proposition_type_preserved(self, graph):
        """Proposition type should be preserved."""
        for edge in graph.edges:
            assert edge.proposition_type is not None

    def test_epistemic_state_is_observed_not_supported(self, graph):
        """Static observations should be OBSERVED, not EXPERIMENTALLY_SUPPORTED."""
        for edge in graph.edges:
            if edge.observation_method.value == "static_analysis":
                assert edge.epistemic_state == EpistemicState.OBSERVED


# ---------------------------------------------------------------------------
# Documentation Drift Tests
# ---------------------------------------------------------------------------


class TestDocumentationDrift:
    """Tests for documentation drift detection."""

    def test_undocumented_dependencies_detected(self, graph):
        """Undocumented dependencies should be detected."""
        undocumented = [d for d in graph.drift if d.drift_type.value == "undiscovered"]
        assert len(undocumented) > 0

    def test_documented_dependencies_found(self, graph):
        """Documented dependencies should be found."""
        assert len(graph.documented_edges) > 0

    def test_drift_severity_assigned(self, graph):
        """Drift items should have severity assigned."""
        for d in graph.drift:
            assert d.severity in ("low", "medium", "high", "critical")


# ---------------------------------------------------------------------------
# Dependency Graph Tests
# ---------------------------------------------------------------------------


class TestDependencyGraph:
    """Tests for the dependency graph."""

    def test_graph_has_edges(self, graph):
        """Graph should have edges."""
        assert len(graph.edges) > 0

    def test_graph_has_metadata(self, graph):
        """Graph should have metadata."""
        assert "files_analyzed" in graph.metadata
        assert "lines_analyzed" in graph.metadata

    def test_graph_serializable(self, graph):
        """Graph should be serializable to dict."""
        graph_dict = graph.to_dict()
        assert "edges" in graph_dict
        assert "documented_edges" in graph_dict
        assert "drift" in graph_dict

    def test_edges_have_provenance(self, graph):
        """Edges should have provenance information."""
        for edge in graph.edges:
            assert edge.source_artifact != ""
            assert edge.provenance_id is not None


# ---------------------------------------------------------------------------
# Report Generation Tests
# ---------------------------------------------------------------------------


class TestReportGeneration:
    """Tests for report generation."""

    def test_report_generated(self, graph):
        """Report should be generated."""
        report = generate_dependency_report(graph)
        assert len(report) > 0

    def test_report_contains_summary(self, graph):
        """Report should contain summary section."""
        report = generate_dependency_report(graph)
        assert "## Summary" in report

    def test_report_contains_drift(self, graph):
        """Report should contain documentation drift section."""
        report = generate_dependency_report(graph)
        assert "## Documentation Drift" in report

    def test_report_contains_limitations(self, graph):
        """Report should contain limitations section."""
        report = generate_dependency_report(graph)
        assert "## Limitations" in report


# ---------------------------------------------------------------------------
# Full Audit Tests
# ---------------------------------------------------------------------------


class TestFullAudit:
    """Tests for the full audit pipeline."""

    def test_full_audit(self, fixture_dir: Path):
        """Full audit should complete successfully."""
        auditor = PaymentDependencyAuditor(fixture_dir)
        graph, report = auditor.audit()
        assert graph is not None
        assert report is not None

    def test_audit_produces_graph(self, fixture_dir: Path):
        """Audit should produce a dependency graph."""
        auditor = PaymentDependencyAuditor(fixture_dir)
        graph, _ = auditor.audit()
        assert len(graph.edges) > 0

    def test_audit_produces_report(self, fixture_dir: Path):
        """Audit should produce a report."""
        auditor = PaymentDependencyAuditor(fixture_dir)
        _, report = auditor.audit()
        assert "## Summary" in report
