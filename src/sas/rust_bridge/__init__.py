"""Rust bridge for Sovereign Agent Stack.

This module provides Python bindings to the Rust compile-time verification layer.
Falls back to pure Python implementations if the Rust extension is not available.
"""
from __future__ import annotations

import logging
from typing import Any, Optional, Set

logger = logging.getLogger(__name__)

try:
    from . import sas_core_py as _rust
    _RUST_AVAILABLE = True
except ImportError:
    _rust = None
    _RUST_AVAILABLE = False
    logger.warning("Rust extension not available. Using pure Python fallback.")


def is_available() -> bool:
    """Check if the Rust extension is available."""
    return _RUST_AVAILABLE


# ── Pure Python fallback implementations ─────────────────────────────────────

class _PyExecutionContext:
    """Pure Python fallback for ExecutionContext."""
    
    def __init__(self):
        self._capabilities = {
            "read_filesystem": False,
            "write_filesystem": False,
            "dispatch_network": False,
            "execute_commands": False,
            "process_payments": False,
        }
    
    @property
    def can_read_filesystem(self) -> bool:
        return self._capabilities["read_filesystem"]
    
    @property
    def can_write_filesystem(self) -> bool:
        return self._capabilities["write_filesystem"]
    
    @property
    def can_dispatch_network(self) -> bool:
        return self._capabilities["dispatch_network"]
    
    @property
    def can_execute_commands(self) -> bool:
        return self._capabilities["execute_commands"]
    
    @property
    def can_process_payments(self) -> bool:
        return self._capabilities["process_payments"]
    
    def with_read_filesystem(self) -> "_PyExecutionContext":
        new = _PyExecutionContext()
        new._capabilities = dict(self._capabilities)
        new._capabilities["read_filesystem"] = True
        return new
    
    def with_write_filesystem(self) -> "_PyExecutionContext":
        new = _PyExecutionContext()
        new._capabilities = dict(self._capabilities)
        new._capabilities["write_filesystem"] = True
        return new
    
    def with_dispatch_network(self) -> "_PyExecutionContext":
        new = _PyExecutionContext()
        new._capabilities = dict(self._capabilities)
        new._capabilities["dispatch_network"] = True
        return new
    
    def with_execute_commands(self) -> "_PyExecutionContext":
        new = _PyExecutionContext()
        new._capabilities = dict(self._capabilities)
        new._capabilities["execute_commands"] = True
        return new
    
    def with_process_payments(self) -> "_PyExecutionContext":
        new = _PyExecutionContext()
        new._capabilities = dict(self._capabilities)
        new._capabilities["process_payments"] = True
        return new
    
    def __repr__(self) -> str:
        caps = ", ".join(f"{k}={v}" for k, v in self._capabilities.items())
        return f"ExecutionContext({caps})"


class _PyCapabilityRegistry:
    """Pure Python fallback for CapabilityRegistry."""
    
    CAPABILITIES = [
        "read_filesystem",
        "write_filesystem",
        "dispatch_network",
        "execute_commands",
        "process_payments",
        "emit_events",
        "read_knowledge",
        "write_knowledge",
    ]
    
    def __init__(self):
        self._granted: Set[str] = set()
    
    def grant(self, capability: str) -> None:
        self._granted.add(capability)
    
    def revoke(self, capability: str) -> None:
        self._granted.discard(capability)
    
    def is_granted(self, capability: str) -> bool:
        return capability in self._granted
    
    def require(self, capability: str) -> None:
        if not self.is_granted(capability):
            raise PermissionError(f"Required capability not granted: {capability}")
    
    def granted_capabilities(self) -> Set[str]:
        return set(self._granted)
    
    def __repr__(self) -> str:
        return f"CapabilityRegistry(granted={self._granted})"


class _PyPolicyEnforcer:
    """Pure Python fallback for PolicyEnforcer."""
    
    def __init__(self, mode: str = "allow"):
        self._mode = mode
    
    def check_write(self, path: str, content: bytes) -> bool:
        if self._mode == "deny":
            raise PermissionError(f"Write to '{path}' forbidden: denied by policy")
        return True
    
    def check_exec(self, command: str, args: list[str]) -> bool:
        if self._mode == "deny":
            raise PermissionError(f"Exec '{command}' forbidden: denied by policy")
        return True
    
    def check_dispatch(self, url: str, method: str = "GET") -> bool:
        if self._mode == "deny":
            raise PermissionError(f"Dispatch to '{url}' forbidden: denied by policy")
        return True
    
    def check_payment(self, amount: float, currency: str, recipient: str) -> bool:
        if self._mode == "deny":
            raise PermissionError(f"Payment {amount} {currency} forbidden: denied by policy")
        return True
    
    def __repr__(self) -> str:
        return f"PolicyEnforcer(mode={self._mode})"


class _PySovereigntyAsserter:
    """Pure Python fallback for SovereigntyAsserter."""
    
    LAYERS = [
        "model",
        "harness",
        "compute",
        "identity",
        "short_term_memory",
        "long_term_knowledge",
        "auth",
        "payments",
    ]
    
    def __init__(self):
        self._layers: dict[str, str] = {}
    
    def with_layer(self, layer: str, ownership: str) -> "_PySovereigntyAsserter":
        self._layers[layer] = ownership
        return self
    
    def assert_all_owned(self) -> bool:
        for layer, ownership in self._layers.items():
            if ownership != "owned":
                raise ValueError(f"Layer '{layer}' is not owned (actual: {ownership})")
        return True
    
    def assert_score_above(self, threshold: float) -> bool:
        score = self.calculate_score()
        if score < threshold:
            raise ValueError(f"Sovereignty score {score} is below required {threshold}")
        return True
    
    def calculate_score(self) -> float:
        if not self._layers:
            return 0.0
        owned = sum(1 for o in self._layers.values() if o == "owned")
        return owned / len(self._layers)
    
    @property
    def score(self) -> float:
        return self.calculate_score()
    
    @property
    def owned_count(self) -> int:
        return sum(1 for o in self._layers.values() if o == "owned")
    
    @property
    def total_count(self) -> int:
        return len(self._layers)
    
    @property
    def verdict(self) -> str:
        score = self.score
        if score >= 0.875:
            return "Fully Sovereign"
        elif score >= 0.625:
            return "Sovereign (target)"
        elif score >= 0.375:
            return "Partially sovereign"
        else:
            return "Rented"
    
    def __repr__(self) -> str:
        return f"SovereigntyAsserter(owned={self.owned_count}/{self.total_count}, score={self.score:.2})"


class _PyAgentStateMachine:
    """Pure Python fallback for AgentStateMachine."""
    
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
        self._current = "Idle"
        self._history: list[dict] = []
    
    @property
    def current(self) -> str:
        return self._current
    
    def transition(self, to: str, reason: str | None = None) -> None:
        if to not in self.VALID_TRANSITIONS.get(self._current, []):
            raise ValueError(f"Invalid state transition: {self._current} -> {to}")
        self._history.append({
            "from": self._current,
            "to": to,
            "reason": reason,
        })
        self._current = to
    
    @property
    def history(self) -> list[dict]:
        return list(self._history)
    
    def can_transition_to(self, state: str) -> bool:
        return state in self.VALID_TRANSITIONS.get(self._current, [])
    
    @property
    def is_terminal(self) -> bool:
        return len(self.VALID_TRANSITIONS.get(self._current, [])) == 0
    
    def __repr__(self) -> str:
        return f"AgentStateMachine(current={self._current})"


# ── Public API: Use Rust if available, else fallback ─────────────────────────

if _RUST_AVAILABLE:
    ExecutionContext = _rust.ExecutionContext
    CapabilityRegistry = _rust.CapabilityRegistry
    PolicyEnforcer = _rust.PolicyEnforcer
    SovereigntyAsserter = _rust.SovereigntyAsserter
    AgentStateMachine = _rust.AgentStateMachine
else:
    ExecutionContext = _PyExecutionContext
    CapabilityRegistry = _PyCapabilityRegistry
    PolicyEnforcer = _PyPolicyEnforcer
    SovereigntyAsserter = _PySovereigntyAsserter
    AgentStateMachine = _PyAgentStateMachine


__all__ = [
    "ExecutionContext",
    "CapabilityRegistry",
    "PolicyEnforcer",
    "SovereigntyAsserter",
    "AgentStateMachine",
    "is_available",
]
