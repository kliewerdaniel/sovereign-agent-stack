"""Dependency Intersection Evaluator.

Determines whether new evidence intersects an authorization's dependency graph.

The critical operation is not:
    "did new evidence appear?"

It is:
    "does the new evidence intersect a dependency of this authorization?"

This is the core mechanism for dependency-sensitive invalidation.
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
    DependencyStrength,
    DependencyType,
    IntersectionResult,
    StalenessType,
)


class EvidenceType(str, Enum):
    """Types of evidence that can arrive."""
    OBSERVATION = "observation"
    EXPERIMENT_RESULT = "experiment_result"
    ASSERTION = "assertion"
    MEASUREMENT = "measurement"
    REPORT = "report"


class EvidenceRelation(str, Enum):
    """Relation of new evidence to existing evidence."""
    UNRELATED = "unrelated"
    RELEVANT = "relevant"
    WEAKENS = "weakens"
    CONTRADICTS = "contradicts"
    INVALIDATES_EXPERIMENT = "invalidates_experiment"
    CHANGES_RESOURCE = "changes_resource"
    CHANGES_GOVERNANCE = "changes_governance"
    HISTORICAL = "historical"


@dataclass(frozen=True)
class Evidence:
    """A piece of evidence."""
    evidence_id: str
    evidence_type: EvidenceType
    content: str
    timestamp: str
    source: str
    provenance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntersectionEvaluation:
    """Result of evaluating whether new evidence intersects an authorization."""
    evaluation_id: str
    timestamp: str
    authorization_id: str
    evidence_id: str
    result: IntersectionResult
    affected_dependencies: list[str] = field(default_factory=list)
    staleness: Optional[StalenessType] = None
    description: str = ""
    requires_reevaluation: bool = False
    requires_suspension: bool = False


@dataclass
class DependencyIntersectionEvaluator:
    """Evaluates whether new evidence intersects authorization dependencies."""

    def evaluate(
        self,
        new_evidence: Evidence,
        auth_graph: AuthorizationDependencyGraph,
    ) -> IntersectionEvaluation:
        """Evaluate whether new evidence intersects authorization dependencies.

        This is the core operation for dependency-sensitive invalidation.
        It distinguishes:
        - DIRECT_DEPENDENCY: Evidence directly affects a dependency
        - TRANSITIVE_DEPENDENCY: Evidence transitively affects a dependency
        - UNRELATED: Evidence has no relation to any dependency
        - UNKNOWN_DEPENDENCY: Cannot determine relation
        - CONTRADICTORY_DEPENDENCY: Evidence contradicts a dependency
        - DEPENDENCY_CHANGED: Evidence changes a dependency but doesn't contradict
        """
        # Determine the relation of the new evidence
        relation = self._classify_relation(new_evidence, auth_graph)

        if relation == EvidenceRelation.UNRELATED:
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.UNRELATED,
                description="Evidence does not intersect any authorization dependency",
            )

        if relation == EvidenceRelation.HISTORICAL:
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.UNRELATED,
                description="Evidence concerns only historical state",
            )

        if relation == EvidenceRelation.RELEVANT:
            affected = self._find_affected_dependencies(new_evidence, auth_graph)
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.TRANSITIVE_DEPENDENCY,
                affected_dependencies=affected,
                description="Evidence is relevant to authorization dependencies",
                requires_reevaluation=True,
            )

        if relation == EvidenceRelation.WEAKENS:
            affected = self._find_affected_dependencies(new_evidence, auth_graph)
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.DEPENDENCY_CHANGED,
                affected_dependencies=affected,
                staleness=StalenessType.EPISTEMICALLY_STALE,
                description="Evidence weakens a dependency",
                requires_reevaluation=True,
            )

        if relation == EvidenceRelation.CONTRADICTS:
            affected = self._find_affected_dependencies(new_evidence, auth_graph)
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.CONTRADICTORY_DEPENDENCY,
                affected_dependencies=affected,
                staleness=StalenessType.EPISTEMICALLY_STALE,
                description="Evidence contradicts a dependency",
                requires_reevaluation=True,
                requires_suspension=True,
            )

        if relation == EvidenceRelation.INVALIDATES_EXPERIMENT:
            affected = self._find_experiment_dependencies(auth_graph)
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.CONTRADICTORY_DEPENDENCY,
                affected_dependencies=affected,
                staleness=StalenessType.EPISTEMICALLY_STALE,
                description="Evidence invalidates experiment that produced original evidence",
                requires_reevaluation=True,
                requires_suspension=True,
            )

        if relation == EvidenceRelation.CHANGES_RESOURCE:
            affected = self._find_resource_dependencies(auth_graph)
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.DEPENDENCY_CHANGED,
                affected_dependencies=affected,
                staleness=StalenessType.RESOURCE_STALE,
                description="Evidence changes resource state",
                requires_reevaluation=True,
            )

        if relation == EvidenceRelation.CHANGES_GOVERNANCE:
            affected = self._find_governance_dependencies(auth_graph)
            return self._create_evaluation(
                new_evidence, auth_graph, IntersectionResult.DEPENDENCY_CHANGED,
                affected_dependencies=affected,
                staleness=StalenessType.GOVERNANCE_STALE,
                description="Evidence changes governance state",
                requires_reevaluation=True,
            )

        return self._create_evaluation(
            new_evidence, auth_graph, IntersectionResult.UNKNOWN_DEPENDENCY,
            description="Cannot determine evidence relation to dependencies",
            requires_reevaluation=True,
        )

    def _classify_relation(
        self,
        new_evidence: Evidence,
        auth_graph: AuthorizationDependencyGraph,
    ) -> EvidenceRelation:
        """Classify the relation of new evidence to authorization dependencies."""
        # Check for direct evidence dependency intersection
        for dep in auth_graph.get_dependencies_by_type(DependencyType.EVIDENCE):
            if new_evidence.evidence_id == dep.target_id:
                # Same evidence - check if it contradicts or weakens
                return self._classify_evidence_relation(new_evidence, dep)

        # Check for proposition dependency intersection
        for dep in auth_graph.get_dependencies_by_type(DependencyType.PROPOSITION):
            if self._evidence_contradicts_proposition(new_evidence, dep):
                return EvidenceRelation.CONTRADICTS
            if self._evidence_weakens_proposition(new_evidence, dep):
                return EvidenceRelation.WEAKENS
            if self._evidence_relevant_to_proposition(new_evidence, dep):
                return EvidenceRelation.RELEVANT

        # Check for resource dependency intersection
        for dep in auth_graph.get_dependencies_by_type(DependencyType.RESOURCE_IDENTITY):
            if self._evidence_changes_resource(new_evidence, dep):
                return EvidenceRelation.CHANGES_RESOURCE

        # Check for governance dependency intersection
        for dep in auth_graph.get_dependencies_by_type(DependencyType.GOVERNANCE_POLICY):
            if self._evidence_changes_governance(new_evidence, dep):
                return EvidenceRelation.CHANGES_GOVERNANCE

        # Check for experiment dependency intersection
        for dep in auth_graph.get_dependencies_by_type(DependencyType.EXPERIMENT):
            if self._evidence_invalidates_experiment(new_evidence, dep):
                return EvidenceRelation.INVALIDATES_EXPERIMENT

        # Check if evidence concerns historical state
        if self._evidence_is_historical(new_evidence):
            return EvidenceRelation.HISTORICAL

        return EvidenceRelation.UNRELATED

    def _classify_evidence_relation(
        self,
        new_evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> EvidenceRelation:
        """Classify how new evidence relates to an existing evidence dependency."""
        dep_content = dependency.metadata.get("content", "")
        if self._contents_contradict(new_evidence.content, dep_content):
            return EvidenceRelation.CONTRADICTS
        if self._contents_weaken(new_evidence.content, dep_content):
            return EvidenceRelation.WEAKENS
        return EvidenceRelation.RELEVANT

    def _find_affected_dependencies(
        self,
        new_evidence: Evidence,
        auth_graph: AuthorizationDependencyGraph,
    ) -> list[str]:
        """Find dependencies affected by new evidence."""
        affected = []
        for dep in auth_graph.dependencies:
            if self._evidence_affects_dependency(new_evidence, dep):
                affected.append(dep.dependency_id)
        return affected

    def _find_experiment_dependencies(
        self,
        auth_graph: AuthorizationDependencyGraph,
    ) -> list[str]:
        """Find experiment dependencies."""
        return [
            dep.dependency_id
            for dep in auth_graph.get_dependencies_by_type(DependencyType.EXPERIMENT)
        ]

    def _find_resource_dependencies(
        self,
        auth_graph: AuthorizationDependencyGraph,
    ) -> list[str]:
        """Find resource dependencies."""
        return [
            dep.dependency_id
            for dep in auth_graph.get_dependencies_by_type(DependencyType.RESOURCE_IDENTITY)
        ]

    def _find_governance_dependencies(
        self,
        auth_graph: AuthorizationDependencyGraph,
    ) -> list[str]:
        """Find governance dependencies."""
        return [
            dep.dependency_id
            for dep in auth_graph.get_dependencies_by_type(DependencyType.GOVERNANCE_POLICY)
        ]

    def _evidence_contradicts_proposition(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence contradicts a proposition dependency."""
        # Check if evidence content contradicts the proposition
        proposition_id = dependency.target_id
        evidence_content = evidence.content.lower()
        # Heuristic: check for negation patterns
        if "not" in evidence_content and proposition_id in evidence_content:
            return True
        if "contradicts" in evidence_content and proposition_id in evidence_content:
            return True
        return False

    def _evidence_weakens_proposition(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence weakens a proposition dependency."""
        proposition_id = dependency.target_id
        evidence_content = evidence.content.lower()
        if "uncertain" in evidence_content and proposition_id in evidence_content:
            return True
        if "weaken" in evidence_content and proposition_id in evidence_content:
            return True
        return False

    def _evidence_relevant_to_proposition(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence is relevant to a proposition dependency."""
        proposition_id = dependency.target_id
        return proposition_id in evidence.content

    def _evidence_changes_resource(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence changes resource state."""
        resource_id = dependency.target_id
        evidence_content = evidence.content.lower()
        return resource_id in evidence_content and ("changed" in evidence_content or "new" in evidence_content)

    def _evidence_changes_governance(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence changes governance state."""
        governance_id = dependency.target_id
        evidence_content = evidence.content.lower()
        return governance_id in evidence_content and ("updated" in evidence_content or "new" in evidence_content)

    def _evidence_invalidates_experiment(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence invalidates an experiment dependency."""
        experiment_id = dependency.target_id
        evidence_content = evidence.content.lower()
        return experiment_id in evidence_content and ("invalid" in evidence_content or "flawed" in evidence_content)

    def _evidence_is_historical(
        self,
        evidence: Evidence,
    ) -> bool:
        """Check if evidence concerns only historical state."""
        evidence_content = evidence.content.lower()
        return "historical" in evidence_content or "past" in evidence_content

    def _contents_contradict(self, content1: str, content2: str) -> bool:
        """Check if two contents contradict each other."""
        c1 = content1.lower()
        c2 = content2.lower()
        # Simple heuristic: check for negation
        if "safe" in c1 and "unsafe" in c2:
            return True
        if "active" in c1 and "inactive" in c2:
            return True
        return False

    def _contents_weaken(self, content1: str, content2: str) -> bool:
        """Check if content1 weakens content2."""
        c1 = content1.lower()
        c2 = content2.lower()
        if "uncertain" in c1 and "certain" in c2:
            return True
        return False

    def _evidence_affects_dependency(
        self,
        evidence: Evidence,
        dependency: AuthorizationDependency,
    ) -> bool:
        """Check if evidence affects a dependency."""
        # Direct ID match
        if evidence.evidence_id == dependency.target_id:
            return True
        # Content relevance
        if dependency.target_id in evidence.content:
            return True
        # Source relevance
        if evidence.source in dependency.provenance:
            return True
        return False

    def _create_evaluation(
        self,
        new_evidence: Evidence,
        auth_graph: AuthorizationDependencyGraph,
        result: IntersectionResult,
        affected_dependencies: list[str] | None = None,
        staleness: StalenessType | None = None,
        description: str = "",
        requires_reevaluation: bool = False,
        requires_suspension: bool = False,
    ) -> IntersectionEvaluation:
        """Create an intersection evaluation result."""
        return IntersectionEvaluation(
            evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            authorization_id=auth_graph.authorization_id,
            evidence_id=new_evidence.evidence_id,
            result=result,
            affected_dependencies=affected_dependencies or [],
            staleness=staleness,
            description=description,
            requires_reevaluation=requires_reevaluation,
            requires_suspension=requires_suspension,
        )


def evaluate_evidence_against_authorization(
    new_evidence: Evidence,
    auth_graph: AuthorizationDependencyGraph,
) -> IntersectionEvaluation:
    """Convenience function to evaluate evidence against an authorization."""
    evaluator = DependencyIntersectionEvaluator()
    return evaluator.evaluate(new_evidence, auth_graph)
