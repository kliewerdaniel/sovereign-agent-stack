"""Append-only event log for experiment provenance.

Every state transition in a governed research experiment is recorded here.
The event log is the authoritative chronological record — the provenance
graph tells you WHAT happened; the event log tells you WHEN and in what
order.

Invariants:
- Events are append-only. Once written, an event is immutable.
- Each event has a unique id, timestamp, and parent event reference.
- The event log can reconstruct the complete chronological trajectory.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional


@dataclass(frozen=True)
class ExperimentEvent:
    """A single immutable event in an experiment's history."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    experiment_id: str = ""
    trial_id: str | None = None
    event_type: str = ""  # e.g. "experiment.created", "trial.proposed", "tool.invoked"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    actor: str = ""  # agent name, "system", "researcher", etc.
    artifact_refs: list[str] = field(default_factory=list)  # artifact ids referenced
    parent_event_id: str | None = None
    metadata: dict = field(default_factory=dict)  # execution metadata

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "experiment_id": self.experiment_id,
            "trial_id": self.trial_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "artifact_refs": list(self.artifact_refs),
            "parent_event_id": self.parent_event_id,
            "metadata": dict(self.metadata),
        }


class EventLog:
    """Append-only event log for a governed experiment.

    Records every state transition: experiment.created, trial.proposed,
    tool.invoked, backtest.completed, critique.created, trial.revised,
    research.terminated, statistics.computed, holdout.opened, etc.
    """

    def __init__(self, experiment_id: str = ""):
        self.experiment_id = experiment_id
        self._events: list[ExperimentEvent] = []
        self._last_event_id: str | None = None

    def record(
        self,
        event_type: str,
        trial_id: str | None = None,
        actor: str = "system",
        artifact_refs: list[str] | None = None,
        metadata: dict | None = None,
        parent_event_id: str | None = None,
    ) -> ExperimentEvent:
        """Record an event. Append-only — events cannot be modified once written."""
        event = ExperimentEvent(
            experiment_id=self.experiment_id,
            trial_id=trial_id,
            event_type=event_type,
            actor=actor,
            artifact_refs=artifact_refs or [],
            parent_event_id=parent_event_id or self._last_event_id,
            metadata=metadata or {},
        )
        self._events.append(event)
        self._last_event_id = event.event_id
        return event

    @property
    def events(self) -> list[ExperimentEvent]:
        """Return all events in chronological order."""
        return list(self._events)

    def for_trial(self, trial_id: str) -> list[ExperimentEvent]:
        """Return all events for a specific trial."""
        return [e for e in self._events if e.trial_id == trial_id]

    def of_type(self, event_type: str) -> list[ExperimentEvent]:
        """Return all events of a specific type."""
        return [e for e in self._events if e.event_type == event_type]

    def last_event(self) -> ExperimentEvent | None:
        """Return the most recent event."""
        return self._events[-1] if self._events else None

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "event_count": len(self._events),
            "events": [e.to_dict() for e in self._events],
        }
