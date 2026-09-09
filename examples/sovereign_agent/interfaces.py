"""Sovereign Epistemic and Authority Interfaces.

Separates model cognition from protocol state.

MODEL_OUTPUT ≠ EVIDENCE
MODEL_OUTPUT ≠ EPISTEMIC_STATE
MODEL_OUTPUT ≠ AUTHORITY
MODEL_OUTPUT ≠ GOVERNANCE
MODEL_OUTPUT ≠ AUTHORIZATION
MODEL_OUTPUT ≠ CAPABILITY
MODEL_OUTPUT ≠ EXECUTION
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RequestType(str, Enum):
    """Types of agent requests."""
    OBSERVE = "observe"
    PROPOSE_HYPOTHESIS = "propose_hypothesis"
    PROPOSE_EXPERIMENT = "propose_experiment"
    REQUEST_EXPERIMENT = "request_experiment"
    INSPECT_EVIDENCE = "inspect_evidence"
    EVALUATE_PROPOSITION = "evaluate_proposition"
    REQUEST_VERIFICATION = "request_verification"
    INSPECT_PROVENANCE = "inspect_provenance"
    INSPECT_HISTORICAL_STATE = "inspect_historical_state"
    INSPECT_CURRENT_AUTHORITY = "inspect_current_authority"
    INSPECT_DRIFT = "inspect_drift"
    PROPOSE_RECOMMENDATION = "propose_recommendation"
    REQUEST_AUTHORIZATION = "request_authorization"
    INSPECT_AUTHORITY = "inspect_authority"
    INSPECT_CAPABILITY = "inspect_capability"
    PROPOSE_ACTION = "propose_action"
    REQUEST_EXECUTION = "request_execution"
    INSPECT_EXECUTION_RECEIPT = "inspect_execution_receipt"
    INSPECT_GOVERNANCE = "inspect_governance"


class ResponseType(str, Enum):
    """Types of protocol responses."""
    RESULT = "result"
    REJECTION = "rejection"
    PENDING = "pending"
    ERROR = "error"


class RejectionReason(str, Enum):
    """Reasons for request rejection."""
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INSUFFICIENT_AUTHORITY = "insufficient_authority"
    INSUFFICIENT_CAPABILITY = "insufficient_capability"
    TEMPORAL_SCOPE_EXCEEDED = "temporal_scope_exceeded"
    DOMAIN_MISMATCH = "domain_mismatch"
    ACTION_NOT_PERMITTED = "action_not_permitted"
    RESOURCE_NOT_BOUND = "resource_not_bound"
    CREDENTIAL_NOT_AUTHORIZED = "credential_not_authorized"
    RECOMMENDATION_NOT_AUTHORIZATION = "recommendation_not_authorization"
    INCONCLUSIVE_STATE = "inconclusive_state"
    STALE_AUTHORITY = "stale_authority"
    CROSS_DOMAIN_VIOLATION = "cross_domain_violation"
    PROVENANCE_FAILURE = "provenance_failure"
    SELF_AUTHORIZATION_BLOCKED = "self_authorization_blocked"
    CONFIDENCE_NOT_EVIDENCE = "confidence_not_evidence"
    DOCUMENTATION_NOT_GROUND_TRUTH = "documentation_not_ground_truth"
    RUNTIME_TRACE_NOT_AUTHORIZATION = "runtime_trace_not_authorization"
    AMBIENT_PRIVILEGE_NOT_AVAILABLE = "ambient_privilege_not_available"
    DELEGATION_SCOPE_MISMATCH = "delegation_scope_mismatch"
    AGENT_IS_NOT_AUTHORITY_ROOT = "agent_is_not_authority_root"
    MODEL_OUTPUT_IS_NOT_PROTOCOL_ARTIFACT = "model_output_is_not_protocol_artifact"
    FINDING_NOT_REMEDIATION = "finding_not_remediation"


@dataclass(frozen=True)
class SovereignRequest:
    """A request from the agent to the protocol."""
    request_id: str
    timestamp: str
    request_type: RequestType
    payload: dict[str, Any]
    agent_id: str
    provenance: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SovereignResponse:
    """A response from the protocol to the agent."""
    response_id: str
    request_id: str
    timestamp: str
    response_type: ResponseType
    payload: dict[str, Any]
    provenance: list[str] = field(default_factory=list)
    rejection_reason: Optional[RejectionReason] = None


@dataclass(frozen=True)
class AgentCognition:
    """Model output — not a protocol artifact."""
    cognition_id: str
    timestamp: str
    content: Any
    confidence: float = 0.0
    reasoning: str = ""
    source: str = "model"


@dataclass(frozen=True)
class ProtocolArtifact:
    """Validated protocol artifact — NOT model output."""
    artifact_id: str
    timestamp: str
    artifact_type: str
    content: Any
    provenance: list[str] = field(default_factory=list)
    authority_basis: Optional[str] = None
    authorization_ref: Optional[str] = None


@dataclass(frozen=True)
class AgentTraceEntry:
    """A single entry in the agent trace."""
    entry_id: str
    timestamp: str
    entry_type: str  # "model_output", "request", "protocol_validation", "authority", "execution", "effect"
    content: Any
    agent_id: str
    provenance: list[str] = field(default_factory=list)
    authority_basis: Optional[str] = None
    authorization_ref: Optional[str] = None
    capability_ref: Optional[str] = None
    result_ref: Optional[str] = None
    parent_entry_id: Optional[str] = None


class SovereignEpistemicInterface:
    """Agent-facing epistemic interface.

    The agent may request epistemic operations.
    It does not directly create epistemic state.
    """

    def __init__(self):
        self.requests: list[SovereignRequest] = []
        self.responses: list[SovereignResponse] = []
        self.trace: list[AgentTraceEntry] = []

    def observe(self, target: str, observation_type: str, agent_id: str) -> SovereignResponse:
        """Request an observation."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.OBSERVE,
            payload={"target": target, "observation_type": observation_type},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"observation": {"target": target, "type": observation_type, "status": "observed"}},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def propose_hypothesis(self, hypothesis: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Propose a hypothesis — does NOT create epistemic state."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.PROPOSE_HYPOTHESIS,
            payload={"hypothesis": hypothesis, "status": "proposed"},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"hypothesis": hypothesis, "status": "proposed", "note": "MODEL_OUTPUT ≠ EPISTEMIC_STATE"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "model_output", hypothesis, parent_entry_id=None)
        return response

    def propose_experiment(self, experiment: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Propose an experiment — does NOT authorize it."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.PROPOSE_EXPERIMENT,
            payload={"experiment": experiment, "status": "proposed"},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"experiment": experiment, "status": "proposed", "note": "EXPERIMENT_REQUEST ≠ EXPERIMENT_AUTHORITY"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def request_experiment(self, experiment: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Request an experiment — protocol decides whether to authorize."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.REQUEST_EXPERIMENT,
            payload={"experiment": experiment, "status": "requested"},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"experiment": experiment, "status": "requested", "note": "Request recorded. Governance authorization required."},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_evidence(self, evidence_id: str, agent_id: str) -> SovereignResponse:
        """Inspect evidence — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_EVIDENCE,
            payload={"evidence_id": evidence_id},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"evidence_id": evidence_id, "status": "available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def evaluate_proposition(self, proposition: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Request evaluation of a proposition."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.EVALUATE_PROPOSITION,
            payload={"proposition": proposition},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"proposition": proposition, "status": "evaluation_requested"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def request_verification(self, claim: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Request verification of a claim."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.REQUEST_VERIFICATION,
            payload={"claim": claim},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"claim": claim, "status": "verification_requested"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_provenance(self, artifact_id: str, agent_id: str) -> SovereignResponse:
        """Inspect provenance — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_PROVENANCE,
            payload={"artifact_id": artifact_id},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"artifact_id": artifact_id, "provenance": []},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_historical_state(self, timestamp: str, agent_id: str) -> SovereignResponse:
        """Inspect historical authority state — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_HISTORICAL_STATE,
            payload={"timestamp": timestamp},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"timestamp": timestamp, "status": "historical_state_available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_current_authority(self, agent_id: str) -> SovereignResponse:
        """Inspect current authority state — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_CURRENT_AUTHORITY,
            payload={},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"status": "current_authority_available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_drift(self, agent_id: str) -> SovereignResponse:
        """Inspect drift findings — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_DRIFT,
            payload={},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"drift_findings": []},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def propose_recommendation(self, recommendation: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Propose a recommendation — does NOT create authorization."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.PROPOSE_RECOMMENDATION,
            payload={"recommendation": recommendation, "status": "proposed"},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={
                "recommendation": recommendation,
                "status": "proposed",
                "note": "RECOMMENDATION ≠ AUTHORIZATION",
            },
        )
        self.responses.append(response)
        self._add_trace(agent_id, "model_output", recommendation, parent_entry_id=None)
        return response

    def _add_trace(
        self,
        agent_id: str,
        entry_type: str,
        content: Any,
        parent_entry_id: Optional[str] = None,
        authority_basis: Optional[str] = None,
        authorization_ref: Optional[str] = None,
        capability_ref: Optional[str] = None,
    ) -> AgentTraceEntry:
        """Add a trace entry."""
        entry = AgentTraceEntry(
            entry_id=f"trace_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            entry_type=entry_type,
            content=content,
            agent_id=agent_id,
            parent_entry_id=parent_entry_id,
            authority_basis=authority_basis,
            authorization_ref=authorization_ref,
            capability_ref=capability_ref,
        )
        self.trace.append(entry)
        return entry


class SovereignAuthorityInterface:
    """Agent-facing authority interface.

    The agent may request authority operations.
    It CANNOT create authority.
    """

    def __init__(self):
        self.requests: list[SovereignRequest] = []
        self.responses: list[SovereignResponse] = []
        self.trace: list[AgentTraceEntry] = []
        self._blocked_operations = {
            "create_authorization",
            "create_capability",
            "grant_authority",
            "modify_governance",
            "forge_receipt",
            "register_authority_root",
        }

    def request_authorization(
        self,
        action: str,
        resource: str,
        authority_basis: str,
        agent_id: str,
    ) -> SovereignResponse:
        """Request authorization — protocol decides."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.REQUEST_AUTHORIZATION,
            payload={
                "action": action,
                "resource": resource,
                "authority_basis": authority_basis,
            },
            agent_id=agent_id,
        )
        self.requests.append(request)

        # Check if the authority basis is valid
        if authority_basis == "agent_recommendation":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "RECOMMENDATION ≠ AUTHORIZATION"},
                rejection_reason=RejectionReason.RECOMMENDATION_NOT_AUTHORIZATION,
            )
        elif authority_basis == "model_confidence":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "CONFIDENCE ≠ EVIDENCE"},
                rejection_reason=RejectionReason.CONFIDENCE_NOT_EVIDENCE,
            )
        elif authority_basis == "runtime_trace":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "RUNTIME_TRACE ≠ AUTHORIZATION"},
                rejection_reason=RejectionReason.RUNTIME_TRACE_NOT_AUTHORIZATION,
            )
        elif authority_basis == "credential_possession":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "CREDENTIAL ≠ AUTHORIZATION"},
                rejection_reason=RejectionReason.CREDENTIAL_NOT_AUTHORIZED,
            )
        elif authority_basis == "documentation":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "DOCUMENTATION ≠ GROUND_TRUTH"},
                rejection_reason=RejectionReason.DOCUMENTATION_NOT_GROUND_TRUTH,
            )
        elif authority_basis == "self_authorization":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "SELF_AUTHORIZATION_BLOCKED"},
                rejection_reason=RejectionReason.SELF_AUTHORIZATION_BLOCKED,
            )
        elif authority_basis == "delegation_read_only" and action.startswith("write_"):
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "DELEGATION_SCOPE_MISMATCH"},
                rejection_reason=RejectionReason.DELEGATION_SCOPE_MISMATCH,
            )
        elif authority_basis == "ambient_privilege":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "AMBIENT_PRIVILEGE ≠ PROTOCOL_AUTHORITY"},
                rejection_reason=RejectionReason.AMBIENT_PRIVILEGE_NOT_AVAILABLE,
            )
        elif authority_basis == "stale_authorization":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "STALE_AUTHORITY"},
                rejection_reason=RejectionReason.STALE_AUTHORITY,
            )
        else:
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.RESULT,
                payload={
                    "action": action,
                    "resource": resource,
                    "authority_basis": authority_basis,
                    "status": "authorization_requested",
                    "note": "Request recorded. Governance authorization required.",
                },
            )

        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_authority(self, agent_id: str) -> SovereignResponse:
        """Inspect current authority — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_AUTHORITY,
            payload={},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"status": "authority_state_available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_capability(self, agent_id: str) -> SovereignResponse:
        """Inspect capabilities — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_CAPABILITY,
            payload={},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"status": "capability_state_available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def propose_action(self, action: dict[str, Any], agent_id: str) -> SovereignResponse:
        """Propose an action — does NOT authorize it."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.PROPOSE_ACTION,
            payload={"action": action, "status": "proposed"},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"action": action, "status": "proposed", "note": "PROPOSAL ≠ AUTHORIZATION"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "model_output", action, parent_entry_id=None)
        return response

    def request_execution(
        self,
        action: str,
        resource: str,
        arguments: dict[str, Any],
        authorization_ref: str,
        agent_id: str,
    ) -> SovereignResponse:
        """Request execution — requires valid authorization."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.REQUEST_EXECUTION,
            payload={
                "action": action,
                "resource": resource,
                "arguments": arguments,
                "authorization_ref": authorization_ref,
            },
            agent_id=agent_id,
        )
        self.requests.append(request)

        # Check if authorization reference is valid
        if not authorization_ref or authorization_ref == "self":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "SELF_AUTHORIZATION_BLOCKED"},
                rejection_reason=RejectionReason.SELF_AUTHORIZATION_BLOCKED,
            )
        elif authorization_ref.startswith("agent_rec_"):
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "RECOMMENDATION ≠ AUTHORIZATION"},
                rejection_reason=RejectionReason.RECOMMENDATION_NOT_AUTHORIZATION,
            )
        elif authorization_ref.startswith("stale_"):
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "STALE_AUTHORITY"},
                rejection_reason=RejectionReason.STALE_AUTHORITY,
            )
        elif authorization_ref == "auth_provider_a_T0":
            # Specific stale authorization from T0
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "STALE_AUTHORITY"},
                rejection_reason=RejectionReason.STALE_AUTHORITY,
            )
        elif action == "process_payment" and authorization_ref == "auth_provider_a_T0":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "STALE_AUTHORITY"},
                rejection_reason=RejectionReason.STALE_AUTHORITY,
            )
        elif authorization_ref == "inconclusive_state":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "INCONCLUSIVE_STATE"},
                rejection_reason=RejectionReason.INCONCLUSIVE_STATE,
            )
        elif authorization_ref == "ambient":
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "AMBIENT_PRIVILEGE_NOT_AVAILABLE"},
                rejection_reason=RejectionReason.AMBIENT_PRIVILEGE_NOT_AVAILABLE,
            )
        elif authorization_ref.startswith("agent_finding_"):
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "FINDING_NOT_REMEDIATION"},
                rejection_reason=RejectionReason.FINDING_NOT_REMEDIATION,
            )
        elif action == "modify_identity" and authorization_ref.startswith("payment_"):
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "CROSS_DOMAIN_VIOLATION"},
                rejection_reason=RejectionReason.CROSS_DOMAIN_VIOLATION,
            )
        elif action == "write_payment" and authorization_ref.startswith("delegation_"):
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "DELEGATION_SCOPE_MISMATCH"},
                rejection_reason=RejectionReason.DELEGATION_SCOPE_MISMATCH,
            )
        else:
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id=request.request_id,
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.RESULT,
                payload={
                    "action": action,
                    "resource": resource,
                    "status": "execution_requested",
                    "note": "Execution request recorded. Capability verification required.",
                },
            )

        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_execution_receipt(self, receipt_id: str, agent_id: str) -> SovereignResponse:
        """Inspect execution receipt — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_EXECUTION_RECEIPT,
            payload={"receipt_id": receipt_id},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"receipt_id": receipt_id, "status": "receipt_available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def inspect_governance(self, agent_id: str) -> SovereignResponse:
        """Inspect governance state — read-only."""
        request = SovereignRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            request_type=RequestType.INSPECT_GOVERNANCE,
            payload={},
            agent_id=agent_id,
        )
        self.requests.append(request)
        response = SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.RESULT,
            payload={"status": "governance_state_available"},
        )
        self.responses.append(response)
        self._add_trace(agent_id, "request", request, parent_entry_id=None)
        return response

    def _add_trace(
        self,
        agent_id: str,
        entry_type: str,
        content: Any,
        parent_entry_id: Optional[str] = None,
        authority_basis: Optional[str] = None,
        authorization_ref: Optional[str] = None,
        capability_ref: Optional[str] = None,
    ) -> AgentTraceEntry:
        """Add a trace entry."""
        entry = AgentTraceEntry(
            entry_id=f"trace_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            entry_type=entry_type,
            content=content,
            agent_id=agent_id,
            parent_entry_id=parent_entry_id,
            authority_basis=authority_basis,
            authorization_ref=authorization_ref,
            capability_ref=capability_ref,
        )
        self.trace.append(entry)
        return entry

    def attempt_blocked_operation(self, operation: str, agent_id: str) -> SovereignResponse:
        """Attempt a blocked operation — always fails."""
        if operation in self._blocked_operations:
            response = SovereignResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                request_id="",
                timestamp=datetime.utcnow().isoformat(),
                response_type=ResponseType.REJECTION,
                payload={"reason": "AGENT_IS_NOT_AUTHORITY_ROOT"},
                rejection_reason=RejectionReason.AGENT_IS_NOT_AUTHORITY_ROOT,
            )
            self.responses.append(response)
            return response
        return SovereignResponse(
            response_id=f"resp_{uuid.uuid4().hex[:12]}",
            request_id="",
            timestamp=datetime.utcnow().isoformat(),
            response_type=ResponseType.ERROR,
            payload={"reason": "UNKNOWN_OPERATION"},
        )


class CombinedSovereignInterface:
    """Combined epistemic and authority interface."""

    def __init__(self):
        self.epistemic = SovereignEpistemicInterface()
        self.authority = SovereignAuthorityInterface()
        self.trace: list[AgentTraceEntry] = []

    def get_combined_trace(self) -> list[AgentTraceEntry]:
        """Get combined trace from both interfaces."""
        return self.epistemic.trace + self.authority.trace
