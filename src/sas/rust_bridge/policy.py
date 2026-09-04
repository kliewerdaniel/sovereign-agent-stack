"""Rust-backed policy enforcement."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from . import sas_core_py as _rust
except ImportError:
    _rust = None


class PolicyEnforcer:
    """Policy enforcement backed by Rust.
    
    Enforces policies before privileged operations.
    """
    
    def __init__(self, mode: str = "allow"):
        """
        Args:
            mode: "allow" to allow all, "deny" to deny all
        """
        if _rust is None:
            raise RuntimeError("Rust extension not available")
        self._inner = _rust.PolicyEnforcer(mode)
    
    def check_write(self, path: str, content: bytes) -> bool:
        """Check if write is allowed."""
        return self._inner.check_write(path, content)
    
    def check_exec(self, command: str, args: list[str]) -> bool:
        """Check if command execution is allowed."""
        return self._inner.check_exec(command, args)
    
    def check_dispatch(self, url: str, method: str = "GET") -> bool:
        """Check if network dispatch is allowed."""
        return self._inner.check_dispatch(url, method)
    
    def check_payment(self, amount: float, currency: str, recipient: str) -> bool:
        """Check if payment is allowed."""
        return self._inner.check_payment(amount, currency, recipient)
    
    def __repr__(self) -> str:
        return "PolicyEnforcer()"
