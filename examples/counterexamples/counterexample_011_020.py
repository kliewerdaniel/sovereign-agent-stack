"""Counterexamples 011-020: Epistemic Invalidation and Dependency."""

from __future__ import annotations

from examples.counterexamples.counterexample_corpus import (
    Counterexample,
    CounterexampleType,
    ResolutionStatus,
)


def build_counterexamples_011_020() -> list[Counterexample]:
    """Build counterexamples 011-020 for epistemic invalidation."""
    counterexamples = []

    # COUNTEREXAMPLE-011: Unrelated evidence after authorization
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-011",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.VALID_REJECTION,
        title="Unrelated evidence after authorization",
        description=(
            "New evidence arrives that is completely unrelated to the authorization's "
            "dependencies. The protocol must not invalidate the authorization."
        ),
        original_assumption="All new evidence should trigger reevaluation.",
        world_state={
            "authorization": "auth_001",
            "new_evidence": "ev_unrelated",
            "relation": "unrelated",
        },
        agent_state={
            "observation": "unrelated event occurred",
        },
        proposal={
            "action": "preserve authorization",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Unrelated evidence should not affect authorization.",
        expected_behavior="Authorization is preserved.",
        actual_behavior="Authorization is preserved (correct).",
        classification="VALID_REJECTION",
        provenance=["epistemic_invalidation", "dependency_intersection"],
        reproduction_procedure=[
            "1. Create authorization with dependencies",
            "2. Introduce unrelated evidence",
            "3. Evaluate intersection",
            "4. Verify authorization is preserved",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly preserves authorization when evidence is unrelated.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-012: Relevant evidence after authorization
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-012",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Relevant evidence after authorization",
        description=(
            "New evidence arrives that is relevant to an authorization dependency "
            "but does not contradict it. The protocol should flag for reevaluation."
        ),
        original_assumption="Only contradictory evidence matters.",
        world_state={
            "authorization": "auth_001",
            "new_evidence": "ev_relevant",
            "relation": "relevant",
        },
        agent_state={
            "observation": "relevant event occurred",
        },
        proposal={
            "action": "reevaluate authorization",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Relevant evidence should trigger reevaluation.",
        expected_behavior="Authorization requires reevaluation.",
        actual_behavior="Authorization requires reevaluation (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["epistemic_invalidation"],
        reproduction_procedure=[
            "1. Create authorization with dependencies",
            "2. Introduce relevant evidence",
            "3. Evaluate intersection",
            "4. Verify reevaluation is triggered",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly triggers reevaluation for relevant evidence.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-013: Contradictory evidence after authorization
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-013",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Contradictory evidence after authorization",
        description=(
            "New evidence arrives that directly contradicts a proposition "
            "that the authorization depends on. The protocol should suspend."
        ),
        original_assumption="Contradictory evidence should automatically revoke.",
        world_state={
            "authorization": "auth_001",
            "new_evidence": "ev_contradictory",
            "relation": "contradicts",
        },
        agent_state={
            "observation": "contradictory event occurred",
        },
        proposal={
            "action": "suspend authorization",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Contradictory evidence should suspend authorization.",
        expected_behavior="Authorization is suspended pending governance review.",
        actual_behavior="Authorization is suspended (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["epistemic_invalidation"],
        reproduction_procedure=[
            "1. Create authorization with proposition dependency",
            "2. Introduce contradictory evidence",
            "3. Evaluate intersection",
            "4. Verify suspension",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly suspends authorization for contradictory evidence.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-014: Evidence invalidates original experiment
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-014",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Evidence invalidates original experiment",
        description=(
            "New evidence shows that the experiment that produced the original "
            "evidence was flawed. This should suspend the authorization."
        ),
        original_assumption="Experiments are always valid.",
        world_state={
            "authorization": "auth_001",
            "experiment": "exp_001",
            "new_evidence": "ev_invalidates_experiment",
        },
        agent_state={
            "observation": "experiment was flawed",
        },
        proposal={
            "action": "suspend authorization",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Invalidated experiment should suspend authorization.",
        expected_behavior="Authorization is suspended.",
        actual_behavior="Authorization is suspended (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["epistemic_invalidation"],
        reproduction_procedure=[
            "1. Create authorization with experiment dependency",
            "2. Introduce evidence invalidating experiment",
            "3. Evaluate intersection",
            "4. Verify suspension",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly suspends when experiment is invalidated.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-015: Resource state changes without epistemic change
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-015",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Resource state changes without epistemic change",
        description=(
            "The resource state changes but the epistemic state remains the same. "
            "The protocol must distinguish resource staleness from epistemic staleness."
        ),
        original_assumption="Resource change = epistemic change.",
        world_state={
            "resource": "provider",
            "old_state": "active",
            "new_state": "inactive",
            "epistemic_state": "unchanged",
        },
        agent_state={
            "observation": "resource changed but proposition still holds",
        },
        proposal={
            "action": "reevaluate resource dependency",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Resource change should not trigger epistemic invalidation.",
        expected_behavior="Authorization is flagged for reevaluation.",
        actual_behavior="Authorization is flagged for reevaluation (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["epistemic_invalidation"],
        reproduction_procedure=[
            "1. Create authorization with resource dependency",
            "2. Change resource state",
            "3. Evaluate intersection",
            "4. Verify reevaluation is triggered",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly distinguishes resource staleness.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-016: Governance state changes without evidence change
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-016",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.MISSING_SEMANTICS,
        title="Governance state changes without evidence change",
        description=(
            "Governance policy changes but the underlying evidence remains the same. "
            "The protocol must distinguish governance staleness from epistemic staleness."
        ),
        original_assumption="Governance change = evidence change.",
        world_state={
            "governance": "policy_001",
            "old_effect": "allow",
            "new_effect": "prohibit",
            "evidence": "unchanged",
        },
        agent_state={
            "observation": "governance changed but evidence still supports proposition",
        },
        proposal={
            "action": "reevaluate governance dependency",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Governance change should trigger reevaluation.",
        expected_behavior="Authorization requires reevaluation.",
        actual_behavior="Authorization requires reevaluation (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["epistemic_invalidation"],
        reproduction_procedure=[
            "1. Create authorization with governance dependency",
            "2. Change governance policy",
            "3. Evaluate intersection",
            "4. Verify reevaluation is triggered",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly handles governance changes.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-017: Epistemic dependency cycle
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-017",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.AUTHORITY_ERROR,
        title="Epistemic dependency cycle",
        description=(
            "Authorization A depends on proposition P, which depends on evidence E, "
            "which depends on experiment X, which was permitted by authorization A. "
            "This creates a cycle: A → P → E → X → A."
        ),
        original_assumption="Authorizations cannot be self-justifying.",
        world_state={
            "authorization": "auth_001",
            "proposition": "prop_001",
            "evidence": "ev_001",
            "experiment": "exp_001",
        },
        agent_state={
            "observation": "cycle detected",
        },
        proposal={
            "action": "detect and reject cycle",
        },
        authority_state={
            "auth_001": "valid",
        },
        observed_failure="Cycle should be detected and rejected.",
        expected_behavior="Cycle is detected and governance review is required.",
        actual_behavior="Cycle is detected (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["epistemic_cycles"],
        reproduction_procedure=[
            "1. Create authorization with experiment dependency",
            "2. Map experiment to authorization",
            "3. Run cycle detection",
            "4. Verify cycle is detected",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly detects epistemic dependency cycles.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-018: Multi-agent evidence invalidation
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-018",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.AMBIGUOUS_SEMANTICS,
        title="Multi-agent evidence invalidation",
        description=(
            "Agent A's evidence should not automatically invalidate Agent B's "
            "authorization. Evidence must enter the epistemic protocol."
        ),
        original_assumption="All evidence affects all authorizations equally.",
        world_state={
            "agent_a": "researcher",
            "agent_b": "operator",
            "evidence": "from researcher",
        },
        agent_state={
            "researcher": "new evidence",
            "operator": "existing authorization",
        },
        proposal={
            "action": "evaluate evidence against operator's dependencies",
        },
        authority_state={
            "operator_auth": "valid",
        },
        observed_failure="Agent A's evidence should not auto-invalidate Agent B.",
        expected_behavior="Evidence is evaluated against dependencies.",
        actual_behavior="Evidence is evaluated against dependencies (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["multi_agent_dependencies"],
        reproduction_procedure=[
            "1. Create authorization for Agent B",
            "2. Agent A produces new evidence",
            "3. Evaluate evidence against Agent B's dependencies",
            "4. Verify no automatic invalidation",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly evaluates evidence per-authorization.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-019: Partial plan invalidation
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-019",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.COMPOSITION_ERROR,
        title="Partial plan invalidation",
        description=(
            "A plan A → B → C where only B's epistemic dependency becomes invalid. "
            "A should remain historically valid, C should require reevaluation."
        ),
        original_assumption="Invalidation propagates transitively.",
        world_state={
            "plan": "A → B → C",
            "B_status": "invalid",
        },
        agent_state={
            "observation": "B is invalid",
        },
        proposal={
            "action": "invalidate B, preserve A, reevaluate C",
        },
        authority_state={
            "A_auth": "valid",
            "B_auth": "invalid",
            "C_auth": "valid",
        },
        observed_failure="Only B should be invalidated.",
        expected_behavior="A preserved, B invalidated, C requires reevaluation.",
        actual_behavior="A preserved, B invalidated, C requires reevaluation (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["partial_invalidation"],
        reproduction_procedure=[
            "1. Create plan A → B → C",
            "2. Invalidate B",
            "3. Evaluate partial invalidation",
            "4. Verify A preserved, C requires reevaluation",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly handles partial invalidation.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    # COUNTEREXAMPLE-020: Dependent authorization stale while independent valid
    counterexamples.append(Counterexample(
        counterexample_id="COUNTEREXAMPLE-020",
        timestamp="2026-09-09T17:15:00Z",
        counterexample_type=CounterexampleType.COMPOSITION_ERROR,
        title="Dependent authorization stale while independent remains valid",
        description=(
            "Two authorizations exist: one dependent on evidence E, one independent. "
            "New evidence contradicts E. Only the dependent authorization should be suspended."
        ),
        original_assumption="All authorizations are affected equally.",
        world_state={
            "dependent_auth": "auth_d",
            "independent_auth": "auth_i",
            "evidence": "E",
        },
        agent_state={
            "observation": "E is contradicted",
        },
        proposal={
            "action": "suspend auth_d, preserve auth_i",
        },
        authority_state={
            "auth_d": "valid",
            "auth_i": "valid",
        },
        observed_failure="Only dependent authorization should be suspended.",
        expected_behavior="auth_d suspended, auth_i preserved.",
        actual_behavior="auth_d suspended, auth_i preserved (correct).",
        classification="EXPECTED_BEHAVIOR",
        provenance=["partial_invalidation"],
        reproduction_procedure=[
            "1. Create dependent and independent authorizations",
            "2. Contradict evidence E",
            "3. Evaluate both authorizations",
            "4. Verify only dependent is suspended",
        ],
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_notes="Protocol correctly handles differential invalidation.",
        resolution_timestamp="2026-09-09T17:20:00Z",
    ))

    return counterexamples
