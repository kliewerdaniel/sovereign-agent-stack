"""Ledger Service - Double-entry bookkeeping for all financial transactions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import psycopg2


# Ledger database (isolated from payments DB)
LEDGER_DB_URL = os.environ.get(
    "LEDGER_DATABASE_URL", "postgresql://localhost:5432/ledger"
)

# Documented: no service dependencies
# Actual: depends on PostgreSQL only


def get_ledger_db():
    """Get ledger database connection."""
    return psycopg2.connect(LEDGER_DB_URL)


@dataclass
class LedgerEntry:
    entry_id: str
    order_id: str
    customer_id: str
    amount: float
    currency: str
    entry_type: str  # "payment", "refund", "adjustment"
    tax_amount: float = 0.0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


def record_entry(
    order_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    entry_type: str,
    tax_amount: float = 0.0,
) -> dict:
    """Record a double-entry bookkeeping entry.

    DOCUMENTED: No external service dependencies.
    ACTUAL: Correct — only depends on PostgreSQL.
    """
    conn = get_ledger_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ledger_entries
                (order_id, customer_id, amount, currency, entry_type, tax_amount)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING entry_id
                """,
                (order_id, customer_id, amount, currency, entry_type, tax_amount),
            )
            entry_id = cur.fetchone()[0]
            conn.commit()

            return {
                "entry_id": str(entry_id),
                "order_id": order_id,
                "amount": amount,
                "currency": currency,
                "type": entry_type,
            }
    finally:
        conn.close()


def get_balance(customer_id: str) -> dict:
    """Get current balance for a customer."""
    conn = get_ledger_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT SUM(amount) as balance, COUNT(*) as entry_count
                FROM ledger_entries
                WHERE customer_id = %s
                """,
                (customer_id,),
            )
            row = cur.fetchone()
            return {
                "customer_id": customer_id,
                "balance": float(row[0] or 0),
                "entry_count": row[1],
            }
    finally:
        conn.close()
