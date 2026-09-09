"""Notifications Service - Email and SMS notifications for payment events."""

from __future__ import annotations

import os
from typing import Optional

import httpx


# Notification provider endpoints
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_URL = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

# Documented: no service dependencies (event-driven)
# Actual: depends on external email/SMS providers only


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send email via SendGrid.

    DOCUMENTED: Notifications is event-driven, no internal service dependencies.
    ACTUAL: Correct — only depends on external SendGrid API.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SENDGRID_URL,
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": "payments@example.com"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=15.0,
        )
        return {"status": response.status_code, "provider": "sendgrid"}


async def send_sms(to: str, message: str) -> dict:
    """Send SMS via Twilio.

    DOCUMENTED: No internal service dependencies.
    ACTUAL: Correct — only depends on external Twilio API.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TWILIO_URL,
            data={"To": to, "From": "+15551234567", "Body": message},
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=15.0,
        )
        return {"status": response.status_code, "provider": "twilio"}
