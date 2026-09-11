"""Reconciliation Service - Match internal records with provider records."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx
import psycopg2


# Reconciliation database
RECONCILIATION_DB_URL = os.environ.get(
    "RECONCILIATION_DATABASE_URL", "postgresql://localhost:5432/reconciliation"
)

# Documented dependencies
LEDGER_SERVICE_URL = os.environ.get(
    "LEDGER_SERVICE_URL", "http://ledger:8080"
)

PAYMENTS_SERVICE_URL = os.environ.get(
    "PAYMENTS_SERVICE_URL", "http://payments:8080"
)

# UNDOCUMENTED: Reconciliation downloads settlement files from provider
PAYMENT_PROVIDER_URL = os.environ.get(
    "PAYMENT_PROVIDER_URL", "https://api.stripe.com"
)

PAYMENT_PROVIDER_KEY = os.environ.get("PAYMENT_PROVIDER_KEY", "sk_test_...")


def get_reconciliation_db():
    """Get reconciliation database connection."""
    return psycopg2.connect(RECONCILIATION_DB_URL)


async def download_settlement_file(date: str) -> dict:
    """Download settlement file from payment provider.

    UNDOCUMENTED: Direct API call to Stripe for settlement data.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYMENT_PROVIDER_URL}/v1/reporting/report_runs",
            params={"report_type": "balance.summary.1", "date": date},
            headers={"Authorization": f"Bearer {PAYMENT_PROVIDER_KEY}"},
            timeout=30.0,
        )
        return response.json()


async def reconcile_date(date: str) -> dict:
    """Reconcile internal ledger with provider records for a given date.

    Documented dependencies: ledger, payments
    Actual dependencies: ledger, payments, external provider API
    """
    # Get internal records from ledger (DOCUMENTED)
    async with httpx.AsyncClient() as client:
        ledger_response = await client.get(
            f"{LEDGER_SERVICE_URL}/entries",
            params={"date": date},
            timeout=15.0,
        )
    internal_entries = ledger_response.json().get("entries", [])

    # Get provider records (UNDOCUMENTED)
    provider_data = await download_settlement_file(date)

    # Match and identify discrepancies
    discrepancies = []
    matched = 0
    for entry in internal_entries:
        # Simplified matching logic
        provider_match = next(
            (p for p in provider_data.get("data", [])
             if p.get("reference") == entry.get("provider_ref")),
            None,
        )
        if provider_match:
            matched += 1
        else:
            discrepancies.append({
                "entry_id": entry.get("entry_id"),
                "order_id": entry.get("order_id"),
                "reason": "no_provider_match",
            })

    return {
        "date": date,
        "internal_count": len(internal_entries),
        "matched": matched,
        "discrepancies": discrepancies,
        "status": "complete",
    }
