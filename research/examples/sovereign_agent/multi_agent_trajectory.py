"""Multi-Agent Trajectory for Sovereign Authority Competition.

Each agent has its own independent epistemic trajectory.
Shared world state is separate from agent-specific belief state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TrajectoryEntryType(str, Enum):
    """Types of trajectory entries."""
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    EVIDENCE_REQUEST = "evidence_request"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    PROPOSITION = "proposition"
    PROPOSAL = "proposal"
    DISAGREEMENT = "disagreement"
    CHALLENGE = "challenge"
    AUTHORIZATION_REQUEST = "authorization_request"
    AUTHORIZATION_GRANTED = "authorization_granted"
    AUTHORIZATION_DENIED = "authorization_denied"
    EXECUTION_REQUEST = "execution_request"
    EXECUTION_SUCCESS = "execution_success"
    EXECUTION_FAILURE = "execution_failure"
    REVOCATION = "revocation"
    RECOVERY = "recovery"
    EPISTEMIC_UPDATE = "epistemic_update"
    AUTHORITY_CHALLENGE = "authority_challenge"
    COMPOSITION_PROPOSAL = "composition_proposal"
    TOCTOU_CHECK = "toctou_check"


@dataclass(frozen=True)
class TrajectoryEntry:
    """A single entry in an agent's trajectory."""
    entry_id: str
    timestamp: str
    entry_type: TrajectoryEntryType
    content: Any
    agent_id: str
    world_state_id: int
    provenance: list[str] = field(default_factory=list)
    authority_basis: Optional[str] = None
    authorization_ref: Optional[str] = None
    capability_ref: Optional[str] = None
    parent_entry_id: Optional[str] = None


@dataclass
class DisagreementEvent:
    """Records a disagreement between two agents."""
    disagreement_id: str
    timestamp: str
    agent_a_id: str
    agent_b_id: str
    proposition: str
    agent_a_position: str
    agent_b_position: str
    evidence_overlap: list[str] = field(default_factory=list)
    evidence_independent: list[str] = field(default_factory=list)
    resolution: Optional[str] = None
    resolution_mechanism: Optional[str] = None


@dataclass(frozen=True)
class AuthorityRaceEvent:
    """Records a race condition in authority."""
    race_id: str
    timestamp: str
    agent_id: str
    race_type: str
    description: str
    time_of_check: Optional[str] = None
    time_of_use: Optional[str] = None
    outcome: str = "unknown"
    protocol_response: Optional[str] = None


@dataclass
class AgentTrajectory:
    """Independent epistemic trajectory for a single agent."""
    agent_id: str
    agent_role: str
    entries: list[TrajectoryEntry] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    evidence_analyzed: list[str] = field(default_factory=list)
    propositions: list[dict[str, Any]] = field(default_factory=list)
    disagreements_initiated: list[str] = field(default_factory=list)
    disagreements_received: list[str] = field(default_factory=list)

    def add_entry(
        self,
        entry_type: TrajectoryEntryType,
        content: Any,
        world_state_id: int,
        provenance: list[str] | None = None,
        authority_basis: str | None = None,
        authorization_ref: str | None = None,
        capability_ref: str | None = None,
        parent_entry_id: str | None = None,
    ) -> TrajectoryEntry:
        """Add an entry to this agent's trajectory."""
        entry = TrajectoryEntry(
            entry_id=f"entry_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            entry_type=entry_type,
            content=content,
            agent_id=self.agent_id,
            world_state_id=world_state_id,
            provenance=provenance or [],
            authority_basis=authority_basis,
            authorization_ref=authorization_ref,
            capability_ref=capability_ref,
            parent_entry_id=parent_entry_id,
        )
        self.entries.append(entry)
        return entry

    def get_entries_by_type(self, entry_type: TrajectoryEntryType) -> list[TrajectoryEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.entry_type == entry_type]

    def get_entries_by_world_state(self, world_state_id: int) -> list[TrajectoryEntry]:
        """Get all entries at a specific world state."""
        return [e for e in self.entries if e.world_state_id == world_state_id]

    def get_disagreements(self) -> list[TrajectoryEntry]:
        """Get all disagreement entries."""
        return [e for e in self.entries if e.entry_type == TrajectoryEntryType.DISAGREEMENT]

    def get_authorizations(self) -> list[TrajectoryEntry]:
        """Get all authorization-related entries."""
        return [e for e in self.entries if e.entry_type in (
            TrajectoryEntryType.AUTHORIZATION_REQUEST,
            TrajectoryEntryType.AUTHORIZATION_GRANTED,
            TrajectoryEntryType.AUTHORIZATION_DENIED,
        )]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_role": self.agent_role,
            "trajectory_length": len(self.entries),
            "hypotheses_count": len(self.hypotheses),
            "evidence_analyzed_count": len(self.evidence_analyzed),
            "propositions_count": len(self.propositions),
            "disagreements_initiated": len(self.disagreements_initiated),
            "disagreements_received": len(self.disagreements_received),
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "timestamp": e.timestamp,
                    "entry_type": e.entry_type.value,
                    "content": e.content,
                    "world_state_id": e.world_state_id,
                    "provenance": e.provenance,
                    "authority_basis": e.authority_basis,
                    "authorization_ref": e.authorization_ref,
                    "capability_ref": e.capability_ref,
                    "parent_entry_id": e.parent_entry_id,
                }
                for e in self.entries
            ],
        }


@dataclass
class MultiAgentTrajectory:
    """Collection of all agent trajectories in the multi-agent experiment."""
    trajectories: dict[str, AgentTrajectory] = field(default_factory=dict)
    disagreement_events: list[DisagreementEvent] = field(default_factory=list)
    authority_race_events: list[AuthorityRaceEvent] = field(default_factory=list)

    def get_or_create_trajectory(self, agent_id: str, agent_role: str) -> AgentTrajectory:
        """Get or create an agent trajectory."""
        if agent_id not in self.trajectories:
            self.trajectories[agent_id] = AgentTrajectory(
                agent_id=agent_id,
                agent_role=agent_role,
            )
        return self.trajectories[agent_id]

    def record_disagreement(
        self,
        agent_a_id: str,
        agent_b_id: str,
        proposition: str,
        agent_a_position: str,
        agent_b_position: str,
        evidence_overlap: list[str] | None = None,
        evidence_independent: list[str] | None = None,
    ) -> DisagreementEvent:
        """Record a disagreement between two agents."""
        event = DisagreementEvent(
            disagreement_id=f"disagreement_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            agent_a_id=agent_a_id,
            agent_b_id=agent_b_id,
            proposition=proposition,
            agent_a_position=agent_a_position,
            agent_b_position=agent_b_position,
            evidence_overlap=evidence_overlap or [],
            evidence_independent=evidence_independent or [],
        )
        self.disagreement_events.append(event)
        return event

    def record_authority_race(
        self,
        agent_id: str,
        race_type: str,
        description: str,
        time_of_check: str | None = None,
        time_of_use: str | None = None,
        outcome: str = "unknown",
        protocol_response: str | None = None,
    ) -> AuthorityRaceEvent:
        """Record an authority race condition."""
        event = AuthorityRaceEvent(
            race_id=f"race_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            race_type=race_type,
            description=description,
            time_of_check=time_of_check,
            time_of_use=time_of_use,
            outcome=outcome,
            protocol_response=protocol_response,
        )
        self.authority_race_events.append(event)
        return event

    def get_total_trajectory_length(self) -> int:
        """Get total trajectory length across all agents."""
        return sum(len(t.entries) for t in self.trajectories.values())

    def get_disagreement_count(self) -> int:
        """Get total number of disagreements."""
        return len(self.disagreement_events)

    def get_agreement_count(self) -> int:
        """Get total number of agreements (resolved disagreements)."""
        return sum(1 for d in self.disagreement_events if d.resolution is not None)

    def get_unresolved_disagreement_count(self) -> int:
        """Get number of unresolved disagreements."""
        return sum(1 for d in self.disagreement_events if d.resolution is None)

    def get_evidence_independence_rate(self) -> float:
        """Get rate of independent evidence."""
        total = len(self.disagreement_events)
        if total == 0:
            return 1.0
        independent = sum(1 for d in self.disagreement_events if d.evidence_independent)
        return independent / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_count": len(self.trajectories),
            "total_trajectory_length": self.get_total_trajectory_length(),
            "disagreement_count": self.get_disagreement_count(),
            "agreement_count": self.get_agreement_count(),
            "unresolved_disagreements": self.get_unresolved_disagreement_count(),
            "evidence_independence_rate": self.get_evidence_independence_rate(),
            "authority_race_count": len(self.authority_race_events),
            "trajectories": {aid: t.to_dict() for aid, t in self.trajectories.items()},
            "disagreement_events": [
                {
                    "disagreement_id": d.disagreement_id,
                    "timestamp": d.timestamp,
                    "agent_a_id": d.agent_a_id,
                    "agent_b_id": d.agent_b_id,
                    "proposition": d.proposition,
                    "agent_a_position": d.agent_a_position,
                    "agent_b_position": d.agent_b_position,
                    "evidence_overlap": d.evidence_overlap,
                    "evidence_independent": d.evidence_independent,
                    "resolution": d.resolution,
                    "resolution_mechanism": d.resolution_mechanism,
                }
                for d in self.disagreement_events
            ],
            "authority_race_events": [
                {
                    "race_id": r.race_id,
                    "timestamp": r.timestamp,
                    "agent_id": r.agent_id,
                    "race_type": r.race_type,
                    "description": r.description,
                    "time_of_check": r.time_of_check,
                    "time_of_use": r.time_of_use,
                    "outcome": r.outcome,
                    "protocol_response": r.protocol_response,
                }
                for r in self.authority_race_events
            ],
        }
