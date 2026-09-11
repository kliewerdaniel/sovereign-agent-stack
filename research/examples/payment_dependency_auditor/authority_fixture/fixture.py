"""Adversarial payment infrastructure fixture for authority topology experiments.

This fixture models a payment system with deliberately distributed, undocumented,
conditional, temporal, and partially contradictory authority.

DISCLAIMER: This is a synthetic fixture for testing authority topology analysis.
It does not represent any real payment system.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration."""
    environment: str
    production: bool
    debug: bool
    api_endpoint: str
    fallback_endpoint: Optional[str] = None
    feature_flags: dict[str, bool] = field(default_factory=dict)
    credentials: dict[str, str] = field(default_factory=dict)


def load_environment_config(env: str) -> EnvironmentConfig:
    """Load configuration for an environment."""
    if env == "production":
        return EnvironmentConfig(
            environment="production",
            production=True,
            debug=False,
            api_endpoint="https://api.payment-provider.com/v1",
            fallback_endpoint="https://backup.payment-provider.com/v1",
            feature_flags={
                "new_fraud_service": True,
                "legacy_processor": False,
                "async_settlement": True,
                "enhanced_logging": True,
                "strict_validation": True,
            },
            credentials={
                "payment_api_key": "pk_live_***",
                "fraud_api_key": "fk_live_***",
                "settlement_key": "sk_live_***",
            },
        )
    elif env == "staging":
        return EnvironmentConfig(
            environment="staging",
            production=False,
            debug=True,
            api_endpoint="https://api-staging.payment-provider.com/v1",
            fallback_endpoint=None,
            feature_flags={
                "new_fraud_service": True,
                "legacy_processor": True,  # Still enabled in staging
                "async_settlement": True,
                "enhanced_logging": True,
                "strict_validation": False,
            },
            credentials={
                "payment_api_key": "pk_test_***",
                "fraud_api_key": "fk_test_***",
                "settlement_key": "sk_test_***",
            },
        )
    else:  # development
        return EnvironmentConfig(
            environment="development",
            production=False,
            debug=True,
            api_endpoint="http://localhost:8080/v1",
            fallback_endpoint=None,
            feature_flags={
                "new_fraud_service": False,  # Disabled in dev
                "legacy_processor": True,
                "async_settlement": False,
                "enhanced_logging": False,
                "strict_validation": False,
            },
            credentials={
                "payment_api_key": "pk_test_***",
                "fraud_api_key": "fk_test_***",
                "settlement_key": "sk_test_***",
            },
        )


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


class CheckoutService:
    """Checkout service - entry point for payments."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.payment_gateway = PaymentGateway(config)
        self.feature_flag_service = FeatureFlagService(config)

    def process_payment(self, order_id: str, amount: float, currency: str = "USD") -> dict:
        """Process a payment through checkout."""
        # Check feature flags
        if self.feature_flag_service.is_enabled("strict_validation"):
            self._validate_order(order_id, amount)

        # Route to payment gateway
        result = self.payment_gateway.charge(order_id, amount, currency)

        # Async notification (fire and forget)
        self._notify_async(order_id, result)

        return result

    def _validate_order(self, order_id: str, amount: float):
        """Validate order (only when strict_validation is enabled)."""
        if amount <= 0:
            raise ValueError("Amount must be positive")

    def _notify_async(self, order_id: str, result: dict):
        """Send async notification."""
        # In production, this would be a message queue
        pass


class PaymentGateway:
    """Payment gateway - routes to appropriate processor."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.fraud_service = FraudService(config)
        self.credential_store = CredentialStore(config)

    def charge(self, order_id: str, amount: float, currency: str) -> dict:
        """Charge a payment."""
        # Check fraud first
        fraud_result = self.fraud_service.check_transaction(order_id, amount, currency)
        if fraud_result.get("blocked"):
            return {"status": "blocked", "reason": "fraud_check_failed"}

        # Get credentials
        credentials = self.credential_store.get_payment_credentials()

        # Route based on feature flags
        if self.config.feature_flags.get("legacy_processor"):
            return self._charge_legacy(order_id, amount, currency, credentials)
        else:
            return self._charge_modern(order_id, amount, currency, credentials)

    def _charge_modern(self, order_id: str, amount: float, currency: str, credentials: dict) -> dict:
        """Charge using modern processor."""
        # Modern API call
        return {
            "status": "success",
            "processor": "modern",
            "transaction_id": f"txn_{order_id}",
            "amount": amount,
            "currency": currency,
        }

    def _charge_legacy(self, order_id: str, amount: float, currency: str, credentials: dict) -> dict:
        """Charge using legacy processor (still enabled in some environments)."""
        # Legacy API call - different endpoint
        return {
            "status": "success",
            "processor": "legacy",
            "transaction_id": f"txn_legacy_{order_id}",
            "amount": amount,
            "currency": currency,
        }


class FraudService:
    """Fraud detection service."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.customer_profile = CustomerProfileService(config)

    def check_transaction(self, order_id: str, amount: float, currency: str) -> dict:
        """Check transaction for fraud."""
        # Get customer profile
        profile = self.customer_profile.get_profile(order_id)

        # Simple rule-based check
        if amount > 10000 and not profile.get("verified"):
            return {"blocked": True, "reason": "high_amount_unverified"}

        return {"blocked": False}


class CustomerProfileService:
    """Customer profile service."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def get_profile(self, order_id: str) -> dict:
        """Get customer profile."""
        # In production, this would query a database
        return {
            "customer_id": f"cust_{order_id}",
            "verified": True,
            "risk_score": 0.1,
        }


class TaxService:
    """Tax calculation service."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def calculate_tax(self, amount: float, currency: str, region: str) -> dict:
        """Calculate tax for a transaction."""
        # Simplified tax calculation
        tax_rate = 0.08 if region == "US" else 0.0
        return {
            "tax_amount": amount * tax_rate,
            "tax_rate": tax_rate,
            "region": region,
        }


class LedgerService:
    """Ledger service - records transactions."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def record_transaction(self, transaction: dict) -> dict:
        """Record a transaction in the ledger."""
        return {
            "status": "recorded",
            "transaction_id": transaction.get("transaction_id"),
            "timestamp": "2026-09-09T00:00:00Z",
        }


class SettlementService:
    """Settlement service - handles fund transfers."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.credential_store = CredentialStore(config)

    def settle(self, transaction_id: str, amount: float, currency: str) -> dict:
        """Settle a transaction."""
        credentials = self.credential_store.get_settlement_credentials()

        if self.config.feature_flags.get("async_settlement"):
            self._settle_async(transaction_id, amount, currency, credentials)
            return {"status": "pending", "settlement_id": f"stl_{transaction_id}"}
        else:
            return self._settle_sync(transaction_id, amount, currency, credentials)

    def _settle_sync(self, transaction_id: str, amount: float, currency: str, credentials: dict) -> dict:
        """Synchronous settlement."""
        return {"status": "settled", "settlement_id": f"stl_{transaction_id}"}

    def _settle_async(self, transaction_id: str, amount: float, currency: str, credentials: dict):
        """Asynchronous settlement (background worker)."""
        # In production, this would enqueue a job
        pass


class NotificationService:
    """Notification service - sends notifications."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def send_notification(self, order_id: str, status: str, channel: str = "email") -> dict:
        """Send a notification."""
        return {
            "status": "sent",
            "order_id": order_id,
            "channel": channel,
        }


class FeatureFlagService:
    """Feature flag service."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def is_enabled(self, flag: str) -> bool:
        """Check if a feature flag is enabled."""
        return self.config.feature_flags.get(flag, False)


class CredentialStore:
    """Credential store - manages credentials."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def get_payment_credentials(self) -> dict:
        """Get payment credentials."""
        return {
            "api_key": self.config.credentials.get("payment_api_key"),
            "endpoint": self.config.api_endpoint,
        }

    def get_settlement_credentials(self) -> dict:
        """Get settlement credentials."""
        return {
            "api_key": self.config.credentials.get("settlement_key"),
            "endpoint": self.config.api_endpoint,
        }

    def get_fraud_credentials(self) -> dict:
        """Get fraud service credentials."""
        return {
            "api_key": self.config.credentials.get("fraud_api_key"),
        }


# ---------------------------------------------------------------------------
# Undocumented/Adversarial Components
# ---------------------------------------------------------------------------


class LegacyProcessor:
    """Legacy processor - undocumented but still active in some environments."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def process(self, order_id: str, amount: float, currency: str) -> dict:
        """Process payment via legacy path."""
        # This path is undocumented but still exists
        return {
            "status": "success",
            "processor": "legacy_undocumented",
            "transaction_id": f"txn_legacy_{order_id}",
        }


class AdminService:
    """Admin service - privileged operations."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.credential_store = CredentialStore(config)

    def refund_transaction(self, transaction_id: str, amount: float) -> dict:
        """Refund a transaction (privileged operation)."""
        credentials = self.credential_store.get_payment_credentials()
        return {
            "status": "refunded",
            "transaction_id": transaction_id,
            "amount": amount,
        }

    def void_transaction(self, transaction_id: str) -> dict:
        """Void a transaction (privileged operation)."""
        return {
            "status": "voided",
            "transaction_id": transaction_id,
        }


class BackgroundWorker:
    """Background worker - async operations."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.settlement_service = SettlementService(config)

    def process_settlement_queue(self):
        """Process settlement queue."""
        # Background worker processes settlements asynchronously
        pass

    def process_retry_queue(self):
        """Process retry queue for failed operations."""
        pass


class DeploymentHook:
    """Deployment hook - runs during deployment."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config

    def pre_deploy(self):
        """Run before deployment."""
        pass

    def post_deploy(self):
        """Run after deployment."""
        pass


class PluginManager:
    """Plugin manager - manages plugins."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.plugins: dict[str, Any] = {}

    def register_plugin(self, name: str, plugin: Any):
        """Register a plugin."""
        self.plugins[name] = plugin

    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a plugin."""
        return self.plugins.get(name)


# ---------------------------------------------------------------------------
# Fixture Builder
# ---------------------------------------------------------------------------


class PaymentFixtureBuilder:
    """Builds the payment infrastructure fixture."""

    def __init__(self, environment: str = "production"):
        self.config = load_environment_config(environment)
        self.checkout = CheckoutService(self.config)
        self.payment_gateway = PaymentGateway(self.config)
        self.fraud_service = FraudService(self.config)
        self.customer_profile = CustomerProfileService(self.config)
        self.tax_service = TaxService(self.config)
        self.ledger = LedgerService(self.config)
        self.settlement = SettlementService(self.config)
        self.notification = NotificationService(self.config)
        self.feature_flags = FeatureFlagService(self.config)
        self.credentials = CredentialStore(self.config)
        self.legacy_processor = LegacyProcessor(self.config)
        self.admin = AdminService(self.config)
        self.worker = BackgroundWorker(self.config)
        self.deployment_hook = DeploymentHook(self.config)
        self.plugin_manager = PluginManager(self.config)

    def get_all_services(self) -> dict:
        """Get all services in the fixture."""
        return {
            "checkout": self.checkout,
            "payment_gateway": self.payment_gateway,
            "fraud_service": self.fraud_service,
            "customer_profile": self.customer_profile,
            "tax_service": self.tax_service,
            "ledger": self.ledger,
            "settlement": self.settlement,
            "notification": self.notification,
            "feature_flags": self.feature_flags,
            "credentials": self.credentials,
            "legacy_processor": self.legacy_processor,
            "admin": self.admin,
            "worker": self.worker,
            "deployment_hook": self.deployment_hook,
            "plugin_manager": self.plugin_manager,
        }
