"""Hypothesis Generator — construct explicit hypotheses for suspicious dependencies.

For every candidate undocumented dependency, construct an explicit hypothesis
with alternatives, required experiments, and scope boundaries.

CRITICAL: The model may generate hypotheses. The model does not establish them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from research.examples.payment_dependency_auditor.dependency_types import (
    DependencyEdge,
    DependencyType,
    EpistemicState,
    PropositionType,
)


# ---------------------------------------------------------------------------
# Hypothesis Artifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyHypothesis:
    """An explicit hypothesis about a dependency.

    A hypothesis is NOT a claim that the dependency exists.
    It is a testable proposition that can be supported, refuted, or left inconclusive.

    Attributes:
        hypothesis_id: Unique identifier
        source: Source service
        target: Target service
        dependency_type: Type of dependency proposed
        proposition_type: What kind of proposition this is
        claim: Human-readable statement of the hypothesis
        candidate_mechanism: How the dependency might work
        alternative_explanations: Alternative explanations for the observation
        required_experiment: What experiment would discriminate this hypothesis
        scope: Scope boundary (environment, time, conditions)
        falsification_conditions: Conditions that would refute this hypothesis
        created_at: When this hypothesis was created
    """

    hypothesis_id: str
    source: str
    target: str
    dependency_type: DependencyType
    proposition_type: PropositionType
    claim: str
    candidate_mechanism: str
    alternative_explanations: list[str] = field(default_factory=list)
    required_experiment: str = ""
    scope: str = ""
    falsification_conditions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "source": self.source,
            "target": self.target,
            "dependency_type": self.dependency_type.value,
            "proposition_type": self.proposition_type.value,
            "claim": self.claim,
            "candidate_mechanism": self.candidate_mechanism,
            "alternative_explanations": list(self.alternative_explanations),
            "required_experiment": self.required_experiment,
            "scope": self.scope,
            "falsification_conditions": list(self.falsification_conditions),
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Competing Mechanism
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompetingMechanism:
    """An alternative explanation for an observed dependency.

    For every candidate dependency, there are usually multiple explanations:
    - The code is actively used at runtime
    - The code is dead or conditional
    - The dependency is only at startup
    - The dependency is environment-specific
    - The dependency is transitive, not direct

    Attributes:
        mechanism_id: Unique identifier
        hypothesis_id: Parent hypothesis
        name: Short name for this mechanism
        description: Detailed description
        evidence_for: Evidence supporting this mechanism
        evidence_against: Evidence against this mechanism
        discriminating_experiment: What would distinguish this from alternatives
    """

    mechanism_id: str
    hypothesis_id: str
    name: str
    description: str
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    discriminating_experiment: str = ""

    def to_dict(self) -> dict:
        return {
            "mechanism_id": self.mechanism_id,
            "hypothesis_id": self.hypothesis_id,
            "name": self.name,
            "description": self.description,
            "evidence_for": list(self.evidence_for),
            "evidence_against": list(self.evidence_against),
            "discriminating_experiment": self.discriminating_experiment,
        }


# ---------------------------------------------------------------------------
# Hypothesis Generator
# ---------------------------------------------------------------------------


class HypothesisGenerator:
    """Generate explicit hypotheses for undocumented dependencies.

    For each suspicious dependency, generates:
    1. A primary hypothesis
    2. Alternative explanations (competing mechanisms)
    3. Required experiments to discriminate
    """

    def generate_hypotheses(
        self,
        edge: DependencyEdge,
    ) -> tuple[DependencyHypothesis, list[CompetingMechanism]]:
        """Generate hypotheses and alternatives for a dependency edge.

        Args:
            edge: The observed dependency edge

        Returns:
            Tuple of (primary hypothesis, list of competing mechanisms)
        """
        hypothesis = self._create_primary_hypothesis(edge)
        alternatives = self._create_competing_mechanisms(hypothesis, edge)
        return hypothesis, alternatives

    def _create_primary_hypothesis(self, edge: DependencyEdge) -> DependencyHypothesis:
        """Create the primary hypothesis for a dependency."""
        claim = (
            f"{edge.source} has a {edge.dependency_type.value} dependency "
            f"on {edge.target}"
        )

        mechanism = self._infer_mechanism(edge)
        experiment = self._suggest_experiment(edge)
        scope = self._determine_scope(edge)
        falsification = self._determine_falsification(edge)

        return DependencyHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            source=edge.source,
            target=edge.target,
            dependency_type=edge.dependency_type,
            proposition_type=edge.proposition_type,
            claim=claim,
            candidate_mechanism=mechanism,
            required_experiment=experiment,
            scope=scope,
            falsification_conditions=falsification,
        )

    def _create_competing_mechanisms(
        self,
        hypothesis: DependencyHypothesis,
        edge: DependencyEdge,
    ) -> list[CompetingMechanism]:
        """Create alternative explanations for the observation."""
        mechanisms = []

        # Mechanism 1: Active runtime dependency
        mechanisms.append(CompetingMechanism(
            mechanism_id=f"mech_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            name="active_runtime_dependency",
            description=(
                f"{edge.source} actively calls {edge.target} at runtime "
                f"as part of its core operation"
            ),
            evidence_for=[f"Code reference in {edge.source_artifact}"],
            evidence_against=["May be conditional path", "May be dead code"],
            discriminating_experiment=(
                f"Make {edge.target} unavailable and observe if "
                f"{edge.source} operation fails"
            ),
        ))

        # Mechanism 2: Startup-only dependency
        mechanisms.append(CompetingMechanism(
            mechanism_id=f"mech_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            name="startup_only_dependency",
            description=(
                f"{edge.source} only references {edge.target} during "
                f"initialization, not during normal operation"
            ),
            evidence_for=["Import at module level", "Configuration reference"],
            evidence_against=["Not consistent with runtime call pattern"],
            discriminating_experiment=(
                f"Make {edge.target} unavailable after {edge.source} "
                f"has initialized, observe if operation continues"
            ),
        ))

        # Mechanism 3: Dead code
        mechanisms.append(CompetingMechanism(
            mechanism_id=f"mech_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            name="dead_code",
            description=(
                f"The reference to {edge.target} exists in code but is "
                f"never executed at runtime (dead code)"
            ),
            evidence_for=["Code exists but may not be reachable"],
            evidence_against=["Code appears to be in active call path"],
            discriminating_experiment=(
                f"Add logging/tracing to verify if code path is executed"
            ),
        ))

        # Mechanism 4: Environment-specific dependency
        mechanisms.append(CompetingMechanism(
            mechanism_id=f"mech_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            name="environment_specific",
            description=(
                f"The dependency on {edge.target} only exists in certain "
                f"environments (e.g., production but not staging)"
            ),
            evidence_for=["Configuration may vary by environment"],
            evidence_against=["Code appears to be unconditional"],
            discriminating_experiment=(
                f"Compare behavior across environments "
                f"(development, staging, production)"
            ),
        ))

        # Mechanism 5: Optional dependency
        mechanisms.append(CompetingMechanism(
            mechanism_id=f"mech_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            name="optional_dependency",
            description=(
                f"{edge.source} can operate without {edge.target} using "
                f"defaults or fallback behavior"
            ),
            evidence_for=["May have fallback logic"],
            evidence_against=["Code appears to require the dependency"],
            discriminating_experiment=(
                f"Make {edge.target} unavailable and observe if "
                f"{edge.source} continues with degraded functionality"
            ),
        ))

        return mechanisms

    def _infer_mechanism(self, edge: DependencyEdge) -> str:
        """Infer the likely mechanism from the edge type."""
        mechanisms = {
            DependencyType.IMPORT: f"{edge.source} imports {edge.target} module",
            DependencyType.CALL: f"{edge.source} calls {edge.target} functions",
            DependencyType.NETWORK: f"{edge.source} makes HTTP calls to {edge.target}",
            DependencyType.DATABASE: f"{edge.source} connects to {edge.target} database",
            DependencyType.QUEUE: f"{edge.source} publishes/consumes from {edge.target}",
            DependencyType.CONFIGURATION: f"{edge.source} references {edge.target} in config",
            DependencyType.CREDENTIAL: f"{edge.source} accesses credentials from {edge.target}",
            DependencyType.SERVICE: f"{edge.source} depends on {edge.target} service",
        }
        return mechanisms.get(
            edge.dependency_type,
            f"{edge.source} depends on {edge.target}"
        )

    def _suggest_experiment(self, edge: DependencyEdge) -> str:
        """Suggest an experiment to test the hypothesis."""
        experiments = {
            DependencyType.NETWORK: (
                f"Make {edge.target} unavailable (connection refused/timeout) "
                f"and observe if {edge.source} operation fails"
            ),
            DependencyType.DATABASE: (
                f"Stop {edge.target} database and observe if {edge.source} "
                f"can still process operations"
            ),
            DependencyType.SERVICE: (
                f"Disable {edge.target} service and observe {edge.source} behavior"
            ),
            DependencyType.CONFIGURATION: (
                f"Remove {edge.target} from configuration and observe "
                f"if {edge.source} can initialize"
            ),
            DependencyType.IMPORT: (
                f"Remove the import of {edge.target} and verify "
                f"if {edge.source} still builds and runs"
            ),
        }
        return experiments.get(
            edge.dependency_type,
            f"Remove {edge.target} and observe {edge.source} behavior"
        )

    def _determine_scope(self, edge: DependencyEdge) -> str:
        """Determine the scope boundary for the hypothesis."""
        if edge.environment != "all":
            return f"{edge.environment} environment only"
        return "All environments (to be verified)"

    def _determine_falsification(self, edge: DependencyEdge) -> list[str]:
        """Determine conditions that would falsify the hypothesis."""
        return [
            f"{edge.target} is unavailable and {edge.source} operation succeeds",
            f"No code path in {edge.source} actually calls {edge.target}",
            f"The reference to {edge.target} is dead code",
            f"The dependency only exists in configuration but is never used",
        ]
