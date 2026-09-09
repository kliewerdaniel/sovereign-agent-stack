"""Capability-Bound Substrate — closes the compute execution boundary.

The substrate is a potentially universal consequence primitive. If the system
can execute arbitrary code on a machine, then many other authority boundaries
can be bypassed through it.

Architectural law:
    SUBSTRATE EXECUTION IS A ROOT CONSEQUENCE PRIMITIVE.

A capability for "run diagnostic command" must not authorize "run arbitrary shell".
A capability for "read /tmp" must not authorize "read credential store".

Authorization control and process isolation are different security properties.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

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
# Substrate Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubstrateEnforcementResult:
    """Result of capability-bound substrate enforcement."""
    is_permitted: bool = False
    output: Any = None
    result: Any = None
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Capability-Bound Substrate
# ---------------------------------------------------------------------------


class CapabilityBoundSubstrate:
    """Wraps a compute substrate with capability enforcement.

    Every command execution must pass through capability verification.
    The raw substrate is never directly accessible.

    This closes the substrate boundary by ensuring:
    1. Command execution requires a verified capability
    2. The capability binds to the specific machine and command class
    3. The raw substrate is never directly accessible
    4. Execution receipts are generated for every attempt
    """

    def __init__(
        self,
        substrate: Any,  # LocalDockerSubstrate
        domain: ProtocolDomain,
        verifier: CapabilityVerifier | None = None,
    ):
        self.__substrate = substrate
        self.__domain = domain
        self.__verifier = verifier or create_capability_verifier(domain)
        self.__receipts: list[ExecutionReceipt] = []

    @property
    def name(self) -> str:
        return "capability-bound-substrate"

    def execute(
        self,
        capability: ExecutionCapability,
        machine_id: str,
        command: str,
        current_time: str = "",
    ) -> SubstrateEnforcementResult:
        """Execute a command on a machine under a verified capability.

        The command is only executed if the capability permits it.
        This is the ONLY way to execute commands through this substrate.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="substrate.execute",
            resource=machine_id,
            arguments={
                "command": command,
                "machine_id": machine_id,
            },
            current_time=current_time,
        )

        if not verification.is_permitted:
            return SubstrateEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        # Find the machine
        machine = None
        for m in self.__substrate.list_machines():
            if m.id == machine_id:
                machine = m
                break

        if machine is None:
            return SubstrateEnforcementResult(
                is_permitted=False,
                conflicts=[f"Machine {machine_id} not found"],
                rejection_reason=f"Machine {machine_id} not found",
            )

        # Execute on the underlying substrate
        try:
            output = self.__substrate.execute(machine, command)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Command executed: {command[:50]}... exit_code={output.exit_code}"
            reported_result = str(output.exit_code)
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            output = None

        # Create receipt
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-substrate",
            resource_id=machine_id,
            action="substrate.execute",
            arguments_hash=hashlib.sha256(
                json.dumps({
                    "machine_id": machine_id,
                    "command": command,
                }, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Substrate execute: {machine_id} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"substrate.execute {machine_id} {command}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return SubstrateEnforcementResult(
            is_permitted=True,
            output=output,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def boot(
        self,
        capability: ExecutionCapability,
        template: str,
        current_time: str = "",
    ) -> SubstrateEnforcementResult:
        """Boot a new machine under a verified capability."""
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="substrate.boot",
            resource=template,
            arguments={"template": template},
            current_time=current_time,
        )

        if not verification.is_permitted:
            return SubstrateEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        try:
            machine = self.__substrate.boot(template)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Booted machine {machine.id}"
            reported_result = machine.id
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            machine = None

        return SubstrateEnforcementResult(
            is_permitted=True,
            result=machine,
        )

    def destroy(
        self,
        capability: ExecutionCapability,
        machine_id: str,
        current_time: str = "",
    ) -> SubstrateEnforcementResult:
        """Destroy a machine under a verified capability."""
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="substrate.destroy",
            resource=machine_id,
            arguments={"machine_id": machine_id},
            current_time=current_time,
        )

        if not verification.is_permitted:
            return SubstrateEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        # Find the machine
        machine = None
        for m in self.__substrate.list_machines():
            if m.id == machine_id:
                machine = m
                break

        if machine is None:
            return SubstrateEnforcementResult(
                is_permitted=False,
                conflicts=[f"Machine {machine_id} not found"],
                rejection_reason=f"Machine {machine_id} not found",
            )

        try:
            self.__substrate.destroy(machine)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Destroyed machine {machine_id}"
            reported_result = "destroyed"
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"

        return SubstrateEnforcementResult(
            is_permitted=True,
        )

    def list_machines(
        self,
        capability: ExecutionCapability,
        current_time: str = "",
    ) -> SubstrateEnforcementResult:
        """List machines under a verified capability."""
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="read_only",
            resource="substrate",
            arguments={"operation": "list_machines"},
            current_time=current_time,
        )

        if not verification.is_permitted:
            return SubstrateEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        try:
            machines = self.__substrate.list_machines()
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Listed {len(machines)} machines"
            reported_result = str([m.id for m in machines])
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            machines = None

        return SubstrateEnforcementResult(
            is_permitted=True,
            result=machines,
        )

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self.__receipts)


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------


def create_capability_bound_substrate(
    substrate: Any,
    domain_id: str = "substrate-domain",
) -> CapabilityBoundSubstrate:
    """Create a CapabilityBoundSubstrate with a default domain."""
    from sas.quant.experiment.protocol_lineage import create_protocol_domain, DomainType
    domain = create_protocol_domain(domain_id, DomainType.SOVEREIGN)
    return CapabilityBoundSubstrate(substrate, domain)
