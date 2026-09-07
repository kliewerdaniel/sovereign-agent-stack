"""Unit tests for the event log."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.provenance.graph import EventLog, ExperimentEvent


class TestEventLog:
    """Test the append-only event log."""

    def setup_method(self):
        self.log = EventLog(experiment_id="test-exp-001")

    def test_record_event(self):
        event = self.log.record(
            event_type="experiment.created",
            actor="system",
            metadata={"test": True},
        )
        assert event.event_id is not None
        assert event.experiment_id == "test-exp-001"
        assert event.event_type == "experiment.created"
        assert event.actor == "system"
        assert event.metadata["test"] is True

    def test_events_are_chronological(self):
        e1 = self.log.record(event_type="event.1")
        e2 = self.log.record(event_type="event.2")
        e3 = self.log.record(event_type="event.3")

        events = self.log.events
        assert len(events) == 3
        assert events[0].event_id == e1.event_id
        assert events[1].event_id == e2.event_id
        assert events[2].event_id == e3.event_id

    def test_parent_event_reference(self):
        e1 = self.log.record(event_type="parent")
        e2 = self.log.record(event_type="child")

        # e2 should reference e1 as parent
        assert e2.parent_event_id == e1.event_id

    def test_for_trial(self):
        self.log.record(event_type="trial.1", trial_id="t1")
        self.log.record(event_type="trial.2", trial_id="t2")
        self.log.record(event_type="trial.1.event", trial_id="t1")

        t1_events = self.log.for_trial("t1")
        assert len(t1_events) == 2
        assert all(e.trial_id == "t1" for e in t1_events)

    def test_of_type(self):
        self.log.record(event_type="experiment.created")
        self.log.record(event_type="trial.proposed")
        self.log.record(event_type="trial.proposed")

        proposed = self.log.of_type("trial.proposed")
        assert len(proposed) == 2

    def test_last_event(self):
        assert self.log.last_event() is None
        self.log.record(event_type="first")
        e2 = self.log.record(event_type="second")
        assert self.log.last_event().event_id == e2.event_id

    def test_to_dict(self):
        self.log.record(event_type="test")
        d = self.log.to_dict()
        assert d["experiment_id"] == "test-exp-001"
        assert d["event_count"] == 1
        assert len(d["events"]) == 1
