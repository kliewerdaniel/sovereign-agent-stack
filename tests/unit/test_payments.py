# — Unit tests for the Payments Abstraction (Phase 4) —

import pytest
import time
from sas.layers.payments import (
    MPPAdapter,
    PaymentAdapter,
    PaymentRequirement,
    Receipt,
    SpendingLimit,
    VirtualCardAdapter,
)


# ── VirtualCardAdapter ─────────────────────────────────────────────────────────

class TestVirtualCardAdapter:
    def test_pay_success(self):
        adapter = VirtualCardAdapter()
        req = PaymentRequirement(
            resource="openai-api",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        receipt = adapter.pay(req)
        assert receipt.status == "completed"
        assert receipt.amount == 10.0
        assert receipt.method == "card"
        assert receipt.resource == "openai-api"

    def test_pay_unsupported_method_raises(self):
        adapter = VirtualCardAdapter()
        req = PaymentRequirement(
            resource="test",
            price=10.0,
            currency="USD",
            methods=["stablecoin"],
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="Unsupported payment method"):
            adapter.pay(req)

    def test_pay_exceeds_per_transaction_limit(self):
        adapter = VirtualCardAdapter()
        req = PaymentRequirement(
            resource="test",
            price=100.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="exceeds per-transaction limit"):
            adapter.pay(req)

    def test_pay_exceeds_daily_limit(self):
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=50.0, per_transaction=50.0, currency="USD"))
        req1 = PaymentRequirement("r1", 30.0, "USD", ["card"], "one_shot", {})
        req2 = PaymentRequirement("r2", 30.0, "USD", ["card"], "one_shot", {})
        adapter.pay(req1)
        with pytest.raises(ValueError, match="Daily limit exceeded"):
            adapter.pay(req2)

    def test_authorize_updates_limit(self):
        adapter = VirtualCardAdapter()
        new_limit = SpendingLimit(daily=500.0, per_transaction=200.0, currency="USD")
        adapter.authorize(new_limit)
        req = PaymentRequirement("test", 150.0, "USD", ["card"], "one_shot", {})
        receipt = adapter.pay(req)
        assert receipt.amount == 150.0

    def test_receipt_retrieval(self):
        adapter = VirtualCardAdapter()
        req = PaymentRequirement("test", 5.0, "USD", ["card"], "one_shot", {})
        receipt = adapter.pay(req)
        retrieved = adapter.receipt(receipt.payment_id)
        assert retrieved is not None
        assert retrieved.payment_id == receipt.payment_id

    def test_receipt_unknown_returns_none(self):
        adapter = VirtualCardAdapter()
        assert adapter.receipt("nonexistent") is None

    def test_daily_spending_tracks(self):
        adapter = VirtualCardAdapter()
        assert adapter.daily_spending == 0.0
        adapter.pay(PaymentRequirement("r", 10.0, "USD", ["card"], "one_shot", {}))
        assert adapter.daily_spending == 10.0
        adapter.pay(PaymentRequirement("r", 5.0, "USD", ["card"], "one_shot", {}))
        assert adapter.daily_spending == 15.0

    def test_remaining_daily(self):
        adapter = VirtualCardAdapter()
        assert adapter.remaining_daily == 100.0
        adapter.pay(PaymentRequirement("r", 30.0, "USD", ["card"], "one_shot", {}))
        assert adapter.remaining_daily == 70.0


# ── MPPAdapter ─────────────────────────────────────────────────────────────────

class TestMPPAdapter:
    def test_pay_stablecoin(self):
        adapter = MPPAdapter(settlement="stablecoin")
        req = PaymentRequirement(
            resource="api-call",
            price=0.50,
            currency="USD",
            methods=["stablecoin", "card"],
            cadence="one_shot",
            metadata={},
        )
        receipt = adapter.pay(req)
        assert receipt.method == "stablecoin"
        assert receipt.amount == 0.50

    def test_pay_card(self):
        adapter = MPPAdapter(settlement="card")
        req = PaymentRequirement("test", 25.0, "USD", ["card"], "one_shot", {})
        receipt = adapter.pay(req)
        assert receipt.method == "card"

    def test_pay_bnpl(self):
        adapter = MPPAdapter(settlement="bnpl")
        req = PaymentRequirement("test", 75.0, "USD", ["bnpl"], "one_shot", {})
        receipt = adapter.pay(req)
        assert receipt.method == "bnpl"

    def test_pay_unsupported_settlement_raises(self):
        adapter = MPPAdapter(settlement="card")
        req = PaymentRequirement("test", 10.0, "USD", ["stablecoin"], "one_shot", {})
        with pytest.raises(ValueError, match="Unsupported payment method"):
            adapter.pay(req)

    def test_pay_exceeds_limit(self):
        adapter = MPPAdapter(settlement="stablecoin")
        req = PaymentRequirement("test", 500.0, "USD", ["stablecoin"], "one_shot", {})
        with pytest.raises(ValueError, match="exceeds per-transaction limit"):
            adapter.pay(req)

    def test_pay_exceeds_daily(self):
        adapter = MPPAdapter(settlement="stablecoin", limit=SpendingLimit(daily=50.0, per_transaction=50.0, currency="USD"))
        adapter.pay(PaymentRequirement("r1", 30.0, "USD", ["stablecoin"], "one_shot", {}))
        with pytest.raises(ValueError, match="Daily limit exceeded"):
            adapter.pay(PaymentRequirement("r2", 30.0, "USD", ["stablecoin"], "one_shot", {}))

    def test_authorize(self):
        adapter = MPPAdapter(settlement="stablecoin")
        adapter.authorize(SpendingLimit(daily=500.0, per_transaction=200.0, currency="USD"))
        receipt = adapter.pay(PaymentRequirement("test", 150.0, "USD", ["stablecoin"], "one_shot", {}))
        assert receipt.amount == 150.0

    def test_receipt(self):
        adapter = MPPAdapter(settlement="stablecoin")
        receipt = adapter.pay(PaymentRequirement("test", 1.0, "USD", ["stablecoin"], "one_shot", {}))
        assert adapter.receipt(receipt.payment_id) is not None

    def test_daily_spending(self):
        adapter = MPPAdapter(settlement="stablecoin")
        assert adapter.daily_spending == 0.0
        adapter.pay(PaymentRequirement("r", 5.0, "USD", ["stablecoin"], "one_shot", {}))
        assert adapter.daily_spending == 5.0


# ── Cross-adapter behavior ─────────────────────────────────────────────────────

class TestCrossAdapter:
    def test_both_adapters_same_interface(self):
        """Both adapters expose pay/authorize/receipt/daily_spending/remaining_daily."""
        for adapter_cls in [VirtualCardAdapter, MPPAdapter]:
            adapter = adapter_cls()
            assert hasattr(adapter, "pay")
            assert hasattr(adapter, "authorize")
            assert hasattr(adapter, "receipt")
            assert hasattr(adapter, "daily_spending")
            assert hasattr(adapter, "remaining_daily")

    def test_payment_requirement_dataclass(self):
        req = PaymentRequirement(
            resource="test",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="recurring",
            metadata={"plan": "pro"},
        )
        assert req.resource == "test"
        assert req.cadence == "recurring"
        assert req.metadata["plan"] == "pro"

    def test_spending_limit_dataclass(self):
        limit = SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD")
        assert limit.daily == 100.0
        assert limit.per_transaction == 50.0

    def test_receipt_timestamp(self):
        adapter = VirtualCardAdapter()
        receipt = adapter.pay(PaymentRequirement("r", 1.0, "USD", ["card"], "one_shot", {}))
        assert "T" in receipt.timestamp  # ISO 8601
