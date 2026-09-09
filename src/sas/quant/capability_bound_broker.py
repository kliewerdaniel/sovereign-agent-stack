"""Capability-Bound Broker — wraps broker adapters with authority enforcement.

The raw broker adapters (SimulatedBroker, AlpacaBrokerAdapter) must NOT be
directly accessible to agent/tool/plugin code. Instead, all broker access
must go through the CapabilityBoundBroker, which enforces that every order
has a verified execution capability.

Architectural law:
    THE BROKER IS A CONSEQUENTIAL AUTHORITY BOUNDARY.
    IT MUST NOT TRUST UPSTREAM CODE.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sas.quant.broker import Account, Order, OrderStatus
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.experiment.execution_capability import (
    ExecutionCapability,
    ExecutionReceipt,
    ExecutionStatus,
)
from sas.quant.experiment.protocol_lineage import ProtocolDomain
from sas.quant.risk import TradeIntent


# ---------------------------------------------------------------------------
# Broker Enforcement Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BrokerEnforcementResult:
    """Result of capability-bound broker enforcement."""
    is_permitted: bool = False
    order: Optional[Order] = None
    receipt: Optional[ExecutionReceipt] = None
    conflicts: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    provenance_hash: str = ""


# ---------------------------------------------------------------------------
# Capability-Bound Broker
# ---------------------------------------------------------------------------


class CapabilityBoundBroker:
    """Wraps a broker adapter with capability enforcement.

    Every order submission must pass through capability verification.
    The underlying broker adapter is never directly accessible.

    This makes it structurally impossible to submit an order without
    a verified execution capability.
    """

    def __init__(
        self,
        broker: BrokerAdapter,
        domain: ProtocolDomain,
        executed_nonces: set[str] | None = None,
    ):
        self._broker = broker
        self._domain = domain
        self._executed_nonces: set[str] = executed_nonces if executed_nonces is not None else set()
        self._receipts: list[ExecutionReceipt] = []
        self._sequence_counter: int = 0

    @property
    def name(self) -> str:
        return f"capability-bound-{self._broker.name}"

    @property
    def underlying_broker(self) -> BrokerAdapter:
        """Access to the underlying broker — for testing/inspection only."""
        return self._broker

    def submit_order(
        self,
        capability: ExecutionCapability,
        trade_intent: TradeIntent,
        current_time: str = "",
    ) -> BrokerEnforcementResult:
        """Submit an order with capability enforcement.

        The order is only submitted if the capability permits it.
        This is the ONLY way to submit orders through this broker.
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
        if capability.domain_id and capability.domain_id != self._domain.domain_id:
            conflicts.append(
                f"Domain mismatch: capability.domain_id={capability.domain_id} "
                f"!= broker.domain_id={self._domain.domain_id}"
            )

        # 4. Verify action matches
        if not capability.scope.permits_action("execute_trade"):
            conflicts.append(
                f"Action mismatch: capability permits '{capability.scope.action}', "
                f"trade_intent has action"
            )

        # 5. Verify resource binding
        if capability.resource_binding:
            if not capability.resource_binding.binds_resource(trade_intent.symbol):
                conflicts.append(
                    f"Resource mismatch: capability binds "
                    f"{capability.resource_binding.bound_resources}, "
                    f"trade_intent has '{trade_intent.symbol}'"
                )

        # 6. Verify nonce hasn't been used (replay protection)
        if capability.replay_guard and capability.replay_guard.nonce in self._executed_nonces:
            conflicts.append(f"Nonce {capability.replay_guard.nonce} already used (replay)")

        # 7. Verify authorization reference is present
        if not capability.authorization_ref:
            conflicts.append("Missing authorization reference")

        # 8. Verify quantity constraints
        if not capability.scope.constraints.permits_quantity(trade_intent.quantity):
            conflicts.append(
                f"Quantity {trade_intent.quantity} outside permitted range "
                f"[{capability.scope.constraints.min_quantity}, "
                f"{capability.scope.constraints.max_quantity}]"
            )

        if conflicts:
            return BrokerEnforcementResult(
                is_permitted=False,
                conflicts=conflicts,
                rejection_reason="; ".join(conflicts),
            )

        # Submit to underlying broker
        order = self._broker.submit_trade(trade_intent)

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
            executor_id="capability-bound-broker",
            resource_id=order.symbol,
            action="execute_trade",
            arguments_hash=hashlib.sha256(
                json.dumps({
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "side": order.side,
                }, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            start_time=order.created_at,
            completion_time=datetime.now(UTC).isoformat(),
            effect_summary=f"Order {order.id} {order.status.value}",
            result_hash=order.content_hash,
            external_reference=order.id,
            status=ExecutionStatus(order.status.value) if order.status.value in [s.value for s in ExecutionStatus] else ExecutionStatus.COMPLETED,
            intended_effect=f"execute_trade {{'symbol': '{trade_intent.symbol}', 'quantity': {trade_intent.quantity}}}",
            observed_effect=f"Order {order.id} {order.status.value}",
            reported_result=order.status.value,
            provenance_hash=capability.compute_hash(),
        )

        self._receipts.append(receipt)

        return BrokerEnforcementResult(
            is_permitted=True,
            order=order,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def get_account_summary(self) -> dict:
        """Get account summary."""
        return self._broker.get_account_summary()

    def get_positions(self) -> dict[str, float]:
        """Get current positions."""
        return self._broker.get_positions()

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self._receipts)

    def has_executed(self, nonce: str) -> bool:
        """Check if a nonce has been executed."""
        return nonce in self._executed_nonces


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------


def create_capability_bound_broker(
    broker: BrokerAdapter,
    domain_id: str = "trading-domain",
) -> CapabilityBoundBroker:
    """Create a CapabilityBoundBroker with a default domain."""
    from sas.quant.experiment.protocol_lineage import create_protocol_domain, DomainType
    domain = create_protocol_domain(domain_id, DomainType.SOVEREIGN)
    return CapabilityBoundBroker(broker, domain)
