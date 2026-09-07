"""Rust-backed capability registry."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from . import sas_core_py as _rust
except ImportError:
    _rust = None


class CapabilityRegistry:
    """Capability registry backed by Rust.
    
    Manages capability grants and provides proofs of capability.
    """
    
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
        if _rust is None:
            raise RuntimeError("Rust extension not available")
        self._inner = _rust.CapabilityRegistry()
    
    def grant(self, capability: str) -> None:
        """Grant a capability."""
        self._inner.grant(capability)
    
    def revoke(self, capability: str) -> None:
        """Revoke a capability (not yet supported in Rust)."""
        # TODO: Add revoke to Rust
    
    def is_granted(self, capability: str) -> bool:
        """Check if a capability is granted."""
        return self._inner.is_granted(capability)
    
    def require(self, capability: str) -> None:
        """Require a capability, raising PermissionError if not granted."""
        self._inner.require(capability)
    
    def granted_capabilities(self) -> set[str]:
        """Get all granted capabilities."""
        return {cap for cap in self.CAPABILITIES if self.is_granted(cap)}
    
    def __repr__(self) -> str:
        granted = self.granted_capabilities()
        return f"CapabilityRegistry(granted={granted})"
