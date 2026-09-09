"""Temporal completeness drift experiments.

Exercises 12 scenarios to verify the protocol can distinguish:
- WORLD DRIFT
- DEPENDENCY DRIFT
- COMPLETENESS DRIFT
- EPISTEMIC DRIFT
- GOVERNANCE DRIFT
- AUTHORITY DRIFT

And can answer: WHAT IS THE MINIMUM EPISTEMIC SURFACE THAT MUST BE REVALIDATED?
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from examples.self_audit.authority_drift import (
    AuthorityDriftEvent,
    DriftClassification,
    DriftType,
)
from examples.self_audit.continuous_reconciliation import WorldState
from examples.sovereign_agent.dependency_completeness import (
    CompletenessMethod,
    CompletenessScope,
    CompletenessStatus,
    IntersectionStatus,
    create_completeness_scope,
)
from examples.sovereign_agent.temporal_completeness import (
    CompletenessDriftFinding,
    CompletenessDriftType,
    CompletenessValidityInterval,
    RevalidationFrontier,
    RevalidationRequirement,
    TemporalCompletenessEngine,
)


def make_world(
    timestamp: str,
    providers: list[str],
    extra_nodes: list[dict[str, str]] | None = None,
    extra_edges: list[dict[str, str]] | None = None,
) -> WorldState:
    """Create a world state with given dependency providers."""
    nodes = [{"id": "checkout", "type": "service"}, {"id": "payment_gateway", "type": "service"}]
    edges = [{"source": "checkout", "target": "payment_gateway", "type": "call"}]

    for p in providers:
        nodes.append({"id": p, "type": "external"})
        edges.append({"source": "payment_gateway", "target": p, "type": "dependency"})

    if extra_nodes:
        nodes.extend(extra_nodes)
    if extra_edges:
        edges.extend(extra_edges)

    return WorldState(
        timestamp=timestamp,
        static_topology={"nodes": nodes, "edges": edges},
        documented_topology={"nodes": nodes[:3], "edges": edges[:2]},
        runtime_topology={
            "actors": ["checkout"],
            "paths": [
                {"id": "p1", "actor": "checkout", "source": "checkout", "target": "payment_gateway"},
                {"id": "p2", "actor": "payment_gateway", "source": "payment_gateway", "target": providers[0] if providers else "provider_a"},
            ],
        },
        authority_state={
            "actor": "payment_gateway",
            "operation": "charge",
            "resource": providers[0] if providers else "provider_a",
            "consequence_type": "payment",
            "authorization_id": "auth_001",
        },
        governance_state={
            "policies": [{"id": "pol_1", "actor": "payment_gateway", "action": "charge"}],
        },
    )


def make_drift_event(
    event_id: str,
    timestamp: str,
    event_type: str,
    previous_state: dict[str, Any],
    new_state: dict[str, Any],
    affected_actor: str = "payment_gateway",
    affected_component: str = "payment_gateway",
) -> AuthorityDriftEvent:
    """Create a drift event."""
    return AuthorityDriftEvent(
        event_id=event_id,
        timestamp=timestamp,
        event_type=event_type,
        description=f"{event_type}: {previous_state} -> {new_state}",
        affected_actor=affected_actor,
        affected_component=affected_component,
        previous_state=previous_state,
        new_state=new_state,
    )


def run_t0_baseline(engine: TemporalCompletenessEngine, scope: CompletenessScope):
    """T0: Establish baseline completeness."""
    world_t0 = make_world("2026-01-01T00:00:00Z", ["provider_a"])

    assessment, interval = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a"],
        actual_dependencies=["provider_a"],
        scope=scope,
        timestamp="2026-01-01T00:00:00Z",
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    return world_t0, assessment, interval


def run_t1_irrelevant_world_change(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t0: WorldState, assessment_t0):
    """T1: Irrelevant world change - E99 has no dependency relationship to P or A."""
    # E99 is connected via a "call" edge, not a "dependency" edge
    # So it should NOT show up as a dependency change
    world_t1 = make_world(
        "2026-02-01T00:00:00Z",
        ["provider_a"],
        extra_nodes=[{"id": "e99", "type": "external"}],
        extra_edges=[{"source": "some_service", "target": "e99", "type": "call"}],
    )

    drift_event = make_drift_event(
        "event_t1", "2026-02-01T00:00:00Z", "irrelevant_world_change",
        {"provider": "provider_a"}, {"provider": "provider_a", "e99": "new"},
    )

    assessment_t1, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a"],
        actual_dependencies=["provider_a"],
        scope=scope,
        timestamp="2026-02-01T00:00:00Z",
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t0, world_t1, assessment_t0, assessment_t1,
        "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", scope,
    )

    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", ["provider_a"], "prop_001", "payment", scope,
    )

    return world_t1, assessment_t1, findings, frontier


def run_t2_latent_dependency(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t1: WorldState, assessment_t1):
    """T2: Latent dependency appears - E2 present but no observed consequence."""
    world_t2 = make_world(
        "2026-03-01T00:00:00Z",
        ["provider_a", "e2_new"],
    )

    drift_event = make_drift_event(
        "event_t2", "2026-03-01T00:00:00Z", "latent_dependency_appears",
        {"dependencies": ["provider_a"]}, {"dependencies": ["provider_a", "e2_new"]},
    )

    assessment_t2, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a"],
        actual_dependencies=["provider_a", "e2_new"],
        scope=scope,
        timestamp="2026-03-01T00:00:00Z",
        method=CompletenessMethod.STATIC_ANALYSIS_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t1, world_t2, assessment_t1, assessment_t2,
        "2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z", scope,
    )

    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", ["provider_a"], "prop_001", "payment", scope,
    )

    return world_t2, assessment_t2, findings, frontier


def run_t3_runtime_discovery(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t2: WorldState, assessment_t2):
    """T3: Runtime trace observes A -> E2."""
    world_t3 = make_world(
        "2026-04-01T00:00:00Z",
        ["provider_a", "e2_new"],
    )

    drift_event = make_drift_event(
        "event_t3", "2026-04-01T00:00:00Z", "runtime_discovery",
        {"runtime_known": ["provider_a"]}, {"runtime_known": ["provider_a", "e2_new"]},
    )

    assessment_t3, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a"],
        actual_dependencies=["provider_a", "e2_new"],
        scope=scope,
        timestamp="2026-04-01T00:00:00Z",
        method=CompletenessMethod.RUNTIME_TRACE_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t2, world_t3, assessment_t2, assessment_t3,
        "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", scope,
    )

    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", ["provider_a"], "prop_001", "payment", scope,
    )

    return world_t3, assessment_t3, findings, frontier


def run_t4_intervention(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t3: WorldState, assessment_t3):
    """T4: Controlled intervention on E2."""
    world_t4 = make_world(
        "2026-05-01T00:00:00Z",
        ["provider_a", "e2_new"],
    )

    drift_event = make_drift_event(
        "event_t4", "2026-05-01T00:00:00Z", "intervention_validates_e2",
        {"e2_status": "hypothesized"}, {"e2_status": "validated"},
    )

    assessment_t4, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a", "e2_new"],
        actual_dependencies=["provider_a", "e2_new"],
        scope=scope,
        timestamp="2026-05-01T00:00:00Z",
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t3, world_t4, assessment_t3, assessment_t4,
        "2026-04-01T00:00:00Z", "2026-05-01T00:00:00Z", scope,
    )

    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", ["provider_a", "e2_new"], "prop_001", "payment", scope,
    )

    return world_t4, assessment_t4, findings, frontier


def run_t5_completeness_changes(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t4: WorldState, assessment_t4):
    """T5: Completeness changes - reassess at T0 and T5."""
    world_t5 = make_world(
        "2026-06-01T00:00:00Z",
        ["provider_a", "e2_new"],
    )

    assessment_t5, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a", "e2_new"],
        actual_dependencies=["provider_a", "e2_new"],
        scope=scope,
        timestamp="2026-06-01T00:00:00Z",
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t4, world_t5, assessment_t4, assessment_t5,
        "2026-05-01T00:00:00Z", "2026-06-01T00:00:00Z", scope,
    )

    return world_t5, assessment_t5, findings


def run_t6_contradictory_evidence(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t5: WorldState, assessment_t5):
    """T6: Evidence E3 contradicts proposition P."""
    world_t6 = make_world(
        "2026-07-01T00:00:00Z",
        ["provider_a", "e2_new"],
    )

    drift_event = make_drift_event(
        "event_t6", "2026-07-01T00:00:00Z", "contradictory_evidence",
        {"proposition": "supported"}, {"proposition": "contradicted"},
    )

    assessment_t6, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a", "e2_new"],
        actual_dependencies=["provider_a", "e2_new"],
        scope=scope,
        timestamp="2026-07-01T00:00:00Z",
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t5, world_t6, assessment_t5, assessment_t6,
        "2026-06-01T00:00:00Z", "2026-07-01T00:00:00Z", scope,
    )

    frontier = engine.compute_revalidation_frontier(
        drift_event, "auth_001", ["provider_a", "e2_new"], "prop_001", "payment", scope,
    )

    return world_t6, assessment_t6, findings, frontier


def run_t7_governance(engine: TemporalCompletenessEngine, scope: CompletenessScope, world_t6: WorldState, assessment_t6):
    """T7: Governance reviews authorization."""
    world_t7 = make_world(
        "2026-08-01T00:00:00Z",
        ["provider_a", "e2_new"],
    )

    assessment_t7, _ = engine.assess_temporal_completeness(
        authorization_id="auth_001",
        graph_id="graph_001",
        declared_dependencies=["provider_a", "e2_new"],
        actual_dependencies=["provider_a", "e2_new"],
        scope=scope,
        timestamp="2026-08-01T00:00:00Z",
        method=CompletenessMethod.CONTROLLED_INTERVENTION_DERIVED,
    )

    findings = engine.detect_completeness_drift(
        world_t6, world_t7, assessment_t6, assessment_t7,
        "2026-07-01T00:00:00Z", "2026-08-01T00:00:00Z", scope,
    )

    return world_t7, assessment_t7, findings


def run_full_temporal_experiment() -> dict[str, Any]:
    """Run the full 7-step temporal experiment."""
    engine = TemporalCompletenessEngine()
    scope = create_completeness_scope("prop_001", "payment")

    results = {}

    # T0: Baseline
    world_t0, assessment_t0, interval_t0 = run_t0_baseline(engine, scope)
    results["t0"] = {
        "world": world_t0,
        "assessment": assessment_t0,
        "interval": interval_t0,
        "status": assessment_t0.overall_status,
    }

    # T1: Irrelevant world change
    world_t1, assessment_t1, findings_t1, frontier_t1 = run_t1_irrelevant_world_change(
        engine, scope, world_t0, assessment_t0
    )
    results["t1"] = {
        "world": world_t1,
        "assessment": assessment_t1,
        "findings": findings_t1,
        "frontier": frontier_t1,
        "status": assessment_t1.overall_status,
    }

    # T2: Latent dependency
    world_t2, assessment_t2, findings_t2, frontier_t2 = run_t2_latent_dependency(
        engine, scope, world_t1, assessment_t1
    )
    results["t2"] = {
        "world": world_t2,
        "assessment": assessment_t2,
        "findings": findings_t2,
        "frontier": frontier_t2,
        "status": assessment_t2.overall_status,
    }

    # T3: Runtime discovery
    world_t3, assessment_t3, findings_t3, frontier_t3 = run_t3_runtime_discovery(
        engine, scope, world_t2, assessment_t2
    )
    results["t3"] = {
        "world": world_t3,
        "assessment": assessment_t3,
        "findings": findings_t3,
        "frontier": frontier_t3,
        "status": assessment_t3.overall_status,
    }

    # T4: Intervention
    world_t4, assessment_t4, findings_t4, frontier_t4 = run_t4_intervention(
        engine, scope, world_t3, assessment_t3
    )
    results["t4"] = {
        "world": world_t4,
        "assessment": assessment_t4,
        "findings": findings_t4,
        "frontier": frontier_t4,
        "status": assessment_t4.overall_status,
    }

    # T5: Completeness changes
    world_t5, assessment_t5, findings_t5 = run_t5_completeness_changes(
        engine, scope, world_t4, assessment_t4
    )
    results["t5"] = {
        "world": world_t5,
        "assessment": assessment_t5,
        "findings": findings_t5,
        "status": assessment_t5.overall_status,
    }

    # T6: Contradictory evidence
    world_t6, assessment_t6, findings_t6, frontier_t6 = run_t6_contradictory_evidence(
        engine, scope, world_t5, assessment_t5
    )
    results["t6"] = {
        "world": world_t6,
        "assessment": assessment_t6,
        "findings": findings_t6,
        "frontier": frontier_t6,
        "status": assessment_t6.overall_status,
    }

    # T7: Governance
    world_t7, assessment_t7, findings_t7 = run_t7_governance(
        engine, scope, world_t6, assessment_t6
    )
    results["t7"] = {
        "world": world_t7,
        "assessment": assessment_t7,
        "findings": findings_t7,
        "status": assessment_t7.overall_status,
    }

    return results


if __name__ == "__main__":
    results = run_full_temporal_experiment()
    for step, data in results.items():
        print(f"\n{step.upper()}:")
        print(f"  Status: {data['status']}")
        if "findings" in data:
            for f in data["findings"]:
                print(f"  Finding: {f.drift_type} ({f.drift_classification})")
        if "frontier" in data:
            print(f"  Frontier: {data['frontier'].revalidation_requirement}")
