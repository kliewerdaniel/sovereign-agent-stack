"""Payments abstraction layer — swap from virtual card to MPP with a config change.

Abstracted behind a single pay_for_resource() tool interface.
Current (2026): Computer-use + virtual card with spending limits.
Future (2027+): Stripe MPP native (HTTP 402 → authorize → retry).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass
class PaymentRequirement:
    """A structured payment requirement (from HTTP 402)."""
    resource: str
    price: float
    currency: str
    methods: list[str]  # ["stablecoin", "card", "bnpl"]
    cadence: str  # "one_shot", "recurring", "streaming"
    metadata: dict


@dataclass
class Receipt:
    """Receipt for a completed payment."""
    payment_id: str
    resource: str
    amount: float
    currency: str
    method: str
    timestamp: str
    status: str


@dataclass
class SpendingLimit:
    """Spending limits for the agent."""
    daily: float
    per_transaction: float
    currency: str


class PaymentAdapter(Protocol):
    """Protocol for payment adapters."""
    async def pay(self, requirement: PaymentRequirement) -> Receipt: ...
    async def authorize(self, limit: SpendingLimit) -> None: ...
    async def receipt(self, payment_id: str) -> Receipt: ...


class VirtualCardAdapter:
    """Virtual card adapter — current stopgap (2026).

    Uses computer-use to fill checkout forms with a virtual card.
    Supports card payments only.
    """

    def __init__(self, provider: str = "ramp", limit: SpendingLimit | None = None) -> None:
        self.provider = provider
        self.limit = limit or SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD")
        self._daily_spending = 0.0
        self._receipts: dict[str, Receipt] = {}

    def pay(self, requirement: PaymentRequirement) -> Receipt:
        """Make a payment using the virtual card."""
        # Check payment method
        supported = {"card"}
        if not any(m in supported for m in requirement.methods):
            raise ValueError(
                f"Unsupported payment method: {requirement.methods}. "
                f"Virtual card only supports: {supported}"
            )

        # Check limits
        if requirement.price > self.limit.per_transaction:
            raise ValueError(
                f"Payment ${requirement.price:.2f} exceeds per-transaction limit "
                f"${self.limit.per_transaction:.2f}"
            )

        if self._daily_spending + requirement.price > self.limit.daily:
            remaining = self.limit.daily - self._daily_spending
            raise ValueError(
                f"Daily limit exceeded. Remaining: ${remaining:.2f}, "
                f"Requested: ${requirement.price:.2f}"
            )

        # Process payment
        payment_id = f"pay_{uuid.uuid4().hex[:12]}"
        receipt = Receipt(
            payment_id=payment_id,
            resource=requirement.resource,
            amount=requirement.price,
            currency=requirement.currency,
            method="card",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            status="completed",
        )

        self._daily_spending += requirement.price
        self._receipts[payment_id] = receipt

        return receipt

    def authorize(self, limit: SpendingLimit) -> None:
        """Update spending limits."""
        self.limit = limit

    def receipt(self, payment_id: str) -> Receipt | None:
        """Get a receipt by payment ID."""
        return self._receipts.get(payment_id)

    @property
    def daily_spending(self) -> float:
        """Current daily spending total."""
        return self._daily_spending

    @property
    def remaining_daily(self) -> float:
        """Remaining daily budget."""
        return self.limit.daily - self._daily_spending


class MPPAdapter:
    """Machine Payments Protocol adapter — future architecture (2027+).

    Supports HTTP 402 Payment Required flows with stablecoin, card, and BNPL.
    """

    SUPPORTED_METHODS = {"stablecoin", "card", "bnpl"}

    def __init__(self, settlement: str = "stablecoin", limit: SpendingLimit | None = None) -> None:
        self.settlement = settlement
        self.limit = limit or SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD")
        self._daily_spending = 0.0
        self._receipts: dict[str, Receipt] = {}

    def pay(self, requirement: PaymentRequirement) -> Receipt:
        """Make a payment via MPP."""
        # Check payment method
        if self.settlement not in requirement.methods:
            raise ValueError(
                f"Unsupported payment method: {self.settlement}. "
                f"Supported: {requirement.methods}"
            )

        if self.settlement not in self.SUPPORTED_METHODS:
            raise ValueError(f"Unsupported settlement: {self.settlement}")

        # Check limits
        if requirement.price > self.limit.per_transaction:
            raise ValueError(
                f"Payment ${requirement.price:.2f} exceeds per-transaction limit "
                f"${self.limit.per_transaction:.2f}"
            )

        if self._daily_spending + requirement.price > self.limit.daily:
            remaining = self.limit.daily - self._daily_spending
            raise ValueError(
                f"Daily limit exceeded. Remaining: ${remaining:.2f}, "
                f"Requested: ${requirement.price:.2f}"
            )

        # Process payment
        payment_id = f"mpp_{uuid.uuid4().hex[:12]}"
        receipt = Receipt(
            payment_id=payment_id,
            resource=requirement.resource,
            amount=requirement.price,
            currency=requirement.currency,
            method=self.settlement,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            status="completed",
        )

        self._daily_spending += requirement.price
        self._receipts[payment_id] = receipt

        return receipt

    def authorize(self, limit: SpendingLimit) -> None:
        """Update spending limits."""
        self.limit = limit

    def receipt(self, payment_id: str) -> Receipt | None:
        """Get a receipt by payment ID."""
        return self._receipts.get(payment_id)

    @property
    def daily_spending(self) -> float:
        """Current daily spending total."""
        return self._daily_spending

    @property
    def remaining_daily(self) -> float:
        """Remaining daily budget."""
        return self.limit.daily - self._daily_spending
