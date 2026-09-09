"""Capability-Bound Tool — wraps tool execution with authority enforcement.

Every tool invocation must pass through capability verification.
The raw tool handler is never directly accessible to untrusted callers.

Architectural law:
    REGISTRATION IS DISCOVERABILITY.
    CAPABILITY IS AUTHORITY.
    THOSE MUST BE SEPARATE CONCEPTS.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Optional

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
    """

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: dict | None = None,
    ):
        self.name = name
        self.description = description
        self._handler = handler
        self._parameters = parameters or {"type": "object", "properties": {}}
        self._receipts: list[ExecutionReceipt] = []

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

        conflicts: list[str] = []

        # 1. Verify capability is valid at current time
        if not capability.is_valid_at(current_time):
            conflicts.append(f"Capability not valid at {current_time}")

        # 2. Verify capability can be executed (replay guard)
        if not capability.can_execute():
            conflicts.append("Capability replay guard exhausted")

        # 3. Verify domain binding
        if capability.domain_id and capability.domain_id != domain.domain_id:
            conflicts.append(
                f"Domain mismatch: capability.domain_id={capability.domain_id} "
                f"!= tool.domain_id={domain.domain_id}"
            )

        # 4. Verify action matches
        tool_action = f"tool.{self.name}"
        if not capability.scope.permits_action(tool_action):
            # Also check for wildcard "tool.*" permission
            if not capability.scope.permits_action("tool.*"):
                conflicts.append(
                    f"Action mismatch: capability permits '{capability.scope.action}', "
                    f"tool requires '{tool_action}'"
                )

        # 5. Verify nonce hasn't been used (replay protection)
        # Note: We don't track nonces here; the gate does that

        # 6. Verify authorization reference is present
        if not capability.authorization_ref:
            conflicts.append("Missing authorization reference")

        if conflicts:
            return ToolEnforcementResult(
                is_permitted=False,
                conflicts=conflicts,
                rejection_reason="; ".join(conflicts),
            )

        # Invoke the handler
        start_time = datetime.now(UTC).isoformat()
        try:
            result = self._handler(**arguments)
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

        self._receipts.append(receipt)

        return ToolEnforcementResult(
            is_permitted=True,
            result=result,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self._receipts)
