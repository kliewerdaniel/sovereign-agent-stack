"""Runtime Authority Topology — Static Prediction, Runtime Trace, Reconciliation.

This module implements the experimental framework for distinguishing:

    STATIC AUTHORITY TOPOLOGY  vs  RUNTIME AUTHORITY TOPOLOGY

The central research question:
    Can SAS construct an empirically grounded model of authority that is
    derived from both static architecture and observed runtime behavior
    without allowing either source to silently become more authoritative
    than the evidence permits?

Critical invariants:
    STATIC PATH ≠ RUNTIME PATH
    RUNTIME PATH ≠ AUTHORIZED PATH
    AUTHORIZED PATH ≠ EXTERNAL EFFECT
    TRACE ≠ AUTHORIZATION
    TRACE INTEGRITY ≠ EPISTEMIC VALIDITY
    ABSENCE OF OBSERVATION ≠ OBSERVATION OF ABSENCE
    REACHABILITY ≠ EXECUTION
    EXECUTION ≠ CONSEQUENCE
    CONSEQUENCE ≠ AUTHORITY
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class ObservationSource(str, Enum):
    """Source of an authority observation."""
    STATIC_ANALYSIS = "static_analysis"
    RUNTIME_TRACE = "runtime_trace"
    CONTROLLED_EXPERIMENT = "controlled_experiment"
    INSTRUMENTED_EXECUTION = "instrumented_execution"
    ADVERSARIAL_TEST = "adversarial_test"


class RuntimeEventType(str, Enum):
    """Types of runtime events that can be observed."""
    PROCESS_EXECUTION = "process_execution"
    SUBPROCESS_CREATION = "subprocess_creation"
    NETWORK_REQUEST = "network_request"
    FILESYSTEM_MUTATION = "filesystem_mutation"
    BROKER_CALL = "broker_call"
    CAPABILITY_VERIFICATION = "capability_verification"
    AUTHORIZATION_DERIVATION = "authorization_derivation"
    CONSEQUENCE_BOUNDARY_ENTRY = "consequence_boundary_entry"
    CONSEQUENCE_BOUNDARY_EXIT = "consequence_boundary_exit"
    EXECUTION_RECEIPT = "execution_receipt"
    PROVENANCE_CREATION = "provenance_creation"
    DYNAMIC_IMPORT = "dynamic_import"
    REFLECTION_CALL = "reflection_call"
    DISPATCH_INVOCATION = "dispatch_invocation"
    CONFIGURATION_ACCESS = "configuration_access"
    CREDENTIAL_ACCESS = "credential_access"
    IDENTITY_MUTATION = "identity_mutation"
    PAYMENT_PROCESSING = "payment_processing"
    SUBSTRATE_OPERATION = "substrate_operation"
    CLI_DISPATCH = "cli_dispatch"


class ConsequenceType(str, Enum):
    """Types of consequences."""
    EXTERNAL_CONSEQUENTIAL = "external_consequential"
    AUTHORITY_MANAGEMENT = "authority_management"
    STATE_TRANSFORMING = "state_transforming"
    INFORMATIONAL = "informational"
    NON_CONSEQUENTIAL = "non_consequential"


class AuthorityClassification(str, Enum):
    """Classification of an authority edge after reconciliation."""
    STATIC_ONLY = "static_only"
    RUNTIME_ONLY = "runtime_only"
    STATIC_AND_RUNTIME = "static_and_runtime"
    STATIC_FALSE_POSITIVE = "static_false_positive"
    RUNTIME_UNEXPECTED = "runtime_unexpected"
    AUTHORITY_CONTROLLED = "authority_controlled"
    AUTHORITY_ESCAPE = "authority_escape"
    INCONCLUSIVE = "inconclusive"


class EpistemicState(str, Enum):
    """Epistemic state of a runtime observation."""
    UNKNOWN = "unknown"
    INCONCLUSIVE = "inconclusive"
    OBSERVED = "observed"
    SUPPORTED = "supported"
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"


class ReconstructionState(str, Enum):
    """State of authority reconstruction for a runtime event."""
    AUTHORIZED_AND_RECONSTRUCTIBLE = "authorized_and_reconstructible"
    AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE = "authorized_but_not_reconstructible"
    UNAUTHORIZED = "unauthorized"
    NON_CONSEQUENTIAL = "non_consequential"
    INSUFFICIENT_TRACE = "insufficient_trace"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Runtime Event
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeEvent:
    """A single runtime observation.

    Every runtime observation must contain sufficient context to
    reconstruct the authority path, but the trace itself is NOT
    authority — it is evidence.
    """

    event_id: str
    timestamp: str
    actor: str
    component: str
    operation: str
    resource: str
    consequence_type: ConsequenceType
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
    event_type: RuntimeEventType
    raw_evidence: str = ""

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "component": self.component,
            "operation": self.operation,
            "resource": self.resource,
            "consequence_type": self.consequence_type.value,
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
            "event_type": self.event_type.value,
            "raw_evidence": self.raw_evidence,
        }


# ---------------------------------------------------------------------------
# Static Hypothesis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StaticHypothesis:
    """A predicted authority edge from static analysis.

    This is explicitly a STATIC_HYPOTHESIS, not a RUNTIME_FACT.
    """

    hypothesis_id: str
    source: str
    target: str
    operation: str
    consequence_type: ConsequenceType
    static_evidence: str
    expected_authority_boundary: str
    expected_capability: str
    expected_authorization: str
    expected_provenance: str
    predicted_classification: AuthorityClassification
    confidence: float
    source_location: str
    target_location: str
    alternatives: list[str]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "source": self.source,
            "target": self.target,
            "operation": self.operation,
            "consequence_type": self.consequence_type.value,
            "static_evidence": self.static_evidence,
            "expected_authority_boundary": self.expected_authority_boundary,
            "expected_capability": self.expected_capability,
            "expected_authorization": self.expected_authorization,
            "expected_provenance": self.expected_provenance,
            "predicted_classification": self.predicted_classification.value,
            "confidence": self.confidence,
            "source_location": self.source_location,
            "target_location": self.target_location,
            "alternatives": self.alternatives,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Reconciliation Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconciliationResult:
    """Result of reconciling a static hypothesis against runtime traces."""

    reconciliation_id: str
    hypothesis: StaticHypothesis
    classification: AuthorityClassification
    confidence: float
    runtime_events: list[RuntimeEvent]
    static_evidence: str
    runtime_evidence: str
    authority_reconstruction: Optional[dict[str, Any]]
    epistemic_state: EpistemicState
    limitations: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "reconciliation_id": self.reconciliation_id,
            "hypothesis": self.hypothesis.to_dict(),
            "classification": self.classification.value,
            "confidence": self.confidence,
            "runtime_events": [e.to_dict() for e in self.runtime_events],
            "static_evidence": self.static_evidence,
            "runtime_evidence": self.runtime_evidence,
            "authority_reconstruction": self.authority_reconstruction,
            "epistemic_state": self.epistemic_state.value,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Runtime Trace Recorder
# ---------------------------------------------------------------------------


class RuntimeTraceRecorder:
    """Records runtime events during controlled experiments.

    CRITICAL INVARIANT:
        Runtime traces are observations.
        They are NOT automatically:
        - authorization
        - evidence of legitimacy
        - proof of correctness
        - proof of necessity
        - proof that an action was permitted
    """

    def __init__(self, experiment_id: str, scope: str = "local"):
        self.experiment_id = experiment_id
        self.scope = scope
        self.events: list[RuntimeEvent] = []
        self._active = False
        self._parent_stack: list[str] = []

    def start(self):
        """Start recording runtime events."""
        self._active = True
        self.events = []

    def stop(self):
        """Stop recording runtime events."""
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def record_event(
        self,
        actor: str,
        component: str,
        operation: str,
        resource: str,
        consequence_type: ConsequenceType,
        event_type: RuntimeEventType,
        result: str = "observed",
        authority_context: Optional[dict[str, Any]] = None,
        capability_id: Optional[str] = None,
        authorization_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
        raw_evidence: str = "",
        scope: str = "local",
        limitations: str = "runtime observation only",
    ) -> Optional[RuntimeEvent]:
        """Record a runtime event if recording is active."""
        if not self._active:
            return None

        event = RuntimeEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
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
            event_type=event_type,
            raw_evidence=raw_evidence,
        )
        self.events.append(event)
        return event

    def push_call(self, event_id: str):
        """Push a call onto the parent stack."""
        self._parent_stack.append(event_id)

    def pop_call(self):
        """Pop a call from the parent stack."""
        if self._parent_stack:
            self._parent_stack.pop()

    def get_events_by_type(self, event_type: RuntimeEventType) -> list[RuntimeEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_actor(self, actor: str) -> list[RuntimeEvent]:
        """Get all events for a specific actor."""
        return [e for e in self.events if e.actor == actor]

    def get_events_by_consequence(self, consequence_type: ConsequenceType) -> list[RuntimeEvent]:
        """Get all events with a specific consequence type."""
        return [e for e in self.events if e.consequence_type == consequence_type]

    def get_subprocess_events(self) -> list[RuntimeEvent]:
        """Get all subprocess creation events."""
        return self.get_events_by_type(RuntimeEventType.SUBPROCESS_CREATION)

    def get_network_events(self) -> list[RuntimeEvent]:
        """Get all network request events."""
        return self.get_events_by_type(RuntimeEventType.NETWORK_REQUEST)

    def get_filesystem_events(self) -> list[RuntimeEvent]:
        """Get all filesystem mutation events."""
        return self.get_events_by_type(RuntimeEventType.FILESYSTEM_MUTATION)

    def get_broker_events(self) -> list[RuntimeEvent]:
        """Get all broker call events."""
        return self.get_events_by_type(RuntimeEventType.BROKER_CALL)

    def get_capability_events(self) -> list[RuntimeEvent]:
        """Get all capability verification events."""
        return self.get_events_by_type(RuntimeEventType.CAPABILITY_VERIFICATION)

    def get_authorization_events(self) -> list[RuntimeEvent]:
        """Get all authorization derivation events."""
        return self.get_events_by_type(RuntimeEventType.AUTHORIZATION_DERIVATION)

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "scope": self.scope,
            "total_events": len(self.events),
            "events": [e.to_dict() for e in self.events],
        }


# ---------------------------------------------------------------------------
# Static Authority Graph Builder
# ---------------------------------------------------------------------------


class StaticAuthorityGraphBuilder:
    """Builds a predicted authority graph from static analysis.

    All predictions are explicitly marked as STATIC_HYPOTHESIS.
    """

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src" / "sas"
        self.hypotheses: list[StaticHypothesis] = []

    def build_graph(self) -> list[StaticHypothesis]:
        """Build the full static authority graph."""
        self.hypotheses = []

        # Analyze subprocess paths
        self._analyze_subprocess_paths()

        # Analyze network paths
        self._analyze_network_paths()

        # Analyze filesystem paths
        self._analyze_filesystem_paths()

        # Analyze broker paths
        self._analyze_broker_paths()

        # Analyze dynamic import paths
        self._analyze_dynamic_imports()

        return self.hypotheses

    def _analyze_subprocess_paths(self):
        """Analyze subprocess invocation patterns."""
        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Find subprocess.run calls
                for match in re.finditer(r"subprocess\.run\s*\(", content):
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    # Determine the command being run
                    cmd = self._extract_subprocess_command(context)

                    # Determine if capability verification is present
                    has_capability = "capability" in content.lower() or "CapabilityVerifier" in content
                    has_authorization = "authorization" in content.lower() or "AuthorizationArtifact" in content
                    has_provenance = "provenance" in content.lower() or "ProvenanceRecord" in content

                    # Determine expected authority boundary
                    if has_capability and has_authorization:
                        expected_boundary = "full_protocol"
                    elif has_capability:
                        expected_boundary = "capability_only"
                    elif has_authorization:
                        expected_boundary = "authorization_only"
                    else:
                        expected_boundary = "none"

                    # Determine predicted classification
                    if expected_boundary == "none":
                        predicted = AuthorityClassification.AUTHORITY_ESCAPE
                        confidence = 0.6
                    elif expected_boundary == "full_protocol":
                        predicted = AuthorityClassification.AUTHORITY_CONTROLLED
                        confidence = 0.7
                    else:
                        predicted = AuthorityClassification.INCONCLUSIVE
                        confidence = 0.5

                    self.hypotheses.append(StaticHypothesis(
                        hypothesis_id=f"hyp_{len(self.hypotheses)+1:04d}",
                        source=str(rel_path),
                        target=f"subprocess.run({cmd})",
                        operation="subprocess_execution",
                        consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
                        static_evidence=context[:400],
                        expected_authority_boundary=expected_boundary,
                        expected_capability="CapabilityVerifier" if has_capability else "none",
                        expected_authorization="AuthorizationArtifact" if has_authorization else "none",
                        expected_provenance="ProvenanceRecord" if has_provenance else "none",
                        predicted_classification=predicted,
                        confidence=confidence,
                        source_location=str(rel_path),
                        target_location=f"line {content[:match.start()].count(chr(10)) + 1}",
                        alternatives=[
                            "Path is wrapped by capability-bound executor",
                            "Path is only reachable from trusted computing base",
                            "Path is test-only and not reachable in production",
                            "Path is informational (read-only)",
                            "Subprocess command is parameterized and safe",
                            "Subprocess is invoked by a trusted TCB component",
                        ],
                    ))

            except Exception:
                pass

    def _analyze_network_paths(self):
        """Analyze network request patterns."""
        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Find httpx.post/requests.post calls
                for match in re.finditer(r"(httpx|requests)\.(post|put|delete|patch)\s*\(", content):
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    has_capability = "capability" in content.lower()
                    has_authorization = "authorization" in content.lower()

                    if has_capability and has_authorization:
                        expected_boundary = "full_protocol"
                        predicted = AuthorityClassification.AUTHORITY_CONTROLLED
                        confidence = 0.7
                    elif has_capability:
                        expected_boundary = "capability_only"
                        predicted = AuthorityClassification.INCONCLUSIVE
                        confidence = 0.5
                    else:
                        expected_boundary = "none"
                        predicted = AuthorityClassification.AUTHORITY_ESCAPE
                        confidence = 0.6

                    self.hypotheses.append(StaticHypothesis(
                        hypothesis_id=f"hyp_{len(self.hypotheses)+1:04d}",
                        source=str(rel_path),
                        target=f"{match.group(1)}.{match.group(2)}()",
                        operation="network_mutation",
                        consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
                        static_evidence=context[:400],
                        expected_authority_boundary=expected_boundary,
                        expected_capability="CapabilityVerifier" if has_capability else "none",
                        expected_authorization="AuthorizationArtifact" if has_authorization else "none",
                        expected_provenance="none",
                        predicted_classification=predicted,
                        confidence=confidence,
                        source_location=str(rel_path),
                        target_location=f"line {content[:match.start()].count(chr(10)) + 1}",
                        alternatives=[
                            "Path is wrapped by capability-bound executor",
                            "Path is only reachable from trusted computing base",
                            "Path is test-only",
                        ],
                    ))

            except Exception:
                pass

    def _analyze_filesystem_paths(self):
        """Analyze filesystem mutation patterns."""
        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Find open() calls with write mode
                for match in re.finditer(r"open\s*\([^)]*['\"](w|a|x|wb|ab)['\"]", content):
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    # Determine if this is internal state management
                    is_internal = any(kw in content.lower() for kw in [
                        "config", "cache", "registry", "state", "knowledge.db",
                        "auth.db", "provenance", "evidence",
                    ])

                    if is_internal:
                        consequence_type = ConsequenceType.STATE_TRANSFORMING
                        predicted = AuthorityClassification.STATIC_FALSE_POSITIVE
                        confidence = 0.8
                    else:
                        consequence_type = ConsequenceType.EXTERNAL_CONSEQUENTIAL
                        predicted = AuthorityClassification.INCONCLUSIVE
                        confidence = 0.5

                    self.hypotheses.append(StaticHypothesis(
                        hypothesis_id=f"hyp_{len(self.hypotheses)+1:04d}",
                        source=str(rel_path),
                        target="open(write)",
                        operation="filesystem_mutation",
                        consequence_type=consequence_type,
                        static_evidence=context[:400],
                        expected_authority_boundary="internal_state" if is_internal else "unknown",
                        expected_capability="none",
                        expected_authorization="none",
                        expected_provenance="none",
                        predicted_classification=predicted,
                        confidence=confidence,
                        source_location=str(rel_path),
                        target_location=f"line {content[:match.start()].count(chr(10)) + 1}",
                        alternatives=[
                            "Internal state management (config/cache/registry)",
                            "External file mutation",
                            "Test-only file creation",
                        ],
                    ))

            except Exception:
                pass

    def _analyze_broker_paths(self):
        """Analyze broker invocation patterns."""
        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Find submit_trade calls
                for match in re.finditer(r"submit_trade\s*\(", content):
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    has_capability = "CapabilityBoundBroker" in content
                    has_authorization = "AuthorizationArtifact" in content

                    if has_capability:
                        expected_boundary = "capability_bound"
                        predicted = AuthorityClassification.AUTHORITY_CONTROLLED
                        confidence = 0.75
                    else:
                        expected_boundary = "none"
                        predicted = AuthorityClassification.AUTHORITY_ESCAPE
                        confidence = 0.65

                    self.hypotheses.append(StaticHypothesis(
                        hypothesis_id=f"hyp_{len(self.hypotheses)+1:04d}",
                        source=str(rel_path),
                        target="submit_trade()",
                        operation="broker_call",
                        consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
                        static_evidence=context[:400],
                        expected_authority_boundary=expected_boundary,
                        expected_capability="CapabilityBoundBroker" if has_capability else "none",
                        expected_authorization="AuthorizationArtifact" if has_authorization else "none",
                        expected_provenance="none",
                        predicted_classification=predicted,
                        confidence=confidence,
                        source_location=str(rel_path),
                        target_location=f"line {content[:match.start()].count(chr(10)) + 1}",
                        alternatives=[
                            "Wrapped by CapabilityBoundBroker",
                            "Direct broker access",
                            "Test-only invocation",
                        ],
                    ))

            except Exception:
                pass

    def _analyze_dynamic_imports(self):
        """Analyze dynamic import patterns."""
        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                # Find importlib usage
                for match in re.finditer(r"importlib\.", content):
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    self.hypotheses.append(StaticHypothesis(
                        hypothesis_id=f"hyp_{len(self.hypotheses)+1:04d}",
                        source=str(rel_path),
                        target="importlib.dynamic_import",
                        operation="dynamic_import",
                        consequence_type=ConsequenceType.STATE_TRANSFORMING,
                        static_evidence=context[:400],
                        expected_authority_boundary="unknown",
                        expected_capability="none",
                        expected_authorization="none",
                        expected_provenance="none",
                        predicted_classification=AuthorityClassification.INCONCLUSIVE,
                        confidence = 0.4,
                        source_location=str(rel_path),
                        target_location=f"line {content[:match.start()].count(chr(10)) + 1}",
                        alternatives=[
                            "Dynamic plugin loading",
                            "Dynamic backend selection",
                            "Dynamic test fixture loading",
                        ],
                    ))

            except Exception:
                pass

    def _extract_subprocess_command(self, context: str) -> str:
        """Extract the command from a subprocess.run call."""
        # Try to find the command list
        match = re.search(r"\[\s*([^\]]+)\s*\]", context)
        if match:
            return match.group(1).strip()[:100]
        return "unknown_command"

    def to_dict(self) -> dict:
        return {
            "total_hypotheses": len(self.hypotheses),
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "summary": {
                "by_classification": self._count_by_classification(),
                "by_consequence": self._count_by_consequence(),
            },
        }

    def _count_by_classification(self) -> dict:
        counts = {}
        for h in self.hypotheses:
            cls = h.predicted_classification.value
            counts[cls] = counts.get(cls, 0) + 1
        return counts

    def _count_by_consequence(self) -> dict:
        counts = {}
        for h in self.hypotheses:
            ctype = h.consequence_type.value
            counts[ctype] = counts.get(ctype, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Static-Dynamic Reconciliation Engine
# ---------------------------------------------------------------------------


class ReconciliationEngine:
    """Reconciles static hypotheses against runtime traces."""

    def __init__(
        self,
        hypotheses: list[StaticHypothesis],
        runtime_events: list[RuntimeEvent],
    ):
        self.hypotheses = hypotheses
        self.runtime_events = runtime_events
        self.results: list[ReconciliationResult] = []

    def reconcile(self) -> list[ReconciliationResult]:
        """Run the full reconciliation process."""
        self.results = []

        for hypothesis in self.hypotheses:
            result = self._reconcile_hypothesis(hypothesis)
            self.results.append(result)

        return self.results

    def _reconcile_hypothesis(self, hypothesis: StaticHypothesis) -> ReconciliationResult:
        """Reconcile a single hypothesis against runtime events."""
        # Find matching runtime events
        matching_events = self._find_matching_events(hypothesis)

        if not matching_events:
            # No runtime events match this hypothesis
            if hypothesis.consequence_type == ConsequenceType.STATE_TRANSFORMING:
                # Internal state management - likely false positive
                classification = AuthorityClassification.STATIC_FALSE_POSITIVE
                confidence = 0.7
                epistemic = EpistemicState.OBSERVED
            else:
                # Could be dead code or not exercised in this experiment
                classification = AuthorityClassification.STATIC_ONLY
                confidence = 0.6
                epistemic = EpistemicState.INCONCLUSIVE

            return ReconciliationResult(
                reconciliation_id=f"rec_{hypothesis.hypothesis_id}",
                hypothesis=hypothesis,
                classification=classification,
                confidence=confidence,
                runtime_events=[],
                static_evidence=hypothesis.static_evidence,
                runtime_evidence="No matching runtime events observed",
                authority_reconstruction=None,
                epistemic_state=epistemic,
                limitations="Runtime experiment did not exercise this path",
            )

        # Runtime events found - analyze them
        has_capability = any(e.capability_id for e in matching_events)
        has_authorization = any(e.authorization_id for e in matching_events)
        has_provenance = any(e.provenance_id for e in matching_events)
        has_external_consequence = any(
            e.consequence_type == ConsequenceType.EXTERNAL_CONSEQUENTIAL
            for e in matching_events
        )

        # Reconstruct authority chain
        authority_reconstruction = self._reconstruct_authority(matching_events)

        # Classify
        if has_external_consequence:
            if has_capability and has_authorization and has_provenance:
                classification = AuthorityClassification.AUTHORITY_CONTROLLED
                confidence = 0.85
                epistemic = EpistemicState.AUTHORIZED
            elif has_capability or has_authorization:
                classification = AuthorityClassification.AUTHORITY_CONTROLLED
                confidence = 0.65
                epistemic = EpistemicState.AUTHORIZED
            else:
                classification = AuthorityClassification.AUTHORITY_ESCAPE
                confidence = 0.75
                epistemic = EpistemicState.UNAUTHORIZED
        else:
            if has_capability or has_authorization:
                classification = AuthorityClassification.AUTHORITY_CONTROLLED
                confidence = 0.7
                epistemic = EpistemicState.AUTHORIZED
            else:
                classification = AuthorityClassification.STATIC_FALSE_POSITIVE
                confidence = 0.7
                epistemic = EpistemicState.OBSERVED

        return ReconciliationResult(
            reconciliation_id=f"rec_{hypothesis.hypothesis_id}",
            hypothesis=hypothesis,
            classification=classification,
            confidence=confidence,
            runtime_events=matching_events,
            static_evidence=hypothesis.static_evidence,
            runtime_evidence=f"Observed {len(matching_events)} runtime events",
            authority_reconstruction=authority_reconstruction,
            epistemic_state=epistemic,
            limitations="Runtime observation under controlled conditions",
        )

    def _find_matching_events(self, hypothesis: StaticHypothesis) -> list[RuntimeEvent]:
        """Find runtime events that match a static hypothesis."""
        matching = []
        for event in self.runtime_events:
            # Match by operation type
            if hypothesis.operation == "subprocess_execution" and event.event_type == RuntimeEventType.SUBPROCESS_CREATION:
                matching.append(event)
            elif hypothesis.operation == "network_mutation" and event.event_type == RuntimeEventType.NETWORK_REQUEST:
                matching.append(event)
            elif hypothesis.operation == "filesystem_mutation" and event.event_type == RuntimeEventType.FILESYSTEM_MUTATION:
                matching.append(event)
            elif hypothesis.operation == "broker_call" and event.event_type == RuntimeEventType.BROKER_CALL:
                matching.append(event)
            elif hypothesis.operation == "dynamic_import" and event.event_type == RuntimeEventType.DYNAMIC_IMPORT:
                matching.append(event)
        return matching

    def _reconstruct_authority(self, events: list[RuntimeEvent]) -> dict[str, Any]:
        """Attempt to reconstruct the authority chain from runtime events."""
        if not events:
            return {"state": ReconstructionState.INSUFFICIENT_TRACE}

        # Check for capability verification
        capability_events = [e for e in events if e.capability_id]
        authorization_events = [e for e in events if e.authorization_id]
        provenance_events = [e for e in events if e.provenance_id]

        if capability_events and authorization_events and provenance_events:
            state = ReconstructionState.AUTHORIZED_AND_RECONSTRUCTIBLE
        elif capability_events or authorization_events:
            state = ReconstructionState.AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE
        else:
            state = ReconstructionState.UNAUTHORIZED

        return {
            "state": state.value,
            "capability_events": len(capability_events),
            "authorization_events": len(authorization_events),
            "provenance_events": len(provenance_events),
            "total_events": len(events),
        }

    def to_dict(self) -> dict:
        return {
            "total_reconciliations": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "by_classification": self._count_by_classification(),
                "by_epistemic_state": self._count_by_epistemic_state(),
            },
        }

    def _count_by_classification(self) -> dict:
        counts = {}
        for r in self.results:
            cls = r.classification.value
            counts[cls] = counts.get(cls, 0) + 1
        return counts

    def _count_by_epistemic_state(self) -> dict:
        counts = {}
        for r in self.results:
            state = r.epistemic_state.value
            counts[state] = counts.get(state, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Argopack Experiment
# ---------------------------------------------------------------------------


class ArgopackExperiment:
    """Controlled experiment for the argopack subprocess path.

    Research question:
        Is the subprocess path in argopack.py actually reachable as a
        consequential authority escape?
    """

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.recorder = RuntimeTraceRecorder(
            experiment_id="argopack_subprocess",
            scope="controlled_local",
        )
        self.results: dict[str, Any] = {}

    def run(self) -> dict[str, Any]:
        """Run the full argopack experiment."""
        print("=" * 70)
        print("ARGOPACK SUBPROCESS EXPERIMENT")
        print("=" * 70)

        # Phase 1: Static analysis
        print("\n[Phase 1] Static analysis of argopack.py...")
        static_result = self._analyze_argopack_static()
        print(f"  Subprocess calls found: {static_result['subprocess_calls']}")
        print(f"  Capability verification: {static_result['has_capability']}")
        print(f"  Authorization derivation: {static_result['has_authorization']}")
        print(f"  Provenance recording: {static_result['has_provenance']}")

        # Phase 2: Runtime trace
        print("\n[Phase 2] Runtime trace of subprocess invocation...")
        runtime_result = self._trace_subprocess_invocation()
        print(f"  Events recorded: {runtime_result['events_recorded']}")
        print(f"  Subprocess events: {runtime_result['subprocess_events']}")
        print(f"  Capability events: {runtime_result['capability_events']}")
        print(f"  Authorization events: {runtime_result['authorization_events']}")

        # Phase 3: Authority reconstruction
        print("\n[Phase 3] Authority reconstruction...")
        reconstruction = self._reconstruct_authority()
        print(f"  Reconstruction state: {reconstruction['state']}")
        print(f"  Capability present: {reconstruction['capability_present']}")
        print(f"  Authorization present: {reconstruction['authorization_present']}")
        print(f"  Provenance present: {reconstruction['provenance_present']}")

        # Phase 4: Classification
        print("\n[Phase 4] Classification...")
        classification = self._classify_path(reconstruction)
        print(f"  Classification: {classification['classification']}")
        print(f"  Confidence: {classification['confidence']}")
        print(f"  Epistemic state: {classification['epistemic_state']}")

        self.results = {
            "static_analysis": static_result,
            "runtime_trace": runtime_result,
            "authority_reconstruction": reconstruction,
            "classification": classification,
        }

        return self.results

    def _analyze_argopack_static(self) -> dict:
        """Analyze argopack.py statically."""
        argopack_path = self.repo_root / "src" / "sas" / "argopack.py"
        content = argopack_path.read_text()

        # Count subprocess calls
        subprocess_calls = len(re.findall(r"subprocess\.run\s*\(", content))

        # Check for capability/authorization/provenance
        has_capability = "capability" in content.lower() or "CapabilityVerifier" in content
        has_authorization = "authorization" in content.lower() or "AuthorizationArtifact" in content
        has_provenance = "provenance" in content.lower() or "ProvenanceRecord" in content

        return {
            "subprocess_calls": subprocess_calls,
            "has_capability": has_capability,
            "has_authorization": has_authorization,
            "has_provenance": has_provenance,
            "file": str(argopack_path.relative_to(self.repo_root)),
        }

    def _trace_subprocess_invocation(self) -> dict:
        """Trace the actual subprocess invocation.

        Phase 26 Remediation:
            Uses SubprocessInstrument instead of raw subprocess.run.
            OBSERVATION != AUTHORIZATION.
            INSTRUMENTATION != AUTHORITY.
            The instrument makes subprocess observable, not authorized.
            Subprocess execution still requires capability verification.
        """
        self.recorder.start()

        # Create SubprocessInstrument for observation
        from research.examples.self_audit.runtime_trace import SubprocessInstrument
        instrument = SubprocessInstrument(self.recorder)

        # Record the invocation attempt
        event = self.recorder.record_event(
            actor="argopack_experiment",
            component="argopack.py",
            operation="invoke",
            resource="sas.cli",
            consequence_type=ConsequenceType.EXTERNAL_CONSEQUENTIAL,
            event_type=RuntimeEventType.SUBPROCESS_CREATION,
            result="attempting",
            authority_context={
                "experiment": "argopack_subprocess",
                "controlled": True,
                "local": True,
                "instrumented": True,
            },
            scope="controlled_local",
            limitations="Runtime observation only - not authorization. Instrument makes observable, not authorized.",
        )

        if event:
            self.recorder.push_call(event.event_id)

        try:
            # Actually invoke the subprocess through SubprocessInstrument
            import sys
            cmd = [sys.executable, "-m", "sas", "--help"]
            result = instrument.run(
                cmd,
                actor="argopack_experiment",
                component="subprocess.run",
                consequence_type=ConsequenceType.INFORMATIONAL,
                authority_context={
                    "command": " ".join(cmd),
                    "experiment": "argopack_subprocess",
                    "instrumented": True,
                    "note": "OBSERVATION != AUTHORIZATION",
                },
                scope="controlled_local",
                limitations="Subprocess executed in controlled environment via instrument",
            )

        except Exception as e:
            self.recorder.record_event(
                actor="argopack_experiment",
                component="subprocess.run",
                operation="execute",
                resource="python -m sas --help",
                consequence_type=ConsequenceType.INFORMATIONAL,
                event_type=RuntimeEventType.SUBPROCESS_CREATION,
                result=f"error={str(e)}",
                scope="controlled_local",
                limitations="Subprocess execution failed",
            )

        if event:
            self.recorder.pop_call()

        self.recorder.stop()

        return {
            "events_recorded": len(self.recorder.events),
            "subprocess_events": len(self.recorder.get_subprocess_events()),
            "capability_events": len(self.recorder.get_capability_events()),
            "authorization_events": len(self.recorder.get_authorization_events()),
        }

    def _reconstruct_authority(self) -> dict:
        """Attempt to reconstruct the authority chain."""
        capability_events = self.recorder.get_capability_events()
        authorization_events = self.recorder.get_authorization_events()
        provenance_events = self.recorder.get_events_by_type(RuntimeEventType.PROVENANCE_CREATION)

        if capability_events and authorization_events and provenance_events:
            state = ReconstructionState.AUTHORIZED_AND_RECONSTRUCTIBLE
        elif capability_events or authorization_events:
            state = ReconstructionState.AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE
        else:
            state = ReconstructionState.UNAUTHORIZED

        return {
            "state": state.value,
            "capability_present": len(capability_events) > 0,
            "authorization_present": len(authorization_events) > 0,
            "provenance_present": len(provenance_events) > 0,
            "total_events": len(self.recorder.events),
        }

    def _classify_path(self, reconstruction: dict) -> dict:
        """Classify the argopack subprocess path."""
        state = reconstruction["state"]

        if state == ReconstructionState.AUTHORIZED_AND_RECONSTRUCTIBLE:
            classification = AuthorityClassification.AUTHORITY_CONTROLLED
            confidence = 0.85
            epistemic = EpistemicState.AUTHORIZED
        elif state == ReconstructionState.AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE:
            classification = AuthorityClassification.AUTHORITY_CONTROLLED
            confidence = 0.65
            epistemic = EpistemicState.AUTHORIZED
        elif state == ReconstructionState.UNAUTHORIZED:
            # Check if this is actually consequential
            has_external = any(
                e.consequence_type == ConsequenceType.EXTERNAL_CONSEQUENTIAL
                for e in self.recorder.events
            )
            if has_external:
                classification = AuthorityClassification.AUTHORITY_ESCAPE
                confidence = 0.75
                epistemic = EpistemicState.UNAUTHORIZED
            else:
                classification = AuthorityClassification.STATIC_FALSE_POSITIVE
                confidence = 0.7
                epistemic = EpistemicState.OBSERVED
        else:
            classification = AuthorityClassification.INCONCLUSIVE
            confidence = 0.5
            epistemic = EpistemicState.INCONCLUSIVE

        return {
            "classification": classification.value,
            "confidence": confidence,
            "epistemic_state": epistemic.value,
        }


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def run_runtime_topology_experiment(repo_root: str | Path) -> dict:
    """Run the full runtime authority topology experiment."""
    repo_root = Path(repo_root)

    print("=" * 70)
    print("RUNTIME AUTHORITY TOPOLOGY EXPERIMENT")
    print("=" * 70)

    # Phase 1: Build static authority graph
    print("\n[Phase 1] Building static authority graph...")
    graph_builder = StaticAuthorityGraphBuilder(repo_root)
    hypotheses = graph_builder.build_graph()
    print(f"  Static hypotheses: {len(hypotheses)}")

    # Phase 2: Run argopack experiment
    print("\n[Phase 2] Running argopack experiment...")
    argopack_exp = ArgopackExperiment(repo_root)
    argopack_results = argopack_exp.run()

    # Phase 3: Reconcile
    print("\n[Phase 3] Reconciling static vs runtime...")
    reconciliation_engine = ReconciliationEngine(
        hypotheses=hypotheses,
        runtime_events=argopack_exp.recorder.events,
    )
    reconciliation_results = reconciliation_engine.reconcile()
    print(f"  Reconciliations: {len(reconciliation_results)}")

    # Phase 4: Generate report
    print("\n[Phase 4] Generating report...")
    report = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "repository": str(repo_root),
            "experiment": "runtime_authority_topology",
        },
        "static_graph": graph_builder.to_dict(),
        "argopack_experiment": argopack_results,
        "reconciliation": reconciliation_engine.to_dict(),
    }

    return report


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    report = run_runtime_topology_experiment(repo)

    # Save report
    output_path = Path(repo) / "examples" / "self_audit" / "artifacts" / "runtime_topology_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {output_path}")
