"""Sovereign Payment Infrastructure Dependency Auditor.

This auditor analyzes a payment-oriented software system and produces
a provenance-backed dependency graph with explicit epistemic state.

Critical architectural principles:
    - STATIC_REFERENCE ≠ RUNTIME_DEPENDENCY
    - MODEL OUTPUT ≠ AUTHORITY
    - The system is READ-ONLY with respect to the target infrastructure
    - Every dependency claim carries provenance and epistemic state
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from research.examples.payment_dependency_auditor.dependency_types import (
    DependencyCriticality,
    DependencyEdge,
    DependencyType,
    DocumentationDrift,
    DriftType,
    EpistemicState,
    ObservationMethod,
    PropositionType,
)


# ---------------------------------------------------------------------------
# Ingestion Layer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawObservation:
    """A raw observation from static analysis.

    This is NOT a dependency claim. It is evidence that may support
    a dependency claim after epistemic evaluation.
    """

    source: str
    target: str
    observation_type: str
    artifact: str
    location: str
    context: str = ""
    environment: str = "all"


@dataclass(frozen=True)
class IngestionResult:
    """Result of ingesting a target system."""

    observations: list[RawObservation]
    documented_dependencies: list[DependencyEdge]
    files_analyzed: int
    lines_analyzed: int
    errors: list[str] = field(default_factory=list)


class LocalIngester:
    """Deterministic ingestion layer for local file analysis.

    Analyzes Python, TypeScript/JavaScript, YAML, JSON, Markdown,
    Dockerfiles, Docker Compose, and shell scripts.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def ingest(self) -> IngestionResult:
        """Ingest the target system and produce raw observations."""
        observations: list[RawObservation] = []
        documented: list[DependencyEdge] = []
        errors: list[str] = []
        files_analyzed = 0
        lines_analyzed = 0

        for path in self.root.rglob("*"):
            if path.is_file():
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    file_lines = content.count("\n")
                    lines_analyzed += file_lines

                    if path.suffix == ".py":
                        obs = self._analyze_python(path, content)
                        observations.extend(obs)
                        files_analyzed += 1
                    elif path.suffix in (".yaml", ".yml"):
                        obs, doc = self._analyze_yaml(path, content)
                        observations.extend(obs)
                        documented.extend(doc)
                        files_analyzed += 1
                    elif path.suffix == ".json":
                        obs = self._analyze_json(path, content)
                        observations.extend(obs)
                        files_analyzed += 1
                    elif path.suffix == ".md":
                        doc = self._analyze_markdown(path, content)
                        documented.extend(doc)
                        files_analyzed += 1
                    elif path.name == "Dockerfile":
                        obs = self._analyze_dockerfile(path, content)
                        observations.extend(obs)
                        files_analyzed += 1
                    elif path.name == "docker-compose.yaml":
                        obs = self._analyze_docker_compose(path, content)
                        observations.extend(obs)
                        files_analyzed += 1
                    elif path.suffix == ".sh":
                        obs = self._analyze_shell(path, content)
                        observations.extend(obs)
                        files_analyzed += 1
                    elif path.suffix == ".ts":
                        obs = self._analyze_typescript(path, content)
                        observations.extend(obs)
                        files_analyzed += 1
                except Exception as e:
                    errors.append(f"Error analyzing {path}: {e}")

        return IngestionResult(
            observations=observations,
            documented_dependencies=documented,
            files_analyzed=files_analyzed,
            lines_analyzed=lines_analyzed,
            errors=errors,
        )

    def _analyze_python(self, path: Path, content: str) -> list[RawObservation]:
        """Extract dependency observations from Python source."""
        observations = []
        str_path = str(path)

        # Import statements
        for match in re.finditer(r"^import\s+(\S+)", content, re.MULTILINE):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(1),
                observation_type="import",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        # From imports
        for match in re.finditer(r"^from\s+(\S+)\s+import", content, re.MULTILINE):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(1),
                observation_type="import",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        # HTTP client calls
        for match in re.finditer(r"(httpx|aiohttp|requests)\.(get|post|put|delete)\(", content):
            observations.append(RawObservation(
                source=str_path,
                target="http_call",
                observation_type="network",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0)[:100],
            ))

        # Database connections
        for match in re.finditer(r"(psycopg2|sqlalchemy|sqlite3|pymongo)\.connect", content):
            observations.append(RawObservation(
                source=str_path,
                target="database",
                observation_type="database",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        # Redis connections
        for match in re.finditer(r"redis\.Redis|redis\.from_url", content):
            observations.append(RawObservation(
                source=str_path,
                target="redis",
                observation_type="database",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        # Environment variable references
        for match in re.finditer(r"os\.environ\.get\(\"([^\"]+)\"", content):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(1),
                observation_type="configuration",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        # URL patterns (service endpoints)
        for match in re.finditer(r"(https?://[a-zA-Z0-9_.:-]+)", content):
            url = match.group(1)
            if "localhost" in url or "internal" in url or re.match(r"http://[a-z-]+:", url):
                observations.append(RawObservation(
                    source=str_path,
                    target=url,
                    observation_type="network",
                    artifact=str_path,
                    location=f"line {content[:match.start()].count(chr(10)) + 1}",
                    context=url,
                ))

        return observations

    def _analyze_yaml(self, path: Path, content: str) -> tuple[list[RawObservation], list[DependencyEdge]]:
        """Extract dependency observations from YAML config."""
        observations = []
        documented = []
        str_path = str(path)

        # Service dependencies
        for match in re.finditer(r"dependencies:\s*\n((?:\s+-\s+\S+\s*\n?)+)", content):
            deps_block = match.group(1)
            for dep_match in re.finditer(r"-\s+(\S+)", deps_block):
                dep = dep_match.group(1)
                documented.append(DependencyEdge(
                    source=str_path,
                    target=dep,
                    dependency_type=DependencyType.SERVICE,
                    source_artifact=str_path,
                    observation_method=ObservationMethod.CONFIGURATION_PARSE,
                    epistemic_state=EpistemicState.DOCUMENTED,
                    proposition_type=PropositionType.CONFIGURATION_DEPENDENCY,
                    scope="Configuration file reference",
                ))

        # External endpoints
        for match in re.finditer(r"(endpoint|host|port):\s*(\S+)", content):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(2),
                observation_type="configuration",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        return observations, documented

    def _analyze_json(self, path: Path, content: str) -> list[RawObservation]:
        """Extract dependency observations from JSON."""
        observations = []
        str_path = str(path)

        # Schema references
        for match in re.finditer(r"\$ref[\":\s]+(\S+)", content):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(1),
                observation_type="schema",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        return observations

    def _analyze_markdown(self, path: Path, content: str) -> list[DependencyEdge]:
        """Extract documented dependencies from Markdown."""
        documented = []
        str_path = str(path)

        # Service dependency mentions - various patterns
        patterns = [
            # "Depends on: X Service" or "Depends on: X, Y"
            r"[Dd]epends on:\s*([A-Z][a-zA-Z]+(?:\s+Service)?(?:\s*,\s*[A-Z][a-zA-Z]+(?:\s+Service)?)*)",
            # "X → Y" or "X -> Y"
            r"([A-Z][a-zA-Z]+)\s*(?:→|->)\s*([A-Z][a-zA-Z]+)",
            # "X depends on Y"
            r"([A-Z][a-zA-Z]+)\s+depends\s+on\s+([A-Z][a-zA-Z]+)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                if not groups:
                    continue
                if len(groups) >= 2:
                    source = groups[0].lower()
                    target = groups[1].lower()
                else:
                    # Single group - try to split by comma
                    target_str = groups[0].lower()
                    targets = [t.strip() for t in target_str.split(",")]
                    source = "unknown"
                    for target in targets:
                        documented.append(DependencyEdge(
                            source=source,
                            target=target,
                            dependency_type=DependencyType.SERVICE,
                            source_artifact=str_path,
                            observation_method=ObservationMethod.DOCUMENTATION_PARSE,
                            epistemic_state=EpistemicState.DOCUMENTED,
                            proposition_type=PropositionType.STATIC_REFERENCE,
                            scope="Documentation reference",
                        ))
                    continue
                documented.append(DependencyEdge(
                    source=source,
                    target=target,
                    dependency_type=DependencyType.SERVICE,
                    source_artifact=str_path,
                    observation_method=ObservationMethod.DOCUMENTATION_PARSE,
                    epistemic_state=EpistemicState.DOCUMENTED,
                    proposition_type=PropositionType.STATIC_REFERENCE,
                    scope="Documentation reference",
                ))

        return documented

    def _analyze_dockerfile(self, path: Path, content: str) -> list[RawObservation]:
        """Extract dependency observations from Dockerfile."""
        observations = []
        str_path = str(path)

        for match in re.finditer(r"FROM\s+(\S+)", content):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(1),
                observation_type="import",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        return observations

    def _analyze_docker_compose(self, path: Path, content: str) -> list[RawObservation]:
        """Extract dependency observations from Docker Compose."""
        observations = []
        str_path = str(path)

        for match in re.finditer(r"depends_on:\s*\n((?:\s+-\s+\S+\s*\n?)+)", content):
            deps_block = match.group(1)
            for dep_match in re.finditer(r"-\s+(\S+)", deps_block):
                observations.append(RawObservation(
                    source=str_path,
                    target=dep_match.group(1),
                    observation_type="service",
                    artifact=str_path,
                    location="docker-compose",
                    context=dep_match.group(0),
                ))

        return observations

    def _analyze_shell(self, path: Path, content: str) -> list[RawObservation]:
        """Extract dependency observations from shell scripts."""
        observations = []
        str_path = str(path)

        for match in re.finditer(r"(curl|wget)\s+(\S+)", content):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(2),
                observation_type="network",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0)[:100],
            ))

        return observations

    def _analyze_typescript(self, path: Path, content: str) -> list[RawObservation]:
        """Extract dependency observations from TypeScript."""
        observations = []
        str_path = str(path)

        for match in re.finditer(r"import\s+.*from\s+[\"'](\S+)[\"']", content):
            observations.append(RawObservation(
                source=str_path,
                target=match.group(1),
                observation_type="import",
                artifact=str_path,
                location=f"line {content[:match.start()].count(chr(10)) + 1}",
                context=match.group(0),
            ))

        return observations


# ---------------------------------------------------------------------------
# Dependency Graph Builder
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyGraph:
    """Provenance-backed dependency graph with epistemic state.

    This is NOT a conventional dependency graph. Every edge carries
    complete epistemic provenance.
    """

    edges: list[DependencyEdge]
    documented_edges: list[DependencyEdge]
    drift: list[DocumentationDrift]
    criticality: list[DependencyCriticality]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "edges": [e.to_dict() for e in self.edges],
            "documented_edges": [e.to_dict() for e in self.documented_edges],
            "drift": [
                {
                    "drift_type": d.drift_type.value,
                    "dependency": d.dependency.to_dict(),
                    "documentation_reference": d.documentation_reference,
                    "implementation_reference": d.implementation_reference,
                    "description": d.description,
                    "severity": d.severity,
                }
                for d in self.drift
            ],
            "criticality": [
                {
                    "source": c.source,
                    "target": c.target,
                    "exists": c.exists,
                    "necessary": c.necessary,
                    "centrality": c.centrality,
                    "failure_impact": c.failure_impact,
                    "scope": c.scope,
                    "reversible": c.reversible,
                    "environment": c.environment,
                }
                for c in self.criticality
            ],
            "metadata": self.metadata,
        }


class DependencyGraphBuilder:
    """Builds a dependency graph from raw observations.

    Applies epistemic rules:
    - Static reference ≠ runtime dependency
    - Model output ≠ authority
    - Evidence scope is preserved
    """

    def __init__(self, ingestion: IngestionResult):
        self.ingestion = ingestion

    def build(self) -> DependencyGraph:
        """Build the dependency graph."""
        edges = self._build_edges()
        documented = self.ingestion.documented_dependencies
        drift = self._detect_drift(edges, documented)
        criticality = self._assess_criticality(edges)

        return DependencyGraph(
            edges=edges,
            documented_edges=documented,
            drift=drift,
            criticality=criticality,
            metadata={
                "files_analyzed": self.ingestion.files_analyzed,
                "lines_analyzed": self.ingestion.lines_analyzed,
                "total_observations": len(self.ingestion.observations),
                "total_edges": len(edges),
                "documented_count": len(documented),
                "drift_count": len(drift),
                "generated_at": datetime.utcnow().isoformat(),
            },
        )

    def _build_edges(self) -> list[DependencyEdge]:
        """Convert raw observations to dependency edges with epistemic state."""
        edges = []

        for obs in self.ingestion.observations:
            edge = self._observation_to_edge(obs)
            if edge:
                edges.append(edge)

        return edges

    def _observation_to_edge(self, obs: RawObservation) -> Optional[DependencyEdge]:
        """Convert a raw observation to a dependency edge.

        The key transformation: observations are NOT automatically
        elevated to dependency claims. They are labeled according
        to what they actually establish.
        """
        # Map observation type to dependency type
        type_map = {
            "import": DependencyType.IMPORT,
            "network": DependencyType.NETWORK,
            "database": DependencyType.DATABASE,
            "configuration": DependencyType.CONFIGURATION,
            "service": DependencyType.SERVICE,
            "schema": DependencyType.SCHEMA,
        }

        dep_type = type_map.get(obs.observation_type)
        if dep_type is None:
            return None

        # Determine epistemic state based on observation method
        # CRITICAL: Static observation only establishes STATIC_REFERENCE
        epistemic = EpistemicState.OBSERVED
        proposition = PropositionType.STATIC_REFERENCE

        if obs.observation_type == "network":
            proposition = PropositionType.RUNTIME_DEPENDENCY
        elif obs.observation_type == "database":
            proposition = PropositionType.RUNTIME_DEPENDENCY
        elif obs.observation_type == "configuration":
            proposition = PropositionType.CONFIGURATION_DEPENDENCY

        return DependencyEdge(
            source=obs.source,
            target=obs.target,
            dependency_type=dep_type,
            source_artifact=obs.artifact,
            source_location=obs.location,
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            environment=obs.environment,
            epistemic_state=epistemic,
            proposition_type=proposition,
            evidence=[f"{obs.observation_type}:{obs.context}"],
            scope=f"Static observation: {obs.observation_type}",
            limitations=[
                "Static analysis cannot prove runtime behavior",
                "May be dead code or conditional path",
            ],
        )

    def _detect_drift(
        self,
        observed: list[DependencyEdge],
        documented: list[DependencyEdge],
    ) -> list[DocumentationDrift]:
        """Detect documentation drift."""
        drift = []

        observed_targets = {(e.source, e.target) for e in observed}
        documented_targets = {(e.source, e.target) for e in documented}

        # Undocumented dependencies
        for obs in observed:
            key = (obs.source, obs.target)
            if key not in documented_targets:
                drift.append(DocumentationDrift(
                    drift_type=DriftType.UNDISCOVERED,
                    dependency=obs,
                    documentation_reference="Not found in documentation",
                    implementation_reference=obs.source_artifact,
                    description=f"Observed dependency {obs.source} → {obs.target} not documented",
                    severity="medium",
                ))

        # Documented but removed
        for doc in documented:
            key = (doc.source, doc.target)
            if key not in observed_targets:
                drift.append(DocumentationDrift(
                    drift_type=DriftType.DOCUMENTED_REMOVED,
                    dependency=doc,
                    documentation_reference=doc.source_artifact,
                    implementation_reference="Not found in code",
                    description=f"Documented dependency {doc.source} → {doc.target} not found in code",
                    severity="low",
                ))

        return drift

    def _assess_criticality(self, edges: list[DependencyEdge]) -> list[DependencyCriticality]:
        """Assess criticality of dependencies.

        IMPORTANT: Existence ≠ criticality.
        """
        criticality = []

        for edge in edges:
            # Determine if dependency is necessary based on type
            necessary = edge.dependency_type in (
                DependencyType.DATABASE,
                DependencyType.SERVICE,
            )

            criticality.append(DependencyCriticality(
                source=edge.source,
                target=edge.target,
                exists=True,
                necessary=necessary,
                centrality=0.5,  # Default — requires experiment to determine
                failure_impact="unknown",  # Requires failure injection
                scope=edge.scope,
                reversible=True,
                environment=edge.environment,
            ))

        return criticality


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------


def generate_dependency_report(graph: DependencyGraph, timestamp: str | None = None) -> str:
    """Generate a human-readable dependency report.

    Args:
        graph: The dependency graph to report on
        timestamp: Optional timestamp for deterministic output (for testing)
    """
    ts = timestamp or graph.metadata.get("generated_at", "unknown")
    lines = [
        "# Payment Infrastructure Dependency Report",
        "",
        f"Generated: {ts}",
        f"Files analyzed: {graph.metadata.get('files_analyzed', 0)}",
        f"Lines analyzed: {graph.metadata.get('lines_analyzed', 0)}",
        f"Total observations: {graph.metadata.get('total_observations', 0)}",
        "",
        "## Summary",
        "",
        f"- Total dependency edges: {len(graph.edges)}",
        f"- Documented dependencies: {len(graph.documented_edges)}",
        f"- Documentation drift items: {len(graph.drift)}",
        "",
        "## Dependency Status",
        "",
        "| Source | Target | Type | Epistemic State | Proposition |",
        "|--------|--------|------|-----------------|-------------|",
    ]

    for edge in graph.edges:
        lines.append(
            f"| {edge.source} | {edge.target} | {edge.dependency_type.value} "
            f"| {edge.epistemic_state.value} | {edge.proposition_type.value} |"
        )

    if graph.drift:
        lines.extend([
            "",
            "## Documentation Drift",
            "",
            "| Type | Source | Target | Description | Severity |",
            "|------|--------|--------|-------------|----------|",
        ])
        for d in graph.drift:
            lines.append(
                f"| {d.drift_type.value} | {d.dependency.source} "
                f"| {d.dependency.target} | {d.description} | {d.severity} |"
            )

    lines.extend([
        "",
        "## Key Findings",
        "",
        "### Undocumented Dependencies",
        "",
        "The following dependencies were observed in code but not documented:",
        "",
    ])

    undocumented = [d for d in graph.drift if d.drift_type == DriftType.UNDISCOVERED]
    if undocumented:
        for d in undocumented:
            lines.append(f"- **{d.dependency.source} → {d.dependency.target}**: {d.description}")
    else:
        lines.append("- None found")

    lines.extend([
        "",
        "### Epistemic State Distribution",
        "",
    ])

    state_counts: dict[str, int] = {}
    for edge in graph.edges:
        state = edge.epistemic_state.value
        state_counts[state] = state_counts.get(state, 0) + 1

    for state, count in sorted(state_counts.items()):
        lines.append(f"- {state}: {count}")

    lines.extend([
        "",
        "## Limitations",
        "",
        "1. Static analysis cannot prove runtime behavior",
        "2. Some dependencies may be conditional or environment-specific",
        "3. Dead code may produce false positives",
        "4. Transitive dependencies may not be fully resolved",
        "",
        "## Architectural Invariants",
        "",
        "- STATIC_REFERENCE ≠ RUNTIME_DEPENDENCY",
        "- MODEL OUTPUT ≠ AUTHORITY",
        "- Evidence scope is preserved across transformations",
        "- The system is READ-ONLY with respect to the target infrastructure",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Auditor
# ---------------------------------------------------------------------------


class PaymentDependencyAuditor:
    """Sovereign Payment Infrastructure Dependency Auditor.

    Analyzes a payment-oriented software system and produces
    a provenance-backed dependency graph.
    """

    def __init__(self, target_path: str | Path):
        self.target_path = Path(target_path)
        self.ingester = LocalIngester(self.target_path)

    def audit(self) -> tuple[DependencyGraph, str]:
        """Run the full audit.

        Returns:
            Tuple of (dependency_graph, report_markdown)
        """
        # Ingest
        ingestion = self.ingester.ingest()

        # Build graph
        builder = DependencyGraphBuilder(ingestion)
        graph = builder.build()

        # Generate report
        report = generate_dependency_report(graph)

        return graph, report
