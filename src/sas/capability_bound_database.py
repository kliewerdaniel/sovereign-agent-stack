"""Capability-Bound Database — closes the database authority boundary.

The raw database primitives (sqlite3.connect, execute, etc.) must NOT be
directly accessible to application code. Instead, all database access must
go through the CapabilityBoundDatabase, which enforces that every operation
has a verified execution capability.

Architectural law:
    THE DATABASE IS A CONSEQUENTIAL AUTHORITY BOUNDARY.
    IT MUST NOT TRUST UPSTREAM CODE.

This wrapper enforces an already-established capability (not manufacture one).
It verifies scope, temporal bounds, and capability class before allowing
database operations. It preserves provenance (records what operation was
performed, by what authority). It fails closed (rejects if no valid capability).

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
# Database Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DatabaseEnforcementResult:
    """Result of capability-bound database enforcement."""
    is_permitted: bool = False
    rows: list[Any] = field(default_factory=list)
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Capability-Bound Database
# ---------------------------------------------------------------------------


class CapabilityBoundDatabase:
    """Wraps database operations with capability enforcement.

    Every database operation must pass through capability verification.
    The raw database primitives are never directly accessible.

    This closes the database boundary by ensuring:
    1. Database operations require a verified capability
    2. The capability binds to the specific database and operation class
    3. The raw database primitives are never directly accessible
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
        return "capability-bound-database"

    def connect(
        self,
        capability: ExecutionCapability,
        db_path: str,
        current_time: str = "",
    ) -> DatabaseEnforcementResult:
        """Connect to a database under a verified capability.

        The connection is only established if the capability permits it.
        This is the ONLY way to connect to databases through this wrapper.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action="database.connect",
            resource=db_path,
            arguments={"db_path": db_path},
            current_time=current_time,
        )

        if not verification.is_permitted:
            receipt = self._create_rejected_receipt(
                capability, db_path, "database.connect", verification, current_time
            )
            return DatabaseEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
                receipt=receipt,
            )

        # Establish the connection
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            status = ExecutionStatus.COMPLETED
            observed_effect=f"Database connected: {db_path}"
            reported_result = "connected"
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            conn = None

        # Create receipt
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-database",
            resource_id=db_path,
            action="database.connect",
            arguments_hash=hashlib.sha256(
                json.dumps({"db_path": db_path}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Database connect: {db_path} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"database.connect {db_path}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        if conn is not None:
            conn.close()

        return DatabaseEnforcementResult(
            is_permitted=True,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def execute(
        self,
        capability: ExecutionCapability,
        db_path: str,
        sql: str,
        parameters: tuple = (),
        current_time: str = "",
    ) -> DatabaseEnforcementResult:
        """Execute a SQL statement under a verified capability.

        The execution is only performed if the capability permits it.
        This is the ONLY way to execute SQL through this wrapper.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        # Determine action type based on SQL
        action = "database.write" if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP")) else "database.read"

        # Verify capability
        verification = self.__verifier.verify(
            capability=capability,
            action=action,
            resource=db_path,
            arguments={"db_path": db_path, "sql": sql[:200]},  # Truncate SQL for hash
            current_time=current_time,
        )

        if not verification.is_permitted:
            receipt = self._create_rejected_receipt(
                capability, db_path, action, verification, current_time
            )
            return DatabaseEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
                receipt=receipt,
            )

        # Execute the SQL
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(sql, parameters)
            conn.commit()
            rows = cursor.fetchall()
            conn.close()
            status = ExecutionStatus.COMPLETED
            observed_effect=f"SQL executed on {db_path}: {len(rows)} rows"
            reported_result = f"{len(rows)} rows"
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"
            rows = []

        # Create receipt
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=capability.scope.actor_id,
            executor_id="capability-bound-database",
            resource_id=db_path,
            action=action,
            arguments_hash=hashlib.sha256(
                json.dumps(
                    {"db_path": db_path, "sql": sql[:200], "parameters": str(parameters)},
                    sort_keys=True,
                    default=str,
                ).encode()
            ).hexdigest()[:16],
            start_time=current_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Database execute: {db_path} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps({"status": reported_result, "row_count": len(rows)}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            status=status,
            intended_effect=f"{action} {db_path}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self.__receipts.append(receipt)

        return DatabaseEnforcementResult(
            is_permitted=True,
            rows=rows,
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
            executor_id="capability-bound-database",
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


def create_capability_bound_database(
    domain_id: str = "database-domain",
) -> CapabilityBoundDatabase:
    """Create a CapabilityBoundDatabase with a default domain."""
    from sas.quant.experiment.protocol_lineage import create_protocol_domain, DomainType
    domain = create_protocol_domain(domain_id, DomainType.SOVEREIGN)
    return CapabilityBoundDatabase(domain)
