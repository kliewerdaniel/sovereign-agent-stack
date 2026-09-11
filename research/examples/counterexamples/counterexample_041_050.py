"""Counterexamples 041-050: Temporal Completeness Drift and Revalidation."""

from __future__ import annotations

from research.examples.counterexamples.counterexample_corpus import (
    Counterexample,
    CounterexampleType,
)


def build_counterexamples_041_050() -> list[Counterexample]:
    """Build counterexamples 041-050 for temporal completeness drift."""
    ces = []

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-041",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Unrelated world drift falsely marks completeness stale",
        description=(
            "World changes in a component unrelated to the authorization. "
            "The system must NOT classify completeness as stale merely because the world changed."
        ),
        original_assumption="World change implies completeness staleness.",
        world_state={"t0": {"dependencies": ["E1"]}, "t1": {"dependencies": ["E1"], "unrelated": "E99"}},
        agent_state={"observation": "E99 added but no dependency change"},
        proposal={"action": "mark completeness stale"},
        authority_state={"completeness": "sufficient"},
        observed_failure="Protocol marks completeness stale when world changes.",
        expected_behavior="Protocol should preserve completeness when change is unrelated.",
        actual_behavior="Protocol marks completeness stale.",
        classification="OVERLY_CONSERVATIVE_POLICY",
        provenance=["temporal_completeness", "world_drift_vs_completeness_drift"],
        reproduction_procedure=[
            "1. Create authorization with dependency E1",
            "2. Assess completeness = sufficient",
            "3. World changes: E99 added (unrelated)",
            "4. Observe whether completeness is falsely marked stale",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-042",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Hidden dependency exists before discovery",
        description=(
            "E2 exists in the world at T0 but is not discovered until T2. "
            "At T1, the actual world differs from the model's dependency graph, but the protocol does not yet know that. "
            "Determine whether the correct epistemic state is COMPLETE, UNKNOWN, or SUFFICIENT_WITHIN_KNOWN_SCOPE."
        ),
        original_assumption="Objective completeness = epistemically established completeness.",
        world_state={"t0": {"actual": ["E1", "E2"], "known": ["E1"]}},
        agent_state={"observation": "E2 exists but undiscovered"},
        proposal={"action": "classify completeness"},
        authority_state={"completeness": "ambiguous"},
        observed_failure="Protocol cannot represent complete within known scope.",
        expected_behavior="Protocol should use UNKNOWN or SCOPE_LIMITED_COMPLETENESS.",
        actual_behavior="Protocol declares COMPLETE.",
        classification="MISSING_SEMANTICS",
        provenance=["temporal_completeness", "hidden_staleness"],
        reproduction_procedure=[
            "1. E2 exists at T0 but undiscovered",
            "2. Protocol assesses completeness at T0",
            "3. E2 discovered at T2",
            "4. Verify protocol didn't falsely claim complete knowledge",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-043",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.EPISTEMIC_ERROR,
        title="Runtime discovery mistaken for validated dependency",
        description=(
            "Runtime trace observes A -> E2. "
            "Do not automatically classify this as necessary dependency. "
            "Runtime co-occurrence is not necessary dependency."
        ),
        original_assumption="Runtime trace equals dependency.",
        world_state={"runtime": ["A -> E2"]},
        agent_state={"observation": "Runtime observed co-occurrence"},
        proposal={"action": "classify E2 as validated dependency"},
        authority_state={"E2_status": "hypothesized"},
        observed_failure="Protocol promotes runtime observation to validated dependency.",
        expected_behavior="Protocol should keep E2 as DEPENDENCY_HYPOTHESIS.",
        actual_behavior="Protocol classifies E2 as validated dependency.",
        classification="EPISTEMIC_ERROR",
        provenance=["temporal_completeness", "runtime_vs_validated"],
        reproduction_procedure=[
            "1. Runtime observes A -> E2",
            "2. Protocol must not promote to validated",
            "3. Requires controlled intervention for validation",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-044",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Completeness sufficient for one consequence but insufficient for another",
        description=(
            "Same dependency model used for multiple consequences: "
            "Observation, Research, Recommendation, Trade, Payment, Identity Mutation. "
            "The same completeness evidence may be sufficient for READ_ONLY but insufficient for PAYMENT."
        ),
        original_assumption="Completeness is consequence-independent.",
        world_state={"dependency_model": ["E1", "E2"], "consequence": "PAYMENT"},
        agent_state={"observation": "Graph complete for READ_ONLY"},
        proposal={"action": "authorize PAYMENT"},
        authority_state={"completeness": "READ_ONLY", "requested": "PAYMENT"},
        observed_failure="Protocol allows PAYMENT with READ_ONLY completeness.",
        expected_behavior="Protocol should require PAYMENT-level completeness.",
        actual_behavior="Protocol uses same completeness for all consequences.",
        classification="SCOPE_MISMATCH",
        provenance=["temporal_completeness", "consequence_escalation"],
        reproduction_procedure=[
            "1. Create dependency model sufficient for READ_ONLY",
            "2. Attempt to authorize PAYMENT using same model",
            "3. Observe whether protocol requires consequence-specific completeness",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-045",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Completeness valid in staging but not production",
        description=(
            "Dependency graph is complete in staging environment. "
            "Authorization is requested for production. "
            "The protocol must not allow staging completeness to authorize production."
        ),
        original_assumption="Completeness is environment-independent.",
        world_state={"environment": "production", "completeness_scope": "staging"},
        agent_state={"observation": "Graph complete in staging"},
        proposal={"action": "authorize in production"},
        authority_state={"completeness": "staging", "requested": "production"},
        observed_failure="Protocol allows production authorization with staging completeness.",
        expected_behavior="Protocol should require production-specific completeness.",
        actual_behavior="Protocol uses staging completeness for production.",
        classification="ENVIRONMENT_MISMATCH",
        provenance=["temporal_completeness", "environment_scope"],
        reproduction_procedure=[
            "1. Create graph complete in staging",
            "2. Request production authorization",
            "3. Observe whether protocol checks environment scope",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-046",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.TEMPORAL_ERROR,
        title="Completeness valid before feature-flag activation but stale afterward",
        description=(
            "P depends on E2 only when feature_flag = true. "
            "At T0: flag = false, completeness valid. "
            "At T1: flag = true, completeness becomes stale."
        ),
        original_assumption="Completeness is temporally stable.",
        world_state={"t0": {"flag": False}, "t1": {"flag": True}},
        agent_state={"observation": "Feature flag changed"},
        proposal={"action": "preserve completeness claim"},
        authority_state={"completeness": "conditional"},
        observed_failure="Protocol does not track conditional completeness.",
        expected_behavior="Protocol should detect that condition changed.",
        actual_behavior="Protocol preserves stale completeness.",
        classification="MISSING_SEMANTICS",
        provenance=["temporal_completeness", "conditional_completeness"],
        reproduction_procedure=[
            "1. Create conditional completeness (flag=false)",
            "2. Change flag to true",
            "3. Observe whether protocol detects staleness",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-047",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Dependency change propagates farther than authority should",
        description=(
            "A -> B -> C -> D. Change B. "
            "Protocol must determine exact propagation frontier: "
            "A preserved, B reevaluated, C affected, D affected. "
            "Do not propagate farther than necessary."
        ),
        original_assumption="Dependency propagation equals authority propagation.",
        world_state={"chain": "A -> B -> C -> D", "change": "B"},
        agent_state={"observation": "B changed"},
        proposal={"action": "reevaluate entire chain"},
        authority_state={"propagation": "unbounded"},
        observed_failure="Protocol propagates revocation beyond necessary frontier.",
        expected_behavior="Protocol should compute minimal revalidation frontier.",
        actual_behavior="Protocol reevaluates everything.",
        classification="OVERLY_CONSERVATIVE_POLICY",
        provenance=["temporal_completeness", "revalidation_propagation"],
        reproduction_procedure=[
            "1. Create chain A -> B -> C -> D",
            "2. Change B",
            "3. Observe whether protocol propagates beyond affected nodes",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-048",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Completeness change incorrectly revokes historical authority",
        description=(
            "T0: Authorization issued, completeness valid. "
            "T1: Execution occurs. "
            "T2: Dependency discovered. "
            "T3: Completeness reassessed. "
            "The T0 authorization must NOT be retroactively invalidated."
        ),
        original_assumption="Completeness discovery retroactively invalidates authority.",
        world_state={"t0": {"auth": "valid"}, "t2": {"discovery": "E2"}},
        agent_state={"observation": "E2 discovered post-execution"},
        proposal={"action": "revoke T0 authorization"},
        authority_state={"t0": "valid", "t2": "revoked"},
        observed_failure="Protocol retroactively revokes historical authority.",
        expected_behavior="Protocol should preserve historical authority.",
        actual_behavior="Protocol revokes T0 authorization.",
        classification="AUTHORITY_ERROR",
        provenance=["temporal_completeness", "historical_authority"],
        reproduction_procedure=[
            "1. Issue authorization at T0",
            "2. Execute at T1",
            "3. Discover dependency at T2",
            "4. Verify T0 authorization is not revoked",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-049",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Distributed completeness disagreement resolved by majority",
        description=(
            "Node A: completeness assessment C1. "
            "Node B: completeness assessment C2. "
            "Node C: newly discovered dependency. "
            "C1 != C2. "
            "Protocol must not simply choose the majority."
        ),
        original_assumption="Distributed agreement equals completeness authority.",
        world_state={"C1": "complete", "C2": "incomplete", "C3": "unknown"},
        agent_state={"observation": "Nodes disagree"},
        proposal={"action": "resolve by majority"},
        authority_state={"completeness": "conflicting"},
        observed_failure="Protocol resolves disagreement by majority.",
        expected_behavior="Protocol should produce UNKNOWN/CONFLICT.",
        actual_behavior="Protocol chooses majority.",
        classification="AUTHORITY_ERROR",
        provenance=["temporal_completeness", "distributed_completeness"],
        reproduction_procedure=[
            "1. Create 3 nodes with different completeness assessments",
            "2. Introduce new dependency on Node C",
            "3. Observe whether protocol resolves by majority",
        ],
    ))

    ces.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-050",
        timestamp="2026-09-09T19:00:00Z",
        counterexample_type=CounterexampleType.OVERLY_CONSERVATIVE_POLICY,
        title="Revalidation scope broader than necessary",
        description=(
            "Authorization A with dependencies {E1, E2, E3, R1, G1}. "
            "Change occurs to E2. "
            "Protocol must determine the MINIMUM epistemic surface to reconsider. "
            "Do not recompute everything."
        ),
        original_assumption="Any change requires full revalidation.",
        world_state={"dependencies": ["E1", "E2", "E3", "R1", "G1"], "change": "E2"},
        agent_state={"observation": "E2 changed"},
        proposal={"action": "revalidate everything"},
        authority_state={"revalidation": "full"},
        observed_failure="Protocol recomputes everything.",
        expected_behavior="Protocol should compute minimal frontier: {E2, P, C, A}.",
        actual_behavior="Protocol recomputes all dependencies.",
        classification="OVERLY_CONSERVATIVE_POLICY",
        provenance=["temporal_completeness", "revalidation_minimality"],
        reproduction_procedure=[
            "1. Create authorization with 5 dependencies",
            "2. Change E2",
            "3. Observe whether protocol computes minimal frontier",
        ],
    ))

    return ces
