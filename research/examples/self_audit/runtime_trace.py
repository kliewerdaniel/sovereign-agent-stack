"""Runtime Trace Infrastructure for Authority Topology Experiments.

This module provides bounded runtime instrumentation for recording
process execution, subprocess creation, network requests, filesystem
mutations, broker calls, and authority chain events.

CRITICAL INVARIANT:
    Runtime traces are observations.
    They are NOT automatically authorization, evidence of legitimacy,
    proof of correctness, or proof that an action was permitted.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class TraceEventType(str, Enum):
    """Types of trace events."""
    SUBPROCESS_CREATE = "subprocess_create"
    SUBPROCESS_COMPLETE = "subprocess_complete"
    NETWORK_REQUEST = "network_request"
    NETWORK_RESPONSE = "network_response"
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    BROKER_CALL = "broker_call"
    BROKER_RESPONSE = "broker_response"
    CAPABILITY_VERIFY = "capability_verify"
    AUTHORIZATION_DERIVE = "authorization_derive"
    CONSEQUENCE_ENTER = "consequence_enter"
    CONSEQUENCE_EXIT = "consequence_exit"
    EXECUTION_RECEIPT = "execution_receipt"
    PROVENANCE_RECORD = "provenance_record"
    DYNAMIC_IMPORT = "dynamic_import"
    REFLECTION_CALL = "reflection_call"
    DISPATCH_CALL = "dispatch_call"
    CONFIG_ACCESS = "config_access"
    CREDENTIAL_ACCESS = "credential_access"
    IDENTITY_MUTATION = "identity_mutation"
    PAYMENT_PROCESS = "payment_process"
    SUBSTRATE_OPERATION = "substrate_operation"
    CLI_DISPATCH = "cli_dispatch"


class ConsequenceType(str, Enum):
    """Types of consequences."""
    EXTERNAL_CONSEQUENTIAL = "external_consequential"
    AUTHORITY_MANAGEMENT = "authority_management"
    STATE_TRANSFORMING = "state_transforming"
    INFORMATIONAL = "informational"
    NON_CONSEQUENTIAL = "non_consequential"


@dataclass(frozen=True)
class TraceEvent:
    """A single runtime trace event."""

    event_id: str
    timestamp: str
    event_type: str
    actor: str
    component: str
    operation: str
    resource: str
    consequence_type: str
    parent_event: Optional[str]
    call_path: list[str]
    authority_context: dict[str, Any]
    capability_id: Optional[str]
    authorization_id: Optional[str]
    provenance_id: Optional[str]
    environment: str
    process_id: int
    thread_id: int
    result: str
    scope: str
    limitations: str
    raw_evidence: str = ""

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "component": self.component,
            "operation": self.operation,
            "resource": self.resource,
            "consequence_type": self.consequence_type,
            "parent_event": self.parent_event,
            "call_path": self.call_path,
            "authority_context": self.authority_context,
            "capability_id": self.capability_id,
            "authorization_id": self.authorization_id,
            "provenance_id": self.provenance_id,
            "environment": self.environment,
            "process_id": self.process_id,
            "thread_id": self.thread_id,
            "result": self.result,
            "scope": self.scope,
            "limitations": self.limitations,
            "raw_evidence": self.raw_evidence,
        }


class RuntimeTraceRecorder:
    """Records runtime events during controlled experiments."""

    def __init__(self, experiment_id: str, scope: str = "local"):
        self.experiment_id = experiment_id
        self.scope = scope
        self.events: list[TraceEvent] = []
        self._active = False
        self._parent_stack: list[str] = []
        self._lock = threading.Lock()

    def start(self):
        """Start recording."""
        with self._lock:
            self._active = True
            self.events = []
            self._parent_stack = []

    def stop(self):
        """Stop recording."""
        with self._lock:
            self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def record(
        self,
        event_type: str,
        actor: str,
        component: str,
        operation: str,
        resource: str,
        consequence_type: str,
        result: str = "observed",
        authority_context: Optional[dict[str, Any]] = None,
        capability_id: Optional[str] = None,
        authorization_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
        raw_evidence: str = "",
        scope: str = "local",
        limitations: str = "runtime observation only",
    ) -> Optional[TraceEvent]:
        """Record a trace event."""
        with self._lock:
            if not self._active:
                return None

            event = TraceEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.utcnow().isoformat(),
                event_type=event_type,
                actor=actor,
                component=component,
                operation=operation,
                resource=resource,
                consequence_type=consequence_type,
                parent_event=self._parent_stack[-1] if self._parent_stack else None,
                call_path=list(self._parent_stack),
                authority_context=authority_context or {},
                capability_id=capability_id,
                authorization_id=authorization_id,
                provenance_id=provenance_id,
                environment=self.scope,
                process_id=os.getpid(),
                thread_id=threading.current_thread().ident or 0,
                result=result,
                scope=scope,
                limitations=limitations,
                raw_evidence=raw_evidence,
            )
            self.events.append(event)
            return event

    def push_call(self, event_id: str):
        """Push a call onto the parent stack."""
        with self._lock:
            self._parent_stack.append(event_id)

    def pop_call(self):
        """Pop a call from the parent stack."""
        with self._lock:
            if self._parent_stack:
                self._parent_stack.pop()

    def get_events_by_type(self, event_type: str) -> list[TraceEvent]:
        """Get events by type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_actor(self, actor: str) -> list[TraceEvent]:
        """Get events by actor."""
        return [e for e in self.events if e.actor == actor]

    def get_events_by_consequence(self, consequence_type: str) -> list[TraceEvent]:
        """Get events by consequence type."""
        return [e for e in self.events if e.consequence_type == consequence_type]

    def get_subprocess_events(self) -> list[TraceEvent]:
        """Get subprocess events."""
        return [
            e for e in self.events
            if e.event_type in (TraceEventType.SUBPROCESS_CREATE, TraceEventType.SUBPROCESS_COMPLETE)
        ]

    def get_network_events(self) -> list[TraceEvent]:
        """Get network events."""
        return self.get_events_by_type(TraceEventType.NETWORK_REQUEST)

    def get_filesystem_events(self) -> list[TraceEvent]:
        """Get filesystem events."""
        return self.get_events_by_type(TraceEventType.FILESYSTEM_WRITE)

    def get_broker_events(self) -> list[TraceEvent]:
        """Get broker events."""
        return self.get_events_by_type(TraceEventType.BROKER_CALL)

    def get_capability_events(self) -> list[TraceEvent]:
        """Get capability verification events."""
        return self.get_events_by_type(TraceEventType.CAPABILITY_VERIFY)

    def get_authorization_events(self) -> list[TraceEvent]:
        """Get authorization derivation events."""
        return self.get_events_by_type(TraceEventType.AUTHORIZATION_DERIVE)

    def get_provenance_events(self) -> list[TraceEvent]:
        """Get provenance recording events."""
        return self.get_events_by_type(TraceEventType.PROVENANCE_RECORD)

    def get_consequence_events(self) -> list[TraceEvent]:
        """Get consequence boundary events."""
        return [
            e for e in self.events
            if e.event_type in (TraceEventType.CONSEQUENCE_ENTER, TraceEventType.CONSEQUENCE_EXIT)
        ]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "scope": self.scope,
            "total_events": len(self.events),
            "events": [e.to_dict() for e in self.events],
        }


class SubprocessInstrument:
    """Instruments subprocess calls."""

    def __init__(self, recorder: RuntimeTraceRecorder):
        self.recorder = recorder

    def run(
        self,
        cmd: list[str],
        actor: str = "unknown",
        component: str = "unknown",
        consequence_type: str = ConsequenceType.INFORMATIONAL,
        authority_context: Optional[dict[str, Any]] = None,
        capability_id: Optional[str] = None,
        authorization_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Run a subprocess with instrumentation."""
        event = self.recorder.record(
            event_type=TraceEventType.SUBPROCESS_CREATE,
            actor=actor,
            component=component,
            operation="subprocess.run",
            resource=" ".join(cmd),
            consequence_type=consequence_type,
            result="attempting",
            authority_context=authority_context or {},
            capability_id=capability_id,
            authorization_id=authorization_id,
            provenance_id=provenance_id,
        )

        if event:
            self.recorder.push_call(event.event_id)

        try:
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)

            self.recorder.record(
                event_type=TraceEventType.SUBPROCESS_COMPLETE,
                actor=actor,
                component=component,
                operation="subprocess.run",
                resource=" ".join(cmd),
                consequence_type=consequence_type,
                result=f"exit_code={result.returncode}",
                authority_context=authority_context or {},
                capability_id=capability_id,
                authorization_id=authorization_id,
                provenance_id=provenance_id,
                raw_evidence=f"stdout_len={len(result.stdout)}, stderr_len={len(result.stderr)}",
            )

            return {
                "ok": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            self.recorder.record(
                event_type=TraceEventType.SUBPROCESS_COMPLETE,
                actor=actor,
                component=component,
                operation="subprocess.run",
                resource=" ".join(cmd),
                consequence_type=consequence_type,
                result=f"error={str(e)}",
                authority_context=authority_context or {},
                capability_id=capability_id,
                authorization_id=authorization_id,
                provenance_id=provenance_id,
            )
            return {"ok": False, "error": str(e)}
        finally:
            if event:
                self.recorder.pop_call()


class FilesystemInstrument:
    """Instruments filesystem operations."""

    def __init__(self, recorder: RuntimeTraceRecorder):
        self.recorder = recorder

    def write(
        self,
        path: str,
        content: str,
        actor: str = "unknown",
        component: str = "unknown",
        consequence_type: str = ConsequenceType.STATE_TRANSFORMING,
        authority_context: Optional[dict[str, Any]] = None,
        capability_id: Optional[str] = None,
        authorization_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
    ) -> dict:
        """Write to filesystem with instrumentation."""
        event = self.recorder.record(
            event_type=TraceEventType.FILESYSTEM_WRITE,
            actor=actor,
            component=component,
            operation="open(write)",
            resource=path,
            consequence_type=consequence_type,
            result="attempting",
            authority_context=authority_context or {},
            capability_id=capability_id,
            authorization_id=authorization_id,
            provenance_id=provenance_id,
        )

        try:
            with open(path, "w") as f:
                f.write(content)

            if event:
                self.recorder.record(
                    event_type=TraceEventType.FILESYSTEM_WRITE,
                    actor=actor,
                    component=component,
                    operation="open(write)",
                    resource=path,
                    consequence_type=consequence_type,
                    result="success",
                    authority_context=authority_context or {},
                    capability_id=capability_id,
                    authorization_id=authorization_id,
                    provenance_id=provenance_id,
                    raw_evidence=f"content_len={len(content)}",
                )
            return {"ok": True}
        except Exception as e:
            if event:
                self.recorder.record(
                    event_type=TraceEventType.FILESYSTEM_WRITE,
                    actor=actor,
                    component=component,
                    operation="open(write)",
                    resource=path,
                    consequence_type=consequence_type,
                    result=f"error={str(e)}",
                    authority_context=authority_context or {},
                    capability_id=capability_id,
                    authorization_id=authorization_id,
                    provenance_id=provenance_id,
                )
            return {"ok": False, "error": str(e)}
        finally:
            if event:
                self.recorder.pop_call()

    def read(
        self,
        path: str,
        actor: str = "unknown",
        component: str = "unknown",
        consequence_type: str = ConsequenceType.INFORMATIONAL,
        authority_context: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Read from filesystem with instrumentation."""
        event = self.recorder.record(
            event_type=TraceEventType.FILESYSTEM_READ,
            actor=actor,
            component=component,
            operation="open(read)",
            resource=path,
            consequence_type=consequence_type,
            result="attempting",
            authority_context=authority_context or {},
        )

        try:
            with open(path, "r") as f:
                content = f.read()

            if event:
                self.recorder.record(
                    event_type=TraceEventType.FILESYSTEM_READ,
                    actor=actor,
                    component=component,
                    operation="open(read)",
                    resource=path,
                    consequence_type=consequence_type,
                    result="success",
                    authority_context=authority_context or {},
                    raw_evidence=f"content_len={len(content)}",
                )
            return {"ok": True, "content": content}
        except Exception as e:
            if event:
                self.recorder.record(
                    event_type=TraceEventType.FILESYSTEM_READ,
                    actor=actor,
                    component=component,
                    operation="open(read)",
                    resource=path,
                    consequence_type=consequence_type,
                    result=f"error={str(e)}",
                    authority_context=authority_context or {},
                )
            return {"ok": False, "error": str(e)}
        finally:
            if event:
                self.recorder.pop_call()


class BrokerInstrument:
    """Instruments broker calls."""

    def __init__(self, recorder: RuntimeTraceRecorder):
        self.recorder = recorder

    def submit_trade(
        self,
        trade: Any,
        actor: str = "unknown",
        component: str = "unknown",
        consequence_type: str = ConsequenceType.EXTERNAL_CONSEQUENTIAL,
        authority_context: Optional[dict[str, Any]] = None,
        capability_id: Optional[str] = None,
        authorization_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
    ) -> dict:
        """Submit a trade with instrumentation."""
        event = self.recorder.record(
            event_type=TraceEventType.BROKER_CALL,
            actor=actor,
            component=component,
            operation="submit_trade",
            resource=str(getattr(trade, "symbol", trade)),
            consequence_type=consequence_type,
            result="attempting",
            authority_context=authority_context or {},
            capability_id=capability_id,
            authorization_id=authorization_id,
            provenance_id=provenance_id,
        )

        if event:
            self.recorder.push_call(event.event_id)

        try:
            # In a real experiment, this would call the actual broker
            # For now, we just record the attempt
            result = {"ok": True, "status": "simulated"}

            self.recorder.record(
                event_type=TraceEventType.BROKER_RESPONSE,
                actor=actor,
                component=component,
                operation="submit_trade",
                resource=str(getattr(trade, "symbol", trade)),
                consequence_type=consequence_type,
                result="simulated_success",
                authority_context=authority_context or {},
                capability_id=capability_id,
                authorization_id=authorization_id,
                provenance_id=provenance_id,
            )

            return result
        except Exception as e:
            self.recorder.record(
                event_type=TraceEventType.BROKER_RESPONSE,
                actor=actor,
                component=component,
                operation="submit_trade",
                resource=str(getattr(trade, "symbol", trade)),
                consequence_type=consequence_type,
                result=f"error={str(e)}",
                authority_context=authority_context or {},
                capability_id=capability_id,
                authorization_id=authorization_id,
                provenance_id=provenance_id,
            )
            return {"ok": False, "error": str(e)}
        finally:
            if event:
                self.recorder.pop_call()


class CapabilityInstrument:
    """Instruments capability verification."""

    def __init__(self, recorder: RuntimeTraceRecorder):
        self.recorder = recorder

    def verify(
        self,
        capability_id: str,
        actor: str = "unknown",
        component: str = "unknown",
        result: str = "verified",
        authority_context: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Record capability verification."""
        event = self.recorder.record(
            event_type=TraceEventType.CAPABILITY_VERIFY,
            actor=actor,
            component=component,
            operation="verify_capability",
            resource=capability_id,
            consequence_type=ConsequenceType.AUTHORITY_MANAGEMENT,
            result=result,
            authority_context=authority_context or {},
            capability_id=capability_id,
        )

        return {"ok": True, "event_id": event.event_id if event else None}


class AuthorizationInstrument:
    """Instruments authorization derivation."""

    def __init__(self, recorder: RuntimeTraceRecorder):
        self.recorder = recorder

    def derive(
        self,
        authorization_id: str,
        actor: str = "unknown",
        component: str = "unknown",
        result: str = "derived",
        authority_context: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Record authorization derivation."""
        event = self.recorder.record(
            event_type=TraceEventType.AUTHORIZATION_DERIVE,
            actor=actor,
            component=component,
            operation="derive_authorization",
            resource=authorization_id,
            consequence_type=ConsequenceType.AUTHORITY_MANAGEMENT,
            result=result,
            authority_context=authority_context or {},
            authorization_id=authorization_id,
        )

        return {"ok": True, "event_id": event.event_id if event else None}


class ProvenanceInstrument:
    """Instruments provenance recording."""

    def __init__(self, recorder: RuntimeTraceRecorder):
        self.recorder = recorder

    def record(
        self,
        provenance_id: str,
        actor: str = "unknown",
        component: str = "unknown",
        result: str = "recorded",
        authority_context: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Record provenance."""
        event = self.recorder.record(
            event_type=TraceEventType.PROVENANCE_RECORD,
            actor=actor,
            component=component,
            operation="record_provenance",
            resource=provenance_id,
            consequence_type=ConsequenceType.STATE_TRANSFORMING,
            result=result,
            authority_context=authority_context or {},
            provenance_id=provenance_id,
        )

        return {"ok": True, "event_id": event.event_id if event else None}


class InstrumentationSuite:
    """Complete instrumentation suite for runtime experiments."""

    def __init__(self, experiment_id: str, scope: str = "local"):
        self.recorder = RuntimeTraceRecorder(experiment_id, scope)
        self.subprocess = SubprocessInstrument(self.recorder)
        self.filesystem = FilesystemInstrument(self.recorder)
        self.broker = BrokerInstrument(self.recorder)
        self.capability = CapabilityInstrument(self.recorder)
        self.authorization = AuthorizationInstrument(self.recorder)
        self.provenance = ProvenanceInstrument(self.recorder)

    def start(self):
        """Start all instrumentation."""
        self.recorder.start()

    def stop(self):
        """Stop all instrumentation."""
        self.recorder.stop()

    @property
    def is_active(self) -> bool:
        return self.recorder.is_active

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.recorder.to_dict()
