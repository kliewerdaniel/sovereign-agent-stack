"""Capability-Bound Tool — wraps tool execution with authority enforcement.

Every tool invocation must pass through capability verification.
The raw tool handler is never directly accessible to untrusted callers.

Architectural law:
    REGISTRATION IS DISCOVERABILITY.
    CAPABILITY IS AUTHORITY.
    THOSE MUST BE SEPARATE CONCEPTS.

This implementation uses the canonical CapabilityVerifier to ensure
authority semantics are identical across all boundaries.
"""

from __future__ import annotations

import hashlib
import json
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
# Tool Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolEnforcementResult:
    """Result of capability-bound tool enforcement."""
    is_permitted: bool = False
    result: Any = None
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Capability-Bound Tool
# ---------------------------------------------------------------------------


class CapabilityBoundTool:
    """Wraps a tool handler with capability enforcement.

    Every tool invocation must pass through capability verification.
    This makes it structurally impossible to invoke a tool without
    a verified execution capability.

    The tool handler is never directly accessible — it can only be
    invoked through the capability-bound interface.

    Uses the canonical CapabilityVerifier so that authority semantics
    are identical across all boundaries.
    """

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: dict | None = None,
        verifier: CapabilityVerifier | None = None,
    ):
        self.name = name
        self.description = description
        self.__handler = handler
        self.__parameters = parameters or {"type": "object", "properties": {}}
        self.__verifier = verifier
        self.__receipts: list[ExecutionReceipt] = []

    def invoke(
        self,
        capability: ExecutionCapability,
        arguments: dict,
        domain: ProtocolDomain,
        current_time: str = "",
    ) -> ToolEnforcementResult:
        """Invoke the tool with capability enforcement.

        The tool is only invoked if the capability permits it.
        This is the ONLY way to invoke the tool.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        tool_action = f"tool.{self.name}"

        # Use canonical verifier
        verifier = self.__verifier or create_capability_verifier(domain)
        verification = verifier.verify(
            capability=capability,
            action=tool_action,
            resource=self.name,
            arguments=arguments,
            current_time=current_time,
        )

        if not verification.is_permitted:
            return ToolEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        # Invoke the handler
        start_time = datetime.now(UTC).isoformat()
        try:
            result = self.__handler(**arguments)
            status = ExecutionStatus.COMPLETED
            observed_effect = str(result)
            reported_result = "completed"
        except Exception as e:
            result = None
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
            executor_id=f"tool-{self.name}",
            resource_id=self.name,
            action=tool_action,
            arguments_hash=hashlib.sha256(
                json.dumps(arguments, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=start_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Tool {self.name} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps(result, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"{tool_action} {arguments}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return ToolEnforcementResult(
            is_permitted=True,
            result=result,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    @property
    def parameters(self) -> dict:
        """Get the tool parameters."""
        return self.__parameters
