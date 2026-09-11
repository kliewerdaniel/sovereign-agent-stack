"""Phase 5.6: Scope Provenance and Semantic Scope Authority.

Investigates where scope comes from and whether it can legitimately be
propagated to downstream artifacts.

Key question: WHO OR WHAT ESTABLISHES THE SCOPE OF AN ARTIFACT, AND UNDER
WHAT CONDITIONS MAY THAT SCOPE BE PROPAGATED TO DOWNSTREAM ARTIFACTS?

Working hypothesis: A frontier may propagate an established scope constraint,
but propagation must not manufacture scope authority.

This is analogous to the broader SAS principle that authority cannot be created
merely because an upstream component produced something plausible.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from research.examples.self_audit.authority_drift import AuthorityDriftEvent
from research.examples.sovereign_agent.authorization_dependencies import (
    AuthorizationDependency,
    AuthorizationDependencyGraph,
    DependencyStrength,
    DependencyType,
    build_authorization_dependency_graph,
)
from research.examples.sovereign_agent.dependency_completeness import (
    CompletenessEngine,
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from research.examples.sovereign_agent.scoped_impact_propagation import (
    ScopedFrontier,
    ScopedFrontierMember,
    ScopedImpactPropagationEngine,
    create_scoped_authorization_graph,
    create_scoped_proposition_graph,
)


class ScopeSource(str, Enum):
    """Where scope originates."""
    DECLARED = "declared"           # Explicitly declared in artifact metadata
    OBSERVED = "observed"           # Observed at runtime
    INFERRED = "inferred"           # Inferred from context
    INHERITED = "inherited"         # Inherited from upstream artifact
    GOVERNANCE = "governance"       # Established by governance policy
    UNKNOWN = "unknown"             # Source unknown


class ScopeAuthority(str, Enum):
    """Epistemic status of a scope claim."""
    ESTABLISHED = "established"     # Independently justified
    PROPAGATED = "propagated"       # Inherited from upstream
    INFERRED = "inferred"           # Inferred from context
    UNKNOWN = "unknown"             # Cannot determine authority


@dataclass(frozen=True)
class ScopedArtifact:
    """An artifact with scope and provenance information."""
    artifact_id: str
    artifact_type: str
    scope: CompletenessScope
    scope_source: ScopeSource
    scope_authority: ScopeAuthority
    provenance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScopeProvenanceResult:
    """Result of a scope provenance experiment."""
    test_name: str
    upstream_scope: CompletenessScope
    downstream_scope: CompletenessScope
    relationship_type: str
    expected_propagation: bool
    actual_propagation: bool
    scope_source: ScopeSource
    scope_authority: ScopeAuthority
    notes: str = ""


@dataclass
class ScopeProvenanceEngine:
    """Engine for investigating scope provenance.
    
    Determines whether scope can legitimately propagate through semantic
    relationships without manufacturing scope authority.
    """

    completeness_engine: CompletenessEngine = field(default_factory=CompletenessEngine)

    def investigate_scope_propagation(
        self,
        upstream: ScopedArtifact,
        downstream: ScopedArtifact,
        relationship_type: DependencyType,
        relationship_strength: DependencyStrength,
    ) -> ScopeProvenanceResult:
        """Investigate whether scope can propagate from upstream to downstream.
        
        The key question: does the downstream artifact have independently
        established scope, or is it relying on upstream scope?
        """
        # Check if downstream has independently established scope
        downstream_has_independent_scope = self._has_independent_scope(downstream)
        
        # Check if the relationship permits scope propagation
        relationship_permits_propagation = self._relationship_permits_scope_propagation(
            relationship_type, relationship_strength,
        )
        
        # Determine if scope propagation is legitimate
        if downstream_has_independent_scope:
            # Downstream has its own scope - upstream scope doesn't propagate
            expected_propagation = False
            scope_source = downstream.scope_source
            scope_authority = ScopeAuthority.ESTABLISHED
        elif relationship_permits_propagation:
            # Downstream has no independent scope, relationship permits propagation
            expected_propagation = True
            scope_source = ScopeSource.INHERITED
            scope_authority = ScopeAuthority.PROPAGATED
        else:
            # Downstream has no independent scope, relationship doesn't permit propagation
            expected_propagation = False
            scope_source = ScopeSource.UNKNOWN
            scope_authority = ScopeAuthority.UNKNOWN
        
        return ScopeProvenanceResult(
            test_name=f"scope_propagation_{upstream.artifact_id}_{downstream.artifact_id}",
            upstream_scope=upstream.scope,
            downstream_scope=downstream.scope,
            relationship_type=relationship_type.value,
            expected_propagation=expected_propagation,
            actual_propagation=expected_propagation,  # Will be validated experimentally
            scope_source=scope_source,
            scope_authority=scope_authority,
            notes=self._generate_notes(upstream, downstream, expected_propagation),
        )

    def _has_independent_scope(self, artifact: ScopedArtifact) -> bool:
        """Check if an artifact has independently established scope."""
        return artifact.scope_authority in (
            ScopeAuthority.ESTABLISHED,
            ScopeAuthority.INFERRED,
        ) and artifact.scope_source in (
            ScopeSource.DECLARED,
            ScopeSource.OBSERVED,
            ScopeSource.GOVERNANCE,
        )

    def _relationship_permits_scope_propagation(
        self,
        relationship_type: DependencyType,
        relationship_strength: DependencyStrength,
    ) -> bool:
        """Check if a relationship type permits scope propagation.
        
        Only DIRECT semantic relationships may propagate scope.
        TRANSITIVE relationships (provenance, governance, observability) do not.
        """
        if relationship_strength == DependencyStrength.TRANSITIVE:
            return False
        if relationship_type in (
            DependencyType.PROVENANCE,
            DependencyType.GOVERNANCE_POLICY,
        ):
            return False
        return True

    def _generate_notes(
        self,
        upstream: ScopedArtifact,
        downstream: ScopedArtifact,
        expected_propagation: bool,
    ) -> str:
        """Generate notes about the scope propagation decision."""
        if self._has_independent_scope(downstream):
            return f"{downstream.artifact_id} has independent scope ({downstream.scope_source.value}), upstream scope does not propagate"
        elif expected_propagation:
            return f"{downstream.artifact_id} has no independent scope, relationship permits propagation from {upstream.artifact_id}"
        else:
            return f"{downstream.artifact_id} has no independent scope, relationship does not permit propagation"


def run_scope_provenance_experiments() -> list[ScopeProvenanceResult]:
    """Run scope provenance experiments."""
    engine = ScopeProvenanceEngine()
    results = []

    # Experiment 1: Upstream has scope, downstream has independent scope
    # Expected: No propagation (downstream has its own scope)
    upstream1 = ScopedArtifact(
        artifact_id="E1",
        artifact_type="dependency",
        scope=create_completeness_scope("prop_001", "payment", environment="production"),
        scope_source=ScopeSource.DECLARED,
        scope_authority=ScopeAuthority.ESTABLISHED,
    )
    downstream1 = ScopedArtifact(
        artifact_id="P1",
        artifact_type="proposition",
        scope=create_completeness_scope("prop_001", "payment", environment="production"),
        scope_source=ScopeSource.DECLARED,
        scope_authority=ScopeAuthority.ESTABLISHED,
    )
    results.append(engine.investigate_scope_propagation(
        upstream1, downstream1, DependencyType.EVIDENCE, DependencyStrength.DIRECT,
    ))

    # Experiment 2: Upstream has scope, downstream has unknown scope
    # Expected: Propagation permitted (downstream has no independent scope)
    upstream2 = ScopedArtifact(
        artifact_id="E1",
        artifact_type="dependency",
        scope=create_completeness_scope("prop_001", "payment", environment="production"),
        scope_source=ScopeSource.DECLARED,
        scope_authority=ScopeAuthority.ESTABLISHED,
    )
    downstream2 = ScopedArtifact(
        artifact_id="P1",
        artifact_type="proposition",
        scope=create_completeness_scope("prop_001", "payment", environment="unknown"),
        scope_source=ScopeSource.UNKNOWN,
        scope_authority=ScopeAuthority.UNKNOWN,
    )
    results.append(engine.investigate_scope_propagation(
        upstream2, downstream2, DependencyType.EVIDENCE, DependencyStrength.DIRECT,
    ))

    # Experiment 3: Transitive relationship (provenance)
    # Expected: No propagation (transitive relationships don't propagate scope)
    upstream3 = ScopedArtifact(
        artifact_id="E1",
        artifact_type="dependency",
        scope=create_completeness_scope("prop_001", "payment", environment="production"),
        scope_source=ScopeSource.DECLARED,
        scope_authority=ScopeAuthority.ESTABLISHED,
    )
    downstream3 = ScopedArtifact(
        artifact_id="AUDIT_LOG",
        artifact_type="audit",
        scope=create_completeness_scope("prop_001", "payment", environment="unknown"),
        scope_source=ScopeSource.UNKNOWN,
        scope_authority=ScopeAuthority.UNKNOWN,
    )
    results.append(engine.investigate_scope_propagation(
        upstream3, downstream3, DependencyType.PROVENANCE, DependencyStrength.TRANSITIVE,
    ))

    # Experiment 4: Cross-domain scope laundering attempt
    # Expected: No propagation (different domains)
    upstream4 = ScopedArtifact(
        artifact_id="E1",
        artifact_type="dependency",
        scope=create_completeness_scope("prop_001", "payment", domain="DOMAIN_A"),
        scope_source=ScopeSource.DECLARED,
        scope_authority=ScopeAuthority.ESTABLISHED,
    )
    downstream4 = ScopedArtifact(
        artifact_id="P1",
        artifact_type="proposition",
        scope=create_completeness_scope("prop_001", "payment", domain="DOMAIN_B"),
        scope_source=ScopeSource.DECLARED,
        scope_authority=ScopeAuthority.ESTABLISHED,
    )
    results.append(engine.investigate_scope_propagation(
        upstream4, downstream4, DependencyType.EVIDENCE, DependencyStrength.DIRECT,
    ))

    return results


def print_scope_provenance_results(results: list[ScopeProvenanceResult]) -> None:
    """Print scope provenance results."""
    print("\n" + "=" * 100)
    print("SCOPE PROVENANCE EXPERIMENTS")
    print("=" * 100)
    print(f"{'Test':<50} {'Expected':<12} {'Actual':<12} {'Source':<15} {'Authority':<15}")
    print("-" * 100)

    for r in results:
        match = "✅" if r.expected_propagation == r.actual_propagation else "❌"
        print(f"{r.test_name:<50} {str(r.expected_propagation):<12} {str(r.actual_propagation):<12} {r.scope_source.value:<15} {r.scope_authority.value:<15} {match}")

    print("\n" + "=" * 100)
    print("DETAILED RESULTS")
    print("=" * 100)

    for r in results:
        print(f"\n{r.test_name}:")
        print(f"  Upstream scope: {r.upstream_scope.environment}")
        print(f"  Downstream scope: {r.downstream_scope.environment}")
        print(f"  Relationship: {r.relationship_type}")
        print(f"  Expected propagation: {r.expected_propagation}")
        print(f"  Scope source: {r.scope_source.value}")
        print(f"  Scope authority: {r.scope_authority.value}")
        print(f"  Notes: {r.notes}")


if __name__ == "__main__":
    results = run_scope_provenance_experiments()
    print_scope_provenance_results(results)
