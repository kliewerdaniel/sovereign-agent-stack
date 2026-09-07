"""Deterministic simulated broker.

No real money. No real market connection.
All fills are simulated with configurable slippage and fees.
Designed so a real brokerage adapter can replace this without
changing the agent architecture.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Optional

import numpy as np


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """A simulated order."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    symbol: str = ""
    side: str = "buy"            # buy, sell
    quantity: float = 0.0
    price: float = 0.0
    order_type: OrderType = OrderType.MARKET
    limit_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    fill_price: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    rejection_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    filled_at: str | None = None
    parent_trade_id: str = ""
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                json.dumps(self.to_dict(), sort_keys=True, default=str).encode()
            ).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "content_hash"}


@dataclass
class Fill:
    """A fill report."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    fees: float
    slippage_bps: float
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class Account:
    """Simulated account."""
    cash: float = 100_000.0
    initial_cash: float = 100_000.0
    positions: dict[str, float] = field(default_factory=dict)  # symbol → shares
    order_history: list[Order] = field(default_factory=list)
    fill_history: list[Fill] = field(default_factory=list)
    total_fees_paid: float = 0.0

    @property
    def equity(self) -> float:
        return self.cash + sum(self.positions.values())

    @property
    def pnl(self) -> float:
        return self.equity - self.initial_cash


@dataclass
class BrokerConfig:
    """Broker configuration."""
    commission_per_share: float = 0.005
    commission_per_trade: float = 0.0
    slippage_bps: float = 5.0
    market_impact_bps: float = 2.0
    spread_bps: float = 3.0
    min_order_size: float = 1.0
    reject_above_value: float = 1_000_000


class SimulatedBroker:
    """Deterministic simulated broker."""

    def __init__(self, config: BrokerConfig | None = None,
                 seed: int = 42):
        self.config = config or BrokerConfig()
        self.account = Account()
        self._rng = np.random.default_rng(seed)
        self._version = "1.0.0"

    def submit_order(self, symbol: str, side: str,
                      quantity: float, price: float,
                      order_type: OrderType = OrderType.MARKET,
                      limit_price: float = 0.0) -> Order:
        """Submit a simulated order."""
        # Validate
        if quantity <= 0:
            return self._reject(symbol, side, quantity, "quantity must be positive")
        if price <= 0:
            return self._reject(symbol, side, quantity, "price must be positive")

        order_value = quantity * price
        if order_value > self.config.reject_above_value:
            return self._reject(symbol, side, quantity,
                                f"order value ${order_value:,.0f} exceeds limit")

        order = Order(
            symbol=symbol, side=side, quantity=quantity,
            price=price, order_type=order_type,
            limit_price=limit_price,
        )

        # Simulate fill
        fill = self._simulate_fill(order)
        if fill:
            order.status = OrderStatus.FILLED
            order.filled_quantity = fill.quantity
            order.fill_price = fill.price
            order.fees = fill.fees
            order.slippage = fill.slippage_bps
            order.filled_at = fill.timestamp

            # Update account
            if side == "buy":
                self.account.cash -= fill.quantity * fill.price + fill.fees
                self.account.positions[symbol] = (
                    self.account.positions.get(symbol, 0) + fill.quantity
                )
            else:
                self.account.cash += fill.quantity * fill.price - fill.fees
                self.account.positions[symbol] = (
                    self.account.positions.get(symbol, 0) - fill.quantity
                )

            self.account.fill_history.append(fill)
            self.account.total_fees_paid += fill.fees
        else:
            order.status = OrderStatus.REJECTED
            order.rejection_reason = "fill simulation failed"

        self.account.order_history.append(order)
        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        for order in self.account.order_history:
            if order.id == order_id and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                return True
        return False

    def get_positions(self) -> dict[str, float]:
        """Get current positions."""
        return dict(self.account.positions)

    def get_account_summary(self) -> dict:
        """Get account summary."""
        return {
            "cash": self.account.cash,
            "equity": self.account.equity,
            "pnl": self.account.pnl,
            "positions": dict(self.account.positions),
            "total_fees": self.account.total_fees_paid,
            "order_count": len(self.account.order_history),
            "fill_count": len(self.account.fill_history),
        }

    def _simulate_fill(self, order: Order) -> Fill | None:
        """Simulate a fill with slippage and fees."""
        price = order.price
        if order.order_type == OrderType.MARKET:
            # Market order: random slippage
            slip = self._rng.normal(0, self.config.slippage_bps)
        else:
            # Limit order: slippage toward limit price
            slip = self.config.slippage_bps * 0.5

        fill_price = price * (1 + slip / 10000)
        fees = (self.config.commission_per_share * order.quantity +
                self.config.commission_per_trade)
        # Market impact
        impact = price * (self.config.market_impact_bps / 10000) * order.quantity
        fees += impact

        return Fill(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            fees=fees,
            slippage_bps=abs(slip),
        )

    def _reject(self, symbol: str, side: str,
                quantity: float, reason: str) -> Order:
        """Create a rejected order."""
        return Order(
            symbol=symbol, side=side, quantity=quantity,
            price=0, status=OrderStatus.REJECTED,
            rejection_reason=reason,
        )