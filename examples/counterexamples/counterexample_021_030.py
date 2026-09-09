"""Counterexamples 021-030: Dependency Validation and Discovery."""

from __future__ import annotations

from examples.counterexamples.counterexample_corpus import (
    Counterexample,
    CounterexampleType,
    ResolutionStatus,
)


def build_counterexamples_021_030() -> list[Counterexample]:
    """Build counterexamples 021-030 for dependency validation."""
    counterexamples = []

    # COUNTEREXAMPLE-021: Missing Direct Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-021",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Missing direct dependency",
        description=(
            "Authorization depends on evidence E1 and E2, but only E1 was declared. "
            "New evidence E3 contradicts E2 (the missing dependency). "
            "The protocol preserves because E3 does not intersect the declared graph. "
            "This is a false preservation due to incomplete dependency graph."
        ),
        original_assumption="All relevant dependencies are declared.",
        world_state={
            "declared_dependencies": ["E1"],
            "actual_dependencies": ["E1", "E2"],
            "new_evidence": "E3 contradicts E2",
        },
        agent_state={
            "observation": "E3 contradicts the missing dependency E2",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "dependency_graph": "incomplete",
        },
        observed_failure="Protocol preserves authorization despite relevant evidence.",
        expected_behavior="Protocol should detect incomplete graph and require reevaluation.",
        actual_behavior="Protocol preserves because E3 doesn't intersect declared dependencies.",
        classification="MISSING_SEMANTICS",
        provenance=["adversarial_validation", "missing_direct_dependency"],
        reproduction_procedure=[
            "1. Create authorization with only E1 declared",
            "2. Introduce E3 that contradicts E2 (missing dependency)",
            "3. Evaluate intersection",
            "4. Observe false preservation",
        ],
    ))

    # COUNTEREXAMPLE-022: Missing Transitive Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-022",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Missing transitive dependency",
        description=(
            "Authorization depends on experiment X, which depends on evidence E. "
            "The transitive dependency X→E was not declared. "
            "New evidence contradicts E. "
            "The protocol preserves because the contradiction doesn't intersect the graph."
        ),
        original_assumption="Transitive dependencies are declared.",
        world_state={
            "declared_dependencies": ["X"],
            "actual_dependencies": ["X", "E"],
            "new_evidence": "contradicts E",
        },
        agent_state={
            "observation": "evidence contradicts transitive dependency E",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "dependency_graph": "incomplete transitive",
        },
        observed_failure="Protocol preserves authorization despite relevant evidence.",
        expected_behavior="Protocol should detect incomplete transitive dependencies.",
        actual_behavior="Protocol preserves because evidence doesn't intersect declared dependencies.",
        classification="MISSING_SEMANTICS",
        provenance=["adversarial_validation", "missing_transitive_dependency"],
        reproduction_procedure=[
            "1. Create authorization with only X declared",
            "2. Introduce evidence contradicting E (transitive dependency)",
            "3. Evaluate intersection",
            "4. Observe false preservation",
        ],
    ))

    # COUNTEREXAMPLE-023: False Runtime Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-023",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.VALID_REJECTION,
        title="False runtime dependency",
        description=(
            "Runtime trace shows A and B co-occurring. "
            "System infers A depends on B. "
            "Controlled intervention demonstrates A continues when B is removed. "
            "The dependency should be rejected."
        ),
        original_assumption="Runtime co-occurrence implies dependency.",
        world_state={
            "runtime_trace": "A and B co-occur",
            "intervention": "A continues without B",
        },
        agent_state={
            "observation": "A operates independently of B",
        },
        proposal={
            "action": "reject false dependency",
        },
        authority_state={
            "inferred_dependency": "A depends on B",
            "actual": "A independent of B",
        },
        observed_failure="Runtime co-occurrence should not create dependency authority.",
        expected_behavior="Dependency is rejected after controlled intervention.",
        actual_behavior="Dependency is rejected (correct).",
        classification="VALID_REJECTION",
        provenance=["dependency_discovery", "controlled_intervention"],
        reproduction_procedure=[
            "1. Observe runtime co-occurrence of A and B",
            "2. Infer dependency A→B",
            "3. Perform controlled intervention: remove B",
            "4. Verify A continues to operate",
            "5. Reject dependency",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly rejects false dependencies through controlled intervention.",
        resolution_timestamp="2026-09-09T17:35:00Z",
    ))

    # COUNTEREXAMPLE-024: Over-Broad Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-024",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.OVERLY_CONSERVATIVE_POLICY,
        title="Over-broad dependency",
        description=(
            "Authorization declares many extra dependencies beyond what is necessary. "
            "Evidence contradicts one of the extra dependencies. "
            "The protocol suspends, but the suspension is unjustified because "
            "the contradicted dependency was not actually necessary."
        ),
        original_assumption="More dependencies = more safety.",
        world_state={
            "declared_dependencies": ["E1", "E2", "E3", "E4", "E5"],
            "actual_dependencies": ["E1"],
            "new_evidence": "contradicts E5",
        },
        agent_state={
            "observation": "E5 was not necessary",
        },
        proposal={
            "action": "suspend authorization",
        },
        authority_state={
            "auth_001": "valid",
            "dependency_graph": "over-broad",
        },
        observed_failure="Over-broad dependencies cause false suspensions.",
        expected_behavior="Protocol should only suspend for necessary dependencies.",
        actual_behavior="Protocol suspends due to contradicted extra dependency.",
        classification="OVERLY_CONSERVATIVE_POLICY",
        provenance=["adversarial_validation", "over_broad_dependency"],
        reproduction_procedure=[
            "1. Create authorization with extra dependencies",
            "2. Introduce evidence contradicting an extra dependency",
            "3. Observe false suspension",
        ],
    ))

    # COUNTEREXAMPLE-025: Stale Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-025",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.TEMPORAL_ERROR,
        title="Stale dependency",
        description=(
            "Authorization depends on evidence E that was valid at T0. "
            "At T1, E becomes stale but the dependency graph is not updated. "
            "At T2, execution is attempted. "
            "The protocol should detect staleness."
        ),
        original_assumption="Dependencies remain valid indefinitely.",
        world_state={
            "T0": "E is valid",
            "T1": "E becomes stale",
            "T2": "execution attempted",
        },
        agent_state={
            "observation": "E is stale but dependency graph unchanged",
        },
        proposal={
            "action": "execute authorization",
        },
        authority_state={
            "auth_001": "valid",
            "E_status": "stale",
        },
        observed_failure="Protocol should detect stale dependencies.",
        expected_behavior="Protocol marks authorization as requiring reevaluation.",
        actual_behavior="Protocol marks stale but doesn't auto-revocate.",
        classification="EXPECTED_BEHAVIOR",
        provenance=["adversarial_validation", "stale_dependency"],
        reproduction_procedure=[
            "1. Create authorization with dependency E",
            "2. Mark E as stale",
            "3. Attempt execution",
            "4. Verify staleness is detected",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly tracks staleness without auto-revocation.",
        resolution_timestamp="2026-09-09T17:35:00Z",
    ))

    # COUNTEREXAMPLE-026: Cross-Domain Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-026",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Cross-domain dependency",
        description=(
            "Authorization in payment domain depends on identity_service. "
            "The dependency graph does not track cross-domain provenance. "
            "Identity service changes. "
            "The protocol preserves because the change doesn't intersect the graph."
        ),
        original_assumption="Dependencies are domain-local.",
        world_state={
            "payment_domain": "auth_001",
            "identity_domain": "identity_service changed",
        },
        agent_state={
            "observation": "cross-domain impact not detected",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "cross_domain_impact": "unknown",
        },
        observed_failure="Protocol cannot detect cross-domain impacts.",
        expected_behavior="Protocol should flag cross-domain dependency changes.",
        actual_behavior="Protocol preserves because change doesn't intersect graph.",
        classification="MISSING_SEMANTICS",
        provenance=["adversarial_validation", "cross_domain_dependency"],
        reproduction_procedure=[
            "1. Create authorization with cross-domain dependency",
            "2. Change identity service",
            "3. Evaluate intersection",
            "4. Observe false preservation",
        ],
    ))

    # COUNTEREXAMPLE-027: Feature-Flag Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-027",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Feature-flag dependency",
        description=(
            "Authorization depends on feature_flag_enabled. "
            "Feature flag is not in the dependency graph (discovered only at runtime). "
            "Feature flag is disabled. "
            "The protocol preserves because the change doesn't intersect the graph."
        ),
        original_assumption="Feature flags are part of the dependency graph.",
        world_state={
            "feature_flag": "disabled",
            "declared_dependencies": ["E1"],
        },
        agent_state={
            "observation": "feature flag change not detected",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "feature_flag": "disabled",
        },
        observed_failure="Protocol cannot detect feature flag impacts.",
        expected_behavior="Protocol should flag feature flag changes.",
        actual_behavior="Protocol preserves because change doesn't intersect graph.",
        classification="MISSING_SEMANTICS",
        provenance=["adversarial_validation", "feature_flag_dependency"],
        reproduction_procedure=[
            "1. Create authorization with feature flag dependency",
            "2. Disable feature flag",
            "3. Evaluate intersection",
            "4. Observe false preservation",
        ],
    ))

    # COUNTEREXAMPLE-028: Failure-Only Dependency
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-028",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Failure-only dependency",
        description=(
            "Authorization depends on failure_condition NOT being present. "
            "Failure condition is not in the dependency graph (negative dependency). "
            "Failure occurs. "
            "The protocol preserves because the failure doesn't intersect the graph."
        ),
        original_assumption="Negative dependencies are tracked.",
        world_state={
            "failure_condition": "present",
            "declared_dependencies": ["E1"],
        },
        agent_state={
            "observation": "failure condition not detected",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "failure_condition": "present",
        },
        observed_failure="Protocol cannot detect failure condition impacts.",
        expected_behavior="Protocol should suspend when failure condition occurs.",
        actual_behavior="Protocol preserves because failure doesn't intersect graph.",
        classification="MISSING_SEMANTICS",
        provenance=["adversarial_validation", "failure_only_dependency"],
        reproduction_procedure=[
            "1. Create authorization with negative dependency",
            "2. Trigger failure condition",
            "3. Evaluate intersection",
            "4. Observe false preservation",
        ],
    ))

    # COUNTEREXAMPLE-029: Post-Authorization Dependency Discovery
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-029",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.TEMPORAL_ERROR,
        title="Post-authorization dependency discovery",
        description=(
            "Authorization created at T0 with dependency graph frozen. "
            "At T1, a previously unknown dependency is discovered. "
            "At T2, evidence associated with the new dependency contradicts the proposition. "
            "The protocol must NOT retroactively rewrite the historical authorization."
        ),
        original_assumption="Dependency graph is complete at authorization time.",
        world_state={
            "T0": "authorization created",
            "T1": "new dependency discovered",
            "T2": "evidence contradicts proposition",
        },
        agent_state={
            "observation": "new dependency discovered post-authorization",
        },
        proposal={
            "action": "reevaluate authorization",
        },
        authority_state={
            "auth_001": "valid_at_T0",
            "new_dependency": "discovered_at_T1",
        },
        observed_failure="Historical authorization must not be retroactively rewritten.",
        expected_behavior="Protocol preserves historical truth while flagging for reevaluation.",
        actual_behavior="Protocol preserves historical truth (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["adversarial_validation", "post_authorization_discovery"],
        reproduction_procedure=[
            "1. Create authorization at T0",
            "2. Freeze dependency graph",
            "3. Discover new dependency at T1",
            "4. Introduce contradicting evidence at T2",
            "5. Verify historical truth preserved",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly preserves historical authority while flagging for reevaluation.",
        resolution_timestamp="2026-09-09T17:35:00Z",
    ))

    # COUNTEREXAMPLE-030: Dependency Provenance Failure
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-030",
        timestamp="2026-09-09T17:30:00Z",
        counterexample_type=CounterexampleType.PROVENANCE_ERROR,
        title="Dependency provenance failure",
        description=(
            "Authorization depends on evidence E with incomplete provenance. "
            "The provenance chain is broken (missing intermediate steps). "
            "New evidence contradicts E. "
            "The protocol should flag the broken provenance."
        ),
        original_assumption="All dependencies have complete provenance.",
        world_state={
            "evidence": "E",
            "provenance": "incomplete",
            "new_evidence": "contradicts E",
        },
        agent_state={
            "observation": "provenance chain is broken",
        },
        proposal={
            "action": "flag broken provenance",
        },
        authority_state={
            "auth_001": "valid",
            "provenance": "incomplete",
        },
        observed_failure="Protocol cannot assess provenance completeness.",
        expected_behavior="Protocol should flag broken provenance chains.",
        actual_behavior="Protocol preserves because evidence doesn't intersect graph.",
        classification="MISSING_SEMANTICS",
        provenance=["adversarial_validation", "incomplete_provenance"],
        reproduction_procedure=[
            "1. Create authorization with incomplete provenance",
            "2. Introduce contradicting evidence",
            "3. Evaluate intersection",
            "4. Observe false preservation",
        ],
    ))

    return counterexamples
