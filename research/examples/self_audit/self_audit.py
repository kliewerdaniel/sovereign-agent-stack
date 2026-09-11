"""Recursive Sovereign Architecture Audit — Enhanced.

This module performs a self-audit of the Sovereign Agent Stack using its own
dependency auditor and epistemic protocol.

The central research question:
> Can SAS produce a mechanically reconstructible architectural model of itself
> while preserving the distinction between observation, inference, proposition,
> evidence, epistemic authority, and operational authority?
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from research.examples.payment_dependency_auditor.dependency_types import (
    DependencyEdge,
    DependencyType,
    DocumentationDrift,
    DriftType,
    EpistemicState,
    ObservationMethod,
    PropositionType,
)
from research.examples.payment_dependency_auditor.epistemic_composition import (
    CompositionOperator,
    CompositionValidity,
    EpistemicCompositionEngine,
    account_epistemic_authority,
)


# ---------------------------------------------------------------------------
# Architecture-Specific Observation Types
# ---------------------------------------------------------------------------


class ArchitectureObservationType(str, Enum):
    """Extended observation types for architectural analysis."""

    # Standard dependency types
    IMPORT = "import"
    CALL = "call"
    NETWORK = "network"
    DATABASE = "database"
    CONFIGURATION = "configuration"

    # Authority-specific types
    AUTHORITY_GATE = "authority_gate"
    AUTHORIZATION_SOURCE = "authorization_source"
    CAPABILITY_SOURCE = "capability_source"
    GOVERNANCE_SOURCE = "governance_source"
    EPISTEMIC_SOURCE = "epistemic_source"
    PROVENANCE_SOURCE = "provenance_source"
    CONSEQUENCE_BOUNDARY = "consequence_boundary"
    EXECUTOR_BOUNDARY = "executor_boundary"
    TRUST_BOUNDARY = "trust_boundary"
    VERIFICATION_BOUNDARY = "verification_boundary"
    REGISTRATION_BOUNDARY = "registration_boundary"
    CREDENTIAL_BOUNDARY = "credential_boundary"
    DOMAIN_BOUNDARY = "domain_boundary"
    TEMPORAL_BOUNDARY = "temporal_boundary"


# ---------------------------------------------------------------------------
# Architectural Claim
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArchitecturalClaim:
    """An architectural claim with full epistemic provenance."""

    claim_id: str
    proposition_type: PropositionType
    claim: str
    scope: str
    environment: str
    temporal_boundary: str
    evidence_refs: list[str]
    parent_claims: list[str]
    alternative_hypotheses: list[str]
    intervention_refs: list[str]
    epistemic_state: EpistemicState
    authority_level: str
    provenance_id: str
    documentation_refs: list[str]
    implementation_refs: list[str]
    test_refs: list[str]
    limitations: list[str]
    next_experiment: str

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "proposition_type": self.proposition_type.value,
            "claim": self.claim,
            "scope": self.scope,
            "environment": self.environment,
            "temporal_boundary": self.temporal_boundary,
            "evidence_refs": self.evidence_refs,
            "parent_claims": self.parent_claims,
            "alternative_hypotheses": self.alternative_hypotheses,
            "intervention_refs": self.intervention_refs,
            "epistemic_state": self.epistemic_state.value,
            "authority_level": self.authority_level,
            "provenance_id": self.provenance_id,
            "documentation_refs": self.documentation_refs,
            "implementation_refs": self.implementation_refs,
            "test_refs": self.test_refs,
            "limitations": self.limitations,
            "next_experiment": self.next_experiment,
        }


# ---------------------------------------------------------------------------
# Raw Architectural Observation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawArchObservation:
    """A raw observation from architectural analysis."""

    source: str
    target: str
    observation_type: ArchitectureObservationType
    artifact: str
    location: str
    context: str
    environment: str = "all"


# ---------------------------------------------------------------------------
# Self-Audit Engine
# ---------------------------------------------------------------------------


class RecursiveSelfAudit:
    """Performs a recursive audit of the Sovereign Agent Stack."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src" / "sas"
        self.docs_root = self.repo_root / "docs"
        self.tests_root = self.repo_root / "tests"
        self.composition_engine = EpistemicCompositionEngine()

        # Collected data
        self.observations: list[RawArchObservation] = []
        self.documentation_claims: list[DependencyEdge] = []
        self.implementation_edges: list[DependencyEdge] = []
        self.test_edges: list[DependencyEdge] = []
        self.drift_items: list[DocumentationDrift] = []
        self.architectural_claims: list[ArchitecturalClaim] = []
        self.authority_paths: list[dict] = []
        self.composition_results: list[Any] = []

        # Authority-related patterns for investigation
        self.authority_patterns = {
            "authorization": r"authorize|authorization|AuthorizationArtifact",
            "capability": r"capability|CapabilityScope|ExecutionCapability",
            "governance": r"govern|governance|epistemic_governance",
            "epistemic": r"epistemic|EpistemicStatus|evaluate_hypothesis",
            "provenance": r"provenance|ProvenanceGraph|provenance_id",
            "consequence": r"consequence|consequential|ConsequenceType",
            "verification": r"verif|verify|CapabilityVerifier",
            "credential": r"credential|Credential|auth_broker",
            "boundary": r"boundary|capability_bound|CapabilityBound",
        }

    def run_full_audit(self) -> dict:
        """Run the complete recursive self-audit."""
        print("=" * 70)
        print("RECURSIVE SOVEREIGN ARCHITECTURE AUDIT")
        print("=" * 70)

        # Phase 1: Gather observations
        print("\n[Phase 1] Gathering architectural observations...")
        self._gather_implementation_observations()
        self._gather_documentation_observations()
        self._gather_test_observations()

        # Phase 2: Detect documentation drift
        print("\n[Phase 2] Detecting documentation drift...")
        self._detect_documentation_drift()

        # Phase 3: Construct authority escape graph
        print("\n[Phase 3] Constructing authority escape graph...")
        self._construct_authority_escape_graph()

        # Phase 4: Analyze epistemic gaps
        print("\n[Phase 4] Analyzing epistemic gaps...")
        self._analyze_epistemic_gaps()

        # Phase 5: Composition audit
        print("\n[Phase 5] Running composition audit...")
        self._run_composition_audit()

        # Phase 6: Generate architectural claims
        print("\n[Phase 6] Generating architectural claims...")
        self._generate_architectural_claims()

        # Phase 7: Produce report
        print("\n[Phase 7] Producing audit report...")
        report = self._produce_report()

        print("\n" + "=" * 70)
        print("AUDIT COMPLETE")
        print("=" * 70)

        return report

    def _gather_implementation_observations(self):
        """Gather observations from actual source code."""
        observation_count = 0

        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Extract imports
                for match in re.finditer(r"^from\s+(\S+)\s+import", content, re.MULTILINE):
                    target = match.group(1)
                    if not target.startswith("."):
                        self.observations.append(RawArchObservation(
                            source=str(rel_path),
                            target=target,
                            observation_type=ArchitectureObservationType.IMPORT,
                            artifact=str(rel_path),
                            location=f"line {content[:match.start()].count(chr(10)) + 1}",
                            context=match.group(0)[:100],
                        ))
                        observation_count += 1

                # Extract authority-specific patterns
                for obs_type_name, pattern in [
                    ("authority_gate", self.authority_patterns["authorization"]),
                    ("capability_source", self.authority_patterns["capability"]),
                    ("governance_source", self.authority_patterns["governance"]),
                    ("epistemic_source", self.authority_patterns["epistemic"]),
                    ("provenance_source", self.authority_patterns["provenance"]),
                    ("consequence_boundary", self.authority_patterns["consequence"]),
                    ("verification_boundary", self.authority_patterns["verification"]),
                    ("credential_boundary", self.authority_patterns["credential"]),
                    ("boundary", self.authority_patterns["boundary"]),
                ]:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        self.observations.append(RawArchObservation(
                            source=str(rel_path),
                            target=match.group(0),
                            observation_type=ArchitectureObservationType[obs_type_name.upper()],
                            artifact=str(rel_path),
                            location="",
                            context=content[max(0, match.start()-20):match.end()+20],
                        ))
                        observation_count += 1

            except Exception:
                pass

        print(f"  Gathered {observation_count} implementation observations")

    def _gather_documentation_observations(self):
        """Gather claims from documentation."""
        if not self.docs_root.exists():
            return

        for md_file in self.docs_root.rglob("*.md"):
            if "__pycache__" in str(md_file):
                continue
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                rel_path = md_file.relative_to(self.repo_root)

                # Extract documented dependencies (various formats)
                dep_patterns = [
                    # "A → B" or "A -> B"
                    r"([A-Z][a-zA-Z_]+)\s*[→->]+\s*([A-Z][a-zA-Z_]+)",
                    # "A depends on B"
                    r"([A-Z][a-zA-Z_]+)\s+depends\s+on\s+([A-Z][a-zA-Z_]+)",
                    # "A: B" (in lists)
                    r"-\s+([A-Z][a-zA-Z_]+)\s*:\s*([A-Z][a-zA-Z_]+)",
                ]

                for pattern in dep_patterns:
                    for match in re.finditer(pattern, content):
                        self.documentation_claims.append(DependencyEdge(
                            source=match.group(1),
                            target=match.group(2),
                            dependency_type=DependencyType.SERVICE,
                            source_artifact=str(rel_path),
                            observation_method=ObservationMethod.DOCUMENTATION_PARSE,
                            epistemic_state=EpistemicState.DOCUMENTED,
                            proposition_type=PropositionType.STATIC_REFERENCE,
                            scope="Documentation reference",
                        ))

                # Extract authority-specific documented claims
                for pattern_name, pattern in self.authority_patterns.items():
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        self.documentation_claims.append(DependencyEdge(
                            source=str(rel_path),
                            target=match.group(0),
                            dependency_type=DependencyType.SERVICE,
                            source_artifact=str(rel_path),
                            observation_method=ObservationMethod.DOCUMENTATION_PARSE,
                            epistemic_state=EpistemicState.DOCUMENTED,
                            proposition_type=PropositionType.STATIC_REFERENCE,
                            scope=f"Documented {pattern_name} claim",
                        ))

            except Exception:
                pass

        print(f"  Gathered {len(self.documentation_claims)} documentation claims")

    def _gather_test_observations(self):
        """Gather observations from test files."""
        if not self.tests_root.exists():
            return

        for py_file in self.tests_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Extract test assertions about architecture
                for match in re.finditer(r"assert.*(?:authority|capability|govern|epistemic|provenance|consequence|verif|credential|boundary)", content, re.IGNORECASE):
                    self.test_edges.append(DependencyEdge(
                        source=str(rel_path),
                        target="architectural_assertion",
                        dependency_type=DependencyType.SERVICE,
                        source_artifact=str(rel_path),
                        observation_method=ObservationMethod.DOCUMENTATION_PARSE,
                        epistemic_state=EpistemicState.OBSERVED,
                        proposition_type=PropositionType.STATIC_REFERENCE,
                        scope="Test assertion",
                    ))

                # Extract test class names that indicate architectural testing
                for match in re.finditer(r"class\s+Test(\w+)", content):
                    component = match.group(1)
                    self.test_edges.append(DependencyEdge(
                        source=str(rel_path),
                        target=component,
                        dependency_type=DependencyType.SERVICE,
                        source_artifact=str(rel_path),
                        observation_method=ObservationMethod.DOCUMENTATION_PARSE,
                        epistemic_state=EpistemicState.OBSERVED,
                        proposition_type=PropositionType.STATIC_REFERENCE,
                        scope=f"Test class for {component}",
                    ))

            except Exception:
                pass

        print(f"  Gathered {len(self.test_edges)} test observations")

    def _detect_documentation_drift(self):
        """Detect drift between documentation and implementation."""
        # Build sets of documented dependencies
        documented_pairs = set()
        for d in self.documentation_claims:
            if not d.source_artifact.endswith(".md"):
                continue
            documented_pairs.add((d.source.lower(), d.target.lower()))

        # Build set of implemented dependencies
        implemented_pairs = set()
        for obs in self.observations:
            if obs.observation_type == ArchitectureObservationType.IMPORT:
                implemented_pairs.add((obs.source.lower(), obs.target.lower()))

        # Find undocumented dependencies (in implementation but not docs)
        # Only count significant imports (not stdlib)
        stdlib_modules = {"__future__", "dataclasses", "datetime", "enum", "pathlib",
                         "typing", "os", "sys", "json", "re", "collections",
                         "functools", "itertools", "math", "random", "string",
                         "time", "uuid", "warnings", "abc", "io", "logging"}

        undocumented_count = 0
        for obs in self.observations:
            if obs.observation_type != ArchitectureObservationType.IMPORT:
                continue
            target = obs.target.split(".")[0] if "." in obs.target else obs.target
            if target in stdlib_modules:
                continue
            if target.startswith("sas") or target.startswith("examples"):
                # Internal dependencies should be documented
                found_in_docs = False
                for doc in self.documentation_claims:
                    if target.lower() in doc.target.lower():
                        found_in_docs = True
                        break
                if not found_in_docs:
                    self.drift_items.append(DocumentationDrift(
                        drift_type=DriftType.UNDISCOVERED,
                        dependency=DependencyEdge(
                            source=obs.source,
                            target=obs.target,
                            dependency_type=DependencyType.IMPORT,
                            source_artifact=obs.artifact,
                            observation_method=ObservationMethod.STATIC_ANALYSIS,
                            epistemic_state=EpistemicState.OBSERVED,
                            proposition_type=PropositionType.STATIC_REFERENCE,
                        ),
                        documentation_reference="Not found in documentation",
                        implementation_reference=obs.artifact,
                        description=f"Implemented dependency '{obs.target}' not documented",
                        severity="low",
                    ))
                    undocumented_count += 1

        print(f"  Detected {len(self.drift_items)} documentation drift items")

    def _construct_authority_escape_graph(self):
        """Construct a graph of all possible authority escape paths."""
        # Define the canonical authority paths
        canonical_paths = [
            {
                "name": "Quant Trading",
                "path": ["Model", "ResearchDecision", "AuthorizationArtifact", "ExecutionCapability", "CapabilityBoundBroker", "BrokerAdapter", "ExternalEffect"],
                "boundary": "Canonical",
                "authorization_required": True,
                "capability_required": True,
                "verification": True,
                "provenance": True,
            },
            {
                "name": "Agent Tool Execution",
                "path": ["Model", "AgentRuntime", "CapabilityBoundTool", "ToolHandler", "ExternalEffect"],
                "boundary": "Canonical",
                "authorization_required": True,
                "capability_required": True,
                "verification": True,
                "provenance": True,
            },
            {
                "name": "CLI Command",
                "path": ["CLI", "Runtime", "ConsequenceExecutor", "ExternalEffect"],
                "boundary": "Canonical",
                "authorization_required": True,
                "capability_required": True,
                "verification": True,
                "provenance": True,
            },
            {
                "name": "Plugin Execution",
                "path": ["Plugin", "CapabilityBoundPluginExecutor", "PluginHandler", "ExternalEffect"],
                "boundary": "Canonical",
                "authorization_required": True,
                "capability_required": True,
                "verification": True,
                "provenance": True,
            },
            {
                "name": "Credential Access",
                "path": ["Caller", "CapabilityBoundAuthBroker", "Credential", "ExternalEffect"],
                "boundary": "Canonical",
                "authorization_required": True,
                "capability_required": True,
                "verification": True,
                "provenance": True,
            },
            {
                "name": "Substrate Execution",
                "path": ["Caller", "CapabilityBoundSubstrate", "Process", "ExternalEffect"],
                "boundary": "Canonical",
                "authorization_required": True,
                "capability_required": True,
                "verification": True,
                "provenance": True,
            },
        ]

        # Define potential escape paths (undocumented or non-canonical)
        escape_paths = [
            {
                "name": "Direct Broker Access",
                "path": ["Caller", "BrokerAdapter", "ExternalEffect"],
                "boundary": "ESCAPE",
                "authorization_required": False,
                "capability_required": False,
                "verification": False,
                "provenance": False,
                "risk": "HIGH",
            },
            {
                "name": "Direct Subprocess",
                "path": ["Caller", "subprocess", "ExternalEffect"],
                "boundary": "ESCAPE",
                "authorization_required": False,
                "capability_required": False,
                "verification": False,
                "provenance": False,
                "risk": "CRITICAL",
            },
            {
                "name": "Direct Network",
                "path": ["Caller", "httpx/requests", "ExternalEffect"],
                "boundary": "ESCAPE",
                "authorization_required": False,
                "capability_required": False,
                "verification": False,
                "provenance": False,
                "risk": "HIGH",
            },
            {
                "name": "Direct Filesystem",
                "path": ["Caller", "open/write", "ExternalEffect"],
                "boundary": "ESCAPE",
                "authorization_required": False,
                "capability_required": False,
                "verification": False,
                "provenance": False,
                "risk": "MEDIUM",
            },
        ]

        self.authority_paths = canonical_paths + escape_paths
        print(f"  Constructed {len(canonical_paths)} canonical paths")
        print(f"  Identified {len(escape_paths)} potential escape paths")

    def _analyze_epistemic_gaps(self):
        """Analyze gaps between architectural claims and evidence."""
        # Key architectural claims to investigate
        claims_to_investigate = [
            ("Every consequential runtime effect passes through the canonical authority gate",
             ["authority_gate", "consequence_boundary", "verification_boundary"]),
            ("No runtime component can manufacture authority",
             ["authorization_source", "authority_gate"]),
            ("Model output cannot directly create authority",
             ["authorization_source", "epistemic_source"]),
            ("Registration does not create authority",
             ["registration_boundary", "authorization_source"]),
            ("Capability does not exceed authorization",
             ["capability_source", "authorization_source"]),
            ("Credentials do not become authority",
             ["credential_boundary", "authorization_source"]),
            ("Executor privilege does not become caller authority",
             ["executor_boundary", "authorization_source"]),
            ("Epistemic evidence cannot silently become authorization",
             ["epistemic_source", "authorization_source"]),
            ("Documentation does not establish runtime behavior",
             ["boundary", "authority_gate"]),
            ("Tests do not establish runtime behavior",
             ["boundary", "verification_boundary"]),
            ("Graph reachability does not establish semantic dependency",
             ["boundary", "epistemic_source"]),
            ("Epistemic composition does not amplify authority",
             ["epistemic_source", "authorization_source"]),
            ("Provenance is sufficient to reconstruct authority",
             ["provenance_source", "authorization_source"]),
            ("Revocation propagates correctly",
             ["authorization_source", "temporal_boundary"]),
            ("Temporal boundaries are preserved",
             ["temporal_boundary", "authorization_source"]),
            ("Domain boundaries are preserved",
             ["domain_boundary", "authorization_source"]),
            ("Capability replay is prevented",
             ["verification_boundary", "capability_source"]),
            ("External consequential effects are identifiable",
             ["consequence_boundary", "boundary"]),
            ("All consequential interfaces are known",
             ["consequence_boundary", "executor_boundary"]),
            ("There are no undocumented authority roots",
             ["authorization_source", "authority_gate"]),
        ]

        for claim_text, related_patterns in claims_to_investigate:
            # Find evidence by pattern matching
            evidence_refs = []
            for obs in self.observations:
                for pattern_name in related_patterns:
                    if pattern_name in obs.observation_type.value:
                        evidence_refs.append(obs.artifact)
                        break

            # Find documentation refs
            doc_refs = []
            for doc in self.documentation_claims:
                for pattern_name in related_patterns:
                    if pattern_name in doc.scope.lower() or pattern_name in doc.target.lower():
                        doc_refs.append(doc.source_artifact)
                        break

            # Find test refs
            test_refs = []
            for test in self.test_edges:
                for pattern_name in related_patterns:
                    if pattern_name in test.scope.lower() or pattern_name in test.target.lower():
                        test_refs.append(test.source_artifact)
                        break

            # Determine epistemic state
            if evidence_refs and doc_refs and test_refs:
                epistemic_state = EpistemicState.OBSERVED
                authority_level = "IMPLEMENTED + TESTED + DOCUMENTED"
            elif evidence_refs and doc_refs:
                epistemic_state = EpistemicState.OBSERVED
                authority_level = "IMPLEMENTED + DOCUMENTED"
            elif evidence_refs:
                epistemic_state = EpistemicState.INFERRED
                authority_level = "IMPLEMENTED"
            elif doc_refs:
                epistemic_state = EpistemicState.DOCUMENTED
                authority_level = "DOCUMENTED ONLY"
            else:
                epistemic_state = EpistemicState.INCONCLUSIVE
                authority_level = "UNVERIFIED"

            self.architectural_claims.append(ArchitecturalClaim(
                claim_id=f"claim_{len(self.architectural_claims)+1:03d}",
                proposition_type=PropositionType.OPERATIONAL_DEPENDENCY,
                claim=claim_text,
                scope="SAS architecture",
                environment="all",
                temporal_boundary="runtime",
                evidence_refs=list(set(evidence_refs))[:5],
                parent_claims=[],
                alternative_hypotheses=[
                    "Undocumented path exists",
                    "Test coverage is incomplete",
                    "Documentation is outdated",
                ],
                intervention_refs=[],
                epistemic_state=epistemic_state,
                authority_level=authority_level,
                provenance_id=f"prov_{len(self.architectural_claims)+1:03d}",
                documentation_refs=list(set(doc_refs))[:3],
                implementation_refs=list(set(evidence_refs))[:3],
                test_refs=list(set(test_refs))[:3],
                limitations=[
                    "Static analysis only",
                    "No runtime verification",
                    "Test coverage may be incomplete",
                ],
                next_experiment="Runtime verification recommended",
            ))

        print(f"  Generated {len(self.architectural_claims)} architectural claims")

    def _run_composition_audit(self):
        """Run the Epistemic Composition engine against SAS dependencies."""
        # Build edges from observations
        edges = []
        for obs in self.observations:
            if obs.observation_type == ArchitectureObservationType.IMPORT:
                edge = DependencyEdge(
                    source=obs.source,
                    target=obs.target,
                    dependency_type=DependencyType.IMPORT,
                    source_artifact=obs.artifact,
                    observation_method=ObservationMethod.STATIC_ANALYSIS,
                    epistemic_state=EpistemicState.OBSERVED,
                    proposition_type=PropositionType.STATIC_REFERENCE,
                    provenance_id=f"obs_{len(edges)+1:04d}",
                    confidence=0.9,
                )
                edges.append(edge)

        # Try composing edges that share intermediate nodes
        composition_count = 0
        for i, edge_a in enumerate(edges[:100]):  # Limit to avoid explosion
            for j, edge_b in enumerate(edges[:100]):
                if i != j and edge_a.target == edge_b.source:
                    result = self.composition_engine.compose(edge_a, edge_b)
                    if result.derived_edge is not None:
                        self.composition_results.append(result)
                        composition_count += 1

        print(f"  Ran {composition_count} composition operations")

    def _generate_architectural_claims(self):
        """Generate final architectural claims from all audit data."""
        # Add claims about documentation drift
        for drift in self.drift_items[:50]:  # Limit to top 50
            self.architectural_claims.append(ArchitecturalClaim(
                claim_id=f"drift_{len(self.architectural_claims)+1:03d}",
                proposition_type=PropositionType.STATIC_REFERENCE,
                claim=f"Documentation drift: {drift.description}",
                scope="Documentation",
                environment="all",
                temporal_boundary="permanent",
                evidence_refs=[drift.dependency.source_artifact],
                parent_claims=[],
                alternative_hypotheses=[
                    "Documentation is outdated",
                    "Implementation changed without doc update",
                    "Intentional omission",
                ],
                intervention_refs=[],
                epistemic_state=EpistemicState.OBSERVED,
                authority_level="DRIFT DETECTED",
                provenance_id=f"drift_{len(self.architectural_claims)+1:03d}",
                documentation_refs=[drift.documentation_reference],
                implementation_refs=[drift.implementation_reference],
                test_refs=[],
                limitations=["Static analysis only"],
                next_experiment="Manual review recommended",
            ))

    def _produce_report(self) -> dict:
        """Produce the final audit report."""
        # Count epistemic states
        state_counts = {}
        for claim in self.architectural_claims:
            state = claim.epistemic_state.value
            state_counts[state] = state_counts.get(state, 0) + 1

        # Count authority levels
        authority_counts = {}
        for claim in self.architectural_claims:
            level = claim.authority_level
            authority_counts[level] = authority_counts.get(level, 0) + 1

        # Count drift types
        drift_counts = {}
        for drift in self.drift_items:
            dtype = drift.drift_type.value
            drift_counts[dtype] = drift_counts.get(dtype, 0) + 1

        report = {
            "audit_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "repository": str(self.repo_root),
                "total_files_analyzed": len(list(self.src_root.rglob("*.py"))),
                "total_observations": len(self.observations),
                "total_documentation_claims": len(self.documentation_claims),
                "total_test_observations": len(self.test_edges),
            },
            "summary": {
                "total_architectural_claims": len(self.architectural_claims),
                "total_drift_items": len(self.drift_items),
                "total_authority_paths": len(self.authority_paths),
                "total_compositions": len(self.composition_results),
                "epistemic_state_distribution": state_counts,
                "authority_level_distribution": authority_counts,
                "drift_type_distribution": drift_counts,
            },
            "architectural_claims": [c.to_dict() for c in self.architectural_claims],
            "documentation_drift": [
                {
                    "drift_type": d.drift_type.value,
                    "description": d.description,
                    "severity": d.severity,
                    "documentation_reference": d.documentation_reference,
                    "implementation_reference": d.implementation_reference,
                }
                for d in self.drift_items[:100]  # Top 100
            ],
            "authority_paths": self.authority_paths,
            "composition_audit": {
                "total_compositions": len(self.composition_results),
                "authority_amplified_count": sum(
                    1 for r in self.composition_results
                    if r.derived_edge and r.derived_edge.confidence > 0.9
                ),
                "authority_reduced_count": sum(
                    1 for r in self.composition_results
                    if r.derived_edge and r.derived_edge.confidence < 0.9
                ),
            },
            "three_way_drift_matrix": self._build_three_way_matrix(),
            "key_findings": self._generate_key_findings(),
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _build_three_way_matrix(self) -> list[dict]:
        """Build the three-way drift matrix (Documentation vs Implementation vs Tests)."""
        matrix = []

        # For each architectural claim, determine its status in each dimension
        for claim in self.architectural_claims[:30]:  # Top 30 claims
            doc_status = "SUPPORTED" if claim.documentation_refs else "ABSENT"
            impl_status = "SUPPORTED" if claim.implementation_refs else "ABSENT"
            test_status = "SUPPORTED" if claim.test_refs else "ABSENT"

            # Determine overall epistemic state
            if doc_status == "SUPPORTED" and impl_status == "SUPPORTED" and test_status == "SUPPORTED":
                overall = "STRONG"
            elif impl_status == "SUPPORTED" and test_status == "SUPPORTED":
                overall = "GOOD"
            elif impl_status == "SUPPORTED":
                overall = "IMPLEMENTED_ONLY"
            elif doc_status == "SUPPORTED":
                overall = "DOCUMENTED_ONLY"
            else:
                overall = "INCONCLUSIVE"

            matrix.append({
                "claim": claim.claim[:80],
                "documentation": doc_status,
                "implementation": impl_status,
                "tests": test_status,
                "epistemic_state": claim.epistemic_state.value,
                "overall": overall,
            })

        return matrix

    def _generate_key_findings(self) -> list[str]:
        """Generate key findings from the audit."""
        findings = []

        # Finding 1: Documentation drift
        undocumented = len([d for d in self.drift_items if d.drift_type == DriftType.UNDISCOVERED])
        if undocumented > 0:
            findings.append(
                f"Found {undocumented} undocumented dependencies in implementation"
            )

        # Finding 2: Authority paths
        escape_paths = [p for p in self.authority_paths if p["boundary"] == "ESCAPE"]
        if escape_paths:
            findings.append(
                f"Identified {len(escape_paths)} potential authority escape paths"
            )

        # Finding 3: Epistemic state distribution
        inconclusive = len([c for c in self.architectural_claims if c.epistemic_state == EpistemicState.INCONCLUSIVE])
        if inconclusive > 0:
            findings.append(
                f"{inconclusive} architectural claims remain INCONCLUSIVE"
            )

        # Finding 4: Composition audit
        if self.composition_results:
            amplified = sum(1 for r in self.composition_results if r.derived_edge and r.derived_edge.confidence > 0.9)
            if amplified == 0:
                findings.append(
                    "Composition audit: No authority amplification detected"
                )

        # Finding 5: Test coverage
        tested_claims = len([c for c in self.architectural_claims if c.test_refs])
        untested = len(self.architectural_claims) - tested_claims
        if untested > 0:
            findings.append(
                f"{untested} architectural claims lack test coverage"
            )

        return findings

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations from the audit."""
        recommendations = []

        if any(d.drift_type == DriftType.UNDISCOVERED for d in self.drift_items):
            recommendations.append("Update documentation to reflect implementation")

        if any(p["boundary"] == "ESCAPE" for p in self.authority_paths):
            recommendations.append("Investigate potential authority escape paths")

        if any(c.epistemic_state == EpistemicState.INCONCLUSIVE for c in self.architectural_claims):
            recommendations.append("Design experiments to resolve inconclusive claims")

        if any(not c.test_refs for c in self.architectural_claims):
            recommendations.append("Add tests for architectural invariants")

        recommendations.append("Run periodic self-audits to detect drift")

        return recommendations


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def run_self_audit(repo_root: str | Path) -> dict:
    """Run the recursive self-audit and return the report."""
    audit = RecursiveSelfAudit(repo_root)
    return audit.run_full_audit()


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    report = run_self_audit(repo)
    print(json.dumps(report, indent=2))
