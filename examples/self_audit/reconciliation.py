"""Static-Dynamic Reconciliation Engine.

Reconciles static authority hypotheses against runtime trace observations.
Produces a reconciliation graph classifying each edge as:
- STATIC_ONLY: Predicted but not observed at runtime
- RUNTIME_ONLY: Observed but not predicted
- STATIC_AND_RUNTIME: Predicted and observed
- STATIC_FALSE_POSITIVE: Predicted but not actually consequential
- RUNTIME_UNEXPECTED: Observed but not predicted
- AUTHORITY_CONTROLLED: Observed with reconstructible authority
- AUTHORITY_ESCAPE: Observed without authority
- INCONCLUSIVE: Cannot be determined
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ReconciliationClassification(str, Enum):
    """Classification of a reconciled edge."""
    STATIC_ONLY = "static_only"
    RUNTIME_ONLY = "runtime_only"
    STATIC_AND_RUNTIME = "static_and_runtime"
    STATIC_FALSE_POSITIVE = "static_false_positive"
    RUNTIME_UNEXPECTED = "runtime_unexpected"
    AUTHORITY_CONTROLLED = "authority_controlled"
    AUTHORITY_ESCAPE = "authority_escape"
    INCONCLUSIVE = "inconclusive"


class EpistemicState(str, Enum):
    """Epistemic state of a reconciliation."""
    UNKNOWN = "unknown"
    INCONCLUSIVE = "inconclusive"
    OBSERVED = "observed"
    SUPPORTED = "supported"
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"


class ReconstructionState(str, Enum):
    """State of authority reconstruction."""
    AUTHORIZED_AND_RECONSTRUCTIBLE = "authorized_and_reconstructible"
    AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE = "authorized_but_not_reconstructible"
    UNAUTHORIZED = "unauthorized"
    NON_CONSEQUENTIAL = "non_consequential"
    INSUFFICIENT_TRACE = "insufficient_trace"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class StaticHypothesis:
    """A predicted authority edge from static analysis."""

    hypothesis_id: str
    source: str
    target: str
    operation: str
    consequence_type: str
    static_evidence: str
    expected_authority_boundary: str
    expected_capability: str
    expected_authorization: str
    expected_provenance: str
    predicted_classification: str
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
            "consequence_type": self.consequence_type,
            "static_evidence": self.static_evidence,
            "expected_authority_boundary": self.expected_authority_boundary,
            "expected_capability": self.expected_capability,
            "expected_authorization": self.expected_authorization,
            "expected_provenance": self.expected_provenance,
            "predicted_classification": self.predicted_classification,
            "confidence": self.confidence,
            "source_location": self.source_location,
            "target_location": self.target_location,
            "alternatives": self.alternatives,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RuntimeEvent:
    """A runtime observation."""

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


@dataclass(frozen=True)
class ReconciliationResult:
    """Result of reconciling a static hypothesis against runtime traces."""

    reconciliation_id: str
    hypothesis: StaticHypothesis
    classification: ReconciliationClassification
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


@dataclass(frozen=True)
class AuthorityGraphEdge:
    """An edge in the authority graph."""

    edge_id: str
    source: str
    target: str
    operation: str
    consequence_type: str
    authority_state: str
    capability_id: Optional[str]
    authorization_id: Optional[str]
    provenance_id: Optional[str]
    evidence: str
    limitations: str

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "operation": self.operation,
            "consequence_type": self.consequence_type,
            "authority_state": self.authority_state,
            "capability_id": self.capability_id,
            "authorization_id": self.authorization_id,
            "provenance_id": self.provenance_id,
            "evidence": self.evidence,
            "limitations": self.limitations,
        }


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
        matching_events = self._find_matching_events(hypothesis)

        if not matching_events:
            return self._handle_no_runtime_evidence(hypothesis, matching_events)

        return self._handle_runtime_evidence(hypothesis, matching_events)

    def _handle_no_runtime_evidence(
        self,
        hypothesis: StaticHypothesis,
        matching_events: list[RuntimeEvent],
    ) -> ReconciliationResult:
        """Handle case where no runtime events match the hypothesis."""
        if hypothesis.consequence_type == "state_transforming":
            classification = ReconciliationClassification.STATIC_FALSE_POSITIVE
            confidence = 0.7
            epistemic = EpistemicState.OBSERVED
            limitations = "Internal state management, not external consequence"
        else:
            classification = ReconciliationClassification.STATIC_ONLY
            confidence = 0.6
            epistemic = EpistemicState.INCONCLUSIVE
            limitations = "Runtime experiment did not exercise this path"

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
            limitations=limitations,
        )

    def _handle_runtime_evidence(
        self,
        hypothesis: StaticHypothesis,
        matching_events: list[RuntimeEvent],
    ) -> ReconciliationResult:
        """Handle case where runtime events match the hypothesis."""
        has_capability = any(e.capability_id for e in matching_events)
        has_authorization = any(e.authorization_id for e in matching_events)
        has_provenance = any(e.provenance_id for e in matching_events)
        has_external_consequence = any(
            e.consequence_type == "external_consequential"
            for e in matching_events
        )

        authority_reconstruction = self._reconstruct_authority(matching_events)

        if has_external_consequence:
            if has_capability and has_authorization and has_provenance:
                classification = ReconciliationClassification.AUTHORITY_CONTROLLED
                confidence = 0.85
                epistemic = EpistemicState.AUTHORIZED
            elif has_capability or has_authorization:
                classification = ReconciliationClassification.AUTHORITY_CONTROLLED
                confidence = 0.65
                epistemic = EpistemicState.AUTHORIZED
            else:
                classification = ReconciliationClassification.AUTHORITY_ESCAPE
                confidence = 0.75
                epistemic = EpistemicState.UNAUTHORIZED
        else:
            if has_capability or has_authorization:
                classification = ReconciliationClassification.AUTHORITY_CONTROLLED
                confidence = 0.7
                epistemic = EpistemicState.AUTHORIZED
            else:
                classification = ReconciliationClassification.STATIC_FALSE_POSITIVE
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
            if self._events_match(hypothesis, event):
                matching.append(event)
        return matching

    def _events_match(self, hypothesis: StaticHypothesis, event: RuntimeEvent) -> bool:
        """Check if a runtime event matches a static hypothesis."""
        if hypothesis.operation == "subprocess_execution" and event.event_type in ("subprocess_create", "subprocess_complete"):
            return True
        if hypothesis.operation == "network_mutation" and event.event_type in ("network_request", "network_response"):
            return True
        if hypothesis.operation == "filesystem_mutation" and event.event_type in ("filesystem_read", "filesystem_write"):
            return True
        if hypothesis.operation == "broker_call" and event.event_type in ("broker_call", "broker_response"):
            return True
        if hypothesis.operation == "dynamic_import" and event.event_type == "dynamic_import":
            return True
        return False

    def _reconstruct_authority(self, events: list[RuntimeEvent]) -> dict[str, Any]:
        """Attempt to reconstruct the authority chain from runtime events."""
        if not events:
            return {"state": ReconstructionState.INSUFFICIENT_TRACE}

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
        """Convert to dictionary."""
        classification_counts = {}
        for r in self.results:
            cls = r.classification.value
            classification_counts[cls] = classification_counts.get(cls, 0) + 1

        epistemic_counts = {}
        for r in self.results:
            state = r.epistemic_state.value
            epistemic_counts[state] = epistemic_counts.get(state, 0) + 1

        return {
            "total_reconciliations": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "by_classification": classification_counts,
                "by_epistemic_state": epistemic_counts,
            },
        }


class TraceBasedAuthorityGraph:
    """Constructs a runtime authority graph from execution traces.

    Distinguishes:
    - CALL GRAPH (who calls whom)
    - CONSEQUENCE GRAPH (what causes external effects)
    - AUTHORITY GRAPH (what authorizes what)
    - PROVENANCE GRAPH (what records lineage)
    """

    def __init__(self, runtime_events: list[RuntimeEvent]):
        self.events = runtime_events
        self.call_edges: list[AuthorityGraphEdge] = []
        self.consequence_edges: list[AuthorityGraphEdge] = []
        self.authority_edges: list[AuthorityGraphEdge] = []
        self.provenance_edges: list[AuthorityGraphEdge] = []

    def build_graphs(self) -> dict[str, list[AuthorityGraphEdge]]:
        """Build all four graph types."""
        self._build_call_graph()
        self._build_consequence_graph()
        self._build_authority_graph()
        self._build_provenance_graph()
        return {
            "call_graph": self.call_edges,
            "consequence_graph": self.consequence_edges,
            "authority_graph": self.authority_edges,
            "provenance_graph": self.provenance_edges,
        }

    def _build_call_graph(self):
        """Build the call graph from runtime events."""
        for event in self.events:
            if event.parent_event:
                self.call_edges.append(AuthorityGraphEdge(
                    edge_id=f"call_{event.event_id}",
                    source=event.parent_event,
                    target=event.event_id,
                    operation=event.operation,
                    consequence_type=event.consequence_type,
                    authority_state="call",
                    capability_id=event.capability_id,
                    authorization_id=event.authorization_id,
                    provenance_id=event.provenance_id,
                    evidence=f"Runtime observation: {event.operation}",
                    limitations="Call graph shows invocation, not authorization",
                ))

    def _build_consequence_graph(self):
        """Build the consequence graph from runtime events."""
        for event in self.events:
            if event.consequence_type in ("external_consequential", "authority_management"):
                self.consequence_edges.append(AuthorityGraphEdge(
                    edge_id=f"cons_{event.event_id}",
                    source=event.actor,
                    target=event.resource,
                    operation=event.operation,
                    consequence_type=event.consequence_type,
                    authority_state="consequence",
                    capability_id=event.capability_id,
                    authorization_id=event.authorization_id,
                    provenance_id=event.provenance_id,
                    evidence=f"Consequential effect observed: {event.operation}",
                    limitations="Consequence graph shows effect, not authorization",
                ))

    def _build_authority_graph(self):
        """Build the authority graph from runtime events."""
        for event in self.events:
            if event.capability_id or event.authorization_id:
                self.authority_edges.append(AuthorityGraphEdge(
                    edge_id=f"auth_{event.event_id}",
                    source=event.actor,
                    target=event.resource,
                    operation=event.operation,
                    consequence_type=event.consequence_type,
                    authority_state="authorized" if (event.capability_id and event.authorization_id) else "partial",
                    capability_id=event.capability_id,
                    authorization_id=event.authorization_id,
                    provenance_id=event.provenance_id,
                    evidence=f"Authority observed: capability={event.capability_id}, authorization={event.authorization_id}",
                    limitations="Authority graph shows observed authority, not complete chain",
                ))

    def _build_provenance_graph(self):
        """Build the provenance graph from runtime events."""
        for event in self.events:
            if event.provenance_id:
                self.provenance_edges.append(AuthorityGraphEdge(
                    edge_id=f"prov_{event.event_id}",
                    source=event.actor,
                    target=event.resource,
                    operation=event.operation,
                    consequence_type=event.consequence_type,
                    authority_state="provenanced",
                    capability_id=event.capability_id,
                    authorization_id=event.authorization_id,
                    provenance_id=event.provenance_id,
                    evidence=f"Provenance recorded: {event.provenance_id}",
                    limitations="Provenance graph shows recording, not authorization",
                ))

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "call_graph": [e.to_dict() for e in self.call_edges],
            "consequence_graph": [e.to_dict() for e in self.consequence_edges],
            "authority_graph": [e.to_dict() for e in self.authority_edges],
            "provenance_graph": [e.to_dict() for e in self.provenance_edges],
            "summary": {
                "call_edges": len(self.call_edges),
                "consequence_edges": len(self.consequence_edges),
                "authority_edges": len(self.authority_edges),
                "provenance_edges": len(self.provenance_edges),
            },
        }


class RuntimeAuthorityReconstructor:
    """Reconstructs authority chains for runtime events.

    For every consequential runtime event, attempts to reconstruct:
    SOVEREIGN_ROOT → POLICY → ACTOR → GOVERNANCE → AUTHORIZATION → CAPABILITY → EXECUTION → EFFECT → RECEIPT → PROVENANCE
    """

    def __init__(self, runtime_events: list[RuntimeEvent]):
        self.events = runtime_events
        self.reconstructions: list[dict[str, Any]] = []

    def reconstruct_all(self) -> list[dict[str, Any]]:
        """Reconstruct authority for all consequential events."""
        self.reconstructions = []

        for event in self.events:
            if event.consequence_type in ("external_consequential", "authority_management"):
                reconstruction = self._reconstruct_event(event)
                self.reconstructions.append(reconstruction)

        return self.reconstructions

    def _reconstruct_event(self, event: RuntimeEvent) -> dict[str, Any]:
        """Reconstruct authority chain for a single event."""
        chain: dict[str, Any] = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "actor": event.actor,
            "operation": event.operation,
            "resource": event.resource,
            "consequence_type": event.consequence_type,
        }

        # Check each link in the chain
        chain["sovereign_root"] = {
            "present": False,
            "evidence": "No sovereign root established",
        }

        chain["policy"] = {
            "present": False,
            "evidence": "No governance policy consulted",
        }

        chain["actor"] = {
            "present": True,
            "evidence": event.actor,
        }

        chain["governance"] = {
            "present": False,
            "evidence": "No governance decision recorded",
        }

        chain["authorization"] = {
            "present": event.authorization_id is not None,
            "evidence": event.authorization_id or "No authorization derived",
        }

        chain["capability"] = {
            "present": event.capability_id is not None,
            "evidence": event.capability_id or "No capability verified",
        }

        chain["execution"] = {
            "present": True,
            "evidence": f"{event.operation} → {event.result}",
        }

        chain["effect"] = {
            "present": True,
            "evidence": f"Consequence type: {event.consequence_type}",
        }

        chain["receipt"] = {
            "present": False,
            "evidence": "No execution receipt produced",
        }

        chain["provenance"] = {
            "present": event.provenance_id is not None,
            "evidence": event.provenance_id or "No provenance recorded",
        }

        # Determine overall state
        chain["reconstruction_state"] = self._determine_state(chain)
        chain["missing_links"] = self._find_missing_links(chain)

        return chain

    def _determine_state(self, chain: dict[str, Any]) -> str:
        """Determine the overall reconstruction state."""
        has_authorization = chain["authorization"]["present"]
        has_capability = chain["capability"]["present"]
        has_provenance = chain["provenance"]["present"]
        has_governance = chain["governance"]["present"]

        if has_authorization and has_capability and has_provenance and has_governance:
            return ReconstructionState.AUTHORIZED_AND_RECONSTRUCTIBLE
        elif has_authorization or has_capability:
            return ReconstructionState.AUTHORIZED_BUT_NOT_RECONSTRUCTIBLE
        else:
            return ReconstructionState.UNAUTHORIZED

    def _find_missing_links(self, chain: dict[str, Any]) -> list[str]:
        """Find missing links in the authority chain."""
        missing = []
        for key in ["sovereign_root", "policy", "governance", "authorization", "capability", "receipt", "provenance"]:
            if not chain[key]["present"]:
                missing.append(key)
        return missing

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_reconstructions": len(self.reconstructions),
            "reconstructions": self.reconstructions,
            "summary": {
                "by_state": self._count_by_state(),
                "total_missing_links": sum(
                    len(r.get("missing_links", []))
                    for r in self.reconstructions
                ),
            },
        }

    def _count_by_state(self) -> dict:
        counts = {}
        for r in self.reconstructions:
            state = r.get("reconstruction_state", "unknown")
            counts[state] = counts.get(state, 0) + 1
        return counts
