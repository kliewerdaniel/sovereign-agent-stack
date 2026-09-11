"""Refunds Service - Process refund requests and coordinate reversals."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
import psycopg2


# Refunds database
REFUNDS_DB_URL = os.environ.get(
    "REFUNDS_DATABASE_URL", "postgresql://localhost:5432/refunds"
)

# Documented dependencies
PAYMENTS_SERVICE_URL = os.environ.get(
    "PAYMENTS_SERVICE_URL", "http://payments:8080"
)

LEDGER_SERVICE_URL = os.environ.get(
    "LEDGER_SERVICE_URL", "http://ledger:8080"
)

# UNDOCUMENTED: Refunds checks customer eligibility directly
CUSTOMER_PROFILE_URL = os.environ.get(
    "CUSTOMER_PROFILE_URL", "http://customer-profile:8080"
)

# UNDOCUMENTED: Feature flags control refund policy changes
FEATURE_FLAGS_URL = os.environ.get(
    "FEATURE_FLAGS_URL", "http://feature-flags:8080"
)


def get_refunds_db():
    """Get refunds database connection."""
    return psycopg2.connect(REFUNDS_DB_URL)


async def check_refund_eligibility(customer_id: str, order_id: str) -> dict:
    """Check if a refund is eligible.

    UNDOCUMENTED: Calls customer-profile service directly.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CUSTOMER_PROFILE_URL}/customers/{customer_id}/refund-eligibility",
            params={"order_id": order_id},
            timeout=10.0,
        )
        return response.json()


async def process_refund(
    order_id: str,
    customer_id: str,
    amount: float,
    reason: str = "customer_request",
) -> dict:
    """Process a refund.

    Documented dependencies: payments, ledger
    Actual dependencies: payments, ledger, customer-profile, feature-flags
    """
    # Check eligibility (UNDOCUMENTED dependency)
    eligibility = await check_refund_eligibility(customer_id, order_id)
    if not eligibility.get("eligible", False):
        raise ValueError(
            f"Refund not eligible: {eligibility.get('reason', 'unknown')}"
        )

    # Check feature flag for refund policy (UNDOCUMENTED)
    async with httpx.AsyncClient() as client:
        flag_response = await client.get(
            f"{FEATURE_FLAGS_URL}/flags/new-refund-policy",
            timeout=5.0,
        )
        new_policy = flag_response.json().get("enabled", False)

    # Process via payments service (DOCUMENTED)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENTS_SERVICE_URL}/refunds",
            json={
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": amount,
                "reason": reason,
            },
            timeout=30.0,
        )

    return response.json()
