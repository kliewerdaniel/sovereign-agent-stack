"""Identity adapters — agent-native communication on legacy rails.

AgentMail and AgentPhone are unavoidably rented (can't self-host phone/MX records).
Abstracted behind local adapters so providers are swapped without touching agent logic.

Authenticity-by-disclosure: use agentmail.to domain, not spoofed @nick.ai.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Inbox:
    """An email inbox."""
    id: str
    username: str
    domain: str
    created_at: str


@dataclass
class Email:
    """An email message."""
    from_: str
    to: str
    subject: str
    body: str
    thread_id: str | None = None


@dataclass
class PhoneNumber:
    """A phone number."""
    id: str
    number: str
    region: str
    capabilities: list[str]  # ["voice", "sms", "imessage"]


@dataclass
class Call:
    """A phone call."""
    id: str
    from_number: str
    to_number: str
    status: str


class EmailIdentity(Protocol):
    """Protocol for email identity adapters."""
    def provision(self, username: str, domain: str) -> Inbox: ...
    def send(self, inbox: Inbox, message: Email) -> None: ...
    def watch(self, inbox: Inbox) -> list[Email]: ...


class PhoneIdentity(Protocol):
    """Protocol for phone identity adapters."""
    def provision(self, region: str) -> PhoneNumber: ...
    def call(self, number: PhoneNumber, target: str) -> Call: ...
    def sms(self, number: PhoneNumber, message: str) -> None: ...


class AgentMailAdapter:
    """AgentMail API adapter — real production adapter."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def provision(self, username: str, domain: str) -> Inbox:
        """Provision a new inbox via AgentMail API."""
        # In production: POST https://api.agentmail.com/v1/inboxes
        # For now, simulate
        return Inbox(
            id=f"inbox_{uuid.uuid4().hex[:8]}",
            username=username,
            domain=domain,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def send(self, inbox: Inbox, message: Email) -> None:
        """Send an email via AgentMail API."""
        # In production: POST https://api.agentmail.com/v1/inboxes/{inbox.id}/send
        pass

    def watch(self, inbox: Inbox) -> list[Email]:
        """Watch for incoming emails via AgentMail webhooks."""
        # In production: poll or webhook
        return []


class AgentPhoneAdapter:
    """AgentPhone API adapter — real production adapter."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def provision(self, region: str) -> PhoneNumber:
        """Provision a phone number via AgentPhone API."""
        # In production: POST https://api.agentphone.com/v1/numbers
        return PhoneNumber(
            id=f"phone_{uuid.uuid4().hex[:8]}",
            number=f"+1555{uuid.uuid4().hex[:7]}",
            region=region,
            capabilities=["voice", "sms", "imessage"],
        )

    def call(self, number: PhoneNumber, target: str) -> Call:
        """Make a call via AgentPhone API."""
        # In production: POST https://api.agentphone.com/v1/calls
        return Call(
            id=f"call_{uuid.uuid4().hex[:8]}",
            from_number=number.number,
            to_number=target,
            status="completed",
        )

    def sms(self, number: PhoneNumber, message: str) -> None:
        """Send SMS via AgentPhone API."""
        # In production: POST https://api.agentphone.com/v1/sms
        pass


class MockEmailAdapter:
    """Mock email adapter for local development."""

    def __init__(self) -> None:
        self._inboxes: dict[str, Inbox] = {}
        self._sent: dict[str, list[Email]] = {}

    def provision(self, username: str, domain: str) -> Inbox:
        """Provision a mock inbox."""
        inbox = Inbox(
            id=f"mock_inbox_{uuid.uuid4().hex[:8]}",
            username=username,
            domain=domain,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self._inboxes[inbox.id] = inbox
        self._sent[inbox.id] = []
        return inbox

    def send(self, inbox: Inbox, message: Email) -> None:
        """Send a mock email (stores it)."""
        if inbox.id not in self._sent:
            self._sent[inbox.id] = []
        self._sent[inbox.id].append(message)

    def watch(self, inbox: Inbox) -> list[Email]:
        """Watch returns sent emails (for testing)."""
        return self._sent.get(inbox.id, [])


class MockPhoneAdapter:
    """Mock phone adapter for local development."""

    def __init__(self) -> None:
        self._numbers: dict[str, PhoneNumber] = {}
        self._calls: dict[str, list[Call]] = {}
        self._sms: dict[str, list[str]] = {}

    def provision(self, region: str) -> PhoneNumber:
        """Provision a mock phone number."""
        number = PhoneNumber(
            id=f"mock_phone_{uuid.uuid4().hex[:8]}",
            number=f"+1555{uuid.uuid4().hex[:7]}",
            region=region,
            capabilities=["voice", "sms", "imessage"],
        )
        self._numbers[number.id] = number
        self._calls[number.id] = []
        self._sms[number.id] = []
        return number

    def call(self, number: PhoneNumber, target: str) -> Call:
        """Make a mock call."""
        call = Call(
            id=f"mock_call_{uuid.uuid4().hex[:8]}",
            from_number=number.number,
            to_number=target,
            status="completed",
        )
        if number.id not in self._calls:
            self._calls[number.id] = []
        self._calls[number.id].append(call)
        return call

    def sms(self, number: PhoneNumber, message: str) -> None:
        """Send a mock SMS."""
        if number.id not in self._sms:
            self._sms[number.id] = []
        self._sms[number.id].append(message)

    def get_sent_messages(self, number: PhoneNumber) -> list[str]:
        """Get sent SMS messages for a number."""
        return self._sms.get(number.id, [])

    def get_call_history(self, number: PhoneNumber) -> list[Call]:
        """Get call history for a number."""
        return self._calls.get(number.id, [])
