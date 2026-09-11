"""Adversarial composition fixture for epistemic dependency composition testing.

This fixture is deliberately designed so that:
1. Every individual edge is valid
2. Naive transitive reasoning produces false conclusions
3. The epistemic system must distinguish many types of dependency relationships

DEPENDENCY TYPES ENCODED:
- True direct: checkout → payment_gateway
- True transitive: checkout → payment_gateway → ledger
- False transitive: checkout → feature_flag_service (UI only, not payment)
- Optional: payment_gateway → tax_service (international only)
- Fail-open: payment_gateway → fraud_service (can skip if down)
- Fail-closed: payment_gateway → external_identity (must verify)
- Environment-specific: payment_gateway → tax_service (production only)
- Feature-flagged: checkout → new_payment_flow (behind flag)
- Cached: payment_gateway → customer_profile (cached in redis)
- Replicated: ledger → database (primary + replica)
- Async: payment_gateway → notification_service (via queue)
- Failure-only: refund_service → fraud_service (high-value only)
- Startup-only: payment_gateway → configuration_service (startup only)
- Deployment-only: payment_gateway → database_migration (deploy only)
- Observability-only: payment_gateway → metrics_service (monitoring only)
- Dead: payment_gateway → legacy_service (dead code)
- Substitutable: payment_gateway → payment_processor (Stripe or PayPal)
- Circular: customer_profile ↔ notification_service (circular ref)
- Shared infrastructure: multiple → redis (shared cache)
- Operation-dependent: payment_gateway → fraud_service (auth required, capture not)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import httpx
import psycopg2
import redis


# ===========================================================================
# SHARED INFRASTRUCTURE
# ===========================================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/payments")


def get_redis() -> redis.Redis:
    """Shared Redis instance - used by multiple services."""
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_database() -> psycopg2.extensions.connection:
    """Shared database - primary + replica configuration."""
    return psycopg2.connect(DATABASE_URL)


# ===========================================================================
# CONFIGURATION SERVICE (startup-only dependency)
# ===========================================================================

CONFIG_SERVICE_URL = os.environ.get("CONFIG_SERVICE_URL", "http://config:8080")


async def load_configuration(service_name: str) -> dict:
    """Load service configuration at startup.

    STARTUP-ONLY DEPENDENCY: This is only called during service initialization.
    The configuration is cached in memory and never refreshed from the service.
    Therefore, the service does NOT have a runtime dependency on config-service.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONFIG_SERVICE_URL}/config/{service_name}",
            timeout=5.0,
        )
        return response.json()


# ===========================================================================
# FEATURE FLAG SERVICE (false transitive dependency)
# ===========================================================================

FEATURE_FLAG_URL = os.environ.get("FEATURE_FLAG_URL", "http://feature-flags:8080")


async def check_feature_flag(flag_name: str) -> bool:
    """Check if a feature flag is enabled.

    FALSE TRANSITIVE DEPENDENCY: The checkout service calls feature-flag-service
    ONLY for UI rendering decisions (which button to show, which layout to use).
    The payment processing path does NOT depend on feature-flag-service.
    Therefore: checkout → feature-flag-service does NOT imply
    checkout operationally requires feature-flag-service for payment processing.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{FEATURE_FLAG_URL}/flags/{flag_name}",
            timeout=5.0,
        )
        return response.json().get("enabled", False)


# ===========================================================================
# CUSTOMER PROFILE SERVICE (cached dependency)
# ===========================================================================

CUSTOMER_PROFILE_URL = os.environ.get("CUSTOMER_PROFILE_URL", "http://customer-profile:8080")


async def get_customer_profile(customer_id: str) -> dict:
    """Get customer profile with caching.

    CACHED DEPENDENCY: The payment-gateway calls customer-profile through
    a Redis cache. If customer-profile is unavailable, the service can
    operate using cached data (with stale reads).
    Therefore: payment-gateway → customer-profile is a SOFT dependency.
    """
    # Check cache first
    cache_key = f"customer:{customer_id}"
    cached = get_redis().get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    # Cache miss - call service
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CUSTOMER_PROFILE_URL}/customers/{customer_id}",
            timeout=10.0,
        )
        profile = response.json()

        # Cache for future requests
        import json
        get_redis().setex(cache_key, 3600, json.dumps(profile))
        return profile


# ===========================================================================
# FRAUD SERVICE (fail-open dependency)
# ===========================================================================

FRAUD_SERVICE_URL = os.environ.get("FRAUD_SERVICE_URL", "http://fraud:8080")


async def evaluate_fraud(order_id: str, customer_id: str, amount: float) -> dict:
    """Evaluate transaction for fraud risk.

    FAIL-OPEN DEPENDENCY: If fraud-service is unavailable, the payment
    gateway can skip fraud evaluation and process the transaction anyway.
    This is a business decision: better to process legit transactions
    with risk of fraud than to block all transactions.
    Therefore: payment-gateway → fraud-service is OPTIONAL, not REQUIRED.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FRAUD_SERVICE_URL}/evaluate",
                json={"order_id": order_id, "customer_id": customer_id, "amount": amount},
                timeout=5.0,  # Short timeout - fail open
            )
            return response.json()
    except (httpx.TimeoutException, httpx.ConnectError):
        # FAIL OPEN: Return low risk if service unavailable
        return {"score": 0.0, "risk_level": "unknown", "fail_open": True}


# ===========================================================================
# EXTERNAL IDENTITY SERVICE (fail-closed dependency)
# ===========================================================================

EXTERNAL_IDENTITY_URL = os.environ.get("EXTERNAL_IDENTITY_URL", "http://identity:8080")


async def verify_identity(customer_id: str) -> dict:
    """Verify customer identity.

    FAIL-CLOSED DEPENDENCY: If external-identity is unavailable, the payment
    gateway MUST NOT process the transaction. Identity verification is
    a regulatory requirement (KYC/AML).
    Therefore: payment-gateway → external-identity is REQUIRED.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{EXTERNAL_IDENTITY_URL}/verify/{customer_id}",
            timeout=10.0,
        )
        return response.json()


# ===========================================================================
# TAX SERVICE (environment-specific dependency)
# ===========================================================================

TAX_SERVICE_URL = os.environ.get("TAX_SERVICE_URL", "http://tax:8080")


async def calculate_tax(amount: float, currency: str, country: str) -> dict:
    """Calculate tax for international transactions.

    ENVIRONMENT-SPECIFIC DEPENDENCY: Tax service is only called for
    non-USD transactions. In staging, all transactions are USD, so
    tax-service is never called. In production, tax-service is called
    for international transactions only.
    Therefore: payment-gateway → tax-service is ENVIRONMENT-SPECIFIC.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TAX_SERVICE_URL}/calculate",
            json={"amount": amount, "currency": currency, "country": country},
            timeout=10.0,
        )
        return response.json()


# ===========================================================================
# NOTIFICATION SERVICE (async dependency)
# ===========================================================================

NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notifications:8080")
QUEUE_URL = os.environ.get("QUEUE_URL", "http://queue:8080")


async def send_notification(customer_id: str, message: str) -> None:
    """Send notification asynchronously via queue.

    ASYNC DEPENDENCY: Notifications are sent via a message queue.
    The payment-gateway does NOT wait for notification delivery.
    If notification-service is down, messages accumulate in the queue
    and are delivered when the service recovers.
    Therefore: payment-gateway → notification-service is ASYNC (non-blocking).
    """
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{QUEUE_URL}/publish",
            json={
                "topic": "notifications",
                "payload": {"customer_id": customer_id, "message": message},
            },
            timeout=5.0,
        )


# ===========================================================================
# METRICS SERVICE (observability-only dependency)
# ===========================================================================

METRICS_SERVICE_URL = os.environ.get("METRICS_SERVICE_URL", "http://metrics:8080")


async def record_metric(metric_name: str, value: float, tags: dict = None) -> None:
    """Record a metric for observability.

    OBSERVABILITY-ONLY DEPENDENCY: Metrics are recorded for monitoring
    and alerting. If metrics-service is unavailable, the payment gateway
    continues to operate normally. Metrics are not required for business logic.
    Therefore: payment-gateway → metrics-service is OBSERVABILITY-ONLY.
    """
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{METRICS_SERVICE_URL}/metrics",
                json={"name": metric_name, "value": value, "tags": tags or {}},
                timeout=2.0,  # Short timeout - don't block business logic
            )
    except Exception:
        # Silently drop metrics if service unavailable
        pass


# ===========================================================================
# LEGACY SERVICE (dead dependency)
# ===========================================================================

LEGACY_SERVICE_URL = os.environ.get("LEGACY_SERVICE_URL", "http://legacy:8080")


async def legacy_process(order_id: str) -> dict:
    """Legacy payment processing - NEVER CALLED.

    DEAD DEPENDENCY: This function exists in the codebase but is never
    called. The import is maintained for backward compatibility but
    the code path is unreachable.
    Therefore: payment-gateway → legacy-service is DEAD.
    """
    raise NotImplementedError("This function is deprecated and never called")


# ===========================================================================
# PAYMENT PROCESSOR (substitutable dependency)
# ===========================================================================

STRIPE_URL = os.environ.get("STRIPE_URL", "https://api.stripe.com")
PAYPAL_URL = os.environ.get("PAYPAL_URL", "https://api.paypal.com")


async def process_with_stripe(amount: float, currency: str, token: str) -> dict:
    """Process payment via Stripe."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRIPE_URL}/v1/charges",
            json={"amount": int(amount * 100), "currency": currency, "source": token},
            timeout=30.0,
        )
        return response.json()


async def process_with_paypal(amount: float, currency: str, token: str) -> dict:
    """Process payment via PayPal."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_URL}/v2/payments",
            json={"amount": {"value": str(amount), "currency": currency}, "token": token},
            timeout=30.0,
        )
        return response.json()


async def process_payment(amount: float, currency: str, token: str, provider: str = "stripe") -> dict:
    """Process payment via configurable provider.

    SUBSTITUTABLE DEPENDENCY: The payment gateway can use either Stripe
    or PayPal. If one is unavailable, it can failover to the other.
    Therefore: payment-gateway → payment-processor is SUBSTITUTABLE.
    """
    if provider == "stripe":
        try:
            return await process_with_stripe(amount, currency, token)
        except httpx.TimeoutException:
            # Failover to PayPal
            return await process_with_paypal(amount, currency, token)
    else:
        return await process_with_paypal(amount, currency, token)


# ===========================================================================
# DATABASE MIGRATION (deployment-only dependency)
# ===========================================================================

async def run_database_migrations() -> None:
    """Run database migrations during deployment.

    DEPLOYMENT-ONLY DEPENDENCY: This is only called during deployment,
    not during runtime. The payment gateway does not call this function
    during normal operation.
    Therefore: payment-gateway → database-migration is DEPLOYMENT-ONLY.
    """
    # This would run migrations in a real system
    pass


# ===========================================================================
# CHECKOUT SERVICE
# ===========================================================================

@dataclass
class CheckoutRequest:
    order_id: str
    customer_id: str
    amount: float
    currency: str
    payment_token: str


async def process_checkout(request: CheckoutRequest) -> dict:
    """Process a checkout request.

    DEPENDENCIES:
    - payment_gateway (TRUE DIRECT - required for payment processing)
    - feature_flag_service (FALSE TRANSITIVE - UI only, not payment)
    - configuration_service (STARTUP-ONLY - cached after startup)
    """
    # UI decision - feature flag (FALSE TRANSITIVE for payment)
    new_flow = await check_feature_flag("new-checkout-flow")

    # Process payment (TRUE DIRECT dependency)
    result = await process_payment(
        amount=request.amount,
        currency=request.currency,
        token=request.payment_token,
    )

    return {
        "order_id": request.order_id,
        "status": "completed",
        "new_flow_used": new_flow,
        "payment_result": result,
    }


# ===========================================================================
# PAYMENT GATEWAY SERVICE
# ===========================================================================

async def authorize_payment(
    order_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    payment_token: str,
) -> dict:
    """Authorize a payment.

    DEPENDENCIES:
    - external_identity (FAIL-CLOSED - must verify)
    - fraud_service (FAIL-OPEN - can skip if down)
    - customer_profile (CACHED - can use cache)
    - tax_service (ENVIRONMENT-SPECIFIC - international only)
    - payment_processor (SUBSTITUTABLE - Stripe or PayPal)
    - notification_service (ASYNC - non-blocking)
    - metrics_service (OBSERVABILITY-ONLY - monitoring)
    - legacy_service (DEAD - never called)
    - database_migration (DEPLOYMENT-ONLY - not runtime)
    - configuration_service (STARTUP-ONLY - cached)
    """
    # FAIL-CLOSED: Must verify identity
    identity = await verify_identity(customer_id)
    if not identity.get("verified"):
        raise ValueError("Identity not verified")

    # FAIL-OPEN: Fraud evaluation (can skip if down)
    fraud_result = await evaluate_fraud(order_id, customer_id, amount)

    # CACHED: Customer profile (can use cache)
    profile = await get_customer_profile(customer_id)

    # ENVIRONMENT-SPECIFIC: Tax calculation (international only)
    tax_info = None
    if currency != "USD":
        tax_info = await calculate_tax(amount, currency, profile.get("country", "US"))

    # SUBSTITUTABLE: Payment processor (Stripe or PayPal)
    payment_result = await process_payment(amount, currency, payment_token)

    # ASYNC: Notification (non-blocking)
    await send_notification(customer_id, f"Payment of {amount} {currency} processed")

    # OBSERVABILITY-ONLY: Metrics (monitoring)
    await record_metric("payment_authorized", amount, {"currency": currency})

    return {
        "order_id": order_id,
        "status": "authorized",
        "fraud_score": fraud_result.get("score"),
        "tax": tax_info,
        "payment": payment_result,
    }


# ===========================================================================
# LEDGER SERVICE
# ===========================================================================

async def record_transaction(order_id: str, customer_id: str, amount: float, currency: str) -> dict:
    """Record a transaction in the ledger.

    DEPENDENCIES:
    - database (REPLICATED - primary + replica)
    """
    # REPLICATED: Database with primary + replica
    conn = get_database()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ledger_transactions (order_id, customer_id, amount, currency)
                VALUES (%s, %s, %s, %s)
                RETURNING transaction_id
                """,
                (order_id, customer_id, amount, currency),
            )
            transaction_id = cur.fetchone()[0]
            conn.commit()
            return {"transaction_id": str(transaction_id), "status": "recorded"}
    finally:
        conn.close()


# ===========================================================================
# REFUND SERVICE
# ===========================================================================

async def process_refund(order_id: str, customer_id: str, amount: float) -> dict:
    """Process a refund.

    DEPENDENCIES:
    - payment_gateway (TRUE DIRECT - to reverse charge)
    - fraud_service (FAILURE-ONLY - only for high-value refunds)
    - ledger (TRUE DIRECT - to record refund)
    """
    # TRUE DIRECT: Reverse charge via payment gateway
    # (In real system, this would call payment_gateway.reverse())

    # FAILURE-ONLY: Fraud evaluation for high-value refunds
    if amount > 1000:
        fraud_result = await evaluate_fraud(order_id, customer_id, amount)
        if fraud_result.get("score", 0) > 0.8:
            raise ValueError("High fraud risk - refund blocked")

    # TRUE DIRECT: Record refund in ledger
    ledger_result = await record_transaction(order_id, customer_id, -amount, "USD")

    return {"order_id": order_id, "status": "refunded", "ledger": ledger_result}
