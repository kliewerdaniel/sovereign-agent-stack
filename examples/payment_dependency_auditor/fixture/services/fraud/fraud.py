"""Fraud Service - Transaction risk evaluation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx


# Documented: no service dependencies (stateless evaluation)
# Actual: depends on external ML model service for scoring

ML_MODEL_URL = os.environ.get(
    "ML_MODEL_URL", "http://fraud-ml-model:8080"
)

# UNDOCUMENTED: Fraud service uses Redis for rate limiting
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


@dataclass
class FraudEvaluation:
    score: float  # 0.0 = safe, 1.0 = fraud
    risk_level: str  # "low", "medium", "high"
    reasons: list[str]


async def evaluate_transaction(
    order_id: str,
    customer_id: str,
    amount: float,
    payment_method: str = "card",
) -> dict:
    """Evaluate transaction for fraud risk.

    DOCUMENTED: Stateless, no service dependencies.
    ACTUAL: Depends on external ML model service for scoring.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ML_MODEL_URL}/predict",
            json={
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": amount,
                "payment_method": payment_method,
            },
            timeout=10.0,
        )

    result = response.json()
    score = result.get("fraud_probability", 0.5)

    if score < 0.3:
        risk_level = "low"
    elif score < 0.7:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "score": score,
        "risk_level": risk_level,
        "reasons": result.get("reasons", []),
    }
