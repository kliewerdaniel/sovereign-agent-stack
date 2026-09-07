"""ResearchWindow — immutable temporal authority for governed research.

Every tool invocation executes against an immutable temporal authority
containing the earliest available timestamp and the maximum permitted
timestamp. The data provider receives a validated window rather than
arbitrary dates from the model.

This makes point-in-time enforcement a property of the execution
protocol rather than a convention implemented independently by each tool.

The holdout boundary is impossible to cross through ordinary tool calls.
The runtime transitions from RESEARCH → HOLDOUT → FINAL, one-way only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ExecutionCapability(Enum):
    """The agent's available capabilities change according to lifecycle state.

    RESEARCH: allowed <= research_end
    HOLDOUT: allowed >= holdout_start, strategy immutable, no critique, no revision
    FINAL: no market data access, evaluation only

    Transitions are one-way: RESEARCH → HOLDOUT → FINAL
    """
    RESEARCH = "research"
    HOLDOUT = "holdout"
    FINAL = "final"


@dataclass(frozen=True)
class ResearchWindow:
    """Immutable temporal authority for a research experiment.

    Contains the earliest available timestamp and the maximum permitted
    timestamp. Any request for data beyond max_permitted_timestamp is
    rejected by the execution protocol — not by individual tools.

    The holdout_start marks the boundary. Once the research phase
    terminates, the model cannot access data beyond research_end
    through ordinary tool calls.
    """
    earliest_timestamp: str = ""  # earliest available data
    max_permitted_timestamp: str = ""  # research_end — hard limit
    holdout_start: str = ""  # holdout window begins
    final_timestamp: str = ""  # end of all data

    def validate_date_range(self, start: str, end: str) -> tuple[bool, str]:
        """Validate that a date range request is within the permitted window.

        Returns (is_valid, error_message).
        """
        if not start and not end:
            return True, ""

        # Check start is not before earliest
        if start and self.earliest_timestamp and start < self.earliest_timestamp:
            return False, (
                f"Start date {start} is before earliest available "
                f"{self.earliest_timestamp}"
            )

        # Check end is not beyond max permitted
        if end and self.max_permitted_timestamp and end > self.max_permitted_timestamp:
            return False, (
                f"End date {end} exceeds maximum permitted timestamp "
                f"{self.max_permitted_timestamp}. Access to data beyond "
                f"the research window is not permitted."
            )

        # Check start is not beyond max permitted
        if start and self.max_permitted_timestamp and start > self.max_permitted_timestamp:
            return False, (
                f"Start date {start} is beyond the research window "
                f"({self.max_permitted_timestamp})."
            )

        return True, ""

    def to_dict(self) -> dict:
        return {
            "earliest_timestamp": self.earliest_timestamp,
            "max_permitted_timestamp": self.max_permitted_timestamp,
            "holdout_start": self.holdout_start,
            "final_timestamp": self.final_timestamp,
        }


@dataclass(frozen=True)
class HoldoutWindow:
    """Immutable temporal authority for holdout evaluation.

    The holdout window is physically separate from the research window.
    Once the research phase terminates, the model cannot mutate the
    strategy and access the holdout again.
    """
    holdout_start: str = ""
    final_timestamp: str = ""
    strategy_immutable: bool = True
    no_critique: bool = True
    no_revision: bool = True
    no_research_writes: bool = True

    def validate_date_range(self, start: str, end: str) -> tuple[bool, str]:
        """Validate that a date range request is within the holdout window."""
        if not start and not end:
            return True, ""

        if self.holdout_start and start and start < self.holdout_start:
            return False, (
                f"Holdout evaluation cannot access data before "
                f"{self.holdout_start}"
            )

        return True, ""

    def to_dict(self) -> dict:
        return {
            "holdout_start": self.holdout_start,
            "final_timestamp": self.final_timestamp,
            "strategy_immutable": self.strategy_immutable,
            "no_critique": self.no_critique,
            "no_revision": self.no_revision,
            "no_research_writes": self.no_research_writes,
        }


class TemporalAuthority:
    """Manages the one-way transition between execution capabilities.

    RESEARCH → HOLDOUT → FINAL

    There is no valid transition from HOLDOUT back to RESEARCH.
    This makes the holdout separation an execution property rather
    than a prompt instruction.
    """

    def __init__(
        self,
        research_window: ResearchWindow,
        holdout_window: HoldoutWindow | None = None,
    ):
        self.research_window = research_window
        self.holdout_window = holdout_window
        self._capability = ExecutionCapability.RESEARCH
        self._transitioned_to_holdout = False
        self._transitioned_to_final = False

    @property
    def capability(self) -> ExecutionCapability:
        return self._capability

    def transition_to_holdout(self) -> None:
        """Transition from RESEARCH to HOLDOUT. One-way only."""
        if self._capability != ExecutionCapability.RESEARCH:
            raise ValueError(
                f"Cannot transition to HOLDOUT from {self._capability.value}"
            )
        if self._transitioned_to_holdout:
            raise ValueError("Already transitioned to HOLDOUT")
        self._capability = ExecutionCapability.HOLDOUT
        self._transitioned_to_holdout = True

    def transition_to_final(self) -> None:
        """Transition from HOLDOUT to FINAL. One-way only."""
        if self._capability != ExecutionCapability.HOLDOUT:
            raise ValueError(
                f"Cannot transition to FINAL from {self._capability.value}"
            )
        if self._transitioned_to_final:
            raise ValueError("Already transitioned to FINAL")
        self._capability = ExecutionCapability.FINAL
        self._transitioned_to_final = True

    def validate_date_range(self, start: str, end: str) -> tuple[bool, str]:
        """Validate a date range request against the current capability."""
        if self._capability == ExecutionCapability.RESEARCH:
            return self.research_window.validate_date_range(start, end)
        elif self._capability == ExecutionCapability.HOLDOUT:
            if self.holdout_window:
                return self.holdout_window.validate_date_range(start, end)
            return False, "No holdout window configured"
        else:  # FINAL
            return False, "No market data access in FINAL state"

    def to_dict(self) -> dict:
        return {
            "capability": self._capability.value,
            "research_window": self.research_window.to_dict(),
            "holdout_window": self.holdout_window.to_dict() if self.holdout_window else None,
            "transitioned_to_holdout": self._transitioned_to_holdout,
            "transitioned_to_final": self._transitioned_to_final,
        }
