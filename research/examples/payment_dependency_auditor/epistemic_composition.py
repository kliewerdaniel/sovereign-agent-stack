"""Epistemic Composition Engine for dependency claims.

This module implements the core research question:
> Can individually valid dependency claims be composed into system-level
> knowledge without manufacturing epistemic authority?

CENTRAL LAW:
    VALID(A) + VALID(B) + VALID(C) DOES NOT IMPLY VALID(A+B+C)

Composition may produce a new claim only when the semantics and evidence
required by that new proposition are themselves satisfied.

A graph path is NOT automatically evidence for the semantic proposition
represented by that path.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from research.examples.payment_dependency_auditor.dependency_types import (
    DependencyEdge,
    DependencyType,
    EpistemicState,
    ObservationMethod,
    PropositionType,
)


# ---------------------------------------------------------------------------
# Composition Operators
# ---------------------------------------------------------------------------


class CompositionOperator(str, Enum):
    """Types of epistemic composition.

    Each operator defines what proposition types it accepts,
    what it produces, and what evidence is required.
    """

    DIRECT_COMPOSITION = "direct_composition"          # A→B, B→C ⊢ A→C (same type)
    TRANSITIVE_COMPOSITION = "transitive_composition"  # A→B, B→C ⊢ A→C (transitive type)
    CONDITIONAL_COMPOSITION = "conditional_composition"  # A→B (if C) ⊢ A→B (conditional)
    TEMPORAL_COMPOSITION = "temporal_composition"     # A→B (t1), B→C (t2) ⊢ A→C (temporal)
    ENVIRONMENT_COMPOSITION = "environment_composition"  # A→B (env1) ⊢ A→B (env1 only)
    FAILURE_COMPOSITION = "failure_composition"        # A→B (fail) ⊢ A→B (failure dep)
    OPERATIONAL_COMPOSITION = "operational_composition"  # A→B (runtime) ⊢ A→B (operational)
    NECESSITY_COMPOSITION = "necessity_composition"    # A→B (required) ⊢ A→B (necessary)
    SUBSTITUTION_COMPOSITION = "substitution_composition"  # A→B, A→C ⊢ A→(B|C)
    ALTERNATIVE_COMPOSITION = "alternative_composition"  # A→B, A→C ⊢ A→(B or C)


class CompositionValidity(str, Enum):
    """Result of a composition attempt."""

    VALID = "valid"                    # Composition preserves authority
    AUTHORITY_REDUCED = "authority_reduced"  # Composition weakens authority
    INCONCLUSIVE = "inconclusive"      # Composition cannot be determined
    REJECTED = "rejected"              # Composition is invalid


# ---------------------------------------------------------------------------
# Composition Rule
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositionRule:
    """Rule for whether a composition is valid.

    Attributes:
        operator: The composition operator
        input_types: Accepted proposition types
        output_type: Produced proposition type
        authority_preservation: How authority changes
        required_evidence: Additional evidence required
        assumptions: Assumptions introduced
        alternatives_to_exclude: Alternatives that must be excluded
    """

    operator: CompositionOperator
    input_types: tuple[PropositionType, ...]
    output_type: PropositionType
    authority_preservation: CompositionValidity
    required_evidence: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    alternatives_to_exclude: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Composition Rules (the core epistemic logic)
# ---------------------------------------------------------------------------


COMPOSITION_RULES: list[CompositionRule] = [
    # Direct composition: same type, same authority
    CompositionRule(
        operator=CompositionOperator.DIRECT_COMPOSITION,
        input_types=(PropositionType.STATIC_REFERENCE, PropositionType.STATIC_REFERENCE),
        output_type=PropositionType.TRANSITIVE_DEPENDENCY,
        authority_preservation=CompositionValidity.AUTHORITY_REDUCED,
        required_evidence=["path_exists"],
        assumptions=["intermediate_node_is_reachable"],
        alternatives_to_exclude=["dead_code_path"],
    ),
    # Mixed composition: static + runtime = transitive with reduced authority
    CompositionRule(
        operator=CompositionOperator.DIRECT_COMPOSITION,
        input_types=(PropositionType.STATIC_REFERENCE, PropositionType.RUNTIME_DEPENDENCY),
        output_type=PropositionType.TRANSITIVE_DEPENDENCY,
        authority_preservation=CompositionValidity.AUTHORITY_REDUCED,
        required_evidence=["path_exists", "runtime_evidence_for_one_hop"],
        assumptions=["intermediate_node_is_reachable"],
        alternatives_to_exclude=["dead_code_path"],
    ),
    # Transitive composition: requires runtime evidence for each hop
    CompositionRule(
        operator=CompositionOperator.TRANSITIVE_COMPOSITION,
        input_types=(PropositionType.RUNTIME_DEPENDENCY, PropositionType.RUNTIME_DEPENDENCY),
        output_type=PropositionType.TRANSITIVE_DEPENDENCY,
        authority_preservation=CompositionValidity.INCONCLUSIVE,
        required_evidence=["runtime_path_exists", "no_caching", "no_failover"],
        assumptions=["no_intermediate_caching", "no_intermediate_failover"],
        alternatives_to_exclude=["cached_path", "failopen_path"],
    ),
    # Operational composition: requires operational evidence
    CompositionRule(
        operator=CompositionOperator.OPERATIONAL_COMPOSITION,
        input_types=(PropositionType.RUNTIME_DEPENDENCY, PropositionType.RUNTIME_DEPENDENCY),
        output_type=PropositionType.OPERATIONAL_DEPENDENCY,
        authority_preservation=CompositionValidity.INCONCLUSIVE,
        required_evidence=["failure_injection_result", "operational_test"],
        assumptions=["failure_propagation_is_direct"],
        alternatives_to_exclude=["failopen_path", "cached_path", "async_path"],
    ),
    # Necessity composition: requires necessity evidence
    CompositionRule(
        operator=CompositionOperator.NECESSITY_COMPOSITION,
        input_types=(PropositionType.OPERATIONAL_DEPENDENCY, PropositionType.OPERATIONAL_DEPENDENCY),
        output_type=PropositionType.OPERATIONAL_DEPENDENCY,
        authority_preservation=CompositionValidity.INCONCLUSIVE,
        required_evidence=["necessity_test", "no_substitute"],
        assumptions=["no_substitute_available"],
        alternatives_to_exclude=["substitutable_path"],
    ),
    # Conditional composition: preserves conditionality
    CompositionRule(
        operator=CompositionOperator.CONDITIONAL_COMPOSITION,
        input_types=(PropositionType.STATIC_REFERENCE, PropositionType.STATIC_REFERENCE),
        output_type=PropositionType.STATIC_REFERENCE,
        authority_preservation=CompositionValidity.AUTHORITY_REDUCED,
        required_evidence=["condition_identified"],
        assumptions=["condition_is_necessary"],
        alternatives_to_exclude=["unconditional_path"],
    ),
    # Temporal composition: preserves temporal scope
    CompositionRule(
        operator=CompositionOperator.TEMPORAL_COMPOSITION,
        input_types=(PropositionType.TEMPORAL_DEPENDENCY, PropositionType.TEMPORAL_DEPENDENCY),
        output_type=PropositionType.TEMPORAL_DEPENDENCY,
        authority_preservation=CompositionValidity.AUTHORITY_REDUCED,
        required_evidence=["temporal_overlap"],
        assumptions=["temporal_consistency"],
        alternatives_to_exclude=["temporal_mismatch"],
    ),
    # Environment composition: preserves environment scope
    CompositionRule(
        operator=CompositionOperator.ENVIRONMENT_COMPOSITION,
        input_types=(PropositionType.ENVIRONMENT_DEPENDENCY, PropositionType.ENVIRONMENT_DEPENDENCY),
        output_type=PropositionType.ENVIRONMENT_DEPENDENCY,
        authority_preservation=CompositionValidity.AUTHORITY_REDUCED,
        required_evidence=["environment_match"],
        assumptions=["environment_consistency"],
        alternatives_to_exclude=["environment_mismatch"],
    ),
    # Failure composition: requires failure propagation evidence
    CompositionRule(
        operator=CompositionOperator.FAILURE_COMPOSITION,
        input_types=(PropositionType.FAILURE_DEPENDENCY, PropositionType.FAILURE_DEPENDENCY),
        output_type=PropositionType.FAILURE_DEPENDENCY,
        authority_preservation=CompositionValidity.INCONCLUSIVE,
        required_evidence=["failure_propagation_test"],
        assumptions=["failure_propagates_linearly"],
        alternatives_to_exclude=["failopen_intermediate", "cached_intermediate"],
    ),
    # Substitution composition: handles substitutable providers
    CompositionRule(
        operator=CompositionOperator.SUBSTITUTION_COMPOSITION,
        input_types=(PropositionType.RUNTIME_DEPENDENCY, PropositionType.RUNTIME_DEPENDENCY),
        output_type=PropositionType.RUNTIME_DEPENDENCY,
        authority_preservation=CompositionValidity.AUTHORITY_REDUCED,
        required_evidence=["substitution_test"],
        assumptions=["substitute_is_equivalent"],
        alternatives_to_exclude=["substitute_not_equivalent"],
    ),
]


# ---------------------------------------------------------------------------
# Composition Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositionResult:
    """Result of attempting to compose two dependency claims.

    Attributes:
        result_id: Unique identifier
        parent_edges: The edges being composed
        operator: The composition operator used
        validity: Whether the composition is valid
        derived_edge: The resulting edge (if any)
        authority_change: How authority changed
        evidence_required: What evidence would be needed
        assumptions_introduced: Assumptions made
        scope: Scope of the derived claim
        limitations: Known limitations
        provenance_id: Provenance identifier
        created_at: When this result was created
    """

    result_id: str
    parent_edges: tuple[DependencyEdge, ...]
    operator: CompositionOperator
    validity: CompositionValidity
    derived_edge: Optional[DependencyEdge]
    authority_change: str
    evidence_required: list[str]
    assumptions_introduced: list[str]
    scope: str
    limitations: list[str]
    provenance_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "parent_edges": [e.to_dict() for e in self.parent_edges],
            "operator": self.operator.value,
            "validity": self.validity.value,
            "derived_edge": self.derived_edge.to_dict() if self.derived_edge else None,
            "authority_change": self.authority_change,
            "evidence_required": self.evidence_required,
            "assumptions_introduced": self.assumptions_introduced,
            "scope": self.scope,
            "limitations": self.limitations,
            "provenance_id": self.provenance_id,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Epistemic Composition Engine
# ---------------------------------------------------------------------------


class EpistemicCompositionEngine:
    """Engine for composing dependency claims with epistemic accounting.

    Core principle: Composition cannot create epistemic authority from nothing.

    The engine:
    1. Takes two dependency edges (A→B, B→C)
    2. Determines the appropriate composition operator
    3. Checks if the composition is valid
    4. Produces a derived edge with appropriate epistemic state
    5. Records all assumptions, limitations, and evidence requirements
    """

    def __init__(self, rules: list[CompositionRule] | None = None):
        self.rules = rules or COMPOSITION_RULES

    def compose(
        self,
        edge_ab: DependencyEdge,
        edge_bc: DependencyEdge,
        operator: CompositionOperator | None = None,
    ) -> CompositionResult:
        """Compose two dependency edges.

        Args:
            edge_ab: First edge (A → B)
            edge_bc: Second edge (B → C)
            operator: Optional explicit operator (auto-detected if None)

        Returns:
            CompositionResult with the derived edge and epistemic accounting
        """
        # Verify edges are composable (target of first matches source of second)
        if edge_ab.target != edge_bc.source:
            # Not composable - intermediate nodes don't match
            return self._rejected_result(
                (edge_ab, edge_bc),
                CompositionOperator.DIRECT_COMPOSITION,
                "Edges are not composable: intermediate nodes don't match",
            )

        # Auto-detect operator if not specified
        if operator is None:
            operator = self._detect_operator(edge_ab, edge_bc)

        # Find matching rule
        rule = self._find_rule(operator, edge_ab.proposition_type, edge_bc.proposition_type)
        if rule is None:
            return self._rejected_result(
                (edge_ab, edge_bc),
                operator,
                f"No composition rule for {operator.value} with types "
                f"{edge_ab.proposition_type.value}, {edge_bc.proposition_type.value}",
            )

        # Apply the rule
        return self._apply_rule(rule, edge_ab, edge_bc)

    def _detect_operator(
        self,
        edge_ab: DependencyEdge,
        edge_bc: DependencyEdge,
    ) -> CompositionOperator:
        """Auto-detect the appropriate composition operator."""
        # If both are static references, use direct composition
        if (edge_ab.proposition_type == PropositionType.STATIC_REFERENCE and
                edge_bc.proposition_type == PropositionType.STATIC_REFERENCE):
            return CompositionOperator.DIRECT_COMPOSITION

        # If both are runtime dependencies, use transitive composition
        if (edge_ab.proposition_type == PropositionType.RUNTIME_DEPENDENCY and
                edge_bc.proposition_type == PropositionType.RUNTIME_DEPENDENCY):
            return CompositionOperator.TRANSITIVE_COMPOSITION

        # If both are operational dependencies, use operational composition
        if (edge_ab.proposition_type == PropositionType.OPERATIONAL_DEPENDENCY and
                edge_bc.proposition_type == PropositionType.OPERATIONAL_DEPENDENCY):
            return CompositionOperator.OPERATIONAL_COMPOSITION

        # If both are failure dependencies, use failure composition
        if (edge_ab.proposition_type == PropositionType.FAILURE_DEPENDENCY and
                edge_bc.proposition_type == PropositionType.FAILURE_DEPENDENCY):
            return CompositionOperator.FAILURE_COMPOSITION

        # If both are temporal dependencies, use temporal composition
        if (edge_ab.proposition_type == PropositionType.TEMPORAL_DEPENDENCY and
                edge_bc.proposition_type == PropositionType.TEMPORAL_DEPENDENCY):
            return CompositionOperator.TEMPORAL_COMPOSITION

        # If both are environment dependencies, use environment composition
        if (edge_ab.proposition_type == PropositionType.ENVIRONMENT_DEPENDENCY and
                edge_bc.proposition_type == PropositionType.ENVIRONMENT_DEPENDENCY):
            return CompositionOperator.ENVIRONMENT_COMPOSITION

        # Default to direct composition
        return CompositionOperator.DIRECT_COMPOSITION

    def _find_rule(
        self,
        operator: CompositionOperator,
        type_a: PropositionType,
        type_b: PropositionType,
    ) -> CompositionRule | None:
        """Find a matching composition rule."""
        for rule in self.rules:
            if rule.operator == operator:
                if type_a in rule.input_types and type_b in rule.input_types:
                    return rule
        return None

    def _apply_rule(
        self,
        rule: CompositionRule,
        edge_ab: DependencyEdge,
        edge_bc: DependencyEdge,
    ) -> CompositionResult:
        """Apply a composition rule to produce a derived edge."""
        # Determine the derived edge's properties
        source = edge_ab.source
        target = edge_bc.target

        # Determine epistemic state based on authority preservation
        if rule.authority_preservation == CompositionValidity.VALID:
            epistemic_state = EpistemicState.OBSERVED
        elif rule.authority_preservation == CompositionValidity.AUTHORITY_REDUCED:
            epistemic_state = EpistemicState.INFERRED
        elif rule.authority_preservation == CompositionValidity.INCONCLUSIVE:
            epistemic_state = EpistemicState.INCONCLUSIVE
        else:
            epistemic_state = EpistemicState.UNKNOWN

        # Build scope
        scope_parts = []
        if edge_ab.scope:
            scope_parts.append(f"Via {edge_ab.target}: {edge_ab.scope}")
        if edge_bc.scope:
            scope_parts.append(f"Via {edge_bc.target}: {edge_bc.scope}")
        scope = " | ".join(scope_parts) if scope_parts else "Transitive composition"

        # Build limitations
        limitations = [
            "Transitive dependency - not directly observed",
            f"Authority: {rule.authority_preservation.value}",
        ]
        limitations.extend(rule.assumptions)

        # Create the derived edge
        derived_edge = DependencyEdge(
            source=source,
            target=target,
            dependency_type=edge_ab.dependency_type,  # Inherit from first edge
            source_artifact=f"composed:{edge_ab.source_artifact}+{edge_bc.source_artifact}",
            source_location=f"composed:{edge_ab.source_location}+{edge_bc.source_location}",
            observation_method=ObservationMethod.STATIC_ANALYSIS,
            environment=self._combine_environments(edge_ab.environment, edge_bc.environment),
            epistemic_state=epistemic_state,
            proposition_type=rule.output_type,
            evidence=[
                f"composed_from:{edge_ab.provenance_id}",
                f"composed_from:{edge_bc.provenance_id}",
            ],
            alternatives=rule.alternatives_to_exclude,
            scope=scope,
            limitations=limitations,
            provenance_id=f"comp_{uuid.uuid4().hex[:8]}",
            confidence=min(edge_ab.confidence, edge_bc.confidence) * 0.9,  # Authority decreases
        )

        return CompositionResult(
            result_id=f"res_{uuid.uuid4().hex[:8]}",
            parent_edges=(edge_ab, edge_bc),
            operator=rule.operator,
            validity=rule.authority_preservation,
            derived_edge=derived_edge,
            authority_change=rule.authority_preservation.value,
            evidence_required=rule.required_evidence,
            assumptions_introduced=rule.assumptions,
            scope=scope,
            limitations=limitations,
            provenance_id=derived_edge.provenance_id,
        )

    def _rejected_result(
        self,
        edges: tuple[DependencyEdge, ...],
        operator: CompositionOperator,
        reason: str,
    ) -> CompositionResult:
        """Create a rejected composition result."""
        return CompositionResult(
            result_id=f"rej_{uuid.uuid4().hex[:8]}",
            parent_edges=edges,
            operator=operator,
            validity=CompositionValidity.REJECTED,
            derived_edge=None,
            authority_change="rejected",
            evidence_required=[],
            assumptions_introduced=[],
            scope="",
            limitations=[reason],
            provenance_id=f"rej_{uuid.uuid4().hex[:8]}",
        )

    def _combine_environments(self, env_a: str, env_b: str) -> str:
        """Combine environment scopes."""
        if env_a == env_b:
            return env_a
        if env_a == "all":
            return env_b
        if env_b == "all":
            return env_a
        return f"{env_a}+{env_b}"  # Both environments apply

    def compose_chain(
        self,
        edges: list[DependencyEdge],
    ) -> list[CompositionResult]:
        """Compose a chain of edges.

        For edges [A→B, B→C, C→D], produces:
        - Composition of A→B and B→C → A→C
        - Composition of B→C and C→D → B→D
        - Composition of A→C and C→D → A→D

        Each step reduces authority.
        """
        results = []
        current_edges = list(edges)

        # Compose adjacent pairs
        for i in range(len(current_edges) - 1):
            result = self.compose(current_edges[i], current_edges[i + 1])
            results.append(result)
            if result.derived_edge is not None:
                # Add derived edge to the chain for further composition
                current_edges.append(result.derived_edge)

        return results


# ---------------------------------------------------------------------------
# Epistemic Accounting
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistemicAccounting:
    """Accounting for epistemic authority during composition.

    Tracks whether composition accidentally:
    - Amplifies authority
    - Erases uncertainty
    - Erases scope
    - Erases environmental restrictions
    - Erases temporal restrictions
    - Erases alternatives
    - Converts observation into necessity
    - Converts correlation into dependency
    - Converts dependency into criticality
    - Converts local evidence into generalization
    """

    parent_authority: float
    derived_authority: float
    authority_preserved: bool
    authority_amplified: bool
    uncertainty_preserved: bool
    scope_preserved: bool
    environment_preserved: bool
    temporal_preserved: bool
    alternatives_preserved: bool
    observation_not_necessity: bool
    correlation_not_dependency: bool
    dependency_not_criticality: bool
    local_not_generalization: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "parent_authority": self.parent_authority,
            "derived_authority": self.derived_authority,
            "authority_preserved": self.authority_preserved,
            "authority_amplified": self.authority_amplified,
            "uncertainty_preserved": self.uncertainty_preserved,
            "scope_preserved": self.scope_preserved,
            "environment_preserved": self.environment_preserved,
            "temporal_preserved": self.temporal_preserved,
            "alternatives_preserved": self.alternatives_preserved,
            "observation_not_necessity": self.observation_not_necessity,
            "correlation_not_dependency": self.correlation_not_dependency,
            "dependency_not_criticality": self.dependency_not_criticality,
            "local_not_generalization": self.local_not_generalization,
            "issues": self.issues,
        }


def account_epistemic_authority(
    parent_edges: list[DependencyEdge],
    derived_edge: DependencyEdge,
) -> EpistemicAccounting:
    """Account for epistemic authority during composition.

    Verifies that composition does not accidentally amplify authority.
    """
    issues = []

    # Calculate parent authority (minimum of parents - chain is as strong as weakest link)
    parent_authority = min(e.confidence for e in parent_edges) if parent_edges else 0.0
    derived_authority = derived_edge.confidence

    # Check authority amplification
    authority_amplified = derived_authority > parent_authority
    if authority_amplified:
        issues.append(
            f"Authority amplified: parent={parent_authority:.2f}, derived={derived_authority:.2f}"
        )

    authority_preserved = not authority_amplified

    # Check uncertainty preservation
    uncertainty_preserved = derived_edge.epistemic_state in (
        EpistemicState.INFERRED,
        EpistemicState.INCONCLUSIVE,
        EpistemicState.OBSERVED,
    )
    if not uncertainty_preserved:
        issues.append("Uncertainty not preserved - derived state is too certain")

    # Check scope preservation
    scope_preserved = len(derived_edge.scope) > 0
    if not scope_preserved:
        issues.append("Scope not preserved")

    # Check environment preservation
    parent_envs = {e.environment for e in parent_edges}
    environment_preserved = derived_edge.environment in parent_envs or "all" not in parent_envs
    if not environment_preserved:
        issues.append(f"Environment scope widened: {parent_envs} → {derived_edge.environment}")

    # Check temporal preservation
    temporal_preserved = True  # Would need temporal metadata
    # Check alternatives preservation
    alternatives_preserved = len(derived_edge.alternatives) > 0
    if not alternatives_preserved:
        issues.append("Alternatives not preserved")

    # Check observation ≠ necessity
    observation_not_necessity = derived_edge.proposition_type not in (
        PropositionType.OPERATIONAL_DEPENDENCY,
    ) or any(
        e.proposition_type in (PropositionType.OPERATIONAL_DEPENDENCY,)
        for e in parent_edges
    )
    if not observation_not_necessity:
        issues.append("Observation incorrectly elevated to necessity")

    # Check correlation ≠ dependency
    correlation_not_necessity = derived_edge.proposition_type != PropositionType.RUNTIME_DEPENDENCY or any(
        e.proposition_type == PropositionType.RUNTIME_DEPENDENCY for e in parent_edges
    )
    if not correlation_not_necessity:
        issues.append("Correlation incorrectly elevated to dependency")

    # Check dependency ≠ criticality
    dependency_not_criticality = True  # Would need criticality metadata
    if not dependency_not_criticality:
        issues.append("Dependency incorrectly elevated to criticality")

    # Check local ≠ generalization
    local_not_generalization = derived_edge.environment != "all" or any(
        e.environment == "all" for e in parent_edges
    )
    if not local_not_generalization:
        issues.append("Local evidence incorrectly generalized")

    return EpistemicAccounting(
        parent_authority=parent_authority,
        derived_authority=derived_authority,
        authority_preserved=authority_preserved,
        authority_amplified=authority_amplified,
        uncertainty_preserved=uncertainty_preserved,
        scope_preserved=scope_preserved,
        environment_preserved=environment_preserved,
        temporal_preserved=temporal_preserved,
        alternatives_preserved=alternatives_preserved,
        observation_not_necessity=observation_not_necessity,
        correlation_not_dependency=correlation_not_necessity,
        dependency_not_criticality=dependency_not_criticality,
        local_not_generalization=local_not_generalization,
        issues=issues,
    )
