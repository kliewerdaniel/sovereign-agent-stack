"""Layer 4: Identity — The agent's addressable presence on legacy communication rails.

Unavoidably rented — you cannot self-host a phone number or MX records.
Abstracted behind local adapters so providers are swapped without touching agent logic.
"""

from dataclasses import dataclass
from typing import AsyncIterator, Protocol


@dataclass
class Inbox:
    id: str
    username: str
    domain: str
    created_at: str


@dataclass
class Email:
    from_: str
    to: str
    subject: str
    body: str
    thread_id: str | None = None


@dataclass
class PhoneNumber:
    id: str
    number: str
    region: str
    capabilities: list[str]  # ["voice", "sms", "imessage"]


@dataclass
class Call:
    id: str
    from_number: str
    to_number: str
    status: str


class EmailIdentity(Protocol):
    async def provision(self, username: str, domain: str) -> Inbox: ...
    async def send(self, inbox: Inbox, message: Email) -> None: ...
    async def watch(self, inbox: Inbox) -> AsyncIterator[Email]: ...


class PhoneIdentity(Protocol):
    async def provision(self, region: str) -> PhoneNumber: ...
    async def call(self, number: PhoneNumber, target: str) -> Call: ...
    async def sms(self, number: PhoneNumber, message: str) -> None: ...
