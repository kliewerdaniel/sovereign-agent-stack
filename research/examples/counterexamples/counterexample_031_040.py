"""Counterexamples 031-040: Dependency Completeness Authority."""

from __future__ import annotations

from research.examples.counterexamples.counterexample_corpus import (
    Counterexample,
    CounterexampleType,
    ResolutionStatus,
)


def build_counterexamples_031_040() -> list[Counterexample]:
    """Build counterexamples 031-040 for dependency completeness."""
    counterexamples = []

    # COUNTEREXAMPLE-031: False Completeness
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-031",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="False completeness",
        description=(
            "Static analysis, runtime traces, and documentation all agree: "
            "the dependency graph contains E1 and E2. "
            "Everything appears complete. "
            "But controlled intervention reveals E3 is necessary under a failure condition. "
            "The system should classify this as FALSE_COMPLETENESS, not MISSING_DEPENDENCY."
        ),
        original_assumption="Agreement across multiple sources implies completeness.",
        world_state={
            "static_analysis": ["E1", "E2"],
            "runtime_trace": ["E1", "E2"],
            "documentation": ["E1", "E2"],
            "controlled_intervention": ["E1", "E2", "E3"],
        },
        agent_state={
            "observation": "All sources agree but E3 is missing",
        },
        proposal={
            "action": "declare graph complete",
        },
        authority_state={
            "graph_status": "appears_complete",
            "actual": "incomplete_under_failure",
        },
        observed_failure="Protocol cannot detect false completeness.",
        expected_behavior="Protocol should flag agreement across sources as untested completeness.",
        actual_behavior="Protocol declares graph complete because sources agree.",
        classification="FALSE_COMPLETENESS",
        provenance=["completeness_experiment", "false_completeness"],
        reproduction_procedure=[
            "1. Create world where E1, E2 are declared",
            "2. Static analysis confirms E1, E2",
            "3. Runtime trace confirms E1, E2",
            "4. Documentation confirms E1, E2",
            "5. Controlled intervention reveals E3 necessary under failure",
            "6. Observe whether protocol detects false completeness",
        ],
    ))

    # COUNTEREXAMPLE-032: Unknown Completeness Mistaken for Complete
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-032",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Unknown completeness mistaken for complete",
        description=(
            "Authorization A has dependency graph {E1}. "
            "New evidence E2 arrives. "
            "E2 does not intersect the graph. "
            "The protocol concludes PRESERVE because no intersection found. "
            "But the graph is actually incomplete — E2 is relevant. "
            "The system must distinguish NO_INTERSECTION_ESTABLISHED from NO_RELEVANT_DEPENDENCY_EXISTS."
        ),
        original_assumption="No intersection means no relevant dependency.",
        world_state={
            "declared_dependencies": ["E1"],
            "actual_dependencies": ["E1", "E2"],
            "new_evidence": "E2",
        },
        agent_state={
            "observation": "E2 does not intersect graph",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "graph_status": "unknown",
        },
        observed_failure="Protocol preserves because no intersection found.",
        expected_behavior="Protocol should flag unknown completeness.",
        actual_behavior="Protocol preserves because no intersection found.",
        classification="MISSING_SEMANTICS",
        provenance=["completeness_experiment", "unknown_completeness"],
        reproduction_procedure=[
            "1. Create authorization with dependency graph {E1}",
            "2. Actual dependencies are {E1, E2}",
            "3. New evidence E2 arrives",
            "4. Evaluate intersection",
            "5. Observe whether protocol distinguishes unknown from complete",
        ],
    ))

    # COUNTEREXAMPLE-033: Completeness Proven for Wrong Proposition
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-033",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Completeness proven for wrong proposition",
        description=(
            "Dependency graph is complete for proposition P1. "
            "Authorization is requested for proposition P2. "
            "The protocol must not allow completeness for P1 to authorize P2."
        ),
        original_assumption="Completeness is a property of the graph, not the proposition.",
        world_state={
            "proposition": "P2",
            "completeness_scope": "P1",
        },
        agent_state={
            "observation": "Graph is complete for P1, not P2",
        },
        proposal={
            "action": "authorize for P2",
        },
        authority_state={
            "completeness": "P1",
            "authorization": "P2",
        },
        observed_failure="Protocol does not scope completeness to proposition.",
        expected_behavior="Protocol should require completeness for P2 specifically.",
        actual_behavior="Protocol uses P1 completeness for P2 authorization.",
        classification="SCOPE_MISMATCH",
        provenance=["completeness_experiment", "proposition_scope"],
        reproduction_procedure=[
            "1. Create graph complete for P1",
            "2. Request authorization for P2",
            "3. Observe whether protocol checks proposition scope",
        ],
    ))

    # COUNTEREXAMPLE-034: Completeness Proven for Wrong Consequence
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-034",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Completeness proven for wrong consequence",
        description=(
            "Dependency graph is complete for READ_ONLY consequence. "
            "Authorization is requested for PAYMENT consequence. "
            "The same epistemic evidence supports observation but not payment. "
            "The protocol must distinguish consequence scopes."
        ),
        original_assumption="Completeness is independent of consequence.",
        world_state={
            "consequence": "PAYMENT",
            "completeness_scope": "READ_ONLY",
        },
        agent_state={
            "observation": "Graph is complete for read, not payment",
        },
        proposal={
            "action": "authorize payment",
        },
        authority_state={
            "completeness": "READ_ONLY",
            "authorization": "PAYMENT",
        },
        observed_failure="Protocol does not scope completeness to consequence.",
        expected_behavior="Protocol should require completeness for PAYMENT specifically.",
        actual_behavior="Protocol uses READ_ONLY completeness for PAYMENT.",
        classification="SCOPE_MISMATCH",
        provenance=["completeness_experiment", "consequence_scope"],
        reproduction_procedure=[
            "1. Create graph complete for READ_ONLY",
            "2. Request authorization for PAYMENT",
            "3. Observe whether protocol checks consequence scope",
        ],
    ))

    # COUNTEREXAMPLE-035: Completeness Proven for Wrong Environment
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-035",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Completeness proven for wrong environment",
        description=(
            "Dependency graph is complete in staging environment. "
            "Authorization is requested for production environment. "
            "The protocol must not allow staging completeness to authorize production."
        ),
        original_assumption="Completeness is independent of environment.",
        world_state={
            "environment": "production",
            "completeness_scope": "staging",
        },
        agent_state={
            "observation": "Graph is complete in staging, not production",
        },
        proposal={
            "action": "authorize in production",
        },
        authority_state={
            "completeness": "staging",
            "authorization": "production",
        },
        observed_failure="Protocol does not scope completeness to environment.",
        expected_behavior="Protocol should require completeness for production specifically.",
        actual_behavior="Protocol uses staging completeness for production.",
        classification="ENVIRONMENT_MISMATCH",
        provenance=["completeness_experiment", "environment_scope"],
        reproduction_procedure=[
            "1. Create graph complete in staging",
            "2. Request authorization for production",
            "3. Observe whether protocol checks environment scope",
        ],
    ))

    # COUNTEREXAMPLE-036: Completeness Proven for Wrong Temporal Interval
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-036",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.TEMPORAL_ERROR,
        title="Completeness proven for wrong temporal interval",
        description=(
            "Dependency graph is complete for 2026-01-01/2027-01-01. "
            "Authorization is requested for 2027-01-01/2028-01-01. "
            "The protocol must not allow temporal completeness to authorize outside bounds."
        ),
        original_assumption="Completeness is temporally unbounded.",
        world_state={
            "temporal_interval": "2027-01-01/2028-01-01",
            "completeness_scope": "2026-01-01/2027-01-01",
        },
        agent_state={
            "observation": "Graph is complete in 2026, not 2027",
        },
        proposal={
            "action": "authorize for 2027",
        },
        authority_state={
            "completeness": "2026",
            "authorization": "2027",
        },
        observed_failure="Protocol does not scope completeness to temporal interval.",
        expected_behavior="Protocol should require completeness for 2027 specifically.",
        actual_behavior="Protocol uses 2026 completeness for 2027.",
        classification="TEMPORAL_MISMATCH",
        provenance=["completeness_experiment", "temporal_scope"],
        reproduction_procedure=[
            "1. Create graph complete for 2026",
            "2. Request authorization for 2027",
            "3. Observe whether protocol checks temporal scope",
        ],
    ))

    # COUNTEREXAMPLE-037: Over-Approximation Causes False Suspension
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-037",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.OVERLY_CONSERVATIVE_POLICY,
        title="Over-approximation causes false suspension",
        description=(
            "Actual dependencies: {E1}. "
            "Declared dependencies: {E1, E2, E3, E4, E5}. "
            "Evidence contradicts E5 (which was never necessary). "
            "The protocol suspends the authorization. "
            "This is a false suspension caused by over-approximation."
        ),
        original_assumption="More dependencies = more safety.",
        world_state={
            "actual_dependencies": ["E1"],
            "declared_dependencies": ["E1", "E2", "E3", "E4", "E5"],
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
            "graph_status": "over_approximated",
        },
        observed_failure="Over-broad dependencies cause false suspensions.",
        expected_behavior="Protocol should only suspend for necessary dependencies.",
        actual_behavior="Protocol suspends due to contradicted extra dependency.",
        classification="OVERLY_CONSERVATIVE_POLICY",
        provenance=["completeness_experiment", "over_approximation"],
        reproduction_procedure=[
            "1. Create authorization with extra dependencies",
            "2. Introduce evidence contradicting an extra dependency",
            "3. Observe false suspension",
        ],
    ))

    # COUNTEREXAMPLE-038: Under-Approximation Causes False Preservation
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-038",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Under-approximation causes false preservation",
        description=(
            "Actual dependencies: {E1, E2, E3}. "
            "Declared dependencies: {E1}. "
            "New evidence E4 arrives that contradicts E2 (a missing dependency). "
            "The protocol preserves because E4 doesn't intersect the (incomplete) graph. "
            "This is a false preservation caused by under-approximation."
        ),
        original_assumption="No intersection means no relevant dependency.",
        world_state={
            "actual_dependencies": ["E1", "E2", "E3"],
            "declared_dependencies": ["E1"],
            "new_evidence": "E4 contradicts E2",
        },
        agent_state={
            "observation": "E4 contradicts missing dependency E2",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
            "graph_status": "under_approximated",
        },
        observed_failure="Protocol preserves because no intersection found.",
        expected_behavior="Protocol should detect incomplete graph and require reevaluation.",
        actual_behavior="Protocol preserves because E4 doesn't intersect graph.",
        classification="MISSING_SEMANTICS",
        provenance=["completeness_experiment", "under_approximation"],
        reproduction_procedure=[
            "1. Create authorization with incomplete graph {E1}",
            "2. Actual dependencies are {E1, E2, E3}",
            "3. New evidence E4 contradicts E2",
            "4. Evaluate intersection",
            "5. Observe false preservation",
        ],
    ))

    # COUNTEREXAMPLE-039: Completeness Bootstrap Cycle
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-039",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Completeness bootstrap cycle",
        description=(
            "Authorization A requires completeness claim C. "
            "C depends on experiment X. "
            "X requires Authorization A. "
            "This produces a cycle: A → C → X → A. "
            "The protocol must detect this as a bootstrap, not a valid dependency."
        ),
        original_assumption="Completeness claims are independently justified.",
        world_state={
            "authorization": "A",
            "completeness_claim": "C",
            "experiment": "X",
        },
        agent_state={
            "observation": "Cycle detected: A → C → X → A",
        },
        proposal={
            "action": "break cycle",
        },
        authority_state={
            "A": "requires C",
            "C": "requires X",
            "X": "requires A",
        },
        observed_failure="Protocol cannot detect bootstrap cycles.",
        expected_behavior="Protocol should detect and reject bootstrap cycles.",
        actual_behavior="Protocol accepts cycle as valid dependency structure.",
        classification="AUTHORITY_BOOTSTRAP",
        provenance=["completeness_experiment", "bootstrap_cycle"],
        reproduction_procedure=[
            "1. Create authorization A",
            "2. A requires completeness claim C",
            "3. C depends on experiment X",
            "4. X requires authorization A",
            "5. Observe whether protocol detects cycle",
        ],
    ))

    # COUNTEREXAMPLE-040: Cross-Domain Completeness Laundering
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-040",
        timestamp="2026-09-09T18:00:00Z",
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Cross-domain completeness laundering",
        description=(
            "Domain A (payments) has a complete dependency graph. "
            "Domain B (identity) imports Domain A's completeness claim. "
            "Domain B's authorization is granted based on Domain A's completeness. "
            "The protocol must not allow cross-domain completeness laundering."
        ),
        original_assumption="Completeness is domain-independent.",
        world_state={
            "domain_a": "payments",
            "domain_b": "identity",
            "completeness": "domain_a",
        },
        agent_state={
            "observation": "Domain B imports Domain A's completeness",
        },
        proposal={
            "action": "authorize in Domain B",
        },
        authority_state={
            "domain_a_completeness": "valid",
            "domain_b_authorization": "granted",
        },
        observed_failure="Protocol allows cross-domain completeness laundering.",
        expected_behavior="Protocol should require domain-specific completeness.",
        actual_behavior="Protocol grants authorization based on foreign completeness.",
        classification="DOMAIN_MISMATCH",
        provenance=["completeness_experiment", "cross_domain"],
        reproduction_procedure=[
            "1. Create complete graph in Domain A",
            "2. Request authorization in Domain B",
            "3. Domain B imports Domain A's completeness",
            "4. Observe whether protocol detects domain mismatch",
        ],
    ))

    return counterexamples
