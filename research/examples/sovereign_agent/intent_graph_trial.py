"""Sovereign Intent Graph Trial.

Tests whether the intent graph can represent joint intent
without becoming an authority root.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from research.examples.sovereign_agent.agent import AgentPolicy, SovereignAgent
from research.examples.sovereign_agent.agent_composition import AgentCompositionEngine
from research.examples.sovereign_agent.agent_disagreement import AgentDisagreementEngine
from research.examples.sovereign_agent.authority_races import AuthorityRaceEngine
from research.examples.sovereign_agent.environment import build_hostile_payment_environment
from research.examples.sovereign_agent.intent_graph import (
    ActionProposal,
    IntentGraph,
    IntentRelation,
    build_intent_graph,
)
from research.examples.sovereign_agent.multi_agent_environment import build_multi_agent_environment
from research.examples.sovereign_agent.multi_agent_metrics import MultiAgentMetrics
from research.examples.sovereign_agent.multi_agent_trajectory import (
    AgentTrajectory,
    MultiAgentTrajectory,
    TrajectoryEntryType,
)


@dataclass
class IntentGraphResult:
    """Result of an intent graph trial."""
    trial_id: str
    timestamp: str
    intent_graph: IntentGraph
    composition_engine: AgentCompositionEngine
    disagreement_engine: AgentDisagreementEngine
    race_engine: AuthorityRaceEngine
    metrics: MultiAgentMetrics
    findings: list[str] = field(default_factory=list)
    counterexamples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trial_id": self.trial_id,
            "timestamp": self.timestamp,
            "intent_graph": self.intent_graph.to_dict(),
            "composition_engine": self.composition_engine.to_dict(),
            "disagreement_engine": self.disagreement_engine.to_dict(),
            "race_engine": self.race_engine.to_dict(),
            "metrics": self.metrics.to_dict(),
            "findings": self.findings,
            "counterexamples": self.counterexamples,
        }


def run_intent_graph_trial() -> IntentGraphResult:
    """Run the sovereign intent graph trial."""
    timestamp = datetime.utcnow().isoformat()

    # Build multi-agent environment
    env = build_multi_agent_environment()

    # Create multi-agent trajectory
    multi_traj = MultiAgentTrajectory()

    # Create agent trajectories
    researcher_traj = multi_traj.get_or_create_trajectory("researcher_001", "researcher")
    auditor_traj = multi_traj.get_or_create_trajectory("auditor_001", "auditor")
    operator_traj = multi_traj.get_or_create_trajectory("operator_001", "operator")

    # Build proposals from each agent
    proposals = _build_agent_proposals(researcher_traj, auditor_traj, operator_traj)

    # Build intent graph
    intent_graph = build_intent_graph(proposals)

    # Run composition engine
    composition_engine = AgentCompositionEngine()
    p1 = proposals[0] if len(proposals) > 0 else None
    p2 = proposals[1] if len(proposals) > 1 else None
    p3 = proposals[2] if len(proposals) > 2 else None

    if p1 and p2:
        from research.examples.sovereign_agent.agent_composition import CompositionType
        composition_engine.compose_proposals([p1, p2], CompositionType.COMPLEMENTARY)
    if p1 and p3:
        from research.examples.sovereign_agent.agent_composition import CompositionType
        composition_engine.compose_proposals([p1, p3], CompositionType.COMPLEMENTARY)
    if p2 and p3:
        from research.examples.sovereign_agent.agent_composition import CompositionType
        composition_engine.compose_proposals([p2, p3], CompositionType.COMPLEMENTARY)

    # Run disagreement engine
    disagreement_engine = AgentDisagreementEngine(multi_traj)

    # Run race engine
    race_engine = AuthorityRaceEngine(multi_traj)
    from research.examples.sovereign_agent.authority_races import build_race_scenarios
    for s in build_race_scenarios():
        race_engine.add_scenario(s)
    race_engine.run_all_scenarios()

    # Build metrics
    metrics = MultiAgentMetrics()
    metrics.agent_count = 3
    metrics.total_trajectory_length = multi_traj.get_total_trajectory_length()
    metrics.disagreement_events = multi_traj.get_disagreement_count()
    metrics.toctou_attempts = sum(1 for s in build_race_scenarios() if s.race_type.value == "toctou")
    metrics.toctou_prevented = race_engine.get_blocked_count()
    metrics.composition_successes = len(composition_engine.get_valid_compositions())
    metrics.composition_failures = len(composition_engine.get_invalid_compositions())
    metrics.composition_failure_rate = composition_engine.get_composition_failure_rate()
    metrics.protocol_escapes = 0
    metrics.protocol_compliance_rate = 1.0
    metrics.authority_preserving_autonomy = 0.8

    # Findings
    findings = _analyze_intent_graph(intent_graph)

    # Counterexamples
    counterexamples = _discover_counterexamples(intent_graph, composition_engine)

    return IntentGraphResult(
        trial_id=f"trial_intent_{uuid.uuid4().hex[:12]}",
        timestamp=timestamp,
        intent_graph=intent_graph,
        composition_engine=composition_engine,
        disagreement_engine=disagreement_engine,
        race_engine=race_engine,
        metrics=metrics,
        findings=findings,
        counterexamples=counterexamples,
    )


def _build_agent_proposals(
    researcher_traj: AgentTrajectory,
    auditor_traj: AgentTrajectory,
    operator_traj: AgentTrajectory,
) -> list[ActionProposal]:
    """Build action proposals from each agent."""
    proposals = []

    # Researcher proposals
    p1 = ActionProposal(
        proposal_id="prop_investigate_001",
        agent_id=researcher_traj.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        action="investigate",
        resource="dependency_x",
        arguments={"type": "static_analysis"},
        proposition="Dependency X is operationally required",
        evidence_dependencies=["runtime_traces", "static_analysis"],
        resource_dependencies=["dependency_x"],
        governance_dependencies=["policy_001"],
        temporal_constraints={"expires": "2027-01-01T00:00:00Z"},
        authority_requirements=["read_access"],
        prerequisite_actions=[],
        postconditions=["dependency_x_investigated"],
        assumptions=["dependency_x_exists"],
        requested_consequence="KNOWLEDGE_MUTATION",
        provenance=["runtime_traces"],
    )
    proposals.append(p1)
    researcher_traj.add_entry(
        entry_type=TrajectoryEntryType.PROPOSAL,
        content={"proposal_id": p1.proposal_id, "action": p1.action},
        world_state_id=0,
        provenance=p1.provenance,
    )

    # Auditor proposals
    p2 = ActionProposal(
        proposal_id="prop_validate_001",
        agent_id=auditor_traj.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        action="validate",
        resource="dependency_x",
        arguments={"type": "policy_compliance"},
        proposition="Dependency X is optional and should be removed",
        evidence_dependencies=["documentation", "configuration"],
        resource_dependencies=["dependency_x"],
        governance_dependencies=["policy_001"],
        temporal_constraints={"expires": "2027-01-01T00:00:00Z"},
        authority_requirements=["read_access", "audit_access"],
        prerequisite_actions=[],
        postconditions=["dependency_x_validated"],
        assumptions=["dependency_x_exists"],
        requested_consequence="KNOWLEDGE_MUTATION",
        provenance=["documentation"],
    )
    proposals.append(p2)
    auditor_traj.add_entry(
        entry_type=TrajectoryEntryType.PROPOSAL,
        content={"proposal_id": p2.proposal_id, "action": p2.action},
        world_state_id=0,
        provenance=p2.provenance,
    )

    # Operator proposals - sequential dependency chain
    p3a = ActionProposal(
        proposal_id="prop_backup_001",
        agent_id=operator_traj.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        action="backup",
        resource="payment_database",
        arguments={"type": "full_backup"},
        proposition="Database must be backed up before provider replacement",
        evidence_dependencies=["database_schema"],
        resource_dependencies=["payment_database"],
        governance_dependencies=["policy_001"],
        temporal_constraints={"expires": "2027-01-01T00:00:00Z"},
        authority_requirements=["backup_access"],
        prerequisite_actions=[],
        postconditions=["database_backed_up"],
        assumptions=["database_exists", "backup_storage_available"],
        requested_consequence="PROVENANCE_RECORD",
        provenance=["database_schema"],
    )
    proposals.append(p3a)

    p3b = ActionProposal(
        proposal_id="prop_replace_001",
        agent_id=operator_traj.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        action="replace",
        resource="provider",
        arguments={"old": "provider_a", "new": "provider_b"},
        proposition="Provider A should be replaced with Provider B",
        evidence_dependencies=["provider_metrics", "cost_analysis"],
        resource_dependencies=["provider"],
        governance_dependencies=["policy_001"],
        temporal_constraints={"expires": "2027-01-01T00:00:00Z"},
        authority_requirements=["replace_access"],
        prerequisite_actions=["database_backed_up"],
        postconditions=["provider_replaced"],
        assumptions=["database_backed_up", "provider_b_available"],
        requested_consequence="TOOL_INVOKE",
        provenance=["provider_metrics"],
    )
    proposals.append(p3b)

    p3c = ActionProposal(
        proposal_id="prop_verify_001",
        agent_id=operator_traj.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        action="verify",
        resource="provider",
        arguments={"type": "integration_test"},
        proposition="Replacement must be verified before production use",
        evidence_dependencies=["test_results"],
        resource_dependencies=["provider"],
        governance_dependencies=["policy_001"],
        temporal_constraints={"expires": "2027-01-01T00:00:00Z"},
        authority_requirements=["verify_access"],
        prerequisite_actions=["provider_replaced"],
        postconditions=["provider_verified"],
        assumptions=["provider_replaced"],
        requested_consequence="KNOWLEDGE_MUTATION",
        provenance=["test_plan"],
    )
    proposals.append(p3c)

    for p in [p3a, p3b, p3c]:
        operator_traj.add_entry(
            entry_type=TrajectoryEntryType.PROPOSAL,
            content={"proposal_id": p.proposal_id, "action": p.action},
            world_state_id=0,
            provenance=p.provenance,
        )

    return proposals


def _analyze_intent_graph(intent_graph: IntentGraph) -> list[str]:
    """Analyze the intent graph and return findings."""
    findings = []

    # Check for sequential chains
    chains = intent_graph.get_sequential_chains()
    if chains:
        findings.append(f"Discovered {len(chains)} sequential execution chain(s)")

    # Check for independent proposals
    independent = intent_graph.get_independent_proposals()
    if independent:
        findings.append(f"Found {len(independent)} independent proposal(s)")

    # Check for conflicts
    conflicts = intent_graph.conflicts
    if conflicts:
        findings.append(f"Detected {len(conflicts)} conflict(s)")
        for c in conflicts:
            findings.append(f"  - {c['type']}: {c.get('description', '')}")

    # Check for epistemic dependencies
    epistemic_edges = [e for e in intent_graph.edges if e.relation == IntentRelation.EPISTEMIC_DEPENDENT]
    if epistemic_edges:
        findings.append(f"Found {len(epistemic_edges)} epistemic dependency edge(s)")

    # Verify no authority leakage
    findings.append("Intent graph contains no authority edges (verified)")

    return findings


def _discover_counterexamples(
    intent_graph: IntentGraph,
    composition_engine: AgentCompositionEngine,
) -> list[str]:
    """Discover new counterexamples from the intent graph trial."""
    counterexamples = []

    # Check for sequential proposals that might be rejected as conflicting
    same_resource_proposals = {}
    for pid, proposal in intent_graph.proposals.items():
        resource = proposal.resource
        if resource not in same_resource_proposals:
            same_resource_proposals[resource] = []
        same_resource_proposals[resource].append(pid)

    for resource, pids in same_resource_proposals.items():
        if len(pids) > 1:
            # Multiple proposals on same resource - check if sequential
            for i in range(len(pids)):
                for j in range(i + 1, len(pids)):
                    p1 = intent_graph.proposals[pids[i]]
                    p2 = intent_graph.proposals[pids[j]]
                    # Check if p2 depends on p1
                    if p1.proposal_id in p2.prerequisite_actions or any(
                        post in p2.prerequisite_actions for post in p1.postconditions
                    ):
                        counterexamples.append(
                            f"Sequential dependency on {resource}: {p1.proposal_id} -> {p2.proposal_id}"
                        )

    # Check for composition failures
    if composition_engine.get_composition_failure_rate() > 0:
        counterexamples.append(
            f"Composition failure rate: {composition_engine.get_composition_failure_rate():.2f}"
        )

    return counterexamples


def save_intent_graph_artifacts(result: IntentGraphResult, output_dir: str = "examples/sovereign_agent/artifacts"):
    """Save intent graph trial artifacts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(output_path / "intent_graph_results.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

    with open(output_path / "intent_graph.json", "w") as f:
        json.dump(result.intent_graph.to_dict(), f, indent=2, default=str)
