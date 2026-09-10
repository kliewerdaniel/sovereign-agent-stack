"""Capability-Bound Filesystem — closes the filesystem authority boundary.

The raw filesystem primitives (open, write, read) must NOT be directly
accessible to application code. Instead, all filesystem access must go
through the CapabilityBoundFilesystem, which enforces that every operation
has a verified execution capability.

Architectural law:
    THE FILESYSTEM IS A CONSEQUENTIAL AUTHORITY BOUNDARY.
    IT MUST NOT TRUST UPSTREAM CODE.

This wrapper enforces an already-established capability (not manufacture one).
It verifies scope, temporal bounds, and capability class before allowing
file operations. It preserves provenance (records what operation was performed,
by what authority). It fails closed (rejects if no valid capability).

The wrapper does NOT create authority. It only verifies and materializes
already-established authority from a capability.

Invariants:
    DIRECT PRIMITIVE ACCESS != GOVERNED EXECUTION
    CAPABILITY ≠ AUTHORITY
    GATE ≠ AUTHORITY ROOT
    OBSERVATION ≠ AUTHORIZATION
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
# Filesystem Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FilesystemEnforcementResult:
    """Result of capability-bound filesystem enforcement."""
    is_permitted: bool = False
    content: Any = None
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Capability-Bound Filesystem
# ---------------------------------------------------------------------------


class CapabilityBoundFilesystem:
    """Wraps filesystem operations with capability enforcement.

    Every file operation must pass through capability verification.
    The raw filesystem primitives are never directly accessible.

    This closes the filesystem boundary by ensuring:
    1. File operations require a verified capability
    2. The capability binds to the specific path and operation class
    3. The raw filesystem primitives are never directly accessible
    4. Execution receipts are generated for every attempt
    5. Provenance is preserved for every operation

    CRITICAL: This wrapper does NOT create authority. It only verifies
    and materializes already-established authority from a capability.
    """

    def __init__(
        self,
        domain: ProtocolDomain,
        verifier: CapabilityVerifier | None = None,
    ):
        self.__domain = domain
        self.__verifier = verifier or create_capability_verifier(domain)
        self.__receipts: list[ExecutionReceipt] = []

    @property
    def name(self) -> str:
        return "capability-bound-filesystem"

    def write(
        self,
        capability: ExecutionCapability,
        path: str,
        content: str,
        current_time: str = "",
    ) -> FilesystemEnforcementResult:
        """Write to a file under a verified capability.

        The write is only performed if the capability permits it.
        This is the ONLY way to write files through this wrapper.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="filesystem.write",
            resource=path,
            arguments={"path": path, "content_length": len(content)},
            current_time=current_time,
        )

        if not verification.is_permitted:
            receipt = self._create_rejected_receipt(
                capability, path, "filesystem.write", verification, current_time
            )
            return FilesystemEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
                receipt=receipt,
            )

        # Perform the write
        try:
            from pathlib import Path as FsPath
            FsPath(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"File written: {path} ({len(content)} bytes)"
            reported_result = "written"
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
            executor_id="capability-bound-filesystem",
            resource_id=path,
            action="filesystem.write",
            arguments_hash=hashlib.sha256(
                json.dumps(
                    {"path": path, "content_length": len(content)},
                    sort_keys=True,
                    default=str,
                ).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Filesystem write: {path} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"filesystem.write {path}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return FilesystemEnforcementResult(
            is_permitted=True,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def read(
        self,
        capability: ExecutionCapability,
        path: str,
        current_time: str = "",
    ) -> FilesystemEnforcementResult:
        """Read from a file under a verified capability.

        The read is only performed if the capability permits it.
        This is the ONLY way to read files through this wrapper.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="filesystem.read",
            resource=path,
            arguments={"path": path},
            current_time=current_time,
        )

        if not verification.is_permitted:
            receipt = self._create_rejected_receipt(
                capability, path, "filesystem.read", verification, current_time
            )
            return FilesystemEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
                receipt=receipt,
            )

        # Perform the read
        try:
            with open(path, "r") as f:
                content = f.read()
            status = ExecutionStatus.COMPLETED
            observed_effect=f"File read: {path} ({len(content)} bytes)"
            reported_result = f"read {len(content)} bytes"
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            content = None

        # Create receipt
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-filesystem",
            resource_id=path,
            action="filesystem.read",
            arguments_hash=hashlib.sha256(
                json.dumps({"path": path}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Filesystem read: {path} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"filesystem.read {path}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return FilesystemEnforcementResult(
            is_permitted=True,
            content=content,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self.__receipts)

    def _create_rejected_receipt(
        self,
        capability: ExecutionCapability,
        resource: str,
        action: str,
        verification: VerificationResult,
        current_time: str,
    ) -> ExecutionReceipt:
        """Create a receipt for a rejected operation."""
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-filesystem",
            resource_id=resource,
            action=action,
            arguments_hash="",
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"REJECTED: {'; '.join(verification.conflicts)}",
            status=ExecutionStatus.REJECTED,
            intended_effect=f"{action} {resource}",
            observed_effect="rejected",
            reported_result="rejected",
            provenance_hash=capability.compute_hash(),
        )
        self.__receipts.append(receipt)
        return receipt


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------


def create_capability_bound_filesystem(
    domain_id: str = "filesystem-domain",
) -> CapabilityBoundFilesystem:
    """Create a CapabilityBoundFilesystem with a default domain."""
    from sas.quant.experiment.protocol_lineage import create_protocol_domain, DomainType
    domain = create_protocol_domain(domain_id, DomainType.SOVEREIGN)
    return CapabilityBoundFilesystem(domain)
