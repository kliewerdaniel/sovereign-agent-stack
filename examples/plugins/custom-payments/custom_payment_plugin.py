"""Example payment adapter plugin.

Demonstrates the SAS plugin system with a simple mock payment processor.

To use:
    mkdir -p ~/.sas/plugins/
    cp custom_payment_plugin.py ~/.sas/plugins/
    python -c "from sas.plugins import auto_register_discovered, get_plugin; auto_register_discovered(); print(get_plugin('layer_8_payments'))"
"""

from sas.plugins import LayerPlugin, PluginSource, register_plugin
from sas.layers.payments import (
    PaymentAdapter,
    PaymentRequirement,
    Receipt,
    SpendingLimit,
)


class CustomPaymentProcessor(PaymentAdapter):
    """A custom payment adapter for a hypothetical payment processor.

    This demonstrates how to implement a payment adapter plugin.
    In production, this would call a real payment API.
    """

    def __init__(self, config: dict = None) -> None:
        self.config = config or {}
        self._daily_spending = 0.0
        self._receipts: dict[str, Receipt] = {}
        self._limit = SpendingLimit(
            daily=self.config.get("daily_limit", 500.0),
            per_transaction=self.config.get("per_transaction_limit", 100.0),
            currency=self.config.get("currency", "USD"),
        )

    def pay(self, requirement: PaymentRequirement) -> Receipt:
        """Process a payment via the custom processor."""
        if requirement.price > self._limit.per_transaction:
            raise ValueError(
                f"Payment ${requirement.price:.2f} exceeds per-transaction limit "
                f"${self._limit.per_transaction:.2f}"
            )

        if self._daily_spending + requirement.price > self._limit.daily:
            raise ValueError(
                f"Daily limit exceeded. Remaining: ${self._limit.daily - self._daily_spending:.2f}"
            )

        import time
        import uuid

        payment_id = f"custom_{uuid.uuid4().hex[:12]}"
        receipt = Receipt(
            payment_id=payment_id,
            resource=requirement.resource,
            amount=requirement.price,
            currency=requirement.currency,
            method="custom_processor",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            status="completed",
        )

        self._daily_spending += requirement.price
        self._receipts[payment_id] = receipt
        return receipt

    def authorize(self, limit: SpendingLimit) -> None:
        """Update spending limits."""
        self._limit = limit

    def receipt(self, payment_id: str) -> Receipt | None:
        """Get a receipt by ID."""
        return self._receipts.get(payment_id)


# Plugin metadata — used by the plugin discovery system
SAS_PLUGIN = {
    "name": "custom-payment-processor",
    "layer_id": "layer_8_payments",
    "version": "0.1.0",
    "description": "Example custom payment adapter plugin",
    "author": "SAS Community",
    "url": "https://github.com/example/sas-payments-custom",
}

# Register the plugin when the module is loaded
register_plugin(LayerPlugin(
    name=SAS_PLUGIN["name"],
    layer_id=SAS_PLUGIN["layer_id"],
    version=SAS_PLUGIN["version"],
    description=SAS_PLUGIN["description"],
    source=PluginSource.LOCAL,
    author=SAS_PLUGIN["author"],
    url=SAS_PLUGIN["url"],
    factory=lambda: CustomPaymentProcessor(),
))
