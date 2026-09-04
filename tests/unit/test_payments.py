"""Tests for the payments abstraction layer."""

import pytest

from sas.layers.payments import (
    PaymentRequirement,
    Receipt,
    SpendingLimit,
    PaymentAdapter,
    VirtualCardAdapter,
    MPPAdapter,
)


class TestPaymentRequirement:
    """Tests for payment requirement."""

    def test_create_one_shot_requirement(self) -> None:
        """One-shot payment requirement."""
        req = PaymentRequirement(
            resource="api.openai.com/v1/chat",
            price=0.002,
            currency="USD",
            methods=["card", "stablecoin"],
            cadence="one_shot",
            metadata={"model": "gpt-4o"},
        )
        assert req.price == 0.002
        assert req.cadence == "one_shot"

    def test_create_streaming_requirement(self) -> None:
        """Streaming payment requirement."""
        req = PaymentRequirement(
            resource="api.anthropic.com/v1/messages",
            price=0.001,
            currency="USD",
            methods=["stablecoin"],
            cadence="streaming",
            metadata={"model": "claude-sonnet"},
        )
        assert req.cadence == "streaming"


class TestVirtualCardAdapter:
    """Tests for the virtual card payment adapter."""

    def test_pay_within_limit(self) -> None:
        """Payment within spending limit succeeds."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        receipt = adapter.pay(req)
        assert receipt.status == "completed"
        assert receipt.amount == 10.0

    def test_pay_exceeds_daily_limit(self) -> None:
        """Payment exceeding daily limit is rejected."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=5.0, per_transaction=50.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="Daily limit"):
            adapter.pay(req)

    def test_pay_exceeds_transaction_limit(self) -> None:
        """Payment exceeding per-transaction limit is rejected."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=1000.0, per_transaction=10.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=50.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="transaction limit"):
            adapter.pay(req)

    def test_pay_unsupported_method(self) -> None:
        """Payment with unsupported method is rejected."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=10.0,
            currency="USD",
            methods=["stablecoin"],  # Virtual card only supports card
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="Unsupported payment method"):
            adapter.pay(req)

    def test_receipt_retrieval(self) -> None:
        """Can retrieve receipt by payment ID."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        receipt = adapter.pay(req)
        retrieved = adapter.receipt(receipt.payment_id)
        assert retrieved is not None
        assert retrieved.payment_id == receipt.payment_id

    def test_track_spending(self) -> None:
        """Adapter tracks cumulative daily spending."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        adapter.pay(req)
        adapter.pay(req)
        assert adapter.daily_spending == 20.0

    def test_remaining_daily(self) -> None:
        """Can check remaining daily budget."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=30.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        adapter.pay(req)
        assert adapter.remaining_daily == 70.0


class TestMPPAdapter:
    """Tests for the Machine Payments Protocol adapter."""

    def test_pay_with_stablecoin(self) -> None:
        """Pay with stablecoin via MPP."""
        adapter = MPPAdapter(
            settlement="stablecoin",
            limit=SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=0.5,
            currency="USD",
            methods=["stablecoin"],
            cadence="streaming",
            metadata={},
        )
        receipt = adapter.pay(req)
        assert receipt.status == "completed"
        assert receipt.method == "stablecoin"

    def test_pay_with_card(self) -> None:
        """Pay with card via Shared Payment Token."""
        adapter = MPPAdapter(
            settlement="card",
            limit=SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=0.5,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )
        receipt = adapter.pay(req)
        assert receipt.status == "completed"
        assert receipt.method == "card"

    def test_pay_exceeds_limit(self) -> None:
        """Payment exceeding limit is rejected."""
        adapter = MPPAdapter(
            settlement="stablecoin",
            limit=SpendingLimit(daily=1.0, per_transaction=0.1, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=10.0,
            currency="USD",
            methods=["stablecoin"],
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="limit"):
            adapter.pay(req)

    def test_pay_unsupported_settlement(self) -> None:
        """Payment with unsupported settlement method is rejected."""
        adapter = MPPAdapter(
            settlement="stablecoin",
            limit=SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=0.5,
            currency="USD",
            methods=["bnpl"],  # BNPL not supported by this adapter
            cadence="one_shot",
            metadata={},
        )
        with pytest.raises(ValueError, match="Unsupported"):
            adapter.pay(req)

    def test_streaming_payment(self) -> None:
        """Streaming payment cadence is tracked differently."""
        adapter = MPPAdapter(
            settlement="stablecoin",
            limit=SpendingLimit(daily=1000.0, per_transaction=1.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/stream",
            price=0.001,
            currency="USD",
            methods=["stablecoin"],
            cadence="streaming",
            metadata={},
        )
        # Should succeed for small amounts
        receipt = adapter.pay(req)
        assert receipt.status == "completed"

    def test_receipt_retrieval(self) -> None:
        """Can retrieve MPP receipt by payment ID."""
        adapter = MPPAdapter(
            settlement="stablecoin",
            limit=SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD"),
        )
        req = PaymentRequirement(
            resource="api.example.com/data",
            price=0.5,
            currency="USD",
            methods=["stablecoin"],
            cadence="one_shot",
            metadata={},
        )
        receipt = adapter.pay(req)
        retrieved = adapter.receipt(receipt.payment_id)
        assert retrieved is not None
        assert retrieved.payment_id == receipt.payment_id
        assert retrieved.amount == 0.5


class TestPaymentAdapterProtocol:
    """Tests for the PaymentAdapter protocol."""

    def test_virtual_card_implements_protocol(self) -> None:
        """VirtualCardAdapter implements PaymentAdapter protocol."""
        adapter = VirtualCardAdapter(
            provider="ramp",
            limit=SpendingLimit(daily=100.0, per_transaction=50.0, currency="USD"),
        )
        assert hasattr(adapter, "pay")
        assert hasattr(adapter, "authorize")
        assert hasattr(adapter, "receipt")

    def test_mpp_implements_protocol(self) -> None:
        """MPPAdapter implements PaymentAdapter protocol."""
        adapter = MPPAdapter(
            settlement="stablecoin",
            limit=SpendingLimit(daily=1000.0, per_transaction=100.0, currency="USD"),
        )
        assert hasattr(adapter, "pay")
        assert hasattr(adapter, "authorize")
        assert hasattr(adapter, "receipt")
