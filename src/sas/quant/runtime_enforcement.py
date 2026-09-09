"""Runtime Capability Enforcer — bridges the formal protocol to the actual runtime.

This module provides the concrete enforcement points that prevent the runtime
from silently widening, substituting, or laundering the authority established
by the formal protocol layers.

The central law enforced here:
    THE RUNTIME MAY MATERIALIZE AUTHORITY, BUT IT MUST NEVER CREATE AUTHORITY.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sas.quant.broker import Order, OrderStatus, Account
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.experiment.execution_capability import (
    AttenuationType,
    CapabilityConstraints,
    CapabilityMaterializer,
    CapabilityScope,
    CapabilityType,
    ExecutionContext,
    ExecutionCapability,
    ExecutionReceipt,
    ExecutionStatus,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)
from sas.quant.risk import TradeIntent


# ---------------------------------------------------------------------------
# Runtime Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeEnforcementResult:
    """Result of runtime capability enforcement."""
    is_permitted: bool
    order: Optional[Order] = None
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Runtime Capability Enforcer
# ---------------------------------------------------------------------------


class RuntimeCapabilityEnforcer:
    """Enforces capability constraints at the actual runtime boundary.

    This is the concrete enforcement point that prevents the runtime from
    bypassing the formal protocol. Every order submission passes through
    this enforcer.
    """

    def __init__(self, domain: ProtocolDomain):
        self.domain = domain
        self._executed_nonces: set[str] = set()
        self._sequence_counter: int = 0
        self._receipts: list[ExecutionReceipt] = []

    def enforce(
        self,
        capability: ExecutionCapability,
        trade_intent: TradeIntent,
        current_time: str = "",
    ) -> RuntimeEnforcementResult:
        """Enforce capability constraints on a trade intent.

        This is the single point where the formal protocol meets the runtime.
        Every order must pass through here.
        """
        conflicts = []

        # 1. Verify capability is valid at current time
        if not capability.is_valid_at(current_time):
            conflicts.append(f"Capability not valid at {current_time}")

        # 2. Verify capability can be executed (replay guard)
        if not capability.can_execute():
            conflicts.append("Capability replay guard exhausted")

        # 3. Verify domain binding
        if capability.domain_id != self.domain.domain_id:
            conflicts.append(
                f"Domain mismatch: capability.domain_id={capability.domain_id} "
                f"!= runtime.domain_id={self.domain.domain_id}"
            )

        # 4. Verify action matches
        if not capability.scope.permits_action("execute_trade"):
            conflicts.append(
                f"Action mismatch: capability permits '{capability.scope.action}', "
                f"trade_intent has action"
            )

        # 5. Verify quantity constraints
        quantity = trade_intent.quantity
        if not capability.scope.constraints.permits_quantity(quantity):
            conflicts.append(
                f"Quantity {quantity} outside permitted range "
                f"[{capability.scope.constraints.min_quantity}, "
                f"{capability.scope.constraints.max_quantity}]"
            )

        # 6. Verify resource binding (if present)
        if capability.resource_binding:
            if not capability.resource_binding.binds_resource(trade_intent.symbol):
                conflicts.append(
                    f"Resource mismatch: capability binds "
                    f"{capability.resource_binding.bound_resources}, "
                    f"trade_intent has '{trade_intent.symbol}'"
                )

        # 7. Verify nonce hasn't been used (replay protection)
        if capability.replay_guard and capability.replay_guard.nonce in self._executed_nonces:
            conflicts.append(f"Nonce {capability.replay_guard.nonce} already used (replay)")

        # 8. Verify authorization reference is present
        if not capability.authorization_ref:
            conflicts.append("Missing authorization reference")

        is_permitted = len(conflicts) == 0
        rejection_reason = "; ".join(conflicts) if conflicts else ""

        return RuntimeEnforcementResult(
            is_permitted=is_permitted,
            conflicts=conflicts,
            rejection_reason=rejection_reason,
        )

    def record_execution(
        self,
        capability: ExecutionCapability,
        order: Order,
        status: ExecutionStatus,
        external_reference: str = "",
    ) -> ExecutionReceipt:
        """Record an execution and return an immutable receipt."""
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
            actor_id=capability.scope.actor_id,
            executor_id="runtime-enforcer",
            resource_id=order.symbol,
            action=capability.scope.action,
            arguments_hash=hashlib.sha256(
                json.dumps({"symbol": order.symbol, "quantity": order.quantity, "side": order.side}, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=order.created_at,
            completion_time=datetime.now().isoformat(),
            effect_summary=f"Order {order.id} {status.value}",
            result_hash=order.content_hash,
            external_reference=external_reference,
            status=status,
            intended_effect=f"{capability.scope.action} {capability.scope.arguments}",
            observed_effect=f"Order {order.id} {status.value}",
            reported_result=status.value,
            provenance_hash=capability.compute_hash(),
        )

        self._receipts.append(receipt)
        return receipt

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self._receipts)

    def has_executed(self, nonce: str) -> bool:
        """Check if a nonce has been executed."""
        return nonce in self._executed_nonces


# ---------------------------------------------------------------------------
# Capability-Bound Broker
# ---------------------------------------------------------------------------


class CapabilityBoundBroker:
    """Broker wrapper that enforces capability constraints.

    The actual broker adapter is wrapped so that every order submission
    is checked against the capability. The broker never receives
    unrestricted access to the underlying resource.
    """

    def __init__(
        self,
        broker: BrokerAdapter,
        enforcer: RuntimeCapabilityEnforcer,
    ):
        self._broker = broker
        self._enforcer = enforcer

    @property
    def name(self) -> str:
        return f"capability-bound-{self._broker.name}"

    def submit_order(
        self,
        capability: ExecutionCapability,
        trade_intent: TradeIntent,
        current_time: str = "",
    ) -> RuntimeEnforcementResult:
        """Submit an order with capability enforcement.

        The order is only submitted if the capability permits it.
        """
        # Enforce capability constraints
        enforcement = self._enforcer.enforce(capability, trade_intent, current_time)

        if not enforcement.is_permitted:
            return enforcement

        # Create order from trade intent
        order = Order(
            symbol=trade_intent.symbol,
            side=trade_intent.side,
            quantity=trade_intent.quantity,
            parent_trade_id=trade_intent.id,
        )

        # Submit to underlying broker
        submitted = self._broker.submit_trade(trade_intent)

        # Record execution
        receipt = self._enforcer.record_execution(
            capability=capability,
            order=submitted,
            status=ExecutionStatus(submitted.status.value),
            external_reference=submitted.id,
        )

        return RuntimeEnforcementResult(
            is_permitted=True,
            order=submitted,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def get_account(self) -> Account:
        """Get account info."""
        return self._broker.get_account()

    def get_name(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Credential Separation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CredentialSeparation:
    """Enforces the distinction between credentials and capabilities.

    A credential may authorize broad access, but a capability narrows it.
    The credential must never widen the protocol capability.
    """
    credential_scope: dict = field(default_factory=dict)
    capability_scope: dict = field(default_factory=dict)

    def verify_no_widening(self) -> tuple[bool, list[str]]:
        """Verify that capability doesn't exceed credential scope."""
        conflicts = []

        # Check actions
        cred_actions = set(self.credential_scope.get("allowed_actions", []))
        cap_actions = set(self.capability_scope.get("allowed_actions", []))
        if cap_actions and cred_actions:
            extra = cap_actions - cred_actions
            if extra:
                conflicts.append(f"Capability actions {extra} exceed credential scope")

        # Check resources
        cred_resources = set(self.credential_scope.get("allowed_resources", []))
        cap_resources = set(self.capability_scope.get("allowed_resources", []))
        if cap_resources and cred_resources:
            extra = cap_resources - cred_resources
            if extra:
                conflicts.append(f"Capability resources {extra} exceed credential scope")

        # Check accounts
        cred_accounts = set(self.credential_scope.get("allowed_accounts", []))
        cap_accounts = set(self.capability_scope.get("allowed_accounts", []))
        if cap_accounts and cred_accounts:
            extra = cap_accounts - cred_accounts
            if extra:
                conflicts.append(f"Capability accounts {extra} exceed credential scope")

        return len(conflicts) == 0, conflicts


# ---------------------------------------------------------------------------
# Malicious Executor
# ---------------------------------------------------------------------------


class MaliciousExecutor:
    """A deliberately malicious executor that tries to bypass capability constraints.

    Used to test that the runtime enforcement actually works.
    """

    def __init__(self, target_account: str = "B", target_symbol: str = "MSFT", target_quantity: float = 1000):
        self.target_account = target_account
        self.target_symbol = target_symbol
        self.target_quantity = target_quantity
        self.attempts: list[dict] = []

    def attempt_widening(
        self,
        capability: ExecutionCapability,
        original_trade: TradeIntent,
        enforcer: RuntimeCapabilityEnforcer,
    ) -> RuntimeEnforcementResult:
        """Attempt to execute a trade that widens the capability."""
        # Create a modified trade intent that exceeds capability
        widened_trade = TradeIntent(
            id=f"malicious_{uuid.uuid4().hex[:8]}",
            symbol=self.target_symbol,  # Different symbol
            side=original_trade.side,
            quantity=self.target_quantity,  # Larger quantity
        )

        result = enforcer.enforce(capability, widened_trade)
        self.attempts.append({
            "type": "widening",
            "result": result.is_permitted,
            "reason": result.rejection_reason,
        })
        return result

    def attempt_replay(
        self,
        capability: ExecutionCapability,
        trade: TradeIntent,
        enforcer: RuntimeCapabilityEnforcer,
    ) -> RuntimeEnforcementResult:
        """Attempt to replay an already-used capability."""
        # First execution should succeed
        result1 = enforcer.enforce(capability, trade)
        if result1.is_permitted:
            # Mark as executed
            enforcer._executed_nonces.add(capability.replay_guard.nonce)
            # Second execution should fail
            result2 = enforcer.enforce(capability, trade)
            self.attempts.append({
                "type": "replay",
                "first": result1.is_permitted,
                "second": result2.is_permitted,
                "reason": result2.rejection_reason,
            })
            return result2
        return result1

    def attempt_domain_escape(
        self,
        capability: ExecutionCapability,
        trade: TradeIntent,
        wrong_domain: ProtocolDomain,
    ) -> tuple[bool, list[str]]:
        """Attempt to use capability in wrong domain."""
        enforcer = RuntimeCapabilityEnforcer(wrong_domain)
        result = enforcer.enforce(capability, trade)
        self.attempts.append({
            "type": "domain_escape",
            "result": result.is_permitted,
            "reason": result.rejection_reason,
        })
        return result.is_permitted, result.conflicts

    def get_attempts(self) -> list[dict]:
        """Get all malicious attempts."""
        return list(self.attempts)


# ---------------------------------------------------------------------------
# Protocol/Runtime Trace
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProtocolRuntimeTrace:
    """Traces the flow from protocol to runtime.

    Records every transition from formal protocol to actual execution.
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Protocol layer
    authorization_id: str = ""
    capability_id: str = ""
    domain_id: str = ""
    lineage_id: str = ""
    authority_root: str = ""
    actor: str = ""
    action: str = ""
    resource: str = ""

    # Runtime layer
    order_id: str = ""
    receipt_id: str = ""
    broker_name: str = ""
    execution_status: str = ""

    # Enforcement
    enforcement_permitted: bool = False
    enforcement_conflicts: list[str] = field(default_factory=list)

    # Provenance
    protocol_hash: str = ""
    runtime_hash: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "trace_id": self.trace_id,
            "authorization_id": self.authorization_id,
            "capability_id": self.capability_id,
            "order_id": self.order_id,
            "receipt_id": self.receipt_id,
            "enforcement_permitted": self.enforcement_permitted,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def has_information_loss(self) -> bool:
        """Check if any protocol information was lost at runtime."""
        # If capability has domain but runtime doesn't record it
        if self.domain_id and not self.lineage_id:
            return True
        # If capability has actor but runtime doesn't record it
        if self.actor and not self.receipt_id:
            return True
        return False


# ---------------------------------------------------------------------------
# Runtime Death Recovery
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeDeathRecovery:
    """Tests that authority survives process death.

    All protocol artifacts are persisted, then the runtime is "killed"
    and reconstructed from persisted state.
    """
    persisted_capability: Optional[ExecutionCapability] = None
    persisted_receipts: list[ExecutionReceipt] = field(default_factory=list)
    persisted_traces: list[ProtocolRuntimeTrace] = field(default_factory=list)

    def reconstruct_authority(self) -> dict:
        """Reconstruct authority from persisted artifacts."""
        if not self.persisted_capability:
            return {"status": "no_capability"}

        cap = self.persisted_capability
        return {
            "status": "reconstructed",
            "capability_id": cap.capability_id,
            "authorization_ref": cap.authorization_ref,
            "domain_id": cap.domain_id,
            "lineage_id": cap.lineage_id,
            "authority_root": cap.authority_root,
            "scope_action": cap.scope.action,
            "scope_resource": cap.scope.resource,
            "scope_actor": cap.scope.actor_id,
            "valid_at_creation": cap.is_valid_at(cap.derived_at),
            "receipts_count": len(self.persisted_receipts),
            "traces_count": len(self.persisted_traces),
        }

    def verify_reconstruction(self) -> tuple[bool, list[str]]:
        """Verify that reconstructed authority matches original."""
        conflicts = []

        if not self.persisted_capability:
            conflicts.append("No capability to reconstruct")
            return False, conflicts

        cap = self.persisted_capability

        # Verify capability integrity
        if not cap.authorization_ref:
            conflicts.append("Capability missing authorization reference")

        # Verify receipts reference capability
        for receipt in self.persisted_receipts:
            if receipt.capability_ref != cap.capability_id:
                conflicts.append(
                    f"Receipt {receipt.receipt_id} references wrong capability"
                )

        # Verify traces
        for trace in self.persisted_traces:
            if trace.capability_id != cap.capability_id:
                conflicts.append(
                    f"Trace {trace.trace_id} references wrong capability"
                )

        return len(conflicts) == 0, conflicts


# ---------------------------------------------------------------------------
# Enforcement Classification
# ---------------------------------------------------------------------------


from enum import Enum


class EnforcementClassification(str, Enum):
    """Classification of enforcement points."""
    PROTOCOL_ENFORCED = "protocol_enforced"
    RUNTIME_ENFORCED = "runtime_enforced"
    EXTERNAL_SYSTEM_ENFORCED = "external_system_enforced"
    TRUST_ASSUMPTION = "trust_assumption"
    UNENFORCED = "unenforced"


@dataclass(frozen=True)
class BoundaryClassification:
    """Classification of a specific authority boundary."""
    boundary_name: str
    classification: EnforcementClassification
    protocol_enforcement: bool = False
    runtime_enforcement: bool = False
    external_enforcement: bool = False
    trust_assumptions: list[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_capability_bound_broker(
    broker: BrokerAdapter,
    domain: ProtocolDomain,
) -> CapabilityBoundBroker:
    """Create a capability-bound broker wrapper."""
    enforcer = RuntimeCapabilityEnforcer(domain)
    return CapabilityBoundBroker(broker, enforcer)


def classify_boundary(
    boundary_name: str,
    protocol_enforced: bool = False,
    runtime_enforced: bool = False,
    external_enforced: bool = False,
    trust_assumptions: list[str] | None = None,
    notes: str = "",
) -> BoundaryClassification:
    """Classify an authority boundary."""
    if protocol_enforced and runtime_enforced:
        classification = EnforcementClassification.PROTOCOL_ENFORCED
    elif runtime_enforced:
        classification = EnforcementClassification.RUNTIME_ENFORCED
    elif external_enforced:
        classification = EnforcementClassification.EXTERNAL_SYSTEM_ENFORCED
    elif trust_assumptions:
        classification = EnforcementClassification.TRUST_ASSUMPTION
    else:
        classification = EnforcementClassification.UNENFORCED

    return BoundaryClassification(
        boundary_name=boundary_name,
        classification=classification,
        protocol_enforcement=protocol_enforced,
        runtime_enforcement=runtime_enforced,
        external_enforcement=external_enforced,
        trust_assumptions=trust_assumptions or [],
        notes=notes,
    )
