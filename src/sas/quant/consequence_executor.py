"""Consequence Executor Protocol — the unified interface for all bounded execution.

Every consequential operation in SAS must ultimately flow through this protocol.
Whether the effect is a trade, payment, identity mutation, filesystem mutation,
process execution, network request, or tool invocation — the authority
semantics are identical.

Architectural law:
    CONSEQUENTIALITY IS A PROTOCOL PROPERTY, NOT A SUBSYSTEM PROPERTY.

This protocol is the boundary between the authority framework and the
implementation-specific executors. It ensures that no subsystem can
invent its own authority semantics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from sas.quant.capability_verifier import VerificationResult
from sas.quant.experiment.execution_capability import (
    ExecutionCapability,
    ExecutionReceipt,
)
from sas.quant.experiment.protocol_lineage import ProtocolDomain


# ---------------------------------------------------------------------------
# Consequence Request
# ---------------------------------------------------------------------------


class ConsequenceRequest:
    """A request to perform a consequential operation.

    This is the unified request type for all consequential operations
    across every subsystem. It carries all the information needed to
    resolve authorization, materialize capability, and verify bounds.

    Subsystems may extend this with additional fields, but the core
    authority fields must always be present.
    """

    def __init__(
        self,
        action: str,
        resource: str,
        arguments: dict | None = None,
        actor_id: str = "",
        domain: ProtocolDomain | None = None,
        source: str = "",
    ):
        self.action = action
        self.resource = resource
        self.arguments = arguments or {}
        self.actor_id = actor_id
        self.domain = domain
        self.source = source


# ---------------------------------------------------------------------------
# Consequence Result
# ---------------------------------------------------------------------------


class ConsequenceResult:
    """Result of a consequential operation.

    Every consequential execution produces a result that includes:
    - Whether the operation was permitted
    - The execution receipt (for provenance)
    - Any conflicts that caused rejection
    """

    def __init__(
        self,
        is_permitted: bool = False,
        receipt: ExecutionReceipt | None = None,
        conflicts: list[str] | None = None,
        rejection_reason: str = "",
        result: Any = None,
    ):
        self.is_permitted = is_permitted
        self.receipt = receipt
        self.conflicts = conflicts or []
        self.rejection_reason = rejection_reason
        self.result = result


# ---------------------------------------------------------------------------
# Consequence Executor Protocol
# ---------------------------------------------------------------------------


class ConsequenceExecutor(ABC):
    """Protocol for all bounded consequence executors.

    Every subsystem that produces consequential effects must implement
    this protocol. The protocol ensures that:

    1. Capability verification is canonical (via CapabilityVerifier)
    2. Execution receipts are generated for every attempt
    3. The raw executor is never directly accessible
    4. Authority semantics are identical across subsystems

    Implementations include:
    - CapabilityBoundBroker (quant trading)
    - CapabilityBoundTool (agent tools)
    - CapabilityBoundPayment (payments) [future]
    - CapabilityBoundIdentity (identity) [future]
    - CapabilityBoundSubstrate (compute) [future]
    """

    @abstractmethod
    def execute(
        self,
        capability: ExecutionCapability,
        request: ConsequenceRequest,
        current_time: str = "",
    ) -> ConsequenceResult:
        """Execute a consequential operation under a verified capability.

        The operation is only executed if the capability permits it.
        Returns a ConsequenceResult regardless of success or failure.

        Args:
            capability: The verified execution capability.
            request: The consequence request.
            current_time: The current timestamp (ISO 8601).

        Returns:
            ConsequenceResult indicating success or failure.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this executor."""
        ...

    def verify_capability(
        self,
        capability: ExecutionCapability,
        request: ConsequenceRequest,
        current_time: str = "",
    ) -> VerificationResult:
        """Verify a capability permits the requested operation.

        Uses the canonical CapabilityVerifier to ensure authority
        semantics are identical across all subsystems.

        Args:
            capability: The execution capability to verify.
            request: The consequence request.
            current_time: The current timestamp.

        Returns:
            VerificationResult indicating whether the operation is permitted.
        """
        from sas.quant.capability_verifier import CapabilityVerifier

        verifier = CapabilityVerifier(request.domain)
        return verifier.verify(
            capability=capability,
            action=request.action,
            resource=request.resource,
            arguments=request.arguments,
            current_time=current_time,
        )


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_consequence_request(
    action: str,
    resource: str,
    arguments: dict | None = None,
    actor_id: str = "",
    domain: ProtocolDomain | None = None,
    source: str = "",
) -> ConsequenceRequest:
    """Create a ConsequenceRequest."""
    return ConsequenceRequest(
        action=action,
        resource=resource,
        arguments=arguments,
        actor_id=actor_id,
        domain=domain,
        source=source,
    )
