"""Tests for the broker adapter abstraction and Alpaca paper adapter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from sas.quant.broker import BrokerConfig, Order, OrderStatus, OrderType, SimulatedBroker
from sas.quant.broker.adapter import BrokerAdapter
from sas.quant.risk import RiskEngine, RiskPolicy, TradeIntent


class TestSimulatedBrokerAdapter:
    """Tests that SimulatedBroker implements BrokerAdapter."""

    def test_is_broker_adapter(self):
        broker = SimulatedBroker()
        assert isinstance(broker, BrokerAdapter)

    def test_name(self):
        broker = SimulatedBroker()
        assert broker.name == "simulated"

    def test_is_not_live(self):
        broker = SimulatedBroker()
        assert broker.is_live is False

    def test_submit_trade(self):
        broker = SimulatedBroker()
        trade = TradeIntent(
            symbol="AAPL",
            side="buy",
            quantity=10,
            price_assumption=150.0,
            reason="Test trade",
        )
        order = broker.submit_trade(trade)
        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.quantity == 10
        assert order.status == OrderStatus.FILLED
        assert order.parent_trade_id == trade.id

    def test_get_account_summary(self):
        broker = SimulatedBroker()
        summary = broker.get_account_summary()
        assert "cash" in summary
        assert "equity" in summary
        assert summary["cash"] == 100_000.0

    def test_get_positions(self):
        broker = SimulatedBroker()
        broker.submit_trade(
            TradeIntent(symbol="AAPL", side="buy", quantity=10, price_assumption=150.0)
        )
        positions = broker.get_positions()
        assert "AAPL" in positions
        assert positions["AAPL"] == 10


class TestAlpacaBrokerAdapter:
    """Tests for the Alpaca paper adapter (without live connection)."""

    def test_import(self):
        from sas.quant.broker.alpaca import AlpacaBrokerAdapter
        assert AlpacaBrokerAdapter is not None

    def test_is_broker_adapter(self):
        from sas.quant.broker.alpaca import AlpacaBrokerAdapter
        adapter = AlpacaBrokerAdapter(key_id="test", secret_key="test")
        assert isinstance(adapter, BrokerAdapter)

    def test_name(self):
        from sas.quant.broker.alpaca import AlpacaBrokerAdapter
        adapter = AlpacaBrokerAdapter(key_id="test", secret_key="test")
        assert adapter.name == "alpaca-paper"

    def test_is_live(self):
        from sas.quant.broker.alpaca import AlpacaBrokerAdapter
        adapter = AlpacaBrokerAdapter(key_id="test", secret_key="test")
        assert adapter.is_live is True

    def test_no_credentials_raises(self):
        from sas.quant.broker.alpaca import AlpacaBrokerAdapter, _get_alpaca_credentials
        # Clear env vars
        import os
        old_key = os.environ.pop("APCA_API_KEY_ID", None)
        old_secret = os.environ.pop("APCA_API_SECRET_KEY", None)
        try:
            with pytest.raises(ValueError, match="Alpaca credentials not found"):
                _get_alpaca_credentials()
        finally:
            if old_key:
                os.environ["APCA_API_KEY_ID"] = old_key
            if old_secret:
                os.environ["APCA_API_SECRET_KEY"] = old_secret

    def test_repr_no_credentials(self):
        from sas.quant.broker.alpaca import AlpacaBrokerAdapter
        adapter = AlpacaBrokerAdapter(key_id="test", secret_key="test")
        repr_str = repr(adapter)
        assert "alpaca-paper" in repr_str
        assert "test" not in repr_str  # credentials should not leak
