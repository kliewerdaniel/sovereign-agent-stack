"""Capability-Bound Broker — wraps broker adapters with authority enforcement.

The raw broker adapters (SimulatedBroker, AlpacaBrokerAdapter) must NOT be
directly accessible to agent/tool/plugin code. Instead, all broker access
must go through the CapabilityBoundBroker, which enforces that every order
has a verified execution capability.

Architectural law:
    THE BROKER IS A CONSEQUENTIAL AUTHORITY BOUNDARY.
    IT MUST NOT TRUST UPSTREAM CODE.

This implementation uses the canonical CapabilityVerifier to ensure
authority semantics are identical across all boundaries.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sas.quant.broker import Order, OrderStatus
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.capability_verifier import (
    CapabilityVerifier,
    ReplayProtectionStore,
    VerificationResult,
    create_capability_verifier,
    create_replay_protection_store,
)
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
    The underlying broker adapter is never directly accessible through
    any public API.

    This makes it structurally impossible to submit an order without
    a verified execution capability.

    The verification uses the canonical CapabilityVerifier so that
    authority semantics are identical across all boundaries.
    """

    def __init__(
        self,
        broker: BrokerAdapter,
        domain: ProtocolDomain,
        verifier: CapabilityVerifier | None = None,
        replay_store: ReplayProtectionStore | None = None,
    ):
        self.__broker = broker
        self.__domain = domain
        self.__verifier = verifier or create_capability_verifier(domain)
        self.__replay_store = replay_store or create_replay_protection_store()
        self.__receipts: list[ExecutionReceipt] = []
        self.__sequence_counter: int = 0

    @property
    def name(self) -> str:
        return f"capability-bound-{self.__broker.name}"

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

        # Check replay protection first
        if capability.replay_guard and capability.replay_guard.nonce:
            if self.__replay_store.has_used(capability.replay_guard.nonce):
                return BrokerEnforcementResult(
                    is_permitted=False,
                    conflicts=["Replay: nonce already consumed"],
                    rejection_reason=f"Nonce {capability.replay_guard.nonce} already used",
                )

        # Use canonical verifier
        verification = self.__verifier.verify(
            capability=capability,
            action="execute_trade",
            resource=trade_intent.symbol,
            arguments={
                "quantity": trade_intent.quantity,
                "side": trade_intent.side,
                "symbol": trade_intent.symbol,
            },
            current_time=current_time,
        )

        if not verification.is_permitted:
            return BrokerEnforcementResult(
                is_permitted=False,
                conflicts=verification.conflicts,
                rejection_reason=verification.rejection_reason,
            )

        # Additional broker-specific constraint: quantity must be positive
        if trade_intent.quantity <= 0:
            return BrokerEnforcementResult(
                is_permitted=False,
                conflicts=["Quantity must be positive"],
                rejection_reason=f"Quantity {trade_intent.quantity} is not positive",
            )

        # Submit to underlying broker
        order = self.__broker.submit_trade(trade_intent)

        # Mark nonce as used
        if capability.replay_guard and capability.replay_guard.nonce:
            self.__replay_store.mark_used(
                capability.replay_guard.nonce,
                capability.capability_id,
                current_time,
            )

        # Increment sequence
        self.__sequence_counter += 1

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

        self.__receipts.append(receipt)

        return BrokerEnforcementResult(
            is_permitted=True,
            order=order,
            receipt=receipt,
            provenance_hash=receipt.compute_hash(),
        )

    def get_account_summary(self) -> dict:
        """Get account summary."""
        return self.__broker.get_account_summary()

    def get_positions(self) -> dict[str, float]:
        """Get current positions."""
        return self.__broker.get_positions()

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all recorded receipts."""
        return list(self.__receipts)

    def has_executed(self, nonce: str) -> bool:
        """Check if a nonce has been executed."""
        return self.__replay_store.has_used(nonce)

    def get_replay_state(self) -> dict:
        """Get durable replay protection state."""
        return self.__replay_store.get_durable_state()

    def restore_replay_state(self, state: dict) -> None:
        """Restore replay protection state (for process restart)."""
        self.__replay_store.restore_from_state(state)


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
