"""Runtime Authority Gate — the single enforcement point.

Every consequential runtime operation must pass through this gate.
The gate resolves authorization, verifies capability, constructs
execution context, and returns a bounded executor.

Architectural law:
    THE RUNTIME MAY MATERIALIZE AUTHORITY, BUT IT MUST NEVER CREATE AUTHORITY.

This module is the bridge between the formal protocol and the actual runtime.
It ensures that the runtime cannot perform any consequential action without
a reconstructible authority path from sovereign root to external effect.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Optional

from sas.quant.experiment.epistemic_governance import (
    AuthorizationArtifact,
    AuthorizationStatus,
)
from sas.quant.experiment.execution_capability import (
    BindingType,
    CapabilityConstraints,
    CapabilityMaterializer,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutionReceipt,
    ExecutionStatus,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)


# ---------------------------------------------------------------------------
# Operation Request
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OperationRequest:
    """A request to perform a consequential operation.

    This is the untrusted input from any runtime component.
    It does NOT carry authority — authority is derived by the gate.
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    action: str = ""  # e.g., "execute_trade", "read_file", "run_command"
    resource: str = ""  # e.g., "AAPL", "/path/to/file", "docker"
    arguments: dict = field(default_factory=dict)
    actor_id: str = ""
    domain_id: str = ""
    requested_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: str = ""  # e.g., "agent", "argo", "plugin", "cli", "orchestrator"


# ---------------------------------------------------------------------------
# Authority Resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthorityResolution:
    """Result of resolving an authorization for an operation.

    Contains the verified authorization artifact and the materialized
    execution capability. If resolution fails, `is_valid` is False
    and `rejection_reason` explains why.
    """
    is_valid: bool = False
    authorization: Optional[AuthorizationArtifact] = None
    capability: Optional[ExecutionCapability] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Runtime Authority Gate
# ---------------------------------------------------------------------------


class RuntimeAuthorityGate:
    """Single enforcement point where all runtime authority decisions are made.

    Every consequential runtime operation must pass through this gate.
    The gate is responsible for:

    1. Resolving the relevant authorization
    2. Verifying the authorization
    3. Verifying domain/lineage
    4. Verifying temporal validity
    5. Verifying actor identity
    6. Verifying policy
    7. Verifying capability scope
    8. Verifying resource identity
    9. Verifying replay state
    10. Constructing ExecutionContext
    11. Returning a bounded executor/capability
    12. Producing execution provenance

    The gate does NOT execute operations. It returns a `BoundedExecutor`
    that CAN execute them. This separation ensures that execution is
    impossible without first passing through the gate.
    """

    def __init__(
        self,
        domain: ProtocolDomain,
        materializer: CapabilityMaterializer | None = None,
    ):
        self.domain = domain
        self._materializer = materializer or CapabilityMaterializer(domain)
        self._executed_nonces: set[str] = set()
        self._sequence_counter: int = 0
        self._receipts: list[ExecutionReceipt] = []
        self._authorizations: dict[str, AuthorizationArtifact] = {}

    # -------------------------------------------------------------------
    # Authorization Registry
    # -------------------------------------------------------------------

    def register_authorization(self, auth: AuthorizationArtifact) -> None:
        """Register an authorization artifact for later resolution."""
        self._authorizations[auth.authorization_id] = auth

    def get_authorization(self, auth_id: str) -> AuthorizationArtifact | None:
        """Retrieve a registered authorization."""
        return self._authorizations.get(auth_id)

    # -------------------------------------------------------------------
    # Authority Resolution
    # -------------------------------------------------------------------

    def resolve(
        self,
        request: OperationRequest,
        authorization_id: str,
    ) -> AuthorityResolution:
        """Resolve an authorization for an operation request.

        This is the core enforcement method. It:
        1. Looks up the authorization
        2. Verifies the authorization is valid
        3. Verifies the request matches the authorization scope
        4. Materializes an execution capability
        5. Returns the resolution

        If any step fails, the resolution is invalid and the operation
        cannot proceed.
        """
        conflicts: list[str] = []

        # 1. Look up authorization
        auth = self._authorizations.get(authorization_id)
        if auth is None:
            return AuthorityResolution(
                is_valid=False,
                rejection_reason=f"Authorization {authorization_id} not found",
            )

        # 2. Verify authorization status
        if auth.status != AuthorizationStatus.AUTHORIZED:
            conflicts.append(f"Authorization status is '{auth.status}', not 'authorized'")

        # 3. Verify temporal validity
        now = request.requested_at
        if auth.expiration and now > auth.expiration:
            conflicts.append(f"Authorization expired at {auth.expiration}")

        # 4. Verify domain compatibility
        if auth.authorization_scope:
            auth_domain = auth.authorization_scope.get("domain_id", "")
            if auth_domain and auth_domain != request.domain_id:
                conflicts.append(
                    f"Domain mismatch: auth domain={auth_domain}, request domain={request.domain_id}"
                )

        # 5. Verify actor
        if auth.identity_ref and auth.identity_ref != request.actor_id:
            conflicts.append(
                f"Actor mismatch: auth actor={auth.identity_ref}, request actor={request.actor_id}"
            )

        # 6. Verify action is permitted
        if auth.authorization_scope:
            allowed = auth.authorization_scope.get("allowed_actions", [])
            if allowed and request.action not in allowed:
                conflicts.append(
                    f"Action '{request.action}' not in allowed actions {allowed}"
                )

        # 7. Verify resource is permitted
        if auth.authorization_scope:
            resources = auth.authorization_scope.get("target_resources", [])
            if resources and request.resource not in resources:
                conflicts.append(
                    f"Resource '{request.resource}' not in target resources {resources}"
                )

        if conflicts:
            return AuthorityResolution(
                is_valid=False,
                authorization=auth,
                conflicts=conflicts,
                rejection_reason="; ".join(conflicts),
            )

        # 8. Materialize capability
        capability = self._materialize_capability(auth, request)

        return AuthorityResolution(
            is_valid=True,
            authorization=auth,
            capability=capability,
            provenance_hash=capability.compute_hash(),
        )

    # -------------------------------------------------------------------
    # Capability Verification
    # -------------------------------------------------------------------

    def verify_capability(
        self,
        capability: ExecutionCapability,
        request: OperationRequest,
    ) -> tuple[bool, list[str]]:
        """Verify a capability permits the requested operation.

        Returns (is_permitted, conflicts).
        """
        conflicts: list[str] = []

        # 1. Verify capability is valid at current time
        if not capability.is_valid_at(request.requested_at):
            conflicts.append(f"Capability not valid at {request.requested_at}")

        # 2. Verify capability can be executed (replay guard)
        if not capability.can_execute():
            conflicts.append("Capability replay guard exhausted")

        # 3. Verify domain binding
        if capability.domain_id and capability.domain_id != self.domain.domain_id:
            conflicts.append(
                f"Domain mismatch: capability.domain_id={capability.domain_id} "
                f"!= runtime.domain_id={self.domain.domain_id}"
            )

        # 4. Verify action matches
        if not capability.scope.permits_action(request.action):
            conflicts.append(
                f"Action mismatch: capability permits '{capability.scope.action}', "
                f"request has '{request.action}'"
            )

        # 5. Verify resource binding
        if capability.resource_binding:
            if not capability.resource_binding.binds_resource(request.resource):
                conflicts.append(
                    f"Resource mismatch: capability binds "
                    f"{capability.resource_binding.bound_resources}, "
                    f"request has '{request.resource}'"
                )

        # 6. Verify nonce hasn't been used (replay protection)
        if capability.replay_guard and capability.replay_guard.nonce in self._executed_nonces:
            conflicts.append(f"Nonce {capability.replay_guard.nonce} already used (replay)")

        # 7. Verify authorization reference is present
        if not capability.authorization_ref:
            conflicts.append("Missing authorization reference")

        # 8. Verify quantity constraints (if applicable)
        quantity = request.arguments.get("quantity")
        if quantity is not None:
            if not capability.scope.constraints.permits_quantity(float(quantity)):
                conflicts.append(
                    f"Quantity {quantity} outside permitted range "
                    f"[{capability.scope.constraints.min_quantity}, "
                    f"{capability.scope.constraints.max_quantity}]"
                )

        return len(conflicts) == 0, conflicts

    # -------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------

    def execute(
        self,
        capability: ExecutionCapability,
        request: OperationRequest,
        operation: Callable[[], Any],
    ) -> ExecutionReceipt:
        """Execute an operation under a verified capability.

        The operation is only executed if the capability permits it.
        Returns an ExecutionReceipt regardless of success or failure.

        This is the ONLY way to execute consequential operations.
        """
        # Verify capability
        is_permitted, conflicts = self.verify_capability(capability, request)

        start_time = datetime.now(UTC).isoformat()
        result: Any = None

        if not is_permitted:
            # Return rejected receipt
            receipt = ExecutionReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                capability_ref=capability.capability_id,
                authorization_ref=capability.authorization_ref,
                domain_id=capability.domain_id,
                lineage_id=capability.lineage_id,
                actor_id=request.actor_id,
                executor_id="runtime-authority-gate",
                resource_id=request.resource,
                action=request.action,
                arguments_hash=hashlib.sha256(
                    json.dumps(request.arguments, sort_keys=True, default=str).encode()
                ).hexdigest()[:16],
                start_time=start_time,
                completion_time=datetime.now(UTC).isoformat(),
                effect_summary=f"REJECTED: {'; '.join(conflicts)}",
                status=ExecutionStatus.REJECTED,
                intended_effect=f"{request.action} {request.arguments}",
                observed_effect="rejected",
                reported_result="rejected",
                provenance_hash=capability.compute_hash(),
            )
            self._receipts.append(receipt)
            return receipt

        # Execute the operation
        try:
            result = operation()
            status = ExecutionStatus.COMPLETED
            observed_effect = str(result)
            reported_result = "completed"
        except Exception as e:
            status = ExecutionStatus.FAILED
            observed_effect = f"error: {e}"
            reported_result = f"error: {e}"

        # Mark nonce as used
        if capability.replay_guard and capability.replay_guard.nonce:
            self._executed_nonces.add(capability.replay_guard.nonce)

        # Increment sequence
        self._sequence_counter += 1

        # Create receipt
        receipt = ExecutionReceipt(
            receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
            capability_ref=capability.capability_id,
            authorization_ref=capability.authorization_ref,
            domain_id=capability.domain_id,
            lineage_id=capability.lineage_id,
            actor_id=request.actor_id,
            executor_id="runtime-authority-gate",
            resource_id=request.resource,
            action=request.action,
            arguments_hash=hashlib.sha256(
                json.dumps(request.arguments, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=start_time,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"{request.action} {request.resource} -> {status.value}",
            result_hash=hashlib.sha256(
                json.dumps(result, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            external_reference="",
            status=status,
            intended_effect=f"{request.action} {request.arguments}",
            observed_effect=observed_effect,
            reported_result=reported_result,
            provenance_hash=capability.compute_hash(),
        )

        self._receipts.append(receipt)
        return receipt

    # -------------------------------------------------------------------
    # Receipt Management
    # -------------------------------------------------------------------

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self._receipts)

    def has_executed(self, nonce: str) -> bool:
        """Check if a nonce has been executed."""
        return nonce in self._executed_nonces

    # -------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------

    def _materialize_capability(
        self,
        auth: AuthorizationArtifact,
        request: OperationRequest,
    ) -> ExecutionCapability:
        """Materialize an execution capability from an authorization."""
        # Build scope from authorization
        scope = CapabilityScope(
            domain_id=request.domain_id or self.domain.domain_id,
            lineage_id=self.domain.lineage_hash,
            actor_id=request.actor_id or auth.identity_ref,
            action=request.action,
            resource=request.resource,
            resource_class=self._infer_resource_class(request.action),
            arguments=request.arguments,
            constraints=CapabilityConstraints(
                allowed_actions=[request.action],
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=request.requested_at,
                valid_until=auth.expiration or "",
            ),
            authorization_ref=auth.authorization_id,
        )

        # Build replay guard
        replay_guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce_{uuid.uuid4().hex[:16]}",
            sequence=self._sequence_counter,
            max_uses=1,
            created_at=request.requested_at,
        )

        # Build executor binding
        binding = ExecutorBinding(
            binding_id=f"binding_{uuid.uuid4().hex[:12]}",
            executor_id="runtime-authority-gate",
            resource_id=request.resource,
            bound_resources=[request.resource],
            bound_at=request.requested_at,
            bound_until=auth.expiration or "",
        )

        return ExecutionCapability(
            capability_id=f"cap_{uuid.uuid4().hex[:12]}",
            authorization_ref=auth.authorization_id,
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=replay_guard,
            actor_identity_ref=request.actor_id or auth.identity_ref,
            resource_binding=binding,
            domain_id=request.domain_id or self.domain.domain_id,
            lineage_id=self.domain.lineage_hash,
            authority_root=auth.authorization_id,
            derived_at=request.requested_at,
            derived_by="runtime-authority-gate",
        )

    def _infer_resource_class(self, action: str) -> str:
        """Infer the resource class from the action."""
        if "trade" in action or "order" in action:
            return "financial_instrument"
        if "file" in action or "read" in action or "write" in action:
            return "filesystem"
        if "command" in action or "exec" in action or "subprocess" in action:
            return "process"
        if "docker" in action or "container" in action:
            return "container"
        if "payment" in action or "pay" in action:
            return "payment"
        return "generic"


# ---------------------------------------------------------------------------
# Bounded Executor
# ---------------------------------------------------------------------------


class BoundedExecutor:
    """An executor that can only operate within the bounds of a capability.

    This is the object returned by the RuntimeAuthorityGate. It wraps
    the actual operation and ensures that the operation cannot exceed
    the capability's scope.
    """

    def __init__(
        self,
        capability: ExecutionCapability,
        gate: RuntimeAuthorityGate,
    ):
        self.capability = capability
        self._gate = gate

    def execute(
        self,
        request: OperationRequest,
        operation: Callable[[], Any],
    ) -> ExecutionReceipt:
        """Execute an operation under this executor's capability."""
        return self._gate.execute(self.capability, request, operation)

    def verify(self, request: OperationRequest) -> tuple[bool, list[str]]:
        """Verify that a request is within this executor's capability."""
        return self._gate.verify_capability(self.capability, request)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_runtime_authority_gate(
    domain_id: str = "runtime-domain",
    domain_type: DomainType = DomainType.SOVEREIGN,
) -> RuntimeAuthorityGate:
    """Create a RuntimeAuthorityGate with a default domain."""
    domain = create_protocol_domain(domain_id, domain_type)
    return RuntimeAuthorityGate(domain)


def create_operation_request(
    action: str,
    resource: str,
    arguments: dict | None = None,
    actor_id: str = "",
    domain_id: str = "",
    source: str = "",
) -> OperationRequest:
    """Create an OperationRequest."""
    return OperationRequest(
        action=action,
        resource=resource,
        arguments=arguments or {},
        actor_id=actor_id,
        domain_id=domain_id,
        source=source,
    )
