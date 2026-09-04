"""Layer 8: Payments — How the agent pays for things.

Abstracted behind a single pay_for_resource() tool interface.
Current (2026): Computer-use + virtual card with spending limits.
Future (2027+): Stripe MPP native (HTTP 402 → authorize → retry).
Swapping is a config change, not a rewrite.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class PaymentRequirement:
    resource: str
    price: float
    currency: str
    methods: list[str]  # ["stablecoin", "card", "bnpl"]
    cadence: str  # "one_shot", "recurring", "streaming"
    metadata: dict


@dataclass
class Receipt:
    payment_id: str
    resource: str
    amount: float
    currency: str
    method: str
    timestamp: str
    status: str


@dataclass
class SpendingLimit:
    daily: float
    per_transaction: float
    currency: str


class PaymentAdapter(Protocol):
    async def pay(self, requirement: PaymentRequirement) -> Receipt: ...
    async def authorize(self, limit: SpendingLimit) -> None: ...
    async def receipt(self, payment_id: str) -> Receipt: ...
