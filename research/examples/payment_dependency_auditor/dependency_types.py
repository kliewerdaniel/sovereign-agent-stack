"""Dependency Ontology — typed taxonomy for payment infrastructure dependencies.

This module defines the dependency types and epistemic states for the
Sovereign Payment Infrastructure Dependency Auditor.

Critical distinction:
    STATIC_REFERENCE ≠ RUNTIME_DEPENDENCY ≠ OPERATIONAL_NECESSITY

Each dependency edge carries epistemic state, not just existence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Dependency Types
# ---------------------------------------------------------------------------


class DependencyType(str, Enum):
    """Types of dependencies that can exist between services.

    Each type represents a different semantic relationship.
    Evidence for one type does NOT automatically authorize another.
    """

    IMPORT = "import"                    # Code imports another module
    CALL = "call"                        # Function/method call
    NETWORK = "network"                  # HTTP/gRPC network call
    DATABASE = "database"                # Database connection
    QUEUE = "queue"                      # Message queue
    FILESYSTEM = "filesystem"            # File system access
    PROCESS = "process"                  # Subprocess execution
    CONFIGURATION = "configuration"      # Configuration reference
    CREDENTIAL = "credential"            # Credential access
    IDENTITY = "identity"                # Identity/auth dependency
    SERVICE = "service"                  # Service-to-service call
    SCHEMA = "schema"                    # Schema reference
    TEMPORAL = "temporal"                # Time-dependent dependency
    ENVIRONMENT = "environment"          # Environment-specific dependency
    DOCUMENTATION = "documentation"      # Documentation reference
    TEST = "test"                        # Test fixture dependency
    TRANSITIVE = "transitive"            # Transitive dependency


class EpistemicState(str, Enum):
    """Epistemic state of a dependency claim.

    The state represents what the evidence actually establishes,
    not what the model believes.
    """

    DOCUMENTED = "documented"                    # Appears in documentation
    OBSERVED = "observed"                        # Observed in code/config
    INFERRED = "inferred"                        # Inferred from patterns
    HYPOTHESIZED = "hypothesized"                # Proposed but unverified
    EXPERIMENTALLY_SUPPORTED = "experimentally_supported"  # Supported by experiment
    CONTRADICTED = "contradicted"                # Evidence contradicts
    INCONCLUSIVE = "inconclusive"                # Insufficient evidence
    UNKNOWN = "unknown"                          # No evidence either way


class PropositionType(str, Enum):
    """Types of dependency propositions.

    Each proposition type requires different evidence to establish.
    Evidence for one type cannot automatically authorize another.
    """

    STATIC_REFERENCE = "static_reference"        # Code mentions something
    CONFIGURATION_DEPENDENCY = "configuration_dependency"  # Config references it
    RUNTIME_DEPENDENCY = "runtime_dependency"    # Required at runtime
    OPERATIONAL_DEPENDENCY = "operational_dependency"  # Required for operation
    FAILURE_DEPENDENCY = "failure_dependency"    # Causes failure if unavailable
    TEMPORAL_DEPENDENCY = "temporal_dependency"  # Only at specific times
    ENVIRONMENT_DEPENDENCY = "environment_dependency"  # Only in some environments
    TRANSITIVE_DEPENDENCY = "transitive_dependency"  # Through another service


class ObservationMethod(str, Enum):
    """How the dependency was observed."""

    STATIC_ANALYSIS = "static_analysis"         # Code parsing
    CONFIGURATION_PARSE = "configuration_parse" # Config file parsing
    DOCUMENTATION_PARSE = "documentation_parse" # Doc parsing
    RUNTIME_TEST = "runtime_test"               # Runtime experiment
    FAILURE_INJECTION = "failure_injection"     # Failure experiment
    MANUAL_VERIFICATION = "manual_verification" # Human verification


# ---------------------------------------------------------------------------
# Dependency Edge
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyEdge:
    """A single dependency edge with full epistemic provenance.

    This is NOT a simple graph edge. It carries the complete epistemic
    state necessary to reconstruct why the dependency claim exists.

    Attributes:
        source: Source service/module
        target: Target service/module
        dependency_type: Type of dependency
        source_artifact: File/path where observed
        source_location: Line number or location
        observation_method: How it was observed
        environment: Which environment (production/staging/all)
        epistemic_state: Current epistemic state
        proposition_type: What kind of proposition this supports
        evidence: List of evidence references
        alternatives: Alternative explanations considered
        experiment: Experiment that established this (if any)
        scope: Scope of the claim (what it does and doesn't establish)
        limitations: Known limitations of the claim
        provenance_id: Unique provenance identifier
        created_at: When this claim was created
        confidence: Explicit confidence (NOT authority)
    """

    source: str
    target: str
    dependency_type: DependencyType
    source_artifact: str
    source_location: str = ""
    observation_method: ObservationMethod = ObservationMethod.STATIC_ANALYSIS
    environment: str = "all"
    epistemic_state: EpistemicState = EpistemicState.OBSERVED
    proposition_type: PropositionType = PropositionType.STATIC_REFERENCE
    evidence: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    experiment: Optional[str] = None
    scope: str = ""
    limitations: list[str] = field(default_factory=list)
    provenance_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = 0.0  # NOT authority — merely a stated certainty

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "dependency_type": self.dependency_type.value,
            "source_artifact": self.source_artifact,
            "source_location": self.source_location,
            "observation_method": self.observation_method.value,
            "environment": self.environment,
            "epistemic_state": self.epistemic_state.value,
            "proposition_type": self.proposition_type.value,
            "evidence": list(self.evidence),
            "alternatives": list(self.alternatives),
            "experiment": self.experiment,
            "scope": self.scope,
            "limitations": list(self.limitations),
            "provenance_id": self.provenance_id,
            "created_at": self.created_at,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# Documentation Drift
# ---------------------------------------------------------------------------


class DriftType(str, Enum):
    """Types of documentation drift."""

    DOCUMENTED_EXISTS = "documented_exists"           # Doc says exists, does
    DOCUMENTED_REMOVED = "documented_removed"          # Doc says exists, removed
    UNDISCOVERED = "undiscovered"                      # Exists but not documented
    WRONG_MECHANISM = "wrong_mechanism"                # Doc describes wrong mechanism
    WRONG_ENVIRONMENT = "wrong_environment"            # Doc says wrong environment
    MISSING_CONDITIONAL = "missing_conditional"        # Doc omits conditional
    WRONG_CRITICALITY = "wrong_criticality"            # Doc says required but optional


@dataclass(frozen=True)
class DocumentationDrift:
    """A discrepancy between documentation and implementation."""

    drift_type: DriftType
    dependency: DependencyEdge
    documentation_reference: str
    implementation_reference: str
    description: str
    severity: str = "medium"  # low, medium, high, critical


# ---------------------------------------------------------------------------
# Dependency Criticality
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyCriticality:
    """Criticality assessment for a dependency.

    IMPORTANT: Dependency existence ≠ criticality.
    A service may depend on something without being unable to operate
    when that dependency disappears.
    """

    source: str
    target: str
    exists: bool = True              # Does the dependency exist?
    necessary: bool = False          # Is it necessary for operation?
    centrality: float = 0.0          # How central (0-1)
    failure_impact: str = "none"     # Impact if dependency fails
    scope: str = ""                  # Scope of the assessment
    reversible: bool = True          # Can the dependency be reversed?
    environment: str = "all"         # Which environment
