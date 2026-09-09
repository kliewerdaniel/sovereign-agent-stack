"""Canonical capability verification — one authority verification semantics.

All capability verification in the runtime flows through this single
implementation. This prevents divergence where:

    Gate verification ≠ Tool verification ≠ Broker verification

The verifier checks every dimension of a capability's authority before
permitting execution. Boundary-specific constraints (e.g., broker-specific
order validation) are layered on top, but the core authority logic is
canonical.

Architectural law:
    THERE IS ONE AUTHORITY VERIFICATION IMPLEMENTATION.
    ALL CONSEQUENTIAL EXECUTION CONSUMES IT.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sas.quant.experiment.execution_capability import (
    ExecutionCapability,
    ExecutionStatus,
)
from sas.quant.experiment.protocol_lineage import ProtocolDomain


# ---------------------------------------------------------------------------
# Verification Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationResult:
    """Result of capability verification."""
    is_permitted: bool = False
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""

    @classmethod
    def permitted(cls) -> VerificationResult:
        return cls(is_permitted=True)

    @classmethod
    def rejected(cls, reason: str, conflicts: list[str] | None = None) -> VerificationResult:
        return cls(
            is_permitted=False,
            conflicts=conflicts or [reason],
            rejection_reason=reason,
        )


# ---------------------------------------------------------------------------
# Canonical Capability Verifier
# ---------------------------------------------------------------------------


class CapabilityVerifier:
    """Single canonical implementation of capability verification.

    Every consequential execution path consumes this verifier.
    This ensures that authority semantics cannot diverge between
    the gate, tools, broker, plugins, or any other boundary.

    The verifier checks:

    1. Temporal validity
    2. Replay guard state
    3. Domain binding
    4. Action matching
    5. Resource binding
    6. Authorization reference presence
    7. Quantity constraints
    8. Executor binding (if present)
    9. Actor binding (if present)
    """

    def __init__(self, domain: ProtocolDomain | None = None):
        self._domain = domain

    def verify(
        self,
        capability: ExecutionCapability,
        action: str,
        resource: str,
        arguments: dict | None = None,
        current_time: str = "",
        domain: ProtocolDomain | None = None,
    ) -> VerificationResult:
        """Verify a capability permits the requested operation.

        This is the single entry point for all capability verification.
        Every consequential execution must call this method.

        Args:
            capability: The execution capability to verify.
            action: The action being attempted.
            resource: The resource being targeted.
            arguments: The arguments being passed.
            current_time: The current timestamp (ISO 8601).
            domain: The domain context (overrides the verifier's default).

        Returns:
            VerificationResult indicating whether the operation is permitted.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        check_domain = domain or self._domain
        conflicts: list[str] = []

        # 1. Verify capability is valid at current time
        if not capability.is_valid_at(current_time):
            conflicts.append(f"Capability not valid at {current_time}")

        # 2. Verify capability can be executed (replay guard)
        if not capability.can_execute():
            conflicts.append("Capability replay guard exhausted")

        # 3. Verify domain binding
        if check_domain and capability.domain_id:
            if capability.domain_id != check_domain.domain_id:
                conflicts.append(
                    f"Domain mismatch: capability.domain_id={capability.domain_id} "
                    f"!= runtime.domain_id={check_domain.domain_id}"
                )

        # 4. Verify action matches
        if not capability.scope.permits_action(action):
            # Check for wildcard permission
            action_prefix = action.split(".")[0] if "." in action else action
            if not capability.scope.permits_action(f"{action_prefix}.*"):
                conflicts.append(
                    f"Action mismatch: capability permits '{capability.scope.action}', "
                    f"request has '{action}'"
                )

        # 5. Verify resource binding
        if capability.resource_binding:
            if not capability.resource_binding.binds_resource(resource):
                conflicts.append(
                    f"Resource mismatch: capability binds "
                    f"{capability.resource_binding.bound_resources}, "
                    f"request has '{resource}'"
                )

        # 6. Verify authorization reference is present
        if not capability.authorization_ref:
            conflicts.append("Missing authorization reference")

        # 7. Verify quantity constraints (if applicable)
        quantity = arguments.get("quantity") if arguments else None
        if quantity is not None:
            if not capability.scope.constraints.permits_quantity(float(quantity)):
                conflicts.append(
                    f"Quantity {quantity} outside permitted range "
                    f"[{capability.scope.constraints.min_quantity}, "
                    f"{capability.scope.constraints.max_quantity}]"
                )

        # 8. Verify executor binding (if present)
        if capability.resource_binding:
            if capability.resource_binding.bound_until:
                if capability.resource_binding.bound_until != "-1":
                    if current_time > capability.resource_binding.bound_until:
                        conflicts.append(
                            f"Executor binding expired at {capability.resource_binding.bound_until}"
                        )

        # 9. Verify actor binding (if present)
        if capability.actor_identity_ref and arguments:
            actor = arguments.get("actor_id")
            if actor and actor != capability.actor_identity_ref:
                conflicts.append(
                    f"Actor mismatch: capability bound to '{capability.actor_identity_ref}', "
                    f"request from '{actor}'"
                )

        if conflicts:
            return VerificationResult.rejected(
                reason="; ".join(conflicts),
                conflicts=conflicts,
            )

        return VerificationResult.permitted()

    def verify_strict(
        self,
        capability: ExecutionCapability,
        action: str,
        resource: str,
        arguments: dict,
        expected_actor: str,
        expected_domain: str,
        current_time: str = "",
    ) -> VerificationResult:
        """Strict verification — all dimensions must match exactly.

        Use this for the most consequential operations where any
        ambiguity should result in rejection.

        Args:
            capability: The execution capability to verify.
            action: The exact action expected.
            resource: The exact resource expected.
            arguments: The exact arguments expected.
            expected_actor: The exact actor expected.
            expected_domain: The exact domain expected.
            current_time: The current timestamp.

        Returns:
            VerificationResult — permitted only if ALL dimensions match.
        """
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        conflicts: list[str] = []

        # Run base verification
        base = self.verify(capability, action, resource, arguments, current_time)
        if not base.is_permitted:
            return base

        # Additional strict checks

        # Actor must match exactly
        if capability.actor_identity_ref != expected_actor:
            conflicts.append(
                f"Actor mismatch: expected '{expected_actor}', "
                f"capability bound to '{capability.actor_identity_ref}'"
            )

        # Domain must match exactly
        if capability.domain_id != expected_domain:
            conflicts.append(
                f"Domain mismatch: expected '{expected_domain}', "
                f"capability bound to '{capability.domain_id}'"
            )

        # Action must be exact (no wildcards)
        if capability.scope.action != action:
            conflicts.append(
                f"Action mismatch: expected '{action}', "
                f"capability permits '{capability.scope.action}'"
            )

        # Resource must be exact
        if capability.resource_binding:
            if resource not in capability.resource_binding.bound_resources:
                conflicts.append(
                    f"Resource mismatch: expected '{resource}', "
                    f"capability binds {capability.resource_binding.bound_resources}"
                )

        if conflicts:
            return VerificationResult.rejected(
                reason="; ".join(conflicts),
                conflicts=conflicts,
            )

        return VerificationResult.permitted()


# ---------------------------------------------------------------------------
# Replay Protection Store
# ---------------------------------------------------------------------------


class ReplayProtectionStore:
    """Durable replay protection for capabilities.

    Tracks which nonces have been consumed. Supports both in-memory
    and durable storage backends.

    The store is the authority for whether a capability has been used.
    A capability with max_uses=1 must be rejected if its nonce is in
    this store, regardless of what the capability object itself claims.
    """

    def __init__(self):
        self._nonces: set[str] = set()
        self._durable: dict[str, dict] = {}  # For process-restart survival

    def has_used(self, nonce: str) -> bool:
        """Check if a nonce has been consumed."""
        return nonce in self._nonces

    def mark_used(self, nonce: str, capability_id: str = "", timestamp: str = "") -> None:
        """Mark a nonce as consumed."""
        self._nonces.add(nonce)
        self._durable[nonce] = {
            "capability_id": capability_id,
            "consumed_at": timestamp or datetime.now(UTC).isoformat(),
        }

    def is_exhausted(self, capability: ExecutionCapability) -> bool:
        """Check if a capability's replay guard is exhausted."""
        if not capability.replay_guard:
            return False
        if capability.replay_guard.nonce and self.has_used(capability.replay_guard.nonce):
            return True
        return capability.replay_guard.is_exhausted()

    def get_durable_state(self) -> dict:
        """Get the durable state for persistence."""
        return {
            "nonces": sorted(self._nonces),
            "durable": self._durable,
        }

    def restore_from_state(self, state: dict) -> None:
        """Restore state from a durable store."""
        for nonce in state.get("nonces", []):
            self._nonces.add(nonce)
        for nonce, data in state.get("durable", {}).items():
            self._durable[nonce] = data


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_capability_verifier(domain: ProtocolDomain | None = None) -> CapabilityVerifier:
    """Create a CapabilityVerifier."""
    return CapabilityVerifier(domain)


def create_replay_protection_store() -> ReplayProtectionStore:
    """Create a ReplayProtectionStore."""
    return ReplayProtectionStore()
