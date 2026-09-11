"""Dependency Completeness Authority.

Investigates whether the protocol can reason about whether an authorization's
dependency graph is complete enough for the claim and consequence being authorized.

Critical distinction:
    NO INTERSECTION FOUND ≠ DEPENDENCY GRAPH IS COMPLETE

A completeness assessment is itself an epistemic claim — not authority.

Architectural thesis:
    AUTHORITY
        ↓ DEPENDS ON
    EPISTEMIC STATE
        ↓ DEPENDS ON
    EVIDENCE
        ↓ DEPENDS ON
    DEPENDENCY MODEL
        ↓ DEPENDS ON
    COMPLETENESS CLAIM
        ↓ DEPENDS ON
    EVIDENCE ABOUT THE WORLD

But no claim may acquire authority merely by being required to justify that authority.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class CompletenessStatus(str, Enum):
    """Status of a completeness assessment."""
    KNOWN_COMPLETE = "known_complete"
    KNOWN_INCOMPLETE = "known_incomplete"
    UNKNOWN = "unknown"
    FALSE_COMPLETENESS = "false_completeness"
    UNTESTED_COMPLETENESS = "untested_completeness"
    CONDITIONAL_COMPLETENESS = "conditional_completeness"
    SCOPE_LIMITED_COMPLETENESS = "scope_limited_completeness"
    INCONCLUSIVE = "inconclusive"
    OVER_APPROXIMATED = "over_approximated"
    UNDER_APPROXIMATED = "under_approximated"


class CompletenessDimension(str, Enum):
    """Dimensions along which completeness can be assessed."""
    PROPOSITION = "proposition"
    EVIDENCE = "evidence"
    MECHANISM = "mechanism"
    CONSEQUENCE = "consequence"
    RESOURCE = "resource"
    ACTOR = "actor"
    ENVIRONMENT = "environment"
    TEMPORAL = "temporal"
    GOVERNANCE = "governance"
    EXECUTION_PATH = "execution_path"


class CompletenessMethod(str, Enum):
    """Methods for assessing dependency completeness."""
    DOCUMENTATION_DERIVED = "documentation_derived"
    STATIC_ANALYSIS_DERIVED = "static_analysis_derived"
    RUNTIME_TRACE_DERIVED = "runtime_trace_derived"
    CONTROLLED_INTERVENTION_DERIVED = "controlled_intervention_derived"
    COUNTERFACTUAL_DERIVED = "counterfactual_derived"
    GOVERNANCE_DECLARED = "governance_declared"
    MULTI_SOURCE = "multi_source"
    MODEL_HYPOTHESIZED = "model_hypothesized"


class IntersectionStatus(str, Enum):
    """Status of evidence intersection with dependency graph."""
    NO_INTERSECTION_ESTABLISHED = "no_intersection_established"
    NO_RELEVANT_DEPENDENCY_EXISTS = "no_relevant_dependency_exists"
    GRAPH_SUFFICIENTLY_COMPLETE = "graph_sufficiently_complete"
    INTERSECTION_FOUND = "intersection_found"
    CANNOT_DETERMINE = "cannot_determine"


@dataclass(frozen=True)
class CompletenessScope:
    """Scope within which a completeness claim is valid."""
    proposition_id: str
    consequence_type: str
    environment: str = "production"
    temporal_interval: str = "unbounded"
    domain: str = "sovereign"
    actor_id: str = "any"
    resource_id: str = "any"

    def matches(self, other: "CompletenessScope") -> bool:
        """Check if this scope covers another scope."""
        return (
            self.proposition_id == other.proposition_id
            and self.consequence_type == other.consequence_type
            and self.environment == other.environment
            and self.domain == other.domain
        )


@dataclass(frozen=True)
class CompletenessClaim:
    """A claim that a dependency graph is sufficiently complete.
    
    This is an epistemic artifact, NOT authority.
    """
    claim_id: str
    authorization_id: str
    graph_id: str
    status: CompletenessStatus
    scope: CompletenessScope
    method: CompletenessMethod
    confidence: float = 0.0
    timestamp: str = ""
    evidence: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    dimension_coverage: dict[str, float] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        """A completeness claim is NEVER authoritative by itself."""
        return False

    def can_support(self, scope: CompletenessScope) -> bool:
        """Check if this claim can support a claim in the given scope."""
        return self.scope.matches(scope)


@dataclass(frozen=True)
class DimensionCoverage:
    """Coverage assessment along a single dimension."""
    dimension: CompletenessDimension
    coverage_score: float  # 0.0 to 1.0
    known_elements: list[str] = field(default_factory=list)
    unknown_elements: list[str] = field(default_factory=list)
    method: CompletenessMethod = CompletenessMethod.MULTI_SOURCE
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompletenessAssessment:
    """A full completeness assessment for an authorization."""
    assessment_id: str
    authorization_id: str
    graph_id: str
    overall_status: CompletenessStatus
    scope: CompletenessScope
    dimension_coverages: list[DimensionCoverage] = field(default_factory=list)
    claims: list[CompletenessClaim] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    method_results: dict[str, CompletenessStatus] = field(default_factory=dict)
    timestamp: str = ""
    provenance: list[str] = field(default_factory=list)

    def get_coverage(self, dimension: CompletenessDimension) -> float:
        """Get coverage for a specific dimension."""
        for dc in self.dimension_coverages:
            if dc.dimension == dimension:
                return dc.coverage_score
        return 0.0

    def is_sufficiently_complete(self, threshold: float = 0.8) -> bool:
        """Check if all dimensions meet threshold.
        
        NOTE: This is a convenience check. A high score does NOT prove
        completeness — it may reflect over-approximation or false completeness.
        """
        if not self.dimension_coverages:
            return False
        return all(dc.coverage_score >= threshold for dc in self.dimension_coverages)

    def has_unknown_dimensions(self) -> bool:
        """Check if any dimension has unknown coverage."""
        return any(dc.coverage_score == 0.0 for dc in self.dimension_coverages)


@dataclass
class CompletenessEngine:
    """Engine for assessing dependency completeness.

    The engine produces epistemic claims, never authority.
    """

    def assess_completeness(
        self,
        authorization_id: str,
        graph_id: str,
        declared_dependencies: list[str],
        actual_dependencies: list[str],
        scope: CompletenessScope,
        method: CompletenessMethod = CompletenessMethod.MULTI_SOURCE,
    ) -> CompletenessAssessment:
        """Assess completeness of a dependency graph.
        
        This is the core operation: comparing declared dependencies against
        the actual (ground truth) dependency set.
        
        In production, actual_dependencies is unknown. In experiments, we
        use it to evaluate the quality of the assessment.
        """
        dimension_coverages = self._compute_dimension_coverages(
            declared_dependencies, actual_dependencies, scope, method
        )

        # Determine overall status
        overall_status = self._determine_overall_status(
            dimension_coverages, declared_dependencies, actual_dependencies, method
        )

        claims = self._generate_claims(
            authorization_id, graph_id, scope, method,
            dimension_coverages, overall_status, declared_dependencies, actual_dependencies
        )

        gaps = self._identify_gaps(declared_dependencies, actual_dependencies, scope)

        return CompletenessAssessment(
            assessment_id=f"assess_{uuid.uuid4().hex[:12]}",
            authorization_id=authorization_id,
            graph_id=graph_id,
            overall_status=overall_status,
            scope=scope,
            dimension_coverages=dimension_coverages,
            claims=claims,
            gaps=gaps,
            timestamp=datetime.utcnow().isoformat(),
            provenance=[f"completeness_engine:{method.value}"],
        )

    def _compute_dimension_coverages(
        self,
        declared: list[str],
        actual: list[str],
        scope: CompletenessScope,
        method: CompletenessMethod,
    ) -> list[DimensionCoverage]:
        """Compute coverage for each dimension."""
        coverages = []

        # Evidence coverage
        evidence_known = [d for d in declared if d.startswith("ev_")]
        evidence_actual = [d for d in actual if d.startswith("ev_")]
        evidence_coverage = _safe_div(len(evidence_known), len(evidence_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.EVIDENCE,
            coverage_score=evidence_coverage,
            known_elements=evidence_known,
            unknown_elements=[d for d in evidence_actual if d not in evidence_known],
            method=method,
        ))

        # Mechanism coverage
        mech_known = [d for d in declared if d.startswith("mech_")]
        mech_actual = [d for d in actual if d.startswith("mech_")]
        mech_coverage = _safe_div(len(mech_known), len(mech_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.MECHANISM,
            coverage_score=mech_coverage,
            known_elements=mech_known,
            unknown_elements=[d for d in mech_actual if d not in mech_known],
            method=method,
        ))

        # Resource coverage
        res_known = [d for d in declared if d.startswith("res_")]
        res_actual = [d for d in actual if d.startswith("res_")]
        res_coverage = _safe_div(len(res_known), len(res_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.RESOURCE,
            coverage_score=res_coverage,
            known_elements=res_known,
            unknown_elements=[d for d in res_actual if d not in res_known],
            method=method,
        ))

        # Consequence coverage
        cons_known = [d for d in declared if d.startswith("cons_")]
        cons_actual = [d for d in actual if d.startswith("cons_")]
        cons_coverage = _safe_div(len(cons_known), len(cons_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.CONSEQUENCE,
            coverage_score=cons_coverage,
            known_elements=cons_known,
            unknown_elements=[d for d in cons_actual if d not in cons_known],
            method=method,
        ))

        # Actor coverage
        actor_known = [d for d in declared if d.startswith("actor_")]
        actor_actual = [d for d in actual if d.startswith("actor_")]
        actor_coverage = _safe_div(len(actor_known), len(actor_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.ACTOR,
            coverage_score=actor_coverage,
            known_elements=actor_known,
            unknown_elements=[d for d in actor_actual if d not in actor_known],
            method=method,
        ))

        # Environment coverage
        env_known = [d for d in declared if d.startswith("env_")]
        env_actual = [d for d in actual if d.startswith("env_")]
        env_coverage = _safe_div(len(env_known), len(env_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.ENVIRONMENT,
            coverage_score=env_coverage,
            known_elements=env_known,
            unknown_elements=[d for d in env_actual if d not in env_known],
            method=method,
        ))

        # Temporal coverage
        temp_known = [d for d in declared if d.startswith("temp_")]
        temp_actual = [d for d in actual if d.startswith("temp_")]
        temp_coverage = _safe_div(len(temp_known), len(temp_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.TEMPORAL,
            coverage_score=temp_coverage,
            known_elements=temp_known,
            unknown_elements=[d for d in temp_actual if d not in temp_known],
            method=method,
        ))

        # Governance coverage
        gov_known = [d for d in declared if d.startswith("gov_")]
        gov_actual = [d for d in actual if d.startswith("gov_")]
        gov_coverage = _safe_div(len(gov_known), len(gov_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.GOVERNANCE,
            coverage_score=gov_coverage,
            known_elements=gov_known,
            unknown_elements=[d for d in gov_actual if d not in gov_known],
            method=method,
        ))

        # Execution path coverage
        exec_known = [d for d in declared if d.startswith("exec_")]
        exec_actual = [d for d in actual if d.startswith("exec_")]
        exec_coverage = _safe_div(len(exec_known), len(exec_actual))
        coverages.append(DimensionCoverage(
            dimension=CompletenessDimension.EXECUTION_PATH,
            coverage_score=exec_coverage,
            known_elements=exec_known,
            unknown_elements=[d for d in exec_actual if d not in exec_known],
            method=method,
        ))

        return coverages

    def _determine_overall_status(
        self,
        coverages: list[DimensionCoverage],
        declared: list[str],
        actual: list[str],
        method: CompletenessMethod,
    ) -> CompletenessStatus:
        """Determine overall completeness status."""
        if not coverages:
            return CompletenessStatus.UNKNOWN

        # Count dimensions with actual elements
        dimensions_with_actual = [dc for dc in coverages if dc.unknown_elements or dc.known_elements]
        
        # If no dimensions have actual elements, check if declared matches actual
        if not dimensions_with_actual:
            if set(declared) >= set(actual):
                return CompletenessStatus.KNOWN_COMPLETE
            return CompletenessStatus.KNOWN_INCOMPLETE

        # Check coverage on dimensions that have actual elements
        all_full = all(dc.coverage_score >= 1.0 for dc in dimensions_with_actual)
        any_partial = any(0 < dc.coverage_score < 1.0 for dc in dimensions_with_actual)
        any_zero = any(dc.coverage_score == 0.0 for dc in dimensions_with_actual)
        
        # Unknown: dimensions with actual elements but no known elements
        any_unknown = any(
            dc.coverage_score == 0.0 and len(dc.unknown_elements) > 0
            for dc in dimensions_with_actual
        )

        # Check for over-approximation: declared superset of actual on all dimensions
        over_approx = all_full and len(declared) > len(actual)

        if over_approx:
            return CompletenessStatus.OVER_APPROXIMATED

        if all_full and not any_zero:
            if method == CompletenessMethod.MODEL_HYPOTHESIZED:
                return CompletenessStatus.UNTESTED_COMPLETENESS
            return CompletenessStatus.KNOWN_COMPLETE

        if any_unknown:
            return CompletenessStatus.UNKNOWN

        if any_partial:
            # Partial coverage on at least one dimension - known incomplete
            return CompletenessStatus.KNOWN_INCOMPLETE

        if any_zero:
            # Zero coverage on at least one dimension with known elements
            all_non_zero = all(dc.coverage_score > 0 for dc in dimensions_with_actual)
            if all_non_zero:
                return CompletenessStatus.CONDITIONAL_COMPLETENESS
            return CompletenessStatus.KNOWN_INCOMPLETE

        return CompletenessStatus.INCONCLUSIVE

    def _generate_claims(
        self,
        authorization_id: str,
        graph_id: str,
        scope: CompletenessScope,
        method: CompletenessMethod,
        coverages: list[DimensionCoverage],
        status: CompletenessStatus,
        declared: list[str],
        actual: list[str],
    ) -> list[CompletenessClaim]:
        """Generate completeness claims based on assessment."""
        claims = []

        # Primary claim
        min_coverage = min((dc.coverage_score for dc in coverages), default=0.0)
        claims.append(CompletenessClaim(
            claim_id=f"claim_{uuid.uuid4().hex[:12]}",
            authorization_id=authorization_id,
            graph_id=graph_id,
            status=status,
            scope=scope,
            method=method,
            confidence=min_coverage,
            evidence=[dc.dimension.value for dc in coverages if dc.coverage_score >= 1.0],
            limitations=[dc.dimension.value for dc in coverages if dc.coverage_score < 1.0],
            dimension_coverage={dc.dimension.value: dc.coverage_score for dc in coverages},
        ))

        return claims

    def _identify_gaps(
        self,
        declared: list[str],
        actual: list[str],
        scope: CompletenessScope,
    ) -> list[str]:
        """Identify gaps between declared and actual dependencies."""
        gaps = []
        declared_set = set(declared)
        for dep in actual:
            if dep not in declared_set:
                gaps.append(dep)
        return gaps

    def compare_methods(
        self,
        authorization_id: str,
        graph_id: str,
        declared: list[str],
        actual: list[str],
        scope: CompletenessScope,
    ) -> dict[str, CompletenessAssessment]:
        """Compare completeness assessments across methods."""
        results = {}
        for method in CompletenessMethod:
            assessment = self.assess_completeness(
                authorization_id, graph_id, declared, actual, scope, method
            )
            results[method.value] = assessment
        return results

    def check_intersection_status(
        self,
        evidence_id: str,
        declared_dependencies: list[str],
        assessment: CompletenessAssessment,
    ) -> IntersectionStatus:
        """Determine the intersection status of new evidence.
        
        This is the critical operation that distinguishes:
        - NO_INTERSECTION_ESTABLISHED: We checked and found no intersection
        - NO_RELEVANT_DEPENDENCY_EXISTS: The graph is complete and this evidence is irrelevant
        - GRAPH_SUFFICIENTLY_COMPLETE: We have high confidence the graph is complete
        - CANNOT_DETERMINE: We don't know enough to decide
        """
        # Check if evidence directly intersects
        if evidence_id in declared_dependencies:
            return IntersectionStatus.INTERSECTION_FOUND

        # Check if the graph is sufficiently complete
        if assessment.overall_status == CompletenessStatus.KNOWN_COMPLETE:
            return IntersectionStatus.NO_RELEVANT_DEPENDENCY_EXISTS

        if assessment.overall_status in (
            CompletenessStatus.UNKNOWN,
            CompletenessStatus.INCONCLUSIVE,
        ):
            return IntersectionStatus.CANNOT_DETERMINE

        if assessment.overall_status == CompletenessStatus.KNOWN_INCOMPLETE:
            return IntersectionStatus.NO_INTERSECTION_ESTABLISHED

        if assessment.overall_status == CompletenessStatus.FALSE_COMPLETENESS:
            return IntersectionStatus.CANNOT_DETERMINE

        return IntersectionStatus.NO_INTERSECTION_ESTABLISHED


def _safe_div(a: int, b: int) -> float:
    """Safe division returning 0.0 when denominator is 0."""
    if b == 0:
        return 1.0 if a == 0 else 0.0
    return a / b


def create_completeness_scope(
    proposition_id: str,
    consequence_type: str,
    **kwargs: Any,
) -> CompletenessScope:
    """Create a completeness scope."""
    return CompletenessScope(
        proposition_id=proposition_id,
        consequence_type=consequence_type,
        **kwargs,
    )
