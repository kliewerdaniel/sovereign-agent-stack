"""Long-horizon trial trajectory recording and reconstruction."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TrajectoryEntryType(str, Enum):
    """Types of trajectory entries."""
    MODEL_OUTPUT = "model_output"
    AGENT_REQUEST = "agent_request"
    PROTOCOL_DECISION = "protocol_decision"
    EVIDENCE = "evidence"
    EPISTEMIC_STATE = "epistemic_state"
    GOVERNANCE = "governance"
    AUTHORIZATION = "authorization"
    CAPABILITY = "capability"
    EXECUTION = "execution"
    RECEIPT = "receipt"
    PROVENANCE = "provenance"
    WORLD_STATE_CHANGE = "world_state_change"
    AGENT_STATE_UPDATE = "agent_state_update"
    CONTRADICTION = "contradiction"
    RECOVERY = "recovery"


@dataclass(frozen=True)
class TrajectoryEntry:
    """A single entry in the agent's trajectory."""
    entry_id: str
    timestamp: str
    step_index: int
    entry_type: str
    content: Any
    agent_id: str
    world_time: str
    authority_basis: Optional[str] = None
    authorization_ref: Optional[str] = None
    capability_ref: Optional[str] = None
    provenance: list[str] = field(default_factory=list)
    parent_entry_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorldStateTransition:
    """A transition in the world state."""
    transition_id: str
    from_time: str
    to_time: str
    description: str
    changes: dict[str, Any]
    previous_state_hash: str
    new_state_hash: str


@dataclass(frozen=True)
class ContradictionEvent:
    """A contradiction discovered during the trial."""
    contradiction_id: str
    timestamp: str
    description: str
    previous_belief: Any
    contradicting_evidence: Any
    resolution: Optional[str] = None
    recovery_action: Optional[str] = None


@dataclass(frozen=True)
class RecoveryEvent:
    """A recovery action after a contradiction."""
    recovery_id: str
    timestamp: str
    contradiction_id: str
    recovery_type: str
    description: str
    successful: bool


@dataclass
class AgentTrajectory:
    """Complete trajectory of an agent run."""
    trajectory_id: str
    agent_id: str
    objective_id: str
    start_time: str
    end_time: Optional[str] = None
    entries: list[TrajectoryEntry] = field(default_factory=list)
    world_transitions: list[WorldStateTransition] = field(default_factory=list)
    contradictions: list[ContradictionEvent] = field(default_factory=list)
    recoveries: list[RecoveryEvent] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    final_state: Optional[str] = None

    def add_entry(
        self,
        entry_type: str,
        content: Any,
        agent_id: str,
        world_time: str,
        authority_basis: Optional[str] = None,
        authorization_ref: Optional[str] = None,
        capability_ref: Optional[str] = None,
        parent_entry_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TrajectoryEntry:
        """Add an entry to the trajectory."""
        entry = TrajectoryEntry(
            entry_id=f"entry_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            step_index=len(self.entries),
            entry_type=entry_type,
            content=content,
            agent_id=agent_id,
            world_time=world_time,
            authority_basis=authority_basis,
            authorization_ref=authorization_ref,
            capability_ref=capability_ref,
            parent_entry_id=parent_entry_id,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        return entry

    def add_world_transition(
        self,
        from_time: str,
        to_time: str,
        description: str,
        changes: dict[str, Any],
        previous_state_hash: str,
        new_state_hash: str,
    ) -> WorldStateTransition:
        """Add a world state transition."""
        transition = WorldStateTransition(
            transition_id=f"wt_{uuid.uuid4().hex[:12]}",
            from_time=from_time,
            to_time=to_time,
            description=description,
            changes=changes,
            previous_state_hash=previous_state_hash,
            new_state_hash=new_state_hash,
        )
        self.world_transitions.append(transition)
        return transition

    def add_contradiction(
        self,
        description: str,
        previous_belief: Any,
        contradicting_evidence: Any,
    ) -> ContradictionEvent:
        """Add a contradiction event."""
        contradiction = ContradictionEvent(
            contradiction_id=f"cont_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            description=description,
            previous_belief=previous_belief,
            contradicting_evidence=contradicting_evidence,
        )
        self.contradictions.append(contradiction)
        return contradiction

    def add_recovery(
        self,
        contradiction_id: str,
        recovery_type: str,
        description: str,
        successful: bool,
    ) -> RecoveryEvent:
        """Add a recovery event."""
        recovery = RecoveryEvent(
            recovery_id=f"rec_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            contradiction_id=contradiction_id,
            recovery_type=recovery_type,
            description=description,
            successful=successful,
        )
        self.recoveries.append(recovery)
        return recovery

    def get_entries_by_type(self, entry_type: str) -> list[TrajectoryEntry]:
        """Get all entries of a given type."""
        return [e for e in self.entries if e.entry_type == entry_type]

    def get_entries_by_world_time(self, world_time: str) -> list[TrajectoryEntry]:
        """Get all entries at a given world time."""
        return [e for e in self.entries if e.world_time == world_time]

    def get_contradiction_recovery_rate(self) -> float:
        """Calculate contradiction recovery rate."""
        if not self.contradictions:
            return 1.0
        recovered = sum(1 for c in self.contradictions if c.resolution is not None)
        return recovered / len(self.contradictions)

    def get_authority_drift_recovery_rate(self) -> float:
        """Calculate authority drift recovery rate."""
        drift_entries = [e for e in self.entries if e.entry_type == "world_state_change" and e.metadata.get("drift_type") == "authority"]
        if not drift_entries:
            return 1.0
        recovered = sum(1 for e in drift_entries if e.metadata.get("recovered", False))
        return recovered / len(drift_entries)

    def reconstruct_at_time(self, world_time: str) -> dict[str, Any]:
        """Reconstruct the agent's state at a given world time."""
        entries = self.get_entries_by_world_time(world_time)
        return {
            "world_time": world_time,
            "entries": [self._entry_to_dict(e) for e in entries],
            "total_entries": len(entries),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert trajectory to dictionary."""
        return {
            "trajectory_id": self.trajectory_id,
            "agent_id": self.agent_id,
            "objective_id": self.objective_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_entries": len(self.entries),
            "total_world_transitions": len(self.world_transitions),
            "total_contradictions": len(self.contradictions),
            "total_recoveries": len(self.recoveries),
            "contradiction_recovery_rate": self.get_contradiction_recovery_rate(),
            "authority_drift_recovery_rate": self.get_authority_drift_recovery_rate(),
            "final_state": self.final_state,
            "metrics": self.metrics,
        }

    def _entry_to_dict(self, entry: TrajectoryEntry) -> dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "entry_id": entry.entry_id,
            "step_index": entry.step_index,
            "entry_type": entry.entry_type,
            "world_time": entry.world_time,
            "authority_basis": entry.authority_basis,
            "authorization_ref": entry.authorization_ref,
        }
