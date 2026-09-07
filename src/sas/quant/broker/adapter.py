"""Broker adapter abstraction.

A broker adapter is the ONLY component permitted to reach a live
exchange.  The LLM never calls a broker directly — the orchestrator
submits a ``TradeIntent`` to the adapter only after the authorization
gate has approved it.

Two implementations ship with SAS:

- ``SimulatedBroker`` — deterministic, in-memory, for backtesting.
- ``AlpacaBrokerAdapter`` — paper-trading via the Alpaca Trade API.

Credentials are sourced from environment variables or the local vault;
they are never logged, never serialized to provenance, and never
returned in any ``__repr__`` or ``to_dict`` output.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sas.quant.broker import Order
    from sas.quant.risk import TradeIntent


class BrokerAdapter(ABC):
    """Abstract broker adapter.

    The orchestrator calls ``submit_trade`` with an approved
    ``TradeIntent``.  The adapter is responsible for translating that
    intent into a broker-specific order and returning an ``Order``
    with the fill result.
    """

    @abstractmethod
    def submit_trade(self, trade: TradeIntent) -> Order:
        """Submit an approved trade intent to the broker.

        Args:
            trade: A ``TradeIntent`` that has passed risk evaluation
                and authorization.  ``trade.status`` is ``"authorized"``.

        Returns:
            An ``Order`` with fill details.
        """
        ...

    @abstractmethod
    def get_account_summary(self) -> dict:
        """Return a summary of the brokerage account.

        Never includes raw credentials.
        """
        ...

    @abstractmethod
    def get_positions(self) -> dict[str, float]:
        """Return current positions as ``symbol -> quantity``."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable broker name (e.g. ``"alpaca-paper"``)."""
        ...

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """True if this adapter connects to a live (paper or real) broker."""
        ...
