"""Tests for runtime trace infrastructure."""

import json
import os
import tempfile
import threading
import time

import pytest

from examples.self_audit.runtime_trace import (
    AuthorizationInstrument,
    BrokerInstrument,
    CapabilityInstrument,
    ConsequenceType,
    FilesystemInstrument,
    InstrumentationSuite,
    ProvenanceInstrument,
    RuntimeTraceRecorder,
    SubprocessInstrument,
    TraceEvent,
    TraceEventType,
)


class TestRuntimeTraceRecorder:
    """Tests for the core trace recorder."""

    def test_start_stop(self):
        recorder = RuntimeTraceRecorder("test_exp")
        assert not recorder.is_active
        recorder.start()
        assert recorder.is_active
        recorder.stop()
        assert not recorder.is_active

    def test_record_event(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        event = recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="test",
            component="test_comp",
            operation="test_op",
            resource="test_res",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        assert event is not None
        assert event.event_id.startswith("evt_")
        assert event.actor == "test"
        assert event.event_type == TraceEventType.SUBPROCESS_CREATE
        recorder.stop()

    def test_record_when_inactive(self):
        recorder = RuntimeTraceRecorder("test_exp")
        event = recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="test",
            component="test_comp",
            operation="test_op",
            resource="test_res",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        assert event is None

    def test_parent_stack(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()

        parent = recorder.record(
            event_type=TraceEventType.CONSEQUENCE_ENTER,
            actor="parent",
            component="parent_comp",
            operation="parent_op",
            resource="parent_res",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
        )
        assert parent is not None
        recorder.push_call(parent.event_id)

        child = recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="child",
            component="child_comp",
            operation="child_op",
            resource="child_res",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )

        assert child is not None
        assert child.parent_event == parent.event_id
        assert child.call_path == [parent.event_id]

        recorder.pop_call()
        recorder.stop()

    def test_get_events_by_type(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()

        recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="a",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        recorder.record(
            event_type=TraceEventType.NETWORK_REQUEST,
            actor="a",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )

        assert len(recorder.get_events_by_type(TraceEventType.SUBPROCESS_CREATE)) == 1
        assert len(recorder.get_events_by_type(TraceEventType.NETWORK_REQUEST)) == 1
        recorder.stop()

    def test_get_events_by_actor(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()

        recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="actor_a",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="actor_b",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )

        assert len(recorder.get_events_by_actor("actor_a")) == 1
        assert len(recorder.get_events_by_actor("actor_b")) == 1
        recorder.stop()

    def test_get_events_by_consequence(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()

        recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="a",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
        )
        recorder.record(
            event_type=TraceEventType.FILESYSTEM_WRITE,
            actor="a",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.STATE_TRANSFORMING,
        )

        assert len(recorder.get_events_by_consequence(ConsequenceType.EXTERNAL_CONSEQUENTIAL)) == 1
        assert len(recorder.get_events_by_consequence(ConsequenceType.STATE_TRANSFORMING)) == 1
        recorder.stop()

    def test_to_dict(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="a",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        recorder.stop()

        d = recorder.to_dict()
        assert d["experiment_id"] == "test_exp"
        assert d["total_events"] == 1
        assert len(d["events"]) == 1

    def test_thread_safety(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()

        def record_events():
            for _ in range(10):
                recorder.record(
                    event_type=TraceEventType.SUBPROCESS_CREATE,
                    actor="thread",
                    component="c",
                    operation="o",
                    resource="r",
                    consequence_type=ConsequenceType.INFORMATIONAL,
                )

        threads = [threading.Thread(target=record_events) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(recorder.events) == 50
        recorder.stop()


class TestSubprocessInstrument:
    """Tests for subprocess instrumentation."""

    def test_run_records_events(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = SubprocessInstrument(recorder)

        result = instrument.run(
            cmd=["echo", "hello"],
            actor="test",
            component="test_comp",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )

        assert result["ok"]
        assert len(recorder.get_subprocess_events()) == 2
        recorder.stop()

    def test_run_with_capability(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = SubprocessInstrument(recorder)

        result = instrument.run(
            cmd=["echo", "hello"],
            actor="test",
            component="test_comp",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            capability_id="cap_123",
            authorization_id="auth_456",
            provenance_id="prov_789",
        )

        assert result["ok"]
        events = recorder.get_subprocess_events()
        assert events[0].capability_id == "cap_123"
        assert events[0].authorization_id == "auth_456"
        assert events[0].provenance_id == "prov_789"
        recorder.stop()

    def test_run_with_error(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = SubprocessInstrument(recorder)

        result = instrument.run(
            cmd=["nonexistent_command_that_does_not_exist"],
            actor="test",
            component="test_comp",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )

        assert not result["ok"]
        assert len(recorder.get_subprocess_events()) == 2
        recorder.stop()


class TestFilesystemInstrument:
    """Tests for filesystem instrumentation."""

    def test_write_records_events(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = FilesystemInstrument(recorder)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name

        try:
            result = instrument.write(
                path=path,
                content="test content",
                actor="test",
                component="test_comp",
                consequence_type=ConsequenceType.STATE_TRANSFORMING,
            )

            assert result["ok"]
            assert len(recorder.get_filesystem_events()) >= 1
        finally:
            os.unlink(path)
        recorder.stop()

    def test_read_records_events(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = FilesystemInstrument(recorder)

        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("test content")
            path = f.name

        try:
            result = instrument.read(
                path=path,
                actor="test",
                component="test_comp",
                consequence_type=ConsequenceType.INFORMATIONAL,
            )

            assert result["ok"]
            assert result["content"] == "test content"
        finally:
            os.unlink(path)
        recorder.stop()


class TestBrokerInstrument:
    """Tests for broker instrumentation."""

    def test_submit_trade_records_events(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = BrokerInstrument(recorder)

        class FakeTrade:
            symbol = "AAPL"

        result = instrument.submit_trade(
            trade=FakeTrade(),
            actor="test",
            component="test_comp",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            capability_id="cap_123",
            authorization_id="auth_456",
        )

        assert result["ok"]
        assert len(recorder.get_broker_events()) >= 1
        recorder.stop()


class TestCapabilityInstrument:
    """Tests for capability instrumentation."""

    def test_verify_records_event(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = CapabilityInstrument(recorder)

        result = instrument.verify(
            capability_id="cap_123",
            actor="test",
            component="test_comp",
            result="verified",
        )

        assert result["ok"]
        events = recorder.get_capability_events()
        assert len(events) == 1
        assert events[0].capability_id == "cap_123"
        recorder.stop()


class TestAuthorizationInstrument:
    """Tests for authorization instrumentation."""

    def test_derive_records_event(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = AuthorizationInstrument(recorder)

        result = instrument.derive(
            authorization_id="auth_123",
            actor="test",
            component="test_comp",
            result="derived",
        )

        assert result["ok"]
        events = recorder.get_authorization_events()
        assert len(events) == 1
        assert events[0].authorization_id == "auth_123"
        recorder.stop()


class TestProvenanceInstrument:
    """Tests for provenance instrumentation."""

    def test_record_records_event(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        instrument = ProvenanceInstrument(recorder)

        result = instrument.record(
            provenance_id="prov_123",
            actor="test",
            component="test_comp",
            result="recorded",
        )

        assert result["ok"]
        events = recorder.get_provenance_events()
        assert len(events) == 1
        assert events[0].provenance_id == "prov_123"
        recorder.stop()


class TestInstrumentationSuite:
    """Tests for the complete instrumentation suite."""

    def test_start_stop(self):
        suite = InstrumentationSuite("test_exp")
        assert not suite.is_active
        suite.start()
        assert suite.is_active
        suite.stop()
        assert not suite.is_active

    def test_full_workflow(self):
        suite = InstrumentationSuite("test_exp")
        suite.start()

        # Capability verification
        suite.capability.verify(
            capability_id="cap_123",
            actor="test",
            component="test_comp",
        )

        # Authorization derivation
        suite.authorization.derive(
            authorization_id="auth_123",
            actor="test",
            component="test_comp",
        )

        # Subprocess execution
        suite.subprocess.run(
            cmd=["echo", "hello"],
            actor="test",
            component="test_comp",
            consequence_type=ConsequenceType.INFORMATIONAL,
            capability_id="cap_123",
            authorization_id="auth_123",
        )

        # Provenance recording
        suite.provenance.record(
            provenance_id="prov_123",
            actor="test",
            component="test_comp",
        )

        suite.stop()

        # Verify all events recorded
        assert len(suite.recorder.get_capability_events()) == 1
        assert len(suite.recorder.get_authorization_events()) == 1
        assert len(suite.recorder.get_subprocess_events()) == 2
        assert len(suite.recorder.get_provenance_events()) == 1

    def test_to_dict(self):
        suite = InstrumentationSuite("test_exp")
        suite.start()
        suite.subprocess.run(
            cmd=["echo", "hello"],
            actor="test",
            component="test_comp",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        suite.stop()

        d = suite.to_dict()
        assert d["experiment_id"] == "test_exp"
        assert d["total_events"] == 2


class TestTraceEvent:
    """Tests for trace event structure."""

    def test_event_fields(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        event = recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="test_actor",
            component="test_comp",
            operation="test_op",
            resource="test_res",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            result="test_result",
            authority_context={"key": "value"},
            capability_id="cap_123",
            authorization_id="auth_456",
            provenance_id="prov_789",
            raw_evidence="test_evidence",
        )
        recorder.stop()

        assert event is not None
        assert event.event_id is not None
        assert event.actor == "test_actor"
        assert event.component == "test_comp"
        assert event.operation == "test_op"
        assert event.resource == "test_res"
        assert event.consequence_type == ConsequenceType.EXTERNAL_CONSEQUENTIAL
        assert event.result == "test_result"
        assert event.authority_context == {"key": "value"}
        assert event.capability_id == "cap_123"
        assert event.authorization_id == "auth_456"
        assert event.provenance_id == "prov_789"
        assert event.raw_evidence == "test_evidence"
        assert event.process_id == os.getpid()

    def test_event_serialization(self):
        recorder = RuntimeTraceRecorder("test_exp")
        recorder.start()
        event = recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor="test",
            component="c",
            operation="o",
            resource="r",
            consequence_type=ConsequenceType.INFORMATIONAL,
        )
        recorder.stop()

        assert event is not None
        d = event.to_dict()
        assert d["event_type"] == TraceEventType.SUBPROCESS_CREATE
        assert d["actor"] == "test"
        assert "event_id" in d
        assert "timestamp" in d
