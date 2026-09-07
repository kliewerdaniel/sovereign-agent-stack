"""Alpaca paper-trading broker adapter.

Connects to the Alpaca Trade API (paper mode) for live order execution.
Credentials are sourced from environment variables or the local vault;
they are never logged, never serialized to provenance, and never
included in any error message or string representation.

Environment variables:
    APCA_API_KEY_ID — Alpaca API key ID
    APCA_API_SECRET_KEY — Alpaca API secret key

Or register via the local auth broker vault with tool name "alpaca".
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import requests as _requests

from sas.quant.broker.adapter import BrokerAdapter

if TYPE_CHECKING:
    from sas.quant.broker import Order, OrderType, OrderStatus
    from sas.quant.risk import TradeIntent

# Alpaca paper trading base URL
ALPACA_PAPER_BASE = "https://paper-api.alpaca.markets"
ALPACA_DATA_BASE = "https://data.alpaca.markets"


def _get_alpaca_credentials() -> tuple[str, str]:
    """Retrieve Alpaca credentials from environment or vault.

    Returns:
        Tuple of (key_id, secret_key).

    Raises:
        ValueError: If credentials are not available.
    """
    key_id = os.environ.get("APCA_API_KEY_ID", "")
    secret_key = os.environ.get("APCA_API_SECRET_KEY", "")

    # Fallback to local auth broker vault
    if not key_id or not secret_key:
        try:
            from sas.layers.auth import LocalAuthBroker
            from pathlib import Path

            broker = LocalAuthBroker(store_path=str(Path.home() / ".sas" / "vault.db"))
            creds = broker.get_credentials("alpaca")
            if creds:
                key_id = key_id or creds.token or ""
                secret_key = secret_key or creds.refresh_token or ""
        except Exception:
            pass

    if not key_id or not secret_key:
        raise ValueError(
            "Alpaca credentials not found. Set APCA_API_KEY_ID and "
            "APCA_API_SECRET_KEY environment variables, or register "
            "via 'sas auth register alpaca --token <key_id> --auth-type oauth'."
        )

    return key_id, secret_key


class AlpacaBrokerAdapter(BrokerAdapter):
    """Alpaca paper-trading broker adapter.

    Uses the Alpaca Trade API v2 for order submission and account management.
    Only paper trading is supported in this adapter.
    """

    def __init__(
        self,
        key_id: str = "",
        secret_key: str = "",
        paper: bool = True,
    ):
        self._key_id = key_id
        self._secret_key = secret_key
        self._paper = paper
        self._base_url = ALPACA_PAPER_BASE if paper else "https://api.alpaca.markets"
        self._headers = {}

    def _ensure_auth(self) -> dict:
        """Build and return auth headers, sourcing credentials if needed."""
        if not self._key_id or not self._secret_key:
            self._key_id, self._secret_key = _get_alpaca_credentials()
        return {
            "APCA-API-KEY-ID": self._key_id,
            "APCA-API-SECRET-KEY": self._secret_key,
            "Content-Type": "application/json",
        }

    @property
    def name(self) -> str:
        return "alpaca-paper" if self._paper else "alpaca-live"

    @property
    def is_live(self) -> bool:
        return True

    def submit_trade(self, trade: TradeIntent) -> Order:
        """Submit a trade intent to Alpaca.

        Args:
            trade: An authorized ``TradeIntent``.

        Returns:
            An ``Order`` with fill details from Alpaca.
        """
        from sas.quant.broker import Order, OrderType, OrderStatus

        headers = self._ensure_auth()

        # Map trade intent to Alpaca order
        side = trade.side  # "buy" or "sell"
        symbol = trade.symbol
        qty = str(int(trade.quantity)) if trade.quantity == int(trade.quantity) else str(trade.quantity)

        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": "day",
        }

        try:
            resp = _requests.post(
                f"{self._base_url}/v2/orders",
                json=order_data,
                headers=headers,
                timeout=30,
            )
        except Exception as e:
            return Order(
                symbol=symbol,
                side=side,
                quantity=trade.quantity,
                price=trade.price_assumption,
                order_type=OrderType.MARKET,
                status=OrderStatus.REJECTED,
                rejection_reason=f"Connection error: {type(e).__name__}",
                parent_trade_id=trade.id,
            )

        if resp.status_code not in (200, 201):
            return Order(
                symbol=symbol,
                side=side,
                quantity=trade.quantity,
                price=trade.price_assumption,
                order_type=OrderType.MARKET,
                status=OrderStatus.REJECTED,
                rejection_reason=f"Alpaca error {resp.status_code}: {resp.text[:200]}",
                parent_trade_id=trade.id,
            )

        try:
            data = resp.json()
        except Exception:
            return Order(
                symbol=symbol,
                side=side,
                quantity=trade.quantity,
                price=trade.price_assumption,
                order_type=OrderType.MARKET,
                status=OrderStatus.REJECTED,
                rejection_reason="Invalid JSON response from Alpaca",
                parent_trade_id=trade.id,
            )

        # Map Alpaca status to our OrderStatus
        alpaca_status = data.get("status", "")
        status_map = {
            "filled": OrderStatus.FILLED,
            "partially_filled": OrderStatus.PARTIAL,
            "accepted": OrderStatus.PENDING,
            "pending_new": OrderStatus.PENDING,
            "new": OrderStatus.PENDING,
            "canceled": OrderStatus.CANCELLED,
            "cancelled": OrderStatus.CANCELLED,
            "expired": OrderStatus.REJECTED,
            "rejected": OrderStatus.REJECTED,
            "replaced": OrderStatus.PENDING,
            "done_for_day": OrderStatus.PENDING,
        }
        status = status_map.get(alpaca_status, OrderStatus.PENDING)

        # Extract fill details
        filled_qty = float(data.get("filled_qty", 0) or 0)
        fill_price = float(data.get("filled_avg_price", 0) or 0)
        if not fill_price:
            fill_price = trade.price_assumption

        return Order(
            id=data.get("id", ""),
            symbol=symbol,
            side=side,
            quantity=filled_qty or trade.quantity,
            price=fill_price,
            order_type=OrderType.MARKET,
            status=status,
            filled_quantity=filled_qty,
            fill_price=fill_price,
            fees=0.0,  # Alpaca doesn't return fees in order response
            slippage=0.0,
            parent_trade_id=trade.id,
        )

    def get_account_summary(self) -> dict:
        """Get Alpaca account summary."""
        headers = self._ensure_auth()
        try:
            resp = _requests.get(
                f"{self._base_url}/v2/account",
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "cash": float(data.get("cash", 0)),
                    "equity": float(data.get("equity", 0)),
                    "portfolio_value": float(data.get("portfolio_value", 0)),
                    "buying_power": float(data.get("buying_power", 0)),
                    "pnl": float(data.get("equity", 0)) - float(data.get("last_equity", 0)),
                    "status": data.get("status", ""),
                    "currency": data.get("currency", "USD"),
                }
        except Exception:
            pass
        return {"error": "Failed to fetch account summary"}

    def get_positions(self) -> dict[str, float]:
        """Get current positions from Alpaca."""
        headers = self._ensure_auth()
        try:
            resp = _requests.get(
                f"{self._base_url}/v2/positions",
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    p["symbol"]: float(p["qty"])
                    for p in data
                    if "symbol" in p and "qty" in p
                }
        except Exception:
            pass
        return {}

    def __repr__(self) -> str:
        return f"AlpacaBrokerAdapter(name={self.name})"
