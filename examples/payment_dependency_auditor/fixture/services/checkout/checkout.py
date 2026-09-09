"""Checkout Service - Customer order intake and payment initiation."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
import psycopg2


# Database connection for order storage
DB_URL = os.environ.get("CHECKOUT_DATABASE_URL", "postgresql://localhost:5432/checkout")

# Payments service endpoint
PAYMENTS_SERVICE_URL = os.environ.get(
    "PAYMENTS_SERVICE_URL", "http://payments:8080"
)

# Customer profile service (documented)
CUSTOMER_SERVICE_URL = os.environ.get(
    "CUSTOMER_SERVICE_URL", "http://customer-profile:8080"
)

# Feature flags service (NOT documented - dependency discovered in code)
FEATURE_FLAGS_URL = os.environ.get(
    "FEATURE_FLAGS_URL", "http://feature-flags:8080"
)

# Fraud service endpoint (documented)
FRAUD_SERVICE_URL = os.environ.get(
    "FRAUD_SERVICE_URL", "http://fraud:8080"
)


@dataclass
class Order:
    order_id: str
    customer_id: str
    amount: float
    currency: str
    items: list[dict]


@dataclass
class PaymentRequest:
    order_id: str
    customer_id: str
    amount: float
    currency: str
    payment_method: str


def get_db_connection():
    """Get database connection for order storage."""
    return psycopg2.connect(DB_URL)


async def check_feature_flag(flag_name: str) -> bool:
    """Check if a feature flag is enabled.

    UNDOCUMENTED: This service calls feature-flags service directly.
    Documentation says checkout only depends on payments.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{FEATURE_FLAGS_URL}/flags/{flag_name}",
            timeout=5.0,
        )
        return response.json().get("enabled", False)


async def verify_customer(customer_id: str) -> dict:
    """Verify customer exists and is in good standing."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}",
            timeout=10.0,
        )
        return response.json()


async def initiate_payment(order: Order) -> dict:
    """Initiate payment for an order.

    Documented dependency: payments service only.
    Actual dependencies: payments, customer-profile, feature-flags.
    """
    # Check feature flag for new checkout flow (UNDOCUMENTED)
    new_flow_enabled = await check_feature_flag("new-checkout-flow")

    # Verify customer (documented)
    customer = await verify_customer(order.customer_id)

    if customer.get("status") != "active":
        raise ValueError(f"Customer {order.customer_id} is not active")

    # Build payment request
    payment_request = PaymentRequest(
        order_id=order.order_id,
        customer_id=order.customer_id,
        amount=order.amount,
        currency=order.currency,
        payment_method=customer.get("default_payment_method", "card"),
    )

    # Send to payments service (documented)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENTS_SERVICE_URL}/authorize",
            json=payment_request.__dict__,
            timeout=30.0,
        )

    return response.json()


async def get_order_status(order_id: str) -> dict:
    """Get current status of an order."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, payment_id FROM orders WHERE order_id = %s",
                (order_id,),
            )
            row = cur.fetchone()
            if row:
                return {"order_id": order_id, "status": row[0], "payment_id": row[1]}
            return {"order_id": order_id, "status": "unknown"}
    finally:
        conn.close()
