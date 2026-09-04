"""Rust-backed agent state machine."""
from __future__ import annotations

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

try:
    from . import sas_core_py as _rust
except ImportError:
    _rust = None


class StateTransition:
    """A recorded state transition."""
    
    def __init__(self, from_state: str, to_state: str, timestamp: str, reason: Optional[str]):
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = timestamp
        self.reason = reason
    
    @classmethod
    def from_string(cls, s: str) -> "StateTransition":
        # Parse "Idle -> Executing (2024-01-01T00:00:00Z)"
        parts = s.split(" -> ")
        from_state = parts[0]
        rest = parts[1].split(" (")
        to_state = rest[0]
        rest = rest[1].rstrip(")")
        timestamp = rest
        return cls(from_state, to_state, timestamp, None)
    
    def __repr__(self) -> str:
        return f"StateTransition({self.from_state} -> {self.to_state})"


class AgentStateMachine:
    """Agent state machine backed by Rust.
    
    Valid transitions:
        Idle -> Compiling, Executing
        Compiling -> Executing, Failed
        Executing -> Verifying, Failed
        Verifying -> Completed, Failed, Executing (retry)
        Failed -> Idle (reset)
        Completed -> Idle (reset)
    """
    
    IDLE = "Idle"
    COMPILING = "Compiling"
    EXECUTING = "Executing"
    VERIFYING = "Verifying"
    FAILED = "Failed"
    COMPLETED = "Completed"
    
    VALID_TRANSITIONS = {
        "Idle": ["Compiling", "Executing"],
        "Compiling": ["Executing", "Failed"],
        "Executing": ["Verifying", "Failed"],
        "Verifying": ["Completed", "Failed", "Executing"],
        "Failed": ["Idle"],
        "Completed": ["Idle"],
    }
    
    def __init__(self):
        if _rust is None:
            raise RuntimeError("Rust extension not available")
        self._inner = _rust.AgentStateMachine()
    
    @property
    def current(self) -> str:
        return self._inner.current
    
    def transition(self, to: str, reason: Optional[str] = None) -> None:
        """Attempt a state transition."""
        self._inner.transition(to, reason)
    
    @property
    def history(self) -> List[StateTransition]:
        return [StateTransition.from_string(h) for h in self._inner.history]
    
    def can_transition_to(self, state: str) -> bool:
        """Check if a transition to the given state is valid."""
        return state in self.VALID_TRANSITIONS.get(self.current, [])
    
    @property
    def is_terminal(self) -> bool:
        """Check if the current state is terminal."""
        return len(self.VALID_TRANSITIONS.get(self.current, [])) == 0
    
    def __repr__(self) -> str:
        return f"AgentStateMachine(current={self.current})"
