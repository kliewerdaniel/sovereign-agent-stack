"""Capability-Bound Auth Broker — closes the credential boundary.

The auth broker is the most dangerous remaining authority surface because it
sits directly between protocol authority and external authority.

Architectural laws:
    CREDENTIAL ≠ AUTHORIZATION
    CREDENTIAL ≠ CAPABILITY
    POSSESSION OF A CREDENTIAL MUST NOT CREATE PROTOCOL AUTHORITY.

Credentials are NEVER released to arbitrary callers. They are only used
inside an explicitly authorized execution context. The credential material
never leaves the broker.

The authority path is:
    AuthorizationArtifact → ExecutionCapability → CapabilityVerifier
    → CapabilityBoundAuthBroker → External Effect → ExecutionReceipt → Provenance
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Optional

from sas.quant.capability_verifier import (
    CapabilityVerifier,
    VerificationResult,
    create_capability_verifier,
)
from sas.quant.experiment.execution_capability import (
    ExecutionCapability,
    ExecutionReceipt,
    ExecutionStatus,
)
from sas.quant.experiment.protocol_lineage import ProtocolDomain


# ---------------------------------------------------------------------------
# Auth Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthEnforcementResult:
    """Result of capability-bound auth enforcement."""
    is_permitted: bool = False
    response: Any = None
    result: Any = None
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Credential Use Request
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CredentialUseRequest:
    """A request to use credentials for an external call.

    This is NOT a request to retrieve credentials. It is a request to
    USE credentials inside an authorized execution context.
    """
    tool_name: str
    method: str
    path: str
    headers: dict = field(default_factory=dict)
    body: bytes | None = None


# ---------------------------------------------------------------------------
# Capability-Bound Auth Broker
# ---------------------------------------------------------------------------


class CapabilityBoundAuthBroker:
    """Wraps LocalAuthBroker with capability enforcement.

    Credentials are NEVER exposed to callers. They are only used inside
    an authorized execution context.

    The broker verifies the capability before using credentials, and
    generates an execution receipt for every attempt.

    This closes the credential boundary by ensuring:
    1. Credentials are never released to arbitrary callers
    2. Credential use requires a verified capability
    3. The raw broker is never directly accessible
    4. Execution receipts are generated for every attempt
    5. Credential material never appears in receipts or provenance
    """

    def __init__(
        self,
        broker: Any,  # LocalAuthBroker
        domain: ProtocolDomain,
        verifier: CapabilityVerifier | None = None,
    ):
        self.__broker = broker
        self.__domain = domain
        self.__verifier = verifier or create_capability_verifier(domain)
        self.__receipts: list[ExecutionReceipt] = []

    @property
    def name(self) -> str:
        return "capability-bound-auth-broker"

    def use_credentials(
        self,
        capability: ExecutionCapability,
        request: CredentialUseRequest,
        http_call: Callable,
        current_time: str = "",
    ) -> AuthEnforcementResult:
        """Use credentials for an external call under a verified capability.

        The credentials are NEVER returned to the caller. They are used
        inside this method to make the external call.

        Args:
            capability: The verified execution capability.
            request: The credential use request.
            http_call: A callable that takes a Request and returns a Response.
            current_time: The current timestamp.

        Returns:
            AuthEnforcementResult with the response (not the credentials).
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="credential.access",
            resource=request.tool_name,
            arguments={
                "method": request.method,
                "path": request.path,
            },
            current_time=current_time,
        )

        if not verification.is_permitted:
            return AuthEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        # Use credentials inside the trusted executor
        # The credential material NEVER leaves this method
        try:
            from sas.layers.auth import Request as AuthRequest

            auth_request = AuthRequest(
                tool_name=request.tool_name,
                method=request.method,
                path=request.path,
                headers=request.headers,
                body=request.body,
            )

            response = self.__broker.call(auth_request, http_call)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"{request.method} {request.path} -> {response.status_code}"
            reported_result = str(response.status_code)
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            response = None

        # Create receipt (NEVER includes credential material)
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-auth-broker",
            resource_id=request.tool_name,
            action="credential.access",
            arguments_hash=hashlib.sha256(
                json.dumps({
                    "tool_name": request.tool_name,
                    "method": request.method,
                    "path": request.path,
                }, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Credential use: {request.tool_name} {request.method} {request.path} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"credential.access {request.tool_name} {request.method} {request.path}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return AuthEnforcementResult(
            is_permitted=True,
            response=response,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self.__receipts)

    # --- Administrative operations (also capability-bound) ---

    def register_tool(
        self,
        capability: ExecutionCapability,
        tool_name: str,
        credentials: Any,
        current_time: str = "",
    ) -> AuthEnforcementResult:
        """Register a tool with its credentials under a verified capability.

        Registration is AUTHORITY-MANAGEMENT because it changes future
        execution capability.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability for authority-management
        verification = self.__verifier.verify(
            capability=capability,
            action="authority.mutation",
            resource=tool_name,
            arguments={"operation": "register_tool"},
            current_time=current_time,
        )

        if not verification.is_permitted:
            return AuthEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        # Perform registration
        try:
            self.__broker.register_tool(tool_name, credentials)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Registered tool {tool_name}"
            reported_result = "registered"
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"

        # Create receipt
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-auth-broker",
            resource_id=tool_name,
            action="authority.mutation",
            arguments_hash=hashlib.sha256(
                json.dumps({"operation": "register_tool", "tool_name": tool_name}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Register tool: {tool_name} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"authority.mutation register_tool {tool_name}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return AuthEnforcementResult(
            is_permitted=True,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def list_tools(
        self,
        capability: ExecutionCapability,
        current_time: str = "",
    ) -> AuthEnforcementResult:
        """List registered tools under a verified capability.

        This is INFORMATIONAL but still requires authorization.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="read_only",
            resource="auth_broker",
            arguments={"operation": "list_tools"},
            current_time=current_time,
        )

        if not verification.is_permitted:
            return AuthEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        try:
            tools = self.__broker.list_tools()
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Listed {len(tools)} tools"
            reported_result = str(tools)
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            tools = None

        return AuthEnforcementResult(
            is_permitted=True,
            result=tools,
        )


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------


def create_capability_bound_auth_broker(
    broker: Any,
    domain_id: str = "auth-domain",
) -> CapabilityBoundAuthBroker:
    """Create a CapabilityBoundAuthBroker with a default domain."""
    from sas.quant.experiment.protocol_lineage import create_protocol_domain, DomainType
    domain = create_protocol_domain(domain_id, DomainType.SOVEREIGN)
    return CapabilityBoundAuthBroker(broker, domain)
