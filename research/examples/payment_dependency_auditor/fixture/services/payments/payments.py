"""Payments Service - Core payment processing with authorization and capture."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import psycopg2
import redis


# --- Database connections ---

PAYMENTS_DB_URL = os.environ.get(
    "PAYMENTS_DATABASE_URL", "postgresql://localhost:5432/payments"
)

LEDGER_DB_URL = os.environ.get(
    "LEDGER_DATABASE_URL", "postgresql://localhost:5432/ledger"
)

# --- Service endpoints (documented) ---

LEDGER_SERVICE_URL = os.environ.get(
    "LEDGER_SERVICE_URL", "http://ledger:8080"
)

FRAUD_SERVICE_URL = os.environ.get(
    "FRAUD_SERVICE_URL", "http://fraud:8080"
)

# --- Service endpoints (UNDOCUMENTED - discovered in code) ---

CUSTOMER_PROFILE_URL = os.environ.get(
    "CUSTOMER_PROFILE_URL", "http://customer-profile:8080"
)

FEATURE_FLAGS_URL = os.environ.get(
    "FEATURE_FLAGS_URL", "http://feature-flags:8080"
)

EXTERNAL_TAX_URL = os.environ.get(
    "EXTERNAL_TAX_URL", "http://tax-service:8080"
)

# --- Redis connection for caching and rate limiting ---

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# --- External payment provider ---

PAYMENT_PROVIDER_URL = os.environ.get(
    "PAYMENT_PROVIDER_URL", "https://api.stripe.com"
)

PAYMENT_PROVIDER_KEY = os.environ.get("PAYMENT_PROVIDER_KEY", "sk_test_...")


@dataclass
class PaymentAuthorization:
    authorization_id: str
    order_id: str
    customer_id: str
    amount: float
    currency: str
    status: str
    provider_reference: str
    created_at: datetime
    fraud_score: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class CaptureRequest:
    authorization_id: str
    amount: float
    ledger_entry_id: Optional[str] = None


def get_payments_db():
    """Get payments database connection."""
    return psycopg2.connect(PAYMENTS_DB_URL)


def get_redis() -> redis.Redis:
    """Get Redis connection for caching."""
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def check_feature_flag(flag_name: str, environment: str = "production") -> bool:
    """Check if a feature flag is enabled.

    UNDOCUMENTED: Payments service uses feature flags for gradual rollout
    of new payment methods. Architecture docs don't mention this dependency.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{FEATURE_FLAGS_URL}/flags/{flag_name}",
            params={"env": environment},
            timeout=5.0,
        )
        return response.json().get("enabled", False)


async def get_customer_profile(customer_id: str) -> dict:
    """Get customer profile for KYC verification.

    UNDOCUMENTED: Payments service calls customer-profile directly
    for KYC/AML checks. Not shown in architecture diagrams.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CUSTOMER_PROFILE_URL}/customers/{customer_id}/kyc",
            timeout=10.0,
        )
        return response.json()


async def calculate_tax(amount: float, currency: str, country: str) -> dict:
    """Calculate tax for international transactions.

    UNDOCUMENTED: External tax service integration for VAT/sales tax.
    Only used for non-US transactions. Not documented in architecture.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EXTERNAL_TAX_URL}/calculate",
            json={"amount": amount, "currency": currency, "country": country},
            timeout=10.0,
        )
        return response.json()


async def evaluate_fraud(order_id: str, customer_id: str, amount: float) -> dict:
    """Evaluate transaction for fraud risk.

    DOCUMENTED: This is a documented dependency.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FRAUD_SERVICE_URL}/evaluate",
            json={
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": amount,
            },
            timeout=15.0,
        )
        return response.json()


async def authorize_payment(
    order_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    payment_method: str = "card",
) -> PaymentAuthorization:
    """Authorize a payment.

    Documented dependencies: ledger, fraud
    Actual dependencies: ledger, fraud, customer-profile, feature-flags, external-tax
    """
    # Check feature flag for new payment methods (UNDOCUMENTED)
    new_methods_enabled = await check_feature_flag("new-payment-methods")

    # KYC verification (UNDOCUMENTED)
    customer = await get_customer_profile(customer_id)
    if customer.get("kyc_status") != "verified":
        raise ValueError(f"Customer {customer_id} KYC not verified")

    # Fraud evaluation (DOCUMENTED)
    fraud_result = await evaluate_fraud(order_id, customer_id, amount)
    fraud_score = fraud_result.get("score", 1.0)

    if fraud_score > 0.8:
        raise ValueError(f"Transaction blocked: fraud score {fraud_score}")

    # Tax calculation for international (UNDOCUMENTED)
    tax_info = None
    if currency != "USD":
        tax_info = await calculate_tax(amount, currency, customer.get("country", "US"))

    # Authorize with external provider
    provider_ref = await _call_payment_provider(
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        customer_id=customer_id,
    )

    # Record in ledger (DOCUMENTED)
    ledger_entry = await _record_in_ledger(
        order_id=order_id,
        customer_id=customer_id,
        amount=amount,
        currency=currency,
        tax_amount=tax_info.get("tax_amount", 0.0) if tax_info else 0.0,
    )

    # Cache authorization in Redis (UNDOCUMENTED)
    redis_client = get_redis()
    redis_client.setex(
        f"auth:{order_id}",
        timedelta(hours=24),
        json.dumps({
            "order_id": order_id,
            "amount": amount,
            "provider_ref": provider_ref,
        }),
    )

    return PaymentAuthorization(
        authorization_id=f"auth_{order_id}",
        order_id=order_id,
        customer_id=customer_id,
        amount=amount,
        currency=currency,
        status="authorized",
        provider_reference=provider_ref,
        created_at=datetime.utcnow(),
        fraud_score=fraud_score,
        metadata={
            "tax_info": tax_info,
            "new_methods_enabled": new_methods_enabled,
            "ledger_entry_id": ledger_entry.get("entry_id"),
        },
    )


async def _call_payment_provider(
    amount: float,
    currency: str,
    payment_method: str,
    customer_id: str,
) -> str:
    """Call external payment provider (Stripe/similar)."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENT_PROVIDER_URL}/v1/charges",
            json={
                "amount": int(amount * 100),
                "currency": currency,
                "payment_method": payment_method,
                "customer": customer_id,
            },
            headers={"Authorization": f"Bearer {PAYMENT_PROVIDER_KEY}"},
            timeout=30.0,
        )
        return response.json().get("id", "unknown")


async def _record_in_ledger(
    order_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    tax_amount: float,
) -> dict:
    """Record transaction in ledger service.

    DOCUMENTED dependency.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LEDGER_SERVICE_URL}/entries",
            json={
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": amount,
                "currency": currency,
                "tax_amount": tax_amount,
                "type": "payment",
            },
            timeout=10.0,
        )
        return response.json()


async def capture_payment(authorization_id: str, amount: float) -> dict:
    """Capture a previously authorized payment.

    Note: capture does NOT require fraud re-evaluation.
    This is a temporal dependency difference.
    """
    # Retrieve authorization from Redis cache (UNDOCUMENTED)
    redis_client = get_redis()
    cached = redis_client.get(f"auth:{authorization_id.replace('auth_', '')}")

    if not cached:
        raise ValueError(f"Authorization {authorization_id} not found or expired")

    auth_data = json.loads(cached)

    # Capture with provider
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENT_PROVIDER_URL}/v1/captures",
            json={
                "charge_id": auth_data["provider_ref"],
                "amount": int(amount * 100),
            },
            headers={"Authorization": f"Bearer {PAYMENT_PROVIDER_KEY}"},
            timeout=30.0,
        )

    return response.json()


async def process_refund(order_id: str, amount: float) -> dict:
    """Process a refund.

    Documented dependencies: payments, ledger
    Actual dependencies: payments, ledger, customer-profile (for refund eligibility)
    """
    # Check refund eligibility via customer profile (UNDOCUMENTED)
    conn = get_payments_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT customer_id, provider_ref FROM authorizations WHERE order_id = %s",
                (order_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No authorization found for order {order_id}")
            customer_id, provider_ref = row
    finally:
        conn.close()

    # Refund with provider
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENT_PROVIDER_URL}/v1/refunds",
            json={
                "charge": provider_ref,
                "amount": int(amount * 100),
            },
            headers={"Authorization": f"Bearer {PAYMENT_PROVIDER_KEY}"},
            timeout=30.0,
        )

    # Record refund in ledger (DOCUMENTED)
    await _record_refund_in_ledger(order_id, customer_id, amount)

    return response.json()


async def _record_refund_in_ledger(
    order_id: str, customer_id: str, amount: float
) -> dict:
    """Record refund in ledger."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LEDGER_SERVICE_URL}/entries",
            json={
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": -amount,
                "type": "refund",
            },
            timeout=10.0,
        )
        return response.json()
